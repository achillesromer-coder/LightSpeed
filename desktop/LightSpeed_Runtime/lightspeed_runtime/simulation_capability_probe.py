from __future__ import annotations

"""Read-only environment probes for GMAT, FEMM and MPL capability state.

These probes report what is actually bound on BouwerBase. They do not run a
simulation, install software, or upgrade evidence state.
"""

import json
import os
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
GMAT_RUNNER = (
    REPO_ROOT
    / "desktop"
    / "Desktop_Hooks"
    / "LightSpeed"
    / "Z Axis"
    / "Z-3_Smith"
    / "tools"
    / "gmat_runner.py"
)
GMAT_EXPECTED = (
    REPO_ROOT
    / "desktop"
    / "Desktop_Hooks"
    / "LightSpeed"
    / "Z Axis"
    / "Z0_TheConstruct"
    / "tools"
    / "GMAT"
    / "GMAT_R2025a"
    / "bin"
    / "GmatConsole.exe"
)
MPL_ADAPTER = REPO_ROOT / "cgx" / "domain_templates" / "mpl_assurance_adapter.json"
MPL_ROOT = REPO_ROOT / "MPL"


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        try:
            if path.exists() and path.is_file():
                return path.resolve()
        except OSError:
            continue
    return None


def probe_gmat() -> dict[str, Any]:
    override = os.environ.get("GMAT_CONSOLE")
    candidates = [
        Path(override) if override else GMAT_EXPECTED,
        Path(r"C:\Program Files\GMAT\R2025a\bin\GmatConsole.exe"),
        Path(r"C:\Program Files\GMAT\R2024a\bin\GmatConsole.exe"),
        Path(r"C:\GMAT\GMAT_R2025a\bin\GmatConsole.exe"),
        Path.home() / "GMAT" / "bin" / "GmatConsole.exe",
    ]
    executable = _first_existing(candidates)
    return {
        "schema": "LIGHTSPEED-GMAT-PROBE/0.1",
        "runner_present": GMAT_RUNNER.exists(),
        "expected_executable": str(GMAT_EXPECTED),
        "executable_found": executable is not None,
        "executable": str(executable) if executable else None,
        "state": "available" if executable else "prepared_not_activated",
        "execution_exposed": False,
        "result_authority": "simulation_result_only",
        "boundary": (
            "GMAT execution is not exposed unless a verified GmatConsole executable "
            "and typed corpus packet are both present. Python fallback/simulation-mode "
            "results must not be represented as GMAT execution."
        ),
    }
def probe_femm() -> dict[str, Any]:
    override = os.environ.get("FEMM_EXE")
    candidates = [
        Path(override) if override else Path(r"C:\femm42\bin\femm.exe"),
        Path(r"C:\Program Files\femm42\bin\femm.exe"),
        Path(r"C:\Program Files (x86)\femm42\bin\femm.exe"),
        Path.home() / "Desktop" / "Programs" / "femm42" / "bin" / "femm.exe",
    ]
    executable = _first_existing(candidates)
    return {
        "schema": "LIGHTSPEED-FEMM-PROBE/0.1",
        "executable_found": executable is not None,
        "executable": str(executable) if executable else None,
        "state": "registered_unavailable" if executable is None else "available_unwrapped",
        "solver_exposed": False,
        "boundary": (
            "No FEMM solve route is exposed until the executable/model contract is "
            "verified and a bounded typed adapter is implemented."
        ),
    }


def probe_mpl() -> dict[str, Any]:
    adapter: dict[str, Any] = {}
    if MPL_ADAPTER.exists():
        try:
            adapter = json.loads(MPL_ADAPTER.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            adapter = {}
    root_exists = False
    root_readable = False
    sample_entries: list[str] = []
    try:
        root_exists = MPL_ROOT.exists() and MPL_ROOT.is_dir()
        if root_exists:
            sample_entries = sorted(item.name for item in MPL_ROOT.iterdir())[:20]
            root_readable = True
    except OSError:
        root_exists = True
        root_readable = False
    boundary = adapter.get("current_known_boundary") if isinstance(adapter, dict) else None
    return {
        "schema": "LIGHTSPEED-MPL-PROBE/0.1",
        "adapter_present": MPL_ADAPTER.exists(),
        "local_root": str(MPL_ROOT),
        "local_root_exists": root_exists,
        "local_root_readable": root_readable,
        "sample_entries": sample_entries,
        "repo_stage": (boundary or {}).get("repo_stage") if isinstance(boundary, dict) else None,
        "application_ready": (boundary or {}).get("application_ready") if isinstance(boundary, dict) else None,
        "state": "prepared_not_activated",
        "execution_exposed": False,
        "result_authority": "bounded_screening_only",
        "boundary": (
            "MPL remains bounded financial/insurance consequence screening. "
            "It does not satisfy FMEA/FMECA, hazard analysis, functional safety, "
            "assurance-case, or regulatory approval requirements."
        ),
    }


__all__ = ["probe_gmat", "probe_femm", "probe_mpl"]
