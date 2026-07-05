#!/usr/bin/env python
"""
Propulsion window runner (baseline deterministic model; optional external bridge)

- Accepts propulsion/power/thermal inputs
- If `exec_path` provided, will shell out; otherwise runs a baseline duty-cycle model
- Writes outputs + manifest under `/w6/data/propulsion/<run_id>/`
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import hashlib
import math

ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / "w6" / "data" / "propulsion"
TOOL_KEY = "propulsion_window"
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
            "note": "Propulsion execution finished",
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-2000:],
        }
    except Exception as exc:
        return {"status": "error", "note": f"External exec failed: {exc}"}


def _baseline_compute(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Simple deterministic estimate: thrust, mass, duration, duty_cycle -> delta_v
    thrust_n = float(payload.get("thrust_n", 0.5))
    mass_kg = float(payload.get("mass_kg", 100.0))
    isp_s = float(payload.get("isp_s", 1500.0))
    duty = float(payload.get("duty_cycle", 0.5))
    duration_s = float(payload.get("duration_s", 3600.0))
    power_kw = float(payload.get("power_kw", 2.0))
    thermal_margin_c = float(payload.get("thermal_margin_c", 25.0))
    g0 = 9.80665

    # Effective on-thrust time
    t_on = max(duration_s * duty, 0.0)
    accel = thrust_n / max(mass_kg, 1e-6)
    delta_v_mps = accel * t_on
    mass_flow = thrust_n / (isp_s * g0) if isp_s > 0 else 0.0
    prop_used_kg = mass_flow * t_on
    # Simple power/thermal check flags
    power_ok = power_kw >= (thrust_n * 0.5 / 1000.0)
    thermal_ok = thermal_margin_c >= 0

    return {
        "status": "completed",
        "note": "Baseline duty-cycle propulsion window estimate",
        "delta_v_mps": delta_v_mps,
        "prop_used_kg": prop_used_kg,
        "thrust_n": thrust_n,
        "mass_kg": mass_kg,
        "isp_s": isp_s,
        "duty_cycle": duty,
        "duration_s": duration_s,
        "power_kw": power_kw,
        "thermal_margin_c": thermal_margin_c,
        "power_ok": power_ok,
        "thermal_ok": thermal_ok,
        "warnings": [] if power_ok and thermal_ok else ["power_check" if not power_ok else "thermal_check"],
    }


def run(payload: Dict[str, Any], output_dir: Path | None = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id = payload.get("run_id") or f"{TOOL_KEY}_{ts}"
    out_dir = output_dir or (DATA_ROOT / run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    payload_path = out_dir / "input_payload.json"
    payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    exec_path = payload.get("exec_path")
    run_info = _baseline_compute(payload)
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
        "job_type": "propulsion_window",
        "tool_key": TOOL_KEY,
        "tool_version": RUNNER_VERSION,
        "workspace": "w5_mission_planning",
        "project_id": payload.get("project_id", "LS-W5-MISSION"),
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
        "thrust_n": 0.5,
        "isp_s": 1500,
        "duty_cycle": 0.5,
        "tags": ["stub", "propulsion"],
    }
    if len(sys.argv) > 1 and Path(sys.argv[1]).exists():
        payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    arts, manifest = run(payload)
    print(json.dumps({"artifacts": arts, "manifest": manifest}, indent=2))
