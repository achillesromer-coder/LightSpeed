#!/usr/bin/env python
"""
GMAT runner (real execution; V1 job ledger + immutable dataspace)

Implements the LightSpeed V1 rule-set:
- Everything is a Job (jobs table)
- Every job produces a manifest.json
- Artifacts are immutable (new job => new folder in `LightSpeed/w6/data/<tool_key>/...`)

This runner:
- Writes a GMAT script into the job run dir
- Executes `GmatConsole.exe` (bundled under TheConstruct)
- Captures stdout/stderr + GMAT log + result.json
- Registers artifacts in DB and finalizes the job manifest

Payload example:
{
  "scenario_name": "AsteroidSampleReturn",
  "script_text": "GMAT SCRIPT HERE...",
  "script_path": "optional/path/to/script.gmat",
  "tags": ["gmat", "mission"],
  "task_id": 123,        # optional
  "project_id": 456,     # optional
  "timeout_s": 900       # optional
}
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# LightSpeed root (two levels above Z Axis)
ROOT = Path(__file__).resolve().parents[3]
TOOL_KEY = "gmat.run"

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

    scenario = (payload.get("scenario_name") or "UnnamedScenario").strip() or "UnnamedScenario"
    script_text = payload.get("script_text")
    script_path = payload.get("script_path")
    tags = payload.get("tags") or []
    timeout_s = int(payload.get("timeout_s") or 900)

    job = db.create_job_v1(
        job_type="gmat_run",
        tool_key=TOOL_KEY,
        z_context="Z0_TheConstruct",
        params={
            "scenario_name": scenario,
            "script_path": script_path,
            "script_text_present": bool(script_text),
            "timeout_s": timeout_s,
        },
        task_id=payload.get("task_id"),
        project_id=payload.get("project_id"),
        tags=tags,
        inputs=[],
    )
    job_id = int(job["job_id"])
    out_dir = Path(output_dir) if output_dir is not None else Path(job["run_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Script materialization.
    script_out = out_dir / f"{scenario}.gmat"
    if script_text:
        script_out.write_text(str(script_text), encoding="utf-8")
    elif script_path and Path(str(script_path)).exists():
        shutil.copy2(Path(str(script_path)), script_out)
    else:
        script_out.write_text("# Empty GMAT script (no script_text/script_path provided)\n", encoding="utf-8")

    # GMAT console bundled under TheConstruct.
    gmat_exe = (
        ROOT
        / "Z Axis"
        / "Z0_TheConstruct"
        / "tools"
        / "GMAT"
        / "GMAT_R2025a"
        / "bin"
        / "GmatConsole.exe"
    ).resolve()

    stdout_path = out_dir / "stdout.txt"
    stderr_path = out_dir / "stderr.txt"
    gmat_log_path = out_dir / "gmat.log"
    run_path = out_dir / "run.json"

    started = time.time()
    status = "failed"
    exit_code: int | None = None
    error_text: str | None = None

    if not gmat_exe.exists():
        error_text = f"GMAT console not found at: {gmat_exe}"
    else:
        cmd = [str(gmat_exe), "-r", str(script_out), "-l", str(gmat_log_path)]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(out_dir),
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            exit_code = int(proc.returncode)
            stdout_path.write_text(proc.stdout or "", encoding="utf-8", errors="replace")
            stderr_path.write_text(proc.stderr or "", encoding="utf-8", errors="replace")
            status = "completed" if exit_code == 0 else "failed"
            if exit_code != 0:
                error_text = f"GMAT exited with code {exit_code}"
        except subprocess.TimeoutExpired as e:
            stdout_path.write_text(getattr(e, "stdout", "") or "", encoding="utf-8", errors="replace")
            stderr_path.write_text(getattr(e, "stderr", "") or "", encoding="utf-8", errors="replace")
            status = "failed"
            error_text = f"GMAT timed out after {timeout_s}s"
        except Exception as e:
            status = "failed"
            error_text = str(e)

    finished = time.time()
    run_info = {
        "status": status,
        "tool_key": TOOL_KEY,
        "job_id": job_id,
        "scenario": scenario,
        "duration_s": round(finished - started, 3),
        "timeout_s": timeout_s,
        "exit_code": exit_code,
        "cmd": {
            "exe": str(gmat_exe),
            "args": ["-r", str(script_out), "-l", str(gmat_log_path)],
        },
        "error": error_text,
        "completed_at_utc": datetime.utcnow().isoformat() + "Z",
    }
    run_path.write_text(json.dumps(run_info, indent=2, ensure_ascii=False), encoding="utf-8")

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

    _register(script_out, "input_script", "text/plain")
    _register(gmat_log_path, "log", "text/plain")
    _register(stdout_path, "stdout", "text/plain")
    _register(stderr_path, "stderr", "text/plain")
    _register(run_path, "result", "application/json")

    # Capture any extra files produced by GMAT.
    try:
        known = {p["name"] for p in artifacts if p.get("name")}
        known |= {"manifest.json", "manifest.final.json"}
        for p in sorted(out_dir.glob("*")):
            if not p.is_file():
                continue
            if p.name in known:
                continue
            _register(p, "output", None)
    except Exception:
        pass

    manifest_path = db.finalize_job_v1(
        job_id=job_id,
        status=status,
        z_context="Z0_TheConstruct",
        outputs=artifacts,
        timings={"duration_s": round(finished - started, 3), "timeout_s": timeout_s},
        result={"exit_code": exit_code, "scenario": scenario},
        error=error_text,
    )

    manifest_fields = {
        "job_id": job_id,
        "tool_key": TOOL_KEY,
        "status": status,
        "run_dir": str(out_dir),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "exit_code": exit_code,
    }
    return artifacts, manifest_fields


if __name__ == "__main__":
    payload = {"scenario_name": "demo"}
    payload_path = None
    if len(sys.argv) > 1:
        payload_path = Path(sys.argv[1])
    if payload_path and payload_path.exists():
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    arts, manifest = run(payload)
    print(json.dumps({"artifacts": arts, "manifest": manifest}, indent=2))
