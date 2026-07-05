#!/usr/bin/env python
"""LightSpeed package entrypoint.

This file is intentionally small. The live desktop application is `N.py`; this
module only preserves `python -m LightSpeed` and legacy launcher flags while
preventing another parallel startup framework from drifting out of date.
"""

from __future__ import annotations

import os
import importlib
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

LIGHTSPEED_ROOT = Path(__file__).resolve().parent
CANONICAL_RUNTIME_ROOT = (LIGHTSPEED_ROOT.parent.parent / "LightSpeed_Runtime").resolve()
N_ENTRYPOINT = LIGHTSPEED_ROOT / "N.py"

if CANONICAL_RUNTIME_ROOT.exists():
    canonical_runtime_path = str(CANONICAL_RUNTIME_ROOT)
    while canonical_runtime_path in sys.path:
        sys.path.remove(canonical_runtime_path)
    sys.path.insert(0, canonical_runtime_path)

_PORTAL_ALIASES = {
    "--direct",
    "--gui",
    "--launcher",
    "--login-only",
    "--oracle",
    "--settings",
    "--setup",
    "--startup",
    "--trinity",
    "--2d",
}
_IMMERSIVE_ALIASES = {"--spatial", "--immersive"}
_VERIFY_ALIASES = {"--backend", "--diagnose", "--discover", "--init-floors", "--no-gui"}
_DROP_ALIASES = {"--n"}


def _launch_runtime_missing_modules() -> list[str]:
    try:
        from lightspeed_runtime.startup_options import LAUNCH_CORE_MODULES
    except Exception:
        return []

    missing: list[str] = []
    for module_name in LAUNCH_CORE_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception:
            missing.append(module_name)
    return missing


def _maybe_reexec_preferred_runtime(args: list[str]) -> int | None:
    if os.environ.get("LIGHTSPEED_RUNTIME_RESOLVED") == "1":
        return None

    current_executable = Path(sys.executable).resolve()
    workspace_venv_python = (LIGHTSPEED_ROOT.parent.parent / "venv" / "Scripts" / "python.exe").resolve()
    if current_executable == workspace_venv_python:
        return None

    missing_modules = _launch_runtime_missing_modules()
    if not missing_modules:
        return None

    try:
        from lightspeed_runtime.startup_options import launch_runtime_candidates
    except Exception:
        return None

    for candidate in launch_runtime_candidates(LIGHTSPEED_ROOT):
        candidate_path = Path(str(candidate.get("path") or "")).expanduser()
        try:
            if not candidate.get("exists") or candidate_path.resolve() == current_executable:
                continue
        except Exception:
            continue

        env = os.environ.copy()
        env["LIGHTSPEED_RUNTIME_RESOLVED"] = "1"
        env.setdefault("LIGHTSPEED_PYTHON", str(candidate_path))
        print(
            "[INFO] Launch runtime missing "
            f"{', '.join(missing_modules)} under {current_executable}. "
            f"Re-launching with {candidate_path}."
        )
        completed = subprocess.run([str(candidate_path), str(__file__), *args], env=env)
        return int(completed.returncode or 0)
    return None


def _read_version() -> str:
    try:
        return (LIGHTSPEED_ROOT / "VERSION").read_text(encoding="utf-8", errors="replace").strip() or "unknown"
    except Exception:
        return "unknown"


def _load_n_module():
    if not N_ENTRYPOINT.exists():
        raise FileNotFoundError(f"N.py not found at {N_ENTRYPOINT}")
    if str(LIGHTSPEED_ROOT) not in sys.path:
        sys.path.insert(0, str(LIGHTSPEED_ROOT))
    spec = spec_from_file_location("lightspeed_n_entrypoint", N_ENTRYPOINT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {N_ENTRYPOINT}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_legacy_args(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    for arg in argv:
        lowered = arg.lower()
        if lowered in _PORTAL_ALIASES:
            if "--portal" not in normalized:
                normalized.append("--portal")
            continue
        if lowered in _IMMERSIVE_ALIASES:
            if "--3d" not in normalized:
                normalized.append("--3d")
            continue
        if lowered in _VERIFY_ALIASES:
            if "--verify" not in normalized:
                normalized.append("--verify")
            continue
        if lowered in _DROP_ALIASES:
            continue
        normalized.append(arg)
    return normalized


def main(argv: list[str] | None = None) -> int:
    """Delegate to the canonical `N.py` shell."""
    args = _normalize_legacy_args(list(sys.argv[1:] if argv is None else argv))
    try:
        os.chdir(str(LIGHTSPEED_ROOT))
    except Exception:
        pass

    if "--version" in args:
        print(f"LightSpeed Unified Orchestrator v{_read_version()}")
        print("Primary Interface: N.py")
        print("Operator Surface: Neo orchestration / Achilles oversight")
        print("Governance Surface: Architect / Trinity")
        print("Holospace Surface: TheConstruct")
        return 0

    rerouted = _maybe_reexec_preferred_runtime(args)
    if rerouted is not None:
        return rerouted

    try:
        module = _load_n_module()
    except Exception as exc:
        print(f"[ERROR] Unable to load canonical shell: {exc}")
        return 1

    if not hasattr(module, "main"):
        print("[ERROR] N.py does not expose main()")
        return 1

    previous_argv = sys.argv[:]
    try:
        sys.argv = ["N.py", *args]
        result = module.main()
        return int(result or 0)
    except SystemExit as exc:
        try:
            return int(exc.code or 0)
        except Exception:
            return 1
    finally:
        sys.argv = previous_argv


if __name__ == "__main__":
    raise SystemExit(main())
