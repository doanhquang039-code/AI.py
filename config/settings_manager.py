"""
config/settings_manager.py — Quản lý settings từ YAML

Load, validate, save và hot-reload settings.
"""
import os
import copy
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("[Settings] PyYAML not found. Run: pip install pyyaml")

_SETTINGS_PATH = Path(__file__).parent / "settings.yaml"

# Default settings (fallback nếu không có YAML)
_DEFAULTS = {
    "language": "vi",
    "world": {
        "width": 30, "height": 30, "cell_size": 24,
        "num_food": 40, "num_hazards": 15, "num_obstacles": 30,
        "food_respawn_rate": 0.03, "max_steps": 1000,
    },
    "agent": {
        "num_agents": 6, "max_energy": 100.0, "energy_decay": 0.3,
        "energy_food": 25.0, "sensor_range": 5,
        "reward_food": 10.0, "reward_hazard": -5.0,
        "reward_death": -20.0, "reward_step": -0.1,
        "reward_survive_bonus": 50.0,
        "algorithms": ["q_learning", "dqn", "sarsa", "ppo", "a2c"],
    },
    "q_learning": {
        "alpha": 0.1, "gamma": 0.95,
        "epsilon_start": 1.0, "epsilon_end": 0.05, "epsilon_decay": 0.995,
    },
    "sarsa": {
        "alpha": 0.1, "gamma": 0.95,
        "epsilon_start": 1.0, "epsilon_end": 0.05, "epsilon_decay": 0.995,
    },
    "dqn": {
        "lr": 0.001, "gamma": 0.99,
        "epsilon_start": 1.0, "epsilon_end": 0.01, "epsilon_decay": 0.995,
        "batch_size": 64, "memory_size": 50000, "target_update_freq": 100,
        "hidden_dim": 128, "num_hidden_layers": 3,
        "use_double_dqn": True, "use_dueling": True, "use_per": True,
    },
    "ppo": {
        "lr_actor": 0.0003, "lr_critic": 0.001, "gamma": 0.99,
        "gae_lambda": 0.95, "clip_ratio": 0.2,
        "epochs_per_update": 4, "rollout_steps": 256,
        "entropy_coef": 0.01, "hidden_dim": 128,
    },
    "a2c": {
        "lr": 0.0007, "gamma": 0.99, "entropy_coef": 0.01,
        "value_loss_coef": 0.5, "max_grad_norm": 0.5,
        "n_steps": 5, "hidden_dim": 128,
    },
    "training": {
        "num_episodes": 2000, "save_every": 100,
        "log_every": 10, "model_dir": "models", "log_dir": "logs",
    },
    "visualization": {
        "fps": 30, "show_sensors": True, "show_trails": True,
        "trail_length": 20, "fullscreen": False,
    },
    "dashboard": {"host": "0.0.0.0", "port": 5000},
    "agent_colors": {
        "q_learning": [99, 102, 241],
        "sarsa":      [56, 189, 248],
        "dqn":        [251, 191, 36],
        "ppo":        [16, 185, 129],
        "a2c":        [244, 63, 94],
    },
}


class SettingsManager:
    """
    Singleton quản lý settings.
    Hỗ trợ load từ YAML, get/set nested keys, save lại file.
    """
    _instance: Optional["SettingsManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = {}
            cls._instance._load()
        return cls._instance

    # ─────────────────────────────────────────────────────────────────────────
    # LOAD / SAVE
    # ─────────────────────────────────────────────────────────────────────────

    def _load(self):
        """Load settings từ YAML, merge với defaults."""
        self._data = copy.deepcopy(_DEFAULTS)
        if YAML_AVAILABLE and _SETTINGS_PATH.exists():
            try:
                with open(_SETTINGS_PATH, encoding="utf-8") as f:
                    user = yaml.safe_load(f) or {}
                self._deep_merge(self._data, user)
                print(f"[Settings] Loaded from {_SETTINGS_PATH}")
            except Exception as e:
                print(f"[Settings] Error loading YAML: {e}. Using defaults.")
        else:
            print("[Settings] Using default settings.")

    def reload(self):
        """Hot-reload settings từ file."""
        self._load()
        print("[Settings] Settings reloaded.")

    def save(self, path: Optional[str] = None):
        """Lưu settings hiện tại ra file YAML."""
        if not YAML_AVAILABLE:
            print("[Settings] PyYAML not available, cannot save.")
            return
        target = Path(path) if path else _SETTINGS_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False)
        print(f"[Settings] Saved to {target}")

    def _deep_merge(self, base: dict, override: dict):
        """Merge nested dicts (override wins)."""
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    # ─────────────────────────────────────────────────────────────────────────
    # GET / SET
    # ─────────────────────────────────────────────────────────────────────────

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Lấy giá trị nested.
        Ví dụ: settings.get("dqn", "lr")  -> 0.001
        """
        d = self._data
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k)
                if d is None:
                    return default
            else:
                return default
        return d

    def set(self, *keys_and_value) -> bool:
        """
        Đặt giá trị nested.
        Ví dụ: settings.set("dqn", "lr", 0.0005)
        Trả về True nếu thành công.
        """
        if len(keys_and_value) < 2:
            return False
        keys = keys_and_value[:-1]
        value = keys_and_value[-1]
        d = self._data
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value
        return True

    def get_section(self, section: str) -> dict:
        """Lấy toàn bộ một section."""
        return dict(self._data.get(section, {}))

    def all(self) -> dict:
        """Trả về toàn bộ settings."""
        return copy.deepcopy(self._data)

    # ─────────────────────────────────────────────────────────────────────────
    # SHORTCUTS
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def language(self) -> str:
        return self.get("language", default="vi")

    @property
    def algorithms(self) -> list:
        return self.get("agent", "algorithms", default=["q_learning", "dqn"])

    @property
    def agent_colors(self) -> dict:
        colors = self.get("agent_colors", default={})
        return {k: tuple(v) for k, v in colors.items()}

    def algo_color(self, algo: str) -> tuple:
        colors = self.agent_colors
        return colors.get(algo, (128, 128, 128))

    def print_summary(self):
        print("\n=== Settings Summary ===")
        print(f"  Language  : {self.language}")
        print(f"  Algorithms: {self.algorithms}")
        print(f"  World     : {self.get('world','width')}x{self.get('world','height')}")
        print(f"  Agents    : {self.get('agent','num_agents')}")
        print(f"  Episodes  : {self.get('training','num_episodes')}")
        print("========================\n")


# Singleton instance
settings = SettingsManager()
