#!/usr/bin/env python
"""
RFS/EMFF sweep runner (baseline implementation)

This replaces the previous stub runner with a deterministic, interpretable
baseline model suitable for early-stage parameter sweeps and dataset growth.

Inputs (payload):
{
  "material": "Cu",
  "frequencies_mhz": [1, 2, 5],
  "field_strength_tesla": [0.1, 0.2],
  "thickness_m": 0.01,
  "tags": ["rfs", "emff", "baseline"],
  "task_id": 123,        # optional
  "project_id": 456      # optional
}

Model (baseline):
- ω = 2πf
- δ = √(2/(ω μ σ))  (skin depth)
- attenuation = exp(-t/δ)
- response = (B * attenuation) / log10(1 + f)

Outputs:
- `result.json` with grid rows + parameters
- V1 ledger job + artifact registration + manifest.json in dataspace
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[3]
TOOL_KEY = "rfs_emff_sweep"

Z_AXIS_ROOT = ROOT / "Z Axis"
MEROVINGIAN_ROOT = Z_AXIS_ROOT / "Z-4_Merovingian"
TRINITY_ROOT = Z_AXIS_ROOT / "Z+3_Trinity"
for _p in (ROOT, Z_AXIS_ROOT, MEROVINGIAN_ROOT, TRINITY_ROOT):
    try:
        if _p.exists() and str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
    except Exception:
        pass


def _force_merovingian_core_package() -> None:
    try:
        if MEROVINGIAN_ROOT.exists() and str(MEROVINGIAN_ROOT) not in sys.path:
            sys.path.insert(0, str(MEROVINGIAN_ROOT))
    except Exception:
        return

    mod = sys.modules.get("core")
    if not mod:
        return

    mod_file = (getattr(mod, "__file__", "") or "").replace("\\", "/")
    mod_paths = [str(p).replace("\\", "/") for p in getattr(mod, "__path__", [])] if hasattr(mod, "__path__") else []
    is_merovingian = ("Z-4_Merovingian" in mod_file) or any("Z-4_Merovingian" in p for p in mod_paths)
    if is_merovingian:
        return

    for key in list(sys.modules.keys()):
        if key == "core" or key.startswith("core."):
            sys.modules.pop(key, None)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run(payload: Dict[str, Any], output_dir: Path | None = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    _force_merovingian_core_package()
    from core.services import get_db  # type: ignore

    db = get_db()

    material = (payload.get("material") or "unknown").strip() or "unknown"
    freqs_mhz = payload.get("frequencies_mhz") or []
    fields_t = payload.get("field_strength_tesla") or []
    thickness_m = float(payload.get("thickness_m") or 0.01)
    tags = payload.get("tags") or []

    materials = {
        "Au": {"sigma": 4.10e7, "mu_r": 1.0},
        "Cu": {"sigma": 5.96e7, "mu_r": 1.0},
        "Al": {"sigma": 3.77e7, "mu_r": 1.0},
        "Fe": {"sigma": 1.00e7, "mu_r": 500.0},
        "Ni": {"sigma": 1.43e7, "mu_r": 600.0},
    }
    props = materials.get(material, materials.get(material.title(), None)) or {"sigma": 1.0e6, "mu_r": 1.0}

    mu0 = 4 * math.pi * 1e-7
    sigma = float(props["sigma"])
    mu = mu0 * float(props["mu_r"])

    job = db.create_job_v1(
        job_type="rfs_emff_sweep",
        tool_key=TOOL_KEY,
        z_context="Z0_TheConstruct",
        params={
            "material": material,
            "frequencies_mhz": freqs_mhz,
            "field_strength_tesla": fields_t,
            "thickness_m": thickness_m,
            "material_props": props,
        },
        task_id=payload.get("task_id"),
        project_id=payload.get("project_id"),
        tags=tags,
        inputs=[],
    )
    job_id = int(job["job_id"])
    out_dir = Path(output_dir) if output_dir is not None else Path(job["run_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    grid: List[Dict[str, Any]] = []
    for f_mhz in freqs_mhz:
        f_hz = float(f_mhz) * 1e6
        omega = 2 * math.pi * max(f_hz, 1e-9)
        delta = math.sqrt(2.0 / max(omega * mu * sigma, 1e-30))
        attenuation = math.exp(-thickness_m / max(delta, 1e-12))
        for b_t in fields_t:
            b = float(b_t)
            response = (b * attenuation) / max(math.log10(1.0 + f_hz), 1e-12)
            grid.append(
                {
                    "frequency_mhz": float(f_mhz),
                    "field_tesla": float(b_t),
                    "omega_rad_s": omega,
                    "skin_depth_m": delta,
                    "attenuation": attenuation,
                    "response": response,
                }
            )

    sweep_result = {
        "status": "completed",
        "tool_key": TOOL_KEY,
        "job_id": job_id,
        "material": material,
        "material_props": props,
        "thickness_m": thickness_m,
        "grid": grid,
        "notes": [
            "Baseline model; extend with validated RFS/EMFF physics as datasets mature.",
            "Uses skin depth + attenuation proxy to support comparative sweeps and tuning.",
        ],
    }
    result_path = out_dir / "result.json"
    result_path.write_text(json.dumps(sweep_result, indent=2, ensure_ascii=False), encoding="utf-8")

    artifacts: List[Dict[str, Any]] = []

    def _register(path: Path, kind: str, media_type: str | None = None) -> None:
        if not path.exists():
            return
        sha = _sha256(path)
        size = path.stat().st_size if path.exists() else 0
        db.register_artifact_v1(
            job_id=job_id,
            z_context="Z0_TheConstruct",
            kind=kind,
            name=path.name,
            path=str(path),
            sha256=sha,
            size_bytes=size,
            media_type=media_type,
        )
        artifacts.append(
            {
                "kind": kind,
                "path": str(path),
                "sha256": sha,
                "size_bytes": size,
                "name": path.name,
                "media_type": media_type,
            }
        )

    _register(result_path, "result", "application/json")

    manifest_path = db.finalize_job_v1(
        job_id=job_id,
        status="completed",
        z_context="Z0_TheConstruct",
        outputs=artifacts,
        timings={},
        result={"rows": len(grid)},
        error=None,
    )

    manifest_fields = {
        "job_id": job_id,
        "tool_key": TOOL_KEY,
        "status": "completed",
        "run_dir": str(out_dir),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "rows": len(grid),
    }
    return artifacts, manifest_fields


if __name__ == "__main__":
    arts, manifest = run(
        {"material": "Cu", "frequencies_mhz": [1, 2, 5], "field_strength_tesla": [0.1, 0.2], "tags": ["baseline", "demo"]}
    )
    print(json.dumps({"artifacts": arts, "manifest": manifest}, indent=2))
