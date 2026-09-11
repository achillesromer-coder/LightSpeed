from __future__ import annotations

import ast
import importlib.util
import sys
import types
from pathlib import Path

import pytest


LIGHTSPEED_ROOT = Path(__file__).resolve().parents[1]
CONSTRUCT_ENTRYPOINT = LIGHTSPEED_ROOT / "Z Axis" / "TheConstruct.py"
SIMULATION_LAUNCHER = (
    LIGHTSPEED_ROOT
    / "Z Axis"
    / "Z+3_Trinity"
    / "ui"
    / "components"
    / "simulation_launcher.py"
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_simulation_launcher(monkeypatch: pytest.MonkeyPatch):
    package_name = "lightspeed_simulation_launcher_contract"
    package = types.ModuleType(package_name)
    package.__path__ = []
    monkeypatch.setitem(sys.modules, package_name, package)

    layered = types.ModuleType(f"{package_name}.layered_card")
    layered.LayeredCard = type("LayeredCard", (), {})
    loading = types.ModuleType(f"{package_name}.loading")
    loading.ProgressBar = type("ProgressBar", (), {})
    loading.LoadingSpinner = type("LoadingSpinner", (), {})
    charts = types.ModuleType(f"{package_name}.charts")
    charts.ChartCard = type("ChartCard", (), {})
    monkeypatch.setitem(sys.modules, layered.__name__, layered)
    monkeypatch.setitem(sys.modules, loading.__name__, loading)
    monkeypatch.setitem(sys.modules, charts.__name__, charts)

    return _load_module(SIMULATION_LAUNCHER, f"{package_name}.simulation_launcher")


def test_n_dispatches_through_the_canonical_construct_entrypoint() -> None:
    n_source = (LIGHTSPEED_ROOT / "N.py").read_text(encoding="utf-8-sig")
    n_module = ast.parse(n_source)
    methods = [
        node
        for node in ast.walk(n_module)
        if isinstance(node, ast.FunctionDef) and node.name == "run_simulation"
    ]

    assert len(methods) == 1
    source = ast.get_source_segment(n_source, methods[0]) or ""
    assert '/ "Z Axis" / "TheConstruct.py"' in source
    assert '"Z0_TheConstruct" / "TheConstruct.py"' not in source
    assert "physics_tools" not in source
    assert not any(isinstance(node, ast.Try) for node in ast.walk(methods[0]))


def test_construct_gate_requires_three_literal_true_values() -> None:
    construct = _load_module(CONSTRUCT_ENTRYPOINT, "lightspeed_construct_gate_contract")

    assert construct.CONSTRUCT_THIN_CAPABILITIES == (
        "dashboard_readback",
        "registry_readback",
        "runtime_profile_readback",
        "scenario_descriptors",
        "bounded_calculator_registry",
    )
    assert "physics_simulations" in construct.CONSTRUCT_HELD_CAPABILITIES
    assert "big_bang" in construct.CONSTRUCT_HELD_CAPABILITIES
    assert not construct.evaluate_construct_heavy_gate()["allowed"]
    assert not construct.evaluate_construct_heavy_gate(
        operator_requested="True",
        owner_approved="True",
        resource_approved="True",
    )["allowed"]
    assert construct.evaluate_construct_heavy_gate(
        operator_requested=True,
        owner_approved=True,
        resource_approved=True,
    )["allowed"]


def test_construct_dispatch_denies_before_importing_physics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    physics_tools = types.ModuleType("core.services.physics_tools")
    physics_tools.calculate_raphael_equations = (
        lambda **params: calls.append(("raphael", params)) or {"kind": "raphael"}
    )
    physics_tools.generate_big_bang_simulation = (
        lambda **params: calls.append(("bigbang", params)) or {"kind": "bigbang"}
    )
    monkeypatch.setitem(sys.modules, "core", types.ModuleType("core"))
    monkeypatch.setitem(sys.modules, "core.services", types.ModuleType("core.services"))
    monkeypatch.setitem(sys.modules, "core.services.physics_tools", physics_tools)
    construct = _load_module(CONSTRUCT_ENTRYPOINT, "lightspeed_construct_dispatch_contract")

    denied_approvals = (
        {},
        {
            "operator_requested": True,
            "owner_approved": True,
        },
        {
            "operator_requested": "True",
            "owner_approved": "True",
            "resource_approved": "True",
        },
    )
    for approvals in denied_approvals:
        with pytest.raises(PermissionError, match="remains held"):
            construct.run_simulation("raphael", protons=1, **approvals)
    assert calls == []

    approvals = {
        "operator_requested": True,
        "owner_approved": True,
        "resource_approved": True,
    }
    assert construct.run_simulation(" RAPHAEL ", protons=1, **approvals) == {"kind": "raphael"}
    assert construct.run_simulation("bigbang", time_steps=2, **approvals) == {"kind": "bigbang"}
    assert calls == [
        ("raphael", {"protons": 1}),
        ("bigbang", {"time_steps": 2}),
    ]
    with pytest.raises(ValueError, match="Unknown simulation type"):
        construct.run_simulation("unregistered", **approvals)
    assert len(calls) == 2


def test_launcher_parameter_parser_is_literal_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    launcher = _load_simulation_launcher(monkeypatch)

    assert launcher.parse_parameter_value("42") == 42
    assert launcher.parse_parameter_value("1e-3") == pytest.approx(0.001)
    assert launcher.parse_parameter_value("[1, 2, (3, 4)]") == [1, 2, (3, 4)]
    assert launcher.parse_parameter_value('{"scale": 0.5}') == {"scale": 0.5}
    assert launcher.parse_parameter_value("unquoted label") == "unquoted label"

    marker = tmp_path / "must_not_exist.txt"
    payload = f"[__import__('pathlib').Path({str(marker)!r}).write_text('owned')]"
    assert launcher.parse_parameter_value(payload) == payload
    assert not marker.exists()

    tree = ast.parse(SIMULATION_LAUNCHER.read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "eval"
        for node in ast.walk(tree)
    )
