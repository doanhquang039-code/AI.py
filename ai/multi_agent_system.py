"""
Multi-Agent Collaboration System
Hệ thống cộng tác đa agent với communication và coordination
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from dataclasses import dataclass, asdict
from enum import Enum


class MessageType(Enum):
    """Loại message giữa các agents"""
    REQUEST_HELP = "request_help"
    OFFER_HELP = "offer_help"
    SHARE_INFO = "share_info"
    COORDINATE = "coordinate"
    ALERT = "alert"


@dataclass
class Message:
    """Message giữa các agents"""
    sender_id: int
    receiver_id: int  # -1 for broadcast
    message_type: MessageType
    content: Dict
    timestamp: float
    priority: int = 1  # 1-5, 5 is highest


@dataclass
class AgentState:
    """Trạng thái của agent"""
    agent_id: int
    position: Tuple[int, int]
    energy: float
    task_queue: List[Dict]
    current_task: Optional[Dict]
    capabilities: List[str]
    status: str  # "idle", "busy", "helping", "emergency"


class MultiAgentSystem:
    """Hệ thống quản lý đa agent"""
    
    def __init__(self, num_agents: int, world_size: Tuple[int, int]):
        self.num_agents = num_agents
        self.world_size = world_size
        self.agents: Dict[int, AgentState] = {}
        self.message_queue: List[Message] = []
        self.shared_knowledge: Dict = {}
        self.collaboration_history: List[Dict] = []
        
        # Initialize agents
        for i in range(num_agents):
            self.agents[i] = AgentState(
                agent_id=i,
                position=(np.random.randint(0, world_size[0]), 
                         np.random.randint(0, world_size[1])),
                energy=100.0,
                task_queue=[],
                current_task=None,
                capabilities=self._assign_capabilities(i),
                status="idle"
            )
    
    def _assign_capabilities(self, agent_id: int) -> List[str]:
        """Gán khả năng cho agent"""
        all_capabilities = [
            "exploration", "resource_collection", "combat",
            "repair", "communication", "navigation"
        ]
        # Mỗi agent có 3-4 capabilities ngẫu nhiên
        num_caps = np.random.randint(3, 5)
        return list(np.random.choice(all_capabilities, num_caps, replace=False))
    
    def send_message(self, message: Message):
        """Gửi message"""
        self.message_queue.append(message)
        self.message_queue.sort(key=lambda m: (-m.priority, m.timestamp))
    
    def broadcast_message(self, sender_id: int, message_type: MessageType, 
                         content: Dict, priority: int = 1):
        """Broadcast message đến tất cả agents"""
        import time
        message = Message(
            sender_id=sender_id,
            receiver_id=-1,
            message_type=message_type,
            content=content,
            timestamp=time.time(),
            priority=priority
        )
        self.send_message(message)
    
    def process_messages(self):
        """Xử lý messages trong queue"""
        processed = []
        
        for message in self.message_queue:
            if message.receiver_id == -1:
                # Broadcast to all
                for agent_id in self.agents.keys():
                    if agent_id != message.sender_id:
                        self._handle_message(agent_id, message)
            else:
                # Direct message
                self._handle_message(message.receiver_id, message)
            
            processed.append(message)
        
        # Clear processed messages
        self.message_queue = []
        return processed
    
    def _handle_message(self, receiver_id: int, message: Message):
        """Xử lý message cho một agent"""
        agent = self.agents[receiver_id]
        
        if message.message_type == MessageType.REQUEST_HELP:
            self._handle_help_request(agent, message)
        elif message.message_type == MessageType.SHARE_INFO:
            self._handle_info_sharing(agent, message)
        elif message.message_type == MessageType.COORDINATE:
            self._handle_coordination(agent, message)
        elif message.message_type == MessageType.ALERT:
            self._handle_alert(agent, message)
    
    def _handle_help_request(self, agent: AgentState, message: Message):
        """Xử lý yêu cầu giúp đỡ"""
        required_capability = message.content.get("required_capability")
        
        if (agent.status == "idle" and 
            required_capability in agent.capabilities and
            agent.energy > 30):
            # Agent có thể giúp
            agent.status = "helping"
            
            # Send offer help message
            import time
            response = Message(
                sender_id=agent.agent_id,
                receiver_id=message.sender_id,
                message_type=MessageType.OFFER_HELP,
                content={"available": True, "eta": self._calculate_eta(agent, message)},
                timestamp=time.time(),
                priority=message.priority
            )
            self.send_message(response)
    
    def _handle_info_sharing(self, agent: AgentState, message: Message):
        """Xử lý chia sẻ thông tin"""
        info_type = message.content.get("type")
        info_data = message.content.get("data")
        
        # Update shared knowledge
        if info_type not in self.shared_knowledge:
            self.shared_knowledge[info_type] = []
        
        self.shared_knowledge[info_type].append({
            "source": message.sender_id,
            "data": info_data,
            "timestamp": message.timestamp
        })
    
    def _handle_coordination(self, agent: AgentState, message: Message):
        """Xử lý coordination"""
        action = message.content.get("action")
        
        if action == "form_team":
            team_members = message.content.get("members", [])
            if agent.agent_id in team_members:
                agent.status = "busy"
                # Add team task to queue
                agent.task_queue.append({
                    "type": "team_task",
                    "team": team_members,
                    "objective": message.content.get("objective")
                })
    
    def _handle_alert(self, agent: AgentState, message: Message):
        """Xử lý cảnh báo"""
        alert_type = message.content.get("alert_type")
        
        if alert_type == "danger":
            # Move away from danger zone
            danger_pos = message.content.get("position")
            if self._distance(agent.position, danger_pos) < 5:
                agent.status = "emergency"
    
    def _calculate_eta(self, agent: AgentState, message: Message) -> float:
        """Tính thời gian đến"""
        target_pos = message.content.get("position", (0, 0))
        distance = self._distance(agent.position, target_pos)
        return distance / 2.0  # Assume speed of 2 units per step
    
    def _distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Tính khoảng cách Manhattan"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def form_coalition(self, task: Dict) -> List[int]:
        """Tạo coalition để thực hiện task"""
        required_capabilities = task.get("required_capabilities", [])
        required_agents = task.get("min_agents", 1)
        
        # Find suitable agents
        suitable_agents = []
        for agent_id, agent in self.agents.items():
            if agent.status == "idle" and agent.energy > 50:
                # Check if agent has any required capability
                if any(cap in agent.capabilities for cap in required_capabilities):
                    suitable_agents.append(agent_id)
        
        # Select best coalition
        if len(suitable_agents) >= required_agents:
            coalition = suitable_agents[:required_agents]
            
            # Notify coalition members
            import time
            self.broadcast_message(
                sender_id=-1,
                message_type=MessageType.COORDINATE,
                content={
                    "action": "form_team",
                    "members": coalition,
                    "objective": task.get("objective", "unknown")
                },
                priority=3
            )
            
            # Record collaboration
            self.collaboration_history.append({
                "timestamp": time.time(),
                "coalition": coalition,
                "task": task,
                "status": "formed"
            })
            
            return coalition
        
        return []
    
    def update_agent_position(self, agent_id: int, new_position: Tuple[int, int]):
        """Cập nhật vị trí agent"""
        if agent_id in self.agents:
            self.agents[agent_id].position = new_position
    
    def update_agent_energy(self, agent_id: int, energy_change: float):
        """Cập nhật năng lượng agent"""
        if agent_id in self.agents:
            self.agents[agent_id].energy = max(0, min(100, 
                self.agents[agent_id].energy + energy_change))
            
            # Alert if low energy
            if self.agents[agent_id].energy < 20:
                import time
                self.broadcast_message(
                    sender_id=agent_id,
                    message_type=MessageType.ALERT,
                    content={
                        "alert_type": "low_energy",
                        "agent_id": agent_id,
                        "energy": self.agents[agent_id].energy
                    },
                    priority=4
                )
    
    def get_system_state(self) -> Dict:
        """Lấy trạng thái hệ thống"""
        return {
            "agents": {aid: asdict(agent) for aid, agent in self.agents.items()},
            "message_queue_size": len(self.message_queue),
            "shared_knowledge_keys": list(self.shared_knowledge.keys()),
            "active_collaborations": len([c for c in self.collaboration_history 
                                         if c["status"] == "formed"])
        }
    
    def get_collaboration_metrics(self) -> Dict:
        """Lấy metrics về collaboration"""
        total_collaborations = len(self.collaboration_history)
        
        if total_collaborations == 0:
            return {
                "total_collaborations": 0,
                "average_team_size": 0,
                "success_rate": 0
            }
        
        team_sizes = [len(c["coalition"]) for c in self.collaboration_history]
        successful = len([c for c in self.collaboration_history 
                         if c.get("status") == "completed"])
        
        return {
            "total_collaborations": total_collaborations,
            "average_team_size": np.mean(team_sizes),
            "success_rate": successful / total_collaborations if total_collaborations > 0 else 0,
            "active_teams": len([c for c in self.collaboration_history 
                                if c["status"] == "formed"])
        }
    
    def save_state(self, filepath: str):
        """Lưu trạng thái hệ thống"""
        state = {
            "agents": {aid: asdict(agent) for aid, agent in self.agents.items()},
            "shared_knowledge": self.shared_knowledge,
            "collaboration_history": self.collaboration_history
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def load_state(self, filepath: str):
        """Load trạng thái hệ thống"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Restore agents
        for aid_str, agent_data in state["agents"].items():
            aid = int(aid_str)
            self.agents[aid] = AgentState(**agent_data)
        
        self.shared_knowledge = state["shared_knowledge"]
        self.collaboration_history = state["collaboration_history"]


class TaskAllocator:
    """Phân bổ tasks cho agents"""
    
    def __init__(self, multi_agent_system: MultiAgentSystem):
        self.mas = multi_agent_system
    
    def allocate_task(self, task: Dict) -> Optional[int]:
        """Phân bổ task cho agent phù hợp nhất"""
        required_capability = task.get("required_capability")
        task_position = task.get("position", (0, 0))
        
        best_agent = None
        best_score = -float('inf')
        
        for agent_id, agent in self.mas.agents.items():
            if agent.status != "idle":
                continue
            
            # Calculate score
            score = 0
            
            # Capability match
            if required_capability in agent.capabilities:
                score += 10
            
            # Energy level
            score += agent.energy / 10
            
            # Distance (closer is better)
            distance = self.mas._distance(agent.position, task_position)
            score -= distance / 5
            
            # Task queue size (less is better)
            score -= len(agent.task_queue) * 2
            
            if score > best_score:
                best_score = score
                best_agent = agent_id
        
        if best_agent is not None:
            # Assign task
            self.mas.agents[best_agent].task_queue.append(task)
            self.mas.agents[best_agent].status = "busy"
            return best_agent
        
        return None
    
    def balance_load(self):
        """Cân bằng load giữa các agents"""
        # Calculate average load
        loads = [len(agent.task_queue) for agent in self.mas.agents.values()]
        avg_load = np.mean(loads)
        
        # Redistribute tasks from overloaded agents
        for agent_id, agent in self.mas.agents.items():
            if len(agent.task_queue) > avg_load + 2:
                # Find underloaded agent
                for other_id, other_agent in self.mas.agents.items():
                    if (other_id != agent_id and 
                        len(other_agent.task_queue) < avg_load - 1 and
                        other_agent.status == "idle"):
                        # Transfer task
                        task = agent.task_queue.pop()
                        other_agent.task_queue.append(task)
                        break


if __name__ == "__main__":
    # Test multi-agent system
    print("🤖 Testing Multi-Agent Collaboration System")
    
    mas = MultiAgentSystem(num_agents=5, world_size=(20, 20))
    allocator = TaskAllocator(mas)
    
    print(f"\n✅ Created system with {mas.num_agents} agents")
    
    # Create some tasks
    tasks = [
        {"required_capability": "exploration", "position": (10, 10), "objective": "explore area"},
        {"required_capability": "combat", "position": (5, 5), "objective": "defend base"},
        {"required_capabilities": ["repair", "navigation"], "min_agents": 2, "objective": "repair station"}
    ]
    
    # Allocate tasks
    for i, task in enumerate(tasks[:2]):
        agent_id = allocator.allocate_task(task)
        print(f"Task {i+1} allocated to Agent {agent_id}")
    
    # Form coalition for complex task
    coalition = mas.form_coalition(tasks[2])
    print(f"\nCoalition formed: {coalition}")
    
    # Process messages
    processed = mas.process_messages()
    print(f"Processed {len(processed)} messages")
    
    # Get metrics
    metrics = mas.get_collaboration_metrics()
    print(f"\n📊 Collaboration Metrics:")
    print(f"  Total collaborations: {metrics['total_collaborations']}")
    print(f"  Average team size: {metrics['average_team_size']:.1f}")
    
    print("\n✅ Multi-Agent System test complete!")
