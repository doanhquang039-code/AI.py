from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
import os
from pathlib import Path
from datetime import datetime
import numpy as np
import asyncio
import random
import shutil
import time
import hashlib

from ai.hyperparameter_tuner import HyperparameterTuner, HyperparameterSpace, OptimizationMethod

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

class TuningConfig(BaseModel):
    algorithm: str = "dqn"
    method: str = "random_search"
    trials: int = 8
    episodes: int = 100
    param_ranges: Dict[str, Any] = Field(default_factory=dict)

class IoTControlCommand(BaseModel):
    device_id: str
    mode: str = "auto"
    target_temperature: Optional[float] = None

class ProjectTaskUpdate(BaseModel):
    status: str
    owner: Optional[str] = None
    note: str = ""

class CloudSyncRequest(BaseModel):
    provider: str = "aws-iot"
    dataset: str = "telemetry"
    region: str = "ap-southeast-1"

class BiometricVerifyRequest(BaseModel):
    identity_id: str
    modality: str = "face"
    template_hash: str = ""
    liveness_score: float = 0.86

class CopilotQuestion(BaseModel):
    question: str
    focus: str = "overview"

class AnalyticsRunRequest(BaseModel):
    dataset: str = "operations"
    horizon: int = 7
    sensitivity: float = 0.72

# In-memory storage (replace with database in production)
training_sessions = {}
models_cache = []
active_websockets: List[WebSocket] = []
experiments = {}
tuning_sessions = {}
iot_commands = []
project_task_overrides: Dict[str, Dict[str, Any]] = {}
cloud_sync_jobs: List[Dict[str, Any]] = []
cloud_deployments: List[Dict[str, Any]] = []
biometric_profiles: Dict[str, Dict[str, Any]] = {}
biometric_events: List[Dict[str, Any]] = []
MODELS_DIR = Path("models")
ALLOWED_MODEL_EXTENSIONS = {".pt", ".npy"}
BIOMETRIC_MODALITIES = {
    "face": {
        "label": "Face Recognition",
        "threshold": 0.82,
        "signals": ["embedding", "liveness", "pose", "occlusion"],
    },
    "fingerprint": {
        "label": "Fingerprint",
        "threshold": 0.88,
        "signals": ["minutiae", "ridge_flow", "sensor_quality", "spoof_guard"],
    },
    "voice": {
        "label": "Voice Print",
        "threshold": 0.79,
        "signals": ["speaker_embedding", "noise_floor", "phrase_match", "replay_guard"],
    },
    "palm": {
        "label": "Palm Vein",
        "threshold": 0.84,
        "signals": ["vein_pattern", "temperature", "alignment", "sensor_quality"],
    },
}

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

def resolve_model_path(model_name: str) -> Path:
    """Return a safe model path inside the models directory."""
    safe_name = os.path.basename(model_name or "")
    if (
        not safe_name
        or safe_name != model_name
        or Path(safe_name).suffix.lower() not in ALLOWED_MODEL_EXTENSIONS
    ):
        raise HTTPException(status_code=400, detail="Invalid model filename")

    return MODELS_DIR / safe_name

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

@app.get("/api/projects")
async def get_projects():
    """Get the two primary product workstreams: AI Core and IoT AI."""
    return {
        "projects": [_apply_project_overrides(project) for project in _build_project_portfolio()],
        "updated_at": datetime.now().isoformat()
    }

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get a single project roadmap."""
    project = _find_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _apply_project_overrides(project)

@app.get("/api/projects/{project_id}/tasks")
async def get_project_tasks(project_id: str):
    """Get project tasks grouped by milestone."""
    project = _find_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project_id": project_id,
        "tasks": _apply_project_overrides(project)["tasks"],
    }

@app.patch("/api/projects/{project_id}/tasks/{task_id}")
async def update_project_task(project_id: str, task_id: str, update: ProjectTaskUpdate):
    """Update a project task status in memory."""
    project = _find_project(project_id)
    if not project or not any(task["id"] == task_id for task in project["tasks"]):
        raise HTTPException(status_code=404, detail="Task not found")

    key = f"{project_id}:{task_id}"
    project_task_overrides[key] = {
        "status": update.status,
        "owner": update.owner,
        "note": update.note,
        "updated_at": datetime.now().isoformat(),
    }
    return {"project_id": project_id, "task_id": task_id, **project_task_overrides[key]}

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
    models = []
    
    if MODELS_DIR.exists():
        for filepath in MODELS_DIR.iterdir():
            if not filepath.is_file() or filepath.suffix.lower() not in ALLOWED_MODEL_EXTENSIONS:
                continue

            filename = filepath.name
            file_size = filepath.stat().st_size
            
            # Parse filename: algorithm_agentX_epY.ext
            parts = filename.replace('.pt', '').replace('.npy', '').split('_')
            
            models.append({
                "name": filename,
                "algorithm": parts[0].upper() if len(parts) > 0 else "Unknown",
                "agent_id": parts[1] if len(parts) > 1 else "0",
                "episodes": parts[2] if len(parts) > 2 else "0",
                "size": file_size,
                "created_at": datetime.fromtimestamp(filepath.stat().st_ctime).isoformat(),
                "performance": {
                    "accuracy": np.random.uniform(0.7, 0.95),
                    "reward": np.random.uniform(50, 100)
                }
            })
    
    return {"models": models}

@app.delete("/api/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a trained model"""
    filepath = resolve_model_path(model_name)
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        filepath.unlink()
        return {"message": f"Model {model_name} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models/export/{model_name}")
async def export_model(model_name: str):
    """Export a model file."""
    filepath = resolve_model_path(model_name)
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Model not found")

    return FileResponse(str(filepath), media_type="application/octet-stream", filename=model_name)

@app.post("/api/models/import")
async def import_model(file: UploadFile = File(...)):
    """Import a model file into the models directory."""
    MODELS_DIR.mkdir(exist_ok=True)
    safe_filename = os.path.basename(file.filename or "")
    filepath = resolve_model_path(safe_filename)

    with filepath.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    return {
        "message": f"Model {safe_filename} imported successfully",
        "filename": safe_filename,
        "size": filepath.stat().st_size
    }

@app.post("/api/models/compare")
async def compare_models(comparison: ModelComparison):
    """Compare two saved model files using lightweight metadata and demo metrics."""
    model1_path = resolve_model_path(comparison.model1)
    model2_path = resolve_model_path(comparison.model2)

    if not model1_path.exists() or not model2_path.exists():
        raise HTTPException(status_code=404, detail="One or both models not found")

    model1_score = float(np.random.uniform(0.70, 0.96))
    model2_score = float(np.random.uniform(0.70, 0.96))

    return {
        "model1": {
            "name": comparison.model1,
            "size": model1_path.stat().st_size,
            "score": round(model1_score, 3),
            "avg_reward": round(float(np.random.uniform(45, 100)), 2)
        },
        "model2": {
            "name": comparison.model2,
            "size": model2_path.stat().st_size,
            "score": round(model2_score, 3),
            "avg_reward": round(float(np.random.uniform(45, 100)), 2)
        },
        "winner": comparison.model1 if model1_score >= model2_score else comparison.model2,
        "comparison_date": datetime.now().isoformat()
    }

@app.post("/api/models/evaluate/{model_name}")
async def evaluate_model(model_name: str, test_episodes: int = 10):
    """Evaluate a saved model with demo metrics."""
    filepath = resolve_model_path(model_name)
    if not filepath.exists():
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
async def start_hyperparameter_tuning(payload: TuningConfig):
    """Run a lightweight hyperparameter tuning job and store the result."""
    tuning_id = f"tuning_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    algorithm = payload.algorithm.lower()
    trials = max(1, min(int(payload.trials), 50))
    method = _resolve_optimization_method(payload.method)
    tuner = HyperparameterTuner(
        _build_parameter_space(algorithm, payload.param_ranges),
        optimization_method=method,
        n_trials=trials,
        random_seed=random.randint(1, 999999),
    )

    started = time.perf_counter()
    _run_tuning_trials(tuner, algorithm, payload.episodes)
    duration = time.perf_counter() - started

    session = {
        "id": tuning_id,
        "algorithm": algorithm,
        "method": method.value,
        "status": "completed",
        "started_at": datetime.now().isoformat(),
        "duration_seconds": round(duration, 4),
        "trials_requested": trials,
        "trials_completed": len(tuner.trials),
        "best_trial": _json_safe(tuner.best_trial),
        "history": _json_safe(tuner.get_optimization_history()),
    }
    tuning_sessions[tuning_id] = session

    return {
        "tuning_id": tuning_id,
        "message": "Hyperparameter tuning completed",
        "algorithm": algorithm,
        "best_trial": session["best_trial"],
        "trials_completed": session["trials_completed"],
    }

@app.get("/api/tuning")
async def get_tuning_sessions():
    """List hyperparameter tuning sessions."""
    return {"sessions": list(tuning_sessions.values())}

@app.get("/api/tuning/{tuning_id}")
async def get_tuning_session(tuning_id: str):
    """Get a stored tuning session."""
    if tuning_id not in tuning_sessions:
        raise HTTPException(status_code=404, detail="Tuning session not found")
    return tuning_sessions[tuning_id]

def _resolve_optimization_method(method: str) -> OptimizationMethod:
    try:
        return OptimizationMethod((method or "random_search").lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Unsupported tuning method")

def _build_parameter_space(algorithm: str, ranges: Dict[str, Any]) -> List[HyperparameterSpace]:
    defaults = {
        "q_learning": [
            HyperparameterSpace("learning_rate", "continuous", 0.001, 0.5, log_scale=True),
            HyperparameterSpace("discount_factor", "continuous", 0.9, 0.999),
            HyperparameterSpace("epsilon_start", "continuous", 0.5, 1.0),
            HyperparameterSpace("epsilon_decay", "continuous", 0.99, 0.9999),
        ],
        "dqn": [
            HyperparameterSpace("learning_rate", "continuous", 0.0001, 0.01, log_scale=True),
            HyperparameterSpace("batch_size", "discrete", 16, 128),
            HyperparameterSpace("buffer_size", "discrete", 1000, 100000),
            HyperparameterSpace("target_update_freq", "discrete", 10, 1000),
            HyperparameterSpace("hidden_size", "categorical", values=[64, 128, 256, 512]),
        ],
        "ppo": [
            HyperparameterSpace("learning_rate", "continuous", 0.0001, 0.01, log_scale=True),
            HyperparameterSpace("clip_epsilon", "continuous", 0.1, 0.3),
            HyperparameterSpace("value_coef", "continuous", 0.1, 1.0),
            HyperparameterSpace("entropy_coef", "continuous", 0.001, 0.1, log_scale=True),
            HyperparameterSpace("n_steps", "discrete", 128, 2048),
        ],
    }
    parameter_space = defaults.get(algorithm, defaults["dqn"])

    if not ranges:
        return parameter_space

    customized = []
    for space in parameter_space:
        override = ranges.get(space.name)
        if not isinstance(override, dict):
            customized.append(space)
            continue

        if space.param_type == "categorical":
            values = override.get("values", space.values)
            customized.append(HyperparameterSpace(space.name, space.param_type, values=values))
        else:
            customized.append(HyperparameterSpace(
                space.name,
                space.param_type,
                override.get("min", space.min_value),
                override.get("max", space.max_value),
                log_scale=space.log_scale,
            ))
    return customized

def _score_tuning_trial(algorithm: str, params: Dict[str, Any], episodes: int):
    started = time.perf_counter()
    score = 0.55

    learning_rate = float(params.get("learning_rate", 0.001))
    score += max(0, 0.22 - abs(np.log10(learning_rate) + 3) * 0.08)

    if algorithm == "q_learning":
        score += float(params.get("discount_factor", 0.95)) * 0.2
        score += (1 - abs(float(params.get("epsilon_start", 0.8)) - 0.75)) * 0.08
    elif algorithm == "ppo":
        score += (1 - abs(float(params.get("clip_epsilon", 0.2)) - 0.2) / 0.2) * 0.12
        score += min(float(params.get("n_steps", 512)) / 2048, 1) * 0.08
    else:
        score += min(float(params.get("batch_size", 64)) / 128, 1) * 0.08
        score += min(float(params.get("hidden_size", 128)) / 512, 1) * 0.08

    score += min(max(episodes, 1), 1000) / 1000 * 0.05
    score += random.uniform(-0.025, 0.025)
    score = round(max(0.0, min(score, 0.99)), 4)
    metrics = {
        "estimated_reward": round(score * 100, 2),
        "stability": round(0.6 + score * 0.35, 4),
    }
    return score, time.perf_counter() - started, metrics

def _run_tuning_trials(tuner: HyperparameterTuner, algorithm: str, episodes: int):
    for _ in range(tuner.n_trials):
        params = tuner.sample_parameters()
        score, training_time, metrics = _score_tuning_trial(algorithm, params, episodes)
        tuner.record_trial(params, score, training_time, metrics)

def _json_safe(value: Any) -> Any:
    if hasattr(value, "__dict__") and not isinstance(value, dict):
        value = value.__dict__
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value

@app.get("/api/iot/devices")
async def get_iot_devices():
    """Get simulated IoT devices with AI-ready status metadata."""
    return {"devices": _generate_iot_devices(), "timestamp": datetime.now().isoformat()}

@app.get("/api/iot/fleet/summary")
async def get_iot_fleet_summary():
    """Get aggregated IoT fleet health, risk, and efficiency metrics."""
    devices = _generate_iot_devices()
    anomaly_scores = [device["ai"]["anomaly_score"] for device in devices]
    total_energy = round(sum(device["metrics"]["energy_kw"] for device in devices), 2)
    high_risk = [device for device in devices if device["ai"]["risk"] == "high"]
    warning_count = len([device for device in devices if device["status"] == "warning"])

    return {
        "device_count": len(devices),
        "online_count": len([device for device in devices if device["status"] == "online"]),
        "warning_count": warning_count,
        "high_risk_count": len(high_risk),
        "avg_anomaly_score": round(float(np.mean(anomaly_scores)), 3),
        "total_energy_kw": total_energy,
        "estimated_savings_kw": round(total_energy * random.uniform(0.08, 0.16), 2),
        "fleet_health": round(max(0.0, 1.0 - float(np.mean(anomaly_scores))) * 100, 1),
        "top_risk_device": max(devices, key=lambda device: device["ai"]["anomaly_score"]),
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/api/iot/commands")
async def get_iot_commands():
    """Get queued IoT control command history."""
    return {"commands": list(reversed(iot_commands[-25:])), "count": len(iot_commands)}

@app.post("/api/iot/optimize")
async def optimize_iot_fleet(payload: Dict[str, Any]):
    """Generate a simulated AI optimization plan for the IoT fleet."""
    objective = payload.get("objective", "energy")
    devices = _generate_iot_devices()
    high_risk_devices = [device for device in devices if device["ai"]["risk"] in {"high", "medium"}]
    energy_kw = sum(device["metrics"]["energy_kw"] for device in devices)
    plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100, 999)}"

    actions = [
        {
            "device_id": device["id"],
            "action": "maintenance_check" if device["ai"]["risk"] == "high" else "setpoint_adjustment",
            "priority": device["ai"]["risk"],
            "expected_impact": f"{round(device['ai']['anomaly_score'] * 18, 1)}% risk reduction",
        }
        for device in high_risk_devices[:4]
    ]

    if not actions:
        actions.append({
            "device_id": devices[0]["id"],
            "action": "eco_schedule",
            "priority": "low",
            "expected_impact": "6.5% energy reduction",
        })

    return {
        "plan_id": plan_id,
        "objective": objective,
        "confidence": round(random.uniform(0.78, 0.94), 3),
        "estimated_savings_kw": round(energy_kw * random.uniform(0.09, 0.18), 2),
        "actions": actions,
        "created_at": datetime.now().isoformat(),
    }

@app.get("/api/iot/cloud/providers")
async def get_iot_cloud_providers():
    """Get supported IoT cloud service connectors."""
    providers = [
        {
            "id": "aws-iot",
            "name": "AWS IoT Core",
            "region": "ap-southeast-1",
            "status": "connected",
            "protocols": ["MQTT", "HTTPS", "Rules Engine"],
            "latency_ms": random.randint(38, 92),
        },
        {
            "id": "azure-iot",
            "name": "Azure IoT Hub",
            "region": "southeastasia",
            "status": "standby",
            "protocols": ["MQTT", "AMQP", "Device Twin"],
            "latency_ms": random.randint(45, 110),
        },
        {
            "id": "gcp-iot",
            "name": "Google Pub/Sub IoT Bridge",
            "region": "asia-southeast1",
            "status": "standby",
            "protocols": ["Pub/Sub", "Cloud Run", "BigQuery"],
            "latency_ms": random.randint(52, 130),
        },
    ]
    return {"providers": providers, "timestamp": datetime.now().isoformat()}

@app.get("/api/iot/cloud/status")
async def get_iot_cloud_status():
    """Get cloud ingestion and edge deployment health."""
    queued = len([job for job in cloud_sync_jobs if job["status"] == "queued"])
    synced = len([job for job in cloud_sync_jobs if job["status"] == "synced"])
    return {
        "ingestion_rate_per_min": random.randint(2400, 9800),
        "stream_lag_ms": random.randint(40, 280),
        "storage_used_gb": round(random.uniform(12.5, 88.0), 2),
        "rules_active": random.randint(8, 24),
        "queued_sync_jobs": queued,
        "synced_jobs": synced,
        "deployment_count": len(cloud_deployments),
        "sla_score": round(random.uniform(98.2, 99.98), 2),
        "timestamp": datetime.now().isoformat(),
    }

@app.post("/api/iot/cloud/sync")
async def post_iot_cloud_sync(request: CloudSyncRequest):
    """Queue a simulated telemetry sync job to a cloud provider."""
    job = {
        "id": f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(cloud_sync_jobs) + 1}",
        "provider": request.provider,
        "dataset": request.dataset,
        "region": request.region,
        "records": random.randint(5000, 45000),
        "status": "synced",
        "duration_ms": random.randint(350, 2400),
        "created_at": datetime.now().isoformat(),
    }
    cloud_sync_jobs.append(job)
    return job

@app.get("/api/iot/cloud/sync")
async def get_iot_cloud_sync_jobs():
    """Get recent cloud sync jobs."""
    return {"jobs": list(reversed(cloud_sync_jobs[-20:])), "count": len(cloud_sync_jobs)}

@app.post("/api/iot/cloud/deploy")
async def post_iot_cloud_deploy(payload: Dict[str, Any]):
    """Create a simulated cloud-to-edge deployment."""
    target = payload.get("target", "edge-gateway-a")
    artifact = payload.get("artifact", "anomaly-model-v1")
    deployment = {
        "id": f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(cloud_deployments) + 1}",
        "target": target,
        "artifact": artifact,
        "version": payload.get("version", "1.0.0"),
        "status": "rolling_out",
        "progress": random.randint(35, 88),
        "created_at": datetime.now().isoformat(),
    }
    cloud_deployments.append(deployment)
    return deployment

@app.get("/api/iot/cloud/deployments")
async def get_iot_cloud_deployments():
    """Get recent cloud-to-edge deployments."""
    defaults = [
        {
            "id": "deploy_demo_gateway",
            "target": "edge-gateway-a",
            "artifact": "telemetry-normalizer",
            "version": "0.9.4",
            "status": "healthy",
            "progress": 100,
            "created_at": datetime.now().isoformat(),
        }
    ]
    return {
        "deployments": list(reversed(cloud_deployments[-20:])) or defaults,
        "count": len(cloud_deployments),
    }

@app.get("/api/iot/cloud/digital-twin")
async def get_iot_cloud_digital_twin():
    """Get a simulated cloud digital twin graph summary."""
    devices = _generate_iot_devices()
    return {
        "nodes": [
            {"id": device["id"], "label": device["name"], "type": "sensor", "risk": device["ai"]["risk"]}
            for device in devices
        ] + [
            {"id": "cloud-ingestion", "label": "Cloud Ingestion", "type": "cloud", "risk": "low"},
            {"id": "edge-gateway-a", "label": "Edge Gateway A", "type": "gateway", "risk": "low"},
        ],
        "edges": [
            {"source": device["id"], "target": "edge-gateway-a", "latency_ms": random.randint(5, 28)}
            for device in devices
        ] + [
            {"source": "edge-gateway-a", "target": "cloud-ingestion", "latency_ms": random.randint(32, 95)}
        ],
        "timestamp": datetime.now().isoformat(),
    }

def _generate_iot_devices() -> List[Dict[str, Any]]:
    devices = []
    for index, zone in enumerate(["Factory A", "Factory B", "Cold Storage", "Solar Roof", "Server Room"], start=1):
        temperature = round(random.uniform(18, 38), 1)
        vibration = round(random.uniform(0.05, 1.4), 3)
        energy = round(random.uniform(1.5, 12.0), 2)
        anomaly_score = _iot_anomaly_score(temperature, vibration, energy)
        devices.append({
            "id": f"iot-{index:03d}",
            "name": f"Edge Sensor {index}",
            "zone": zone,
            "status": "warning" if anomaly_score > 0.65 else "online",
            "last_seen": datetime.now().isoformat(),
            "metrics": {
                "temperature": temperature,
                "humidity": round(random.uniform(35, 82), 1),
                "vibration": vibration,
                "energy_kw": energy,
            },
            "ai": {
                "anomaly_score": anomaly_score,
                "risk": "high" if anomaly_score > 0.78 else "medium" if anomaly_score > 0.55 else "low",
                "predicted_maintenance_hours": int(max(8, 180 - anomaly_score * 150)),
            }
        })
    return devices

@app.get("/api/iot/telemetry")
async def get_iot_telemetry(device_id: str = "iot-001", points: int = 24):
    """Get time-series telemetry and AI forecast for one IoT device."""
    safe_points = max(6, min(points, 96))
    baseline = random.uniform(22, 30)
    telemetry = []
    for idx in range(safe_points):
        drift = idx / safe_points * random.uniform(-1.5, 2.5)
        temperature = baseline + drift + np.sin(idx / 3) * 1.8 + random.uniform(-0.4, 0.4)
        vibration = max(0.02, random.uniform(0.05, 0.55) + (idx / safe_points) * random.uniform(0, 0.5))
        energy = max(0.5, random.uniform(2.5, 8.5) + np.cos(idx / 4) * 0.8)
        telemetry.append({
            "index": idx,
            "temperature": round(float(temperature), 2),
            "vibration": round(float(vibration), 3),
            "energy_kw": round(float(energy), 2),
            "anomaly_score": _iot_anomaly_score(temperature, vibration, energy),
        })

    recent_temp = float(np.mean([point["temperature"] for point in telemetry[-5:]]))
    recent_vibration = float(np.mean([point["vibration"] for point in telemetry[-5:]]))
    forecast = [
        {
            "index": safe_points + idx,
            "temperature": round(recent_temp + idx * random.uniform(-0.08, 0.22), 2),
            "vibration": round(max(0.02, recent_vibration + idx * random.uniform(-0.005, 0.018)), 3),
        }
        for idx in range(1, 7)
    ]

    return {
        "device_id": os.path.basename(device_id),
        "telemetry": telemetry,
        "forecast": forecast,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/iot/insights")
async def get_iot_insights():
    """Get AI-generated IoT operations insights."""
    return {
        "insights": [
            {
                "title": "Cooling optimization",
                "severity": "medium",
                "impact": "Estimated 8-12% energy reduction",
                "recommendation": "Shift HVAC setpoint by 1.5 C during low-load periods."
            },
            {
                "title": "Predictive maintenance",
                "severity": "high",
                "impact": "Vibration trend indicates bearing wear risk",
                "recommendation": "Schedule inspection for Edge Sensor 2 within 48 hours."
            },
            {
                "title": "Sensor calibration",
                "severity": "low",
                "impact": "Humidity variance is outside peer group baseline",
                "recommendation": "Run calibration check on Cold Storage humidity probe."
            }
        ],
        "generated_at": datetime.now().isoformat()
    }

@app.post("/api/iot/control")
async def post_iot_control(command: IoTControlCommand):
    """Store a simulated IoT control command."""
    record = {
        "id": f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(iot_commands) + 1}",
        "device_id": os.path.basename(command.device_id),
        "mode": command.mode,
        "target_temperature": command.target_temperature,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
    }
    iot_commands.append(record)
    return record

def _iot_anomaly_score(temperature: float, vibration: float, energy: float) -> float:
    temp_score = max(0.0, min(1.0, abs(float(temperature) - 25.0) / 18.0))
    vibration_score = max(0.0, min(1.0, float(vibration) / 1.3))
    energy_score = max(0.0, min(1.0, float(energy) / 12.0))
    score = temp_score * 0.34 + vibration_score * 0.46 + energy_score * 0.2
    return round(float(score), 3)

@app.get("/api/biometric/modalities")
async def get_biometric_modalities():
    """Get supported biometric AI modalities and operational thresholds."""
    return {
        "modalities": [
            {"id": key, **value}
            for key, value in BIOMETRIC_MODALITIES.items()
        ],
        "privacy": {
            "raw_sample_storage": False,
            "template_strategy": "sha256-demo-template",
            "note": "Demo endpoints keep only derived metadata and template hashes.",
        },
    }

@app.get("/api/biometric/summary")
async def get_biometric_summary():
    """Get biometric AI operations summary."""
    profile_count = len(biometric_profiles)
    event_count = len(biometric_events)
    verified_count = len([event for event in biometric_events if event.get("decision") == "verified"])
    avg_quality = (
        round(float(np.mean([profile["quality_score"] for profile in biometric_profiles.values()])), 3)
        if biometric_profiles else 0.0
    )
    avg_match = (
        round(float(np.mean([event["match_score"] for event in biometric_events])), 3)
        if biometric_events else 0.0
    )
    return {
        "profile_count": profile_count,
        "event_count": event_count,
        "verified_count": verified_count,
        "review_count": len([event for event in biometric_events if event.get("decision") == "review"]),
        "avg_quality": avg_quality,
        "avg_match": avg_match,
        "modalities_online": len(BIOMETRIC_MODALITIES),
        "risk_level": "low" if avg_match >= 0.84 or event_count == 0 else "medium",
        "updated_at": datetime.now().isoformat(),
    }

@app.get("/api/biometric/profiles")
async def get_biometric_profiles():
    """List enrolled biometric profiles without raw samples."""
    return {
        "profiles": sorted(
            biometric_profiles.values(),
            key=lambda profile: profile["enrolled_at"],
            reverse=True,
        )
    }

@app.post("/api/biometric/enroll")
async def enroll_biometric_profile(
    identity_id: str = Form(...),
    display_name: str = Form(""),
    modality: str = Form("face"),
    sample: UploadFile = File(None),
):
    """Enroll a biometric demo profile using derived metadata only."""
    if modality not in BIOMETRIC_MODALITIES:
        raise HTTPException(status_code=400, detail="Unsupported biometric modality")

    sample_bytes = await sample.read() if sample else b""
    template_hash = _biometric_template_hash(identity_id, modality, sample_bytes)
    quality_score = _biometric_quality_score(template_hash, len(sample_bytes), modality)
    profile_key = f"{identity_id}:{modality}"
    profile = {
        "id": profile_key,
        "identity_id": identity_id,
        "display_name": display_name or identity_id,
        "modality": modality,
        "template_hash": template_hash,
        "quality_score": quality_score,
        "sample_size": len(sample_bytes),
        "status": "ready" if quality_score >= 0.72 else "needs_retake",
        "enrolled_at": datetime.now().isoformat(),
    }
    biometric_profiles[profile_key] = profile
    biometric_events.append({
        "id": f"bio_evt_{len(biometric_events) + 1:04d}",
        "identity_id": identity_id,
        "modality": modality,
        "type": "enrollment",
        "match_score": quality_score,
        "decision": profile["status"],
        "created_at": profile["enrolled_at"],
    })
    return profile

@app.post("/api/biometric/verify")
async def verify_biometric_profile(request: BiometricVerifyRequest):
    """Verify a biometric demo profile against an enrolled template hash."""
    if request.modality not in BIOMETRIC_MODALITIES:
        raise HTTPException(status_code=400, detail="Unsupported biometric modality")

    profile_key = f"{request.identity_id}:{request.modality}"
    profile = biometric_profiles.get(profile_key)
    if not profile:
        raise HTTPException(status_code=404, detail="Biometric profile not found")

    match_score = _biometric_match_score(
        enrolled_hash=profile["template_hash"],
        probe_hash=request.template_hash or profile["template_hash"],
        liveness_score=request.liveness_score,
        quality_score=profile["quality_score"],
    )
    threshold = BIOMETRIC_MODALITIES[request.modality]["threshold"]
    decision = "verified" if match_score >= threshold and request.liveness_score >= 0.68 else "review"
    event = {
        "id": f"bio_evt_{len(biometric_events) + 1:04d}",
        "identity_id": request.identity_id,
        "modality": request.modality,
        "type": "verification",
        "match_score": match_score,
        "threshold": threshold,
        "liveness_score": round(max(0.0, min(1.0, request.liveness_score)), 3),
        "decision": decision,
        "created_at": datetime.now().isoformat(),
    }
    biometric_events.append(event)
    return event

@app.get("/api/biometric/audit")
async def get_biometric_audit():
    """Get recent biometric AI events."""
    return {"events": list(reversed(biometric_events[-30:]))}

@app.get("/api/copilot/briefing")
async def get_ai_copilot_briefing():
    """Generate an AI operations briefing across the research workspace."""
    models_count = len(os.listdir(MODELS_DIR)) if MODELS_DIR.exists() else 0
    active_trainings = len([session for session in training_sessions.values() if session["status"] == "running"])
    fleet_devices = _generate_iot_devices()
    avg_iot_risk = round(float(np.mean([device["ai"]["anomaly_score"] for device in fleet_devices])), 3)
    biometric_quality = (
        round(float(np.mean([profile["quality_score"] for profile in biometric_profiles.values()])), 3)
        if biometric_profiles else 0.0
    )
    project_health = [_apply_project_overrides(project)["health"] for project in _build_project_portfolio()]
    readiness = round(float(np.mean(project_health)), 1) if project_health else 0.0
    analytics_summary = await get_data_analytics_summary("operations")

    risks = []
    if models_count == 0:
        risks.append("Model registry is empty; train or import a baseline model before comparison.")
    if active_trainings == 0:
        risks.append("No active training jobs; schedule a short benchmark run to keep metrics fresh.")
    if avg_iot_risk >= 0.45:
        risks.append("IoT anomaly baseline is trending high; review top-risk telemetry before deployment.")
    if biometric_profiles and biometric_quality < 0.72:
        risks.append("Biometric enrollment quality is below target; retake low quality samples.")
    if not biometric_profiles:
        risks.append("Biometric module has no enrolled templates; enroll a demo identity to test verification.")

    recommendations = [
        {
            "title": "Create a baseline run",
            "area": "training",
            "priority": "high" if models_count == 0 else "medium",
            "action": "Run DQN for 20-50 episodes, then compare against PPO or A2C.",
        },
        {
            "title": "Tune one algorithm",
            "area": "optimization",
            "priority": "medium",
            "action": "Start random search with 5-8 trials and promote the best params to training config.",
        },
        {
            "title": "Harden identity AI",
            "area": "biometric",
            "priority": "high" if not biometric_profiles else "medium",
            "action": "Enroll one face and one fingerprint profile, then verify with liveness above 0.85.",
        },
        {
            "title": "Review edge anomalies",
            "area": "iot",
            "priority": "medium" if avg_iot_risk < 0.45 else "high",
            "action": "Open IoT AI and run Optimize Fleet to generate control recommendations.",
        },
    ]

    return {
        "readiness": readiness,
        "signals": {
            "models": models_count,
            "active_trainings": active_trainings,
            "tuning_sessions": len(tuning_sessions),
            "iot_avg_anomaly": avg_iot_risk,
            "biometric_profiles": len(biometric_profiles),
            "biometric_avg_quality": biometric_quality,
            "analytics_quality": analytics_summary["quality_score"],
            "analytics_anomalies": analytics_summary["anomaly_count"],
        },
        "risks": risks[:5],
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat(),
    }

@app.post("/api/copilot/ask")
async def ask_ai_copilot(question: CopilotQuestion):
    """Answer an AI operations question with local project context."""
    prompt = (question.question or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Question is required")

    lowered = prompt.lower()
    briefing = await get_ai_copilot_briefing()
    if any(keyword in lowered for keyword in ["face", "finger", "biometric", "khuôn mặt", "vân tay"]):
        answer = (
            "Biometric AI is ready as a privacy-first demo pipeline. Enroll a profile, verify it with liveness, "
            "then review audit events. Next technical step: connect a real embedding adapter and encrypt templates."
        )
        next_steps = ["Enroll face and fingerprint samples", "Verify with liveness >= 0.85", "Add OpenCV/SDK adapter layer"]
    elif any(keyword in lowered for keyword in ["train", "model", "dqn", "ppo", "training"]):
        answer = (
            f"The workspace currently sees {briefing['signals']['models']} model files and "
            f"{briefing['signals']['active_trainings']} active training jobs. Start with a small DQN baseline, "
            "then run tuning before comparing models."
        )
        next_steps = ["Run a 50 episode DQN baseline", "Start hyperparameter tuning", "Compare best model against PPO"]
    elif any(keyword in lowered for keyword in ["iot", "device", "sensor", "edge"]):
        answer = (
            f"IoT average anomaly is {briefing['signals']['iot_avg_anomaly']}. Use Optimize Fleet, inspect the "
            "top-risk device, and deploy only after the cloud sync queue is clean."
        )
        next_steps = ["Open IoT AI", "Run Optimize Fleet", "Deploy edge model if anomaly score is stable"]
    else:
        answer = (
            f"Overall AI readiness is {briefing['readiness']}%. The highest value move is to create a baseline "
            "training run, enroll a biometric demo profile, and keep IoT anomaly monitoring active."
        )
        next_steps = ["Start a baseline training run", "Enroll a biometric profile", "Check Project Hub active tasks"]

    return {
        "answer": answer,
        "focus": question.focus,
        "next_steps": next_steps,
        "confidence": 0.86,
        "generated_at": datetime.now().isoformat(),
    }

@app.get("/api/data-analytics/datasets")
async def get_data_analytics_datasets():
    """List synthetic datasets available for AI analytics."""
    return {
        "datasets": [
            {
                "id": "operations",
                "name": "AI Operations",
                "description": "Training throughput, model quality, runtime health, and task completion.",
                "records": 720,
                "freshness": "realtime-demo",
            },
            {
                "id": "iot",
                "name": "IoT Telemetry",
                "description": "Device energy, anomaly, vibration, and maintenance prediction signals.",
                "records": 1440,
                "freshness": "streaming-demo",
            },
            {
                "id": "biometric",
                "name": "Biometric Identity",
                "description": "Enrollment quality, liveness, verification score, and audit decisions.",
                "records": max(120, len(biometric_events) * 12),
                "freshness": "event-driven-demo",
            },
        ],
        "generated_at": datetime.now().isoformat(),
    }

@app.get("/api/data-analytics/summary")
async def get_data_analytics_summary(dataset: str = "operations"):
    """Get AI analytics summary for a dataset."""
    points = _analytics_series(dataset, 30)
    values = [point["value"] for point in points]
    anomalies = [point for point in points if point["anomaly_score"] >= 0.72]
    trend = values[-1] - values[0] if values else 0.0
    return {
        "dataset": dataset,
        "records": len(points),
        "mean": round(float(np.mean(values)), 3),
        "min": round(float(np.min(values)), 3),
        "max": round(float(np.max(values)), 3),
        "trend": round(float(trend), 3),
        "anomaly_count": len(anomalies),
        "quality_score": round(max(0.5, min(0.99, 1.0 - (len(anomalies) / max(len(points), 1)) * 0.8)), 3),
        "updated_at": datetime.now().isoformat(),
    }

@app.post("/api/data-analytics/run")
async def run_data_analytics(request: AnalyticsRunRequest):
    """Run a deterministic AI analytics pass over a synthetic dataset."""
    horizon = max(3, min(int(request.horizon), 30))
    sensitivity = max(0.4, min(float(request.sensitivity), 0.95))
    history = _analytics_series(request.dataset, 36)
    values = [point["value"] for point in history]
    anomalies = [point for point in history if point["anomaly_score"] >= sensitivity]
    forecast = _analytics_forecast(values, horizon)
    correlations = _analytics_correlations(request.dataset)
    recommendations = _analytics_recommendations(request.dataset, anomalies, forecast)
    return {
        "run_id": f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "dataset": request.dataset,
        "sensitivity": sensitivity,
        "history": history,
        "forecast": forecast,
        "anomalies": anomalies[-8:],
        "correlations": correlations,
        "recommendations": recommendations,
        "generated_at": datetime.now().isoformat(),
    }

@app.get("/api/data-analytics/insights")
async def get_data_analytics_insights(dataset: str = "operations"):
    """Get concise analytics insights for cards and dashboards."""
    summary = await get_data_analytics_summary(dataset)
    direction = "up" if summary["trend"] >= 0 else "down"
    severity = "high" if summary["anomaly_count"] >= 6 else "medium" if summary["anomaly_count"] >= 3 else "low"
    return {
        "insights": [
            {
                "title": "Trend direction",
                "severity": "medium" if abs(summary["trend"]) > 8 else "low",
                "body": f"{dataset} signal is trending {direction} by {abs(summary['trend']):.2f} points over the window.",
            },
            {
                "title": "Anomaly pressure",
                "severity": severity,
                "body": f"{summary['anomaly_count']} anomalies detected with quality score {summary['quality_score']:.2f}.",
            },
            {
                "title": "Recommended next step",
                "severity": "low",
                "body": "Run forecast analysis, review correlation drivers, then promote stable signals into Copilot briefing.",
            },
        ],
        "summary": summary,
    }

def _analytics_series(dataset: str, points: int) -> List[Dict[str, Any]]:
    safe_dataset = dataset if dataset in {"operations", "iot", "biometric"} else "operations"
    base = {"operations": 68.0, "iot": 42.0, "biometric": 74.0}[safe_dataset]
    volatility = {"operations": 7.0, "iot": 14.0, "biometric": 9.5}[safe_dataset]
    series = []
    for index in range(points):
        seasonal = np.sin(index / 3.2) * volatility * 0.38
        drift = index * {"operations": 0.16, "iot": -0.05, "biometric": 0.11}[safe_dataset]
        noise = random.uniform(-volatility * 0.35, volatility * 0.35)
        value = max(0.0, min(100.0, base + seasonal + drift + noise))
        rolling_target = base + drift
        anomaly_score = max(0.0, min(0.99, abs(value - rolling_target) / max(volatility * 1.25, 1.0)))
        series.append({
            "index": index,
            "label": f"T-{points - index - 1}",
            "value": round(float(value), 3),
            "anomaly_score": round(float(anomaly_score), 3),
        })
    return series

def _analytics_forecast(values: List[float], horizon: int) -> List[Dict[str, Any]]:
    if not values:
        values = [50.0]
    recent = values[-8:]
    slope = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)
    baseline = recent[-1]
    forecast = []
    for step in range(1, horizon + 1):
        confidence = max(0.55, 0.92 - step * 0.025)
        value = max(0.0, min(100.0, baseline + slope * step + np.sin(step / 2) * 1.8))
        forecast.append({
            "step": step,
            "value": round(float(value), 3),
            "confidence": round(float(confidence), 3),
        })
    return forecast

def _analytics_correlations(dataset: str) -> List[Dict[str, Any]]:
    if dataset == "iot":
        pairs = [("energy_kw", 0.76), ("vibration", 0.69), ("temperature", 0.58), ("cloud_lag", 0.41)]
    elif dataset == "biometric":
        pairs = [("liveness_score", 0.81), ("sample_quality", 0.73), ("sensor_quality", 0.66), ("template_age", -0.34)]
    else:
        pairs = [("training_runs", 0.74), ("model_count", 0.61), ("system_health", 0.57), ("open_tasks", -0.42)]
    return [{"feature": feature, "correlation": score} for feature, score in pairs]

def _analytics_recommendations(dataset: str, anomalies: List[Dict[str, Any]], forecast: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    priority = "high" if len(anomalies) >= 5 else "medium" if anomalies else "low"
    forecast_delta = forecast[-1]["value"] - forecast[0]["value"] if len(forecast) > 1 else 0.0
    return [
        {
            "priority": priority,
            "title": "Investigate anomaly drivers",
            "action": f"Review top {min(len(anomalies), 5)} anomaly points in {dataset} and compare against correlation drivers.",
        },
        {
            "priority": "medium" if abs(forecast_delta) > 5 else "low",
            "title": "Watch forecast drift",
            "action": f"Forecast drift is {forecast_delta:.2f}; set an alert if it crosses 8 points.",
        },
        {
            "priority": "low",
            "title": "Promote to Copilot",
            "action": "Feed stable analytics signals into Copilot recommendations for daily operator briefing.",
        },
    ]

def _biometric_template_hash(identity_id: str, modality: str, sample_bytes: bytes) -> str:
    seed = sample_bytes if sample_bytes else f"{identity_id}:{modality}:{datetime.now().date()}".encode("utf-8")
    return hashlib.sha256(seed + f":{identity_id}:{modality}".encode("utf-8")).hexdigest()

def _biometric_quality_score(template_hash: str, sample_size: int, modality: str) -> float:
    entropy = int(template_hash[:8], 16) / 0xFFFFFFFF
    size_factor = min(sample_size / 250_000, 1.0) if sample_size else 0.62
    modality_bias = {"face": 0.05, "fingerprint": 0.08, "voice": 0.02, "palm": 0.06}.get(modality, 0.0)
    return round(max(0.45, min(0.99, 0.5 + entropy * 0.26 + size_factor * 0.18 + modality_bias)), 3)

def _biometric_match_score(enrolled_hash: str, probe_hash: str, liveness_score: float, quality_score: float) -> float:
    same_prefix = sum(1 for a, b in zip(enrolled_hash[:24], probe_hash[:24]) if a == b) / 24
    liveness = max(0.0, min(1.0, liveness_score))
    return round(max(0.0, min(0.995, 0.42 + same_prefix * 0.32 + liveness * 0.16 + quality_score * 0.1)), 3)

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

def _build_project_portfolio() -> List[Dict[str, Any]]:
    return [
        {
            "id": "ai-core",
            "name": "AI Core Platform",
            "summary": "Training, tuning, simulation, model operations, and decision intelligence.",
            "health": round(random.uniform(78, 94), 1),
            "stage": "buildout",
            "capabilities": [
                "Reinforcement learning lab",
                "Hyperparameter tuning",
                "Model evaluation and comparison",
                "Simulation visualization",
                "Experiment tracking",
            ],
            "metrics": {
                "models": len(os.listdir(MODELS_DIR)) if MODELS_DIR.exists() else 0,
                "active_trainings": len([s for s in training_sessions.values() if s["status"] == "running"]),
                "tuning_runs": len(tuning_sessions),
                "algorithms": 5,
            },
            "milestones": [
                {"id": "ai-m1", "name": "Training workspace", "progress": 82},
                {"id": "ai-m2", "name": "Model governance", "progress": 55},
                {"id": "ai-m3", "name": "Autonomous evaluation", "progress": 36},
            ],
            "tasks": [
                {"id": "ai-task-1", "title": "Persist tuning sessions to disk", "status": "next", "owner": "AI"},
                {"id": "ai-task-2", "title": "Promote best tuning params into training config", "status": "active", "owner": "AI"},
                {"id": "ai-task-3", "title": "Add experiment run comparison charts", "status": "next", "owner": "Frontend"},
                {"id": "ai-task-4", "title": "Model registry metadata and tags", "status": "backlog", "owner": "API"},
            ],
        },
        {
            "id": "iot-ai",
            "name": "IoT AI Operations",
            "summary": "Fleet telemetry, anomaly detection, energy optimization, and command orchestration.",
            "health": round(random.uniform(74, 91), 1),
            "stage": "buildout",
            "capabilities": [
                "Fleet health overview",
                "Telemetry forecasting",
                "Anomaly scoring",
                "Optimization planning",
                "Control command queue",
                "Cloud sync and deployment",
            ],
            "metrics": {
                "devices": 5,
                "queued_commands": len(iot_commands),
                "cloud_sync_jobs": len(cloud_sync_jobs),
                "cloud_deployments": len(cloud_deployments),
                "avg_anomaly": round(float(np.mean([_iot_anomaly_score(random.uniform(18, 38), random.uniform(0.05, 1.4), random.uniform(1.5, 12.0)) for _ in range(5)])), 3),
                "optimization_actions": random.randint(2, 6),
            },
            "milestones": [
                {"id": "iot-m1", "name": "Fleet observability", "progress": 76},
                {"id": "iot-m2", "name": "Control loop automation", "progress": 48},
                {"id": "iot-m3", "name": "Edge deployment readiness", "progress": 31},
            ],
            "tasks": [
                {"id": "iot-task-1", "title": "Persist command audit trail", "status": "active", "owner": "API"},
                {"id": "iot-task-2", "title": "Add device group filtering", "status": "next", "owner": "Frontend"},
                {"id": "iot-task-3", "title": "Train anomaly baseline per zone", "status": "next", "owner": "AI"},
                {"id": "iot-task-4", "title": "MQTT connector scaffold", "status": "active", "owner": "IoT"},
                {"id": "iot-task-5", "title": "Cloud digital twin deployment pipeline", "status": "next", "owner": "Cloud"},
            ],
        },
        {
            "id": "biometric-ai",
            "name": "Biometric AI Identity",
            "summary": "Face, fingerprint, voice, and palm-vein recognition pipelines with privacy-first audit trails.",
            "health": round(random.uniform(71, 89), 1),
            "stage": "prototype",
            "capabilities": [
                "Face recognition workflow",
                "Fingerprint template scoring",
                "Voice print verification",
                "Palm vein pipeline",
                "Liveness and spoof guard scoring",
                "Privacy-safe audit trail",
            ],
            "metrics": {
                "profiles": len(biometric_profiles),
                "events": len(biometric_events),
                "modalities": len(BIOMETRIC_MODALITIES),
                "avg_quality": round(float(np.mean([p["quality_score"] for p in biometric_profiles.values()])), 3) if biometric_profiles else 0.0,
            },
            "milestones": [
                {"id": "bio-m1", "name": "Enrollment and verification API", "progress": 68},
                {"id": "bio-m2", "name": "Operator dashboard", "progress": 52},
                {"id": "bio-m3", "name": "Real model adapter layer", "progress": 18},
            ],
            "tasks": [
                {"id": "bio-task-1", "title": "Wire OpenCV face embedding adapter", "status": "next", "owner": "AI"},
                {"id": "bio-task-2", "title": "Add fingerprint SDK connector interface", "status": "backlog", "owner": "AI"},
                {"id": "bio-task-3", "title": "Persist hashed biometric templates securely", "status": "next", "owner": "API"},
                {"id": "bio-task-4", "title": "Add anti-spoofing policy controls", "status": "active", "owner": "Security"},
            ],
        },
        {
            "id": "data-analytics-ai",
            "name": "Data Analytics AI",
            "summary": "Forecasting, anomaly detection, correlation analysis, and operational insight generation.",
            "health": round(random.uniform(75, 92), 1),
            "stage": "buildout",
            "capabilities": [
                "Synthetic analytics datasets",
                "Forecast generation",
                "Anomaly scoring",
                "Correlation drivers",
                "Recommendation engine",
            ],
            "metrics": {
                "datasets": 3,
                "forecast_horizon": 30,
                "analytics_quality": round(random.uniform(0.82, 0.96), 3),
                "insight_cards": 3,
            },
            "milestones": [
                {"id": "da-m1", "name": "Analytics API", "progress": 72},
                {"id": "da-m2", "name": "Forecast and anomaly UI", "progress": 61},
                {"id": "da-m3", "name": "Real data connectors", "progress": 22},
            ],
            "tasks": [
                {"id": "da-task-1", "title": "Add CSV and database dataset connectors", "status": "next", "owner": "API"},
                {"id": "da-task-2", "title": "Promote analytics signals into Copilot", "status": "active", "owner": "AI"},
                {"id": "da-task-3", "title": "Add chart library visualization layer", "status": "next", "owner": "Frontend"},
                {"id": "da-task-4", "title": "Persist analysis run history", "status": "backlog", "owner": "Data"},
            ],
        },
    ]

def _find_project(project_id: str) -> Optional[Dict[str, Any]]:
    return next((project for project in _build_project_portfolio() if project["id"] == project_id), None)

def _apply_project_overrides(project: Dict[str, Any]) -> Dict[str, Any]:
    project = json.loads(json.dumps(project))
    completed = 0
    for task in project["tasks"]:
        override = project_task_overrides.get(f"{project['id']}:{task['id']}")
        if override:
            task.update({key: value for key, value in override.items() if value is not None})
        if task["status"] == "done":
            completed += 1

    project["task_summary"] = {
        "total": len(project["tasks"]),
        "done": completed,
        "active": len([task for task in project["tasks"] if task["status"] == "active"]),
        "next": len([task for task in project["tasks"] if task["status"] == "next"]),
    }
    return project

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
