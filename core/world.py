"""
core/world.py — Môi trường thế giới ảo 2D

Thế giới là một grid W×H. Mỗi tick, agents thực hiện hành động,
môi trường cập nhật trạng thái và trả về rewards.
"""
import random
import numpy as np
from typing import Dict, List, Optional, Tuple

import config as cfg
from core.entities import Entity, EntityType, Food, Hazard, Obstacle, Portal
from core.weather import WeatherManager


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
        self.portals: Dict[Tuple[int, int], Portal] = {}

        # Stats
        self.step_count: int = 0
        self.food_eaten: int = 0

        self.current_num_food = cfg.WORLD.num_food
        self.current_num_hazards = cfg.WORLD.num_hazards

        self.weather_manager = WeatherManager(change_interval=400)

        self._initialize()

    def update_curriculum(self, episode: int):
        from config.settings_manager import settings
        if not settings.get("training", "curriculum_learning", default=False):
            self.current_num_food = cfg.WORLD.num_food
            self.current_num_hazards = cfg.WORLD.num_hazards
            return

        max_ep = 500
        progress = min(1.0, episode / max_ep)

        # Mới đầu nhiều thức ăn, sau giảm dần về số lượng chuẩn
        self.current_num_food = int(cfg.WORLD.num_food * (1.5 - 0.5 * progress))
        # Mới đầu không có hazard, sau tăng dần lên mức chuẩn
        self.current_num_hazards = int(cfg.WORLD.num_hazards * progress)

    # ─────────────────────────────────────────────────────────────────────────
    # INIT
    # ─────────────────────────────────────────────────────────────────────────

    def _initialize(self):
        """Khởi tạo world với các thực thể ngẫu nhiên."""
        self.grid.fill(EntityType.EMPTY)
        self.foods.clear()
        self.hazards.clear()
        self.obstacles.clear()
        self.portals.clear()

        # Sinh obstacles bằng Cellular Automata
        self._spawn_obstacles(cfg.WORLD.num_obstacles)
        # Sinh portals
        self._spawn_portals()
        # Sinh hazards
        self._spawn_entities(self.current_num_hazards, self._add_hazard)
        # Sinh food
        self._spawn_entities(self.current_num_food, self._add_food)

    def reset(self):
        """Reset world về trạng thái ban đầu."""
        self.step_count = 0
        self.food_eaten = 0
        self.weather_manager.reset()
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
        """Sinh obstacles theo thuật toán Cellular Automata để tạo Hang động (Cave)."""
        fill_prob = 0.28
        temp_grid = np.random.choice([EntityType.OBSTACLE.value, EntityType.EMPTY.value], 
                                     size=(self.H, self.W), p=[fill_prob, 1 - fill_prob])
        
        for _ in range(4):
            new_grid = temp_grid.copy()
            for y in range(self.H):
                for x in range(self.W):
                    rock_count = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if nx < 0 or ny < 0 or nx >= self.W or ny >= self.H:
                                rock_count += 1
                            elif temp_grid[ny, nx] == EntityType.OBSTACLE.value:
                                rock_count += 1
                    if rock_count > 4:
                        new_grid[y, x] = EntityType.OBSTACLE.value
                    elif rock_count < 4:
                        new_grid[y, x] = EntityType.EMPTY.value
            temp_grid = new_grid
            
        for y in range(self.H):
            for x in range(self.W):
                if temp_grid[y, x] == EntityType.OBSTACLE.value:
                    self._add_obstacle(x, y)

    def _spawn_portals(self):
        """Sinh 1 cặp portal."""
        pos1 = self._random_empty_cell()
        pos2 = self._random_empty_cell()
        if pos1 and pos2:
            p1 = Portal(x=pos1[0], y=pos1[1], entity_type=EntityType.PORTAL)
            p2 = Portal(x=pos2[0], y=pos2[1], entity_type=EntityType.PORTAL)
            p1.linked_portal = p2
            p2.linked_portal = p1
            self.portals[pos1] = p1
            self.portals[pos2] = p2
            self.grid[pos1[1], pos1[0]] = EntityType.PORTAL

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

    def spawn_custom_food(self, x: int, y: int):
        """God mode: tự sinh food."""
        if 0 <= x < self.W and 0 <= y < self.H and self.grid[y, x] == EntityType.EMPTY:
            self._add_food(x, y)

    def spawn_custom_hazard(self, x: int, y: int):
        """God mode: tự sinh hazard."""
        if 0 <= x < self.W and 0 <= y < self.H and self.grid[y, x] == EntityType.EMPTY:
            self._add_hazard(x, y)

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
        - Cập nhật thời tiết
        - Tái sinh thức ăn ngẫu nhiên
        """
        self.step_count += 1
        self.weather_manager.step()

        # Tái sinh thức ăn
        if len(self.foods) < self.current_num_food:
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
        """Lấy damage từ hazard tại (x, y) phụ thuộc vào thời tiết."""
        if (x, y) in self.hazards:
            return self.hazards[(x, y)].damage * self.weather_manager.get_hazard_multiplier()
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
