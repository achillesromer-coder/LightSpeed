from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


LIGHTSPEED_ROOT = Path(__file__).resolve().parents[1]
SHELL_ROUTES_PATH = (
    LIGHTSPEED_ROOT
    / "Z Axis"
    / "Z+3_Trinity"
    / "ui"
    / "shell_routes.py"
)


def _load_shell_routes():
    spec = importlib.util.spec_from_file_location(
        "lightspeed_shell_routes_test",
        SHELL_ROUTES_PATH,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_shell_has_one_mode_floor_context_tuple():
    module = _load_shell_routes()
    state = module.ShellState()

    state.transition(
        mode="operator",
        active_floor="Oracle",
        workspace_context="P-17",
    )

    assert state.snapshot() == {
        "mode": "operator",
        "active_floor": "Oracle",
        "workspace_context": "P-17",
    }


def test_shell_modes_are_bounded_and_holospace_is_explicit():
    module = _load_shell_routes()
    router = module.ShellRouter(clearance=5)

    assert module.SHELL_MODES == (
        "workspace",
        "operator",
        "review",
        "publish",
        "settings",
        "holospace",
    )
    assert router.default_route().mode == "workspace"
    assert router.resolve("holospace").mode == "holospace"


def test_shell_router_normalizes_floor_channels_and_enforces_clearance():
    module = _load_shell_routes()

    route = module.ShellRouter(clearance=5).resolve(
        "operator",
        active_floor="Z-2",
        workspace_context="ROMER",
    )
    assert route.active_floor == "Oracle"
    assert route.workspace_context == "ROMER"

    with pytest.raises(PermissionError):
        module.ShellRouter(clearance=2).resolve("publish")


def test_shell_state_rejects_unknown_mode_and_floor():
    module = _load_shell_routes()
    state = module.ShellState()

    with pytest.raises(ValueError, match="mode"):
        state.transition(
            mode="tabs",
            active_floor="Trinity",
            workspace_context="",
        )
    with pytest.raises(ValueError, match="floor"):
        state.transition(
            mode="operator",
            active_floor="Unknown",
            workspace_context="",
        )
