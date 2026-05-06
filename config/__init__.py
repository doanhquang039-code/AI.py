"""
config/__init__.py — Cấu hình toàn cục cho dự án AI Virtual World
"""
from dataclasses import dataclass
from config.settings_manager import settings

@dataclass
class WorldConfig:
    @property
    def width(self): return settings.get("world", "width", default=30)
    @property
    def height(self): return settings.get("world", "height", default=30)
    @property
    def cell_size(self): return settings.get("world", "cell_size", default=24)
    @property
    def num_food(self): return settings.get("world", "num_food", default=40)
    @property
    def num_hazards(self): return settings.get("world", "num_hazards", default=15)
    @property
    def num_obstacles(self): return settings.get("world", "num_obstacles", default=30)
    @property
    def food_respawn_rate(self): return settings.get("world", "food_respawn_rate", default=0.03)
    @property
    def max_steps(self): return settings.get("world", "max_steps", default=1000)

@dataclass
class AgentConfig:
    @property
    def num_agents(self): return settings.get("agent", "num_agents", default=4)
    @property
    def max_energy(self): return settings.get("agent", "max_energy", default=100.0)
    @property
    def energy_decay(self): return settings.get("agent", "energy_decay", default=0.3)
    @property
    def energy_food(self): return settings.get("agent", "energy_food", default=25.0)
    @property
    def sensor_range(self): return settings.get("agent", "sensor_range", default=5)
    @property
    def reward_food(self): return settings.get("agent", "reward_food", default=10.0)
    @property
    def reward_hazard(self): return settings.get("agent", "reward_hazard", default=-5.0)
    @property
    def reward_death(self): return settings.get("agent", "reward_death", default=-20.0)
    @property
    def reward_step(self): return settings.get("agent", "reward_step", default=-0.1)
    @property
    def reward_survive_bonus(self): return settings.get("agent", "reward_survive_bonus", default=50.0)

@dataclass
class QLearningConfig:
    @property
    def alpha(self): return settings.get("q_learning", "alpha", default=0.1)
    @property
    def gamma(self): return settings.get("q_learning", "gamma", default=0.95)
    @property
    def epsilon_start(self): return settings.get("q_learning", "epsilon_start", default=1.0)
    @property
    def epsilon_end(self): return settings.get("q_learning", "epsilon_end", default=0.05)
    @property
    def epsilon_decay(self): return settings.get("q_learning", "epsilon_decay", default=0.995)

@dataclass
class DQNConfig:
    @property
    def lr(self): return settings.get("dqn", "lr", default=0.001)
    @property
    def gamma(self): return settings.get("dqn", "gamma", default=0.99)
    @property
    def epsilon_start(self): return settings.get("dqn", "epsilon_start", default=1.0)
    @property
    def epsilon_end(self): return settings.get("dqn", "epsilon_end", default=0.01)
    @property
    def epsilon_decay(self): return settings.get("dqn", "epsilon_decay", default=0.995)
    @property
    def batch_size(self): return settings.get("dqn", "batch_size", default=64)
    @property
    def memory_size(self): return settings.get("dqn", "memory_size", default=50000)
    @property
    def target_update_freq(self): return settings.get("dqn", "target_update_freq", default=100)
    @property
    def hidden_dim(self): return settings.get("dqn", "hidden_dim", default=128)
    @property
    def num_hidden_layers(self): return settings.get("dqn", "num_hidden_layers", default=3)
    @property
    def use_double_dqn(self): return settings.get("dqn", "use_double_dqn", default=True)

@dataclass
class TrainingConfig:
    @property
    def num_episodes(self): return settings.get("training", "num_episodes", default=2000)
    @property
    def save_every(self): return settings.get("training", "save_every", default=100)
    @property
    def log_every(self): return settings.get("training", "log_every", default=10)
    @property
    def model_dir(self): return settings.get("training", "model_dir", default="models")
    @property
    def log_dir(self): return settings.get("training", "log_dir", default="logs")

@dataclass
class VisualConfig:
    @property
    def fps(self): return settings.get("visualization", "fps", default=30)
    @fps.setter
    def fps(self, value): settings.set("visualization", "fps", value)
    
    @property
    def show_sensors(self): return settings.get("visualization", "show_sensors", default=True)
    @show_sensors.setter
    def show_sensors(self, value): settings.set("visualization", "show_sensors", value)
    
    @property
    def show_trails(self): return settings.get("visualization", "show_trails", default=True)
    @show_trails.setter
    def show_trails(self, value): settings.set("visualization", "show_trails", value)
    
    @property
    def trail_length(self): return settings.get("visualization", "trail_length", default=20)

    # Colors
    COLOR_BG = (15, 15, 26)
    COLOR_GRID = (30, 30, 50)
    COLOR_FOOD = (16, 185, 129)
    COLOR_HAZARD = (244, 63, 94)
    COLOR_OBSTACLE = (55, 65, 81)
    COLOR_SENSOR = (255, 255, 255, 30)
    COLOR_HUD_BG = (10, 10, 20)
    COLOR_TEXT = (240, 240, 255)

@dataclass
class DashboardConfig:
    @property
    def host(self): return settings.get("dashboard", "host", default="0.0.0.0")
    @property
    def port(self): return settings.get("dashboard", "port", default=5000)
    debug: bool = False

# Instances
WORLD = WorldConfig()
AGENT = AgentConfig()
Q_CFG = QLearningConfig()
DQN_CFG = DQNConfig()
TRAIN = TrainingConfig()
VISUAL = VisualConfig()
DASH = DashboardConfig()

STATE_DIM = 8 * 3 + 3
ACTION_DIM = 9
