"""
ai/sarsa.py — SARSA (State-Action-Reward-State-Action)

SARSA là thuật toán On-Policy TD Control:
    Q(s,a) ← Q(s,a) + α [r + γ Q(s',a') - Q(s,a)]

Khác với Q-Learning (off-policy dùng max Q), SARSA dùng
action THỰC SỰ được chọn ở s' → an toàn hơn, converge chậm hơn.

Paper: Sutton & Barto, "Reinforcement Learning: An Introduction" (1998)
"""
import numpy as np
import random
from collections import defaultdict
from typing import Optional

from config.settings_manager import settings


class SARSAAgent:
    """
    Tabular SARSA với epsilon-greedy exploration.

    On-policy: agent học dựa trên chính sách đang dùng,
    không phải chính sách tối ưu như Q-Learning.
    """

    def __init__(self, state_dim: int = 27, action_dim: int = 9):
        self.state_dim = state_dim
        self.action_dim = action_dim

        # Q-Table
        self.q_table: defaultdict = defaultdict(
            lambda: np.zeros(action_dim, dtype=np.float64)
        )

        # Load từ settings
        cfg = settings.get_section("sarsa")
        self.alpha = cfg.get("alpha", 0.1)
        self.gamma = cfg.get("gamma", 0.95)
        self.epsilon = cfg.get("epsilon_start", 1.0)
        self.epsilon_end = cfg.get("epsilon_end", 0.05)
        self.epsilon_decay = cfg.get("epsilon_decay", 0.995)

        # SARSA cần nhớ action ở bước trước để cập nhật
        self._last_state: Optional[tuple] = None
        self._last_action: Optional[int] = None

        # Stats
        self.total_updates: int = 0
        self.episode_rewards: list = []
        self._current_episode_reward: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # STATE DISCRETIZATION
    # ─────────────────────────────────────────────────────────────────────────

    def _discretize(self, state: np.ndarray) -> tuple:
        """Rời rạc hoá state thành 5 mức như Q-Learning."""
        bins = np.array([0.2, 0.4, 0.6, 0.8, 1.01])
        return tuple(int(np.searchsorted(bins, v)) for v in state)

    # ─────────────────────────────────────────────────────────────────────────
    # ACTION SELECTION
    # ─────────────────────────────────────────────────────────────────────────

    def choose_action(self, state: np.ndarray) -> int:
        """Epsilon-greedy — giống Q-Learning nhưng action này được dùng trong SARSA update."""
        if random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        s_key = self._discretize(state)
        return int(np.argmax(self.q_table[s_key]))

    def greedy_action(self, state: np.ndarray) -> int:
        s_key = self._discretize(state)
        return int(np.argmax(self.q_table[s_key]))

    # ─────────────────────────────────────────────────────────────────────────
    # LEARNING — SARSA UPDATE
    # ─────────────────────────────────────────────────────────────────────────

    def learn(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        """
        SARSA update:
            Chọn a' từ s' theo epsilon-greedy (ON-policy)
            Q(s,a) += α [r + γ Q(s',a') - Q(s,a)]

        Đây là điểm khác biệt vs Q-Learning:
            Q-Learning dùng max_a' Q(s',a')
            SARSA     dùng Q(s', choose_action(s'))
        """
        s_key = self._discretize(state)
        ns_key = self._discretize(next_state)

        q_current = self.q_table[s_key][action]

        if done:
            q_next_sa = 0.0
        else:
            # ON-POLICY: chọn action theo epsilon-greedy
            next_action = self.choose_action(next_state)
            q_next_sa = self.q_table[ns_key][next_action]

        td_error = reward + self.gamma * q_next_sa - q_current
        self.q_table[s_key][action] += self.alpha * td_error

        self.total_updates += 1
        self._current_episode_reward += reward

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def end_episode(self):
        self.episode_rewards.append(self._current_episode_reward)
        self._current_episode_reward = 0.0
        self.decay_epsilon()

    # ─────────────────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────────

    def save(self, path: str):
        import os
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        np.save(path, dict(self.q_table), allow_pickle=True)

    def load(self, path: str):
        data = np.load(path, allow_pickle=True).item()
        self.q_table = defaultdict(lambda: np.zeros(self.action_dim), data)

    # ─────────────────────────────────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────────────────────────────────

    def recent_avg_reward(self, n: int = 50) -> float:
        if not self.episode_rewards:
            return 0.0
        return float(np.mean(self.episode_rewards[-n:]))

    @property
    def stats(self) -> dict:
        return {
            "type": "SARSA (On-Policy TD)",
            "epsilon": round(self.epsilon, 4),
            "q_table_size": len(self.q_table),
            "total_updates": self.total_updates,
            "avg_reward_50": round(self.recent_avg_reward(50), 2),
            "episodes": len(self.episode_rewards),
        }
