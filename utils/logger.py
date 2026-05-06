"""
utils/logger.py — Ghi log training ra file JSON
"""
import os
import json
import datetime
from typing import Any, Dict


class TrainingLogger:
    """Ghi mỗi episode ra file JSON Lines (.jsonl) để dễ phân tích."""

    def __init__(self, log_dir: str = "logs"):
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(log_dir, f"training_{ts}.jsonl")
        self._file = open(self.path, "w", encoding="utf-8")
        print(f"[Logger] Ghi log -> {self.path}")

    def log(self, data: Dict[str, Any]):
        self._file.write(json.dumps(data) + "\n")
        self._file.flush()

    def close(self):
        self._file.close()

    def __del__(self):
        try:
            self._file.close()
        except Exception:
            pass
