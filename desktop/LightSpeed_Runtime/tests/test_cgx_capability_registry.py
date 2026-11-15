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



def test_interop_shared_references_keep_selector_and_authority_boundaries():
    import pytest
    from lightspeed_runtime.cgx_capability_registry import capability_interop_review
    a=capability_interop_review("Achilles")
    n=capability_interop_review("Neo")
    assert a==capability_interop_review("Achilles")
    assert a["view_sha256"]!=n["view_sha256"]
    shared=set(a["references"]) & set(n["references"])
    assert all(a["references"][k]==n["references"][k] for k in shared if not k.startswith("surface:"))
    key="skill:cgx-capability-router"
    got=capability_interop_review("Achilles",reference=key,expected_view_sha256=a["view_sha256"])
    assert got["descriptor"]==a["references"][key]
    assert not got["execution_authorized"] and not got["authority_transfer"]
    for bad in (None,n["view_sha256"],"0"*64):
        with pytest.raises(CapabilityRegistryError):
            capability_interop_review("Achilles",reference=key,expected_view_sha256=bad)
    with pytest.raises(CapabilityRegistryError):
        capability_interop_review("Achilles",reference="toolkit:freecad",expected_view_sha256=a["view_sha256"])


def test_interop_all_existing_selectors_and_provider_gaps():
    from lightspeed_runtime.cgx_capability_registry import capability_interop_review
    for selector in load_selector_shortcalls()["selectors"]:
        view=capability_interop_review(selector)
        assert sum(k.startswith("skill:") for k in view["references"])==9
        assert sum(k.startswith("surface:") for k in view["references"])==9
        assert not view["native_admitted"] and not view["provider_invocation_performed"]
        got=capability_interop_review(selector,reference="surface:remote-desktop",expected_view_sha256=view["view_sha256"])
        assert "Remote_Desktop_Commander" in got["metadata"]["provider_candidates"]
        assert got["metadata"]["provider_binding"]=="UNVERIFIED_AT_RUNTIME"
        assert not got["execution_authorized"]
        assert all(k in view["references"] for k in got["metadata"]["route_refs"])



def test_composition_reuses_exact_task_bound_references():
    import pytest
    from lightspeed_runtime.cgx_capability_registry import capability_interop_review,compose_capability_review
    a=capability_interop_review("Achilles")
    refs=["skill:cgx-capability-router","route:ops.health","surface:filespace"]
    def compose(keys=refs,**kwargs):
        return compose_capability_review("Achilles",task_id=kwargs.get("task","001c"),
            expected_view_sha256=kwargs.get("stamp",a["view_sha256"]),references=keys)
    c=compose()
    assert c==compose(refs[::-1])
    assert c["references"]=={k:a["references"][k] for k in refs}
    assert not c["execution_authorized"] and not c["authority_transfer"]
    assert c["composition_sha256"]!=compose(task="001d")["composition_sha256"]
    for keys in ([refs[0],refs[0]],["toolkit:freecad"],[]):
        with pytest.raises(CapabilityRegistryError):compose(keys)
    with pytest.raises(CapabilityRegistryError):compose(stamp="0"*64)



def test_specialist_role_references_preserve_source_scope():
    import hashlib
    import pytest
    from lightspeed_runtime.cgx_capability_registry import capability_interop_review, compose_capability_review, REPO_ROOT
    a=capability_interop_review("Achilles")
    ls=capability_interop_review("LightSpeed")
    assert sum(k.startswith("role:") for k in a["references"])==5
    assert sum(k.startswith("role:") for k in ls["references"])==8
    assert "role:smith" not in a["references"] and "role:achilles" not in ls["references"]
    assert a["references"]["role:architect"]==ls["references"]["role:architect"]
    for key in [k for k in ls["references"] if k.startswith("role:")]:
        result=capability_interop_review("LightSpeed",reference=key,expected_view_sha256=ls["view_sha256"])
        meta=result["metadata"]
        assert hashlib.sha256((REPO_ROOT/meta["source_path"]).read_bytes()).hexdigest()==meta["source_sha256"]
        assert "no_heavy_runner_without_gate" in meta["standing_gates"]
        assert not meta["execution_authorized"] and not meta["live_skill_learning_verified"]
    c=compose_capability_review("Achilles",task_id="review-001c",
            expected_view_sha256=a["view_sha256"],references=["role:achilles","role:oracle","skill:cgx-capability-router"])
    assert len(c["references"])==3 and not c["authority_transfer"]
    with pytest.raises(CapabilityRegistryError):
        compose_capability_review("Achilles",task_id="review-001c",
            expected_view_sha256=a["view_sha256"],references=["role:smith"])
