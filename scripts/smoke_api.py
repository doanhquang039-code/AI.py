import json
import os
import subprocess
import sys
import time
from http.client import HTTPConnection


PORT = int(os.environ.get("AI_SMOKE_PORT", "8012"))
HOST = "127.0.0.1"
BASE_PATHS = [
    "/",
    "/api/health",
    "/api/training/status",
    "/api/training/history",
    "/api/models",
    "/api/stats/summary",
    "/api/stats/performance",
    "/api/stats/detailed",
    "/api/algorithms",
    "/api/experiments",
    "/api/system/health",
]


def request(method, path, body=None):
    conn = HTTPConnection(HOST, PORT, timeout=5)
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    conn.request(method, path, body=payload, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    if response.status >= 400:
        raise RuntimeError(f"{method} {path} returned {response.status}: {data[:200]!r}")
    return response.status, data


def wait_for_server(deadline_seconds=10):
    deadline = time.time() + deadline_seconds
    last_error = None
    while time.time() < deadline:
        try:
            request("GET", "/api/health")
            return
        except Exception as error:
            last_error = error
            time.sleep(0.25)
    raise RuntimeError(f"Server did not start: {last_error}")


def main():
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.main:app",
        "--host",
        HOST,
        "--port",
        str(PORT),
    ]
    process = subprocess.Popen(
        cmd,
        cwd=os.path.dirname(os.path.dirname(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        wait_for_server()
        for path in BASE_PATHS:
            status, _ = request("GET", path)
            print(f"OK {status} {path}")

        training_config = {
            "algorithm": "dqn",
            "episodes": 3,
            "learning_rate": 0.001,
            "gamma": 0.99,
            "epsilon": 0.1,
        }
        status, data = request("POST", "/api/training/start", training_config)
        session_id = json.loads(data.decode("utf-8"))["session_id"]
        print(f"OK {status} /api/training/start")

        status, _ = request("POST", f"/api/training/stop/{session_id}", {})
        print(f"OK {status} /api/training/stop/{session_id}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"SMOKE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
