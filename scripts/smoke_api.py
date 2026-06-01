import json
import os
import subprocess
import sys
import time
from http.client import HTTPConnection


PORT = int(os.environ.get("AI_SMOKE_PORT", "8012"))
HOST = "127.0.0.1"
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(ROOT_DIR, "models")
SMOKE_MODEL_1 = "smoke_dqn_agent1_ep3.pt"
SMOKE_MODEL_2 = "smoke_ppo_agent1_ep3.pt"
SMOKE_NOT_MODEL = "smoke_notes.txt"
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


def request(method, path, body=None, expected_status=None):
    conn = HTTPConnection(HOST, PORT, timeout=5)
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    conn.request(method, path, body=payload, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    if expected_status is not None and response.status != expected_status:
        raise RuntimeError(f"{method} {path} returned {response.status}, expected {expected_status}: {data[:200]!r}")
    if expected_status is None and response.status >= 400:
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
        cwd=ROOT_DIR,
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

        os.makedirs(MODELS_DIR, exist_ok=True)
        model_paths = [
            os.path.join(MODELS_DIR, SMOKE_MODEL_1),
            os.path.join(MODELS_DIR, SMOKE_MODEL_2),
            os.path.join(MODELS_DIR, SMOKE_NOT_MODEL),
        ]
        for index, model_path in enumerate(model_paths, start=1):
            with open(model_path, "wb") as model_file:
                model_file.write(f"smoke model {index}".encode("utf-8"))

        try:
            status, data = request("GET", "/api/models")
            model_names = {model["name"] for model in json.loads(data.decode("utf-8"))["models"]}
            if SMOKE_NOT_MODEL in model_names:
                raise RuntimeError("/api/models included a non-model file")
            print(f"OK {status} /api/models excludes non-model files")

            status, _ = request("POST", "/api/models/compare", {"model1": SMOKE_MODEL_1, "model2": SMOKE_MODEL_2})
            print(f"OK {status} /api/models/compare")

            status, _ = request(
                "POST",
                "/api/models/compare",
                {"model1": "../outside.pt", "model2": SMOKE_MODEL_2},
                expected_status=400,
            )
            print(f"OK {status} /api/models/compare invalid filename")

            status, _ = request("POST", f"/api/models/evaluate/{SMOKE_MODEL_1}", {})
            print(f"OK {status} /api/models/evaluate/{SMOKE_MODEL_1}")

            status, _ = request("GET", f"/api/models/export/{SMOKE_MODEL_1}")
            print(f"OK {status} /api/models/export/{SMOKE_MODEL_1}")

            for model_name in (SMOKE_MODEL_1, SMOKE_MODEL_2):
                status, _ = request("DELETE", f"/api/models/{model_name}")
                print(f"OK {status} /api/models/{model_name}")
        finally:
            for model_path in model_paths:
                if os.path.exists(model_path):
                    os.remove(model_path)
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
