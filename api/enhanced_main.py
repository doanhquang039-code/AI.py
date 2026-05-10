from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
import numpy as np
import asyncio
import io
from websocket_handler import manager

app = FastAPI(
    title="AI Dashboard API - Enhanced",
    description="Enhanced API for AI Training Dashboard with WebSocket support",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
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
    batch_size: Optional[int] = 32
    memory_size: Optional[int] = 10000

class ModelComparison(BaseModel):
    model1: str
    model2: str

class ExperimentConfig(BaseModel):
    name: str
    description: str
    algorithms: List[str]
    episodes: int
    runs: int

# Storage
training_sessions = {}
experiments = {}

@app.get("/")
async def root():
    return {
        "message": "AI Dashboard API - Enhanced Version",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "WebSocket support",
            "Model comparison",
            "Experiment tracking",
            "Real-time updates",
            "Model export/import"
        ]
    }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            elif message.get("type") == "subscribe":
                await manager.send_personal_message({
                    "type": "subscribed",
                    "message": "Successfully subscribed to updates"
                }, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Enhanced training endpoints
@app.post("/api/training/start-advanced")
async def start_advanced_training(config: TrainingConfig, background_tasks: BackgroundTasks):
    """Start advanced training with more parameters"""
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    training_sessions[session_id] = {
        "id": session_id,
        "config": config.dict(),
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "current_episode": 0,
        "total_episodes": config.episodes,
        "metrics_history": []
    }
    
    # Simulate training in background
    background_tasks.add_task(simulate_training, session_id, config.episodes)
    
    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "training_started",
        "session_id": session_id,
        "config": config.dict()
    })
    
    return {
        "session_id": session_id,
        "message": "Advanced training started successfully",
        "config": config.dict()
    }

async def simulate_training(session_id: str, total_episodes: int):
    """Simulate training progress"""
    for episode in range(1, total_episodes + 1):
        await asyncio.sleep(1)  # Simulate training time
        
        # Generate mock metrics
        metrics = {
            "reward": np.random.uniform(10, 100),
            "loss": np.random.uniform(0.1, 2.0),
            "epsilon": max(0.01, 0.1 - (episode / total_episodes) * 0.09)
        }
        
        # Update session
        if session_id in training_sessions:
            training_sessions[session_id]["current_episode"] = episode
            training_sessions[session_id]["metrics_history"].append(metrics)
            
            # Broadcast update
            await manager.broadcast_training_update(
                session_id, episode, total_episodes, metrics
            )

# Model comparison
@app.post("/api/models/compare")
async def compare_models(comparison: ModelComparison):
    """Compare two models"""
    models_dir = "models"
    
    model1_path = os.path.join(models_dir, comparison.model1)
    model2_path = os.path.join(models_dir, comparison.model2)
    
    if not os.path.exists(model1_path) or not os.path.exists(model2_path):
        raise HTTPException(status_code=404, detail="One or both models not found")
    
    # Mock comparison data
    comparison_result = {
        "model1": {
            "name": comparison.model1,
            "accuracy": np.random.uniform(0.7, 0.95),
            "reward": np.random.uniform(50, 100),
            "training_time": np.random.uniform(100, 500),
            "size": os.path.getsize(model1_path)
        },
        "model2": {
            "name": comparison.model2,
            "accuracy": np.random.uniform(0.7, 0.95),
            "reward": np.random.uniform(50, 100),
            "training_time": np.random.uniform(100, 500),
            "size": os.path.getsize(model2_path)
        },
        "winner": comparison.model1 if np.random.random() > 0.5 else comparison.model2,
        "comparison_date": datetime.now().isoformat()
    }
    
    return comparison_result

# Model export
@app.get("/api/models/export/{model_name}")
async def export_model(model_name: str):
    """Export a model file"""
    filepath = os.path.join("models", model_name)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Model not found")
    
    return FileResponse(
        filepath,
        media_type="application/octet-stream",
        filename=model_name
    )

# Model import
@app.post("/api/models/import")
async def import_model(file: UploadFile = File(...)):
    """Import a model file"""
    models_dir = "models"
    
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
    
    filepath = os.path.join(models_dir, file.filename)
    
    # Save uploaded file
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Broadcast model update
    await manager.broadcast_model_update("created", file.filename)
    
    return {
        "message": f"Model {file.filename} imported successfully",
        "filename": file.filename,
        "size": len(content)
    }

# Experiments
@app.post("/api/experiments/create")
async def create_experiment(config: ExperimentConfig):
    """Create a new experiment"""
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
    """Get all experiments"""
    return {"experiments": list(experiments.values())}

@app.get("/api/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Get experiment details"""
    if experiment_id not in experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return experiments[experiment_id]

# Advanced statistics
@app.get("/api/stats/detailed")
async def get_detailed_stats():
    """Get detailed statistics"""
    models_dir = "models"
    logs_dir = "logs"
    
    # Calculate detailed stats
    total_models = len(os.listdir(models_dir)) if os.path.exists(models_dir) else 0
    total_sessions = len(os.listdir(logs_dir)) if os.path.exists(logs_dir) else 0
    
    # Algorithm performance
    algorithm_stats = {
        "DQN": {"avg_reward": np.random.uniform(70, 90), "success_rate": 0.85},
        "Q-Learning": {"avg_reward": np.random.uniform(60, 80), "success_rate": 0.75},
        "SARSA": {"avg_reward": np.random.uniform(55, 75), "success_rate": 0.70},
        "PPO": {"avg_reward": np.random.uniform(75, 95), "success_rate": 0.90},
        "A2C": {"avg_reward": np.random.uniform(65, 85), "success_rate": 0.80}
    }
    
    return {
        "total_models": total_models,
        "total_sessions": total_sessions,
        "active_sessions": len([s for s in training_sessions.values() if s["status"] == "running"]),
        "total_experiments": len(experiments),
        "algorithm_stats": algorithm_stats,
        "system_info": {
            "cpu_usage": np.random.uniform(20, 80),
            "memory_usage": np.random.uniform(30, 70),
            "gpu_available": False
        },
        "last_updated": datetime.now().isoformat()
    }

# Hyperparameter tuning
@app.post("/api/tuning/start")
async def start_hyperparameter_tuning(algorithm: str, param_ranges: Dict[str, List[float]]):
    """Start hyperparameter tuning"""
    tuning_id = f"tuning_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "tuning_id": tuning_id,
        "message": "Hyperparameter tuning started",
        "algorithm": algorithm,
        "param_ranges": param_ranges,
        "estimated_time": "30 minutes"
    }

# Model evaluation
@app.post("/api/models/evaluate/{model_name}")
async def evaluate_model(model_name: str, test_episodes: int = 10):
    """Evaluate a model"""
    filepath = os.path.join("models", model_name)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Mock evaluation results
    results = {
        "model_name": model_name,
        "test_episodes": test_episodes,
        "avg_reward": np.random.uniform(50, 100),
        "std_reward": np.random.uniform(5, 15),
        "min_reward": np.random.uniform(30, 50),
        "max_reward": np.random.uniform(80, 100),
        "success_rate": np.random.uniform(0.7, 0.95),
        "evaluation_date": datetime.now().isoformat()
    }
    
    return results

# System health
@app.get("/api/system/health")
async def system_health():
    """Get system health status"""
    return {
        "status": "healthy",
        "uptime": "2 hours 30 minutes",
        "cpu_usage": np.random.uniform(20, 80),
        "memory_usage": np.random.uniform(30, 70),
        "disk_usage": np.random.uniform(40, 60),
        "active_connections": len(manager.active_connections),
        "active_trainings": len([s for s in training_sessions.values() if s["status"] == "running"]),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
