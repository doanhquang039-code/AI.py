"""
ai/dqn.py — Deep Q-Network (DQN) Agent với Double DQN

Kiến trúc:
    - Neural Network: state → Q-values cho mỗi action
    - Experience Replay: ReplayBuffer / PrioritizedReplayBuffer
    - Target Network: ổn định training
    - Double DQN: giảm overestimation của Q-values
    - Epsilon-greedy exploration

Paper tham khảo:
    - DQN: "Playing Atari with Deep Reinforcement Learning" (Mnih et al., 2013)
    - Double DQN: "Deep Reinforcement Learning with Double Q-learning" (van Hasselt et al., 2015)
"""
import os
import numpy as np
import random
from typing import Tuple, Optional

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[WARNING] PyTorch not installed. Run: pip install torch")

import config as cfg
from ai.memory import ReplayBuffer, PrioritizedReplayBuffer


# ─────────────────────────────────────────────────────────────────────────────
# NEURAL NETWORK
# ─────────────────────────────────────────────────────────────────────────────

class QNetwork(nn.Module):
    """
    Mạng nơ-ron tính Q(s, a) cho tất cả actions cùng lúc.

    Kiến trúc:
        Input  → FC(128) → LayerNorm → ReLU
               → FC(128) → LayerNorm → ReLU
               → FC(128) → LayerNorm → ReLU
               → FC(action_dim)   [output: Q-value cho mỗi action]

    Dùng LayerNorm thay BatchNorm để hoạt động tốt với batch nhỏ.
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int,
        num_hidden: int,
    ):
        super().__init__()

        layers = []
        in_dim = state_dim

        for _ in range(num_hidden):
            layers += [
                nn.Linear(in_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.ReLU(),
            ]
            in_dim = hidden_dim

        layers.append(nn.Linear(in_dim, action_dim))
        self.net = nn.Sequential(*layers)

        # Khởi tạo weights theo He initialization
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_uniform_(m.weight, nonlinearity="relu")
                nn.init.constant_(m.bias, 0.0)

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        return self.net(x)


class DuelingQNetwork(nn.Module):
    """
    Dueling DQN: tách Value function V(s) và Advantage A(s,a)
        Q(s,a) = V(s) + A(s,a) - mean(A(s,·))

    Học hiệu quả hơn khi nhiều actions có cùng Q-value.
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int,
        num_hidden: int,
    ):
        super().__init__()
        self.action_dim = action_dim

        # Shared feature extractor
        shared_layers = []
        in_dim = state_dim
        for _ in range(num_hidden - 1):
            shared_layers += [
                nn.Linear(in_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
                nn.ReLU(),
            ]
            in_dim = hidden_dim
        self.shared = nn.Sequential(*shared_layers)

        # Value stream
        self.value_stream = nn.Sequential(
            nn.Linear(in_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
        )

        # Advantage stream
        self.advantage_stream = nn.Sequential(
            nn.Linear(in_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
        )

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        features = self.shared(x)
        value = self.value_stream(features)
        advantage = self.advantage_stream(features)
        # Q = V + (A - mean(A))
        q = value + advantage - advantage.mean(dim=1, keepdim=True)
        return q


# ─────────────────────────────────────────────────────────────────────────────
# DQN AGENT
# ─────────────────────────────────────────────────────────────────────────────

class DQNAgent:
    """
    Deep Q-Network Agent với:
        ✓ Double DQN (giảm overestimation)
        ✓ Dueling Network (Value + Advantage streams)
        ✓ Prioritized Experience Replay (học tập trung vào transitions quan trọng)
        ✓ Target Network (ổn định training)
        ✓ Epsilon-greedy exploration với decay
        ✓ Gradient clipping (tránh exploding gradients)
    """

    def __init__(
        self,
        state_dim: int = cfg.STATE_DIM,
        action_dim: int = cfg.ACTION_DIM,
        use_dueling: bool = True,
        use_per: bool = True,
    ):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch chưa được cài đặt!")

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.use_double = cfg.DQN_CFG.use_double_dqn
        self.use_per = use_per

        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[DQN] Using device: {self.device}")

        # Networks
        NetClass = DuelingQNetwork if use_dueling else QNetwork
        self.policy_net = NetClass(
            state_dim, action_dim,
            cfg.DQN_CFG.hidden_dim,
            cfg.DQN_CFG.num_hidden_layers,
        ).to(self.device)

        self.target_net = NetClass(
            state_dim, action_dim,
            cfg.DQN_CFG.hidden_dim,
            cfg.DQN_CFG.num_hidden_layers,
        ).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        # Optimizer
        self.optimizer = optim.Adam(
            self.policy_net.parameters(),
            lr=cfg.DQN_CFG.lr,
        )
        self.scheduler = optim.lr_scheduler.StepLR(
            self.optimizer, step_size=500, gamma=0.9
        )

        # Replay Buffer
        if use_per:
            self.memory = PrioritizedReplayBuffer(cfg.DQN_CFG.memory_size)
        else:
            self.memory = ReplayBuffer(cfg.DQN_CFG.memory_size)

        # Hyperparameters
        self.gamma = cfg.DQN_CFG.gamma
        self.batch_size = cfg.DQN_CFG.batch_size
        self.epsilon = cfg.DQN_CFG.epsilon_start
        self.epsilon_end = cfg.DQN_CFG.epsilon_end
        self.epsilon_decay = cfg.DQN_CFG.epsilon_decay
        self.target_update_freq = cfg.DQN_CFG.target_update_freq

        # Counters
        self.total_steps: int = 0
        self.total_updates: int = 0
        self.episode_rewards: list = []
        self.losses: list = []
        self._current_episode_reward: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # ACTION SELECTION
    # ─────────────────────────────────────────────────────────────────────────

    def choose_action(self, state: np.ndarray) -> int:
        """Epsilon-greedy action selection."""
        if random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        return self.greedy_action(state)

    def greedy_action(self, state: np.ndarray) -> int:
        """Chọn action tốt nhất theo policy network."""
        with torch.no_grad():
            s = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(s)
            return int(q_values.argmax().item())

    # ─────────────────────────────────────────────────────────────────────────
    # LEARNING
    # ─────────────────────────────────────────────────────────────────────────

    def learn(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> Optional[float]:
        """
        1. Lưu transition vào memory
        2. Sample batch và tính TD error
        3. Cập nhật policy network
        4. Cập nhật target network định kỳ
        """
        self.memory.push(state, action, reward, next_state, done)
        self.total_steps += 1
        self._current_episode_reward += reward

        if not self.memory.is_ready:
            return None

        loss = self._update()
        self.losses.append(loss)

        # Cập nhật target network
        if self.total_steps % self.target_update_freq == 0:
            self._sync_target()

        return loss

    def _update(self) -> float:
        """Một bước gradient descent trên mini-batch."""
        self.policy_net.train()

        if self.use_per:
            states, actions, rewards, next_states, dones, indices, weights = \
                self.memory.sample(self.batch_size)
            weights_t = torch.FloatTensor(weights).to(self.device)
        else:
            states, actions, rewards, next_states, dones = \
                self.memory.sample(self.batch_size)
            weights_t = None

        # Chuyển sang tensor
        s = torch.FloatTensor(states).to(self.device)
        a = torch.LongTensor(actions).to(self.device)
        r = torch.FloatTensor(rewards).to(self.device)
        ns = torch.FloatTensor(next_states).to(self.device)
        d = torch.FloatTensor(dones).to(self.device)

        # Q(s, a) — Q-values của các action đã thực hiện
        q_values = self.policy_net(s).gather(1, a.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            if self.use_double:
                # Double DQN: dùng policy net chọn action, target net đánh giá
                next_actions = self.policy_net(ns).argmax(1, keepdim=True)
                q_next = self.target_net(ns).gather(1, next_actions).squeeze(1)
            else:
                q_next = self.target_net(ns).max(1)[0]

            td_target = r + self.gamma * q_next * (1 - d)

        td_errors = (q_values - td_target).detach().cpu().numpy()

        # Loss
        if weights_t is not None:
            loss = (weights_t * F.smooth_l1_loss(q_values, td_target, reduction="none")).mean()
            self.memory.update_priorities(indices, td_errors)
        else:
            loss = F.smooth_l1_loss(q_values, td_target)

        # Backward
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), max_norm=10.0)
        self.optimizer.step()

        self.total_updates += 1
        return float(loss.item())

    def _sync_target(self):
        """Soft update target network: θ_target ← τ θ_policy + (1-τ) θ_target"""
        tau = 0.005
        for t_param, p_param in zip(
            self.target_net.parameters(), self.policy_net.parameters()
        ):
            t_param.data.copy_(tau * p_param.data + (1 - tau) * t_param.data)

    def decay_epsilon(self):
        """Giảm epsilon sau mỗi episode."""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def end_episode(self):
        """Gọi cuối mỗi episode."""
        self.episode_rewards.append(self._current_episode_reward)
        self._current_episode_reward = 0.0
        self.decay_epsilon()
        self.scheduler.step()

    # ─────────────────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────────

    def save(self, path: str):
        """Lưu model weights."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        torch.save({
            "policy_net": self.policy_net.state_dict(),
            "target_net": self.target_net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "total_steps": self.total_steps,
            "episode_rewards": self.episode_rewards,
        }, path)
        print(f"[DQN] Model saved -> {path}")

    def load(self, path: str):
        """Load model weights."""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint["policy_net"])
        self.target_net.load_state_dict(checkpoint["target_net"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.epsilon = checkpoint["epsilon"]
        self.total_steps = checkpoint["total_steps"]
        self.episode_rewards = checkpoint.get("episode_rewards", [])
        print(f"[DQN] Model loaded <- {path} (step {self.total_steps})")

    # ─────────────────────────────────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────────────────────────────────

    def recent_avg_reward(self, n: int = 50) -> float:
        if not self.episode_rewards:
            return 0.0
        return float(np.mean(self.episode_rewards[-n:]))

    def recent_avg_loss(self, n: int = 100) -> float:
        if not self.losses:
            return 0.0
        return float(np.mean(self.losses[-n:]))

    @property
    def stats(self) -> dict:
        return {
            "type": "DQN (Double + Dueling + PER)",
            "epsilon": round(self.epsilon, 4),
            "memory_size": len(self.memory),
            "total_steps": self.total_steps,
            "total_updates": self.total_updates,
            "avg_reward_50": round(self.recent_avg_reward(50), 2),
            "avg_loss_100": round(self.recent_avg_loss(100), 4),
            "episodes": len(self.episode_rewards),
            "device": str(self.device),
        }
