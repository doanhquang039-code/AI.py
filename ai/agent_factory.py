"""
ai/agent_factory.py — Factory tạo AI agents từ config

Dùng pattern Factory để tạo bất kỳ loại agent nào
chỉ từ tên thuật toán trong settings.yaml.
"""
from typing import List, Tuple, Optional
from config.settings_manager import settings
from core.world import VirtualWorld
from core.agent import WorldAgent, AgentType


# Map tên thuật toán -> AgentType enum
_ALGO_TO_TYPE = {
    "q_learning": AgentType.Q_LEARNING,
    "sarsa":      AgentType.SARSA,
    "dqn":        AgentType.DQN,
    "ppo":        AgentType.PPO,
    "a2c":        AgentType.A2C,
}


def create_brain(algo: str):
    """
    Tạo brain (AI algorithm) từ tên thuật toán.
    Trả về instance tương ứng, hoặc None nếu không hỗ trợ.
    """
    state_dim = 27
    action_dim = 9

    if algo == "q_learning":
        from ai.q_learning import QLearningAgent
        return QLearningAgent(state_dim, action_dim)

    elif algo == "sarsa":
        from ai.sarsa import SARSAAgent
        return SARSAAgent(state_dim, action_dim)

    elif algo == "dqn":
        try:
            from ai.dqn import DQNAgent, TORCH_AVAILABLE
            if not TORCH_AVAILABLE:
                print("[Factory] PyTorch not available, skipping DQN")
                return None
            cfg = settings.get_section("dqn")
            return DQNAgent(
                state_dim=state_dim,
                action_dim=action_dim,
                use_dueling=cfg.get("use_dueling", True),
                use_per=cfg.get("use_per", True),
            )
        except Exception as e:
            print(f"[Factory] DQN error: {e}")
            return None

    elif algo == "ppo":
        try:
            from ai.ppo import PPOAgent, TORCH_AVAILABLE
            if not TORCH_AVAILABLE:
                print("[Factory] PyTorch not available, skipping PPO")
                return None
            return PPOAgent(state_dim, action_dim)
        except Exception as e:
            print(f"[Factory] PPO error: {e}")
            return None

    elif algo == "a2c":
        try:
            from ai.a2c import A2CAgent, TORCH_AVAILABLE
            if not TORCH_AVAILABLE:
                print("[Factory] PyTorch not available, skipping A2C")
                return None
            return A2CAgent(state_dim, action_dim)
        except Exception as e:
            print(f"[Factory] A2C error: {e}")
            return None

    else:
        print(f"[Factory] Unknown algorithm: '{algo}'")
        return None


def build_agents(world: VirtualWorld) -> List[WorldAgent]:
    """
    Tạo tất cả agents theo config settings.yaml.

    algorithms: [q_learning, dqn, sarsa, ppo, a2c]
    -> 1 agent mỗi thuật toán, màu từ agent_colors config.
    """
    algorithms = settings.algorithms
    colors = settings.agent_colors

    agents = []
    agent_id = 0

    for algo in algorithms:
        brain = create_brain(algo)
        if brain is None:
            continue   # Skip thuật toán không khả dụng

        agent_type = _ALGO_TO_TYPE.get(algo, AgentType.Q_LEARNING)
        color = colors.get(algo, (128, 128, 128))

        agent = WorldAgent(
            agent_id=agent_id,
            agent_type=agent_type,
            brain=brain,
            world=world,
            color=color,
        )
        agents.append(agent)
        agent_id += 1
        print(f"[Factory] Created Agent {agent_id - 1}: {algo} (color={color})")

    print(f"[Factory] Total agents: {len(agents)}")
    return agents


def build_single_agent(
    algo: str,
    world: VirtualWorld,
    agent_id: int = 0,
    color: Optional[Tuple] = None,
) -> Optional[WorldAgent]:
    """Tạo một agent đơn lẻ."""
    brain = create_brain(algo)
    if brain is None:
        return None

    if color is None:
        color = settings.agent_colors.get(algo, (128, 128, 128))

    agent_type = _ALGO_TO_TYPE.get(algo, AgentType.Q_LEARNING)
    return WorldAgent(agent_id, agent_type, brain, world, color)


def available_algorithms() -> List[str]:
    """Danh sách thuật toán có thể dùng."""
    all_algos = ["q_learning", "sarsa", "dqn", "ppo", "a2c"]
    try:
        from ai.dqn import TORCH_AVAILABLE
        if not TORCH_AVAILABLE:
            return ["q_learning", "sarsa"]
    except ImportError:
        return ["q_learning", "sarsa"]
    return all_algos
