"""
ai/a2c.py — Advantage Actor-Critic (A2C)

A2C là phiên bản đồng bộ của A3C:
- Actor network: học policy π(a|s)
- Critic network: ước tính V(s)
- Cập nhật sau n bước (n-step returns)
- Entropy bonus khuyến khích exploration

So với PPO:
    PPO: rollout lớn, nhiều epochs/update, clip ratio
    A2C: n-step nhỏ, một lần update, đơn giản hơn

Paper: "Asynchronous Methods for Deep Reinforcement Learning" (Mnih et al., 2016)
"""
import numpy as np
import random
from typing import Optional, List

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


class A2CNetwork(nn.Module):
    """
    Shared network với hai heads:
        - Actor head: logits cho policy
        - Critic head: scalar value V(s)

    Shared backbone giúp học feature tốt hơn cho cả hai task.
    """

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int):
        super().__init__()

        # Shared backbone
        self.backbone = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        # Actor head
        self.actor_head = nn.Linear(hidden_dim, action_dim)

        # Critic head
        self.critic_head = nn.Linear(hidden_dim, 1)

        # Init
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0)

        # Critic/actor heads cần scale nhỏ hơn
        nn.init.orthogonal_(self.actor_head.weight, gain=0.01)
        nn.init.orthogonal_(self.critic_head.weight, gain=1.0)

    def forward(self, x):
        features = self.backbone(x)
        logits = self.actor_head(features)
        value = self.critic_head(features).squeeze(-1)
        dist = Categorical(logits=logits)
        return dist, value


class A2CAgent:
    """
    Advantage Actor-Critic với n-step returns.

    Flow:
        1. Collect n steps
        2. Compute n-step returns: Gt = rt + γ r(t+1) + ... + γ^(n-1) r(t+n-1) + γ^n V(s(t+n))
        3. Compute advantage: At = Gt - V(st)
        4. Actor loss:  -log π(at|st) * At  (policy gradient)
        5. Critic loss: (Gt - V(st))²        (value regression)
        6. Entropy bonus: -H[π(·|st)]        (encourage explore)
    """

    def __init__(self, state_dim: int = 27, action_dim: int = 9):
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required for A2C")

        self.state_dim = state_dim
        self.action_dim = action_dim

        # Load config
        cfg = settings.get_section("a2c")
        self.lr = cfg.get("lr", 7e-4)
        self.gamma = cfg.get("gamma", 0.99)
        self.entropy_coef = cfg.get("entropy_coef", 0.01)
        self.value_loss_coef = cfg.get("value_loss_coef", 0.5)
        self.max_grad_norm = cfg.get("max_grad_norm", 0.5)
        self.n_steps = cfg.get("n_steps", 5)
        self.hidden_dim = cfg.get("hidden_dim", 128)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Shared Actor-Critic network
        self.net = A2CNetwork(state_dim, action_dim, self.hidden_dim).to(self.device)
        self.optimizer = optim.RMSprop(
            self.net.parameters(), lr=self.lr, eps=1e-5, alpha=0.99
        )

        # n-step buffer
        self._states: List[np.ndarray] = []
        self._actions: List[int] = []
        self._rewards: List[float] = []
        self._dones: List[bool] = []

        # dummy epsilon cho UI
        self.epsilon = 0.0

        # Stats
        self.total_steps: int = 0
        self.episode_rewards: list = []
        self.losses: list = []
        self._current_episode_reward: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # ACTION
    # ─────────────────────────────────────────────────────────────────────────

    def choose_action(self, state: np.ndarray) -> int:
        """Sample action từ stochastic policy."""
        with torch.no_grad():
            s = torch.FloatTensor(state).to(self.device)
            dist, _ = self.net(s)
            return int(dist.sample().item())

    def greedy_action(self, state: np.ndarray) -> int:
        with torch.no_grad():
            s = torch.FloatTensor(state).to(self.device)
            dist, _ = self.net(s)
            return int(dist.probs.argmax().item())

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
        """Collect experience, update sau mỗi n_steps."""
        self._states.append(state)
        self._actions.append(action)
        self._rewards.append(reward)
        self._dones.append(done)
        self.total_steps += 1
        self._current_episode_reward += reward

        if len(self._states) >= self.n_steps or done:
            loss = self._update(next_state, done)
            self._clear_buffer()
            return loss
        return None

    def _update(self, last_state: np.ndarray, last_done: bool) -> float:
        """Tính n-step returns và cập nhật A2C."""
        # Bootstrap value
        with torch.no_grad():
            s = torch.FloatTensor(last_state).to(self.device)
            _, bootstrap_val = self.net(s)
            bootstrap_val = float(bootstrap_val.item()) * (1 - float(last_done))

        # Compute n-step returns (backward)
        returns = []
        R = bootstrap_val
        for r, d in zip(reversed(self._rewards), reversed(self._dones)):
            R = r + self.gamma * R * (1 - float(d))
            returns.insert(0, R)

        # Tensors
        states = torch.FloatTensor(np.array(self._states)).to(self.device)
        actions = torch.LongTensor(self._actions).to(self.device)
        returns_t = torch.FloatTensor(returns).to(self.device)

        # Forward pass
        dists, values = self.net(states)
        log_probs = dists.log_prob(actions)
        entropy = dists.entropy().mean()

        # Advantages
        advantages = (returns_t - values).detach()

        # Normalize advantages (optional, helps stability)
        if len(advantages) > 1:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # Losses
        actor_loss = -(log_probs * advantages).mean()
        critic_loss = F.mse_loss(values, returns_t)
        total_loss = actor_loss + self.value_loss_coef * critic_loss - self.entropy_coef * entropy

        # Backprop
        self.optimizer.zero_grad()
        total_loss.backward()
        nn.utils.clip_grad_norm_(self.net.parameters(), self.max_grad_norm)
        self.optimizer.step()

        loss_val = float(total_loss.item())
        self.losses.append(loss_val)
        return loss_val

    def _clear_buffer(self):
        self._states.clear()
        self._actions.clear()
        self._rewards.clear()
        self._dones.clear()

    def decay_epsilon(self):
        pass  # A2C không dùng epsilon

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
            "net": self.net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "episode_rewards": self.episode_rewards,
            "total_steps": self.total_steps,
        }, path)

    def load(self, path: str):
        ck = torch.load(path, map_location=self.device)
        self.net.load_state_dict(ck["net"])
        self.optimizer.load_state_dict(ck["optimizer"])
        self.episode_rewards = ck.get("episode_rewards", [])
        self.total_steps = ck.get("total_steps", 0)

    # ─────────────────────────────────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────────────────────────────────

    def recent_avg_reward(self, n: int = 50) -> float:
        if not self.episode_rewards:
            return 0.0
        return float(np.mean(self.episode_rewards[-n:]))

    def recent_avg_loss(self, n: int = 50) -> float:
        if not self.losses:
            return 0.0
        return float(np.mean(self.losses[-n:]))

    @property
    def stats(self) -> dict:
        return {
            "type": "A2C (n-step, Shared Net)",
            "epsilon": 0.0,
            "total_steps": self.total_steps,
            "episodes": len(self.episode_rewards),
            "avg_reward_50": round(self.recent_avg_reward(50), 2),
            "avg_loss_50": round(self.recent_avg_loss(50), 4),
            "device": str(self.device),
        }
