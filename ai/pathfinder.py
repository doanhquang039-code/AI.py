"""
ai/pathfinder.py — Agent dùng thuật toán A* Search & QuickSort.
"""
import numpy as np
from typing import Any
from core.algorithms import a_star_search, quick_sort, manhattan_distance
from core.world import DIRECTIONS, ACTIONS, EntityType

class AStarAgent:
    """
    Sử dụng thuật toán A* để tìm đường tối ưu tới thức ăn gần nhất.
    Dùng QuickSort để sắp xếp danh sách thức ăn theo khoảng cách.
    """
    def __init__(self, state_dim: int = 27, action_dim: int = 9):
        self.agent = None
        self.path = []
        self.stats = {"algorithm": "A-Star Search & QuickSort"}

    def set_agent(self, agent):
        self.agent = agent

    def choose_action(self, state: np.ndarray) -> int:
        if self.agent is None:
            return 8 # Đứng yên

        world = self.agent.world
        agent_pos = (self.agent.x, self.agent.y)

        # Cập nhật đường đi nếu đã tới đích hoặc đường đi bị vật cản
        if not self.path or not world.is_walkable(*self.path[0]):
            self._calculate_new_path(world, agent_pos)

        if not self.path:
            return 8 # Không tìm được đường, đứng yên

        next_pos = self.path.pop(0)
        dx, dy = next_pos[0] - agent_pos[0], next_pos[1] - agent_pos[1]
        
        # Tìm action index tương ứng
        for i, (adx, ady) in enumerate(ACTIONS):
            if dx == adx and dy == ady:
                return i
        return 8

    def _calculate_new_path(self, world, agent_pos):
        foods = list(world.foods.keys())
        if not foods:
            self.path = []
            return

        # Sắp xếp thức ăn theo khoảng cách bằng QuickSort
        sorted_foods = quick_sort(foods, key=lambda f: manhattan_distance(agent_pos, f))

        for target in sorted_foods:
            path = a_star_search(
                start=agent_pos,
                target=target,
                is_walkable=lambda x, y: world.is_walkable(x, y) and world.get_cell(x, y) != EntityType.HAZARD,
                max_steps=500
            )
            if path:
                self.path = path
                return
        
        self.path = [] # Không tìm thấy

    def learn(self, state, action, reward, next_state, done):
        pass # A* không cần học từ experience

    def end_episode(self):
        self.path = []
