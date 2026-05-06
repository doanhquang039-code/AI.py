"""
core/weather.py — Hệ thống thời tiết động
"""
from enum import Enum
import random

class WeatherType(Enum):
    NORMAL = "Normal"
    WINTER = "Winter"
    HEATWAVE = "Heatwave"
    STORM = "Storm"

class WeatherManager:
    """Quản lý thời tiết hiện tại và tự động thay đổi sau mỗi khoảng thời gian."""
    def __init__(self, change_interval: int = 300):
        self.current = WeatherType.NORMAL
        self.change_interval = change_interval
        self.step_count = 0
        self.active_weathers = [
            WeatherType.NORMAL, 
            WeatherType.WINTER, 
            WeatherType.HEATWAVE, 
            WeatherType.STORM
        ]
        
    def reset(self):
        self.current = WeatherType.NORMAL
        self.step_count = 0
        
    def step(self):
        self.step_count += 1
        if self.step_count >= self.change_interval:
            self.step_count = 0
            # Chọn ngẫu nhiên thời tiết mới, nhưng thiên vị NORMAL hơn một chút
            weights = [0.4, 0.2, 0.2, 0.2] 
            self.current = random.choices(self.active_weathers, weights=weights, k=1)[0]
            
    def get_energy_multiplier(self) -> float:
        """Hệ số tiêu hao năng lượng. Winter tốn gấp đôi máu."""
        if self.current == WeatherType.WINTER:
            return 2.0
        elif self.current == WeatherType.STORM:
            return 1.5
        return 1.0
        
    def get_hazard_multiplier(self) -> float:
        """Hệ số sát thương của chướng ngại vật (Lửa)."""
        if self.current == WeatherType.HEATWAVE:
            return 1.8
        elif self.current == WeatherType.WINTER:
            return 0.5
        return 1.0
