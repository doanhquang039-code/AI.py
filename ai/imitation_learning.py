"""
Imitation Learning for Reinforcement Learning
Học từ expert demonstrations: Behavioral Cloning, Inverse RL, GAIL, DAgger
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional
from collections import deque
import random


# ============ BEHAVIORAL CLONING ============

class BehavioralCloningAgent(nn.Module):
    """
    Behavioral Cloning - Supervised learning from expert demonstrations
    Học trực tiếp từ expert actions
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super().__init__()
        
        self.policy = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(self, state):
        return self.policy(state)
    
    def get_action(self, state, deterministic=False):
        """Get action from policy"""
        logits = self.forward(state)
        
        if deterministic:
            action = torch.argmax(logits, dim=-1)
        else:
            probs = F.softmax(logits, dim=-1)
            action = torch.multinomial(probs, 1).squeeze(-1)
        
        return action


class BehavioralCloningTrainer:
    """Trainer for Behavioral Cloning"""
    def __init__(self, agent, learning_rate=1e-3):
        self.agent = agent
        self.optimizer = torch.optim.Adam(agent.parameters(), lr=learning_rate)
        self.loss_history = []
    
    def train_step(self, states, actions):
        """
        Train on batch of expert demonstrations
        Args:
            states: (batch_size, state_dim)
            actions: (batch_size,) - expert actions
        """
        # Forward pass
        logits = self.agent(states)
        
        # Compute cross-entropy loss
        loss = F.cross_entropy(logits, actions)
        
        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        self.loss_history.append(loss.item())
        
        return loss.item()
    
    def train(self, expert_data, num_epochs=100, batch_size=64):
        """
        Train on expert demonstrations
        Args:
            expert_data: List of (state, action) tuples
        """
        print(f"🎓 Training Behavioral Cloning on {len(expert_data)} demonstrations\n")
        
        states = torch.stack([torch.FloatTensor(s) for s, a in expert_data])
        actions = torch.LongTensor([a for s, a in expert_data])
        
        dataset = torch.utils.data.TensorDataset(states, actions)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        for epoch in range(num_epochs):
            epoch_loss = 0
            
            for batch_states, batch_actions in dataloader:
                loss = self.train_step(batch_states, batch_actions)
                epoch_loss += loss
            
            if epoch % 10 == 0:
                avg_loss = epoch_loss / len(dataloader)
                print(f"Epoch {epoch}: Loss = {avg_loss:.4f}")
        
        print(f"\n✅ Training complete!")


# ============ INVERSE REINFORCEMENT LEARNING ============

class RewardNetwork(nn.Module):
    """Neural network to learn reward function"""
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
        """
        Compute reward for state-action pair
        """
        # One-hot encode action if needed
        if len(action.shape) == 1:
            action_onehot = F.one_hot(action, num_classes=self.network[0].in_features - state.shape[-1])
            action = action_onehot.float()
        
        x = torch.cat([state, action], dim=-1)
        reward = self.network(x)
        return reward


class InverseRL:
    """
    Inverse Reinforcement Learning
    Học reward function từ expert demonstrations
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Reward network
        self.reward_net = RewardNetwork(state_dim, action_dim, hidden_dim)
        self.reward_optimizer = torch.optim.Adam(self.reward_net.parameters(), lr=1e-3)
        
        # Policy network
        self.policy_net = BehavioralCloningAgent(state_dim, action_dim, hidden_dim)
        self.policy_optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=1e-3)
    
    def compute_expert_reward(self, expert_states, expert_actions):
        """Compute rewards for expert demonstrations"""
        return self.reward_net(expert_states, expert_actions)
    
    def compute_policy_reward(self, states):
        """Compute expected reward under current policy"""
        actions = self.policy_net.get_action(states)
        return self.reward_net(states, actions)
    
    def train_step(self, expert_states, expert_actions, policy_states):
        """
        Train reward and policy networks
        """
        # Compute rewards
        expert_rewards = self.compute_expert_reward(expert_states, expert_actions)
        policy_rewards = self.compute_policy_reward(policy_states)
        
        # Reward loss: maximize expert rewards, minimize policy rewards
        reward_loss = -expert_rewards.mean() + policy_rewards.mean()
        
        # Update reward network
        self.reward_optimizer.zero_grad()
        reward_loss.backward()
        self.reward_optimizer.step()
        
        # Update policy to maximize learned rewards
        policy_actions = self.policy_net.get_action(policy_states)
        policy_rewards = self.reward_net(policy_states, policy_actions)
        policy_loss = -policy_rewards.mean()
        
        self.policy_optimizer.zero_grad()
        policy_loss.backward()
        self.policy_optimizer.step()
        
        return reward_loss.item(), policy_loss.item()


# ============ GAIL (Generative Adversarial Imitation Learning) ============

class Discriminator(nn.Module):
    """
    Discriminator network for GAIL
    Phân biệt expert vs policy trajectories
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
        """
        Output probability that (state, action) is from expert
        """
        if len(action.shape) == 1:
            action_onehot = F.one_hot(action, num_classes=self.network[0].in_features - state.shape[-1])
            action = action_onehot.float()
        
        x = torch.cat([state, action], dim=-1)
        return self.network(x)


class GAIL:
    """
    Generative Adversarial Imitation Learning
    Sử dụng GAN để học từ expert
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Generator (Policy)
        self.policy = BehavioralCloningAgent(state_dim, action_dim, hidden_dim)
        self.policy_optimizer = torch.optim.Adam(self.policy.parameters(), lr=1e-4)
        
        # Discriminator
        self.discriminator = Discriminator(state_dim, action_dim, hidden_dim)
        self.discriminator_optimizer = torch.optim.Adam(self.discriminator.parameters(), lr=1e-4)
        
        self.training_stats = {
            'discriminator_loss': [],
            'policy_loss': [],
            'expert_accuracy': [],
            'policy_accuracy': []
        }
    
    def train_discriminator(self, expert_states, expert_actions, policy_states, policy_actions):
        """
        Train discriminator to distinguish expert from policy
        """
        # Expert predictions (should be 1)
        expert_pred = self.discriminator(expert_states, expert_actions)
        expert_loss = F.binary_cross_entropy(expert_pred, torch.ones_like(expert_pred))
        
        # Policy predictions (should be 0)
        policy_pred = self.discriminator(policy_states, policy_actions)
        policy_loss = F.binary_cross_entropy(policy_pred, torch.zeros_like(policy_pred))
        
        # Total discriminator loss
        disc_loss = expert_loss + policy_loss
        
        # Update discriminator
        self.discriminator_optimizer.zero_grad()
        disc_loss.backward()
        self.discriminator_optimizer.step()
        
        # Calculate accuracies
        expert_acc = (expert_pred > 0.5).float().mean().item()
        policy_acc = (policy_pred < 0.5).float().mean().item()
        
        return disc_loss.item(), expert_acc, policy_acc
    
    def train_policy(self, states):
        """
        Train policy to fool discriminator
        """
        # Get actions from policy
        actions = self.policy.get_action(states)
        
        # Get discriminator predictions
        disc_pred = self.discriminator(states, actions)
        
        # Policy loss: fool discriminator (want disc_pred to be 1)
        policy_loss = F.binary_cross_entropy(disc_pred, torch.ones_like(disc_pred))
        
        # Update policy
        self.policy_optimizer.zero_grad()
        policy_loss.backward()
        self.policy_optimizer.step()
        
        return policy_loss.item()
    
    def train_step(self, expert_batch, policy_batch):
        """
        Single training step
        """
        expert_states, expert_actions = expert_batch
        policy_states, policy_actions = policy_batch
        
        # Train discriminator
        disc_loss, expert_acc, policy_acc = self.train_discriminator(
            expert_states, expert_actions,
            policy_states, policy_actions
        )
        
        # Train policy
        policy_loss = self.train_policy(policy_states)
        
        # Record stats
        self.training_stats['discriminator_loss'].append(disc_loss)
        self.training_stats['policy_loss'].append(policy_loss)
        self.training_stats['expert_accuracy'].append(expert_acc)
        self.training_stats['policy_accuracy'].append(policy_acc)
        
        return disc_loss, policy_loss, expert_acc, policy_acc


# ============ DAGGER (Dataset Aggregation) ============

class DAgger:
    """
    DAgger - Dataset Aggregation
    Iteratively collect data under learned policy, get expert labels
    """
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        self.policy = BehavioralCloningAgent(state_dim, action_dim, hidden_dim)
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=1e-3)
        
        self.dataset = []
        self.beta = 1.0  # Probability of using expert policy
        self.beta_decay = 0.9
    
    def collect_data(self, env, expert_policy, num_episodes=10):
        """
        Collect data by rolling out mixture of expert and learned policy
        """
        new_data = []
        
        for episode in range(num_episodes):
            state = env.reset()
            done = False
            
            while not done:
                # Decide whether to use expert or learned policy
                if random.random() < self.beta:
                    # Use expert
                    action = expert_policy(state)
                else:
                    # Use learned policy
                    with torch.no_grad():
                        state_tensor = torch.FloatTensor(state).unsqueeze(0)
                        action = self.policy.get_action(state_tensor, deterministic=True).item()
                
                # Get expert label for this state
                expert_action = expert_policy(state)
                
                # Store (state, expert_action)
                new_data.append((state.copy(), expert_action))
                
                # Take action
                next_state, reward, done, _ = env.step(action)
                state = next_state
        
        # Add to dataset
        self.dataset.extend(new_data)
        
        # Decay beta
        self.beta *= self.beta_decay
        
        return len(new_data)
    
    def train(self, num_epochs=10, batch_size=64):
        """Train on aggregated dataset"""
        if len(self.dataset) == 0:
            return
        
        states = torch.stack([torch.FloatTensor(s) for s, a in self.dataset])
        actions = torch.LongTensor([a for s, a in self.dataset])
        
        dataset = torch.utils.data.TensorDataset(states, actions)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        for epoch in range(num_epochs):
            for batch_states, batch_actions in dataloader:
                logits = self.policy(batch_states)
                loss = F.cross_entropy(logits, batch_actions)
                
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()


# ============ EXPERT DEMONSTRATION BUFFER ============

class ExpertBuffer:
    """Buffer for storing expert demonstrations"""
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def add(self, state, action, next_state, reward, done):
        """Add demonstration"""
        self.buffer.append((state, action, next_state, reward, done))
    
    def sample(self, batch_size):
        """Sample batch of demonstrations"""
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        
        states = torch.FloatTensor([s for s, a, ns, r, d in batch])
        actions = torch.LongTensor([a for s, a, ns, r, d in batch])
        next_states = torch.FloatTensor([ns for s, a, ns, r, d in batch])
        rewards = torch.FloatTensor([r for s, a, ns, r, d in batch])
        dones = torch.FloatTensor([d for s, a, ns, r, d in batch])
        
        return states, actions, next_states, rewards, dones
    
    def __len__(self):
        return len(self.buffer)


# ============ TESTING ============

if __name__ == "__main__":
    print("🎓 Testing Imitation Learning System\n")
    
    state_dim, action_dim = 10, 4
    batch_size = 32
    
    # Test Behavioral Cloning
    print("1. Testing Behavioral Cloning...")
    bc_agent = BehavioralCloningAgent(state_dim, action_dim, hidden_dim=64)
    bc_trainer = BehavioralCloningTrainer(bc_agent, learning_rate=1e-3)
    
    # Generate fake expert data
    expert_data = [
        (np.random.randn(state_dim), np.random.randint(action_dim))
        for _ in range(100)
    ]
    
    # Train
    bc_trainer.train(expert_data, num_epochs=10, batch_size=32)
    
    # Test inference
    test_state = torch.randn(1, state_dim)
    action = bc_agent.get_action(test_state)
    print(f"   Test action: {action.item()}")
    print(f"   ✅ Behavioral Cloning working\n")
    
    # Test Inverse RL
    print("2. Testing Inverse RL...")
    irl = InverseRL(state_dim, action_dim, hidden_dim=64)
    
    expert_states = torch.randn(batch_size, state_dim)
    expert_actions = torch.randint(0, action_dim, (batch_size,))
    policy_states = torch.randn(batch_size, state_dim)
    
    reward_loss, policy_loss = irl.train_step(expert_states, expert_actions, policy_states)
    print(f"   Reward loss: {reward_loss:.4f}")
    print(f"   Policy loss: {policy_loss:.4f}")
    print(f"   ✅ Inverse RL working\n")
    
    # Test GAIL
    print("3. Testing GAIL...")
    gail = GAIL(state_dim, action_dim, hidden_dim=64)
    
    expert_batch = (expert_states, expert_actions)
    policy_actions = torch.randint(0, action_dim, (batch_size,))
    policy_batch = (policy_states, policy_actions)
    
    disc_loss, pol_loss, exp_acc, pol_acc = gail.train_step(expert_batch, policy_batch)
    print(f"   Discriminator loss: {disc_loss:.4f}")
    print(f"   Policy loss: {pol_loss:.4f}")
    print(f"   Expert accuracy: {exp_acc:.2%}")
    print(f"   Policy accuracy: {pol_acc:.2%}")
    print(f"   ✅ GAIL working\n")
    
    # Test DAgger
    print("4. Testing DAgger...")
    dagger = DAgger(state_dim, action_dim, hidden_dim=64)
    
    # Add some fake data
    for _ in range(50):
        state = np.random.randn(state_dim)
        action = np.random.randint(action_dim)
        dagger.dataset.append((state, action))
    
    dagger.train(num_epochs=5, batch_size=16)
    print(f"   Dataset size: {len(dagger.dataset)}")
    print(f"   Beta: {dagger.beta:.3f}")
    print(f"   ✅ DAgger working\n")
    
    # Test Expert Buffer
    print("5. Testing Expert Buffer...")
    buffer = ExpertBuffer(capacity=1000)
    
    for _ in range(100):
        buffer.add(
            np.random.randn(state_dim),
            np.random.randint(action_dim),
            np.random.randn(state_dim),
            np.random.randn(),
            False
        )
    
    batch = buffer.sample(32)
    print(f"   Buffer size: {len(buffer)}")
    print(f"   Batch states shape: {batch[0].shape}")
    print(f"   ✅ Expert Buffer working\n")
    
    print("✅ All Imitation Learning components tested successfully!")
    
    # Statistics
    print("\n📊 Model Statistics:")
    print(f"   BC Agent: {sum(p.numel() for p in bc_agent.parameters()):,} parameters")
    print(f"   IRL Reward Net: {sum(p.numel() for p in irl.reward_net.parameters()):,} parameters")
    print(f"   GAIL Policy: {sum(p.numel() for p in gail.policy.parameters()):,} parameters")
    print(f"   GAIL Discriminator: {sum(p.numel() for p in gail.discriminator.parameters()):,} parameters")
