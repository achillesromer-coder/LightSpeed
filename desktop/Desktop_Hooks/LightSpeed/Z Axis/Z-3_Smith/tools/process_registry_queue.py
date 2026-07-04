"""
Process operations registry edit queue.

Reads `/w6/data/registry_edits/queue.json`, marks jobs as processing/complete, and
runs embed + depmap regeneration for each queued job.

Usage:
    python Z Axis/Z-3_Smith/tools/process_registry_queue.py
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "w6" / "data" / "registry_edits" / "queue.json"
EMBEDS_SCRIPT = ROOT / "Z Axis" / "Z-3_Smith" / "tools" / "generate_operations_embeds.py"
DEPINDEX_SCRIPT = ROOT / "Z Axis" / "Z-3_Smith" / "tools" / "generate_dataindex.py"


def load_queue() -> List[Dict]:
    if not QUEUE_PATH.exists():
        return []
    try:
        data = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_queue(queue: List[Dict]) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(queue, indent=2), encoding="utf-8")


def run_script(script: Path) -> None:
    subprocess.run(["python", str(script)], check=True)


def process_queue() -> None:
    queue = load_queue()
    changed = False
    for job in queue:
        if job.get("status") != "queued":
            continue
        job["status"] = "processing"
        changed = True
        try:
            if EMBEDS_SCRIPT.exists():
                run_script(EMBEDS_SCRIPT)
            if DEPINDEX_SCRIPT.exists():
                run_script(DEPINDEX_SCRIPT)
            job["status"] = "completed"
        except Exception as exc:
            job["status"] = f"error: {exc}"
    if changed:
        save_queue(queue)


if __name__ == "__main__":
    process_queue()
