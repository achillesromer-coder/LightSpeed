from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "run_ls_go_bridge.py"
SPEC = importlib.util.spec_from_file_location("lightspeed_run_ls_go_bridge", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
resolve_runtime_layout = MODULE.resolve_runtime_layout


def test_import_is_side_effect_free() -> None:
    script = f"""
import importlib.util
import json
import os
import sys
path = {str(MODULE_PATH)!r}
before = {{key: os.environ.get(key) for key in (
    'LIGHTSPEED_CANONICAL_ROOT',
    'LIGHTSPEED_RUNTIME_ROOT',
    'LIGHTSPEED_SHELL_ROOT',
)}}
before_path = list(sys.path)
spec = importlib.util.spec_from_file_location('bridge_layout_probe', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
after = {{key: os.environ.get(key) for key in before}}
print(json.dumps({{
    'environment_unchanged': before == after,
    'path_unchanged': before_path == sys.path,
    'runtime_bound': 'lightspeed_runtime' in sys.modules,
}}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    result = __import__("json").loads(completed.stdout)

    assert result == {
        "environment_unchanged": True,
        "path_unchanged": True,
        "runtime_bound": False,
    }


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
