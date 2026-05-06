"""
test_basic.py — Quick sanity test for all modules
"""
import torch
from core.world import VirtualWorld
from core.agent import WorldAgent, AgentType
from ai.q_learning import QLearningAgent
from ai.dqn import DQNAgent, TORCH_AVAILABLE
from main import run_episode

print("=== IMPORTS OK ===")
print("PyTorch:", torch.__version__)
print("TORCH_AVAILABLE:", TORCH_AVAILABLE)

# Test world
world = VirtualWorld()
print("World:", world.W, "x", world.H)
print("Food:", len(world.foods), "| Hazards:", len(world.hazards), "| Obstacles:", len(world.obstacles))

# Test Q-Learning agent
ql_brain = QLearningAgent()
ql_agent = WorldAgent(0, AgentType.Q_LEARNING, ql_brain, world, (99, 102, 241))
state = ql_agent.get_state()
print("State dim:", state.shape)
reward = ql_agent.step()
print("QL step reward:", round(reward, 2))

# Test DQN agent
dqn_brain = DQNAgent(use_dueling=True, use_per=True)
dqn_agent = WorldAgent(1, AgentType.DQN, dqn_brain, world, (251, 191, 36))
reward = dqn_agent.step()
print("DQN step reward:", round(reward, 2))
print("DQN device:", dqn_brain.device)

# Test 5 episodes quickly
for ep in range(5):
    stats = run_episode(world, [ql_agent, dqn_agent])
    print(f"  Episode {ep}: steps={stats['steps']} alive={stats['alive_count']}")

# Print stats
print("\nQ-Learning stats:", ql_brain.stats)
print("DQN stats:", dqn_brain.stats)

print("\n=== ALL TESTS PASSED! ===")
