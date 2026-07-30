from __future__ import annotations

from pathlib import Path

import launcher_exe
from launcher_exe import build_launch_command, resolve_canonical_root


def test_resolve_canonical_root_uses_executable_parent_when_frozen(tmp_path: Path) -> None:
    executable = tmp_path / "LightSpeed.exe"

    assert resolve_canonical_root(executable=executable, frozen=True) == tmp_path


def test_build_launch_command_prefers_windowless_canonical_python(tmp_path: Path) -> None:
    pythonw = tmp_path / "venv" / "Scripts" / "pythonw.exe"
    entrypoint = tmp_path / "Desktop_Hooks" / "LightSpeed" / "__main__.py"
    pythonw.parent.mkdir(parents=True)
    entrypoint.parent.mkdir(parents=True)
    pythonw.touch()
    entrypoint.touch()

    command, working_directory = build_launch_command(tmp_path)

    assert command == [str(pythonw), str(entrypoint)]
    assert working_directory == entrypoint.parent


def test_canonical_operator_namespace_uses_app_and_environment(
    tmp_path: Path,
    monkeypatch,
) -> None:
    entrypoint = tmp_path / "App" / "__main__.py"
    python = tmp_path / "Environment" / "Scripts" / "python.exe"
    entrypoint.parent.mkdir(parents=True)
    python.parent.mkdir(parents=True)
    entrypoint.touch()
    python.touch()
    monkeypatch.setenv("LIGHTSPEED_CANONICAL_ROOT", str(tmp_path))

    root = resolve_canonical_root()
    command, working_directory = build_launch_command(root)

    assert root == tmp_path.absolute()
    assert command == [str(python), str(entrypoint)]
    assert working_directory == entrypoint.parent
