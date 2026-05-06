"""
utils/stats.py — Theo dõi và vẽ biểu đồ thống kê training
"""
import os
import numpy as np
from collections import defaultdict
from typing import Dict, List, Any


class StatsTracker:
    """Thu thập metrics mỗi episode và vẽ biểu đồ cuối training."""

    def __init__(self):
        self.history: Dict[str, List] = defaultdict(list)

    def update(self, ep_stats: Dict[str, Any]):
        """Cập nhật với stats của một episode."""
        self.history["episode"].append(ep_stats.get("episode", len(self.history["episode"])))
        self.history["steps"].append(ep_stats.get("steps", 0))
        self.history["alive_count"].append(ep_stats.get("alive_count", 0))

        for agent_info in ep_stats.get("agents", []):
            prefix = f"agent_{agent_info['id']}_{agent_info['type'][:2]}"
            self.history[f"{prefix}_reward"].append(agent_info["total_reward"])
            self.history[f"{prefix}_food"].append(agent_info["food_eaten"])
            self.history[f"{prefix}_steps"].append(agent_info["steps_alive"])

    def plot_final(self, save_dir: str = "logs", show: bool = True):
        """Vẽ biểu đồ tổng hợp sau training."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.style as style
            style.use("dark_background")
        except ImportError:
            print("[Stats] matplotlib chưa được cài — bỏ qua vẽ chart")
            return

        episodes = self.history["episode"]
        if not episodes:
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 8))
        fig.suptitle("📊 Training Statistics — AI Virtual World",
                     fontsize=15, color="white", fontweight="bold")

        def smooth(arr, w=30):
            if len(arr) < w:
                return np.array(arr)
            return np.convolve(arr, np.ones(w)/w, mode="valid")

        colors = {
            "QL": "#6366f1",
            "DQ": "#f59e0b",
            "alive": "#10b981",
            "steps": "#38bdf8",
        }

        # Plot rewards
        ax = axes[0, 0]
        for key, vals in self.history.items():
            if "_reward" in key:
                atype = "QL" if "_QL" in key or "_Q-" in key else "DQ"
                color = colors.get(atype, "#888888")
                name = key.split("_reward")[0]
                ax.plot(smooth(vals), color=color, alpha=0.8, linewidth=1.5,
                        label=name)
        ax.set_title("Reward / Episode")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Total Reward")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.15)

        # Plot food
        ax = axes[0, 1]
        for key, vals in self.history.items():
            if "_food" in key:
                atype = "QL" if "_QL" in key or "_Q-" in key else "DQ"
                color = colors.get(atype, "#888888")
                name = key.split("_food")[0]
                ax.plot(smooth(vals), color=color, alpha=0.8, linewidth=1.5,
                        label=name)
        ax.set_title("Food Eaten / Episode")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Food")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.15)

        # Alive count
        ax = axes[1, 0]
        ax.plot(smooth(self.history["alive_count"]), color=colors["alive"],
                linewidth=2, label="Agents Alive at End")
        ax.set_title("Agents Alive at Episode End")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Count")
        ax.legend()
        ax.grid(alpha=0.15)

        # Steps per episode
        ax = axes[1, 1]
        ax.plot(smooth(self.history["steps"]), color=colors["steps"],
                linewidth=2, label="Steps / Episode")
        ax.set_title("Episode Length (Steps)")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Steps")
        ax.legend()
        ax.grid(alpha=0.15)

        plt.tight_layout()
        os.makedirs(save_dir, exist_ok=True)
        out = os.path.join(save_dir, "training_stats.png")
        plt.savefig(out, dpi=150, bbox_inches="tight")
        print(f"\n📊 Stats chart đã lưu: {out}")
        if show:
            plt.show()
