from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = RUNTIME_ROOT.parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.cgx_capability_registry import (
    list_shortcalls,
    selector_profile,
)
from lightspeed_runtime.cgx_cross_analysis import build_cross_analysis_plan
from lightspeed_runtime.cgx_extension_planner import plan_tool_extension
from lightspeed_runtime.cgx_object_context import resolve_object_context
from lightspeed_runtime.cgx_preflight import build_consequence_preflight


def _load_builder():
    path = REPO_ROOT / "plugins" / "source" / "build_plugin_packages.py"
    spec = importlib.util.spec_from_file_location("cgx_plugin_builder_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_preflight_is_read_only_and_non_authoritative():
    result = build_consequence_preflight("romer", "inspect")
    assert result["automatic_execution"] is False
    assert result["canonical_mutation"] is False
    assert result["decision"] in {"ALLOW_WITH_RECEIPTS", "HOLD"}
    assert "not execution permission" in result["authority_limit"]


def test_all_selectors_inherit_new_global_shortcalls_and_node_exchange_calls():
    selectors = [
        "Achilles", "Neo", "Athene", "Raphael", "Cognigrex",
        "Römer-Grex", "Eco-Grex", "EMASSC", "LightSpeed",
    ]
    for selector in selectors:
        calls = list_shortcalls(selector)
        assert calls["preflight"] == "consequence.preflight"
        assert calls["tool-plan"] == "extensions.plan"
        assert calls["open-receipt"] == "receipts.open"
        assert calls["exchange"] == "node.exchange.status"
        assert calls["transfer"] == "node.transfer"
        assert calls["compute"] == "node.compute"

def test_selector_profile_contains_transitive_route_dependencies():
    profile = selector_profile("Achilles")
    assert "cgx.cross_analysis" in profile["routes"]
    assert "consequence.preflight" in profile["routes"]
    assert "assurance.preflight" in profile["routes"]
    assert "custodial.preflight" in profile["routes"]
    assert "tests.plan" in profile["routes"]
    assert "science.query" in profile["routes"]


def test_builder_expands_transitive_dependencies():
    builder = _load_builder()
    routes = {
        "a": {"uses": ["b", "c"]},
        "b": {"uses": ["d"]},
        "c": {},
        "d": {},
    }
    assert builder.expand_route_ids({"a"}, routes) == {"a", "b", "c", "d"}

def test_extension_planner_reuses_existing_sweep():
    plan = plan_tool_extension(
        "Raphael",
        "run a bounded RFS EMFF sweep",
        requested_shortcall="sweep",
    )
    assert plan["decision"] == "reuse_existing"
    assert plan["existing_route"] == "science.rfs_emff_sweep"
    assert plan["implementation_required"] is False


def test_freecad_read_only_adapter_is_reused_not_reimplemented():
    plan = plan_tool_extension("Raphael", "inspect FreeCAD geometry and BOM")
    assert plan["best_existing_route"] is not None
    assert plan["best_existing_route"]["route_id"] in {"cad.freecad", "cad.freecad.bom"}
    assert plan["best_existing_route"]["state"] == "available"
    assert plan["decision"] == "reuse_or_alias"
    assert plan["implementation_required"] is False
    assert plan["safety"]["generic_shell_tool"] is False

def test_cross_analysis_reuses_current_covering_receipt():
    plan = build_cross_analysis_plan(
        "Neo",
        "analyse the current Mark V geometry",
        intent_payload={
            "operation": "analyse",
            "subject": "Mark V",
            "constraints": ["geometry=v3"],
            "requested_outputs": ["cross-analysis-plan"],
        },
        evidence=[{
            "receipt_id": "R-current",
            "status": "PASS",
            "current": True,
            "subject": "Mark V",
            "operation": "analyse",
            "constraints": ["geometry=v3"],
        }],
    )
    assert plan["minimum_work_strategy"] == "reuse_existing"
    assert plan["recommended_routes"][0]["route_id"] == "receipts.list"
    assert plan["execution_policy"]["automatic_execution"] is False

def test_domainless_raphael_consequential_plan_fails_closed_to_domain_required():
    plan = build_cross_analysis_plan(
        "Raphael",
        "compare field assumptions",
        execution_depth="simulate",
    )
    assert plan["preflight"]["state"] == "domain_required"
    assert plan["execution_policy"]["canonical_mutation"] is False


def test_object_context_resolves_cross_surface_watchtower_and_eco_objects():
    watchtower = resolve_object_context("WatchTower", domain="romer")
    assert watchtower["resolved_twin_id"] == "watchtower"
    assert watchtower["semantic_domain"] == "romer"
    assert watchtower["domain_identity"]["semantic_object_id"] == "cgx:domain:romer"
    assert watchtower["semantic_resolution"]["semantic_object_id"] == "WT-001"
    assert watchtower["operations_binding"]["current_record_id"] == "COM-1675"
    assert watchtower["representation"]["representation_class"] == "SOURCE_DERIVED_GEOMETRY"
    assert watchtower["automatic_execution"] is False

    bio = resolve_object_context("Bio Blocks")
    assert bio["resolved_twin_id"] == "embedded_bio_blocks"
    assert bio["semantic_domain"] == "eco"
    assert bio["domain_identity"]["semantic_object_id"] == "cgx:domain:eco"
    assert bio["semantic_resolution"]["state"] == "family_bound_only"


def test_cross_analysis_carries_current_object_context_when_subject_resolves():
    plan = build_cross_analysis_plan(
        "Römer-Grex",
        "analyse current WatchTower source geometry",
        intent_payload={
            "operation": "analyse",
            "subject": "WatchTower",
            "constraints": [],
            "requested_outputs": ["cross-analysis-plan"],
        },
    )
    assert plan["object_context"] is not None
    assert plan["object_context"]["semantic_resolution"]["semantic_object_id"] == "WT-001"
    assert plan["object_context"]["operations_binding"]["current_record_id"] == "COM-1675"
