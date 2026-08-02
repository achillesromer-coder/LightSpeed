from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "config"
CONSTRUCT_ROOT = ROOT / "Z Axis" / "Z0_TheConstruct"


def _load_config(relative_path: str) -> dict:
    return json.loads((CONFIG_ROOT / relative_path).read_text(encoding="utf-8"))


def test_source_bundle_contains_the_public_operating_contracts() -> None:
    expected = {
        "host_runtime_policy.json",
        "project_routing.json",
        "resource_closure_contract.json",
        "workspace_lanes.json",
        "operator_approval_manifest.json",
    }
    assert expected <= {path.name for path in CONFIG_ROOT.glob("*.json")}


def test_operator_namespace_and_model_storage_are_explicit() -> None:
    storage = _load_config("host_runtime_policy.json")["storage_topology"]
    assert storage["workspace_root"] == "D:\\LightSpeed"
    assert storage["workspace_root_type"] == "canonical_d_drive_namespace"
    assert storage["ollama_model_root"] == "D:\\LightSpeed\\Models"


def test_half_speed_profile_preserves_host_headroom() -> None:
    limits = _load_config("host_runtime_policy.json")["runtime_limits"]
    assert limits["active_operating_profile"] == "cognigrex_half_speed"
    assert limits["cognigrex_speed_percent"] == 50
    assert limits["max_background_queue_workers"] == 1
    assert limits["max_concurrent_ollama_jobs"] == 1
    assert limits["max_active_heavy_floors"] == 1


def test_project_routing_reuses_one_shell_and_one_review_chain() -> None:
    routing = _load_config("project_routing.json")
    assert routing["project_roots"][0]["authority"] == "canonical"
    assert routing["project_roots"][1]["authority"] == "legacy_reference"
    assert routing["go_review"]["require_owner_gate"] is True
    assert routing["drive_writeback"]["workbooks_mutable"] is False
    assert routing["cleanup_policy"]["automatic_deletion"] is False
    assert routing["resource_guard"]["volume_paths"] == ["D:\\LightSpeed", "C:\\"]


def test_release_and_heavy_work_remain_bounded() -> None:
    routing = _load_config("project_routing.json")
    closure = _load_config("resource_closure_contract.json")
    assert routing["release_boundary"]["public_publish"] is False
    assert routing["release_boundary"]["direct_cross_app_execution"] is False
    assert routing["release_boundary"]["destructive_cleanup"] is False
    assert closure["execution_policy"]["heavy_floors_manual_gated"] is True


def test_workspace_contract_uses_one_compact_operator_surface() -> None:
    workspace = _load_config("workspace_lanes.json")
    assert workspace["interface_mode"] == "single_surface_bento_shell"
    assert workspace["primary_surface"] == "Trinity"
    assert workspace["chrome_safe_mode"] is True
    assert "duplicate_portals" in workspace["avoid_patterns"]
    assert "unbounded_background_actions" in workspace["avoid_patterns"]



def test_construct_defaults_to_thin_preview_and_holds_heavy_execution() -> None:
    manifest = json.loads((CONSTRUCT_ROOT / "_FLOOR_MANIFEST.json").read_text(encoding="utf-8"))
    construct = json.loads((CONSTRUCT_ROOT / "z0_config.json").read_text(encoding="utf-8"))
    startup = json.loads((CONSTRUCT_ROOT / "Config" / "startup.json").read_text(encoding="utf-8"))
    registry = json.loads((CONSTRUCT_ROOT / "Config" / "service_registry.json").read_text(encoding="utf-8"))
    flows = json.loads((CONSTRUCT_ROOT / "Config" / "data_flows.json").read_text(encoding="utf-8"))

    assert manifest["smart_floor"] == {
        "auto_expand": False,
        "ai_suggestions": False,
        "default_execution_mode": "thin_preview_only",
        "heavy_execution": "manual_owner_and_resource_gated",
        "representation_edge_enabled": False,
    }

    construct_startup = construct["startup"]
    assert construct_startup["auto_launch"] is False
    assert construct_startup["execution_profile"] == "cognigrex_half_speed"
    assert construct_startup["speed_percent"] == 50
    assert construct_startup["thin_preview_default"] is True
    assert construct_startup["max_concurrent_heavy_jobs"] == 1
    assert construct_startup["heavy_services_auto_launch"] is False
    assert construct_startup["representation_edge_enabled"] is False

    assert startup["sequence"] == ["database", "logger", "storage", "event_bus"]
    assert startup["parallel_groups"] == [["database", "event_bus", "logger", "storage"]]
    assert startup["execution_policy"] == {
        "profile": "cognigrex_half_speed",
        "speed_percent": 50,
        "default_mode": "thin_preview_only",
        "manual_heavy_auto_start": False,
        "max_concurrent_heavy_jobs": 1,
        "representation_edge_enabled": False,
    }

    held_services = {
        "mark3_simulator",
        "raphael_equations",
        "orbital_mechanics",
        "quantum_mechanics",
        "big_bang_simulation",
        "hybrid_renderer",
        "sphere_primitive",
        "ast_analyzer",
        "indexer",
        "dependencies",
        "cognigrex_models",
        "cognigrex_training",
        "cognigrex_fleet",
        "immersive_engine",
    }
    assert held_services <= set(startup["manual_services"])
    assert all(registry[name]["enabled"] is False for name in held_services)
    assert registry["mark3_simulator"]["status"] == "blocked_input"
    assert registry["raphael_equations"]["status"] == "evidence_hold"
    assert registry["TheConstruct"]["enabled"] is True
    assert registry["TheConstruct"]["status"] == "operational"
    assert flows
    assert all(flow["enabled"] is False for flow in flows)
    assert all(flow["activation"] for flow in flows)
