"""
main.py — Entry Point dự án AI Virtual World

Chế độ chạy:
    python main.py --mode visual        → Chạy với Pygame visualization
    python main.py --mode train         → Headless training (không cần màn hình)
    python main.py --mode dashboard     → Chỉ chạy web dashboard
    python main.py --mode compare       → So sánh Q-Learning vs DQN với charts

Options:
    --episodes N        Số episodes (default: 2000)
    --agents N          Số agents đồng thời (default: 4)
    --no-per            Tắt Prioritized Experience Replay
    --load-model PATH   Tải model đã train
"""
import argparse
import os
import sys
import time
import json
import threading
import numpy as np
from pathlib import Path
from typing import List

# ─── Import project modules ───────────────────────────────────────────────────
import config as cfg
from core.world import VirtualWorld
from core.agent import WorldAgent, AgentType
from ai.q_learning import QLearningAgent
from ai.dqn import DQNAgent, TORCH_AVAILABLE
from utils.logger import TrainingLogger
from utils.stats import StatsTracker


from i18n import t
from config.settings_manager import settings
from ai.agent_factory import build_agents


def run_episode(world: VirtualWorld, agents: List[WorldAgent]) -> dict:
    """
    Chạy một episode:
        - Reset world và agents
        - Chạy tối đa max_steps bước
        - Trả về thống kê episode
    """
    world.reset()
    for agent in agents:
        agent.reset()

    all_dead = False
    step = 0

    while step < cfg.WORLD.max_steps and not all_dead:
        world.step()

        for agent in agents:
            if agent.is_alive:
                agent.step()
            elif agent.energy <= 0 and step > 10:
                if not hasattr(agent, '_death_reported'):
                    _log_event(f"💀 Agent {agent.id} ({agent.agent_type.value}) đã chết tại step {step}!")
                    agent._death_reported = True

        all_dead = all(not a.is_alive for a in agents)
        step += 1

    # Bonus cho agents sống sót đến cuối
    for agent in agents:
        if agent.is_alive:
            agent.total_reward += cfg.AGENT.reward_survive_bonus

    # End episode cho brains
    for agent in agents:
        agent.brain.end_episode()

    return {
        "steps": step,
        "agents": [a.info for a in agents],
        "world": world.stats,
        "alive_count": sum(1 for a in agents if a.is_alive),
    }


# ─────────────────────────────────────────────────────────────────────────────
# MODE: VISUAL (Pygame)
# ─────────────────────────────────────────────────────────────────────────────

def run_visual(args):
    """Chạy simulation với Pygame visualization."""
    from visualization.renderer import Renderer

    world = VirtualWorld()
    agents = build_agents(world)
    renderer = Renderer(world)
    logger = TrainingLogger(args.log_dir)
    stats = StatsTracker()

    episode = 0
    paused = False

    world.update_curriculum(episode)
    world.reset()
    for agent in agents:
        agent.reset()

    step_in_ep = 0
    print(f"\n{'='*60}")
    print(f"  🤖 {t('sim_title')}")
    print(f"  {t('hud_agents')}: {len(agents)} | {t('metric_episode')}: {args.episodes}")
    print(f"  PyTorch: {'✓' if TORCH_AVAILABLE else '✗ (' + t('no_pytorch') + ')'}")
    print(f"{'='*60}\n")
    print(t('sim_start'))

    running = True
    while running and episode < args.episodes:
        events = renderer.handle_events()

        if events["quit"]:
            break
        if events["pause"]:
            paused = not paused
        if events["reset"]:
            world.reset()
            for a in agents:
                a.reset()
            step_in_ep = 0
        if events["toggle_sensors"]:
            cfg.VISUAL.show_sensors = not cfg.VISUAL.show_sensors
        if events["toggle_trails"]:
            cfg.VISUAL.show_trails = not cfg.VISUAL.show_trails
        if events["speed_up"]:
            cfg.VISUAL.fps = min(120, cfg.VISUAL.fps + 10)
        if events["speed_down"]:
            cfg.VISUAL.fps = max(5, cfg.VISUAL.fps - 10)
        
        if events["spawn_food"]:
            world.spawn_custom_food(*events["spawn_food"])
        if events["spawn_hazard"]:
            world.spawn_custom_hazard(*events["spawn_hazard"])

        if not paused:
            world.step()
            
            # Kiểm tra thời tiết thay đổi để log event
            current_weather = world.weather_manager.current.value
            if not hasattr(world, '_last_weather'):
                world._last_weather = current_weather
            elif world._last_weather != current_weather:
                _log_event(f"🌤 Thời tiết chuyển sang {current_weather}!")
                world._last_weather = current_weather

            for agent in agents:
                if agent.is_alive:
                    agent.step()

            step_in_ep += 1

            # Kết thúc episode
            all_dead = all(not a.is_alive for a in agents)
            if all_dead or step_in_ep >= cfg.WORLD.max_steps:
                for a in agents:
                    if a.is_alive:
                        a.total_reward += cfg.AGENT.reward_survive_bonus
                    a.brain.end_episode()

                ep_stats = {
                    "episode": episode,
                    "steps": step_in_ep,
                    "agents": [a.info for a in agents],
                    "alive_count": sum(1 for a in agents if a.is_alive),
                }
                stats.update(ep_stats)
                logger.log(ep_stats)

                if episode % cfg.TRAIN.log_every == 0:
                    _print_episode_summary(episode, ep_stats, agents)

                if episode % cfg.TRAIN.save_every == 0 and episode > 0:
                    _save_models(agents, args.model_dir, episode)

                episode += 1
                world.update_curriculum(episode)
                world.reset()
                for a in agents:
                    a.reset()
                step_in_ep = 0

        renderer.render(agents, episode, paused)

    renderer.quit()
    stats.plot_final(save_dir=args.log_dir)
    print(f"\n✅ {t('sim_done')}")


# ─────────────────────────────────────────────────────────────────────────────
# MODE: TRAIN (Headless)
# ─────────────────────────────────────────────────────────────────────────────

def run_train(args):
    """Headless training — không cần Pygame."""
    from tqdm import tqdm

    world = VirtualWorld()
    agents = build_agents(world)
    logger = TrainingLogger(args.log_dir)
    stats = StatsTracker()

    print(f"\n{'='*60}")
    print(f"  🧠 AI Virtual World — Headless Training")
    print(f"  {t('hud_agents')}: {len(agents)} | {t('metric_episode')}: {args.episodes}")
    print(f"  Device: {'CUDA' if TORCH_AVAILABLE else 'CPU'}")
    print(f"{'='*60}\n")
    print(t('train_start'))

    pbar = tqdm(range(args.episodes), desc="Training", unit="ep")

    for episode in pbar:
        world.update_curriculum(episode)
        ep_stats = run_episode(world, agents)
        ep_stats["episode"] = episode
        stats.update(ep_stats)
        logger.log(ep_stats)

        if episode % cfg.TRAIN.log_every == 0:
            avg_r = np.mean([a["total_reward"] for a in ep_stats["agents"]])
            pbar.set_postfix({
                "avg_reward": f"{avg_r:.1f}",
                "food": ep_stats["world"]["food_eaten"],
                "alive": ep_stats["alive_count"],
            })

        if episode % cfg.TRAIN.save_every == 0 and episode > 0:
            _save_models(agents, args.model_dir, episode)
            tqdm.write(f"💾 Saved models @ episode {episode}")

    stats.plot_final(save_dir=args.log_dir)
    _save_models(agents, args.model_dir, args.episodes)
    print(f"\n✅ {t('train_done')}")
    _print_final_summary(agents)


# ─────────────────────────────────────────────────────────────────────────────
# MODE: COMPARE
# ─────────────────────────────────────────────────────────────────────────────

def run_compare(args):
    """So sánh Q-Learning vs DQN qua nhiều episodes, vẽ biểu đồ."""
    import matplotlib.pyplot as plt
    import matplotlib.style as style

    style.use("dark_background")

    print("\n📊 So sánh Q-Learning vs DQN...")

    world = VirtualWorld()

    # Tạo riêng từng loại agent
    ql_brain = QLearningAgent()
    ql_agent = WorldAgent(0, AgentType.Q_LEARNING, ql_brain, world, (99, 102, 241))

    dqn_brain = DQNAgent() if TORCH_AVAILABLE else None
    dqn_agent = WorldAgent(1, AgentType.DQN, dqn_brain, world, (251, 191, 36)) \
        if dqn_brain else None

    agents = [ql_agent] + ([dqn_agent] if dqn_agent else [])

    ql_rewards, dqn_rewards = [], []
    ql_foods, dqn_foods = [], []

    episodes = min(args.episodes, 500)

    from tqdm import tqdm
    for ep in tqdm(range(episodes), desc="Comparing"):
        world.update_curriculum(ep)
        ep_stats = run_episode(world, agents)
        for a_info in ep_stats["agents"]:
            if a_info["type"] == AgentType.Q_LEARNING.value:
                ql_rewards.append(a_info["total_reward"])
                ql_foods.append(a_info["food_eaten"])
            elif a_info["type"] == AgentType.DQN.value:
                dqn_rewards.append(a_info["total_reward"])
                dqn_foods.append(a_info["food_eaten"])

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    fig.suptitle("🤖 Q-Learning vs DQN — Virtual World Research",
                 fontsize=16, color="white", fontweight="bold")

    def smooth(arr, window=20):
        if len(arr) < window:
            return arr
        return np.convolve(arr, np.ones(window)/window, mode="valid")

    # Reward per episode
    ax = axes[0, 0]
    ax.plot(smooth(ql_rewards), color="#6366f1", label="Q-Learning", linewidth=2)
    if dqn_rewards:
        ax.plot(smooth(dqn_rewards), color="#f59e0b", label="DQN", linewidth=2)
    ax.set_title("Total Reward / Episode")
    ax.set_xlabel("Episode")
    ax.set_ylabel("Reward")
    ax.legend()
    ax.grid(alpha=0.2)

    # Food per episode
    ax = axes[0, 1]
    ax.plot(smooth(ql_foods), color="#10b981", label="Q-Learning", linewidth=2)
    if dqn_foods:
        ax.plot(smooth(dqn_foods), color="#f43f5e", label="DQN", linewidth=2)
    ax.set_title("Food Eaten / Episode")
    ax.set_xlabel("Episode")
    ax.set_ylabel("Food")
    ax.legend()
    ax.grid(alpha=0.2)

    # Reward distribution
    ax = axes[1, 0]
    ax.hist(ql_rewards, bins=30, color="#6366f1", alpha=0.7, label="Q-Learning")
    if dqn_rewards:
        ax.hist(dqn_rewards, bins=30, color="#f59e0b", alpha=0.7, label="DQN")
    ax.set_title("Reward Distribution")
    ax.legend()
    ax.grid(alpha=0.2)

    # Cumulative food
    ax = axes[1, 1]
    ax.plot(np.cumsum(ql_foods), color="#6366f1", label="Q-Learning", linewidth=2)
    if dqn_foods:
        ax.plot(np.cumsum(dqn_foods), color="#f59e0b", label="DQN", linewidth=2)
    ax.set_title("Cumulative Food Eaten")
    ax.set_xlabel("Episode")
    ax.legend()
    ax.grid(alpha=0.2)

    plt.tight_layout()
    out_path = os.path.join(args.log_dir, "comparison.png")
    os.makedirs(args.log_dir, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"\n📊 Chart đã lưu tại: {out_path}")


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _print_episode_summary(episode: int, ep_stats: dict, agents: List[WorldAgent]):
    ql_agents = [a for a in agents if a.agent_type == AgentType.Q_LEARNING]
    dqn_agents = [a for a in agents if a.agent_type == AgentType.DQN]

    ql_r = np.mean([a.total_reward for a in ql_agents]) if ql_agents else 0
    dqn_r = np.mean([a.total_reward for a in dqn_agents]) if dqn_agents else 0

    print(
        f"  Ep {episode:>4d} | Steps: {ep_stats['steps']:>4d} | "
        f"Alive: {ep_stats['alive_count']}/{len(agents)} | "
        f"QL_R: {ql_r:>7.1f} | DQN_R: {dqn_r:>7.1f}"
    )


def _print_final_summary(agents: List[WorldAgent]):
    print("\n" + "="*60)
    print("  📊 Final Training Summary")
    print("="*60)
    for agent in agents:
        print(f"\n  Agent {agent.id} [{agent.agent_type.value}]")
        for k, v in agent.brain.stats.items():
            print(f"    {k}: {v}")


def _save_models(agents: List[WorldAgent], model_dir: str, episode: int):
    os.makedirs(model_dir, exist_ok=True)
    for agent in agents:
        if agent.agent_type == AgentType.DQN and hasattr(agent.brain, "save"):
            path = os.path.join(model_dir, f"dqn_agent{agent.id}_ep{episode}.pt")
            agent.brain.save(path)
        elif agent.agent_type == AgentType.Q_LEARNING:
            path = os.path.join(model_dir, f"ql_agent{agent.id}_ep{episode}.npy")
            agent.brain.save(path)

def _log_event(msg: str):
    import json
    import os
    from datetime import datetime
    os.makedirs("logs", exist_ok=True)
    event_file = "logs/events.jsonl"
    event = {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg}
    with open(event_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

# ─────────────────────────────────────────────────────────────────────────────
# ARGPARSE
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="🤖 AI Virtual World — Q-Learning & DQN Research"
    )
    parser.add_argument(
        "--mode", choices=["visual", "train", "dashboard", "compare"],
        default="visual", help="Chế độ chạy"
    )
    parser.add_argument("--episodes", type=int, default=cfg.TRAIN.num_episodes)
    parser.add_argument("--agents", type=int, default=cfg.AGENT.num_agents)
    parser.add_argument("--no-per", action="store_true",
                        help="Tắt Prioritized Experience Replay")
    parser.add_argument("--load-model", type=str, default=None)
    parser.add_argument("--model-dir", type=str, default=cfg.TRAIN.model_dir)
    parser.add_argument("--log-dir", type=str, default=cfg.TRAIN.log_dir)
    return parser.parse_args()


def main():
    args = parse_args()

    os.makedirs(args.model_dir, exist_ok=True)
    os.makedirs(args.log_dir, exist_ok=True)

    if args.mode == "visual":
        run_visual(args)
    elif args.mode == "train":
        run_train(args)
    elif args.mode == "compare":
        run_compare(args)
    elif args.mode == "dashboard":
        from dashboard.app import run_dashboard
        run_dashboard()


if __name__ == "__main__":
    main()
