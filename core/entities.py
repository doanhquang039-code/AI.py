"""
core/entities.py — Các thực thể tồn tại trong thế giới ảo
"""
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Tuple


class EntityType(IntEnum):
    EMPTY = 0
    FOOD = 1
    HAZARD = 2
    OBSTACLE = 3
    AGENT = 4
    PORTAL = 5


@dataclass
class Entity:
    """Base class cho mọi thực thể trong world."""
    x: int
    y: int
    entity_type: EntityType

    @property
    def pos(self) -> Tuple[int, int]:
        return (self.x, self.y)


@dataclass
class Food(Entity):
    """Thức ăn — agent nhận reward khi đứng lên ô này."""
    energy_value: float = 25.0
    is_active: bool = True

    def __post_init__(self):
        self.entity_type = EntityType.FOOD


@dataclass
class Hazard(Entity):
    """Ô nguy hiểm — agent mất energy khi đứng lên."""
    damage: float = 5.0

    def __post_init__(self):
        self.entity_type = EntityType.HAZARD


@dataclass
class Obstacle(Entity):
    """Chướng ngại vật — agent không thể đi qua."""
    def __post_init__(self):
        self.entity_type = EntityType.OBSTACLE


@dataclass
class Portal(Entity):
    """Cổng dịch chuyển — agent chạm vào sẽ bị dịch chuyển tới cổng còn lại."""
    linked_portal: 'Portal' = None
    
    def __post_init__(self):
        self.entity_type = EntityType.PORTAL
