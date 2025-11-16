from __future__ import annotations
import json, time, hashlib
from pathlib import Path
from typing import Any

class Audit:
    """JSONL append-only; writes a chain hash for tamper-evidence."""
    def __init__(self, log_dir: Path):
        self.path = Path(log_dir) / "audit.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._prev = ""

    def write(self, actor: str, action: str, obj: str, data: dict[str, Any]) -> None:
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        rec = {"ts": ts, "actor": actor, "action": action, "object": obj, "data": data, "prev": self._prev}
        blob = json.dumps(rec, sort_keys=True, separators=(",", ":")).encode("utf-8")
        h = hashlib.sha256(blob).hexdigest()
        rec["hash"] = h
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        self._prev = h
