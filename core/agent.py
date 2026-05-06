"""
core/agent.py — Base class và logic cho AI Agent trong thế giới ảo

Mỗi agent có:
    - Vị trí (x, y) trong world
    - Năng lượng (energy)
    - Lịch sử di chuyển (trail)
    - Giao diện với thuật toán AI (q_learning / dqn)
"""
import numpy as np
from typing import Optional, List, Tuple, TYPE_CHECKING
from enum import Enum

import config as cfg
from core.world import VirtualWorld, ACTIONS, EntityType

if TYPE_CHECKING:
    from ai.q_learning import QLearningAgent
    from ai.dqn import DQNAgent


class AgentType(Enum):
    Q_LEARNING = "Q-Learning"
    SARSA      = "SARSA"
    DQN        = "DQN"
    PPO        = "PPO"
    A2C        = "A2C"
    PATHFINDER = "Pathfinder"


class WorldAgent:
    """
    Đại diện cho một AI Agent sống trong VirtualWorld.
    Kết nối logic sinh tồn với thuật toán học.
    """

    def __init__(
        self,
        agent_id: int,
        agent_type: AgentType,
        brain,                          # QLearningAgent hoặc DQNAgent
        world: VirtualWorld,
        color: Tuple[int, int, int],
    ):
        self.id = agent_id
        self.agent_type = agent_type
        self.brain = brain
        self.world = world
        self.color = color

        if hasattr(self.brain, "set_agent"):
            self.brain.set_agent(self)

        # State
        self.x: int = 0
        self.y: int = 0
        self.energy: float = cfg.AGENT.max_energy
        self.is_alive: bool = True

        # Stats per episode
        self.score: float = 0.0
        self.steps_alive: int = 0
        self.food_eaten: int = 0
        self.total_reward: float = 0.0

        # Lịch sử vị trí (trail)
        self.trail: List[Tuple[int, int]] = []

        self._spawn()

    # ─────────────────────────────────────────────────────────────────────────
    # SPAWN / RESET
    # ─────────────────────────────────────────────────────────────────────────

    def _spawn(self):
        """Đặt agent vào một ô trống ngẫu nhiên."""
        pos = self.world.get_empty_spawn_point()
        if pos:
            self.x, self.y = pos
        else:
            self.x, self.y = 0, 0
        self.energy = cfg.AGENT.max_energy
        self.is_alive = True
        self.trail.clear()

    def reset(self):
        """Reset agent cho episode mới."""
        self.score = 0.0
        self.steps_alive = 0
        self.food_eaten = 0
        self.total_reward = 0.0
        self._spawn()

    # ─────────────────────────────────────────────────────────────────────────
    # STATE
    # ─────────────────────────────────────────────────────────────────────────

    def get_state(self) -> np.ndarray:
        """
        Lấy state vector (27 chiều) của agent:
            - 24 sensor readings (8 hướng × 3 loại entity)
            - energy (normalized)
            - pos_x (normalized)
            - pos_y (normalized)
        """
        sensors = self.world.get_sensor_readings(
            self.x, self.y, cfg.AGENT.sensor_range
        )
        energy_norm = self.energy / cfg.AGENT.max_energy
        px_norm = self.x / (self.world.W - 1)
        py_norm = self.y / (self.world.H - 1)

        return np.append(sensors, [energy_norm, px_norm, py_norm])

    # ─────────────────────────────────────────────────────────────────────────
    # STEP
    # ─────────────────────────────────────────────────────────────────────────

    def step(self) -> float:
        """
        Thực hiện một bước trong world:
        1. Lấy state hiện tại
        2. Chọn action từ brain
        3. Thực hiện action, tính reward
        4. Học từ (state, action, reward, next_state)

        Trả về: reward nhận được trong bước này
        """
        if not self.is_alive:
            return 0.0

        state = self.get_state()
        action = self.brain.choose_action(state)
        reward = self._execute_action(action)
        next_state = self.get_state()

        # Học
        done = not self.is_alive
        self.brain.learn(state, action, reward, next_state, done)

        self.total_reward += reward
        self.steps_alive += 1
        return reward

    def _execute_action(self, action: int) -> float:
        """Thực hiện action, cập nhật vị trí, energy, trả về reward."""
        dx, dy = ACTIONS[action]
        nx, ny = self.x + dx, self.y + dy
        reward = cfg.AGENT.reward_step  # Phạt nhỏ mỗi bước

        # Kiểm tra di chuyển hợp lệ
        if not self.world.is_walkable(nx, ny):
            # Đâm vào tường — không di chuyển, phạt thêm
            reward -= 1.0
        else:
            # Di chuyển thành công
            self.x, self.y = nx, ny
            cell = self.world.get_cell(self.x, self.y)

            if cell == EntityType.FOOD:
                energy_gained = self.world.consume_food(self.x, self.y)
                self.energy = min(cfg.AGENT.max_energy, self.energy + energy_gained)
                reward += cfg.AGENT.reward_food
                self.food_eaten += 1
                self.score += cfg.AGENT.reward_food

            elif cell == EntityType.HAZARD:
                damage = self.world.get_hazard_damage(self.x, self.y)
                self.energy -= damage
                reward += cfg.AGENT.reward_hazard

            elif cell == EntityType.PORTAL:
                portal = self.world.portals.get((self.x, self.y))
                if portal and portal.linked_portal:
                    self.x, self.y = portal.linked_portal.x, portal.linked_portal.y
                    self.trail.clear()
                    
                    import json, os
                    from datetime import datetime
                    os.makedirs("logs", exist_ok=True)
                    event = {"time": datetime.now().strftime("%H:%M:%S"), "msg": f"🌀 Agent {self.id} ({self.agent_type.value}) vừa bị dịch chuyển không gian!"}
                    with open("logs/events.jsonl", "a", encoding="utf-8") as f:
                        f.write(json.dumps(event, ensure_ascii=False) + "\n")

        # Giảm energy theo thời gian (phụ thuộc thời tiết)
        self.energy -= cfg.AGENT.energy_decay * self.world.weather_manager.get_energy_multiplier()

        # Cập nhật trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > cfg.VISUAL.trail_length:
            self.trail.pop(0)

        # Kiểm tra chết
        if self.energy <= 0:
            self.energy = 0.0
            self.is_alive = False
            reward += cfg.AGENT.reward_death

        return reward

    # ─────────────────────────────────────────────────────────────────────────
    # PROPERTIES
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def energy_pct(self) -> float:
        """Phần trăm năng lượng còn lại [0, 1]."""
        return self.energy / cfg.AGENT.max_energy

    @property
    def info(self) -> dict:
        return {
            "id": self.id,
            "type": self.agent_type.value,
            "alive": self.is_alive,
            "energy": round(self.energy, 1),
            "score": round(self.score, 1),
            "food_eaten": self.food_eaten,
            "steps_alive": self.steps_alive,
            "total_reward": round(self.total_reward, 2),
            "epsilon": round(getattr(self.brain, "epsilon", 0), 4),
        }
