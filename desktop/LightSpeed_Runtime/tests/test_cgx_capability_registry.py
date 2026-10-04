from __future__ import annotations

from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.cgx_capability_registry import (
    CapabilityRegistryError,
    capability_summary,
    list_shortcalls,
    load_capability_routes,
    load_selector_shortcalls,
    normalize_shortcall,
    resolve_shortcall,
    selector_profile,
)


def test_registry_has_nine_selector_profiles_and_registered_routes():
    routes = load_capability_routes()
    selectors = load_selector_shortcalls()
    assert len(selectors["selectors"]) == 9
    assert len(routes["routes"]) >= 30


def test_shortcall_normalisation():
    assert normalize_shortcall("/SWEEP") == "sweep"
    assert normalize_shortcall("capabilities") == "capabilities"
def test_raphael_sweep_is_real_bounded_runtime_route():
    resolved = resolve_shortcall("@Raphael", "/sweep")
    assert resolved["route_id"] == "science.rfs_emff_sweep"
    assert resolved["route"]["state"] == "available"
    assert resolved["route"]["handler"].endswith(":execute_sweep")
    assert "freecad" in resolved["toolkits"]


def test_eco_shortcalls_are_explicitly_assisted_not_fake_runtime_tools():
    resolved = resolve_shortcall("Eco-Grex", "habitat")
    assert resolved["route_id"] == "eco.assess"
    assert resolved["route"]["state"] == "assisted"
    assert "deterministic ecology engine" in resolved["route"]["limitation"]


def test_freecad_readonly_available_and_femm_gap_visible():
    routes = load_capability_routes()["routes"]
    assert routes["cad.freecad"]["state"] == "available"
    assert routes["cad.freecad"]["ro"] is True
    assert routes["physics.femm"]["state"] == "missing"


def test_all_selectors_inherit_extension_shortcall():
    selectors = load_selector_shortcalls()["selectors"]
    for selector in selectors:
        assert list_shortcalls(selector)["extend"] == "extensions.tool"
def test_capability_summary_groups_states():
    summary = capability_summary("LightSpeed")
    assert summary["selector"] == "lightspeed"
    assert "available" in summary["by_state"]
    assert summary["shortcall_count"] >= 10


def test_unknown_shortcall_fails_closed():
    try:
        resolve_shortcall("Neo", "/invented")
    except CapabilityRegistryError:
        pass
    else:
        raise AssertionError("unknown shortcall must fail closed")


def test_selector_profile_embeds_only_referenced_routes_plus_gaps():
    profile = selector_profile("Achilles")
    assert profile["selector"] == "achilles"
    assert "audit" in profile["shortcalls"]
    assert "cgx.cross_analysis" in profile["routes"]
    assert not any(item["id"] == "shared-mcp-tools" for item in profile["gaps"])
    assert load_capability_routes()["shared_tool_plane"]["state"] == "available_local"

def test_all_selectors_inherit_node_exchange_handoff_shortcalls():
    selectors = load_selector_shortcalls()["selectors"]
    for selector in selectors:
        calls = list_shortcalls(selector)
        assert calls["exchange"] == "node.exchange.status"
        assert calls["transfer"] == "node.transfer"
        assert calls["compute"] == "node.compute"


def test_node_exchange_routes_bind_promoted_local_runtime_without_peer_overclaim():
    routes = load_capability_routes()["routes"]

    status = routes["node.exchange.status"]
    assert status["state"] == "available"
    assert status["kind"] == "runtime"
    assert status["ro"] is True
    assert status["handler"].endswith(":build_exchange_status")
    assert "Mounted storage is not peer compute" in status["limitation"]

    transfer = routes["node.transfer"]
    assert transfer["state"] == "gated"
    assert transfer["kind"] == "runtime"
    assert transfer["handler"].endswith(":execute_local_transfer")
    assert "DIGITAL_WRITE" in transfer["gate"]
    assert "off-device peer transport" in transfer["limitation"]
    assert transfer["authority_transfer"] is False

    compute = routes["node.compute"]
    assert compute["state"] == "gated"
    assert compute["kind"] == "runtime"
    assert compute["handler"].endswith(":execute_local_compute")
    assert "COMPUTE_ONLY" in compute["gate"]
    assert "Off-device peer compute remains unproven" in compute["limitation"]
    assert compute["authority_transfer"] is False


def test_all_selectors_inherit_object_context_shortcall():
    selectors = load_selector_shortcalls()["selectors"]
    for selector in selectors:
        calls = list_shortcalls(selector)
        assert calls["object"] == "cgx.object_context"


def test_romer_twin_shortcall_resolves_current_object_context_route():
    resolved = resolve_shortcall("Römer-Grex", "/twin")
    assert resolved["route_id"] == "cgx.object_context"
    assert resolved["route"]["state"] == "available"
    assert resolved["route"]["ro"] is True


def test_shared_tool_plane_exposes_object_resolver():
    routes = load_capability_routes()
    assert "cgx_resolve_object" in routes["shared_tool_plane"]["tools"]
