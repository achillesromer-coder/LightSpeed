#!/usr/bin/env python
"""
Energy trials runner (stubbed)

- Accepts trial_type (solar_hull or free_flow) with layer/graphene inputs
- Writes outputs + manifest under `/w6/data/energy/<run_id>/`
- Returns artifacts + manifest fields (no real material test yet)
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import hashlib

# LightSpeed root (two levels above Z Axis)
ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / "w6" / "data" / "energy"
TOOL_KEY = "energy_trials"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run(payload: Dict[str, Any], output_dir: Path | None = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id = payload.get("run_id") or f"{TOOL_KEY}_{ts}"
    out_dir = output_dir or (DATA_ROOT / run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "trial_type": payload.get("trial_type"),
        "layers": payload.get("layers"),
        "graphene_conc": payload.get("graphene_conc"),
        "status": "stub"
    }
    result_path = out_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    artifacts = [
        {"path": str(result_path), "kind": "result", "sha256": _sha256(result_path)}
    ]
    manifest_fields = {
        "id": run_id,
        "job_type": "energy_trial",
        "tool_key": TOOL_KEY,
        "workspace": "w6_asset_library",
        "project_id": payload.get("project_id", "LS-W6-ASSETS"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "inputs": payload,
        "outputs": artifacts,
        "status": "completed_stub",
        "metadata": {
            "tags": payload.get("tags", []),
            "note": "Stub energy trial; replace with real test harness."
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest_fields, indent=2), encoding="utf-8")
    return artifacts, manifest_fields


if __name__ == "__main__":
    arts, manifest = run({"trial_type": "solar_hull", "layers": 5, "graphene_conc": 80.0, "tags": ["stub", "demo"]})
    print(json.dumps({"artifacts": arts, "manifest": manifest}, indent=2))
