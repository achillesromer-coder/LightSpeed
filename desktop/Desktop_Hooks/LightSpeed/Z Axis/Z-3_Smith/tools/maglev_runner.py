#!/usr/bin/env python
"""
Mag-Lev capture runner (bridge-ready; falls back to stub)

- Accepts scenario config (mass, orbit params, station specs)
- If external exec provided, attempts to run; otherwise writes stub outputs
- Writes outputs + manifest under `/w6/data/maglev/<run_id>/`
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import hashlib

ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / "w6" / "data" / "maglev"
TOOL_KEY = "maglev_capture"
RUNNER_VERSION = "0.1.0"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_manifest(output_dir: Path, manifest_fields: Dict[str, Any]) -> Path:
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest_fields, indent=2), encoding="utf-8")
    return path


def _maybe_run(exec_path: Path, payload_path: Path) -> Dict[str, Any]:
    try:
        result = subprocess.run([str(exec_path), str(payload_path)], capture_output=True, text=True, check=True)
        return {
            "status": "completed",
            "note": "Mag-Lev execution finished",
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
        }
    except Exception as exc:
        return {"status": "stub", "note": f"External exec failed or unavailable: {exc}"}


def run(payload: Dict[str, Any], output_dir: Path | None = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id = payload.get("run_id") or f"{TOOL_KEY}_{ts}"
    out_dir = output_dir or (DATA_ROOT / run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload_path = out_dir / "input_payload.json"
    payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    exec_path = payload.get("exec_path")
    run_info = {
        "status": "stub",
        "note": "External execution not attempted.",
        "timestamp": ts,
    }
    if exec_path and Path(exec_path).exists():
        run_info = _maybe_run(Path(exec_path), payload_path)

    result_path = out_dir / "result.json"
    result_path.write_text(json.dumps(run_info, indent=2), encoding="utf-8")

    artifacts = [
        {"path": str(payload_path), "kind": "input_payload", "sha256": _sha256(payload_path)},
        {"path": str(result_path), "kind": "result", "sha256": _sha256(result_path)},
    ]

    manifest_fields = {
        "id": run_id,
        "job_type": "maglev_capture",
        "tool_key": TOOL_KEY,
        "tool_version": RUNNER_VERSION,
        "workspace": "w1_deposit_analysis",
        "project_id": payload.get("project_id", "LS-W1-MAGLEV"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "inputs": payload,
        "outputs": artifacts,
        "status": run_info.get("status", "stub"),
        "metadata": {
            "tags": payload.get("tags", []),
            "note": run_info.get("note"),
        },
    }
    _write_manifest(out_dir, manifest_fields)
    return artifacts, manifest_fields


if __name__ == "__main__":
    import sys
    payload = {
        "mass_kg": 100.0,
        "initial_orbit": "GEO",
        "station_orbital": "Luke II",
        "station_ground": "Luke IV",
        "tags": ["stub", "maglev"],
    }
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    arts, manifest = run(payload)
    print(json.dumps({"artifacts": arts, "manifest": manifest}, indent=2))
