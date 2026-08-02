from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "run_ls_go_bridge.py"
SPEC = importlib.util.spec_from_file_location("lightspeed_run_ls_go_bridge", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
resolve_runtime_layout = MODULE.resolve_runtime_layout


def test_resolve_runtime_layout_uses_source_checkout_by_default(tmp_path: Path) -> None:
    canonical, desktop, runtime = resolve_runtime_layout(tmp_path, {})

    assert canonical == tmp_path
    assert desktop == tmp_path / "desktop" / "Desktop_Hooks" / "LightSpeed"
    assert runtime == tmp_path / "desktop" / "LightSpeed_Runtime"


def test_resolve_runtime_layout_detects_installed_namespace(tmp_path: Path) -> None:
    (tmp_path / "App").mkdir()
    (tmp_path / "Core").mkdir()

    canonical, desktop, runtime = resolve_runtime_layout(tmp_path, {})

    assert canonical == tmp_path
    assert desktop == tmp_path / "App"
    assert runtime == tmp_path / "Core"


def test_resolve_runtime_layout_honours_explicit_canonical_root(tmp_path: Path) -> None:
    configured = tmp_path / "configured"

    canonical, desktop, runtime = resolve_runtime_layout(
        tmp_path,
        {"LIGHTSPEED_CANONICAL_ROOT": str(configured)},
    )

    assert canonical == configured
    assert desktop == configured / "App"
    assert runtime == configured / "Core"


def test_bridge_status_preserves_the_operator_namespace() -> None:
    source = (
        MODULE_PATH.parents[1]
        / "desktop"
        / "LightSpeed_Runtime"
        / "lightspeed_runtime"
        / "ls_go_bridge.py"
    ).read_text(encoding="utf-8")

    assert "shell_root = Path(root).absolute()" in source
    assert "shell_root = Path(root).resolve()" not in source
