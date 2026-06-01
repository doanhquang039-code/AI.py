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
import random
import shutil

app = FastAPI(
    title="AI Dashboard API",
    description="API for AI Training Dashboard - Enhanced Version",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:4200").split(","),
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

class ModelComparison(BaseModel):
    model1: str
    model2: str

class ExperimentConfig(BaseModel):
    name: str
    description: str = ""
    algorithms: List[str]
    episodes: int
    runs: int = 1

# In-memory storage (replace with database in production)
training_sessions = {}
models_cache = []
active_websockets: List[WebSocket] = []
experiments = {}

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
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
        "version": "2.1.0",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "active_websockets": len(manager.active_connections),
        "active_training_sessions": len([s for s in training_sessions.values() if s["status"] == "running"])
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
            if not filename.endswith('.jsonl'):
                continue

            filepath = os.path.join(logs_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    entries = [json.loads(line) for line in f if line.strip()]

                if not entries:
                    continue

                stat = os.stat(filepath)
                history.append({
                    "filename": filename,
                    "episodes": len(entries),
                    "last_episode": entries[-1],
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                history.append({
                    "filename": filename,
                    "episodes": 0,
                    "last_episode": None,
                    "created_at": None,
                    "error": str(e)
                })
    
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

@app.get("/api/models/export/{model_name}")
async def export_model(model_name: str):
    """Export a model file."""
    filepath = os.path.join("models", model_name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Model not found")

    return FileResponse(filepath, media_type="application/octet-stream", filename=model_name)

@app.post("/api/models/import")
async def import_model(file: UploadFile = File(...)):
    """Import a model file into the models directory."""
    os.makedirs("models", exist_ok=True)
    safe_filename = os.path.basename(file.filename or "")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    filepath = os.path.join("models", safe_filename)
    with open(filepath, "wb") as output:
        shutil.copyfileobj(file.file, output)

    return {
        "message": f"Model {safe_filename} imported successfully",
        "filename": safe_filename,
        "size": os.path.getsize(filepath)
    }

@app.post("/api/models/compare")
async def compare_models(comparison: ModelComparison):
    """Compare two saved model files using lightweight metadata and demo metrics."""
    models_dir = "models"
    model1_path = os.path.join(models_dir, comparison.model1)
    model2_path = os.path.join(models_dir, comparison.model2)

    if not os.path.exists(model1_path) or not os.path.exists(model2_path):
        raise HTTPException(status_code=404, detail="One or both models not found")

    model1_score = float(np.random.uniform(0.70, 0.96))
    model2_score = float(np.random.uniform(0.70, 0.96))

    return {
        "model1": {
            "name": comparison.model1,
            "size": os.path.getsize(model1_path),
            "score": round(model1_score, 3),
            "avg_reward": round(float(np.random.uniform(45, 100)), 2)
        },
        "model2": {
            "name": comparison.model2,
            "size": os.path.getsize(model2_path),
            "score": round(model2_score, 3),
            "avg_reward": round(float(np.random.uniform(45, 100)), 2)
        },
        "winner": comparison.model1 if model1_score >= model2_score else comparison.model2,
        "comparison_date": datetime.now().isoformat()
    }

@app.post("/api/models/evaluate/{model_name}")
async def evaluate_model(model_name: str, test_episodes: int = 10):
    """Evaluate a saved model with demo metrics."""
    filepath = os.path.join("models", model_name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Model not found")

    rewards = [float(np.random.uniform(30, 100)) for _ in range(max(1, test_episodes))]
    return {
        "model_name": model_name,
        "test_episodes": len(rewards),
        "avg_reward": round(float(np.mean(rewards)), 2),
        "min_reward": round(float(np.min(rewards)), 2),
        "max_reward": round(float(np.max(rewards)), 2),
        "success_rate": round(float(np.random.uniform(0.70, 0.96)), 3),
        "evaluation_date": datetime.now().isoformat()
    }

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

@app.get("/api/stats/detailed")
async def get_detailed_stats():
    """Get detailed statistics for analytics dashboards"""
    summary = await get_stats_summary()
    performance = await get_performance_stats()
    algorithm_stats = {}

    for algorithm in summary["algorithms"]:
        base_reward = float(performance["avg_reward"])
        algorithm_stats[algorithm] = {
            "avg_reward": round(base_reward * random.uniform(0.85, 1.15), 2),
            "success_rate": round(random.uniform(0.62, 0.94), 3),
            "sessions": random.randint(1, max(1, summary["total_training_sessions"] + 1)),
            "best_reward": round(float(performance["max_reward"]) * random.uniform(0.9, 1.2), 2)
        }

    return {
        "total_models": summary["total_models"],
        "total_sessions": summary["total_training_sessions"],
        "active_sessions": summary["active_sessions"],
        "total_experiments": len(summary["algorithms"]) * max(1, summary["total_training_sessions"]),
        "algorithm_stats": algorithm_stats,
        "system_info": {
            "cpu_usage": round(random.uniform(12, 48), 1),
            "memory_usage": round(random.uniform(35, 72), 1),
            "gpu_available": False
        },
        "last_updated": datetime.now().isoformat()
    }

@app.post("/api/experiments/create")
async def create_experiment(config: ExperimentConfig):
    """Create an experiment definition."""
    experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    experiments[experiment_id] = {
        "id": experiment_id,
        "config": config.dict(),
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "results": []
    }

    return {
        "experiment_id": experiment_id,
        "message": "Experiment created successfully",
        "config": config.dict()
    }

@app.get("/api/experiments")
async def get_experiments():
    return {"experiments": list(experiments.values())}

@app.get("/api/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    if experiment_id not in experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiments[experiment_id]

@app.post("/api/tuning/start")
async def start_hyperparameter_tuning(payload: Dict[str, Any]):
    """Start a lightweight hyperparameter tuning job placeholder."""
    tuning_id = f"tuning_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return {
        "tuning_id": tuning_id,
        "message": "Hyperparameter tuning started",
        "algorithm": payload.get("algorithm", "dqn"),
        "param_ranges": payload.get("param_ranges", {}),
        "estimated_time": "30 minutes"
    }

@app.get("/api/system/health")
async def system_health():
    """Get system health details for dashboard diagnostics."""
    return {
        "status": "healthy",
        "cpu_usage": round(random.uniform(12, 68), 1),
        "memory_usage": round(random.uniform(30, 74), 1),
        "disk_usage": round(random.uniform(35, 70), 1),
        "active_connections": len(manager.active_connections),
        "active_trainings": len([s for s in training_sessions.values() if s["status"] == "running"]),
        "timestamp": datetime.now().isoformat()
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

def generate_world_state(episode: int, step: int) -> Dict[str, Any]:
    """Generate a lightweight demo world state for realtime visualization."""
    colors = ["#4CAF50", "#2196F3", "#FFC107", "#E91E63"]
    agents = []

    for agent_id in range(4):
        agents.append({
            "id": agent_id,
            "x": (step + agent_id * 7) % 30,
            "y": (step * 2 + agent_id * 5) % 30,
            "energy": max(10, 100 - ((step + agent_id * 8) % 90)),
            "reward": round(random.uniform(-1, 10), 2),
            "alive": True,
            "color": colors[agent_id % len(colors)]
        })

    return {
        "agents": agents,
        "foods": [{"x": (i * 3 + step) % 30, "y": (i * 5) % 30} for i in range(12)],
        "hazards": [{"x": (i * 7) % 30, "y": (i * 4 + step) % 30} for i in range(6)],
        "obstacles": [{"x": i, "y": 15} for i in range(5, 25, 3)],
        "episode": episode,
        "step": step
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Realtime updates for Angular visualization and statistics components."""
    await manager.connect(websocket)
    episode = 1
    step = 0

    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=0.2)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                elif message.get("type") == "subscribe":
                    await websocket.send_json({"type": "subscribed", "timestamp": datetime.now().isoformat()})
            except asyncio.TimeoutError:
                pass

            await websocket.send_json({
                "type": "world_state",
                "state": generate_world_state(episode, step),
                "timestamp": datetime.now().isoformat()
            })

            if step % 10 == 0:
                await websocket.send_json({
                    "type": "training_update",
                    "episode": episode,
                    "total_episodes": 100,
                    "progress": min(100, episode),
                    "metrics": {
                        "reward": round(random.uniform(20, 95), 2),
                        "loss": round(random.uniform(0.01, 1.5), 4),
                        "epsilon": round(max(0.05, 1 - episode / 100), 3)
                    },
                    "timestamp": datetime.now().isoformat()
                })

            step += 1
            if step >= 100:
                step = 0
                episode += 1

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
