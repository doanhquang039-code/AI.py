from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
import numpy as np
import asyncio

app = FastAPI(
    title="AI Dashboard API",
    description="API for AI Training Dashboard - Enhanced Version",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TrainingConfig(BaseModel):
    algorithm: str
    episodes: int
    learning_rate: float
    gamma: float
    epsilon: Optional[float] = 0.1

class TrainingStatus(BaseModel):
    status: str
    current_episode: int
    total_episodes: int
    progress: float
    metrics: Dict[str, Any]

class ModelInfo(BaseModel):
    name: str
    algorithm: str
    episodes: int
    created_at: str
    size: int
    performance: Dict[str, float]

# In-memory storage (replace with database in production)
training_sessions = {}
models_cache = []
active_websockets: List[WebSocket] = []

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/")
async def root():
    return {
        "message": "AI Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/training/status")
async def get_training_status():
    """Get current training status"""
    return {
        "status": "idle",
        "current_episode": 0,
        "total_episodes": 0,
        "progress": 0.0,
        "metrics": {
            "reward": 0.0,
            "loss": 0.0,
            "epsilon": 0.1
        }
    }

@app.post("/api/training/start")
async def start_training(config: TrainingConfig):
    """Start a new training session"""
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    training_sessions[session_id] = {
        "id": session_id,
        "config": config.dict(),
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "current_episode": 0,
        "total_episodes": config.episodes
    }
    
    return {
        "session_id": session_id,
        "message": "Training started successfully",
        "config": config.dict()
    }

@app.post("/api/training/stop/{session_id}")
async def stop_training(session_id: str):
    """Stop a training session"""
    if session_id not in training_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    training_sessions[session_id]["status"] = "stopped"
    training_sessions[session_id]["stopped_at"] = datetime.now().isoformat()
    
    return {
        "message": "Training stopped successfully",
        "session_id": session_id
    }

@app.get("/api/training/history")
async def get_training_history():
    """Get training history"""
    logs_dir = "logs"
    history = []
    
    if os.path.exists(logs_dir):
        for filename in os.listdir(logs_dir):
            if filename.endswith('.jsonl'):
                filepath = os.path.join(logs_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            last_line = json.loads(lines[-1])
                            history.append({
                                "filename": filename,
                                "episodes": len(lines),
                                "last_episode": last_line,
                                "created_at": filename.split('_')[1] + '_' + filename.split('_')[2].replace('.jsonl', '')
                            })
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
    
    return {"history": history}

@app.get("/api/models")
async def get_models():
    """Get list of trained models"""
    models_dir = "models"
    models = []
    
    if os.path.exists(models_dir):
        for filename in os.listdir(models_dir):
            filepath = os.path.join(models_dir, filename)
            file_size = os.path.getsize(filepath)
            
            # Parse filename: algorithm_agentX_epY.ext
            parts = filename.replace('.pt', '').replace('.npy', '').split('_')
            
            models.append({
                "name": filename,
                "algorithm": parts[0].upper() if len(parts) > 0 else "Unknown",
                "agent_id": parts[1] if len(parts) > 1 else "0",
                "episodes": parts[2] if len(parts) > 2 else "0",
                "size": file_size,
                "created_at": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                "performance": {
                    "accuracy": np.random.uniform(0.7, 0.95),
                    "reward": np.random.uniform(50, 100)
                }
            })
    
    return {"models": models}

@app.delete("/api/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a trained model"""
    filepath = os.path.join("models", model_name)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        os.remove(filepath)
        return {"message": f"Model {model_name} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/summary")
async def get_stats_summary():
    """Get summary statistics"""
    models_dir = "models"
    logs_dir = "logs"
    
    total_models = len(os.listdir(models_dir)) if os.path.exists(models_dir) else 0
    total_sessions = len(os.listdir(logs_dir)) if os.path.exists(logs_dir) else 0
    
    return {
        "total_models": total_models,
        "total_training_sessions": total_sessions,
        "active_sessions": len([s for s in training_sessions.values() if s["status"] == "running"]),
        "algorithms": ["DQN", "Q-Learning", "SARSA", "PPO", "A2C"],
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/stats/performance")
async def get_performance_stats():
    """Get performance statistics"""
    # Mock data - replace with actual stats from training logs
    episodes = list(range(1, 11))
    rewards = [np.random.uniform(10, 100) for _ in episodes]
    losses = [np.random.uniform(0.1, 2.0) for _ in episodes]
    
    return {
        "episodes": episodes,
        "rewards": rewards,
        "losses": losses,
        "avg_reward": np.mean(rewards),
        "max_reward": np.max(rewards),
        "min_reward": np.min(rewards)
    }

@app.get("/api/algorithms")
async def get_algorithms():
    """Get available AI algorithms"""
    return {
        "algorithms": [
            {
                "id": "dqn",
                "name": "Deep Q-Network (DQN)",
                "description": "Deep reinforcement learning algorithm using neural networks",
                "type": "value-based",
                "complexity": "high"
            },
            {
                "id": "q_learning",
                "name": "Q-Learning",
                "description": "Classic tabular reinforcement learning algorithm",
                "type": "value-based",
                "complexity": "low"
            },
            {
                "id": "sarsa",
                "name": "SARSA",
                "description": "On-policy temporal difference learning",
                "type": "value-based",
                "complexity": "low"
            },
            {
                "id": "ppo",
                "name": "Proximal Policy Optimization (PPO)",
                "description": "Advanced policy gradient method",
                "type": "policy-based",
                "complexity": "high"
            },
            {
                "id": "a2c",
                "name": "Advantage Actor-Critic (A2C)",
                "description": "Actor-critic method with advantage function",
                "type": "actor-critic",
                "complexity": "medium"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
