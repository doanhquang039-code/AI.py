"""
ai/ppo.py — Proximal Policy Optimization (PPO)

PPO là thuật toán Policy Gradient hiện đại, stable và hiệu quả:
- Actor network: học policy π(a|s)
- Critic network: ước tính value V(s)
- Clipped surrogate objective: giới hạn update không quá lớn
- GAE (Generalized Advantage Estimation): ước tính advantage

Paper: "Proximal Policy Optimization Algorithms" (Schulman et al., 2017)
"""
import numpy as np
import random
from typing import List, Optional, Tuple

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    from torch.distributions import Categorical
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from config.settings_manager import settings


# ─────────────────────────────────────────────────────────────────────────────
# NETWORKS
# ─────────────────────────────────────────────────────────────────────────────

class ActorNetwork(nn.Module):
    """
    Policy network: π(a|s) — xác suất chọn mỗi action.
    Output qua Softmax để tạo distribution.
    """
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
        )

    def forward(self, x):
        logits = self.net(x)
        return Categorical(logits=logits)


class CriticNetwork(nn.Module):
    """
    Value network: V(s) — ước tính tổng reward từ s.
    """
    def __init__(self, state_dim: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


# ─────────────────────────────────────────────────────────────────────────────
# ROLLOUT BUFFER
# ─────────────────────────────────────────────────────────────────────────────

class RolloutBuffer:
    """
    Lưu trữ trajectory (s, a, r, done, log_prob, value) trong một rollout.
    Được dùng để tính GAE và update PPO.
    """
    def __init__(self):
        self.states: List[np.ndarray] = []
        self.actions: List[int] = []
        self.rewards: List[float] = []
        self.dones: List[bool] = []
        self.log_probs: List[float] = []
        self.values: List[float] = []

    def push(self, state, action, reward, done, log_prob, value):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.dones.append(done)
        self.log_probs.append(log_prob)
        self.values.append(value)

    def clear(self):
        self.__init__()

    def __len__(self):
        return len(self.states)


# ─────────────────────────────────────────────────────────────────────────────
# PPO AGENT
# ─────────────────────────────────────────────────────────────────────────────

class PPOAgent:
    """
    PPO Agent với:
        ✓ Actor-Critic networks (tách biệt)
        ✓ Clipped surrogate objective
        ✓ Generalized Advantage Estimation (GAE)
        ✓ Entropy bonus (khuyến khích explore)
        ✓ Mini-batch updates
    """

    def __init__(self, state_dim: int = 27, action_dim: int = 9):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required for PPO")

        self.state_dim = state_dim
        self.action_dim = action_dim

        # Load config
        cfg = settings.get_section("ppo")
        self.lr_actor = cfg.get("lr_actor", 3e-4)
        self.lr_critic = cfg.get("lr_critic", 1e-3)
        self.gamma = cfg.get("gamma", 0.99)
        self.gae_lambda = cfg.get("gae_lambda", 0.95)
        self.clip_ratio = cfg.get("clip_ratio", 0.2)
        self.epochs = cfg.get("epochs_per_update", 4)
        self.rollout_steps = cfg.get("rollout_steps", 256)
        self.entropy_coef = cfg.get("entropy_coef", 0.01)
        self.hidden_dim = cfg.get("hidden_dim", 128)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Networks
        self.actor = ActorNetwork(state_dim, action_dim, self.hidden_dim).to(self.device)
        self.critic = CriticNetwork(state_dim, self.hidden_dim).to(self.device)

        self.opt_actor = optim.Adam(self.actor.parameters(), lr=self.lr_actor)
        self.opt_critic = optim.Adam(self.critic.parameters(), lr=self.lr_critic)

        # Buffer
        self.buffer = RolloutBuffer()

        # Không dùng epsilon (PPO tự explore qua entropy)
        self.epsilon = 0.0   # dummy, cho UI

        # Stats
        self.total_steps: int = 0
        self.episode_rewards: list = []
        self.losses: list = []
        self._current_episode_reward: float = 0.0
        self._step_in_rollout: int = 0

    # ─────────────────────────────────────────────────────────────────────────
    # ACTION
    # ─────────────────────────────────────────────────────────────────────────

    def choose_action(self, state: np.ndarray) -> int:
        """Sample action từ policy distribution."""
        with torch.no_grad():
            s = torch.FloatTensor(state).to(self.device)
            dist = self.actor(s)
            action = dist.sample()
        return int(action.item())

    def greedy_action(self, state: np.ndarray) -> int:
        """Chọn action xác suất cao nhất (no exploration)."""
        with torch.no_grad():
            s = torch.FloatTensor(state).to(self.device)
            dist = self.actor(s)
            return int(dist.probs.argmax().item())

    def _get_log_prob_value(self, state: np.ndarray, action: int):
        """Lấy log_prob và value cho (state, action)."""
        with torch.no_grad():
            s = torch.FloatTensor(state).to(self.device)
            dist = self.actor(s)
            log_prob = dist.log_prob(torch.tensor(action).to(self.device))
            value = self.critic(s)
        return float(log_prob.item()), float(value.item())

    # ─────────────────────────────────────────────────────────────────────────
    # LEARN
    # ─────────────────────────────────────────────────────────────────────────

    def learn(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> Optional[float]:
        """Thu thập experience và update khi đủ rollout_steps."""
        log_prob, value = self._get_log_prob_value(state, action)
        self.buffer.push(state, action, reward, done, log_prob, value)
        self.total_steps += 1
        self._current_episode_reward += reward
        self._step_in_rollout += 1

        # Update khi đủ rollout_steps
        if self._step_in_rollout >= self.rollout_steps:
            loss = self._update(next_state, done)
            self.buffer.clear()
            self._step_in_rollout = 0
            return loss
        return None

    def _compute_gae(
        self, rewards, values, dones, last_value: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generalized Advantage Estimation (GAE):
            δt = rt + γ V(st+1) - V(st)
            At = δt + (γλ) δt+1 + (γλ)² δt+2 + ...
        """
        n = len(rewards)
        advantages = np.zeros(n, dtype=np.float32)
        returns = np.zeros(n, dtype=np.float32)
        gae = 0.0

        for t in reversed(range(n)):
            if t == n - 1:
                next_val = last_value * (1 - dones[t])
            else:
                next_val = values[t + 1] * (1 - dones[t])

            delta = rewards[t] + self.gamma * next_val - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages[t] = gae
            returns[t] = gae + values[t]

        return advantages, returns

    def _update(self, last_state: np.ndarray, last_done: bool) -> float:
        """Cập nhật Actor và Critic bằng PPO loss."""
        with torch.no_grad():
            s = torch.FloatTensor(last_state).to(self.device)
            last_val = float(self.critic(s).item()) * (1 - last_done)

        rewards = np.array(self.buffer.rewards, dtype=np.float32)
        values = np.array(self.buffer.values, dtype=np.float32)
        dones = np.array(self.buffer.dones, dtype=np.float32)
        old_log_probs = torch.FloatTensor(self.buffer.log_probs).to(self.device)

        advantages, returns = self._compute_gae(rewards, values, dones, last_val)
        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = torch.FloatTensor(returns).to(self.device)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        states = torch.FloatTensor(np.array(self.buffer.states)).to(self.device)
        actions = torch.LongTensor(self.buffer.actions).to(self.device)

        total_loss = 0.0

        for _ in range(self.epochs):
            # Actor loss (PPO-Clip)
            dist = self.actor(states)
            log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()

            ratio = torch.exp(log_probs - old_log_probs.detach())
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.clip_ratio, 1 + self.clip_ratio) * advantages
            actor_loss = -torch.min(surr1, surr2).mean() - self.entropy_coef * entropy

            # Critic loss
            values_pred = self.critic(states)
            critic_loss = F.mse_loss(values_pred, returns)

            # Update
            self.opt_actor.zero_grad()
            actor_loss.backward()
            nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
            self.opt_actor.step()

            self.opt_critic.zero_grad()
            critic_loss.backward()
            nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
            self.opt_critic.step()

            total_loss += float((actor_loss + critic_loss).item())

        avg_loss = total_loss / self.epochs
        self.losses.append(avg_loss)
        return avg_loss

    def decay_epsilon(self):
        pass  # PPO không dùng epsilon

    def end_episode(self):
        self.episode_rewards.append(self._current_episode_reward)
        self._current_episode_reward = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────────

    def save(self, path: str):
        import os
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        torch.save({
            "actor": self.actor.state_dict(),
            "critic": self.critic.state_dict(),
            "episode_rewards": self.episode_rewards,
            "total_steps": self.total_steps,
        }, path)

    def load(self, path: str):
        ck = torch.load(path, map_location=self.device)
        self.actor.load_state_dict(ck["actor"])
        self.critic.load_state_dict(ck["critic"])
        self.episode_rewards = ck.get("episode_rewards", [])
        self.total_steps = ck.get("total_steps", 0)

    # ─────────────────────────────────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────────────────────────────────

    def recent_avg_reward(self, n: int = 50) -> float:
        if not self.episode_rewards:
            return 0.0
        return float(np.mean(self.episode_rewards[-n:]))

    def recent_avg_loss(self, n: int = 20) -> float:
        if not self.losses:
            return 0.0
        return float(np.mean(self.losses[-n:]))

    @property
    def stats(self) -> dict:
        return {
            "type": "PPO (Clip + GAE)",
            "epsilon": 0.0,   # PPO không có epsilon
            "total_steps": self.total_steps,
            "episodes": len(self.episode_rewards),
            "avg_reward_50": round(self.recent_avg_reward(50), 2),
            "avg_loss_20": round(self.recent_avg_loss(20), 4),
            "device": str(self.device),
            "buffer_size": len(self.buffer),
        }
