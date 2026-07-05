from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import time


LIGHTSPEED_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    LIGHTSPEED_ROOT
    / "Z Axis"
    / "Z0_TheConstruct"
    / "ui"
    / "cognigrex_3d_environment.py"
)


def _load_module():
    module_name = "lightspeed_test_cognigrex_3d_environment"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_passive_renderer_uses_bounded_low_power_interval() -> None:
    module = _load_module()
    scheduled: list[int] = []

    class Parent:
        def after(self, interval_ms: int, callback) -> None:
            del callback
            scheduled.append(interval_ms)

    class Background:
        def update(self, delta_seconds: float) -> None:
            assert delta_seconds >= 0

    environment = module.Cognigrex3DEnvironment.__new__(
        module.Cognigrex3DEnvironment
    )
    environment.running = True
    environment.last_time = time.time()
    environment.background = Background()
    environment.parent = Parent()
    environment.frame_interval_ms = module.PASSIVE_FRAME_INTERVAL_MS
    environment._render = lambda: None

    environment._render_loop()

    assert scheduled == [250]


def test_launch_modes_select_active_and_passive_render_policies(monkeypatch) -> None:
    module = _load_module()
    captured: list[int] = []

    def fake_environment(
        parent,
        canvas=None,
        on_floor_select=None,
        *,
        frame_interval_ms: int,
    ):
        del parent, canvas, on_floor_select
        captured.append(frame_interval_ms)
        return object()

    monkeypatch.setattr(module, "Cognigrex3DEnvironment", fake_environment)
    parent = object()
    canvas = object()

    module.attach_cognigrex_3d(parent, canvas)
    module.launch_cognigrex_3d(parent=parent)

    assert captured == [
        module.PASSIVE_FRAME_INTERVAL_MS,
        module.ACTIVE_FRAME_INTERVAL_MS,
    ]
