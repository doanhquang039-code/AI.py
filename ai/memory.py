"""
ai/memory.py — Experience Replay Buffer cho DQN

Lưu trữ các transitions (s, a, r, s', done) và lấy mẫu ngẫu nhiên
để huấn luyện neural network, phá vỡ correlation giữa các samples.
"""
import random
import numpy as np
from collections import deque
from typing import Tuple, List


class ReplayBuffer:
    """
    Experience Replay Buffer tiêu chuẩn.
    Lưu tối đa `capacity` transitions, tự động loại bỏ cũ nhất.
    """

    def __init__(self, capacity: int):
        self.buffer: deque = deque(maxlen=capacity)

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        """Thêm một transition vào buffer."""
        self.buffer.append((state, action, reward, next_state, done))

    def sample(
        self, batch_size: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Lấy ngẫu nhiên `batch_size` transitions.
        Trả về (states, actions, rewards, next_states, dones) dạng numpy arrays.
        """
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.float32),
        )

    def __len__(self) -> int:
        return len(self.buffer)

    @property
    def is_ready(self) -> bool:
        """Buffer đã đủ dữ liệu để lấy mẫu chưa."""
        from config import DQN_CFG
        return len(self.buffer) >= DQN_CFG.batch_size


class PrioritizedReplayBuffer:
    """
    Prioritized Experience Replay (PER) — ưu tiên sample những transitions
    có TD error lớn (quan trọng hơn để học).

    Dùng SumTree để sample hiệu quả O(log N).
    """

    def __init__(self, capacity: int, alpha: float = 0.6, beta: float = 0.4):
        self.capacity = capacity
        self.alpha = alpha      # Mức độ ưu tiên hóa (0 = uniform, 1 = fully prioritized)
        self.beta = beta        # Importance sampling correction
        self.beta_increment = 0.001

        self.buffer: List = []
        self.priorities: np.ndarray = np.zeros(capacity, dtype=np.float32)
        self.pos: int = 0
        self.max_priority: float = 1.0

    def push(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        transition = (state, action, reward, next_state, done)
        idx = self.pos % self.capacity

        if len(self.buffer) < self.capacity:
            self.buffer.append(transition)
        else:
            self.buffer[idx] = transition

        self.priorities[idx] = self.max_priority
        self.pos += 1

    def sample(
        self, batch_size: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Trả về: states, actions, rewards, next_states, dones, indices, weights
        """
        n = len(self.buffer)
        priorities = self.priorities[:n]
        probs = priorities ** self.alpha
        probs /= probs.sum()

        indices = np.random.choice(n, batch_size, p=probs, replace=False)

        # Importance sampling weights
        weights = (n * probs[indices]) ** (-self.beta)
        weights /= weights.max()
        self.beta = min(1.0, self.beta + self.beta_increment)

        batch = [self.buffer[i] for i in indices]
        states, actions, rewards, next_states, dones = zip(*batch)

        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.float32),
            indices,
            np.array(weights, dtype=np.float32),
        )

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """Cập nhật priority dựa trên TD error."""
        for idx, td_err in zip(indices, td_errors):
            priority = (abs(td_err) + 1e-6)
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)

    def __len__(self) -> int:
        return len(self.buffer)

    @property
    def is_ready(self) -> bool:
        from config import DQN_CFG
        return len(self.buffer) >= DQN_CFG.batch_size
