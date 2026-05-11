"""
Multi-Task Learning for Reinforcement Learning
Học nhiều tasks cùng lúc với shared representations
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


# ============ MULTI-TASK NETWORK ============

class SharedEncoder(nn.Module):
    """Shared encoder for all tasks"""
    def __init__(self, input_dim, hidden_dim, num_layers=3):
        super().__init__()
        
        layers = []
        layers.append(nn.Linear(input_dim, hidden_dim))
        layers.append(nn.ReLU())
        
        for _ in range(num_layers - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.ReLU())
        
        self.encoder = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.encoder(x)


class TaskSpecificHead(nn.Module):
    """Task-specific head"""
    def __init__(self, input_dim, output_dim, hidden_dim=128):
        super().__init__()
        
        self.head = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, x):
        return self.head(x)


class MultiTaskAgent(nn.Module):
    """
    Multi-Task RL Agent
    Shared encoder + Task-specific heads
    """
    def __init__(self, state_dim, task_configs: Dict[str, int], hidden_dim=256):
        """
        Args:
            state_dim: State dimension
            task_configs: Dict mapping task_name -> action_dim
            hidden_dim: Hidden dimension
        """
        super().__init__()
        
        self.task_names = list(task_configs.keys())
        self.hidden_dim = hidden_dim
        
        # Shared encoder
        self.shared_encoder = SharedEncoder(state_dim, hidden_dim, num_layers=3)
        
        # Task-specific policy heads
        self.policy_heads = nn.ModuleDict({
            task_name: TaskSpecificHead(hidden_dim, action_dim)
            for task_name, action_dim in task_configs.items()
        })
        
        # Task-specific value heads
        self.value_heads = nn.ModuleDict({
            task_name: TaskSpecificHead(hidden_dim, 1)
            for task_name in task_configs.keys()
        })
    
    def forward(self, state, task_name):
        """
        Forward pass for specific task
        """
        # Shared encoding
        shared_features = self.shared_encoder(state)
        
        # Task-specific outputs
        policy_logits = self.policy_heads[task_name](shared_features)
        value = self.value_heads[task_name](shared_features)
        
        return policy_logits, value, shared_features
    
    def get_action(self, state, task_name):
        """Get action for specific task"""
        policy_logits, value, _ = self.forward(state, task_name)
        probs = F.softmax(policy_logits, dim=-1)
        action = torch.multinomial(probs, 1)
        return action, probs, value


# ============ HARD PARAMETER SHARING ============

class HardParameterSharing(nn.Module):
    """
    Hard parameter sharing architecture
    Nhiều tasks share toàn bộ hidden layers
    """
    def __init__(self, state_dim, task_configs: Dict[str, int], hidden_dim=256, num_shared_layers=4):
        super().__init__()
        
        self.task_names = list(task_configs.keys())
        
        # Shared layers
        shared_layers = []
        shared_layers.append(nn.Linear(state_dim, hidden_dim))
        shared_layers.append(nn.ReLU())
        
        for _ in range(num_shared_layers - 1):
            shared_layers.append(nn.Linear(hidden_dim, hidden_dim))
            shared_layers.append(nn.ReLU())
        
        self.shared_layers = nn.Sequential(*shared_layers)
        
        # Task-specific output layers
        self.task_outputs = nn.ModuleDict({
            task_name: nn.Linear(hidden_dim, action_dim)
            for task_name, action_dim in task_configs.items()
        })
    
    def forward(self, state, task_name):
        shared_features = self.shared_layers(state)
        output = self.task_outputs[task_name](shared_features)
        return output


# ============ SOFT PARAMETER SHARING ============

class TaskSpecificNetwork(nn.Module):
    """Task-specific network for soft parameter sharing"""
    def __init__(self, input_dim, output_dim, hidden_dim=256):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, x):
        return self.network(x)
    
    def get_parameters(self):
        """Get flattened parameters"""
        return torch.cat([p.flatten() for p in self.parameters()])


class SoftParameterSharing(nn.Module):
    """
    Soft parameter sharing với regularization
    Mỗi task có network riêng nhưng được encourage to be similar
    """
    def __init__(self, state_dim, task_configs: Dict[str, int], hidden_dim=256, l2_reg=0.01):
        super().__init__()
        
        self.task_names = list(task_configs.keys())
        self.l2_reg = l2_reg
        
        # Task-specific networks
        self.task_networks = nn.ModuleDict({
            task_name: TaskSpecificNetwork(state_dim, action_dim, hidden_dim)
            for task_name, action_dim in task_configs.items()
        })
    
    def forward(self, state, task_name):
        return self.task_networks[task_name](state)
    
    def compute_regularization_loss(self):
        """
        Compute L2 regularization between task networks
        Encourage parameters to be similar
        """
        if len(self.task_names) < 2:
            return torch.tensor(0.0)
        
        reg_loss = 0.0
        count = 0
        
        # Compare all pairs of tasks
        for i, task1 in enumerate(self.task_names):
            for task2 in self.task_names[i+1:]:
                params1 = self.task_networks[task1].get_parameters()
                params2 = self.task_networks[task2].get_parameters()
                
                reg_loss += F.mse_loss(params1, params2)
                count += 1
        
        return self.l2_reg * reg_loss / count if count > 0 else torch.tensor(0.0)


# ============ CROSS-STITCH NETWORKS ============

class CrossStitchUnit(nn.Module):
    """Cross-stitch unit for combining task features"""
    def __init__(self, num_tasks):
        super().__init__()
        
        # Learnable combination matrix
        self.alpha = nn.Parameter(torch.eye(num_tasks))
    
    def forward(self, task_features: List[torch.Tensor]):
        """
        Combine features from different tasks
        Args:
            task_features: List of tensors (batch_size, feature_dim)
        """
        # Stack features
        stacked = torch.stack(task_features, dim=0)  # (num_tasks, batch_size, feature_dim)
        
        # Apply cross-stitch
        combined = torch.einsum('ij,jbf->ibf', self.alpha, stacked)
        
        # Unstack
        return [combined[i] for i in range(len(task_features))]


class CrossStitchNetwork(nn.Module):
    """
    Cross-Stitch Networks
    Cho phép tasks share information ở mỗi layer
    """
    def __init__(self, state_dim, task_configs: Dict[str, int], hidden_dim=256, num_layers=4):
        super().__init__()
        
        self.task_names = list(task_configs.keys())
        self.num_tasks = len(self.task_names)
        self.num_layers = num_layers
        
        # Task-specific layers for each layer depth
        self.task_layers = nn.ModuleList()
        for layer_idx in range(num_layers):
            input_dim = state_dim if layer_idx == 0 else hidden_dim
            
            layer_dict = nn.ModuleDict({
                task_name: nn.Sequential(
                    nn.Linear(input_dim, hidden_dim),
                    nn.ReLU()
                )
                for task_name in self.task_names
            })
            self.task_layers.append(layer_dict)
        
        # Cross-stitch units between layers
        self.cross_stitch_units = nn.ModuleList([
            CrossStitchUnit(self.num_tasks)
            for _ in range(num_layers - 1)
        ])
        
        # Output heads
        self.output_heads = nn.ModuleDict({
            task_name: nn.Linear(hidden_dim, action_dim)
            for task_name, action_dim in task_configs.items()
        })
    
    def forward(self, state, task_name=None):
        """
        Forward pass
        If task_name is None, return outputs for all tasks
        """
        # Initial features for each task
        task_features = {
            name: state for name in self.task_names
        }
        
        # Pass through layers with cross-stitch
        for layer_idx in range(self.num_layers):
            # Apply task-specific layers
            new_features = {}
            for name in self.task_names:
                new_features[name] = self.task_layers[layer_idx][name](task_features[name])
            
            # Apply cross-stitch (except after last layer)
            if layer_idx < self.num_layers - 1:
                feature_list = [new_features[name] for name in self.task_names]
                combined_list = self.cross_stitch_units[layer_idx](feature_list)
                
                for i, name in enumerate(self.task_names):
                    new_features[name] = combined_list[i]
            
            task_features = new_features
        
        # Output heads
        outputs = {
            name: self.output_heads[name](task_features[name])
            for name in self.task_names
        }
        
        if task_name is not None:
            return outputs[task_name]
        return outputs


# ============ MULTI-TASK TRAINER ============

class MultiTaskTrainer:
    """
    Trainer for multi-task learning
    """
    def __init__(self, agent, task_names: List[str], optimizer):
        self.agent = agent
        self.task_names = task_names
        self.optimizer = optimizer
        
        # Statistics per task
        self.task_stats = {
            task: {
                'episodes': 0,
                'total_reward': 0,
                'avg_reward': 0,
                'losses': []
            }
            for task in task_names
        }
    
    def train_step(self, task_name, batch):
        """
        Train on batch for specific task
        """
        states, actions, rewards, next_states, dones = batch
        
        # Forward pass
        policy_logits, values, _ = self.agent(states, task_name)
        
        # Compute loss (example: policy gradient)
        log_probs = F.log_softmax(policy_logits, dim=-1)
        selected_log_probs = log_probs.gather(1, actions.unsqueeze(1))
        
        policy_loss = -(selected_log_probs * rewards.unsqueeze(1)).mean()
        value_loss = F.mse_loss(values, rewards.unsqueeze(1))
        
        total_loss = policy_loss + 0.5 * value_loss
        
        # Backward pass
        self.optimizer.zero_grad()
        total_loss.backward()
        self.optimizer.step()
        
        # Record statistics
        self.task_stats[task_name]['losses'].append(total_loss.item())
        
        return total_loss.item()
    
    def train_multi_task(self, task_batches: Dict[str, Tuple], task_weights: Optional[Dict[str, float]] = None):
        """
        Train on multiple tasks simultaneously
        Args:
            task_batches: Dict mapping task_name -> batch
            task_weights: Optional weights for each task
        """
        if task_weights is None:
            task_weights = {task: 1.0 for task in self.task_names}
        
        total_loss = 0.0
        
        for task_name, batch in task_batches.items():
            loss = self.train_step(task_name, batch)
            total_loss += task_weights[task_name] * loss
        
        return total_loss
    
    def get_task_statistics(self):
        """Get statistics for all tasks"""
        stats = {}
        for task_name, task_stat in self.task_stats.items():
            if len(task_stat['losses']) > 0:
                stats[task_name] = {
                    'episodes': task_stat['episodes'],
                    'avg_reward': task_stat['avg_reward'],
                    'avg_loss': np.mean(task_stat['losses'][-100:])
                }
        return stats


# ============ TASK SCHEDULER ============

class TaskScheduler:
    """
    Schedule which tasks to train on
    """
    def __init__(self, task_names: List[str], strategy='round_robin'):
        self.task_names = task_names
        self.strategy = strategy
        self.current_idx = 0
        
        self.task_priorities = {task: 1.0 for task in task_names}
    
    def get_next_task(self) -> str:
        """Get next task to train on"""
        if self.strategy == 'round_robin':
            task = self.task_names[self.current_idx]
            self.current_idx = (self.current_idx + 1) % len(self.task_names)
            return task
        
        elif self.strategy == 'random':
            return np.random.choice(self.task_names)
        
        elif self.strategy == 'priority':
            # Sample based on priorities
            probs = np.array([self.task_priorities[t] for t in self.task_names])
            probs = probs / probs.sum()
            return np.random.choice(self.task_names, p=probs)
        
        else:
            return self.task_names[0]
    
    def update_priority(self, task_name: str, priority: float):
        """Update task priority"""
        self.task_priorities[task_name] = priority


# ============ TESTING ============

if __name__ == "__main__":
    print("🎯 Testing Multi-Task Learning System\n")
    
    # Test Multi-Task Agent
    print("1. Testing Multi-Task Agent...")
    state_dim = 10
    task_configs = {
        'navigation': 4,
        'manipulation': 6,
        'communication': 3
    }
    
    agent = MultiTaskAgent(state_dim, task_configs, hidden_dim=64)
    
    state = torch.randn(4, state_dim)
    
    for task_name in task_configs.keys():
        policy, value, features = agent(state, task_name)
        print(f"   Task '{task_name}': policy shape {policy.shape}, value shape {value.shape}")
    
    print(f"   ✅ Multi-Task Agent working\n")
    
    # Test Hard Parameter Sharing
    print("2. Testing Hard Parameter Sharing...")
    hard_agent = HardParameterSharing(state_dim, task_configs, hidden_dim=64)
    
    for task_name in task_configs.keys():
        output = hard_agent(state, task_name)
        print(f"   Task '{task_name}': output shape {output.shape}")
    
    print(f"   ✅ Hard Parameter Sharing working\n")
    
    # Test Soft Parameter Sharing
    print("3. Testing Soft Parameter Sharing...")
    soft_agent = SoftParameterSharing(state_dim, task_configs, hidden_dim=64)
    
    reg_loss = soft_agent.compute_regularization_loss()
    print(f"   Regularization loss: {reg_loss.item():.4f}")
    print(f"   ✅ Soft Parameter Sharing working\n")
    
    # Test Cross-Stitch Network
    print("4. Testing Cross-Stitch Network...")
    cross_agent = CrossStitchNetwork(state_dim, task_configs, hidden_dim=64, num_layers=3)
    
    outputs = cross_agent(state)
    for task_name, output in outputs.items():
        print(f"   Task '{task_name}': output shape {output.shape}")
    
    print(f"   ✅ Cross-Stitch Network working\n")
    
    # Test Task Scheduler
    print("5. Testing Task Scheduler...")
    scheduler = TaskScheduler(list(task_configs.keys()), strategy='round_robin')
    
    tasks = [scheduler.get_next_task() for _ in range(6)]
    print(f"   Task sequence: {tasks}")
    print(f"   ✅ Task Scheduler working\n")
    
    print("✅ All Multi-Task Learning components tested successfully!")
    
    # Statistics
    print("\n📊 Model Statistics:")
    print(f"   Multi-Task Agent: {sum(p.numel() for p in agent.parameters()):,} parameters")
    print(f"   Hard Sharing: {sum(p.numel() for p in hard_agent.parameters()):,} parameters")
    print(f"   Soft Sharing: {sum(p.numel() for p in soft_agent.parameters()):,} parameters")
    print(f"   Cross-Stitch: {sum(p.numel() for p in cross_agent.parameters()):,} parameters")
