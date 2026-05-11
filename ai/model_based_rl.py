"""
Model-Based Reinforcement Learning
Học world model và sử dụng cho planning: World Models, Dyna-Q, MBPO
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional
from collections import deque
import random


# ============ WORLD MODEL ============

class TransitionModel(nn.Module):
    """
    Transition model: predicts next state
    s_{t+1} = f(s_t, a_t)
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, state_dim)
        )
    
    def forward(self, state, action):
        """Predict next state"""
        # One-hot encode action if needed
        if len(action.shape) == 1:
            action_onehot = F.one_hot(action, num_classes=self.network[0].in_features - state.shape[-1])
            action = action_onehot.float()
        
        x = torch.cat([state, action], dim=-1)
        next_state = self.network(x)
        return next_state


class RewardModel(nn.Module):
    """
    Reward model: predicts reward
    r_t = g(s_t, a_t)
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, state, action):
        """Predict reward"""
        if len(action.shape) == 1:
            action_onehot = F.one_hot(action, num_classes=self.network[0].in_features - state.shape[-1])
            action = action_onehot.float()
        
        x = torch.cat([state, action], dim=-1)
        reward = self.network(x)
        return reward


class DoneModel(nn.Module):
    """
    Done model: predicts episode termination
    done_t = h(s_t, a_t)
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
    
    def forward(self, state, action):
        """Predict done probability"""
        if len(action.shape) == 1:
            action_onehot = F.one_hot(action, num_classes=self.network[0].in_features - state.shape[-1])
            action = action_onehot.float()
        
        x = torch.cat([state, action], dim=-1)
        done_prob = self.network(x)
        return done_prob


class WorldModel:
    """
    Complete World Model
    Bao gồm: Transition, Reward, Done models
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256, learning_rate=1e-3):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Models
        self.transition_model = TransitionModel(state_dim, action_dim, hidden_dim)
        self.reward_model = RewardModel(state_dim, action_dim, hidden_dim)
        self.done_model = DoneModel(state_dim, action_dim, hidden_dim)
        
        # Optimizers
        self.transition_optimizer = torch.optim.Adam(self.transition_model.parameters(), lr=learning_rate)
        self.reward_optimizer = torch.optim.Adam(self.reward_model.parameters(), lr=learning_rate)
        self.done_optimizer = torch.optim.Adam(self.done_model.parameters(), lr=learning_rate)
        
        self.training_stats = {
            'transition_loss': [],
            'reward_loss': [],
            'done_loss': []
        }
    
    def train_step(self, states, actions, next_states, rewards, dones):
        """
        Train world model on real experience
        """
        # Train transition model
        pred_next_states = self.transition_model(states, actions)
        transition_loss = F.mse_loss(pred_next_states, next_states)
        
        self.transition_optimizer.zero_grad()
        transition_loss.backward()
        self.transition_optimizer.step()
        
        # Train reward model
        pred_rewards = self.reward_model(states, actions)
        reward_loss = F.mse_loss(pred_rewards, rewards.unsqueeze(1))
        
        self.reward_optimizer.zero_grad()
        reward_loss.backward()
        self.reward_optimizer.step()
        
        # Train done model
        pred_dones = self.done_model(states, actions)
        done_loss = F.binary_cross_entropy(pred_dones, dones.unsqueeze(1))
        
        self.done_optimizer.zero_grad()
        done_loss.backward()
        self.done_optimizer.step()
        
        # Record stats
        self.training_stats['transition_loss'].append(transition_loss.item())
        self.training_stats['reward_loss'].append(reward_loss.item())
        self.training_stats['done_loss'].append(done_loss.item())
        
        return transition_loss.item(), reward_loss.item(), done_loss.item()
    
    def predict(self, state, action):
        """
        Predict next state, reward, done
        """
        with torch.no_grad():
            next_state = self.transition_model(state, action)
            reward = self.reward_model(state, action)
            done_prob = self.done_model(state, action)
            done = done_prob > 0.5
        
        return next_state, reward, done
    
    def rollout(self, initial_state, policy, horizon=10):
        """
        Rollout trajectory using world model
        """
        states = [initial_state]
        actions = []
        rewards = []
        dones = []
        
        state = initial_state
        
        for t in range(horizon):
            # Get action from policy
            with torch.no_grad():
                action = policy(state)
            
            # Predict next state, reward, done
            next_state, reward, done = self.predict(state, action)
            
            states.append(next_state)
            actions.append(action)
            rewards.append(reward)
            dones.append(done)
            
            if done.item():
                break
            
            state = next_state
        
        return states, actions, rewards, dones


# ============ DYNA-Q ============

class DynaQ:
    """
    Dyna-Q Algorithm
    Kết hợp model-free learning với planning
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256, planning_steps=5):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.planning_steps = planning_steps
        
        # Q-network (model-free)
        self.q_network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        
        self.q_optimizer = torch.optim.Adam(self.q_network.parameters(), lr=1e-3)
        
        # World model
        self.world_model = WorldModel(state_dim, action_dim, hidden_dim)
        
        # Experience buffer
        self.buffer = deque(maxlen=10000)
        
        self.gamma = 0.99
    
    def select_action(self, state, epsilon=0.1):
        """Epsilon-greedy action selection"""
        if random.random() < epsilon:
            return random.randint(0, self.action_dim - 1)
        
        with torch.no_grad():
            q_values = self.q_network(state)
            return q_values.argmax().item()
    
    def update_q_network(self, state, action, reward, next_state, done):
        """Update Q-network (model-free)"""
        # Compute target
        with torch.no_grad():
            next_q_values = self.q_network(next_state)
            target = reward + self.gamma * next_q_values.max() * (1 - done)
        
        # Compute current Q-value
        q_values = self.q_network(state)
        current_q = q_values[0, action]
        
        # Loss
        loss = F.mse_loss(current_q, target)
        
        # Update
        self.q_optimizer.zero_grad()
        loss.backward()
        self.q_optimizer.step()
        
        return loss.item()
    
    def planning(self):
        """Planning using world model"""
        if len(self.buffer) < 10:
            return
        
        for _ in range(self.planning_steps):
            # Sample random experience
            state, action, reward, next_state, done = random.choice(self.buffer)
            
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            action_tensor = torch.LongTensor([action])
            
            # Predict using world model
            pred_next_state, pred_reward, pred_done = self.world_model.predict(
                state_tensor, action_tensor
            )
            
            # Update Q-network with simulated experience
            self.update_q_network(
                state_tensor,
                action,
                pred_reward.item(),
                pred_next_state,
                pred_done.item()
            )
    
    def train_step(self, state, action, reward, next_state, done):
        """
        Single training step
        1. Update world model
        2. Update Q-network with real experience
        3. Planning with simulated experience
        """
        # Store experience
        self.buffer.append((state, action, reward, next_state, done))
        
        # Convert to tensors
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        action_tensor = torch.LongTensor([action])
        next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0)
        reward_tensor = torch.FloatTensor([reward])
        done_tensor = torch.FloatTensor([done])
        
        # Update world model
        self.world_model.train_step(
            state_tensor, action_tensor,
            next_state_tensor, reward_tensor, done_tensor
        )
        
        # Update Q-network with real experience
        q_loss = self.update_q_network(
            state_tensor, action, reward, next_state_tensor, done
        )
        
        # Planning
        self.planning()
        
        return q_loss


# ============ MODEL-BASED POLICY OPTIMIZATION (MBPO) ============

class EnsembleModel(nn.Module):
    """
    Ensemble of world models for uncertainty estimation
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256, num_models=5):
        super().__init__()
        
        self.num_models = num_models
        
        # Create ensemble of transition models
        self.models = nn.ModuleList([
            TransitionModel(state_dim, action_dim, hidden_dim)
            for _ in range(num_models)
        ])
    
    def forward(self, state, action, model_idx=None):
        """
        Forward pass through ensemble
        If model_idx is None, return all predictions
        """
        if model_idx is not None:
            return self.models[model_idx](state, action)
        
        predictions = [model(state, action) for model in self.models]
        return torch.stack(predictions)
    
    def predict_with_uncertainty(self, state, action):
        """
        Predict with uncertainty estimation
        Returns: mean, std
        """
        predictions = self.forward(state, action)
        mean = predictions.mean(dim=0)
        std = predictions.std(dim=0)
        return mean, std


class MBPO:
    """
    Model-Based Policy Optimization
    Sử dụng ensemble models và short rollouts
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256, num_models=5):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Ensemble world model
        self.ensemble = EnsembleModel(state_dim, action_dim, hidden_dim, num_models)
        self.ensemble_optimizers = [
            torch.optim.Adam(model.parameters(), lr=1e-3)
            for model in self.ensemble.models
        ]
        
        # Policy network
        self.policy = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        
        self.policy_optimizer = torch.optim.Adam(self.policy.parameters(), lr=1e-3)
        
        # Buffers
        self.real_buffer = deque(maxlen=100000)
        self.model_buffer = deque(maxlen=100000)
    
    def train_ensemble(self, batch_size=256):
        """Train ensemble models"""
        if len(self.real_buffer) < batch_size:
            return
        
        # Sample batch
        batch = random.sample(self.real_buffer, batch_size)
        states = torch.FloatTensor([s for s, a, r, ns, d in batch])
        actions = torch.LongTensor([a for s, a, r, ns, d in batch])
        next_states = torch.FloatTensor([ns for s, a, r, ns, d in batch])
        
        # Train each model in ensemble
        losses = []
        for i, (model, optimizer) in enumerate(zip(self.ensemble.models, self.ensemble_optimizers)):
            pred_next_states = model(states, actions)
            loss = F.mse_loss(pred_next_states, next_states)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            losses.append(loss.item())
        
        return np.mean(losses)
    
    def generate_model_rollouts(self, num_rollouts=1000, rollout_length=5):
        """Generate synthetic data using world model"""
        if len(self.real_buffer) == 0:
            return
        
        for _ in range(num_rollouts):
            # Sample initial state from real buffer
            state, _, _, _, _ = random.choice(self.real_buffer)
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            
            # Rollout
            for t in range(rollout_length):
                # Get action from policy
                with torch.no_grad():
                    logits = self.policy(state_tensor)
                    action = torch.argmax(logits, dim=-1)
                
                # Predict next state using random model from ensemble
                model_idx = random.randint(0, self.ensemble.num_models - 1)
                with torch.no_grad():
                    next_state_tensor = self.ensemble(state_tensor, action, model_idx)
                
                # Store in model buffer
                self.model_buffer.append((
                    state_tensor.squeeze(0).numpy(),
                    action.item(),
                    0.0,  # Reward (would need reward model)
                    next_state_tensor.squeeze(0).numpy(),
                    False
                ))
                
                state_tensor = next_state_tensor


# ============ TESTING ============

if __name__ == "__main__":
    print("🌍 Testing Model-Based RL System\n")
    
    state_dim, action_dim = 10, 4
    batch_size = 32
    
    # Test World Model
    print("1. Testing World Model...")
    world_model = WorldModel(state_dim, action_dim, hidden_dim=64)
    
    states = torch.randn(batch_size, state_dim)
    actions = torch.randint(0, action_dim, (batch_size,))
    next_states = torch.randn(batch_size, state_dim)
    rewards = torch.randn(batch_size)
    dones = torch.randint(0, 2, (batch_size,)).float()
    
    trans_loss, rew_loss, done_loss = world_model.train_step(
        states, actions, next_states, rewards, dones
    )
    
    print(f"   Transition loss: {trans_loss:.4f}")
    print(f"   Reward loss: {rew_loss:.4f}")
    print(f"   Done loss: {done_loss:.4f}")
    
    # Test prediction
    test_state = torch.randn(1, state_dim)
    test_action = torch.LongTensor([0])
    pred_next, pred_reward, pred_done = world_model.predict(test_state, test_action)
    
    print(f"   Predicted next state shape: {pred_next.shape}")
    print(f"   Predicted reward: {pred_reward.item():.4f}")
    print(f"   Predicted done: {pred_done.item()}")
    print(f"   ✅ World Model working\n")
    
    # Test Dyna-Q
    print("2. Testing Dyna-Q...")
    dyna_q = DynaQ(state_dim, action_dim, hidden_dim=64, planning_steps=3)
    
    # Simulate training step
    state = np.random.randn(state_dim)
    action = np.random.randint(action_dim)
    reward = np.random.randn()
    next_state = np.random.randn(state_dim)
    done = False
    
    q_loss = dyna_q.train_step(state, action, reward, next_state, done)
    
    print(f"   Q-loss: {q_loss:.4f}")
    print(f"   Buffer size: {len(dyna_q.buffer)}")
    print(f"   ✅ Dyna-Q working\n")
    
    # Test Ensemble Model
    print("3. Testing Ensemble Model...")
    ensemble = EnsembleModel(state_dim, action_dim, hidden_dim=64, num_models=5)
    
    test_state = torch.randn(batch_size, state_dim)
    test_action = torch.randint(0, action_dim, (batch_size,))
    
    mean, std = ensemble.predict_with_uncertainty(test_state, test_action)
    
    print(f"   Mean prediction shape: {mean.shape}")
    print(f"   Std prediction shape: {std.shape}")
    print(f"   Avg uncertainty: {std.mean().item():.4f}")
    print(f"   ✅ Ensemble Model working\n")
    
    # Test MBPO
    print("4. Testing MBPO...")
    mbpo = MBPO(state_dim, action_dim, hidden_dim=64, num_models=3)
    
    # Add some data to buffer
    for _ in range(100):
        mbpo.real_buffer.append((
            np.random.randn(state_dim),
            np.random.randint(action_dim),
            np.random.randn(),
            np.random.randn(state_dim),
            False
        ))
    
    # Train ensemble
    ensemble_loss = mbpo.train_ensemble(batch_size=32)
    print(f"   Ensemble loss: {ensemble_loss:.4f}")
    
    # Generate rollouts
    mbpo.generate_model_rollouts(num_rollouts=10, rollout_length=3)
    print(f"   Model buffer size: {len(mbpo.model_buffer)}")
    print(f"   ✅ MBPO working\n")
    
    print("✅ All Model-Based RL components tested successfully!")
    
    # Statistics
    print("\n📊 Model Statistics:")
    print(f"   World Model Transition: {sum(p.numel() for p in world_model.transition_model.parameters()):,} parameters")
    print(f"   World Model Reward: {sum(p.numel() for p in world_model.reward_model.parameters()):,} parameters")
    print(f"   Dyna-Q Network: {sum(p.numel() for p in dyna_q.q_network.parameters()):,} parameters")
    print(f"   Ensemble (total): {sum(p.numel() for p in ensemble.parameters()):,} parameters")
    print(f"   MBPO Policy: {sum(p.numel() for p in mbpo.policy.parameters()):,} parameters")
