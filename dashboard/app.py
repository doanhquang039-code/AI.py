"""
dashboard/app.py — Flask Web Dashboard để giám sát AI training

Chạy song song với training qua thread.
Truy cập: http://localhost:5000
"""
import os
import json
import time
import threading
from pathlib import Path
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "ai-virtual-world-2026"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Global state — được cập nhật từ training thread
_dashboard_state = {
    "episode": 0,
    "world_stats": {},
    "agents": [],
    "rewards": {}, # algo -> list of rewards
    "foods": {},   # algo -> list of foods
    "running": False,
}
_lock = threading.Lock()

def update_dashboard(episode: int, world_stats: dict, agents: list):
    """Gọi hàm này từ training loop để cập nhật dashboard."""
    with _lock:
        _dashboard_state["episode"] = episode
        _dashboard_state["world_stats"] = world_stats
        _dashboard_state["agents"] = agents
        _dashboard_state["running"] = True

        for a in agents:
            algo = a.get("type", "Unknown")
            if algo not in _dashboard_state["rewards"]:
                _dashboard_state["rewards"][algo] = []
                _dashboard_state["foods"][algo] = []
            
            _dashboard_state["rewards"][algo].append(a["total_reward"])
            _dashboard_state["foods"][algo].append(a["food_eaten"])

    socketio.emit("update", _get_snapshot())


def _get_snapshot() -> dict:
    with _lock:
        s = _dashboard_state
        n = 100   # Chỉ gửi 100 episodes gần nhất
        
        rewards = {k: v[-n:] for k, v in s["rewards"].items()}
        foods = {k: v[-n:] for k, v in s["foods"].items()}
        
        return {
            "episode": s["episode"],
            "world": s["world_stats"],
            "agents": s["agents"],
            "rewards": rewards,
            "foods": foods,
            "running": s["running"],
        }


from i18n import t, get_language, set_language, language_menu

@app.route("/")
def index():
    return render_template("index.html", t=t, lang=get_language(), lang_menu=language_menu())

@app.route("/api/lang/<lang>")
def api_set_lang(lang):
    if set_language(lang):
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

    return jsonify(_get_snapshot())


@socketio.on("connect")
def on_connect():
    socketio.emit("update", _get_snapshot())


def run_dashboard(host: str = "0.0.0.0", port: int = 5000):
    """Chạy dashboard server."""
    print(f"\n🌐 Dashboard: http://localhost:{port}")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)
