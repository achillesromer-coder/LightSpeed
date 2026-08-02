from __future__ import annotations

import importlib.util
import itertools
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Z Axis" / "TheConstruct.py"


def _load_construct_module():
    module_name = f"lightspeed_construct_gate_{abs(hash(str(SOURCE)))}"
    spec = importlib.util.spec_from_file_location(module_name, SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


CONSTRUCT = _load_construct_module()


def test_heavy_gate_requires_all_three_explicit_booleans() -> None:
    for operator_requested, owner_approved, resource_approved in itertools.product((False, True), repeat=3):
        gate = CONSTRUCT.evaluate_construct_heavy_gate(
            operator_requested=operator_requested,
            owner_approved=owner_approved,
            resource_approved=resource_approved,
        )
        assert gate["allowed"] is (operator_requested and owner_approved and resource_approved)

    assert CONSTRUCT.evaluate_construct_heavy_gate(
        operator_requested="true",
        owner_approved=True,
        resource_approved=True,
    )["allowed"] is False


def test_denied_immersive_request_never_loads_the_engine(monkeypatch) -> None:
    ui = object.__new__(CONSTRUCT.TheConstructUI)
    ui.state = CONSTRUCT.TheConstructFloorState()
    ui._construct_owner_approved = False
    ui._construct_resource_approved = True
    ui.winfo_toplevel = lambda: None

    monkeypatch.setattr(CONSTRUCT.messagebox, "showwarning", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        CONSTRUCT,
        "_load_symbol",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("immersive engine was loaded")),
    )

    assert ui._launch_3d_immersive(operator_requested=True) is False
    assert ui.state.immersive_active is False


def test_approved_immersive_request_uses_one_bounded_launch_callback(monkeypatch) -> None:
    ui = object.__new__(CONSTRUCT.TheConstructUI)
    ui.state = CONSTRUCT.TheConstructFloorState()
    ui._construct_owner_approved = True
    ui._construct_resource_approved = True
    ui.winfo_toplevel = lambda: "test-parent"
    launches = []

    def fake_loader(_path: str, symbol: str):
        assert symbol == "launch_immersive_3d_environment"
        return lambda *, parent: launches.append(parent)

    monkeypatch.setattr(CONSTRUCT, "_load_symbol", fake_loader)

    assert ui._launch_3d_immersive(operator_requested=True) is True
    assert launches == ["test-parent"]
    assert ui.state.immersive_active is True


def test_floor_boot_advertises_thin_and_held_capabilities_without_heavy_imports(monkeypatch) -> None:
    published = []

    class FakeEventBus:
        def publish(self, topic, payload):
            published.append((topic, payload))

        def subscribe(self, *_args, **_kwargs):
            return None

    event_bus = FakeEventBus()
    core_module = types.ModuleType("core")
    core_module.__path__ = []
    services_module = types.ModuleType("core.services")
    services_module.get_db = lambda: object()
    services_module.get_event_bus = lambda: event_bus
    services_module.get_storage = lambda: object()
    services_module.get_logger = lambda: None
    services_module.get_physics_tools = lambda: (_ for _ in ()).throw(AssertionError("physics tools were loaded"))
    core_module.services = services_module
    monkeypatch.setitem(sys.modules, "core", core_module)
    monkeypatch.setitem(sys.modules, "core.services", services_module)

    def fake_symbol(_path: str, symbol: str):
        if symbol == "load_construct_runtime_profile":
            return lambda: {"default_surface": "thin_preview_only"}
        if symbol == "load_virtual_space_test_matrix":
            return lambda: {"virtual_space_tests": {"smoke_lanes": []}}
        raise AssertionError(f"unexpected source load: {symbol}")

    monkeypatch.setattr(CONSTRUCT, "_load_symbol", fake_symbol)
    CONSTRUCT._THECONSTRUCT_INITIALIZED = False
    CONSTRUCT.THECONSTRUCT_RUNTIME = {}

    assert CONSTRUCT.initialize() is True
    assert CONSTRUCT.THECONSTRUCT_RUNTIME["physics_status"] == "held_by_three_condition_gate"
    assert CONSTRUCT.THECONSTRUCT_RUNTIME["visualization_status"] == "held_by_three_condition_gate"
    ready = next(payload for topic, payload in published if topic == "theconstruct.floor.ready")
    assert ready["capabilities"] == list(CONSTRUCT.CONSTRUCT_THIN_CAPABILITIES)
    assert ready["held_capabilities"] == list(CONSTRUCT.CONSTRUCT_HELD_CAPABILITIES)
    assert ready["heavy_gate"]["allowed"] is False
