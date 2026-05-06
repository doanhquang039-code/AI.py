"""
ai/q_learning.py — Tabular Q-Learning Agent

Sử dụng Q-Table để học giá trị Q(s, a) cho từng cặp (state, action).
Phù hợp với state space nhỏ, được rời rạc hoá.

Thuật toán:
    Q(s,a) ← Q(s,a) + α [r + γ max_a' Q(s',a') - Q(s,a)]
"""
import numpy as np
import random
from typing import Tuple
from collections import defaultdict

import config as cfg


class QLearningAgent:
    """
    Tabular Q-Learning với epsilon-greedy exploration.

    State được rời rạc hoá thành tuple hashable để lưu vào Q-Table dict.
    """

    def __init__(self, state_dim: int = cfg.STATE_DIM, action_dim: int = cfg.ACTION_DIM):
        self.state_dim = state_dim
        self.action_dim = action_dim

        # Q-Table: defaultdict(float) → {state_key: [q_val_a0, ..., q_val_a8]}
        self.q_table: defaultdict = defaultdict(
            lambda: np.zeros(action_dim, dtype=np.float64)
        )

        # Hyperparameters
        self.alpha = cfg.Q_CFG.alpha
        self.gamma = cfg.Q_CFG.gamma
        self.epsilon = cfg.Q_CFG.epsilon_start
        self.epsilon_end = cfg.Q_CFG.epsilon_end
        self.epsilon_decay = cfg.Q_CFG.epsilon_decay

        # Stats
        self.total_updates: int = 0
        self.episode_rewards: list = []
        self._current_episode_reward: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # STATE DISCRETIZATION
    # ─────────────────────────────────────────────────────────────────────────

    def _discretize(self, state: np.ndarray) -> tuple:
        """
        Rời rạc hoá state vector thành tuple dùng làm key Q-Table.
        Mỗi sensor chia thành 5 mức: [rất gần, gần, trung, xa, không thấy]
        """
        bins = np.array([0.2, 0.4, 0.6, 0.8, 1.01])
        discrete = []
        for val in state:
            bucket = int(np.searchsorted(bins, val))
            discrete.append(bucket)
        return tuple(discrete)

    # ─────────────────────────────────────────────────────────────────────────
    # ACTION SELECTION
    # ─────────────────────────────────────────────────────────────────────────

    def choose_action(self, state: np.ndarray) -> int:
        """
        Epsilon-greedy: xác suất ε chọn ngẫu nhiên, còn lại chọn greedy.
        """
        if random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)

        state_key = self._discretize(state)
        q_values = self.q_table[state_key]
        return int(np.argmax(q_values))

    def greedy_action(self, state: np.ndarray) -> int:
        """Chọn action tốt nhất (không exploration) — dùng khi evaluate."""
        state_key = self._discretize(state)
        return int(np.argmax(self.q_table[state_key]))

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
    ):
        """
        Cập nhật Q-Table theo công thức Q-Learning:
            Q(s,a) ← Q(s,a) + α [r + γ max Q(s',a') - Q(s,a)]
        """
        s_key = self._discretize(state)
        ns_key = self._discretize(next_state)

        q_current = self.q_table[s_key][action]
        q_next = 0.0 if done else np.max(self.q_table[ns_key])

        td_target = reward + self.gamma * q_next
        td_error = td_target - q_current

        # Update Q
        self.q_table[s_key][action] += self.alpha * td_error
        self.total_updates += 1
        self._current_episode_reward += reward

    def decay_epsilon(self):
        """Giảm epsilon sau mỗi episode."""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def end_episode(self):
        """Gọi sau mỗi episode để lưu stats và decay epsilon."""
        self.episode_rewards.append(self._current_episode_reward)
        self._current_episode_reward = 0.0
        self.decay_epsilon()

    # ─────────────────────────────────────────────────────────────────────────
    # PERSISTENCE
    # ─────────────────────────────────────────────────────────────────────────

    def save(self, path: str):
        """Lưu Q-Table ra file .npz"""
        import os
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        data = {k: v for k, v in self.q_table.items()}
        np.save(path, data, allow_pickle=True)
        print(f"[Q-Learning] Đã lưu Q-Table → {path} ({len(data)} states)")

    def load(self, path: str):
        """Tải Q-Table từ file .npz"""
        data = np.load(path, allow_pickle=True).item()
        self.q_table = defaultdict(lambda: np.zeros(self.action_dim), data)
        print(f"[Q-Learning] Đã tải Q-Table ← {path} ({len(data)} states)")

    # ─────────────────────────────────────────────────────────────────────────
    # STATS
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def q_table_size(self) -> int:
        return len(self.q_table)

    def recent_avg_reward(self, n: int = 50) -> float:
        if not self.episode_rewards:
            return 0.0
        return float(np.mean(self.episode_rewards[-n:]))

    @property
    def stats(self) -> dict:
        return {
            "type": "Q-Learning",
            "epsilon": round(self.epsilon, 4),
            "q_table_size": self.q_table_size,
            "total_updates": self.total_updates,
            "avg_reward_50": round(self.recent_avg_reward(50), 2),
            "episodes": len(self.episode_rewards),
        }
