from __future__ import annotations

from pathlib import Path

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
