from __future__ import annotations

from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.smart_floor_visuals import (
    FLOOR_VISUAL_CONTRACTS,
    build_smart_floor_widget_export,
    build_smart_floor_visual_catalog,
    floor_fidelity_checks,
    floor_visual_widgets,
    project_wall_smart_widget_descriptors,
    smoke_matrix,
    smart_floor_fidelity_matrix,
    smart_floor_widget_templates,
    visual_result_analysis_plan,
    write_smart_floor_widget_export,
    write_smart_floor_visual_catalog,
    write_smart_floor_visual_report,
)


def test_smart_floor_visual_contracts_cover_all_canonical_floors() -> None:
    assert set(FLOOR_VISUAL_CONTRACTS) == {
        "Trinity",
        "Neo",
        "Architect",
        "TheConstruct",
        "Morpheus",
        "Oracle",
        "Smith",
        "Merovingian",
    }

    for floor, contract in FLOOR_VISUAL_CONTRACTS.items():
        assert contract.floor == floor
        assert contract.bento_widgets
        assert contract.charts
        assert contract.maps_3d
        assert contract.scientific_tools
        assert contract.simulation_hooks
        assert contract.smoke_checks


def test_smart_floor_visual_catalog_merges_manifest_and_python_analysis() -> None:
    catalog = build_smart_floor_visual_catalog(RUNTIME_ROOT)

    assert catalog["purpose"].startswith("Shared smart-floor UI")
    assert catalog["smoke_matrix"]["totals"]["floors"] == 8
    for floor, data in catalog["floors"].items():
        assert data["manifest"]["present"] is True, floor
        assert data["python_analysis"]["present"] is True, floor
        assert data["python_analysis"]["line_count"] > 0, floor
        assert data["visual_result_analysis"]["loading"].startswith("progress")
        assert data["resource_policy"]["maps_3d"] == "defer_until_visible_or_fullscreen"


def test_construct_visual_contract_includes_zoning_maps_gmat_and_ephemeris_rerun() -> None:
    construct = build_smart_floor_visual_catalog(RUNTIME_ROOT)["floors"]["TheConstruct"]

    widget_ids = {widget["id"] for widget in construct["bento_widgets"]}
    tool_ids = {tool["id"] for tool in construct["scientific_tools"]}
    hook_ids = {hook["id"] for hook in construct["simulation_hooks"]}
    map_ids = {item["id"] for item in construct["maps_3d"]}

    assert {"heliocentric_grid", "asteroid_clusters", "gmat_batch", "scenario_lab"} <= widget_ids
    assert {"assign_zone", "cluster_engine", "gmat_exporter"} <= tool_ids
    assert "ephemeris_rerun" in hook_ids
    assert "orbital_rings" in map_ids
    assert "PDS data is a refinement layer, not the bulk macro map." in construct["ui_prompts"]


def test_smart_floor_widget_templates_export_project_wall_descriptors() -> None:
    construct_templates = smart_floor_widget_templates("TheConstruct")
    wall_widgets = project_wall_smart_widget_descriptors()
    export = build_smart_floor_widget_export(RUNTIME_ROOT)

    assert {template["widget_id"] for template in construct_templates} >= {
        "heliocentric_grid",
        "gmat_batch",
        "scenario_lab",
    }
    assert all(template["tile_template"]["kind"] == "smart_widget" for template in construct_templates)
    assert len(wall_widgets) == 8
    assert {widget["floor"] for widget in wall_widgets} == set(FLOOR_VISUAL_CONTRACTS)
    construct_widget = next(widget for widget in wall_widgets if widget["floor"] == "TheConstruct")
    assert "heliocentric_grid" in construct_widget["contract_widgets"]
    assert any(check["id"] == "construct_ephemeris_rerun" for check in construct_widget["fidelity_checks"])
    assert export["widget_template_count"] == sum(len(contract.bento_widgets) for contract in FLOOR_VISUAL_CONTRACTS.values())
    assert export["project_wall_widget_count"] == 8


def test_fidelity_matrix_proofs_construct_oracle_morpheus_smith_and_merovingian_flows() -> None:
    matrix = smart_floor_fidelity_matrix()
    rows = {row["floor"]: row for row in matrix["rows"]}

    assert matrix["checked_floor_count"] == 5
    assert matrix["warn"] == 0
    assert {check["id"] for check in floor_fidelity_checks("TheConstruct")} == {
        "construct_zoning",
        "construct_gmat_batch",
        "construct_ephemeris_rerun",
    }
    assert all(check["status"] == "pass" for check in rows["TheConstruct"]["checks"])
    assert any(check["id"] == "oracle_originals_to_proof" for check in rows["Oracle"]["checks"])
    assert any(check["id"] == "morpheus_proof_flow" for check in rows["Morpheus"]["checks"])
    assert any(check["id"] == "smith_receipt_flow" for check in rows["Smith"]["checks"])
    assert any(check["id"] == "merovingian_diagnostics" for check in rows["Merovingian"]["checks"])


def test_oracle_morpheus_contracts_keep_originals_proof_and_library_roles_separate() -> None:
    catalog = build_smart_floor_visual_catalog(RUNTIME_ROOT)
    oracle = catalog["floors"]["Oracle"]
    morpheus = catalog["floors"]["Morpheus"]

    assert "original_file" in oracle["data_objects"]
    assert "dictionary_term" in oracle["data_objects"]
    assert any(widget["id"] == "dictionary_it" for widget in oracle["bento_widgets"])
    assert any(handoff["to"] == "Morpheus" for handoff in oracle["handoffs"])

    assert "proof_record" in morpheus["data_objects"]
    assert any(widget["id"] == "confidence_curve" for widget in morpheus["bento_widgets"])
    assert any(item["id"] == "definition_neural_tree" for item in morpheus["maps_3d"])


def test_merovingian_visual_contract_owns_diagnostics_performance_and_release_clean() -> None:
    merovingian = build_smart_floor_visual_catalog(RUNTIME_ROOT)["floors"]["Merovingian"]

    widget_ids = {widget["id"] for widget in merovingian["bento_widgets"]}
    chart_ids = {chart["id"] for chart in merovingian["charts"]}
    hook_ids = {hook["id"] for hook in merovingian["simulation_hooks"]}

    assert {"diagnostics", "performance", "release_clean", "audit_log"} <= widget_ids
    assert {"smoke_results", "resource_budget"} <= chart_ids
    assert "release_cull_dry_run" in hook_ids
    assert "cleanup_candidate" in merovingian["data_objects"]


def test_smoke_matrix_and_visual_plan_are_ready_for_ui_binding() -> None:
    matrix = smoke_matrix(RUNTIME_ROOT)
    plan = visual_result_analysis_plan(RUNTIME_ROOT)

    assert matrix["totals"]["floors"] == 8
    assert matrix["totals"]["pass"] == 8
    assert len(plan["surfaces"]) == 8
    assert "chart/map/simulation descriptor catalog" in plan["analysis_outputs"]
    assert "project-wall smart widget descriptor export" in plan["analysis_outputs"]
    assert floor_visual_widgets("TheConstruct")[0]["id"] == "heliocentric_grid"
    construct_surface = next(surface for surface in plan["surfaces"] if surface["floor"] == "TheConstruct")
    assert construct_surface["project_wall_widget_id"] == "floor.construct"
    assert "construct_gmat_batch" in construct_surface["fidelity_checks"]


def test_visual_catalog_and_report_can_be_written_to_runtime_paths(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalog.json"
    report_path = tmp_path / "report.md"
    widget_export_path = tmp_path / "widgets.json"

    catalog = write_smart_floor_visual_catalog(RUNTIME_ROOT, catalog_path)
    report = write_smart_floor_visual_report(RUNTIME_ROOT, report_path)
    widget_export = write_smart_floor_widget_export(RUNTIME_ROOT, widget_export_path)
    default_widget_export = write_smart_floor_widget_export(tmp_path)

    assert catalog_path.exists()
    assert report_path.exists()
    assert widget_export_path.exists()
    assert (tmp_path / "Z Axis" / "Z+3_Trinity" / "data" / "ui" / "smart_floor_widget_export.json").exists()
    assert catalog["floors"]["Trinity"]["primary_surface"]
    assert catalog["project_wall_widgets"]
    assert catalog["fidelity_matrix"]["checked_floor_count"] == 5
    assert report["path"] == str(report_path)
    assert widget_export["project_wall_widget_count"] == 8
    assert default_widget_export["project_wall_widget_count"] == 8
    assert "| TheConstruct | 0 |" in report_path.read_text(encoding="utf-8")
    assert "| TheConstruct | TheConstruct GMAT target export flow | pass |" in report_path.read_text(encoding="utf-8")
