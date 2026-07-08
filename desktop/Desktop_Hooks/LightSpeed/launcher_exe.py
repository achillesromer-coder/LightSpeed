from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def resolve_canonical_root(
    *,
    executable: Path | None = None,
    frozen: bool | None = None,
) -> Path:
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if is_frozen:
        return Path(executable or sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def build_launch_command(root: Path) -> tuple[list[str], Path]:
    root = Path(root).resolve()
    shell_root = root / "Desktop_Hooks" / "LightSpeed"
    entrypoint = shell_root / "__main__.py"
    python_candidates = (
        root / "venv" / "Scripts" / "python.exe",
        root / "venv" / "Scripts" / "pythonw.exe",
    )
    python = next((candidate for candidate in python_candidates if candidate.is_file()), None)

    if python is None:
        raise FileNotFoundError(f"LightSpeed Python runtime not found under {root / 'venv'}")
    if not entrypoint.is_file():
        raise FileNotFoundError(f"LightSpeed entrypoint not found: {entrypoint}")
    return [str(python), str(entrypoint)], shell_root


def launch() -> int:
    root = resolve_canonical_root()
    command, working_directory = build_launch_command(root)
    environment = os.environ.copy()
    environment["LIGHTSPEED_CANONICAL_ROOT"] = str(root)
    environment["LIGHTSPEED_RUNTIME_RESOLVED"] = "1"
    environment.setdefault("LIGHTSPEED_PYTHON", command[0])
    venv_root = root / "venv"
    if venv_root.exists():
        environment["VIRTUAL_ENV"] = str(venv_root)
        environment["PATH"] = f"{venv_root / 'Scripts'}{os.pathsep}{environment.get('PATH', '')}"
    creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    creation_flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        command,
        cwd=working_directory,
        env=environment,
        creationflags=creation_flags,
        close_fds=True,
    )
    return process.pid


def _show_launch_error(message: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "LightSpeed launch failed", 0x10)
    except Exception:
        print(message, file=sys.stderr)


if __name__ == "__main__":
    try:
        launch()
    except Exception as exc:
        _show_launch_error(str(exc))
        raise SystemExit(1)
