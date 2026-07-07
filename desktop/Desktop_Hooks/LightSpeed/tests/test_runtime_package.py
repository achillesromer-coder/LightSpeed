from __future__ import annotations

import json
import importlib.util
import sqlite3
import sys
from pathlib import Path

from lightspeed_runtime.activity_tables import default_activity_db_path, default_activity_tables_path
from lightspeed_runtime.contracts import CANONICAL_DATASET_ROLES
from lightspeed_runtime.analytics_validation import (
    default_bellcurve_overlay_path,
    default_table_validation_report_path,
)
from lightspeed_runtime.closure_readiness import default_closure_readiness_path
from lightspeed_runtime.curated_tables import default_curated_tables_index_path
from lightspeed_runtime.dataset_catalog import default_dataset_catalog_path
from lightspeed_runtime.definition_library import default_it_dictionary_path, default_oracle_definition_library_path
from lightspeed_runtime.entity_registry import default_dataset_manifest_index_path
from lightspeed_runtime.finalization import default_dataindex_reduction_path
from lightspeed_runtime.finalization_control import (
    default_execution_control_path,
    default_finalization_overview_path,
)
from lightspeed_runtime.governance_ledgers import default_action_ledger_path, default_approval_ledger_path
from lightspeed_runtime.governance_ledgers import append_action_ledger, append_approval_ledger
from lightspeed_runtime.interchange import default_columnar_handoff_path
from lightspeed_runtime.knowns import default_knowns_declassification_audit_path, default_knowns_queue_objects_path
from lightspeed_runtime.labs.presets import default_simulation_presets_path
from lightspeed_runtime.reference_project import default_romer_reference_path
from lightspeed_runtime.smith_router import default_smith_router_path
from lightspeed_runtime.telemetry import default_telemetry_path
from lightspeed_runtime.units import default_unit_validation_path
from lightspeed_runtime.ui_experience import default_ui_experience_alignment_path
from lightspeed_runtime.ui_polish import default_ui_polish_contract_path
from lightspeed_runtime.operator_os import default_operator_os_contract_path
from lightspeed_runtime.bridge_health import default_bridge_health_path
from lightspeed_runtime.web_integration import default_romer_web_integration_path
from lightspeed_runtime.walkthrough import default_walkthrough_readiness_path
from lightspeed_runtime.route_probe import build_route_probe_report, default_route_probe_report_path, write_route_probe_report
from lightspeed_runtime.workflow_state import default_workflow_state_path
from lightspeed_runtime.storage_paths import (
    active_generated_root,
    canonical_intermediary_targets_path,
    canonical_runtime_config_path,
    ensure_generated_layout,
    finalization_queue_root,
    resolve_intermediary_targets_path,
    resolve_runtime_config_path,
)
from lightspeed_runtime.ai_settings import load_ai_settings
from lightspeed_runtime.contracts import validate_contract_payload
from lightspeed_runtime.desktop_adapters import _ui_state
from lightspeed_runtime.runtime import LightSpeedRuntime


def _write_zoning_runtime_config(root: Path, dataset_dir: Path) -> None:
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "rocks_catalog",
                        "root_path": str(dataset_dir),
                        "source_type": "dataset",
                        "classification": "reference",
                        "floor_owner": "TheConstruct",
                        "workspace_tags": ["romer", "physicslab"],
                        "project_tags": ["Romer"],
                        "trusted_documents": ["asteroids"],
                        "extractors": ["csv"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_sample_asteroid_catalog(dataset_dir: Path) -> Path:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    csv_path = dataset_dir / "asteroids.csv"
    csv_path.write_text(
        "\n".join(
            [
                "id,name,a,e,i,diameter,density,taxonomy,moid",
                "1,16 Psyche,2.921,0.14,3.1,226,3.99,M,0.37",
                "2,1986 DA,1.52,0.23,4.3,2.3,5.1,M,0.03",
                "3,433 Eros,1.458,0.223,10.83,16.8,2.67,S,0.15",
                "4,341843,1.12,0.08,6.4,0.35,1.95,C,0.02",
            ]
        ),
        encoding="utf-8",
    )
    return csv_path


def _write_empirical_runtime_config(root: Path, dataset_dir: Path) -> None:
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "library_empirical_data",
                        "root_path": str(dataset_dir),
                        "source_type": "dataset_bundle",
                        "classification": "reference",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer", "physicslab"],
                        "project_tags": ["Romer"],
                        "trusted_documents": ["empirical", "asteroid", "simulation"],
                        "extractors": ["structured"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_knowns_runtime_config(root: Path, dataset_dir: Path) -> None:
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "achilles_alignment_notes",
                        "root_path": str(dataset_dir),
                        "source_type": "document_bundle",
                        "classification": "canonical",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer"],
                        "project_tags": ["Romer"],
                        "trusted_documents": ["alignment", "doctrine", "log"],
                        "extractors": ["text"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_runtime_package_is_importable_from_app_root() -> None:
    import lightspeed_runtime

    package_root = Path(lightspeed_runtime.__file__).resolve().parent
    assert (package_root / "runtime.py").exists()
    assert (package_root / "desktop_adapters.py").exists()


def test_desktop_ui_state_labels_are_standardized() -> None:
    assert _ui_state("loading", "Workspace state.") == "Loading: Workspace state."
    assert _ui_state("empty", "No payload selected.") == "Empty: No payload selected."
    assert _ui_state("error", "Missing path.") == "Action needed: Missing path."


def test_runtime_log_event_emits_otel_compatible_span(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    config_dir = root / "config" / "runtime"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    entry = runtime.log_event("test_event", "Testing telemetry", payload={"trace_id": "trace_test"})
    summary = runtime.telemetry_summary()

    assert entry["otel_trace_id"] == "trace_test"
    assert summary["span_count"] == 1
    assert summary["recent"][-1]["name"] == "lightspeed.test_event"
    assert Path(default_telemetry_path(root)).exists()


def test_runtime_prefers_nested_runtime_config_paths(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    config_dir = root / "config" / "runtime"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    (config_dir / "intermediary_targets.json").write_text(
        json.dumps({"website_bridge": {"label": "Runtime Test Bridge"}}),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)

    assert runtime.config_path == canonical_runtime_config_path(root)
    assert resolve_runtime_config_path(root) == config_dir / "runtime_reservoirs.json"
    assert resolve_intermediary_targets_path(root) == config_dir / "intermediary_targets.json"
    assert runtime.load_intermediary_targets()["website_bridge"]["label"] == "Runtime Test Bridge"


def test_runtime_bootstrap_reports_canonical_and_snapshot_contracts(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    config_dir = root / "config" / "runtime"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.bootstrap(index_limit_per_source=4)

    contracts = payload["runtime_contracts"]
    assert contracts["canonical_runtime_config_path"].endswith("Z-2_Oracle\\config\\runtime\\runtime_reservoirs.json")
    assert contracts["canonical_intermediary_targets_path"].endswith("Z+1_Architect\\config\\runtime\\intermediary_targets.json")
    assert contracts["publish_snapshot_root"].endswith("Z+1_Architect\\data\\publish\\snapshot")
    assert contracts["snapshot_export_root"].endswith("Z-4_Merovingian\\data\\runtime_exports\\snapshot")
    assert contracts["runtime_exports_generated_on_demand"] is True
    assert payload["config_summary"]["canonical_vs_legacy_order"] == ["canonical", "legacy_fallback"]


def test_runtime_load_config_normalizes_missing_fields(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.load_config()

    assert payload["sources"] == []
    assert payload["catalog_policy"]["default_view"] == "curated_first"
    assert payload["catalog_policy"]["raw_sources_secondary"] is True


def test_approved_publish_action_writes_into_canonical_publish_tree(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    config_dir = root / "config" / "runtime"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    run = runtime.create_lab_run(
        workspace_id="romer",
        project_id="Romer",
        lab_type="gmat",
        scenario_id="romer_publish_test",
        dataset_refs=["rocks.catalog"],
        parameter_set={"window": "2026-Q4"},
        engine="gmat",
    )
    runtime.complete_lab_run(run["run_id"], metrics={"delta_v": 4.0}, outputs=[{"artifact": "bundle.json"}])
    action = runtime.propose_workspace_action(
        "romer",
        "Romer",
        target_scope="project/romer",
        action_type="publish_manifest",
        inputs={"project_id": "Romer"},
    )
    approved = runtime.approve_workspace_action("romer", "Romer", action["action_id"], audit_ref="runtime_test")

    assert approved["result_ref"] is not None
    assert "Z Axis" in approved["result_ref"]
    assert "Z+1_Architect" in approved["result_ref"]
    assert "publish" in approved["result_ref"]
    assert Path(approved["result_ref"]).exists()


def test_runtime_normalizes_ai_settings_from_live_config_shape(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    config_dir = root / "config"
    runtime_dir = config_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    (config_dir / "ai_config.json").write_text(
        json.dumps(
            {
                "ollama": {"enabled": True, "host": "http://localhost:11434", "model": "llama3.2"},
                "achilles": {"enabled": False},
                "modes": {"orchestrator": {"tone": "professional"}},
            }
        ),
        encoding="utf-8",
    )

    settings = load_ai_settings(root)

    assert settings["backends"]["ollama_local"]["model"] == "llama3.2"
    assert settings["personas"]["orchestrator"]["tone"] == "professional"
    assert settings["achilles"]["enabled"] is False


def test_runtime_registers_rich_reservoir_metadata(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "library_empirical_data",
                        "root_path": str(root / "Mounted" / "Empirical"),
                        "source_type": "dataset_bundle",
                        "classification": "reference",
                        "floor_owner": "Oracle",
                        "source_label": "Library Empirical Data",
                        "definition": "Mounted empirical asteroid and laboratory data.",
                        "operator_notes": "Prefer curated-first review.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    source_count = runtime.register_configured_sources()

    manifest = runtime.registry.manifests()[0]
    assert source_count == 1
    assert manifest.source_label == "Library Empirical Data"
    assert "mounted empirical" in manifest.definition.lower()
    assert "curated-first" in manifest.operator_notes.lower()


def test_preferred_empirical_datasets_rewrites_stale_absolute_paths_from_manifest_root(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    internal_empirical = root / "Z Axis" / "Z0_TheConstruct" / "data" / "reservoirs" / "Library" / "Empirical Data"
    internal_empirical.mkdir(parents=True, exist_ok=True)
    dataset_path = internal_empirical / "asteroids.json"
    dataset_path.write_text(json.dumps([{"id": "1", "name": "Psyche", "a": 2.9, "e": 0.14, "i": 3.1}]), encoding="utf-8")

    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "library_empirical_data",
                        "root_path": str(internal_empirical),
                        "source_type": "empirical_dataset_bundle",
                        "classification": "reference",
                        "floor_owner": "TheConstruct",
                        "workspace_tags": ["romer"],
                        "project_tags": ["Romer"],
                        "trusted_documents": ["asteroids"],
                        "extractors": ["json"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    empirical_dir = root / "Z Axis" / "Z-2_Oracle" / "data" / "library" / "empirical"
    empirical_dir.mkdir(parents=True, exist_ok=True)
    (empirical_dir / "empirical_catalog.json").write_text(
        json.dumps(
            {
                "clusterable_inputs": [
                    {
                        "source_id": "library_empirical_data",
                        "relative_path": "asteroids.json",
                        "absolute_path": "C:\\stale\\Library\\Empirical Data\\asteroids.json",
                        "dataset_role": "macro_mapping",
                        "priority": 320,
                    }
                ],
                "recommended_datasets": [],
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    preferred = runtime.preferred_empirical_datasets()

    assert preferred
    assert preferred[0]["absolute_path"] == str(dataset_path)
    assert preferred[0]["relative_path"] == "asteroids.json"


def test_legacy_runtime_bundle_migration_copies_exports_into_canonical_generated_tree(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    legacy_exports = root / "canonical_runtime" / "exports"
    (legacy_exports / "website").mkdir(parents=True, exist_ok=True)
    (legacy_exports / "packages" / "romer").mkdir(parents=True, exist_ok=True)
    (legacy_exports / "reservoir_snapshot.json").write_text(json.dumps({"sources": 1}), encoding="utf-8")
    (legacy_exports / "website" / "romer_manifest.json").write_text(json.dumps({"project": "Romer"}), encoding="utf-8")
    (legacy_exports / "packages" / "romer" / "package_metadata.json").write_text(
        json.dumps({"exported_at": "2026-04-02T00:00:00Z"}),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    summary = runtime.migrate_legacy_runtime_bundle()

    assert summary["migrated"] is True
    assert (root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports" / "legacy_bundle" / "reservoir_snapshot.json").exists()
    assert (root / "Z Axis" / "Z+1_Architect" / "data" / "publish" / "legacy_bundle" / "romer" / "package_metadata.json").exists()


def test_compaction_plan_and_yearly_rollups_are_written(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    tool_dir = root / "w6" / "data" / "oracle_ingest_file"
    for run_id in ("20260101_000000_0001", "20260102_000000_0002", "20270101_000000_0003"):
        run_dir = tool_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "manifest.json").write_text(json.dumps({"tool": "oracle_ingest_file", "status": "ok"}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    runtime.write_generated_data_summary()
    plan = runtime.write_compaction_plan(manifest_threshold=1)
    indexes = runtime.write_compaction_indexes()
    archive = runtime.write_archive_workflow(batch_size=2)
    archive_stage = runtime.stage_next_archive_batch()
    rollups = runtime.write_yearly_rollups()

    assert len(plan["recommendations"]) == 1
    assert plan["recommendations"][0]["tool"] == "oracle_ingest_file"
    assert indexes["tool_count"] == 1
    assert any(path.endswith("index.json") for path in indexes["created_files"])
    assert archive["manifest_count"] == 3
    assert archive["year_plans"][0]["chunk_count"] == 1
    assert archive_stage["staged"] is True
    assert archive_stage["execution_state"]["staged_count"] == 1
    assert any(path.endswith("2026.json") for path in rollups["created_files"])
    assert any(path.endswith("2027.json") for path in rollups["created_files"])


def test_cleanup_report_and_cache_removal_are_safe(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    (root / ".pytest_cache").mkdir(parents=True, exist_ok=True)
    (root / "__pycache__").mkdir(parents=True, exist_ok=True)
    tests_cache = root / "tests" / "__pycache__"
    tests_cache.mkdir(parents=True, exist_ok=True)
    live_pycache = root / "lightspeed_runtime" / "labs" / "__pycache__"
    live_pycache.mkdir(parents=True, exist_ok=True)
    legacy_pycache = root / "canonical_runtime" / "lightspeed_runtime" / "__pycache__"
    legacy_pycache.mkdir(parents=True, exist_ok=True)
    (root / "N.py").write_text("# canonical_runtime reference for audit\n", encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    report = runtime.cleanup_report(force_refresh=True)
    removed = runtime.remove_safe_cache_dirs()

    assert len(report["safe_remove_candidates"]) >= 3
    assert len(removed["removed"]) >= 3
    assert not (root / ".pytest_cache").exists()
    assert not tests_cache.exists()
    assert not live_pycache.exists()
    assert not legacy_pycache.exists()


def test_legacy_runtime_audit_detects_references(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    (root / "canonical_runtime" / "lightspeed_runtime").mkdir(parents=True, exist_ok=True)
    (root / "entry.py").write_text("CANONICAL = 'canonical_runtime'\n", encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    audit = runtime.legacy_runtime_audit(force_refresh=True)

    assert audit["legacy_root_present"] is True
    assert audit["legacy_package_present"] is True
    assert audit["active_code_reference_count"] >= 1


def test_finalization_reports_write_all_canonical_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    (root / "canonical_runtime" / "lightspeed_runtime").mkdir(parents=True, exist_ok=True)
    tool_dir = root / "w6" / "data" / "oracle_ingest_file" / "20260101_000000_0001"
    tool_dir.mkdir(parents=True, exist_ok=True)
    (tool_dir / "manifest.json").write_text(json.dumps({"tool": "oracle_ingest_file", "status": "ok"}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.write_finalization_reports()

    assert Path(payload["summary_path"]).exists()
    assert Path(payload["compaction_plan_path"]).exists()
    assert Path(payload["compaction_index_path"]).exists()
    assert Path(payload["archive_workflow_path"]).exists()
    assert Path(payload["archive_execution_state_path"]).exists()
    assert Path(payload["ingestion_preparation_path"]).exists()
    assert Path(payload["knowns_registry_path"]).exists()
    assert Path(payload["oracle_definition_library_path"]).exists()
    assert Path(payload["it_dictionary_path"]).exists()
    assert Path(payload["ui_polish_contract_path"]).exists()
    assert Path(payload["operator_os_contract_path"]).exists()
    assert Path(payload["romer_web_integration_path"]).exists()
    assert Path(payload["bridge_health_path"]).exists()
    assert Path(payload["walkthrough_readiness_path"]).exists()
    assert Path(payload["knowns_proofing_queue_path"]).exists()
    assert Path(payload["knowns_queue_objects_path"]).exists()
    assert Path(payload["generated_layout_audit_path"]).exists()
    assert Path(payload["finalization_overview_path"]).exists()
    assert Path(payload["execution_control_path"]).exists()
    assert Path(payload["closure_readiness_path"]).exists()
    assert Path(payload["legacy_runtime_diff_path"]).exists()
    assert Path(payload["legacy_runtime_audit_path"]).exists()
    assert Path(payload["cleanup_candidates_path"]).exists()
    assert Path(payload["cleanup_report_path"]).exists()
    assert Path(payload["smart_floor_assimilation_path"]).exists()
    assert payload["execution_control"]["queue_root_kind"] == "canonical_architect_finalization_root"
    assert payload["finalization_overview"]["source_root_kind"] == "canonical_c_root"


def test_execute_heliocentric_zoning_writes_gmat_target_batch(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = tmp_path / "datasets"
    _write_zoning_runtime_config(root, dataset_dir)
    _write_sample_asteroid_catalog(dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    runtime.bootstrap(index_limit_per_source=12)
    result = runtime.execute_heliocentric_zoning("romer", "Romer", source_id="rocks_catalog", top_targets=3)

    assert result["gmat_targets"]
    assert result["gmat_target_batch"]["mission_family"] == "Romer"
    assert Path(result["artifacts"]["gmat_target_batch_json"]).exists()
    assert result["publish_snapshot"]["artifact_count"] >= 1
    workspace = runtime.workspace_state("romer", "Romer")
    assert workspace["latest_publish_manifest"]["artifacts"]


def test_assimilate_external_roots_refreshes_empirical_catalog_to_internal_paths(tmp_path: Path) -> None:
    outer = tmp_path / "LightSpeed Consolidated"
    root = outer / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    outer_empirical = outer / "Library" / "Empirical Data"
    outer_empirical.mkdir(parents=True, exist_ok=True)
    (outer_empirical / "asteroids.json").write_text(
        json.dumps([{"id": "1", "name": "Psyche", "a": 2.9, "e": 0.14, "i": 3.1}]),
        encoding="utf-8",
    )
    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "library_empirical_data",
                        "root_path": str(outer_empirical),
                        "source_type": "empirical_dataset_bundle",
                        "classification": "reference",
                        "floor_owner": "TheConstruct",
                        "workspace_tags": ["romer"],
                        "project_tags": ["Romer"],
                        "trusted_documents": ["asteroids"],
                        "extractors": ["json"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.assimilate_external_roots()
    catalog = runtime.empirical_catalog(force_refresh=True)

    assert payload["moved_count"] >= 1
    assert catalog["recommended_datasets"][0]["absolute_path"].startswith(str(root))


def test_knowns_registry_condenses_doctrine_and_ai_logs(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    doctrine_dir = tmp_path / "NoteBookLM"
    doctrine_dir.mkdir(parents=True, exist_ok=True)
    (doctrine_dir / "Achilles Protocol v1.1.md").write_text(
        "\n".join(
            [
                "Achilles is the sovereign strategic protocol and mission co-pilot.",
                "Cognigrex is the swarm body beneath Achilles oversight.",
                "EMASSC is the IP custodian and Romer is the executor.",
                "Z-axis smart floors structure the desktop operating shell.",
            ]
        ),
        encoding="utf-8",
    )

    ai_logs_dir = root / "ai_logs"
    ai_logs_dir.mkdir(parents=True, exist_ok=True)
    (ai_logs_dir / "ARCHITECTURE_ALIGNMENT_V1.md").write_text(
        "\n".join(
            [
                "The workspace shell, operator portal, and holospace share one smart-floor runtime.",
                "Use ingestion proofing to stage knowns, library, encyclopedia, and datatables.",
                "Stage here, approve in Trinity, commit on review.",
            ]
        ),
        encoding="utf-8",
    )
    empirical_root = tmp_path / "Empirical Data"
    (empirical_root / "Asteroid & Solar System Archive").mkdir(parents=True, exist_ok=True)
    (empirical_root / "Asteroid_Strategic_Mapping_Base_withRocks.xlsx").write_text("sheet", encoding="utf-8")
    (empirical_root / "Asteroid & Solar System Archive" / "asteroids.json").write_text("{}", encoding="utf-8")

    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "notebooklm_2026",
                        "root_path": str(doctrine_dir),
                        "source_type": "doctrine_export",
                        "classification": "canonical",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer", "achilles"],
                        "project_tags": ["Romer", "Achilles"],
                        "trusted_documents": ["Achilles Protocol v1.1"],
                        "extractors": ["text"],
                    },
                    {
                        "source_id": "lightspeed_ai_logs",
                        "root_path": str(ai_logs_dir),
                        "source_type": "alignment_log_bundle",
                        "classification": "reference",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer", "cognigrex"],
                        "project_tags": ["LightSpeed"],
                        "trusted_documents": ["ARCHITECTURE_ALIGNMENT_V1"],
                        "extractors": ["text"],
                    },
                    {
                        "source_id": "library_empirical_data",
                        "root_path": str(empirical_root),
                        "source_type": "empirical_dataset_bundle",
                        "classification": "reference",
                        "floor_owner": "TheConstruct",
                        "workspace_tags": ["romer", "physicslab"],
                        "project_tags": ["Romer", "GMAT", "PhysicsLab"],
                        "trusted_documents": ["Asteroid_Strategic_Mapping_Base_withRocks", "asteroids.json"],
                        "extractors": ["json", "xlsx"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    runtime.write_empirical_catalog()
    payload = runtime.write_knowns_registry()

    assert payload["source_count"] == 3
    assert payload["document_count"] >= 2
    theme_ids = {item["theme_id"] for item in payload["themes"]}
    assert "achilles_operator" in theme_ids
    assert "smart_floor_os" in theme_ids
    assert "empirical_dataset_layer" in theme_ids
    achilles = next(item for item in payload["themes"] if item["theme_id"] == "achilles_operator")
    assert "governed operator" in achilles["proofed_definition"].lower()
    assert achilles["definition_basis"] == "curated_oracle_dictionary"
    assert payload["empirical_layer"]["headline_count"] >= 1
    assert Path(payload["registry_path"]).exists()
    assert Path(default_oracle_definition_library_path(root)).exists()


def test_ingestion_preparation_routes_doctrine_sources_into_knowns(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    doctrine_dir = tmp_path / "Docs"
    doctrine_dir.mkdir(parents=True, exist_ok=True)
    (doctrine_dir / "Achilles Protocol v1.1.md").write_text("Achilles architecture and doctrine", encoding="utf-8")

    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "docs_2026_master",
                        "root_path": str(doctrine_dir),
                        "source_type": "master_doctrine_bundle",
                        "classification": "canonical",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer", "achilles"],
                        "project_tags": ["Romer", "Achilles"],
                        "trusted_documents": ["Achilles Protocol"],
                        "extractors": ["text"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    payload = runtime.write_ingestion_preparation()

    assert payload["destination_counts"]["knowns"] >= 1
    assert "knowns" in payload["sources"][0]["intended_destinations"]


def test_knowns_proofing_queue_routes_themes_into_floor_targets(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    doctrine_dir = tmp_path / "Doctrine"
    doctrine_dir.mkdir(parents=True, exist_ok=True)
    (doctrine_dir / "Achilles Protocol v1.1.md").write_text(
        "\n".join(
            [
                "Achilles is the governed operator and mission co-pilot.",
                "Cognigrex is the execution body.",
                "Romer and EMASSC governance is central.",
                "GMAT scenario workflows support mission planning.",
            ]
        ),
        encoding="utf-8",
    )

    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "notebooklm_2026",
                        "root_path": str(doctrine_dir),
                        "source_type": "doctrine_export",
                        "classification": "canonical",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer", "achilles"],
                        "project_tags": ["Romer", "Achilles"],
                        "trusted_documents": ["Achilles Protocol v1.1"],
                        "extractors": ["text"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    payload = runtime.write_knowns_proofing_queue()

    assert payload["entry_count"] >= 1
    destinations = {item["destination"] for item in payload["entries"]}
    assert "knowns" in destinations
    assert "library" in destinations or "datatables" in destinations
    assert Path(payload["queue_path"]).exists()
    objects = runtime.write_knowns_queue_objects()
    assert objects["object_count"] >= 1
    assert any(item["entity_kind"] == "promotion_queue" for item in objects["objects"])
    assert Path(default_knowns_queue_objects_path(root)).exists()


def test_empirical_dataset_layer_routes_to_library_datatables_and_scenario_lab(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    doctrine_dir = tmp_path / "Doctrine"
    doctrine_dir.mkdir(parents=True, exist_ok=True)
    (doctrine_dir / "Achilles Protocol v1.1.md").write_text("Achilles operator and GMAT mission doctrine.", encoding="utf-8")
    empirical_root = tmp_path / "Empirical Data"
    (empirical_root / "Asteroid & Solar System Archive").mkdir(parents=True, exist_ok=True)
    (empirical_root / "Asteroid_Strategic_Mapping_Base_withRocks.xlsx").write_text("sheet", encoding="utf-8")
    (empirical_root / "Asteroid & Solar System Archive" / "asteroids.json").write_text("{}", encoding="utf-8")

    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "notebooklm_2026",
                        "root_path": str(doctrine_dir),
                        "source_type": "doctrine_export",
                        "classification": "canonical",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer", "achilles"],
                        "project_tags": ["Romer", "Achilles"],
                        "trusted_documents": ["Achilles Protocol v1.1"],
                        "extractors": ["text"],
                    },
                    {
                        "source_id": "library_empirical_data",
                        "root_path": str(empirical_root),
                        "source_type": "empirical_dataset_bundle",
                        "classification": "reference",
                        "floor_owner": "TheConstruct",
                        "workspace_tags": ["romer", "physicslab"],
                        "project_tags": ["Romer", "GMAT", "PhysicsLab"],
                        "trusted_documents": ["Asteroid_Strategic_Mapping_Base_withRocks", "asteroids.json"],
                        "extractors": ["json", "xlsx"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    runtime.write_empirical_catalog()
    payload = runtime.write_knowns_proofing_queue()

    empirical_entries = [item for item in payload["entries"] if item["theme_id"] == "empirical_dataset_layer"]
    destinations = {item["destination"] for item in empirical_entries}
    assert {"knowns", "library", "encyclopedia_candidates", "datatables", "scenario_lab"} <= destinations


def test_legacy_runtime_diff_classifies_duplicate_files(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    canonical = root / "lightspeed_runtime"
    legacy = root / "canonical_runtime" / "lightspeed_runtime"
    canonical.mkdir(parents=True, exist_ok=True)
    legacy.mkdir(parents=True, exist_ok=True)
    (canonical / "runtime.py").write_text("A = 1\n", encoding="utf-8")
    (legacy / "runtime.py").write_text("A = 2\n", encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    diff = runtime.legacy_runtime_diff(force_refresh=True)

    assert diff["legacy_file_count"] == 1
    assert diff["different_file_count"] == 1
    assert diff["files"][0]["status"] == "different"


def test_legacy_runtime_sync_reconciles_duplicate_bundle(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    canonical = root / "lightspeed_runtime"
    legacy = root / "canonical_runtime" / "lightspeed_runtime"
    canonical.mkdir(parents=True, exist_ok=True)
    legacy.mkdir(parents=True, exist_ok=True)
    (canonical / "runtime.py").write_text("A = 2\n", encoding="utf-8")
    (legacy / "runtime.py").write_text("A = 1\n", encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.sync_legacy_runtime_bundle()

    assert payload["synced_count"] >= 1
    assert payload["after_diff"]["different_file_count"] == 0
    assert payload["removal_ready_after_sync"] is True


def test_cleanup_candidate_report_finds_safe_candidates(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    (root / "empty.txt").write_text("", encoding="utf-8")
    (root / "empty_dir").mkdir(parents=True, exist_ok=True)

    legacy_exports = root / "canonical_runtime" / "exports"
    (legacy_exports / "website").mkdir(parents=True, exist_ok=True)
    (legacy_exports / "website" / "romer_manifest.json").write_text(json.dumps({"project": "Romer"}), encoding="utf-8")
    mirror = root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports" / "legacy_bundle" / "website"
    mirror.mkdir(parents=True, exist_ok=True)
    (mirror / "romer_manifest.json").write_text(json.dumps({"project": "Romer"}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.cleanup_candidate_report(force_refresh=True)

    assert payload["empty_file_count"] >= 1
    assert payload["empty_directory_count"] >= 1
    assert payload["duplicate_legacy_export_count"] >= 1


def test_remove_duplicate_legacy_exports_clears_exact_legacy_copies(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    legacy_exports = root / "canonical_runtime" / "exports"
    (legacy_exports / "website").mkdir(parents=True, exist_ok=True)
    (legacy_exports / "website" / "romer_manifest.json").write_text(json.dumps({"project": "Romer"}), encoding="utf-8")

    mirror = root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports" / "legacy_bundle" / "website"
    mirror.mkdir(parents=True, exist_ok=True)
    (mirror / "romer_manifest.json").write_text(json.dumps({"project": "Romer"}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.remove_duplicate_legacy_exports()

    assert payload["removed_count"] == 1
    assert payload["cleanup_candidates_after"] == 0
    assert not (legacy_exports / "website" / "romer_manifest.json").exists()


def test_weekly_log_consolidates_runtime_events_into_one_file(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    routine = runtime.log_event("test_event", "routine event")
    runtime.log_event("publish_review", "first governed event")
    runtime.log_event("maintenance_complete", "second governed event")
    summary = runtime.weekly_log_summary()

    assert routine["persisted"] is False
    assert summary["exists"] is True
    assert summary["entry_count"] == 2
    assert summary["latest_category"] == "maintenance_complete"
    assert Path(summary["path"]).exists()
    assert "Z-4_Merovingian" in summary["path"]


def test_ingestion_preparation_classifies_sources_for_proofing(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    docs = tmp_path / "NotebookLM"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "Achilles Protocol.md").write_text("# Achilles Protocol\n", encoding="utf-8")
    data = tmp_path / "Rocks"
    data.mkdir(parents=True, exist_ok=True)
    (data / "rocks.csv").write_text("id,name\n1,Ceres\n", encoding="utf-8")
    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "notebooklm_2026",
                        "root_path": str(docs),
                        "source_type": "document_bundle",
                        "classification": "canonical",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer"],
                        "project_tags": ["Romer"],
                        "trusted_documents": ["Achilles Protocol"],
                        "extractors": ["text"],
                    },
                    {
                        "source_id": "rocks_catalog",
                        "root_path": str(data),
                        "source_type": "dataset",
                        "classification": "reference",
                        "floor_owner": "TheConstruct",
                        "workspace_tags": ["romer"],
                        "project_tags": ["Romer"],
                        "trusted_documents": [],
                        "extractors": ["csv"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    runtime.bootstrap(index_limit_per_source=10)
    payload = runtime.write_ingestion_preparation()

    assert payload["source_count"] == 2
    assert payload["destination_counts"]["library"] >= 1
    assert payload["destination_counts"]["datatables"] >= 1
    assert Path(root / "Z Axis" / "Z-2_Oracle" / "data" / "ingestion" / "ingestion_preparation.json").exists()


def test_generated_layout_audit_marks_operations_w6_as_legacy_mirror(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    canonical = root / "Z Axis" / "Z-2_Oracle" / "data" / "ingestion" / "oracle_ingest_file"
    legacy = root / "operations" / "w6" / "data" / "oracle_ingest_file"
    (canonical / "20260101_000000_0001").mkdir(parents=True, exist_ok=True)
    (canonical / "20260102_000000_0002").mkdir(parents=True, exist_ok=True)
    (legacy / "20251231_000000_0001").mkdir(parents=True, exist_ok=True)

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.write_generated_layout_audit()

    assert payload["legacy_operations"]["present"] is True
    assert payload["canonical"]["tool_count"] == 1
    assert any(item["status"] == "legacy_partial_mirror" for item in payload["comparisons"])
    assert Path(root / "Z Axis" / "Z-4_Merovingian" / "data" / "reports" / "generated_layout_audit.json").exists()


def test_heliocentric_zoning_writes_outputs_into_canonical_lab_tree(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = tmp_path / "datasets"
    _write_sample_asteroid_catalog(dataset_dir)
    _write_zoning_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    result = runtime.execute_heliocentric_zoning(
        "romer",
        "Romer",
        source_id="rocks_catalog",
        max_records=20,
        cluster_target=2,
        top_targets=3,
    )

    assert result["metrics"]["records_zoned"] == 4
    assert result["metrics"]["cluster_count"] >= 1
    assert "Z Axis" in result["artifacts"]["zones_summary_json"]
    assert "Z0_TheConstruct" in result["artifacts"]["zones_summary_json"]
    assert "labs" in result["artifacts"]["zones_summary_json"]
    assert "heliocentric_zoning" in result["artifacts"]["zones_summary_json"]
    assert Path(result["artifacts"]["targets_shortlist_json"]).exists()
    state = runtime.workspace_state("romer", "Romer")
    assert state["latest_runs"][-1]["lab_type"] == "heliocentric_zoning"
    assert state["latest_runs"][-1]["status"] == "completed"


def test_approved_zoning_action_executes_and_returns_shortlist_reference(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = tmp_path / "datasets"
    _write_sample_asteroid_catalog(dataset_dir)
    _write_zoning_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    action = runtime.propose_workspace_action(
        "romer",
        "Romer",
        target_scope="project/romer",
        action_type="build_heliocentric_zoning",
        inputs={
            "source_id": "rocks_catalog",
            "max_records": 20,
            "cluster_target": 2,
            "top_targets": 2,
        },
    )

    approved = runtime.approve_workspace_action("romer", "Romer", action["action_id"], audit_ref="runtime_test")
    state = runtime.workspace_state("romer", "Romer")

    assert approved["result_ref"] is not None
    assert Path(approved["result_ref"]).exists()
    assert state["latest_runs"][-1]["lab_type"] == "heliocentric_zoning"
    assert state["latest_runs"][-1]["status"] == "completed"


def test_smart_floor_assimilation_report_tracks_external_sources_and_floor_roots(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = tmp_path / "datasets"
    _write_sample_asteroid_catalog(dataset_dir)
    _write_zoning_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.write_smart_floor_assimilation()

    assert payload["external_source_count"] == 1
    assert payload["canonical_output_roots"]["oracle_ingestion"].endswith("Z-2_Oracle\\data\\ingestion")
    assert payload["canonical_output_roots"]["construct_labs"].endswith("Z0_TheConstruct\\data\\labs")
    assert payload["legacy_roots"]["root_w6"]["present"] is False


def test_smart_floor_migration_copies_flat_outputs_and_test_results(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    (root / "data" / "generated" / "reports").mkdir(parents=True, exist_ok=True)
    (root / "data" / "generated" / "reports" / "generated_layout_audit.json").write_text("{}", encoding="utf-8")
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "latest_test_results.json").write_text(json.dumps({"passed": 1}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.migrate_smart_floor_outputs()

    assert payload["copied_file_count"] >= 2
    assert (root / "Z Axis" / "Z-4_Merovingian" / "data" / "reports" / "generated_layout_audit.json").exists()
    assert (root / "Z Axis" / "Z-4_Merovingian" / "data" / "quality" / "latest_test_results.json").exists()
    assert (root / "Z Axis" / "Z-3_Smith" / "data" / "operations" / "legacy_operations_registry.json").exists()


def test_rehome_legacy_roots_moves_w6_operations_and_runtime_bundle_under_smart_floors(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    (root / "w6" / "data" / "oracle_ingest_file" / "20260101_000000_0001").mkdir(parents=True, exist_ok=True)
    (root / "w6" / "data" / "oracle_ingest_file" / "20260101_000000_0001" / "manifest.json").write_text(
        json.dumps({"tool": "oracle_ingest_file"}),
        encoding="utf-8",
    )
    (root / "operations" / "w6" / "data" / "oracle_ingest_file" / "20251231_000000_0001").mkdir(parents=True, exist_ok=True)
    (root / "canonical_runtime" / "exports").mkdir(parents=True, exist_ok=True)
    (root / "canonical_runtime" / "lightspeed_runtime").mkdir(parents=True, exist_ok=True)
    (root / "canonical_runtime" / "lightspeed_runtime" / "runtime.py").write_text("A = 1\n", encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.rehome_legacy_roots()

    assert payload["moved_count"] >= 3
    assert not (root / "w6").exists()
    assert not (root / "operations" / "w6").exists()
    assert not (root / "canonical_runtime").exists()
    assert (root / "Z Axis" / "Z-3_Smith" / "data" / "legacy" / "w6" / "data" / "oracle_ingest_file").exists()
    assert (root / "Z Axis" / "Z-3_Smith" / "data" / "legacy" / "operations_w6" / "data" / "oracle_ingest_file").exists()
    assert (root / "Z Axis" / "Z-4_Merovingian" / "data" / "legacy_runtime_bundle" / "canonical_runtime" / "lightspeed_runtime" / "runtime.py").exists()


def test_promote_knowns_queue_writes_oracle_destinations_and_ledger(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    docs = tmp_path / "NotebookLM"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "Achilles Protocol v1.1.md").write_text(
        "# Achilles Protocol\nAchilles is the operator. Cognigrex is the swarm body. Romer uses GMAT mission batches.\n",
        encoding="utf-8",
    )
    (docs / "Architecture Notes.md").write_text(
        "Smart floor workspace shell operator portal holospace proofed knowns pipeline.\n",
        encoding="utf-8",
    )
    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "docs_2026_master",
                        "root_path": str(docs),
                        "source_type": "document_bundle",
                        "classification": "canonical",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer"],
                        "project_tags": ["Romer"],
                        "trusted_documents": ["Achilles Protocol v1.1.md"],
                        "extractors": ["text"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    runtime.write_knowns_registry()
    runtime.write_knowns_proofing_queue()
    payload = runtime.promote_knowns_queue(destinations=["library", "encyclopedia_candidates"], max_entries=20)

    assert payload["promoted_count"] >= 1
    assert Path(payload["ledger_path"]).exists()
    assert any((root / "Z Axis" / "Z-2_Oracle" / "data" / "library" / "knowns").rglob("*.md"))
    assert any((root / "Z Axis" / "Z-2_Oracle" / "data" / "encyclopedia" / "candidates").rglob("*.json"))
    markdown = next((root / "Z Axis" / "Z-2_Oracle" / "data" / "library" / "knowns").rglob("*.md")).read_text(
        encoding="utf-8"
    )
    assert "## Proofed Definition" in markdown
    refreshed_queue = runtime.knowns_proofing_queue()
    assert refreshed_queue["promoted_count"] >= 1


def test_remove_duplicate_generated_shell_files_clears_exact_compatibility_copies(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    legacy_file = root / "data" / "generated" / "reports" / "generated_layout_audit.json"
    canonical_file = root / "Z Axis" / "Z-4_Merovingian" / "data" / "reports" / "generated_layout_audit.json"
    legacy_file.parent.mkdir(parents=True, exist_ok=True)
    canonical_file.parent.mkdir(parents=True, exist_ok=True)
    canonical_file.write_text(json.dumps({"status": "canonical"}), encoding="utf-8")
    legacy_file.write_text(canonical_file.read_text(encoding="utf-8"), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.remove_duplicate_generated_shell_files()

    assert payload["removed_count"] == 1
    assert payload["remaining_duplicate_count"] == 0
    assert not legacy_file.exists()


def test_remove_duplicate_generated_shell_files_merges_legacy_weekly_log(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    legacy_log = root / "data" / "generated" / "logs" / "lightspeed_2026_W14.jsonl"
    canonical_log = root / "Z Axis" / "Z-4_Merovingian" / "data" / "logs" / "lightspeed_2026_W14.jsonl"
    legacy_log.parent.mkdir(parents=True, exist_ok=True)
    canonical_log.parent.mkdir(parents=True, exist_ok=True)
    canonical_log.write_text('{"message":"canonical"}\n', encoding="utf-8")
    legacy_log.write_text('{"message":"canonical"}\n{"message":"legacy-only"}\n', encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.remove_duplicate_generated_shell_files()

    assert payload["merged_log_count"] == 1
    assert payload["generated_root_present_after"] is False
    assert not legacy_log.exists()
    assert not (root / "data" / "generated").exists()
    merged_text = canonical_log.read_text(encoding="utf-8")
    assert '{"message":"legacy-only"}' in merged_text


def test_empirical_catalog_condenses_empirical_source_bundle(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    empirical_root = tmp_path / "Empirical Data"
    (empirical_root / "Asteroid & Solar System Archive").mkdir(parents=True, exist_ok=True)
    (empirical_root / "Asteroid_Strategic_Mapping_Base_withRocks.xlsx").write_text("sheet", encoding="utf-8")
    (empirical_root / "Asteroid & Solar System Archive" / "asteroids.json").write_text("{}", encoding="utf-8")
    (empirical_root / "Asteroid & Solar System Archive" / "Asteroid_Mining_Concepts.txt").write_text("concepts", encoding="utf-8")
    (empirical_root / "Asteroid & Solar System Archive" / "Eros.obj").write_text("o Eros\n", encoding="utf-8")
    (empirical_root / "Asteroid & Solar System Archive" / "Solar System Dynamics - Nasa.jpg").write_bytes(b"img")
    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "library_empirical_data",
                        "root_path": str(empirical_root),
                        "source_type": "empirical_dataset_bundle",
                        "classification": "reference",
                        "floor_owner": "TheConstruct",
                        "workspace_tags": ["romer", "physicslab"],
                        "project_tags": ["Romer", "GMAT", "PhysicsLab"],
                        "trusted_documents": [
                            "Asteroid_Strategic_Mapping_Base_withRocks",
                            "asteroids.json",
                            "Asteroid_Mining_Concepts",
                        ],
                        "extractors": ["json", "xlsx", "csv", "image", "obj"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    payload = runtime.write_empirical_catalog()

    assert payload["source_count"] == 1
    assert payload["class_totals"]["structured_dataset"] >= 2
    assert len(payload["recommended_datasets"]) >= 2
    assert len(payload["dataset_table"]) >= 2
    assert len(payload["headline_knowns"]) >= 1
    assert payload["role_totals"]["macro_mapping"] >= 1
    assert Path(payload["catalog_path"]).exists()


def test_execution_queues_build_three_queues_with_master_backlog(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.write_execution_queues()

    assert payload["queue_count"] == 3
    assert payload["action_count"] >= 25
    assert len(payload["queues"]) == 3
    assert all(len(queue["active_top_five"]) <= 5 for queue in payload["queues"])
    assert Path(payload["queue_path"]).exists()
    assert payload["owner_floor"] == "Architect"
    assert payload["control_floor"] == "Architect"
    assert payload["queue_root_kind"] == "canonical_architect_finalization_root"


def test_execution_queue_advance_marks_action_completed(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    runtime.write_execution_queues()
    payload = runtime.advance_execution_queue("KA-01", note="Completed in test pass.")

    assert payload["updated"] is True
    refreshed = runtime.execution_queues()
    action = next(item for item in refreshed["actions"] if item["action_id"] == "KA-01")
    assert action["status"] == "completed"
    assert action["action_taken"] == "Completed in test pass."


def test_entity_registry_writes_dataset_manifests_with_canonical_roles(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = dataset_dir / "asteroids.json"
    dataset_path.write_text(
        json.dumps(
            [
                {"id": 16, "name": "Psyche", "a": 2.921, "e": 0.14, "i": 3.1},
                {"id": 433, "name": "Eros", "a": 1.458, "e": 0.223, "i": 10.83},
            ]
        ),
        encoding="utf-8",
    )
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.write_entity_registry()

    assert payload["entity_count"] >= 10
    assert payload["dataset_manifest_count"] >= 1

    index_path = default_dataset_manifest_index_path(root)
    assert index_path.exists()
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert index_payload["manifest_count"] >= 1

    manifest_path = Path(index_payload["items"][0]["manifest_path"])
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["role"] in CANONICAL_DATASET_ROLES
    assert len(manifest["hash_sha256"]) == 64
    assert manifest["source_id"] == "library_empirical_data"
    assert manifest["scientific_role"] in {"macro_mapping", "micro_validation", "general_empirical", "reference_imagery", "simulation_model"}


def test_entity_registry_dataset_ids_are_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = dataset_dir / "asteroids.json"
    dataset_path.write_text(json.dumps([{"id": 1, "name": "Psyche"}]), encoding="utf-8")
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    runtime.write_entity_registry()
    first_index = json.loads(default_dataset_manifest_index_path(root).read_text(encoding="utf-8"))
    runtime.write_entity_registry()
    second_index = json.loads(default_dataset_manifest_index_path(root).read_text(encoding="utf-8"))

    assert first_index["items"][0]["dataset_id"] == second_index["items"][0]["dataset_id"]


def test_curated_tables_index_writes_governed_table_exports(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "asteroids.json").write_text(
        json.dumps(
            [
                {"id": 16, "name": "Psyche", "a": 2.921, "e": 0.14, "i": 3.1},
                {"id": 433, "name": "Eros", "a": 1.458, "e": 0.223, "i": 10.83},
            ]
        ),
        encoding="utf-8",
    )
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.write_curated_tables_index()

    assert payload["table_count"] >= 2
    index_path = default_curated_tables_index_path(root)
    assert index_path.exists()
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert index_payload["table_count"] >= 2
    first_table = index_payload["tables"][0]
    assert Path(first_table["csv_path"]).exists()
    assert Path(first_table["json_path"]).exists()
    assert first_table["actual_format"] in {"csv", "parquet"}


def test_columnar_handoff_bundle_writes_column_first_tables(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "asteroids.json").write_text(
        json.dumps(
            [
                {"id": 16, "name": "Psyche", "a": 2.921},
                {"id": 433, "name": "Eros", "a": 1.458},
            ]
        ),
        encoding="utf-8",
    )
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.write_columnar_handoff()

    assert payload["table_count"] >= 2
    bundle_path = default_columnar_handoff_path(root)
    assert bundle_path.exists()
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    first_table = bundle["tables"][0]
    assert first_table["row_count"] >= 1
    assert isinstance(first_table["columns"], list)
    assert isinstance(first_table["columnar_data"], dict)


def test_entity_registry_includes_runtime_workspace_table_and_agent_entities(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "asteroids.json").write_text(
        json.dumps([{"id": 1, "name": "Ceres", "a": 2.77, "e": 0.08, "i": 10.6}]),
        encoding="utf-8",
    )
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    runtime.propose_workspace_action(
        "romer",
        "Romer",
        target_scope="project/romer",
        action_type="publish_manifest",
        inputs={"query": "test"},
        requires_approval=True,
    )
    runtime.create_lab_run(
        "romer",
        "Romer",
        lab_type="heliocentric_zoning",
        scenario_id="heliocentric_zoning_grid",
        dataset_refs=["source://library_empirical_data/asteroids.json"],
        parameter_set={"cluster_target": 3},
        engine="python",
    )

    payload = runtime.write_entity_registry()
    kinds = payload["entity_kinds"]

    assert kinds["workspace"] >= 1
    assert kinds["project"] >= 1
    assert kinds["run"] >= 1
    assert kinds["action"] >= 1
    assert kinds["table"] >= 2
    assert kinds["agent"] >= 2


def test_scientific_query_layer_and_query_execution_work_with_mounted_dataset(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "asteroids.json").write_text(
        json.dumps(
            [
                {"id": 16, "name": "Psyche", "a": 2.921, "e": 0.14, "i": 3.1},
                {"id": 433, "name": "Eros", "a": 1.458, "e": 0.22, "i": 10.8},
            ]
        ),
        encoding="utf-8",
    )
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.write_scientific_query_layer()

    assert payload["queryable_count"] >= 1
    assert payload["preferred_engine"] in {"duckdb", "pandas", "python"}
    assert payload["query_templates"][0]["template_id"] in {"tap_like_curated_review", "tap_like_dataset_lookup"}

    query_name = payload["queryables"][0]["query_name"]
    assert payload["queryables"][0]["owner_floor"] == "Oracle"
    assert payload["queryables"][0]["source_label"] == "library_empirical_data"
    result = runtime.query_scientific_table(
        query_name,
        limit=1,
        filters=[{"column": "name", "op": "contains", "value": "Psy"}],
    )
    assert result["matched_count"] == 1
    assert result["rows"][0]["name"] == "Psyche"
    assert result["owner_floor"] == "Oracle"
    assert "returned 1 row" in result["summary"]


def test_dataset_catalog_shell_writes_stac_dcat_entries_and_pds4_like_profiles(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    mission_dir = dataset_dir / "PDS" / "Eros"
    mission_dir.mkdir(parents=True, exist_ok=True)
    (mission_dir / "shape_model.json").write_text(
        json.dumps(
            [
                {"id": 433, "name": "Eros", "harmonic_degree": 12, "shape_vertices": 1024},
            ]
        ),
        encoding="utf-8",
    )
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    runtime.write_knowns_registry()
    runtime.write_curated_tables_index()
    runtime.write_entity_registry()
    runtime.write_scientific_query_layer()
    payload = runtime.write_dataset_catalog_shell()

    assert payload["catalog_profile"] == "stac_dcat_shell"
    assert payload["dataset_count"] >= 1
    assert payload["mission_refinement_count"] >= 1
    assert Path(default_dataset_catalog_path(root)).exists()
    mission_profiles = [item for item in payload["datasets"] if item.get("metadata_profile")]
    assert mission_profiles
    assert mission_profiles[0]["metadata_profile"]["profile_type"] == "pds4_like"
    assert mission_profiles[0]["owner_floor"] == "Oracle"
    assert mission_profiles[0]["usage_role"] in CANONICAL_DATASET_ROLES
    assert mission_profiles[0]["source_label"] == "library_empirical_data"


def test_tap_like_query_surface_executes_filter_request(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "asteroids.json").write_text(
        json.dumps(
            [
                {"id": 16, "name": "Psyche", "a": 2.921, "e": 0.14, "i": 3.1},
                {"id": 433, "name": "Eros", "a": 1.458, "e": 0.22, "i": 10.8},
            ]
        ),
        encoding="utf-8",
    )
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    query_layer = runtime.write_scientific_query_layer()
    assert query_layer["query_protocol"] == "tap_like"
    assert len(query_layer["query_templates"]) >= 1

    request = {
        "from": query_layer["queryables"][0]["query_name"],
        "where": [{"column": "name", "op": "contains", "value": "Psy"}],
        "limit": 1,
    }
    result = runtime.query_scientific_table_tap(request)

    assert result["protocol"] == "tap_like"
    assert result["matched_count"] == 1
    assert result["rows"][0]["name"] == "Psyche"


def test_unit_validation_report_and_zoning_unit_summary_are_written(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "asteroids.json").write_text(
        json.dumps(
            [
                {"id": 16, "name": "Psyche", "a": 2.921, "e": 0.14, "i": 3.1, "diameter": 226.0},
                {"id": 433, "name": "Eros", "a": 1.458, "e": 0.22, "i": 10.8, "diameter": 16.8},
            ]
        ),
        encoding="utf-8",
    )
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    report = runtime.write_unit_validation_report()
    assert report["dataset_count"] >= 1
    assert Path(default_unit_validation_path(root)).exists()
    assert report["datasets"][0]["owner_floor"] == "Oracle"
    assert report["datasets"][0]["usage_role"] in CANONICAL_DATASET_ROLES

    zoning = runtime.execute_heliocentric_zoning(
        "romer",
        "Romer",
        source_path=str(dataset_dir / "asteroids.json"),
        scenario_id="heliocentric_zoning_grid",
        max_records=50,
        cluster_target=2,
        top_targets=10,
    )
    assert "unit_validation" in zoning
    assert any(check["column"] == "semi_major_axis" for check in zoning["unit_validation"]["checks"])
    assert zoning["simulation_parameters"]["owner_floor"] == "TheConstruct"
    assert zoning["simulation_parameters"]["source_owner"] == "Oracle"


def test_curated_table_validation_and_bellcurve_overlay_are_written(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = root / "Mounted" / "Empirical"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    (dataset_dir / "asteroids.json").write_text(
        json.dumps(
            [
                {"id": 16, "name": "Psyche", "a": 2.921, "e": 0.14, "i": 3.1, "diameter": 226.0},
                {"id": 433, "name": "Eros", "a": 1.458, "e": 0.22, "i": 10.8, "diameter": 16.8},
            ]
        ),
        encoding="utf-8",
    )
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    runtime.write_knowns_registry()
    runtime.write_curated_tables_index()
    validation = runtime.write_table_validation_report()
    overlay = runtime.write_bellcurve_overlay()

    assert validation["table_count"] >= 2
    assert validation["failed_count"] == 0
    assert Path(default_table_validation_report_path(root)).exists()
    assert len(overlay["dataset_confidence_histogram"]) >= 1
    assert Path(default_bellcurve_overlay_path(root)).exists()


def test_publish_package_includes_checkpoint_and_contract_validation(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    config_dir = root / "config" / "runtime"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    run = runtime.create_lab_run(
        workspace_id="romer",
        project_id="Romer",
        lab_type="gmat",
        scenario_id="publish_validation_test",
        dataset_refs=["oracle.dataset"],
        parameter_set={"window": "2026-Q4"},
        engine="gmat",
    )
    runtime.complete_lab_run(
        run["run_id"],
        metrics={"delta_v": 4.2},
        outputs=[{"artifact": "gmat_manifest.json", "path": "generated/gmat_manifest.json"}],
    )
    package_dir = runtime.default_workspace_package_dir("Romer", workspace_id="romer", label="checkpoint_test")
    package = runtime.export_workspace_package(
        package_dir,
        workspace_id="romer",
        project_id="Romer",
        summary="Checkpoint validation package.",
        artifact_refs=[],
        metadata={"bridge": "test"},
    )

    checkpoint = package.get("publish_checkpoint") or {}
    assert checkpoint["expectation_count"] >= 1
    assert Path(package["files"]["publish_checkpoint"]).exists()
    assert Path(package["files"]["governed_bundle"]).exists()
    assert package["governed_bundle"]["bundle_shape_version"] == "1.0"
    assert package["governed_bundle"]["workspace_id"] == "romer"
    assert package["metadata"]["bridge"] == "test"
    assert package["metadata"]["publish_snapshot_contract"]["destination_root"] == str(package_dir.resolve())
    assert package["metadata"]["publish_snapshot_contract"]["destination_kind"] == "snapshot"
    assert package["metadata"]["publish_snapshot_contract"]["owner_floor"] == "Architect"
    assert package["metadata"]["publish_snapshot_contract"]["control_floor"] == "Architect"
    manifest = json.loads(Path(package["files"]["manifest"]).read_text())
    assert manifest["source_root"] == str(root.resolve())
    assert manifest["source_root_kind"] == "canonical_c_root"
    assert manifest["destination_root"] == str(package_dir.resolve())
    assert manifest["destination_kind"] == "snapshot"
    assert manifest["destination_root_kind"] == "snapshot_output"
    assert manifest["owner_floor"] == "Architect"
    assert manifest["control_floor"] == "Architect"
    assert manifest["overwrite_existing"] is True
    validation = validate_contract_payload("publish_manifest", json.loads(Path(package["files"]["manifest"]).read_text()))
    assert validation["valid"] is True


def test_workspace_action_carries_risk_rating_and_handoff_context(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    config_dir = root / "config" / "runtime"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.propose_workspace_action(
        "romer",
        "Romer",
        target_scope="TheConstruct",
        action_type="build_heliocentric_zoning",
        inputs={
            "summary": "Build zoning from approved empirical shortlist.",
            "artifact_refs": [{"kind": "dataset", "ref": "dataset_001"}],
        },
        requires_approval=False,
        source_floor="Neo",
        target_floor="TheConstruct",
        rationale="Prefer a bounded floor tool invocation before escalating to a full handoff.",
        prefer_handoff=False,
    )

    assert payload["risk_level"] == "execute"
    assert payload["execution_mode"] == "tool_first"
    assert payload["requires_approval"] is True
    assert payload["trace_id"]
    assert payload["handoff_context"]["source_floor"] == "Neo"
    assert payload["handoff_context"]["target_floor"] == "TheConstruct"
    assert payload["handoff_context"]["artifact_refs"][0]["ref"] == "dataset_001"
    assert Path(default_action_ledger_path(root)).exists()

    review_payload = runtime.propose_workspace_action(
        "romer",
        "Romer",
        target_scope="Oracle",
        action_type="operator_brief",
        inputs={"summary": "Prepare a bounded review brief."},
        requires_approval=True,
        source_floor="Neo",
        target_floor="Oracle",
        rationale="Safe approval path for approval-ledger verification.",
        prefer_handoff=False,
    )
    approved = runtime.approve_workspace_action("romer", "Romer", review_payload["action_id"], audit_ref="audit://approval")
    assert approved["approval_state"] == "approved"
    assert approved["trace_id"] == review_payload["trace_id"]
    assert Path(default_approval_ledger_path(root)).exists()


def test_knowns_declassification_audit_flags_duplicate_alignment_notes(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    notes_dir = root / "Mounted" / "Doctrine"
    (notes_dir / "set_a").mkdir(parents=True, exist_ok=True)
    (notes_dir / "set_b").mkdir(parents=True, exist_ok=True)
    duplicate_text = (
        "Romer alignment note. Achilles governs operator flow. "
        "This doctrine handoff keeps zoning, GMAT, and publish behavior aligned."
    )
    (notes_dir / "set_a" / "alignment_note.md").write_text(duplicate_text, encoding="utf-8")
    (notes_dir / "set_b" / "alignment_note.md").write_text(duplicate_text, encoding="utf-8")
    _write_knowns_runtime_config(root, notes_dir)

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    runtime.write_knowns_registry()
    runtime.write_knowns_proofing_queue()
    audit = runtime.write_knowns_declassification_audit()

    assert audit["candidate_count"] >= 1
    assert audit["duplicate_group_count"] >= 1
    assert Path(default_knowns_declassification_audit_path(root)).exists()


def test_knowns_registry_and_queue_use_proofed_definitions(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    notes_dir = root / "Mounted" / "Doctrine"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "alignment_note.md").write_text(
        "Achilles governs the operator model. Oracle proofs definitions before reuse. "
        "The Construct uses empirical anchors for zoning and GMAT-ready batches.",
        encoding="utf-8",
    )
    _write_knowns_runtime_config(root, notes_dir)

    runtime = LightSpeedRuntime(root=root)
    registry = runtime.write_knowns_registry()
    queue = runtime.write_knowns_proofing_queue()

    assert registry["themes"]
    first_theme = registry["themes"][0]
    assert first_theme["proofed_definition"]
    assert first_theme["operator_notes"]
    assert first_theme["source_label"]

    assert queue["entries"]
    first_entry = queue["entries"][0]
    assert first_entry["source_label"]
    assert first_entry["proofed_definition"]
    assert first_entry["definition_basis"] in {"curated_oracle_dictionary", "theme_summary"}
    assert first_entry["definition_confidence"] in {"high", "medium"}


def test_smith_router_queues_and_completes_construct_job(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")

    runtime = LightSpeedRuntime(root=root)
    runtime.write_execution_queues()
    queued = runtime.queue_smith_job(
        job_type="heliocentric_zoning",
        source_floor="TheConstruct",
        workspace_id="romer",
        project_id="Romer",
        payload={"scenario_id": "heliocentric_zoning_grid"},
        note="Queued in runtime package test.",
    )

    assert queued["queued"] is True
    assert queued["target_floor"] == "TheConstruct"

    completed = runtime.complete_smith_job(
        queued["job_id"],
        result_ref="Z Axis/Z0_TheConstruct/data/labs/test_run",
        note="Completed in runtime package test.",
    )
    assert completed["updated"] is True

    router = runtime.smith_router_state()
    job = next(item for item in router["jobs"] if item["job_id"] == queued["job_id"])
    assert job["status"] == "completed"
    assert Path(default_smith_router_path(root)).exists()
    assert router["owner_floor"] == "Smith"
    assert router["control_floor"] == "Architect"
    assert router["router_root_kind"] == "canonical_smith_operations_root"


def test_assimilate_external_roots_rehomes_outer_sources_and_rewrites_config(tmp_path: Path) -> None:
    outer = tmp_path / "LightSpeed Consolidated"
    root = outer / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    docs = outer / "2026 Documents"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "README_Export_Package.md").write_text("docs", encoding="utf-8")
    notebook = docs / "Notebook" / "NoteBookLM"
    notebook.mkdir(parents=True, exist_ok=True)
    (notebook / "Achilles Protocol v1.1.md").write_text("achilles", encoding="utf-8")

    processor = outer / "ACHILLES_FileProcessor_v2.0.0"
    processor.mkdir(parents=True, exist_ok=True)
    (processor / "README.md").write_text("processor", encoding="utf-8")

    library = outer / "Library"
    (library / "Empirical Data").mkdir(parents=True, exist_ok=True)
    (library / "Empirical Data" / "asteroids.json").write_text("{}", encoding="utf-8")
    (library / "web Calculators").mkdir(parents=True, exist_ok=True)
    (library / "web Calculators" / "index.json").write_text("{}", encoding="utf-8")
    (library / "Physics").mkdir(parents=True, exist_ok=True)
    (library / "Physics" / "physics.pdf").write_text("physics", encoding="utf-8")
    (library / "root_note.txt").write_text("library", encoding="utf-8")

    ref_library = outer / "LightSpeed_Reference_Library"
    ref_library.mkdir(parents=True, exist_ok=True)
    (ref_library / "reference.pdf").write_text("ref", encoding="utf-8")

    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
                {
                    "sources": [
                        {
                            "source_id": "docs_2026_master",
                            "root_path": str(docs),
                            "source_type": "master_doctrine_bundle",
                            "classification": "canonical",
                            "floor_owner": "Oracle",
                            "workspace_tags": ["romer"],
                            "project_tags": ["Romer"],
                            "trusted_documents": ["README_Export_Package"],
                            "extractors": ["text"],
                        },
                        {
                            "source_id": "notebooklm_2026",
                            "root_path": str(notebook),
                            "source_type": "doctrine_export",
                            "classification": "canonical",
                            "floor_owner": "Oracle",
                            "workspace_tags": ["romer"],
                            "project_tags": ["Romer"],
                            "trusted_documents": ["Achilles Protocol v1.1"],
                            "extractors": ["text"],
                        },
                        {
                            "source_id": "achilles_fileprocessor_archive",
                            "root_path": str(processor),
                            "source_type": "ingestion_tool_archive",
                            "classification": "archive",
                            "floor_owner": "Smith",
                            "workspace_tags": ["achilles"],
                            "project_tags": ["Achilles"],
                            "trusted_documents": ["README"],
                            "extractors": ["text"],
                        },
                        {
                            "source_id": "library_empirical_data",
                            "root_path": str(library / "Empirical Data"),
                            "source_type": "empirical_dataset_bundle",
                            "classification": "reference",
                            "floor_owner": "TheConstruct",
                            "workspace_tags": ["romer"],
                            "project_tags": ["Romer"],
                            "trusted_documents": ["asteroids"],
                            "extractors": ["json"],
                        },
                        {
                            "source_id": "library_calculators",
                            "root_path": str(library / "web Calculators"),
                            "source_type": "calculator_library",
                            "classification": "reference",
                            "floor_owner": "TheConstruct",
                            "workspace_tags": ["romer"],
                            "project_tags": ["Romer"],
                            "trusted_documents": ["index"],
                            "extractors": ["json"],
                        },
                        {
                            "source_id": "lightspeed_reference_library",
                            "root_path": str(ref_library),
                            "source_type": "reference_library",
                            "classification": "reference",
                            "floor_owner": "Oracle",
                            "workspace_tags": ["romer"],
                            "project_tags": ["Romer"],
                            "trusted_documents": ["reference"],
                            "extractors": ["pdf"],
                        },
                    ]
                }
            ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    payload = runtime.assimilate_external_roots()

    assert payload["moved_count"] >= 4
    assert Path(payload["config_path"]).exists()
    config = json.loads(Path(payload["config_path"]).read_text(encoding="utf-8"))
    ids = {item["source_id"]: item["root_path"] for item in config["sources"]}
    assert "library_reference_general" in ids
    assert Path(ids["docs_2026_master"]).exists()
    assert Path(ids["library_empirical_data"]).exists()
    assert Path(ids["library_calculators"]).exists()
    assert Path(ids["lightspeed_reference_library"]).exists()
    assert not docs.exists()
    assert not processor.exists()
    assert not ref_library.exists()



def test_operator_simulation_context_builds_recursive_priority_queue(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime_dir = root / "config" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    doctrine_dir = tmp_path / "NoteBookLM"
    doctrine_dir.mkdir(parents=True, exist_ok=True)
    (doctrine_dir / "Achilles Protocol v1.1.md").write_text(
        "Achilles is the governed operator. Cognigrex is the swarm body.",
        encoding="utf-8",
    )
    empirical_root = tmp_path / "Empirical Data"
    (empirical_root / "Asteroid & Solar System Archive").mkdir(parents=True, exist_ok=True)
    (empirical_root / "Asteroid_Strategic_Mapping_Base_withRocks.xlsx").write_text("sheet", encoding="utf-8")
    (empirical_root / "Asteroid & Solar System Archive" / "asteroids.json").write_text("{}", encoding="utf-8")

    (runtime_dir / "runtime_reservoirs.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "notebooklm_2026",
                        "root_path": str(doctrine_dir),
                        "source_type": "doctrine_export",
                        "classification": "canonical",
                        "floor_owner": "Oracle",
                        "workspace_tags": ["romer", "achilles"],
                        "project_tags": ["Romer", "Achilles"],
                        "trusted_documents": ["Achilles Protocol v1.1"],
                        "extractors": ["text"],
                    },
                    {
                        "source_id": "library_empirical_data",
                        "root_path": str(empirical_root),
                        "source_type": "empirical_dataset_bundle",
                        "classification": "reference",
                        "floor_owner": "TheConstruct",
                        "workspace_tags": ["romer", "physicslab"],
                        "project_tags": ["Romer", "GMAT", "PhysicsLab"],
                        "trusted_documents": ["Asteroid_Strategic_Mapping_Base_withRocks", "asteroids.json"],
                        "extractors": ["json", "xlsx"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    runtime.write_empirical_catalog()
    context = runtime.operator_simulation_context("romer", "Romer", query="asteroid zoning", limit=5)

    assert context["scenario_id"] == "heliocentric_zoning_grid"
    assert len(context["priority_queue"]) == 5
    assert context["priority_queue"][0]["priority"] == 1
    assert context["empirical_headline_count"] >= 1
    assert len(context["dataset_labels"]) >= 1


def test_simulation_presets_are_derived_from_empirical_roles(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataset_dir = tmp_path / "Empirical Data"
    (dataset_dir / "Asteroid & Solar System Archive").mkdir(parents=True, exist_ok=True)
    (dataset_dir / "Asteroid_Strategic_Mapping_Base_withRocks.xlsx").write_text("sheet", encoding="utf-8")
    (dataset_dir / "Asteroid & Solar System Archive" / "asteroids.json").write_text("{}", encoding="utf-8")
    _write_empirical_runtime_config(root, dataset_dir)

    runtime = LightSpeedRuntime(root=root)
    runtime.register_configured_sources()
    payload = runtime.write_simulation_presets()

    assert default_simulation_presets_path(root).exists()
    assert payload["reference_project"] == "Romer"
    assert payload["preset_count"] == 4
    preset_ids = {item["preset_id"] for item in payload["presets"]}
    assert "romer_heliocentric_zoning" in preset_ids
    zoning = next(item for item in payload["presets"] if item["preset_id"] == "romer_heliocentric_zoning")
    assert zoning["primary_dataset_role"] == "macro_mapping"
    assert zoning["default_parameters"]["top_targets"] == 25


def test_resumable_workflow_state_tracks_smith_jobs(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)
    runtime.queue_smith_job(
        job_type="heliocentric_zoning",
        source_floor="TheConstruct",
        workspace_id="romer",
        project_id="Romer",
        payload={"scenario_id": "heliocentric_zoning_grid"},
        note="test resumable state",
    )

    payload = runtime.write_resumable_workflow_state()

    assert default_workflow_state_path(root).exists()
    assert payload["owner_floor"] == "Smith"
    assert payload["workflow_count"] >= 1
    assert payload["resumable_count"] >= 1
    first = payload["workflows"][0]
    assert first["resume_token"].startswith("resume_")
    assert "awaiting_dispatch" in first["checkpoint_order"]
    assert first["resume_policy"]["requires_approval"] is True


def test_romer_reference_path_records_end_to_end_contract(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    config_dir = root / "config" / "runtime"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "runtime_reservoirs.json").write_text(json.dumps({"sources": []}), encoding="utf-8")
    runtime = LightSpeedRuntime(root=root)

    payload = runtime.write_romer_reference_path()

    assert default_romer_reference_path(root).exists()
    assert payload["workspace_id"] == "romer"
    assert payload["project_id"] == "Romer"
    assert len(payload["end_to_end_steps"]) == 6
    assert "Workspace" in payload["operating_modes"]
    assert payload["publish_bundle_shape"] == "1.0"


def test_dataindex_reduction_moves_superseded_and_generated_files(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    dataindex = root / "dataindex"
    dataindex.mkdir(parents=True)
    (dataindex / "05_FINALIZATION_BACKLOG_50.md").write_text("old backlog", encoding="utf-8")
    (dataindex / "06_FINALIZATION_BACKLOG_50.md").write_text("new backlog", encoding="utf-8")
    (dataindex / "06_ROOT_CLASSIFICATION_MAP.md").write_text("old map", encoding="utf-8")
    (dataindex / "07_ROOT_CLASSIFICATION_MAP.md").write_text("new map", encoding="utf-8")
    (dataindex / "00_DIRECTORY_TREE.txt").write_text("generated tree", encoding="utf-8")
    runtime = LightSpeedRuntime(root=root)

    payload = runtime.dataindex_reduction(apply=True)

    assert default_dataindex_reduction_path(root).exists()
    assert payload["moved_count"] == 3
    assert not (dataindex / "05_FINALIZATION_BACKLOG_50.md").exists()
    assert not (dataindex / "06_ROOT_CLASSIFICATION_MAP.md").exists()
    assert not (dataindex / "00_DIRECTORY_TREE.txt").exists()
    assert (root / "Z Axis" / "Z-4_Merovingian" / "data" / "reports" / "dataindex_archive" / "05_FINALIZATION_BACKLOG_50.md").exists()
    assert (root / "Z Axis" / "Z-4_Merovingian" / "data" / "reports" / "dataindex_generated" / "00_DIRECTORY_TREE.txt").exists()


def test_finalization_overview_and_execution_control_are_operator_summaries(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)
    runtime.write_execution_queues()
    runtime.advance_execution_queue("SF-01", note="test queue progress")
    runtime.queue_smith_job(
        job_type="cleanup_review",
        source_floor="Architect",
        workspace_id="romer",
        project_id="Romer",
        payload={"target": "finalization"},
        note="test execution control",
    )

    overview = runtime.write_finalization_overview()
    control = runtime.write_execution_control()

    assert default_finalization_overview_path(root).exists()
    assert default_execution_control_path(root).exists()
    assert overview["owner_floor"] == "Merovingian"
    assert overview["control_floor"] == "Architect"
    assert overview["status"]["total_actions"] == 81
    assert overview["status"]["activity_owner_floor"] == "Merovingian"
    assert overview["status"]["activity_control_floor"] == "Architect"
    assert "execution_queues" in overview["source_reports"]
    assert "closure_readiness" in overview["source_reports"]
    assert "activity_tables" in overview["source_reports"]
    assert control["owner_floor"] == "Architect"
    assert control["completion"]["total_actions"] == 81
    assert control["lanes"]
    assert control["operator_controls"]
    assert control["workflow_controls"]["resumable_count"] >= 1


def test_activity_tables_compact_runtime_logs_and_governance_ledgers(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)
    runtime.log_event(
        "publish_knowns_registry",
        "Updated Oracle knowns registry.",
        source="Oracle",
        payload={"owner_floor": "Oracle", "path": "Z Axis/Z-2_Oracle/data/knowns/knowns_registry.json"},
    )
    append_action_ledger(
        root,
        {
            "event_id": "action-activity-1",
            "recorded_at": "2026-04-08T00:00:00+00:00",
            "source_floor": "Neo",
            "target_floor": "TheConstruct",
            "action_id": "ACT-001",
            "risk": "execute",
            "trace_id": "trace-001",
        },
    )
    append_approval_ledger(
        root,
        {
            "event_id": "approval-activity-1",
            "recorded_at": "2026-04-08T00:01:00+00:00",
            "source_floor": "Architect",
            "target_floor": "Neo",
            "action_id": "APR-001",
            "risk": "publish",
            "trace_id": "trace-002",
        },
    )

    payload = runtime.write_activity_tables()

    assert default_activity_tables_path(root).exists()
    assert default_activity_db_path(root).exists()
    assert payload["owner_floor"] == "Merovingian"
    assert payload["summary"]["owner_floor"] == "Merovingian"
    assert payload["summary"]["control_floor"] == "Architect"
    assert payload["summary"]["compaction_policy"] == "latest_signal_per_floor_category_stream"
    assert payload["summary"]["source_evidence"] == "weekly_jsonl_plus_sqlite_operational_events"
    assert payload["database_path"] == str(default_activity_db_path(root))
    assert default_activity_db_path(root) == default_action_ledger_path(root)
    assert payload["source_line_counts"]["weekly_log"] >= 1
    assert payload["source_line_counts"]["telemetry"] >= 1
    assert payload["source_line_counts"]["action_ledger"] == 1
    assert payload["source_line_counts"]["approval_ledger"] == 1
    assert payload["summary"]["total_source_events"] >= 4
    assert payload["summary"]["floor_counts"]["Oracle"] >= 1
    assert any(row["stream"] == "action_ledger" for row in payload["activity_rows"])
    with sqlite3.connect(default_activity_db_path(root)) as connection:
        row_count = connection.execute("SELECT COUNT(*) FROM activity_events").fetchone()[0]
        oracle_count = connection.execute("SELECT COUNT(*) FROM activity_events WHERE floor = 'Oracle'").fetchone()[0]
        summary_rows = connection.execute("SELECT COUNT(*) FROM activity_summary").fetchone()[0]
    assert row_count == payload["summary"]["table_rows"]
    assert oracle_count >= 1
    assert summary_rows == 10


def test_governance_ledgers_classify_action_classes_and_floor_ownership(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"

    action = append_action_ledger(
        root,
        {
            "source_floor": "Neo",
            "target_floor": "Architect",
            "action_type": "publish_snapshot",
            "risk": "publish",
        },
    )
    approval = append_approval_ledger(
        root,
        {
            "source_floor": "Architect",
            "target_floor": "Neo",
            "action_type": "build_heliocentric_zoning",
            "risk": "execute",
        },
    )

    assert action["action_class"] == "publish"
    assert action["ledger_floor"] == "Merovingian"
    assert action["ledger_kind"] == "action"
    assert approval["action_class"] == "execute"
    assert approval["ledger_floor"] == "Architect"
    assert approval["ledger_kind"] == "approval"


def test_activity_tables_preserve_floor_signal_when_recent_events_are_noisy(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)
    runtime.log_event(
        "knowns_registry",
        "Updated Oracle knowns registry.",
        source="Oracle",
        payload={"owner_floor": "Oracle", "path": "Z Axis/Z-2_Oracle/data/knowns/knowns_registry.json"},
    )
    for index in range(20):
        runtime.log_event(
            "finalization_overview",
            f"Wrote consolidated finalization overview {index}.",
            source="Merovingian",
            payload={"owner_floor": "Merovingian", "path": f"reports/finalization_{index}.json"},
        )

    payload = runtime.write_activity_tables(max_rows=8)

    assert payload["summary"]["table_rows"] == 8
    assert payload["summary"]["floor_counts"]["Oracle"] >= 1
    assert payload["summary"]["floor_counts"]["Merovingian"] >= 1
    assert any(row["category"] == "knowns_registry" for row in payload["activity_rows"])


def test_ui_experience_alignment_translates_original_pdf_into_bento_rules(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)

    payload = runtime.write_ui_experience_alignment()

    output = default_ui_experience_alignment_path(root)
    assert output.exists()
    assert payload["owner_floor"] == "Trinity"
    assert payload["source_page_count"] == 14
    assert {item["mode"] for item in payload["content_plan"]} == {
        "Workspace",
        "Operator",
        "Review",
        "Holospace",
        "Publish",
        "Settings",
    }
    assert any("WASD" in rule and "Holospace" in rule for rule in payload["bento_translation_rules"])
    assert any("Ctrl+S" in rule for rule in payload["bento_translation_rules"])
    assert any("modal" in rule.lower() or "toggle" in rule.lower() for rule in payload["bento_translation_rules"])
    assert payload["fixed_panel_wall"]["approx_width_meters"] == 1.5
    assert payload["project_bento_model"]["double_click"] == "open full-screen editor/viewer or attach file if the tile has no file yet"
    assert "uploaded_environment_reference" in payload["background_control_model"]["editable_inputs"]
    assert "UX-05" in payload["queue_alignment"]["completed_by_this_contract"]


def test_ui_polish_contract_covers_final_bento_refinement_tasks(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)

    payload = runtime.write_ui_polish_contract()

    assert default_ui_polish_contract_path(root).exists()
    assert payload["owner_floor"] == "Trinity"
    assert payload["motion_policy"]["decorative_motion"] == "disabled_by_default"
    assert "Ctrl+S opens search." in payload["shortcut_hints"]
    assert "Ctrl+Shift+S opens visible settings." in payload["shortcut_hints"]
    assert payload["floor_ownership"]["Neo"].startswith("Achilles")
    assert payload["page_pattern"]["actions"].startswith("group by")
    assert payload["bento_project_wall"]["artifact_clicks"].startswith("single click")
    assert "uploaded_images" in payload["theme_control"]["editable_backgrounds"]
    assert set(payload["completed_by_this_contract"]) == {"UX-13", "UX-14", "UX-15", "UX-16", "UX-17", "UX-18", "UX-19"}


def test_operator_os_contract_and_it_dictionary_capture_final_interaction_model(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)

    operator_os = runtime.write_operator_os_contract()
    dictionary = runtime.write_it_dictionary()
    definitions = runtime.write_oracle_definition_library()

    assert default_operator_os_contract_path(root).exists()
    assert default_it_dictionary_path(root).exists()
    assert operator_os["main_interface"]["name"] == "Smart Bento Project Wall"
    assert operator_os["controls"]["search"] == "Ctrl+S"
    assert operator_os["controls"]["settings"] == "Ctrl+Shift+S"
    assert "uploaded_environment_reference" in operator_os["backgrounds"]["editable"]
    assert operator_os["oracle_ingestion_handoff"]["original_file_policy"].startswith("Oracle receives")

    assert dictionary["dictionary"] == "IT"
    assert dictionary["term_count"] >= 25
    terms = {item["term_id"]: item for item in dictionary["terms"]}
    assert terms["partial_object_data"]["shorthand"] == "POD"
    assert terms["handoff_queue"]["owner_floor"] == "Smith"
    assert "B" in dictionary["a_to_z"]
    assert definitions["dictionary_categories"]["IT"]["term_count"] == dictionary["term_count"]


def test_romer_web_integration_contract_maps_public_site_and_drive_feeds(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)

    payload = runtime.write_romer_web_integration()
    routes = {item["route"]: item for item in payload["website_routes"]}
    drive_sources = {item["id"]: item for item in payload["drive_sources"]}
    sheets = {item["id"]: item for item in payload["spreadsheet_feeds"]}

    assert default_romer_web_integration_path(root).exists()
    assert payload["owner_floor"] == "Oracle"
    assert routes["/operations/w1"]["workspace"] == "W1"
    assert routes["/operations/w6"]["role"].endswith("compatibility facade")
    assert routes["/w5/data"]["observed_status"] == "requires_auth_401"
    assert payload["squarespace_embed_source"]["id"] == "1wLNW2cC-vQ1ZTzNmgGQiSFE0wGp_dvupCW1ZGBtT_yw"
    assert payload["squarespace_embed_source"]["copy_cell"] == "01_One_Cell_Embed!A10"
    assert payload["squarespace_embed_source"]["gate"] == "COMP2_STAGED_WAITING_ON_COMP1"
    assert len(payload["squarespace_routes"]) == 31
    assert any(item["route"] == "/ls-go/handoff" for item in payload["squarespace_routes"])
    assert any(item["route"] == "/tools/calculators" for item in payload["squarespace_routes"])
    assert all(str(item["route"]).startswith("/") for item in payload["squarespace_routes"])
    assert len(payload["squarespace_implementation_log"]) == 8
    assert payload["brand_tokens"]["romer_gold"] == "#C9A24A"
    assert drive_sources["1clPyKU1C_Prd-a4g-Cbl2RZQybLL2oag"]["observed_status"] == "accessible"
    assert "Empirical Data" in drive_sources["1clPyKU1C_Prd-a4g-Cbl2RZQybLL2oag"]["observed_children"]
    assert drive_sources["1PkXMyv26BBvvUbxShTRMTwhnEaK_a1qb"]["queue_contract"]["id"] == "future_lightspeed_go_drive_queue"
    assert drive_sources["1PkXMyv26BBvvUbxShTRMTwhnEaK_a1qb"]["queue_contract"]["observed_status"] == "workbook_materialized"
    assert sheets["1POCTGwSyaznMCO-7rA79wNRWT7rReSjOsNx-CLn5u5E"]["title"] == "Website Logs"
    assert "Schema Dictionary" in sheets["1POCTGwSyaznMCO-7rA79wNRWT7rReSjOsNx-CLn5u5E"]["tabs_observed"]
    assert sheets["1GOzjF5BESSTWDqxi1hpGIk4a5R2kyrEY6EUeYN3vm9M"]["observed_status"].startswith("permission_denied")
    assert sheets["1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM"]["title"] == "LS_GO_Queue_2026_07_07"
    assert "Phone Tasks" in sheets["1f5i4V3FshYHkztv3_HAg0ZofUl0sdcJZcwrlesUlCfM"]["tabs_observed"]
    assert [item["id"] for item in payload["drive_queue_contracts"]] == ["future_lightspeed_go_drive_queue"]
    assert payload["handoff_policy"]["publish"].startswith("Architect publishes")


def test_bridge_health_contract_drives_trinity_bento_status_tile(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)
    runtime.write_romer_web_integration()

    payload = runtime.write_bridge_health()

    assert default_bridge_health_path(root).exists()
    assert payload["owner_floor"] == "Trinity"
    assert payload["walkthrough_ready"] is True
    assert payload["overall_status"] == "ready_with_warnings"
    assert payload["public_routes"]["pass_count"] == payload["public_routes"]["required_count"]
    assert payload["dataspace_routes"]["pending_count"] == 8
    assert payload["squarespace_embed"]["source_workbook_id"] == "1wLNW2cC-vQ1ZTzNmgGQiSFE0wGp_dvupCW1ZGBtT_yw"
    assert payload["squarespace_embed"]["unconfirmed_count"] == 8
    assert payload["squarespace_embed"]["partial_seen_routes"] == ["/ls-go/handoff"]
    assert payload["drive_sources"]["pending"] == []
    assert payload["spreadsheet_feeds"]["pending"] == ["1GOzjF5BESSTWDqxi1hpGIk4a5R2kyrEY6EUeYN3vm9M"]
    assert payload["drive_queue_contracts"]["workbook_materialized"] == ["future_lightspeed_go_drive_queue"]
    assert payload["bento_tile"]["id"] == "romer_bridge_health"
    assert payload["bento_tile"]["widget_type"] == "status"


def test_operations_manager_lists_bridge_health_workspace() -> None:
    root = Path(__file__).resolve().parents[1]
    module_path = root / "Z Axis" / "Z+3_Trinity" / "ui" / "operations_manager_panel.py"
    spec = importlib.util.spec_from_file_location("operations_manager_panel_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    bridge_workspaces = module.list_workspaces(tags=["bridge"])
    assert bridge_workspaces
    bridge = bridge_workspaces[0]
    assert bridge["workspace_id"] == "LS-BRIDGE-HEALTH"
    assert bridge["widget_type"] == "bento.status"
    assert module.is_readonly(bridge) is True
    assert "LS-BRIDGE-HEALTH" in module.render_embed_snippet(bridge)


def test_walkthrough_readiness_contract_holds_publish_until_review(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    runtime = LightSpeedRuntime(root=root)
    runtime.write_operator_os_contract()
    runtime.write_ui_experience_alignment()
    runtime.write_ui_polish_contract()
    runtime.write_romer_web_integration()
    runtime.write_bridge_health()

    payload = runtime.write_walkthrough_readiness()
    gates = {gate["gate_id"]: gate for gate in payload["gates"]}

    assert default_walkthrough_readiness_path(root).exists()
    assert payload["owner_floor"] == "Architect"
    assert payload["walkthrough_ready"] is True
    assert payload["overall_status"] == "walkthrough_ready_with_warnings"
    assert gates["WT-01"]["status"] == "pass"
    assert gates["WT-06"]["status"] == "warn"
    assert gates["WT-09"]["status"] == "hold"
    assert "Smart Bento Project Wall" in payload["run_of_show"][1]


def test_route_probe_report_supports_fake_fetcher_without_network(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    routes = [
        {
            "route": "/operations",
            "url": "https://example.test/operations",
            "owner_floor": "Smith",
            "workspace": "Operations",
            "observed_status": "public_200",
            "title": "Operations",
        },
        {
            "route": "/w1/data",
            "url": "https://example.test/w1/data",
            "owner_floor": "Smith",
            "workspace": "W1",
            "observed_status": "connection_closed",
            "title": "W1 Data",
        },
    ]

    def fake_fetch(url: str, timeout: float) -> dict:
        if url.endswith("/operations"):
            return {"actual_status": 200, "probe_status": "http_ok", "title": "Operations"}
        return {"actual_status": None, "probe_status": "connection_error", "error": "closed"}

    payload = write_route_probe_report(root, routes=routes, fetcher=fake_fetch)

    assert default_route_probe_report_path(root).exists()
    assert payload["status"] == "public_pass_data_warnings"
    assert payload["public_route_ok_count"] == 1
    assert payload["data_route_ok_count"] == 0
    assert payload["failure_count"] == 1
    assert build_route_probe_report(root, routes=routes, fetcher=fake_fetch)["results"][0]["ok"] is True


def test_generated_layout_does_not_recreate_flat_compatibility_root(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"

    paths = ensure_generated_layout(root)

    assert paths["active_generated_root"].endswith("data\\generated") or paths["active_generated_root"].endswith("data/generated")
    assert not active_generated_root(root).exists()
    assert (root / "Z Axis" / "Z-4_Merovingian" / "data" / "runtime_exports").exists()


def test_core_paths_keep_generated_aliases_floor_native() -> None:
    root = Path(__file__).resolve().parents[1]
    module_path = root / "Z Axis" / "Z-4_Merovingian" / "core" / "config" / "paths.py"
    spec = importlib.util.spec_from_file_location("lightspeed_core_paths_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.GENERATED_DATA_ROOT == module.MEROVINGIAN_DATA
    assert module.GENERATED_LOGS == module.MEROVINGIAN_DATA / "logs"
    assert module.GENERATED_RUNTIME_EXPORTS == module.MEROVINGIAN_DATA / "runtime_exports"
    assert module.GENERATED_PUBLISH == module.ARCHITECT_ROOT / "data" / "publish"
    assert module.GENERATED_INGESTION_ROOT == module.ORACLE_ROOT / "data" / "ingestion"
    assert "data/generated" not in module.GENERATED_LOGS.as_posix()


def test_project_workspace_package_exports_active_construct_contract(monkeypatch) -> None:
    root = Path(__file__).resolve().parents[1]
    z_axis = root / "Z Axis"
    merovingian = z_axis / "Z-4_Merovingian"
    monkeypatch.syspath_prepend(str(root))
    monkeypatch.syspath_prepend(str(z_axis))
    monkeypatch.syspath_prepend(str(merovingian))

    module = importlib.import_module("core.project_workspace")

    assert module.__version__ == "5.1.2"
    assert module.ComponentPuller is not None
    assert module.WorkspaceSphericalLayout is not None
    assert module.SchemaValidator is not None
    assert callable(module.create_component_puller)
    assert callable(module.create_workspace_layout)
    assert callable(module.create_schema_validator)
    assert "create_component_puller" in module.__all__
    assert "create_workspace_layout" in module.__all__
    assert "create_schema_validator" in module.__all__


def test_trinity_settings_manager_defaults_to_floor_owned_paths(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    module_path = root / "Z Axis" / "Z+3_Trinity" / "ui" / "settings_manager.py"
    spec = importlib.util.spec_from_file_location("trinity_settings_manager_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert module.SETTINGS_FILE == root / "Z Axis" / "Z+3_Trinity" / "settings" / "settings.json"
    assert module.CANONICAL_LOG_FILE == root / "Z Axis" / "Z-4_Merovingian" / "data" / "logs" / "main.log"
    assert module.CANONICAL_BACKUP_DIR == root / "Z Axis" / "Z-4_Merovingian" / "data" / "backups"

    manager = module.SettingsManager(config_path=tmp_path / "settings.json")

    assert manager.settings.app_version == "5.1.2"
    assert manager.settings.ollama_enabled is True
    assert manager.settings.ollama_model == "qwen3:8b"
    assert manager.settings.apis_enabled["ollama"] is True
    assert Path(manager.settings.db_path) == root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"
    assert Path(manager.settings.projects_root) == root / "Z Axis" / "Z+1_Architect" / "projects"
    assert Path(manager.settings.log_file_path) == root / "Z Axis" / "Z-4_Merovingian" / "data" / "logs" / "main.log"
    assert Path(manager.settings.backup_directory) == root / "Z Axis" / "Z-4_Merovingian" / "data" / "backups"


def test_trinity_settings_manager_preserves_forward_compatible_contract_fields(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    module_path = root / "Z Axis" / "Z+3_Trinity" / "ui" / "settings_manager.py"
    spec = importlib.util.spec_from_file_location(
        "trinity_settings_manager_contract_test", module_path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    config_path = tmp_path / "settings.json"
    original = {
        "app_version": "5.1.2",
        "config_schema_version": "2026.04.finalization",
        "db_path": "Z Axis/Z-4_Merovingian/data/db/lightspeed_unified.db",
        "log_file_path": "Z Axis/Z-4_Merovingian/data/logs/main.log",
        "activity_table_path": "Z Axis/Z-4_Merovingian/data/db/lightspeed_unified.db",
        "approval_ledger_path": "Z Axis/Z+1_Architect/data/approval_ledger.jsonl",
        "future_contract": {"enabled": True},
    }
    config_path.write_text(json.dumps(original), encoding="utf-8")

    manager = module.SettingsManager(config_path=config_path)
    persisted = json.loads(config_path.read_text(encoding="utf-8"))

    assert manager.settings.config_schema_version == "2026.04.finalization"
    assert manager.settings.db_path.startswith("Z Axis/")
    assert persisted["activity_table_path"].startswith("Z Axis/Z-4_Merovingian/")
    assert persisted["approval_ledger_path"].startswith("Z Axis/Z+1_Architect/")
    assert persisted["future_contract"] == {"enabled": True}


def test_trinity_settings_dialog_defaults_to_floor_owned_settings_file(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    z_axis = root / "Z Axis"
    merovingian = z_axis / "Z-4_Merovingian"
    module_path = root / "Z Axis" / "Z+3_Trinity" / "components" / "settings_dialog.py"
    spec = importlib.util.spec_from_file_location("trinity_settings_dialog_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys_path_before = list(sys.path)
    try:
        sys.path[:0] = [str(root), str(z_axis), str(merovingian)]
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = sys_path_before

    module.TRINITY_SETTINGS = tmp_path / "settings"
    manager = module.SettingsManager()

    assert manager.config_path == tmp_path / "settings" / "settings_dialog.json"


def test_theme_designer_writes_theme_state_into_trinity_owned_roots(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    z_axis = root / "Z Axis"
    merovingian = z_axis / "Z-4_Merovingian"
    module_path = root / "Z Axis" / "Z+3_Trinity" / "components" / "theme_switcher.py"
    spec = importlib.util.spec_from_file_location("trinity_theme_switcher_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    sys_path_before = list(sys.path)
    try:
        sys.path[:0] = [str(root), str(z_axis), str(merovingian)]
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = sys_path_before

    module.TRINITY_THEMES = tmp_path / "themes"
    module.TRINITY_SETTINGS = tmp_path / "settings"
    module.messagebox.showinfo = lambda *args, **kwargs: None
    module.messagebox.showerror = lambda *args, **kwargs: None
    module.tk.simpledialog.askstring = lambda *args, **kwargs: "test-theme"

    designer = module.ThemeDesigner.__new__(module.ThemeDesigner)
    designer.current_theme = {"accent_cyan": "#00ffff"}
    designer.color_entries = {}
    designer.on_apply = None

    module.ThemeDesigner._save_theme(designer)
    module.ThemeDesigner._apply_theme(designer)

    assert (tmp_path / "themes" / "custom" / "test-theme.json").exists()
    assert (tmp_path / "settings" / "active_theme.json").exists()


def test_closure_readiness_audits_outer_container_without_recursive_sweep(tmp_path: Path) -> None:
    outer = tmp_path / "LightSpeed Consolidated"
    root = outer / "LightSpeed"
    root.mkdir(parents=True)
    queue_root = finalization_queue_root(root)
    queue_root.mkdir(parents=True, exist_ok=True)
    (queue_root / "execution_queues.json").write_text(
        json.dumps({"action_count": 81, "completed_count": 81, "pending_count": 0}),
        encoding="utf-8",
    )
    (outer / "empty.placeholder").write_text("", encoding="utf-8")
    (outer / ".idea").mkdir()
    runtime = LightSpeedRuntime(root=root)

    payload = runtime.write_closure_readiness()
    removed = runtime.remove_outer_zero_byte_placeholders()

    assert default_closure_readiness_path(root).exists()
    assert payload["outer_child_count"] == 3
    assert payload["readiness"]["queue_closed"] is True
    assert payload["readiness"]["outer_safe_remove_count"] == 1
    assert payload["readiness"]["outer_manual_review_count"] == 1
    assert payload["source_root_kind"] == "canonical_c_root"
    assert payload["destination_roots"]["architect_publish_snapshot_root"].endswith("Z+1_Architect\\data\\publish\\snapshot")
    assert not (outer / "empty.placeholder").exists()
    assert removed["removed"]
    assert removed["after"]["readiness"]["outer_safe_remove_count"] == 0


def _load_project_workspace_module(module_name: str, relative_path: str):
    import types

    root = Path(__file__).resolve().parents[1]
    z_axis = root / "Z Axis"
    merovingian = z_axis / "Z-4_Merovingian"
    module_path = root / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    original_core = sys.modules.get("core")
    original_workspace_package = sys.modules.get("core.project_workspace")
    original_module = sys.modules.get(module_name)

    core_package = sys.modules.setdefault("core", types.ModuleType("core"))
    core_package.__path__ = [str(merovingian / "core")]
    workspace_package = sys.modules.setdefault(
        "core.project_workspace",
        types.ModuleType("core.project_workspace"),
    )
    workspace_package.__path__ = [str(merovingian / "core" / "project_workspace")]
    sys.modules.pop(module_name, None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    sys_path_before = list(sys.path)
    try:
        sys.path[:0] = [str(root), str(z_axis), str(merovingian)]
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = sys_path_before
        if original_module is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = original_module
        if original_workspace_package is None:
            sys.modules.pop("core.project_workspace", None)
        else:
            sys.modules["core.project_workspace"] = original_workspace_package
        if original_core is None:
            sys.modules.pop("core", None)
        else:
            sys.modules["core"] = original_core
    return module


def test_project_workspace_package_exports_workspace_types_from_defining_module() -> None:
    package = _load_project_workspace_module(
        "core.project_workspace",
        "Z Axis/Z-4_Merovingian/core/project_workspace/__init__.py",
    )
    workspace_types = _load_project_workspace_module(
        "core.project_workspace.workspace_types",
        "Z Axis/Z-4_Merovingian/core/project_workspace/workspace_types.py",
    )

    assert package.WorkspaceType.__module__ == "core.project_workspace.workspace_types"
    assert package.WorkspaceStatus.__module__ == "core.project_workspace.workspace_types"
    assert set(package.WorkspaceType.__members__) == set(workspace_types.WorkspaceType.__members__)
    assert set(package.WorkspaceStatus.__members__) == set(workspace_types.WorkspaceStatus.__members__)


def test_project_workspace_create_workspace_uses_ascii_summary_output(tmp_path: Path) -> None:
    import io

    module = _load_project_workspace_module(
        "core.project_workspace.workspace_creator",
        "Z Axis/Z-4_Merovingian/core/project_workspace/workspace_creator.py",
    )
    creator = module.ProjectWorkspaceCreator(base_path=tmp_path)
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="cp1252", newline="")
    original_stdout = sys.stdout
    try:
        sys.stdout = stream
        workspace = creator.create_workspace("Smoke", module.WorkspaceType.RESEARCH)
        stream.flush()
    finally:
        sys.stdout = original_stdout

    output = buffer.getvalue().decode("cp1252")
    assert workspace.workspace_path is not None
    assert "-> Path:" in output
    assert "→" not in output


def test_project_workspace_apply_template_copies_existing_sample_file(tmp_path: Path) -> None:
    module = _load_project_workspace_module(
        "core.project_workspace.workspace_creator",
        "Z Axis/Z-4_Merovingian/core/project_workspace/workspace_creator.py",
    )
    creator = module.ProjectWorkspaceCreator(base_path=tmp_path)
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)
    workspace = module.ProjectWorkspace(
        id="ws_test",
        name="Test",
        workspace_type=module.WorkspaceType.RESEARCH,
        workspace_path=workspace_root,
        data_path=workspace_root / "data",
        output_path=workspace_root / "output",
    )
    template = module.WorkspaceTemplate(
        id="template_test",
        name="Template",
        workspace_type=module.WorkspaceType.RESEARCH,
        description="Test template",
        pre_configured_components=[],
        sample_files=["core/project_workspace/__init__.py"],
    )

    creator._apply_template(workspace, template)

    assert (workspace_root / "core" / "project_workspace" / "__init__.py").exists()


def test_project_workspace_registry_compatibility_extensions_match_workspace_contracts() -> None:
    component_puller = _load_project_workspace_module(
        "core.project_workspace.component_puller",
        "Z Axis/Z-4_Merovingian/core/project_workspace/component_puller.py",
    )
    registry = component_puller.ComponentRegistry()
    expected_memberships = {
        "data_analyzer": {"research"},
        "chart_renderer": {"research"},
        "gmat_launcher": {"engineering"},
        "raphael_engine": {"engineering"},
        "cognigrex_ai": {"analysis"},
        "knowledge_graph": {"analysis", "collaboration"},
        "mission_planner": {"simulation"},
        "workflow_designer": {"collaboration"},
        "physics_simulator": {"mission_planning"},
        "3d_visualization": {"mission_planning"},
    }

    for component_id, expected_values in expected_memberships.items():
        component = registry.get_component(component_id)
        assert component is not None, component_id
        compatible_values = {compatible.value for compatible in component.compatible_workspace_types}
        assert expected_values.issubset(compatible_values), component_id


def test_project_workspace_documentation_defaults_use_documentation_browser() -> None:
    workspace_types = _load_project_workspace_module(
        "core.project_workspace.workspace_types",
        "Z Axis/Z-4_Merovingian/core/project_workspace/workspace_types.py",
    )
    config = workspace_types.WORKSPACE_CONFIGS[workspace_types.WorkspaceType.DOCUMENTATION]

    assert "documentation_browser" in config.recommended_components
    assert "help_browser" not in config.recommended_components


def test_project_workspace_category_defaults_are_shared() -> None:
    component_puller = _load_project_workspace_module(
        "core.project_workspace.component_puller",
        "Z Axis/Z-4_Merovingian/core/project_workspace/component_puller.py",
    )
    category_positions = _load_project_workspace_module(
        "core.project_workspace.category_positions",
        "Z Axis/Z-4_Merovingian/core/project_workspace/category_positions.py",
    )
    workspace_creator = _load_project_workspace_module(
        "core.project_workspace.workspace_creator",
        "Z Axis/Z-4_Merovingian/core/project_workspace/workspace_creator.py",
    )

    puller = component_puller.ComponentPuller()
    metadata = component_puller.ComponentMetadata(
        component_id="category_test",
        name="Category Test",
        z_floor="Z-4_Merovingian",
        category="automation",
        capabilities=[],
        description="Test",
        compatible_workspace_types=[],
    )

    position = puller._auto_assign_position(metadata)
    expected = category_positions.CATEGORY_DEFAULT_POSITIONS["automation"]

    assert (position.theta, position.phi, position.depth) == (
        expected.theta,
        expected.phi,
        expected.depth,
    )
