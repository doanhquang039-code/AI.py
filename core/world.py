"""
core/world.py — Môi trường thế giới ảo 2D

Thế giới là một grid W×H. Mỗi tick, agents thực hiện hành động,
môi trường cập nhật trạng thái và trả về rewards.
"""
import random
import numpy as np
from typing import Dict, List, Optional, Tuple

import config as cfg
from core.entities import Entity, EntityType, Food, Hazard, Obstacle


# 8 hướng di chuyển: (dx, dy)
DIRECTIONS = [
    (-1, -1), (0, -1), (1, -1),   # ↖ ↑ ↗
    (-1,  0),          (1,  0),   # ← → 
    (-1,  1), (0,  1), (1,  1),   # ↙ ↓ ↘
]
# Action index 8 = đứng yên (0, 0)
ACTIONS = DIRECTIONS + [(0, 0)]   # 9 actions


class VirtualWorld:
    """
    Thế giới ảo 2D chứa food, hazards, obstacles và AI agents.

    Mỗi cell trong grid có thể chứa:
        - EMPTY    : ô trống
        - FOOD     : thức ăn
        - HAZARD   : ô nguy hiểm
        - OBSTACLE : chướng ngại vật
        - AGENT    : agent (lưu trên lớp riêng)
    """

    def __init__(self):
        self.W = cfg.WORLD.width
        self.H = cfg.WORLD.height

        # Grid lưu entity_type tại mỗi ô (trừ agent)
        self.grid: np.ndarray = np.zeros((self.H, self.W), dtype=np.int32)

        # Danh sách thực thể
        self.foods: Dict[Tuple[int, int], Food] = {}
        self.hazards: Dict[Tuple[int, int], Hazard] = {}
        self.obstacles: Dict[Tuple[int, int], Obstacle] = {}

        # Stats
        self.step_count: int = 0
        self.food_eaten: int = 0

        self._initialize()

    # ─────────────────────────────────────────────────────────────────────────
    # INIT
    # ─────────────────────────────────────────────────────────────────────────

    def _initialize(self):
        """Khởi tạo world với các thực thể ngẫu nhiên."""
        self.grid.fill(EntityType.EMPTY)
        self.foods.clear()
        self.hazards.clear()
        self.obstacles.clear()

        # Sinh obstacles
        self._spawn_obstacles(cfg.WORLD.num_obstacles)
        # Sinh hazards
        self._spawn_entities(cfg.WORLD.num_hazards, self._add_hazard)
        # Sinh food
        self._spawn_entities(cfg.WORLD.num_food, self._add_food)

    def reset(self):
        """Reset world về trạng thái ban đầu."""
        self.step_count = 0
        self.food_eaten = 0
        self._initialize()

    # ─────────────────────────────────────────────────────────────────────────
    # SPAWN HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _random_empty_cell(self) -> Optional[Tuple[int, int]]:
        """Tìm một ô trống ngẫu nhiên. Trả về None nếu không có."""
        attempts = 0
        while attempts < 200:
            x = random.randint(0, self.W - 1)
            y = random.randint(0, self.H - 1)
            if self.grid[y, x] == EntityType.EMPTY:
                return (x, y)
            attempts += 1
        return None

    def _spawn_obstacles(self, n: int):
        """Sinh obstacles theo cụm để tạo bức tường tự nhiên."""
        placed = 0
        while placed < n:
            pos = self._random_empty_cell()
            if pos is None:
                break
            # Cụm 1-3 ô
            cluster = random.randint(1, 3)
            x, y = pos
            for _ in range(cluster):
                if placed >= n:
                    break
                if 0 <= x < self.W and 0 <= y < self.H and self.grid[y, x] == EntityType.EMPTY:
                    self._add_obstacle(x, y)
                    placed += 1
                x += random.randint(-1, 1)
                y += random.randint(-1, 1)

    def _spawn_entities(self, n: int, add_fn):
        """Sinh n thực thể dùng hàm add_fn."""
        for _ in range(n):
            pos = self._random_empty_cell()
            if pos:
                add_fn(*pos)

    def _add_food(self, x: int, y: int):
        food = Food(x=x, y=y, entity_type=EntityType.FOOD,
                    energy_value=cfg.AGENT.energy_food)
        self.foods[(x, y)] = food
        self.grid[y, x] = EntityType.FOOD

    def _add_hazard(self, x: int, y: int):
        hazard = Hazard(x=x, y=y, entity_type=EntityType.HAZARD,
                        damage=abs(cfg.AGENT.reward_hazard))
        self.hazards[(x, y)] = hazard
        self.grid[y, x] = EntityType.HAZARD

    def _add_obstacle(self, x: int, y: int):
        obs = Obstacle(x=x, y=y, entity_type=EntityType.OBSTACLE)
        self.obstacles[(x, y)] = obs
        self.grid[y, x] = EntityType.OBSTACLE

    # ─────────────────────────────────────────────────────────────────────────
    # QUERIES
    # ─────────────────────────────────────────────────────────────────────────

    def is_walkable(self, x: int, y: int) -> bool:
        """Kiểm tra ô có thể đi được không."""
        if not (0 <= x < self.W and 0 <= y < self.H):
            return False
        return self.grid[y, x] != EntityType.OBSTACLE

    def get_cell(self, x: int, y: int) -> EntityType:
        """Lấy loại thực thể tại ô (x, y)."""
        if not (0 <= x < self.W and 0 <= y < self.H):
            return EntityType.OBSTACLE   # Coi ngoài biên là obstacle
        return EntityType(self.grid[y, x])

    def get_sensor_readings(
        self, ax: int, ay: int, sensor_range: int
    ) -> np.ndarray:
        """
        Đọc sensors của agent tại (ax, ay).
        Trả về vector 24 chiều:
            Với mỗi trong 8 hướng: [dist_food, dist_hazard, dist_obstacle]
            (chuẩn hoá về [0, 1], = 1.0 nếu không thấy gì)
        """
        readings = np.ones(8 * 3, dtype=np.float32)

        for dir_idx, (dx, dy) in enumerate(DIRECTIONS):
            for dist in range(1, sensor_range + 1):
                nx, ny = ax + dx * dist, ay + dy * dist
                cell = self.get_cell(nx, ny)
                norm_dist = dist / sensor_range

                if cell == EntityType.FOOD:
                    readings[dir_idx * 3 + 0] = norm_dist
                    break
                elif cell == EntityType.HAZARD:
                    readings[dir_idx * 3 + 1] = norm_dist
                    break
                elif cell == EntityType.OBSTACLE:
                    readings[dir_idx * 3 + 2] = norm_dist
                    break

        return readings

    # ─────────────────────────────────────────────────────────────────────────
    # STEP
    # ─────────────────────────────────────────────────────────────────────────

    def step(self):
        """
        Cập nhật world mỗi tick:
        - Tái sinh thức ăn ngẫu nhiên
        """
        self.step_count += 1

        # Tái sinh thức ăn
        if len(self.foods) < cfg.WORLD.num_food:
            if random.random() < cfg.WORLD.food_respawn_rate:
                pos = self._random_empty_cell()
                if pos:
                    self._add_food(*pos)

    def consume_food(self, x: int, y: int) -> float:
        """Tiêu thụ thức ăn tại (x, y). Trả về energy nhận được."""
        if (x, y) in self.foods:
            food = self.foods.pop((x, y))
            self.grid[y, x] = EntityType.EMPTY
            self.food_eaten += 1
            return food.energy_value
        return 0.0

    def get_hazard_damage(self, x: int, y: int) -> float:
        """Lấy damage từ hazard tại (x, y)."""
        if (x, y) in self.hazards:
            return self.hazards[(x, y)].damage
        return 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # INFO
    # ─────────────────────────────────────────────────────────────────────────

    def get_empty_spawn_point(self) -> Optional[Tuple[int, int]]:
        """Lấy điểm spawn trống để đặt agent mới."""
        return self._random_empty_cell()

    @property
    def stats(self) -> dict:
        return {
            "step": self.step_count,
            "food_count": len(self.foods),
            "food_eaten": self.food_eaten,
        }
