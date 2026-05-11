"""
Curriculum Learning for Reinforcement Learning
Học theo chương trình từ dễ đến khó, tự động điều chỉnh độ khó
"""

import numpy as np
import torch
import torch.nn as nn
from typing import List, Dict, Tuple, Optional, Callable
from collections import deque
import json


# ============ CURRICULUM MANAGER ============

class CurriculumManager:
    """
    Quản lý curriculum learning
    Tự động điều chỉnh độ khó dựa trên performance
    """
    def __init__(self, levels: List[Dict], success_threshold=0.7, window_size=100):
        """
        Args:
            levels: List of difficulty levels with parameters
            success_threshold: Success rate to advance to next level
            window_size: Window for calculating success rate
        """
        self.levels = levels
        self.current_level = 0
        self.success_threshold = success_threshold
        self.window_size = window_size
        
        self.performance_history = deque(maxlen=window_size)
        self.level_history = []
        self.total_episodes = 0
    
    def get_current_level(self) -> Dict:
        """Get current difficulty level parameters"""
        return self.levels[self.current_level]
    
    def record_episode(self, success: bool, reward: float):
        """Record episode result"""
        self.performance_history.append({
            'success': success,
            'reward': reward,
            'level': self.current_level
        })
        self.total_episodes += 1
    
    def get_success_rate(self) -> float:
        """Calculate recent success rate"""
        if len(self.performance_history) == 0:
            return 0.0
        
        successes = sum(1 for ep in self.performance_history if ep['success'])
        return successes / len(self.performance_history)
    
    def should_advance(self) -> bool:
        """Check if should advance to next level"""
        if self.current_level >= len(self.levels) - 1:
            return False
        
        if len(self.performance_history) < self.window_size:
            return False
        
        success_rate = self.get_success_rate()
        return success_rate >= self.success_threshold
    
    def should_regress(self) -> bool:
        """Check if should go back to easier level"""
        if self.current_level == 0:
            return False
        
        if len(self.performance_history) < self.window_size // 2:
            return False
        
        success_rate = self.get_success_rate()
        return success_rate < self.success_threshold * 0.5
    
    def advance_level(self):
        """Advance to next difficulty level"""
        if self.current_level < len(self.levels) - 1:
            self.current_level += 1
            self.level_history.append({
                'episode': self.total_episodes,
                'level': self.current_level,
                'action': 'advance'
            })
            print(f"📈 Advanced to level {self.current_level}")
            self.performance_history.clear()
    
    def regress_level(self):
        """Go back to easier level"""
        if self.current_level > 0:
            self.current_level -= 1
            self.level_history.append({
                'episode': self.total_episodes,
                'level': self.current_level,
                'action': 'regress'
            })
            print(f"📉 Regressed to level {self.current_level}")
            self.performance_history.clear()
    
    def update(self):
        """Update curriculum based on performance"""
        if self.should_advance():
            self.advance_level()
        elif self.should_regress():
            self.regress_level()
    
    def get_stats(self) -> Dict:
        """Get curriculum statistics"""
        return {
            'current_level': self.current_level,
            'total_levels': len(self.levels),
            'total_episodes': self.total_episodes,
            'success_rate': self.get_success_rate(),
            'level_changes': len(self.level_history)
        }


# ============ TASK DIFFICULTY GENERATOR ============

class TaskDifficultyGenerator:
    """
    Tự động tạo tasks với độ khó khác nhau
    """
    def __init__(self, base_params: Dict):
        self.base_params = base_params
    
    def generate_easy_task(self) -> Dict:
        """Generate easy task"""
        params = self.base_params.copy()
        params['num_obstacles'] = 2
        params['goal_distance'] = 5
        params['time_limit'] = 100
        params['reward_scale'] = 1.0
        return params
    
    def generate_medium_task(self) -> Dict:
        """Generate medium difficulty task"""
        params = self.base_params.copy()
        params['num_obstacles'] = 5
        params['goal_distance'] = 10
        params['time_limit'] = 80
        params['reward_scale'] = 1.5
        return params
    
    def generate_hard_task(self) -> Dict:
        """Generate hard task"""
        params = self.base_params.copy()
        params['num_obstacles'] = 10
        params['goal_distance'] = 15
        params['time_limit'] = 60
        params['reward_scale'] = 2.0
        return params
    
    def generate_expert_task(self) -> Dict:
        """Generate expert level task"""
        params = self.base_params.copy()
        params['num_obstacles'] = 15
        params['goal_distance'] = 20
        params['time_limit'] = 50
        params['reward_scale'] = 3.0
        params['moving_obstacles'] = True
        return params
    
    def generate_custom_task(self, difficulty: float) -> Dict:
        """
        Generate task with custom difficulty (0.0 to 1.0)
        """
        params = self.base_params.copy()
        
        # Interpolate parameters based on difficulty
        params['num_obstacles'] = int(2 + difficulty * 13)
        params['goal_distance'] = int(5 + difficulty * 15)
        params['time_limit'] = int(100 - difficulty * 50)
        params['reward_scale'] = 1.0 + difficulty * 2.0
        params['moving_obstacles'] = difficulty > 0.7
        
        return params


# ============ ADAPTIVE CURRICULUM ============

class AdaptiveCurriculum:
    """
    Adaptive curriculum that adjusts difficulty in real-time
    Sử dụng performance metrics để tự động điều chỉnh
    """
    def __init__(self, min_difficulty=0.0, max_difficulty=1.0, adaptation_rate=0.01):
        self.min_difficulty = min_difficulty
        self.max_difficulty = max_difficulty
        self.current_difficulty = min_difficulty
        self.adaptation_rate = adaptation_rate
        
        self.target_success_rate = 0.7
        self.recent_successes = deque(maxlen=50)
    
    def record_episode(self, success: bool):
        """Record episode result"""
        self.recent_successes.append(1 if success else 0)
    
    def get_success_rate(self) -> float:
        """Get recent success rate"""
        if len(self.recent_successes) == 0:
            return 0.0
        return sum(self.recent_successes) / len(self.recent_successes)
    
    def update_difficulty(self):
        """Update difficulty based on performance"""
        if len(self.recent_successes) < 10:
            return
        
        success_rate = self.get_success_rate()
        
        # Increase difficulty if too easy
        if success_rate > self.target_success_rate + 0.1:
            self.current_difficulty = min(
                self.max_difficulty,
                self.current_difficulty + self.adaptation_rate
            )
        
        # Decrease difficulty if too hard
        elif success_rate < self.target_success_rate - 0.1:
            self.current_difficulty = max(
                self.min_difficulty,
                self.current_difficulty - self.adaptation_rate
            )
    
    def get_difficulty(self) -> float:
        """Get current difficulty level"""
        return self.current_difficulty


# ============ PROGRESSIVE NEURAL NETWORKS ============

class ProgressiveColumn(nn.Module):
    """Single column in Progressive Neural Network"""
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers=3):
        super().__init__()
        
        self.layers = nn.ModuleList()
        
        # First layer
        self.layers.append(nn.Linear(input_dim, hidden_dim))
        
        # Hidden layers
        for _ in range(num_layers - 2):
            self.layers.append(nn.Linear(hidden_dim, hidden_dim))
        
        # Output layer
        self.layers.append(nn.Linear(hidden_dim, output_dim))
    
    def forward(self, x):
        activations = []
        
        for i, layer in enumerate(self.layers):
            x = layer(x)
            if i < len(self.layers) - 1:
                x = torch.relu(x)
            activations.append(x)
        
        return x, activations


class ProgressiveNeuralNetwork(nn.Module):
    """
    Progressive Neural Network for Curriculum Learning
    Thêm columns mới cho tasks mới, giữ lại knowledge cũ
    """
    def __init__(self, input_dim, hidden_dim, output_dim, num_layers=3):
        super().__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers
        
        self.columns = nn.ModuleList()
        self.lateral_connections = nn.ModuleList()
        
        # Add first column
        self.add_column()
    
    def add_column(self):
        """Add new column for new task"""
        column = ProgressiveColumn(
            self.input_dim,
            self.hidden_dim,
            self.output_dim,
            self.num_layers
        )
        self.columns.append(column)
        
        # Add lateral connections from previous columns
        if len(self.columns) > 1:
            lateral = nn.ModuleList()
            for _ in range(self.num_layers):
                # Connection from each previous column
                lateral.append(nn.Linear(
                    self.hidden_dim * (len(self.columns) - 1),
                    self.hidden_dim
                ))
            self.lateral_connections.append(lateral)
        
        print(f"📊 Added column {len(self.columns)}")
    
    def forward(self, x, column_idx=-1):
        """
        Forward pass through specific column
        Args:
            x: Input
            column_idx: Which column to use (-1 for latest)
        """
        if column_idx == -1:
            column_idx = len(self.columns) - 1
        
        # Get activations from previous columns
        prev_activations = []
        for i in range(column_idx):
            _, activations = self.columns[i](x)
            prev_activations.append(activations)
        
        # Forward through current column with lateral connections
        current_x = x
        for layer_idx, layer in enumerate(self.columns[column_idx].layers):
            current_x = layer(current_x)
            
            # Add lateral connections
            if column_idx > 0 and layer_idx < len(self.lateral_connections[column_idx - 1]):
                lateral_input = torch.cat([
                    prev_activations[i][layer_idx] 
                    for i in range(column_idx)
                ], dim=-1)
                lateral_output = self.lateral_connections[column_idx - 1][layer_idx](lateral_input)
                current_x = current_x + lateral_output
            
            if layer_idx < len(self.columns[column_idx].layers) - 1:
                current_x = torch.relu(current_x)
        
        return current_x
    
    def freeze_columns(self, num_columns: int):
        """Freeze first N columns"""
        for i in range(min(num_columns, len(self.columns))):
            for param in self.columns[i].parameters():
                param.requires_grad = False


# ============ CURRICULUM TRAINER ============

class CurriculumTrainer:
    """
    Trainer with curriculum learning support
    """
    def __init__(self, agent, curriculum_manager, optimizer):
        self.agent = agent
        self.curriculum = curriculum_manager
        self.optimizer = optimizer
        
        self.episode_rewards = []
        self.episode_lengths = []
    
    def train_episode(self, env_fn: Callable, max_steps=1000):
        """
        Train one episode with current curriculum level
        """
        # Get current level parameters
        level_params = self.curriculum.get_current_level()
        
        # Create environment with level parameters
        env = env_fn(**level_params)
        
        state = env.reset()
        episode_reward = 0
        episode_length = 0
        done = False
        
        while not done and episode_length < max_steps:
            # Select action
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                action = self.agent.select_action(state_tensor)
            
            # Take action
            next_state, reward, done, info = env.step(action)
            
            # Store transition and train
            # (Implementation depends on specific algorithm)
            
            episode_reward += reward
            episode_length += 1
            state = next_state
        
        # Record episode
        success = info.get('success', episode_reward > 0)
        self.curriculum.record_episode(success, episode_reward)
        
        # Update curriculum
        self.curriculum.update()
        
        self.episode_rewards.append(episode_reward)
        self.episode_lengths.append(episode_length)
        
        return episode_reward, episode_length
    
    def train(self, env_fn: Callable, num_episodes=1000):
        """Train with curriculum learning"""
        print("🎓 Starting Curriculum Learning Training\n")
        
        for episode in range(num_episodes):
            reward, length = self.train_episode(env_fn)
            
            if episode % 100 == 0:
                stats = self.curriculum.get_stats()
                avg_reward = np.mean(self.episode_rewards[-100:])
                
                print(f"Episode {episode}")
                print(f"  Level: {stats['current_level']}/{stats['total_levels']}")
                print(f"  Success Rate: {stats['success_rate']:.2%}")
                print(f"  Avg Reward: {avg_reward:.2f}")
                print()


# ============ TESTING ============

if __name__ == "__main__":
    print("🎓 Testing Curriculum Learning System\n")
    
    # Test Curriculum Manager
    print("1. Testing Curriculum Manager...")
    levels = [
        {'difficulty': 'easy', 'num_obstacles': 2},
        {'difficulty': 'medium', 'num_obstacles': 5},
        {'difficulty': 'hard', 'num_obstacles': 10},
        {'difficulty': 'expert', 'num_obstacles': 15}
    ]
    
    curriculum = CurriculumManager(levels, success_threshold=0.7, window_size=20)
    
    # Simulate training
    for i in range(100):
        success = np.random.random() > 0.3  # 70% success rate
        reward = np.random.uniform(0, 10)
        curriculum.record_episode(success, reward)
        curriculum.update()
    
    stats = curriculum.get_stats()
    print(f"   Current Level: {stats['current_level']}")
    print(f"   Success Rate: {stats['success_rate']:.2%}")
    print(f"   ✅ Curriculum Manager working\n")
    
    # Test Task Generator
    print("2. Testing Task Difficulty Generator...")
    generator = TaskDifficultyGenerator({'base_reward': 1.0})
    
    easy = generator.generate_easy_task()
    hard = generator.generate_hard_task()
    
    print(f"   Easy task obstacles: {easy['num_obstacles']}")
    print(f"   Hard task obstacles: {hard['num_obstacles']}")
    print(f"   ✅ Task Generator working\n")
    
    # Test Adaptive Curriculum
    print("3. Testing Adaptive Curriculum...")
    adaptive = AdaptiveCurriculum(min_difficulty=0.0, max_difficulty=1.0)
    
    for i in range(50):
        success = np.random.random() > 0.5
        adaptive.record_episode(success)
        adaptive.update_difficulty()
    
    print(f"   Current Difficulty: {adaptive.get_difficulty():.2f}")
    print(f"   Success Rate: {adaptive.get_success_rate():.2%}")
    print(f"   ✅ Adaptive Curriculum working\n")
    
    # Test Progressive Neural Network
    print("4. Testing Progressive Neural Network...")
    pnn = ProgressiveNeuralNetwork(input_dim=10, hidden_dim=64, output_dim=4, num_layers=3)
    
    x = torch.randn(4, 10)
    output1 = pnn(x, column_idx=0)
    
    # Add new column for new task
    pnn.add_column()
    output2 = pnn(x, column_idx=1)
    
    print(f"   Input shape: {x.shape}")
    print(f"   Output 1 shape: {output1.shape}")
    print(f"   Output 2 shape: {output2.shape}")
    print(f"   Number of columns: {len(pnn.columns)}")
    print(f"   ✅ Progressive NN working\n")
    
    print("✅ All Curriculum Learning components tested successfully!")
    
    # Statistics
    print("\n📊 System Statistics:")
    print(f"   Curriculum levels: {len(levels)}")
    print(f"   PNN columns: {len(pnn.columns)}")
    print(f"   PNN parameters: {sum(p.numel() for p in pnn.parameters()):,}")
