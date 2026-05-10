from fastapi import WebSocket
from typing import List
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_training_update(self, session_id: str, episode: int, total: int, metrics: dict):
        message = {
            "type": "training_update",
            "session_id": session_id,
            "episode": episode,
            "total_episodes": total,
            "progress": (episode / total) * 100,
            "metrics": metrics,
            "timestamp": str(asyncio.get_event_loop().time())
        }
        await self.broadcast(message)

    async def broadcast_model_update(self, action: str, model_name: str):
        message = {
            "type": "model_update",
            "action": action,  # "created", "deleted", "updated"
            "model_name": model_name,
            "timestamp": str(asyncio.get_event_loop().time())
        }
        await self.broadcast(message)

manager = ConnectionManager()
