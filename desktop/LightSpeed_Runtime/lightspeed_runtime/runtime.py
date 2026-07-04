from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.activity_tables import (
    default_activity_db_path,
    default_activity_tables_path,
    read_activity_tables,
    write_activity_tables,
)
from lightspeed_runtime.ai_settings import (
    ai_backend_summary,
    load_ai_settings,
    save_ai_settings,
)
from lightspeed_runtime.closure_readiness import (
    default_closure_readiness_path,
    read_closure_readiness,
    remove_outer_zero_byte_placeholders,
    write_closure_readiness,
)
from lightspeed_runtime.analytics_validation import (
    build_publish_checkpoint,
    default_bellcurve_overlay_path,
    default_table_validation_report_path,
    write_bellcurve_overlay,
    write_table_validation_report,
)
from lightspeed_runtime.achilles.operator import AchillesOperator
from lightspeed_runtime.assimilation import (
    assimilate_external_roots,
    build_assimilation_report,
    default_assimilation_migration_path,
    default_assimilation_report_path,
    default_external_root_assimilation_path,
    default_legacy_rehome_path,
    migrate_smart_floor_outputs,
    rehome_legacy_roots,
    write_assimilation_report,
)
from lightspeed_runtime.data_hygiene import (
    complete_archive_batch,
    default_archive_execution_state_path,
    default_archive_workflow_path,
    default_compaction_index_path,
    default_compaction_plan_path,
    default_summary_path,
    read_archive_execution_state,
    read_archive_workflow,
    read_compaction_plan,
    read_compaction_indexes,
    read_generated_data_summary,
    stage_archive_batch,
    write_archive_execution_state,
    write_archive_workflow,
    write_compaction_plan,
    write_compaction_indexes,
    write_generated_data_summary,
    write_yearly_rollups,
)
from lightspeed_runtime.ingestion import (
    default_ingestion_preparation_path,
    read_ingestion_preparation,
    write_ingestion_preparation,
)
from lightspeed_runtime.empirical import (
    default_empirical_catalog_path,
    read_empirical_catalog,
    write_empirical_catalog,
)
from lightspeed_runtime.entity_registry import (
    default_dataset_manifest_index_path,
    default_entity_registry_path,
    read_entity_registry,
    write_entity_registry,
)
from lightspeed_runtime.curated_tables import (
    default_curated_tables_index_path,
    read_curated_tables_index,
    write_curated_tables_index,
)
from lightspeed_runtime.dataset_catalog import (
    default_dataset_catalog_path,
    read_dataset_catalog_shell,
    write_dataset_catalog_shell,
)
from lightspeed_runtime.scientific_query import (
    default_scientific_query_path,
    execute_scientific_query,
    execute_tap_like_query,
    read_scientific_query_layer,
    write_scientific_query_layer,
)
from lightspeed_runtime.interchange import (
    default_columnar_handoff_path,
    read_columnar_handoff,
    write_columnar_handoff,
)
from lightspeed_runtime.units import (
    default_unit_validation_path,
    read_unit_validation_report,
    write_unit_validation_report,
)
from lightspeed_runtime.execution_queues import (
    advance_execution_queue,
    default_execution_queue_path,
    read_execution_queues,
    write_execution_queues,
)
from lightspeed_runtime.knowns import (
    default_knowns_declassification_audit_path,
    default_knowns_promotion_ledger_path,
    default_knowns_queue_objects_path,
    promote_knowns_entries,
    read_knowns_declassification_audit,
    read_knowns_queue_objects,
    read_knowns_promotion_ledger,
    default_knowns_registry_path,
    default_knowns_proofing_queue_path,
    read_knowns_proofing_queue,
    read_knowns_registry,
    write_knowns_declassification_audit,
    write_knowns_proofing_queue,
    write_knowns_queue_objects,
    write_knowns_registry,
)
from lightspeed_runtime.definition_library import (
    default_it_dictionary_path,
    default_oracle_definition_library_path,
    read_it_dictionary,
    read_oracle_definition_library,
    write_it_dictionary,
    write_oracle_definition_library,
)
from lightspeed_runtime.smith_router import (
    complete_smith_job as finalize_smith_job,
    default_smith_router_path,
    queue_smith_job as enqueue_smith_job,
    read_smith_router_state,
    write_smith_router_state,
)
from lightspeed_runtime.domain_registry import CANONICAL_DOMAINS
from lightspeed_runtime.finalization import (
    build_cleanup_report,
    build_cleanup_candidate_report,
    build_generated_layout_audit,
    default_generated_shell_cleanup_path,
    build_legacy_runtime_diff,
    build_legacy_runtime_audit,
    default_dataindex_reduction_path,
    default_cleanup_candidates_path,
    default_cleanup_report_path,
    default_generated_layout_audit_path,
    default_legacy_diff_path,
    default_legacy_audit_path,
    default_legacy_export_cleanup_path,
    default_legacy_sync_path,
    legacy_runtime_exports_root,
    remove_duplicate_generated_shell_files,
    remove_duplicate_legacy_exports,
    remove_safe_cache_dirs,
    reduce_dataindex_duplication,
    sync_legacy_runtime_bundle,
    write_generated_layout_audit,
    write_cleanup_candidate_report,
    write_cleanup_report,
    write_legacy_runtime_diff,
    write_legacy_runtime_audit,
)
from lightspeed_runtime.finalization_control import (
    default_execution_control_path,
    default_finalization_overview_path,
    read_execution_control,
    read_finalization_overview,
    write_execution_control,
    write_finalization_overview,
)
from lightspeed_runtime.contracts import (
    ReservoirManifest,
    build_handoff_context,
    classify_action_risk,
    deterministic_id,
    TrustedDocumentList,
    validate_contract_payload,
)
from lightspeed_runtime.governance_ledgers import (
    append_action_ledger,
    append_approval_ledger,
    default_action_ledger_path,
    default_approval_ledger_path,
)
from lightspeed_runtime.labs import discover_structured_files
from lightspeed_runtime.labs.manager import LabManager
from lightspeed_runtime.labs.presets import (
    default_simulation_presets_path,
    read_simulation_presets,
    write_simulation_presets,
)
from lightspeed_runtime.publishing.manager import PublishingManager
from lightspeed_runtime.reference_project import (
    default_romer_reference_path,
    read_romer_reference_path,
    write_romer_reference_path,
)
from lightspeed_runtime.reservoirs.registry import ReservoirRegistry
from lightspeed_runtime.shell.workspace import WorkspaceContext
from lightspeed_runtime.storage_paths import (
    active_generated_root,
    canonical_execution_queue_path,
    canonical_ai_settings_path,
    canonical_intermediary_targets_path,
    canonical_runtime_config_path,
    ensure_generated_layout,
    finalization_queue_root,
    knowns_root,
    quality_root,
    publish_root,
    publish_snapshot_root,
    runtime_exports_root,
    resolve_ai_settings_path,
    resolve_intermediary_targets_path,
    resolve_runtime_config_path,
    snapshot_export_root,
    zoning_root,
)
from lightspeed_runtime.weekly_log import append_weekly_log, weekly_log_path, weekly_log_summary
from lightspeed_runtime.telemetry import append_otel_event, default_telemetry_path, telemetry_summary
from lightspeed_runtime.ui_experience import (
    default_ui_experience_alignment_path,
    read_ui_experience_alignment,
    write_ui_experience_alignment,
)
from lightspeed_runtime.ui_polish import (
    default_ui_polish_contract_path,
    read_ui_polish_contract,
    write_ui_polish_contract,
)
from lightspeed_runtime.operator_os import (
    default_operator_os_contract_path,
    read_operator_os_contract,
    write_operator_os_contract,
)
from lightspeed_runtime.bridge_health import (
    default_bridge_health_path,
    read_bridge_health,
    write_bridge_health,
)
from lightspeed_runtime.web_integration import (
    default_romer_web_integration_path,
    read_romer_web_integration,
    write_romer_web_integration,
)
from lightspeed_runtime.walkthrough import (
    default_walkthrough_readiness_path,
    read_walkthrough_readiness,
    write_walkthrough_readiness,
)
from lightspeed_runtime.route_probe import (
    default_route_probe_report_path,
    read_route_probe_report,
    write_route_probe_report,
)
from lightspeed_runtime.workflow_state import (
    default_workflow_state_path,
    read_resumable_workflow_state,
    write_resumable_workflow_state,
)


_DISCOVERY_SKIP_DIRS = {
    ".git",
    ".hg",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "venv",
}


def _normalize_path_token(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


class LightSpeedRuntime:
    def __init__(self, root: Path, config_path: Path | None = None) -> None:
        self.root = Path(root)
        ensure_generated_layout(self.root)
        self._config_path_explicit = config_path is not None
        self.config_path = Path(config_path) if config_path else self._default_runtime_config_path()
        self.registry = ReservoirRegistry()
        self.achilles = AchillesOperator(self.registry)
        self.labs = LabManager()
        self.publishing = PublishingManager()
        self.workspaces: dict[str, WorkspaceContext] = {}
        self.run_workspace_index: dict[str, str] = {}
        self.workspace_aliases = {
            "w6": "romer",
            "romer_workspace": "romer",
            "romer_operations": "romer",
        }

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", (value or "").strip().lower()).strip("_")
        return slug or "workspace"

    def _default_runtime_config_path(self) -> Path:
        return canonical_runtime_config_path(self.root)

    def _default_intermediary_targets_path(self) -> Path:
        return canonical_intermediary_targets_path(self.root)

    def resolve_runtime_config_path(self) -> Path:
        return resolve_runtime_config_path(self.root)

    def resolve_intermediary_targets_path(self) -> Path:
        return resolve_intermediary_targets_path(self.root)

    def resolve_agent_home_config_path(self) -> Path:
        return self.root / "config" / "agent_home.json"

    def resolve_export_root(self) -> Path:
        return self.root / "exports"

    def resolve_agent_home_export_dir(self) -> Path:
        return self.resolve_export_root() / "agent_home"

    def resolve_package_output_dir(self, project_id: str) -> Path:
        return self.resolve_export_root() / "packages" / project_id.lower()

    def describe_runtime_paths(self, project_id: str = "Romer") -> dict:
        return {
            "root": str(self.root.resolve()),
            "config": str(self.config_path.resolve()),
            "intermediary_targets": str(self.resolve_intermediary_targets_path().resolve()),
            "exports_root": str(self.resolve_export_root().resolve()),
            "package_root": str(self.resolve_package_output_dir(project_id).resolve()),
        }

    def _builtin_zoning_template_path(self) -> Path:
        return self.root / "data" / "templates" / "heliocentric_zoning_template.csv"

    def generated_data_root(self) -> Path:
        """Legacy compatibility root for transient generated files.

        Canonical publish outputs stay on floor-owned roots; this path only
        exists for older consumers that still expect a flat compatibility tree.
        """
        return active_generated_root(self.root)

    def knowns_root(self) -> Path:
        return knowns_root(self.root)

    def canonical_workspace_id(self, workspace_id: str) -> str:
        slug = self._slug(workspace_id)
        return self.workspace_aliases.get(slug, slug)

    def runtime_export_root(self) -> Path:
        return runtime_exports_root(self.root)

    def snapshot_export_root(self) -> Path:
        return snapshot_export_root(self.root)

    def publish_root(self) -> Path:
        return publish_root(self.root)

    def publish_snapshot_root(self) -> Path:
        return publish_snapshot_root(self.root)

    def operational_log_path(self) -> Path:
        return weekly_log_path(self.root)

    def log_event(
        self,
        category: str,
        message: str,
        *,
        level: str = "info",
        source: str = "lightspeed_runtime",
        payload: dict | None = None,
    ) -> dict:
        entry = append_weekly_log(
            self.root,
            category=category,
            message=message,
            level=level,
            source=source,
            payload=payload,
        )
        try:
            telemetry = append_otel_event(
                self.root,
                category=category,
                message=message,
                level=level,
                source=source,
                payload=payload,
            )
            entry["telemetry_path"] = telemetry.get("telemetry_path")
            entry["otel_trace_id"] = (telemetry.get("record") or {}).get("trace_id")
        except Exception:
            entry["telemetry_path"] = str(default_telemetry_path(self.root))
            entry["otel_trace_id"] = None
        return entry

    def weekly_log_summary(self) -> dict:
        return weekly_log_summary(self.root)

    def telemetry_summary(self) -> dict:
        return telemetry_summary(self.root)

    def activity_tables(self, *, force_refresh: bool = False, output_path: Path | None = None, max_rows: int | None = None) -> dict:
        if not force_refresh:
            cached = read_activity_tables(self.root, output_path=output_path)
            if cached:
                return cached
        kwargs = {"max_rows": max_rows} if max_rows is not None else {}
        return write_activity_tables(self.root, output_path=output_path or default_activity_tables_path(self.root), **kwargs)

    def write_activity_tables(self, output_path: Path | None = None, max_rows: int | None = None) -> dict:
        kwargs = {"max_rows": max_rows} if max_rows is not None else {}
        payload = write_activity_tables(self.root, output_path=output_path or default_activity_tables_path(self.root), **kwargs)
        self.log_event(
            "activity_tables",
            "Wrote compact Merovingian activity table.",
            payload={
                "path": str(output_path or default_activity_tables_path(self.root)),
                "database_path": str(default_activity_db_path(self.root)),
                "table_rows": (payload.get("summary") or {}).get("table_rows", 0),
                "total_source_events": (payload.get("summary") or {}).get("total_source_events", 0),
                "owner_floor": payload.get("owner_floor"),
                "control_floor": payload.get("control_floor"),
            },
        )
        return payload

    def ui_experience_alignment(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_ui_experience_alignment(self.root, output_path=output_path)
        cached = read_ui_experience_alignment(self.root, output_path=output_path)
        if cached:
            return cached
        return write_ui_experience_alignment(self.root, output_path=output_path)

    def write_ui_experience_alignment(self, output_path: Path | None = None) -> dict:
        payload = self.ui_experience_alignment(force_refresh=True, output_path=output_path)
        self.log_event(
            "ui_experience_alignment",
            "Wrote Trinity UI experience alignment contract.",
            payload={
                "path": str(output_path or default_ui_experience_alignment_path(self.root)),
                "source_page_count": payload.get("source_page_count", 0),
                "mode_count": len(payload.get("content_plan", [])),
            },
        )
        return payload

    def ui_polish_contract(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_ui_polish_contract(self.root, output_path=output_path)
        cached = read_ui_polish_contract(self.root, output_path=output_path)
        if cached:
            return cached
        return write_ui_polish_contract(self.root, output_path=output_path)

    def write_ui_polish_contract(self, output_path: Path | None = None) -> dict:
        payload = self.ui_polish_contract(force_refresh=True, output_path=output_path)
        self.log_event(
            "ui_polish_contract",
            "Wrote Trinity UI polish contract.",
            payload={
                "path": str(output_path or default_ui_polish_contract_path(self.root)),
                "completed_by_contract": payload.get("completed_by_this_contract", []),
            },
        )
        return payload

    def operator_os_contract(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_operator_os_contract(self.root, output_path=output_path)
        cached = read_operator_os_contract(self.root, output_path=output_path)
        if cached:
            return cached
        return write_operator_os_contract(self.root, output_path=output_path)

    def write_operator_os_contract(self, output_path: Path | None = None) -> dict:
        payload = self.operator_os_contract(force_refresh=True, output_path=output_path)
        self.log_event(
            "operator_os_contract",
            "Wrote Trinity operator OS contract.",
            payload={
                "path": str(output_path or default_operator_os_contract_path(self.root)),
                "main_interface": (payload.get("main_interface") or {}).get("name"),
                "search_shortcut": (payload.get("controls") or {}).get("search"),
                "settings_shortcut": (payload.get("controls") or {}).get("settings"),
            },
        )
        return payload

    def romer_web_integration(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_romer_web_integration(self.root, output_path=output_path)
        cached = read_romer_web_integration(self.root, output_path=output_path)
        if cached:
            return cached
        return write_romer_web_integration(self.root, output_path=output_path)

    def write_romer_web_integration(self, output_path: Path | None = None) -> dict:
        payload = self.romer_web_integration(force_refresh=True, output_path=output_path)
        self.log_event(
            "romer_web_integration",
            "Wrote Oracle website, Drive, and Sheets integration contract.",
            payload={
                "path": str(output_path or default_romer_web_integration_path(self.root)),
                "route_count": len(payload.get("website_routes", [])),
                "drive_sources": len(payload.get("drive_sources", [])),
                "spreadsheet_feeds": len(payload.get("spreadsheet_feeds", [])),
            },
        )
        return payload

    def bridge_health(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_bridge_health(self.root, output_path=output_path)
        cached = read_bridge_health(self.root, output_path=output_path)
        if cached:
            return cached
        return write_bridge_health(self.root, output_path=output_path)

    def write_bridge_health(self, output_path: Path | None = None) -> dict:
        payload = self.bridge_health(force_refresh=True, output_path=output_path)
        self.log_event(
            "bridge_health",
            "Wrote Trinity bridge health card contract.",
            payload={
                "path": str(output_path or default_bridge_health_path(self.root)),
                "overall_status": payload.get("overall_status"),
                "readiness_percent": payload.get("readiness_percent"),
                "walkthrough_ready": payload.get("walkthrough_ready"),
            },
        )
        return payload

    def walkthrough_readiness(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_walkthrough_readiness(self.root, output_path=output_path)
        cached = read_walkthrough_readiness(self.root, output_path=output_path)
        if cached:
            return cached
        return write_walkthrough_readiness(self.root, output_path=output_path)

    def write_walkthrough_readiness(self, output_path: Path | None = None) -> dict:
        payload = self.walkthrough_readiness(force_refresh=True, output_path=output_path)
        self.log_event(
            "walkthrough_readiness",
            "Wrote Architect 9am walkthrough readiness contract.",
            payload={
                "path": str(output_path or default_walkthrough_readiness_path(self.root)),
                "overall_status": payload.get("overall_status"),
                "blocked_count": payload.get("blocked_count"),
                "warning_count": payload.get("warning_count"),
            },
        )
        return payload

    def route_probe_report(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_route_probe_report(self.root, output_path=output_path)
        cached = read_route_probe_report(self.root, output_path=output_path)
        if cached:
            return cached
        return write_route_probe_report(self.root, output_path=output_path)

    def write_route_probe_report(self, output_path: Path | None = None, *, timeout: float = 8.0) -> dict:
        payload = write_route_probe_report(self.root, output_path=output_path, timeout=timeout)
        self.log_event(
            "route_probe_report",
            "Wrote Oracle live route probe report.",
            payload={
                "path": str(output_path or default_route_probe_report_path(self.root)),
                "status": payload.get("status"),
                "public_route_ok_count": payload.get("public_route_ok_count"),
                "failure_count": payload.get("failure_count"),
            },
        )
        return payload

    def default_workspace_package_dir(
        self,
        project_id: str,
        *,
        workspace_id: str,
        label: str = "desktop_export",
        action_id: str | None = None,
    ) -> Path:
        """Return the canonical Architect snapshot output directory for a package."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        suffix = [stamp, self._slug(label)]
        if action_id:
            suffix.append(self._slug(action_id)[:12])
        return self.publish_snapshot_root() / self._slug(project_id) / "_".join(suffix)

    @staticmethod
    def _default_runtime_config_payload() -> dict:
        return {"sources": [], "catalog_policy": {"default_view": "curated_first", "raw_sources_secondary": True}}

    def load_config(self) -> dict:
        """Load the canonical runtime config, falling back to legacy read paths."""
        path = self.config_path if self._config_path_explicit else resolve_runtime_config_path(self.root)
        if not path.exists():
            return self._default_runtime_config_payload()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return self._default_runtime_config_payload()
        if not isinstance(payload, dict):
            return self._default_runtime_config_payload()
        payload.setdefault("sources", [])
        payload.setdefault("catalog_policy", {"default_view": "curated_first", "raw_sources_secondary": True})
        return payload

    def load_intermediary_targets(self) -> dict:
        """Load Architect-owned intermediary targets with legacy compatibility fallback."""
        path = resolve_intermediary_targets_path(self.root)
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        if isinstance(payload.get("targets"), dict):
            payload = payload["targets"]
        elif isinstance(payload.get("intermediary_targets"), dict):
            payload = payload["intermediary_targets"]
        return self._normalize_intermediary_targets(payload)

    def load_ai_settings(self) -> dict:
        return load_ai_settings(self.root)

    def save_ai_settings(self, settings: dict) -> Path:
        return save_ai_settings(self.root, settings)

    def ai_backend_summary(self) -> dict:
        return ai_backend_summary(self.load_ai_settings())

    def _normalize_reservoir_manifest_item(self, item: dict) -> dict:
        normalized = dict(item)
        source_label = normalized.get("source_label") or normalized.get("label") or normalized.get("display_name")
        if not source_label:
            source_label = str(normalized.get("source_id") or "").replace("_", " ").strip().title()
        normalized["source_label"] = str(source_label or "")
        normalized["definition"] = str(
            normalized.get("definition")
            or normalized.get("description")
            or normalized.get("summary")
            or normalized["source_label"]
        )
        trusted_documents = normalized.get("trusted_documents")
        if isinstance(trusted_documents, list):
            normalized["trusted_documents"] = TrustedDocumentList(
                str(value).strip() for value in trusted_documents if str(value).strip()
            )
        normalized["operator_notes"] = str(normalized.get("operator_notes") or normalized.get("notes") or "")
        return normalized

    def _normalize_intermediary_targets(self, payload: dict) -> dict:
        normalized: dict[str, dict] = {}
        for target_id, item in payload.items():
            if not isinstance(item, dict):
                continue
            target = dict(item)
            target_label = str(target.get("label") or target_id).strip()
            target_text = f"{target_id} {target_label} {target.get('description', '')}".lower()
            owner_floor = str(target.get("owner_floor") or target.get("floor_owner") or "").strip()
            if not owner_floor:
                if any(token in target_text for token in ("oracle", "knowns", "catalog", "dataset", "definition")):
                    owner_floor = "Oracle"
                elif any(token in target_text for token in ("smith", "workflow", "queue", "router", "bridge")):
                    owner_floor = "Smith"
                elif any(token in target_text for token in ("neo", "assistant", "ai", "operator")):
                    owner_floor = "Neo"
                elif any(token in target_text for token in ("trinity", "settings", "theme", "ui", "portal")):
                    owner_floor = "Trinity"
                elif any(token in target_text for token in ("construct", "simulation", "zoning", "lab", "workspace")):
                    owner_floor = "TheConstruct"
                elif any(token in target_text for token in ("merovingian", "audit", "log", "finalization")):
                    owner_floor = "Merovingian"
                else:
                    owner_floor = "Architect"
            target["target_id"] = target_id
            target["owner_floor"] = owner_floor
            target["destination_kind"] = str(target.get("destination_kind") or "snapshot")
            normalized[target_id] = target
        return normalized

    def _manifest_from_config(self, item: dict) -> ReservoirManifest:
        payload = self._normalize_reservoir_manifest_item(item)
        configured_root_path = str(payload.get("root_path", ""))
        resolved_root, resolution = self.resolve_reservoir_root(configured_root_path)
        payload["configured_root_path"] = configured_root_path
        payload["root_path"] = str(resolved_root)
        payload["root_resolution"] = resolution
        return ReservoirManifest(**payload)

    def _source_catalog_entry(self, manifest: ReservoirManifest) -> dict:
        resolved_root = Path(manifest.root_path)
        configured_root = Path(manifest.configured_root_path or manifest.root_path)
        return {
            "source_id": manifest.source_id,
            "source_label": manifest.source_label or manifest.source_id,
            "source_type": manifest.source_type,
            "classification": manifest.classification,
            "configured_root_path": str(configured_root),
            "resolved_root_path": str(resolved_root),
            "root_resolution": manifest.root_resolution,
            "root_exists": resolved_root.exists(),
            "trusted_document_count": len(manifest.trusted_documents),
            "trusted_documents": list(manifest.trusted_documents),
            "extractors": list(manifest.extractors),
        }

    def resolve_reservoir_root(self, configured_root: str | Path) -> tuple[Path, str]:
        configured = Path(configured_root).expanduser()
        direct = self._resolve_direct_reservoir_root(configured)
        if direct is not None:
            return direct

        suffix_match = self._discover_reservoir_root_by_suffix(configured)
        if suffix_match is not None:
            return suffix_match

        basename_match = self._discover_reservoir_root_by_basename(configured)
        if basename_match is not None:
            return basename_match

        return configured, "configured_missing"

    def _resolve_direct_reservoir_root(self, configured: Path) -> tuple[Path, str] | None:
        if configured.exists():
            return configured.resolve(), "configured"
        if configured.is_absolute():
            return None
        runtime_relative = (self.root / configured).expanduser()
        if runtime_relative.exists():
            return runtime_relative.resolve(), "runtime_relative"
        return None

    def _discovery_roots(self) -> list[Path]:
        roots: list[Path] = []
        raw_roots: list[Path] = []
        hints = os.environ.get("LIGHTSPEED_RUNTIME_SOURCE_ROOTS", "")
        for item in hints.split(os.pathsep):
            if item.strip():
                raw_roots.append(Path(item.strip()).expanduser())
        raw_roots.extend([self.root, self.root.parent])

        seen: set[str] = set()
        for candidate in raw_roots:
            if not candidate.exists():
                continue
            key = str(candidate.resolve()).lower()
            if key in seen:
                continue
            seen.add(key)
            roots.append(candidate.resolve())
        return roots

    def _meaningful_root_parts(self, configured: Path) -> list[str]:
        parts = [part for part in configured.parts if part not in {configured.drive, configured.root}]
        if not parts:
            return []

        preferred_markers = {
            _normalize_path_token(self.root.parent.name),
            "lightspeedconsolidated",
            "desktop",
        }
        starts = {max(0, len(parts) - width) for width in range(1, min(len(parts), 4) + 1)}
        for index, part in enumerate(parts):
            if _normalize_path_token(part) in preferred_markers and index + 1 < len(parts):
                starts.add(index + 1)

        ordered_starts = sorted(starts, key=lambda value: (len(parts) - value), reverse=True)
        suffixes: list[list[str]] = []
        seen: set[tuple[str, ...]] = set()
        for start in ordered_starts:
            suffix = tuple(parts[start:])
            if not suffix or suffix in seen:
                continue
            seen.add(suffix)
            suffixes.append(list(suffix))
        return suffixes[0] if suffixes else parts

    def _suffix_candidates(self, configured: Path) -> list[tuple[str, ...]]:
        parts = self._meaningful_root_parts(configured)
        if not parts:
            return []

        candidates: list[tuple[str, ...]] = []
        seen: set[tuple[str, ...]] = set()
        for width in range(min(len(parts), 4), 0, -1):
            suffix = tuple(parts[-width:])
            if suffix in seen:
                continue
            seen.add(suffix)
            candidates.append(suffix)
        if tuple(parts) not in seen:
            candidates.insert(0, tuple(parts))
        return candidates

    def _discover_reservoir_root_by_suffix(self, configured: Path) -> tuple[Path, str] | None:
        for anchor in self._discovery_roots():
            for suffix in self._suffix_candidates(configured):
                parts = list(suffix)
                if parts and _normalize_path_token(parts[0]) == _normalize_path_token(anchor.name):
                    parts = parts[1:]
                if not parts:
                    continue
                candidate = anchor.joinpath(*parts)
                if candidate.exists():
                    return candidate.resolve(), "discovered_suffix"
        return None

    def _discover_reservoir_root_by_basename(self, configured: Path) -> tuple[Path, str] | None:
        parts = self._meaningful_root_parts(configured)
        if not parts:
            return None

        target_name = _normalize_path_token(parts[-1])
        target_tail = [_normalize_path_token(part) for part in parts[-3:]]
        best_score: tuple[int, int] | None = None
        best_candidate: Path | None = None
        for anchor in self._discovery_roots():
            for candidate in self._iter_discovery_directories(anchor, max_depth=4):
                if _normalize_path_token(candidate.name) != target_name:
                    continue
                tail = [_normalize_path_token(part) for part in candidate.parts[-len(target_tail) :]]
                score = sum(1 for left, right in zip(reversed(tail), reversed(target_tail)) if left == right)
                ranking = (score, -len(candidate.parts))
                if best_score is None or ranking > best_score:
                    best_score = ranking
                    best_candidate = candidate
        if best_score is None or best_score[0] <= 0 or best_candidate is None:
            return None
        return best_candidate.resolve(), "discovered_basename"

    def _iter_discovery_directories(self, root: Path, *, max_depth: int) -> list[Path]:
        root = root.resolve()
        root_depth = len(root.parts)
        discovered: list[Path] = []
        for current, dirnames, _filenames in os.walk(root):
            current_path = Path(current)
            depth = len(current_path.parts) - root_depth
            dirnames[:] = [
                name for name in dirnames if name not in _DISCOVERY_SKIP_DIRS and depth < max_depth
            ]
            discovered.append(current_path)
            if depth >= max_depth:
                dirnames[:] = []
        return discovered

    def register_configured_sources(self) -> int:
        config = self.load_config()
        count = 0
        for item in config.get("sources", []):
            if not isinstance(item, dict):
                continue
            try:
                manifest = self._manifest_from_config(item)
            except TypeError:
                continue
            self.registry.register_source(manifest)
            count += 1
        return count

    def bootstrap(self, index_limit_per_source: int | None = None) -> dict:
        source_count = self.register_configured_sources()
        indexed_counts: dict[str, int] = {}
        for manifest in self.registry.manifests():
            assets = self.registry.build_index(manifest.source_id, max_files=index_limit_per_source)
            indexed_counts[manifest.source_id] = len(assets)
        config_path = self.config_path
        intermediary_targets_path = resolve_intermediary_targets_path(self.root)
        ai_settings_path = resolve_ai_settings_path(self.root)
        publish_snapshot_root_path = self.publish_snapshot_root()
        snapshot_export_root_path = self.snapshot_export_root()
        source_catalog = [self._source_catalog_entry(manifest) for manifest in self.registry.manifests()]
        return {
            "domains": list(CANONICAL_DOMAINS.keys()),
            "sources": source_count,
            "indexed_counts": indexed_counts,
            "resolved_root_count": sum(
                1 for item in source_catalog if item["root_resolution"] != "configured_missing"
            ),
            "source_catalog": source_catalog,
            "runtime_contracts": {
                "canonical_runtime_config_path": str(canonical_runtime_config_path(self.root)),
                "resolved_runtime_config_path": str(config_path),
                "canonical_intermediary_targets_path": str(canonical_intermediary_targets_path(self.root)),
                "resolved_intermediary_targets_path": str(intermediary_targets_path),
                "canonical_ai_settings_path": str(canonical_ai_settings_path(self.root)),
                "resolved_ai_settings_path": str(ai_settings_path),
                "publish_snapshot_root": str(publish_snapshot_root_path),
                "publish_snapshot_root_exists": publish_snapshot_root_path.exists(),
                "snapshot_export_root": str(snapshot_export_root_path),
                "snapshot_export_root_exists": snapshot_export_root_path.exists(),
                "runtime_exports_root": str(self.runtime_export_root()),
                "runtime_exports_generated_on_demand": True,
                "generated_data_root_legacy": str(self.generated_data_root()),
            },
            "manifests": [manifest.to_dict() for manifest in self.registry.manifests()],
            "config_summary": {
                "config_path": str(config_path),
                "config_exists": config_path.exists(),
                "intermediary_targets_path": str(intermediary_targets_path),
                "intermediary_targets_exists": intermediary_targets_path.exists(),
                "ai_settings_path": str(ai_settings_path),
                "ai_settings_exists": ai_settings_path.exists(),
                "canonical_vs_legacy_order": ["canonical", "legacy_fallback"],
            },
        }

    def source_catalog(self) -> list[dict]:
        if not self.registry.manifests():
            self.register_configured_sources()
        return [self._source_catalog_entry(manifest) for manifest in self.registry.manifests()]

    def structured_dataset_catalog(self, *, limit_per_source: int = 24) -> list[dict]:
        if not self.registry.manifests():
            self.register_configured_sources()
        catalog: list[dict] = []
        seen_paths: set[str] = set()
        template_path = self._builtin_zoning_template_path()
        if template_path.exists():
            catalog.append(
                {
                    "source_id": "builtin_template",
                    "source_type": "template",
                    "classification": "canonical",
                    "floor_owner": "TheConstruct",
                    "relative_path": template_path.name,
                    "absolute_path": str(template_path),
                    "label": f"builtin_template / {template_path.name}",
                }
            )
            seen_paths.add(str(template_path))
        for item in self.preferred_empirical_datasets(limit=limit_per_source):
            absolute_path = str(item["absolute_path"])
            if absolute_path in seen_paths:
                continue
            catalog.append(dict(item))
            seen_paths.add(absolute_path)
        for manifest in self.registry.manifests():
            root = Path(manifest.root_path)
            for path in discover_structured_files(root, limit=limit_per_source):
                absolute_path = str(path)
                if absolute_path in seen_paths:
                    continue
                try:
                    relative_path = path.relative_to(root).as_posix()
                except Exception:
                    relative_path = path.name
                catalog.append(
                    {
                        "source_id": manifest.source_id,
                        "source_type": manifest.source_type,
                        "classification": manifest.classification,
                        "floor_owner": manifest.floor_owner,
                        "relative_path": relative_path,
                        "absolute_path": absolute_path,
                        "label": f"{manifest.source_id} / {relative_path}",
                    }
                )
                seen_paths.add(absolute_path)
        catalog.sort(
            key=lambda item: (
                0 if item["source_id"] == "builtin_template" else 1,
                item["source_id"],
                item["relative_path"].lower(),
            )
        )
        return catalog

    def _manifest_for_source(self, source_id: str) -> ReservoirManifest | None:
        if not self.registry.manifests():
            self.register_configured_sources()
        return next((item for item in self.registry.manifests() if item.source_id == source_id), None)

    def _resolve_manifest_relative_path(
        self,
        *,
        source_id: str,
        relative_path: str | None = None,
        absolute_path: str | None = None,
    ) -> Path | None:
        manifest = self._manifest_for_source(source_id)
        if manifest is not None and relative_path:
            candidate = Path(manifest.root_path) / relative_path
            if candidate.exists():
                return candidate
        if absolute_path:
            candidate = Path(absolute_path)
            if candidate.exists():
                return candidate
        return None

    def preferred_empirical_datasets(self, *, limit: int = 12) -> list[dict]:
        structured_suffixes = {".csv", ".json", ".jsonl", ".ecsv"}
        payload = self.empirical_catalog()
        preferred = (payload.get("clusterable_inputs") or []) + (payload.get("recommended_datasets") or [])
        datasets: list[dict] = []
        seen_paths: set[str] = set()
        for item in preferred:
            source_id = str(item.get("source_id") or "")
            relative_path = str(item.get("relative_path") or "")
            resolved = self._resolve_manifest_relative_path(
                source_id=source_id,
                relative_path=relative_path,
                absolute_path=str(item.get("absolute_path") or ""),
            )
            if resolved is None:
                continue
            if resolved.suffix.lower() not in structured_suffixes:
                continue
            absolute_path = str(resolved)
            if absolute_path in seen_paths:
                continue
            datasets.append(
                {
                    "source_id": source_id,
                    "source_type": "empirical_preferred",
                    "classification": "reference",
                    "floor_owner": "TheConstruct",
                    "relative_path": relative_path or resolved.name,
                    "absolute_path": absolute_path,
                    "label": f"{source_id} / {relative_path or resolved.name}",
                    "dataset_role": item.get("dataset_role"),
                    "priority": int(item.get("priority", 0) or 0),
                }
            )
            seen_paths.add(absolute_path)
            if len(datasets) >= max(1, limit):
                break
        return datasets

    def operator_simulation_context(
        self,
        workspace_id: str,
        project_id: str,
        *,
        query: str = "",
        limit: int = 5,
    ) -> dict:
        if not self.registry.manifests():
            self.register_configured_sources()
        knowns = self.knowns_registry()
        empirical = self.empirical_catalog()
        datasets = self.structured_dataset_catalog(limit_per_source=12)
        return self.labs.build_operator_simulation_context(
            workspace_id=workspace_id,
            project_id=project_id,
            query=query,
            knowns_payload=knowns,
            empirical_payload=empirical,
            dataset_catalog=datasets,
            limit=limit,
        )

    def simulation_presets(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        empirical = self.empirical_catalog()
        if force_refresh:
            return write_simulation_presets(self.root, empirical, output_path=output_path)
        cached = read_simulation_presets(self.root, output_path=output_path)
        if cached:
            return cached
        return write_simulation_presets(self.root, empirical, output_path=output_path)

    def write_simulation_presets(self, output_path: Path | None = None) -> dict:
        payload = self.simulation_presets(force_refresh=True, output_path=output_path)
        self.log_event(
            "simulation_presets",
            "Wrote Romer-first simulation presets from empirical roles.",
            payload={
                "path": str(output_path or default_simulation_presets_path(self.root)),
                "preset_count": payload.get("preset_count", 0),
                "reference_project": payload.get("reference_project", "Romer"),
            },
        )
        return payload

    def resumable_workflow_state(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        try:
            simulation_presets = self.simulation_presets()
        except Exception:
            simulation_presets = {}
        if force_refresh:
            return write_resumable_workflow_state(
                self.root,
                smith_router=self.smith_router_state(),
                simulation_presets=simulation_presets,
                output_path=output_path,
            )
        cached = read_resumable_workflow_state(self.root, output_path=output_path)
        if cached:
            return cached
        return write_resumable_workflow_state(
            self.root,
            smith_router=self.smith_router_state(),
            simulation_presets=simulation_presets,
            output_path=output_path,
        )

    def write_resumable_workflow_state(self, output_path: Path | None = None) -> dict:
        payload = self.resumable_workflow_state(force_refresh=True, output_path=output_path)
        self.log_event(
            "resumable_workflow_state",
            "Wrote Smith resumable workflow state.",
            payload={
                "path": str(output_path or default_workflow_state_path(self.root)),
                "workflow_count": payload.get("workflow_count", 0),
                "resumable_count": payload.get("resumable_count", 0),
            },
        )
        return payload

    def romer_reference_path(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            workspace = self.ensure_workspace("romer", "Romer", active_floor="Architect")
            try:
                simulation_presets = self.simulation_presets()
            except Exception:
                simulation_presets = {}
            return write_romer_reference_path(
                self.root,
                ui_alignment=self.ui_experience_alignment(),
                simulation_presets=simulation_presets,
                workflow_state=self.resumable_workflow_state(),
                latest_package=workspace.latest_package_metadata or {},
                output_path=output_path,
            )
        cached = read_romer_reference_path(self.root, output_path=output_path)
        if cached:
            return cached
        return self.romer_reference_path(force_refresh=True, output_path=output_path)

    def write_romer_reference_path(self, output_path: Path | None = None) -> dict:
        payload = self.romer_reference_path(force_refresh=True, output_path=output_path)
        self.log_event(
            "romer_reference_path",
            "Wrote Romer reference end-to-end project path.",
            payload={
                "path": str(output_path or default_romer_reference_path(self.root)),
                "step_count": len(payload.get("end_to_end_steps", [])),
                "preset_count": payload.get("preset_count", 0),
            },
        )
        return payload

    def _resolve_structured_dataset(
        self,
        *,
        source_id: str | None = None,
        relative_path: str | None = None,
        source_path: str | None = None,
    ) -> dict:
        if source_id == "builtin_template":
            path = self._builtin_zoning_template_path()
            if not path.exists():
                raise ValueError(f"Built-in zoning template not found: {path}")
            return {
                "source_id": "builtin_template",
                "source_label": f"builtin_template / {path.name}",
                "relative_path": path.name,
                "source_path": str(path),
            }
        if source_path:
            path = Path(source_path)
            if not path.exists():
                raise ValueError(f"Structured zoning source not found: {path}")
            return {
                "source_id": source_id or "external_source",
                "source_label": source_id or path.stem,
                "relative_path": relative_path or path.name,
                "source_path": str(path),
            }

        preferred = self.preferred_empirical_datasets(limit=24)
        if source_id:
            preferred = [item for item in preferred if item["source_id"] == source_id]
        if relative_path:
            preferred = [item for item in preferred if item["relative_path"] == relative_path]
        if preferred:
            selected = preferred[0]
            return {
                "source_id": selected["source_id"],
                "source_label": selected["label"],
                "relative_path": selected["relative_path"],
                "source_path": selected["absolute_path"],
            }

        if source_id:
            if not self.registry.manifests():
                self.register_configured_sources()
            manifest = next((item for item in self.registry.manifests() if item.source_id == source_id), None)
            if manifest is None:
                raise ValueError(f"Unknown zoning source id: {source_id}")
            root = Path(manifest.root_path)
            if relative_path:
                path = root / relative_path
                if not path.exists():
                    raise ValueError(f"Structured zoning source not found: {path}")
            else:
                candidates = discover_structured_files(root, limit=12)
                if not candidates:
                    raise ValueError(f"No structured zoning source found under {root}")
                path = candidates[0]
                try:
                    relative_path = path.relative_to(root).as_posix()
                except Exception:
                    relative_path = path.name
            return {
                "source_id": manifest.source_id,
                "source_label": f"{manifest.source_id} / {relative_path}",
                "relative_path": relative_path,
                "source_path": str(path),
            }

        catalog = self.structured_dataset_catalog()
        if source_id:
            catalog = [item for item in catalog if item["source_id"] == source_id]
        if relative_path:
            catalog = [item for item in catalog if item["relative_path"] == relative_path]
        if not catalog:
            raise ValueError("No structured dataset is available for heliocentric zoning.")
        selected = catalog[0]
        return {
            "source_id": selected["source_id"],
            "source_label": selected["label"],
            "relative_path": selected["relative_path"],
            "source_path": selected["absolute_path"],
        }

    def ensure_workspace(self, workspace_id: str, project_id: str, active_floor: str) -> WorkspaceContext:
        workspace_id = self.canonical_workspace_id(workspace_id)
        if workspace_id not in self.workspaces:
            self.workspaces[workspace_id] = WorkspaceContext(
                workspace_id=workspace_id,
                project_id=project_id,
                active_floor=active_floor,
            )
        workspace = self.workspaces[workspace_id]
        workspace.project_id = project_id
        workspace.active_floor = active_floor
        return workspace

    def create_lab_run(
        self,
        workspace_id: str,
        project_id: str,
        *,
        lab_type: str,
        scenario_id: str,
        dataset_refs: list[str],
        parameter_set: dict,
        engine: str,
    ) -> dict:
        workspace_id = self.canonical_workspace_id(workspace_id)
        workspace = self.ensure_workspace(workspace_id, project_id, active_floor="Trinity")
        run = self.labs.create_run(
            lab_type=lab_type,
            scenario_id=scenario_id,
            dataset_refs=dataset_refs,
            parameter_set=parameter_set,
            engine=engine,
        )
        workspace.run_ids.append(run.run_id)
        self.run_workspace_index[run.run_id] = workspace.workspace_id
        payload = run.to_dict()
        self.log_event(
            "lab_run_created",
            f"Created {lab_type} run {run.run_id} for {project_id}.",
            payload={
                "workspace_id": workspace_id,
                "project_id": project_id,
                "run_id": run.run_id,
                "scenario_id": scenario_id,
                "engine": engine,
            },
        )
        return payload

    def complete_lab_run(self, run_id: str, *, metrics: dict, outputs: list[dict]) -> dict:
        run = self.labs.complete_run(run_id, metrics=metrics, outputs=outputs)
        workspace_id = self.run_workspace_index.get(run_id)
        if workspace_id and workspace_id in self.workspaces:
            self.workspaces[workspace_id].active_floor = "Trinity"
            project_id = self.workspaces[workspace_id].project_id
        else:
            project_id = None
        payload = run.to_dict()
        self.log_event(
            "lab_run_completed",
            f"Completed run {run_id}.",
            payload={
                "workspace_id": workspace_id,
                "project_id": project_id,
                "run_id": run_id,
                "metrics": metrics,
                "output_count": len(outputs or []),
            },
        )
        return payload

    def execute_heliocentric_zoning(
        self,
        workspace_id: str,
        project_id: str,
        *,
        source_id: str | None = None,
        relative_path: str | None = None,
        source_path: str | None = None,
        scenario_id: str = "heliocentric_zoning_grid",
        max_records: int = 2500,
        cluster_target: int = 3,
        top_targets: int = 25,
    ) -> dict:
        workspace_id = self.canonical_workspace_id(workspace_id)
        dataset = self._resolve_structured_dataset(
            source_id=source_id,
            relative_path=relative_path,
            source_path=source_path,
        )
        run = self.create_lab_run(
            workspace_id,
            project_id,
            lab_type="heliocentric_zoning",
            scenario_id=scenario_id,
            dataset_refs=[dataset["source_id"]],
            parameter_set={
                "source_id": dataset["source_id"],
                "relative_path": dataset["relative_path"],
                "source_path": dataset["source_path"],
                "max_records": max_records,
                "cluster_target": cluster_target,
                "top_targets": top_targets,
            },
            engine="heliocentric_zoning",
        )
        output_dir = zoning_root(self.root) / self._slug(project_id) / run["run_id"]
        result = self.labs.execute_heliocentric_zoning(
            run["run_id"],
            source_path=dataset["source_path"],
            output_dir=output_dir,
            source_label=dataset["source_label"],
            max_records=max_records,
            cluster_target=cluster_target,
            top_targets=top_targets,
        )
        source_owner = str(
            dataset.get("owner_floor")
            or dataset.get("source_owner")
            or dataset.get("floor_owner")
            or "Oracle"
        ).strip() or "Oracle"
        simulation_parameters = dict(result.get("simulation_parameters") or {})
        simulation_parameters.setdefault("owner_floor", "TheConstruct")
        simulation_parameters.setdefault("source_owner", source_owner)
        result["simulation_parameters"] = simulation_parameters
        workspace = self.ensure_workspace(workspace_id, project_id, active_floor="Trinity")
        workspace.active_floor = "Trinity"
        self.log_event(
            "heliocentric_zoning_completed",
            f"Completed heliocentric zoning run {run['run_id']} for {project_id}.",
            payload={
                "workspace_id": workspace_id,
                "project_id": project_id,
                "run_id": run["run_id"],
                "source_id": dataset["source_id"],
                "relative_path": dataset["relative_path"],
                "output_dir": str(output_dir),
                "zone_count": result["metrics"].get("zone_count", 0),
                "cluster_count": result["metrics"].get("cluster_count", 0),
                "shortlist_count": result["metrics"].get("shortlist_count", 0),
                "gmat_target_count": len(result.get("gmat_targets") or []),
            },
        )
        publish_snapshot = self.create_publish_snapshot(
            workspace_id=workspace_id,
            project_id=project_id,
            summary=(
                f"{project_id} heliocentric zoning run {run['run_id']} is attached to the governed "
                "Architect publish chain."
            ),
        )
        result["publish_snapshot"] = {
            "workspace_id": publish_snapshot.get("workspace_id"),
            "project_id": publish_snapshot.get("project_id"),
            "artifact_count": len(publish_snapshot.get("artifacts") or []),
            "latest_run_count": len(publish_snapshot.get("latest_runs") or []),
            "status": publish_snapshot.get("status"),
        }
        return result

    def _workspace_runs(self, workspace: WorkspaceContext) -> list[dict]:
        runs: list[dict] = []
        for run_id in workspace.run_ids:
            try:
                runs.append(self.labs.get_run(run_id).to_dict())
            except KeyError:
                continue
        return runs

    def _workspace_artifacts(self, workspace: WorkspaceContext, artifact_refs: list[dict] | None = None) -> list[dict]:
        artifacts: list[dict] = []
        seen: set[str] = set()

        def _push(item: dict) -> None:
            key = json.dumps(item, sort_keys=True)
            if key in seen:
                return
            seen.add(key)
            artifacts.append(item)

        for item in artifact_refs or []:
            _push(dict(item))

        for run in self._workspace_runs(workspace):
            if run.get("status") != "completed":
                continue
            for output in run.get("outputs", []):
                payload = dict(output)
                payload.setdefault("run_id", run["run_id"])
                payload.setdefault("scenario_id", run["scenario_id"])
                payload.setdefault("lab_type", run["lab_type"])
                _push(payload)

        return artifacts

    def workspace_state(self, workspace_id: str, project_id: str, *, active_floor: str = "Architect") -> dict:
        workspace_id = self.canonical_workspace_id(workspace_id)
        workspace = self.ensure_workspace(workspace_id, project_id, active_floor=active_floor)
        all_actions = {item["action_id"]: item for item in self.achilles.list_actions()}
        actions = [all_actions[action_id] for action_id in workspace.action_ids if action_id in all_actions]
        return {
            "workspace": workspace.to_dict(),
            "latest_runs": self._workspace_runs(workspace),
            "latest_publish_manifest": workspace.latest_publish_manifest,
            "latest_package_metadata": workspace.latest_package_metadata,
            "actions": actions,
        }

    def generate_workspace_gmat_manifest(self, workspace_id: str, project_id: str, *, mission_name: str) -> dict:
        workspace_id = self.canonical_workspace_id(workspace_id)
        workspace = self.ensure_workspace(workspace_id, project_id, active_floor="Trinity")
        completed_runs = [run for run in self._workspace_runs(workspace) if run.get("status") == "completed"]
        if not completed_runs:
            raise ValueError(f"No completed runs available for workspace {workspace_id}")
        latest = completed_runs[-1]
        run = self.labs.get_run(latest["run_id"])
        manifest = self.labs.generate_gmat_manifest(run, mission_name=mission_name)
        artifact = {
            "artifact": "gmat_manifest.json",
            "kind": "gmat_manifest",
            "mission_name": mission_name,
        }
        if artifact not in run.outputs:
            run.outputs.append(artifact)
        return manifest

    def propose_workspace_action(
        self,
        workspace_id: str,
        project_id: str,
        *,
        target_scope: str,
        action_type: str,
        inputs: dict,
        requires_approval: bool = True,
        source_floor: str = "Neo",
        target_floor: str | None = None,
        rationale: str = "",
        artifact_refs: list[dict] | None = None,
        prefer_handoff: bool = False,
    ) -> dict:
        workspace_id = self.canonical_workspace_id(workspace_id)
        workspace = self.ensure_workspace(workspace_id, project_id, active_floor="Neo")
        risk_level = classify_action_risk(action_type)
        if risk_level in {"write", "execute", "publish"}:
            requires_approval = True
        execution_mode = "handoff" if prefer_handoff else "tool_first"
        effective_artifact_refs = artifact_refs
        if effective_artifact_refs is None and isinstance(inputs, dict):
            embedded_refs = inputs.get("artifact_refs")
            if isinstance(embedded_refs, list):
                effective_artifact_refs = embedded_refs
        envelope = self.achilles.propose_action(
            workspace=workspace_id,
            target_scope=target_scope,
            action_type=action_type,
            inputs=inputs,
            requires_approval=requires_approval,
        )
        envelope.trace_id = deterministic_id("trace", workspace_id, action_type, envelope.action_id)
        envelope.risk_level = risk_level
        envelope.execution_mode = execution_mode
        envelope.handoff_context = build_handoff_context(
            source_floor=source_floor,
            target_floor=target_floor or target_scope,
            rationale=rationale,
            artifact_refs=effective_artifact_refs,
            execution_mode=execution_mode,
        )
        if envelope.action_id not in workspace.action_ids:
            workspace.action_ids.append(envelope.action_id)
        if envelope.approval_state == "pending":
            workspace.approvals_pending += 1
        payload = envelope.to_dict()
        self.log_event(
            "action_proposed",
            f"Proposed {action_type} action {envelope.action_id} for {project_id}.",
            payload={
                "workspace_id": workspace_id,
                "project_id": project_id,
                "action_id": envelope.action_id,
                "action_type": action_type,
                "risk_level": risk_level,
                "execution_mode": execution_mode,
                "requires_approval": requires_approval,
            },
        )
        append_action_ledger(
            self.root,
            {
                "event": "action_proposed",
                "trace_id": envelope.trace_id,
                "workspace_id": workspace_id,
                "project_id": project_id,
                "action_id": envelope.action_id,
                "action_type": action_type,
                "risk_level": risk_level,
                "execution_mode": execution_mode,
                "requires_approval": requires_approval,
                "source_floor": source_floor,
                "target_floor": target_floor or target_scope,
            },
        )
        return payload

    def approve_workspace_action(
        self,
        workspace_id: str,
        project_id: str,
        action_id: str,
        *,
        audit_ref: str | None = None,
    ) -> dict:
        workspace_id = self.canonical_workspace_id(workspace_id)
        workspace = self.ensure_workspace(workspace_id, project_id, active_floor="Neo")
        envelope = self.achilles.approve_action(action_id, audit_ref=audit_ref)
        workspace.approvals_pending = max(0, workspace.approvals_pending - 1)
        self._execute_workspace_action(workspace, envelope)
        payload = envelope.to_dict()
        self.log_event(
            "action_approved",
            f"Approved action {action_id} for {project_id}.",
            payload={
                "workspace_id": workspace_id,
                "project_id": project_id,
                "action_id": action_id,
                "result_ref": payload.get("result_ref"),
                "audit_ref": audit_ref,
            },
        )
        append_approval_ledger(
            self.root,
            {
                "event": "action_approved",
                "trace_id": payload.get("trace_id"),
                "workspace_id": workspace_id,
                "project_id": project_id,
                "action_id": action_id,
                "audit_ref": audit_ref,
                "approval_state": payload.get("approval_state"),
                "result_ref": payload.get("result_ref"),
            },
        )
        return payload

    def _execute_workspace_action(self, workspace: WorkspaceContext, envelope) -> None:
        if envelope.approval_state != "approved":
            return
        if envelope.action_type in {"website_publish_sync", "publish_manifest"}:
            intermediary = self.load_intermediary_targets().get("website_bridge", {})
            package = self.export_workspace_package(
                self.default_workspace_package_dir(
                    workspace.project_id,
                    workspace_id=workspace.workspace_id,
                    label=envelope.action_type,
                    action_id=envelope.action_id,
                ),
                workspace_id=workspace.workspace_id,
                project_id=workspace.project_id,
                summary=f"{workspace.project_id} approved desktop export package.",
                metadata={"intermediary": intermediary, "trigger_action_id": envelope.action_id},
            )
            envelope.result_ref = package["files"].get("package_metadata")
        elif envelope.action_type == "build_heliocentric_zoning":
            inputs = dict(envelope.inputs or {})
            result = self.execute_heliocentric_zoning(
                workspace.workspace_id,
                workspace.project_id,
                source_id=inputs.get("source_id"),
                relative_path=inputs.get("relative_path"),
                source_path=inputs.get("source_path"),
                scenario_id=inputs.get("scenario_id", "heliocentric_zoning_grid"),
                max_records=int(inputs.get("max_records", 2500)),
                cluster_target=int(inputs.get("cluster_target", 3)),
                top_targets=int(inputs.get("top_targets", 25)),
            )
            envelope.result_ref = result["artifacts"].get("targets_shortlist_json") or result["output_dir"]

    def create_publish_snapshot(
        self,
        workspace_id: str,
        project_id: str,
        summary: str,
        artifact_refs: list[dict] | None = None,
        destination_root: Path | None = None,
    ) -> dict:
        requested_workspace_id = workspace_id
        canonical_workspace_id = self.canonical_workspace_id(workspace_id)
        workspace = self.ensure_workspace(canonical_workspace_id, project_id, active_floor="Architect")
        latest_runs = self._workspace_runs(workspace)
        artifacts = self._workspace_artifacts(workspace, artifact_refs=artifact_refs)
        destination_root = (
            Path(destination_root)
            if destination_root is not None
            else self.default_workspace_package_dir(
                project_id,
                workspace_id=canonical_workspace_id,
                label="publish_snapshot",
            )
        )
        manifest = self.publishing.create_workspace_manifest(
            workspace_id=requested_workspace_id,
            project_id=workspace.project_id,
            summary_blocks=[{"title": "Summary", "body": summary}],
            artifacts=artifacts,
            visualizations=[],
            latest_runs=latest_runs,
            links=[],
        )
        manifest.source_root = str(self.root.resolve())
        manifest.source_root_kind = "canonical_c_root"
        manifest.destination_root = str(destination_root.resolve())
        manifest.destination_kind = "snapshot"
        manifest.destination_root_kind = "snapshot_output"
        manifest.owner_floor = "Architect"
        manifest.control_floor = "Architect"
        manifest.overwrite_existing = True
        payload = manifest.to_dict()
        payload["canonical_workspace_id"] = workspace.workspace_id
        payload["publish_snapshot_contract"] = self.publish_snapshot_contract(
            workspace_id=canonical_workspace_id,
            project_id=project_id,
            destination_root=destination_root,
        )
        workspace.latest_publish_manifest = payload
        return payload

    def publish_snapshot_contract(
        self,
        *,
        workspace_id: str,
        project_id: str,
        destination_root: Path,
    ) -> dict:
        """Describe the explicit Architect snapshot publish contract for a workspace export."""
        destination_root = Path(destination_root)
        return {
            "contract_version": "2026.04.finalization",
            "source_root": str(self.root.resolve()),
            "source_root_kind": "canonical_c_root",
            "owner_floor": "Architect",
            "control_floor": "Architect",
            "destination_kind": "snapshot",
            "destination_root": str(destination_root.resolve()),
            "destination_root_kind": "snapshot_output",
            "destination_overwrite": True,
            "destination_overwrite_policy": "replace_existing_snapshot",
            "workspace_id": self.canonical_workspace_id(workspace_id),
            "project_id": project_id,
            "notes": "C-root is the canonical build source; the destination is a snapshot output that may be overwritten on publish.",
        }

    def export_bootstrap_summary(self, output_path: Path, index_limit_per_source: int | None = None) -> dict:
        summary = self.bootstrap(index_limit_per_source=index_limit_per_source)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary

    def export_reservoir_snapshot(self, output_path: Path, max_assets_per_source: int = 25) -> dict:
        snapshot = {
            "manifests": [manifest.to_dict() for manifest in self.registry.manifests()],
            "assets": {},
        }
        for manifest in self.registry.manifests():
            assets = self.registry.get_assets(manifest.source_id)
            snapshot["assets"][manifest.source_id] = [
                asset.to_dict() for asset in assets[:max_assets_per_source]
            ]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        return snapshot

    def build_agent_environment(
        self,
        *,
        config_path: Path | None = None,
        max_assets_per_source: int = 25,
    ) -> dict:
        if not self.registry.manifests():
            self.bootstrap(index_limit_per_source=max_assets_per_source)
        from lightspeed_runtime.operator_home import build_agent_environment

        return build_agent_environment(
            self,
            config_path=config_path,
            max_assets_per_source=max_assets_per_source,
        )

    def export_agent_environment(
        self,
        output_dir: Path | None = None,
        *,
        config_path: Path | None = None,
        max_assets_per_source: int = 25,
    ) -> dict:
        if not self.registry.manifests():
            self.bootstrap(index_limit_per_source=max_assets_per_source)
        from lightspeed_runtime.operator_home import export_agent_environment

        destination = output_dir or self.resolve_agent_home_export_dir()
        return export_agent_environment(
            self,
            destination,
            config_path=config_path,
            max_assets_per_source=max_assets_per_source,
        )

    def export_workspace_package(
        self,
        output_dir: Path,
        *,
        workspace_id: str,
        project_id: str,
        summary: str,
        artifact_refs: list[dict] | None = None,
        max_assets_per_source: int = 25,
        metadata: dict | None = None,
    ) -> dict:
        requested_workspace_id = workspace_id
        workspace_id = self.canonical_workspace_id(workspace_id)
        workspace = self.ensure_workspace(workspace_id, project_id, active_floor="Architect")
        publish_snapshot_contract = self.publish_snapshot_contract(
            workspace_id=workspace_id,
            project_id=project_id,
            destination_root=output_dir,
        )
        for run_id in workspace.run_ids:
            try:
                self.labs.get_run(run_id).published = True
            except KeyError:
                continue
        manifest = self.create_publish_snapshot(
            workspace_id=requested_workspace_id,
            project_id=project_id,
            summary=summary,
            artifact_refs=artifact_refs,
            destination_root=output_dir,
        )
        reservoir_snapshot = {
            "manifests": [manifest_obj.to_dict() for manifest_obj in self.registry.manifests()],
            "assets": {
                manifest_obj.source_id: [
                    asset.to_dict() for asset in self.registry.get_assets(manifest_obj.source_id)[:max_assets_per_source]
                ]
                for manifest_obj in self.registry.manifests()
            },
        }
        metadata = dict(metadata or {})
        metadata["publish_snapshot_contract"] = publish_snapshot_contract
        generated_files: dict[str, dict] = {}
        for run in self._workspace_runs(workspace):
            if run.get("status") != "completed":
                continue
            try:
                generated_files[f"{run['run_id']}_gmat_manifest"] = self.labs.generate_gmat_manifest(
                    self.labs.get_run(run["run_id"]),
                    mission_name=f"{project_id} {run['scenario_id']}",
                )
            except Exception:
                continue
        table_validation = self.table_validation_report()
        package = self.publishing.export_workspace_package(
            output_dir,
            manifest=manifest,
            reservoir_snapshot=reservoir_snapshot,
            latest_runs=self._workspace_runs(workspace),
            metadata=metadata,
            extra_files=generated_files or None,
            table_validation=table_validation,
        )
        workspace.latest_package_metadata = package
        package["publish_snapshot_contract"] = publish_snapshot_contract
        package["runtime_exports_generated_on_demand"] = True
        self.log_event(
            "workspace_package_exported",
            f"Exported workspace package for {project_id}.",
            payload={
                "workspace_id": workspace_id,
                "project_id": project_id,
                "output_dir": str(output_dir),
                "package_metadata": ((package.get("files") or {}).get("package_metadata")),
                "publish_snapshot_contract": publish_snapshot_contract,
                "runtime_exports_generated_on_demand": True,
            },
        )
        return package

    def generated_data_summary(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_generated_data_summary(self.root, output_path=output_path)
        cached = read_generated_data_summary(self.root, output_path=output_path)
        if cached:
            return cached
        return write_generated_data_summary(self.root, output_path=output_path)

    def write_generated_data_summary(self, output_path: Path | None = None) -> dict:
        return self.generated_data_summary(force_refresh=True, output_path=output_path)

    def ingestion_preparation(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if not self.registry.manifests():
            self.register_configured_sources()
        indexed_counts = {
            manifest.source_id: len(self.registry.get_assets(manifest.source_id))
            for manifest in self.registry.manifests()
        }
        if force_refresh:
            return write_ingestion_preparation(
                self.root,
                self.registry.manifests(),
                indexed_counts=indexed_counts,
                output_path=output_path,
            )
        cached = read_ingestion_preparation(self.root, output_path=output_path)
        if cached:
            return cached
        return write_ingestion_preparation(
            self.root,
            self.registry.manifests(),
            indexed_counts=indexed_counts,
            output_path=output_path,
        )

    def write_ingestion_preparation(self, output_path: Path | None = None) -> dict:
        payload = self.ingestion_preparation(force_refresh=True, output_path=output_path)
        self.log_event(
            "ingestion_preparation",
            "Wrote ingestion preparation report.",
            payload={
                "path": str(output_path or default_ingestion_preparation_path(self.root)),
                "source_count": payload.get("source_count", 0),
            },
        )
        return payload

    def knowns_registry(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if not self.registry.manifests():
            self.register_configured_sources()
        if force_refresh:
            return write_knowns_registry(
                self.root,
                self.registry.manifests(),
                output_path=output_path,
            )
        cached = read_knowns_registry(self.root, output_path=output_path)
        if cached:
            return cached
        return write_knowns_registry(
            self.root,
            self.registry.manifests(),
            output_path=output_path,
        )

    def write_knowns_registry(self, output_path: Path | None = None) -> dict:
        payload = self.knowns_registry(force_refresh=True, output_path=output_path)
        self.log_event(
            "knowns_registry",
            "Wrote condensed doctrine and knowns registry.",
            payload={
                "path": str(output_path or default_knowns_registry_path(self.root)),
                "theme_count": len(payload.get("themes", [])),
                "source_count": payload.get("source_count", 0),
            },
        )
        return payload

    def execution_queues(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_execution_queues(self.root, output_path=output_path)
        cached = read_execution_queues(self.root, output_path=output_path)
        if cached:
            return cached
        return write_execution_queues(self.root, output_path=output_path)

    def write_execution_queues(self, output_path: Path | None = None) -> dict:
        payload = self.execution_queues(force_refresh=True, output_path=output_path)
        self.log_event(
            "execution_queues",
            "Wrote three-queue finalization execution plan.",
            payload={
                "path": str(output_path or canonical_execution_queue_path(self.root)),
                "queue_count": payload.get("queue_count", 0),
                "action_count": payload.get("action_count", 0),
                "completed_count": payload.get("completed_count", 0),
                "owner_floor": payload.get("owner_floor"),
                "control_floor": payload.get("control_floor"),
            },
        )
        return payload

    def advance_execution_queue(
        self,
        action_id: str,
        *,
        status: str = "completed",
        note: str = "",
        priority: int | None = None,
        output_path: Path | None = None,
    ) -> dict:
        payload = advance_execution_queue(
            self.root,
            action_id,
            status=status,
            note=note,
            priority=priority,
            output_path=output_path or default_execution_queue_path(self.root),
        )
        if payload.get("updated"):
            self.log_event(
                "execution_queue_action",
                f"Updated execution queue action {action_id}.",
                payload={
                    "action_id": action_id,
                    "status": status,
                    "path": str(output_path or canonical_execution_queue_path(self.root)),
                    "queue_root_kind": "canonical_architect_finalization_root",
                },
            )
        return payload

    def oracle_definition_library(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_oracle_definition_library(
                self.root,
                knowns_registry=self.knowns_registry(),
                empirical_catalog=self.empirical_catalog(),
                output_path=output_path,
            )
        cached = read_oracle_definition_library(
            self.root,
            output_path=output_path or default_oracle_definition_library_path(self.root),
        )
        if cached:
            return cached
        return write_oracle_definition_library(
            self.root,
            knowns_registry=self.knowns_registry(),
            empirical_catalog=self.empirical_catalog(),
            output_path=output_path,
        )

    def write_oracle_definition_library(self, output_path: Path | None = None) -> dict:
        payload = self.oracle_definition_library(force_refresh=True, output_path=output_path)
        self.log_event(
            "oracle_definition_library",
            "Wrote Oracle proofed definition library.",
            payload={
                "path": str(output_path or default_oracle_definition_library_path(self.root)),
                "term_count": payload.get("term_count", 0),
                "theme_definition_count": payload.get("theme_definition_count", 0),
            },
        )
        return payload

    def it_dictionary(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_it_dictionary(self.root, output_path=output_path)
        cached = read_it_dictionary(self.root, output_path=output_path)
        if cached:
            return cached
        return write_it_dictionary(self.root, output_path=output_path)

    def write_it_dictionary(self, output_path: Path | None = None) -> dict:
        payload = self.it_dictionary(force_refresh=True, output_path=output_path)
        self.log_event(
            "it_dictionary",
            "Wrote Oracle IT dictionary for searchable LightSpeed shorthand and workflow terms.",
            payload={
                "path": str(output_path or default_it_dictionary_path(self.root)),
                "term_count": payload.get("term_count", 0),
                "dictionary": payload.get("dictionary"),
            },
        )
        return payload

    def knowns_proofing_queue(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        registry_payload = self.knowns_registry()
        if force_refresh:
            return write_knowns_proofing_queue(
                self.root,
                registry_payload,
                output_path=output_path,
            )
        cached = read_knowns_proofing_queue(self.root, output_path=output_path)
        if cached:
            return cached
        return write_knowns_proofing_queue(
            self.root,
            registry_payload,
            output_path=output_path,
        )

    def write_knowns_proofing_queue(self, output_path: Path | None = None) -> dict:
        payload = self.knowns_proofing_queue(force_refresh=True, output_path=output_path)
        self.log_event(
            "knowns_proofing_queue",
            "Wrote Oracle knowns proofing queue.",
            payload={
                "path": str(output_path or default_knowns_proofing_queue_path(self.root)),
                "entry_count": payload.get("entry_count", 0),
            },
        )
        return payload

    def knowns_queue_objects(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_knowns_queue_objects(
                self.root,
                queue_payload=self.knowns_proofing_queue(),
                registry_payload=self.knowns_registry(),
                output_path=output_path,
            )
        cached = read_knowns_queue_objects(
            self.root,
            output_path=output_path or default_knowns_queue_objects_path(self.root),
        )
        if cached:
            return cached
        return write_knowns_queue_objects(
            self.root,
            queue_payload=self.knowns_proofing_queue(),
            registry_payload=self.knowns_registry(),
            output_path=output_path,
        )

    def write_knowns_queue_objects(self, output_path: Path | None = None) -> dict:
        payload = self.knowns_queue_objects(force_refresh=True, output_path=output_path)
        self.log_event(
            "knowns_queue_objects",
            "Wrote first-class Oracle promotion queue objects.",
            payload={
                "path": str(output_path or default_knowns_queue_objects_path(self.root)),
                "object_count": payload.get("object_count", 0),
                "pending_entries": payload.get("pending_entries", 0),
            },
        )
        return payload

    def empirical_catalog(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if not self.registry.manifests():
            self.register_configured_sources()
        if force_refresh:
            return write_empirical_catalog(
                self.root,
                self.registry.manifests(),
                output_path=output_path,
            )
        cached = read_empirical_catalog(self.root, output_path=output_path)
        if cached:
            return cached
        return write_empirical_catalog(
            self.root,
            self.registry.manifests(),
            output_path=output_path,
        )

    def write_empirical_catalog(self, output_path: Path | None = None) -> dict:
        payload = self.empirical_catalog(force_refresh=True, output_path=output_path)
        self.log_event(
            "empirical_catalog",
            "Wrote condensed empirical catalog for Oracle and Construct use.",
            payload={
                "path": str(output_path or default_empirical_catalog_path(self.root)),
                "source_count": payload.get("source_count", 0),
                "recommended_dataset_count": len(payload.get("recommended_datasets", [])),
            },
        )
        return payload

    def _entity_registry_workspace_snapshots(self) -> list[dict]:
        snapshots: list[dict] = []
        for workspace_id, workspace in self.workspaces.items():
            snapshots.append(
                self.workspace_state(
                    workspace_id,
                    workspace.project_id,
                    active_floor=workspace.active_floor,
                )
            )
        return snapshots

    def entity_registry(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if not self.registry.manifests():
            self.register_configured_sources()
        if force_refresh:
            return write_entity_registry(
                self.root,
                self.registry.manifests(),
                empirical_catalog=self.empirical_catalog(),
                knowns_registry=self.knowns_registry(),
                workspace_snapshots=self._entity_registry_workspace_snapshots(),
                curated_tables=self.curated_tables_index(),
                columnar_handoff=self.columnar_handoff(),
                output_path=output_path,
            )
        cached = read_entity_registry(self.root, output_path=output_path)
        if cached:
            return cached
        return write_entity_registry(
            self.root,
            self.registry.manifests(),
            empirical_catalog=self.empirical_catalog(),
            knowns_registry=self.knowns_registry(),
            workspace_snapshots=self._entity_registry_workspace_snapshots(),
            curated_tables=self.curated_tables_index(),
            columnar_handoff=self.columnar_handoff(),
            output_path=output_path,
        )

    def write_entity_registry(self, output_path: Path | None = None) -> dict:
        payload = self.entity_registry(force_refresh=True, output_path=output_path)
        self.log_event(
            "entity_registry",
            "Wrote canonical Oracle entity registry and dataset manifests.",
            payload={
                "path": str(output_path or default_entity_registry_path(self.root)),
                "entity_count": payload.get("entity_count", 0),
                "dataset_manifest_count": payload.get("dataset_manifest_count", 0),
                "dataset_manifest_index_path": str(default_dataset_manifest_index_path(self.root)),
            },
        )
        return payload

    def curated_tables_index(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_curated_tables_index(
                self.root,
                empirical_catalog=self.empirical_catalog(),
                knowns_registry=self.knowns_registry(),
                output_path=output_path,
            )
        cached = read_curated_tables_index(self.root, output_path=output_path)
        if cached:
            return cached
        return write_curated_tables_index(
            self.root,
            empirical_catalog=self.empirical_catalog(),
            knowns_registry=self.knowns_registry(),
            output_path=output_path,
        )

    def write_curated_tables_index(self, output_path: Path | None = None) -> dict:
        payload = self.curated_tables_index(force_refresh=True, output_path=output_path)
        self.log_event(
            "curated_tables",
            "Wrote Oracle curated analytical tables.",
            payload={
                "path": str(output_path or default_curated_tables_index_path(self.root)),
                "table_count": payload.get("table_count", 0),
            },
        )
        return payload

    def table_validation_report(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_table_validation_report(
                self.root,
                curated_tables=self.curated_tables_index(),
                output_path=output_path,
            )
        path = output_path or default_table_validation_report_path(self.root)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return write_table_validation_report(
            self.root,
            curated_tables=self.curated_tables_index(),
            output_path=output_path,
        )

    def write_table_validation_report(self, output_path: Path | None = None) -> dict:
        payload = self.table_validation_report(force_refresh=True, output_path=output_path)
        self.log_event(
            "table_validation",
            "Wrote curated table validation report.",
            payload={
                "path": str(output_path or default_table_validation_report_path(self.root)),
                "table_count": payload.get("table_count", 0),
                "failed_count": payload.get("failed_count", 0),
            },
        )
        return payload

    def bellcurve_overlay(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_bellcurve_overlay(
                self.root,
                curated_tables=self.curated_tables_index(),
                knowns_registry=self.knowns_registry(),
                output_path=output_path,
            )
        path = output_path or default_bellcurve_overlay_path(self.root)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return write_bellcurve_overlay(
            self.root,
            curated_tables=self.curated_tables_index(),
            knowns_registry=self.knowns_registry(),
            output_path=output_path,
        )

    def write_bellcurve_overlay(self, output_path: Path | None = None) -> dict:
        payload = self.bellcurve_overlay(force_refresh=True, output_path=output_path)
        self.log_event(
            "bellcurve_overlay",
            "Wrote reusable bell-curve and confidence overlays.",
            payload={
                "path": str(output_path or default_bellcurve_overlay_path(self.root)),
                "dataset_histogram_bands": len(payload.get("dataset_confidence_histogram", [])),
                "theme_histogram_bands": len(payload.get("theme_confidence_histogram", [])),
            },
        )
        return payload

    def scientific_query_layer(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_scientific_query_layer(
                self.root,
                empirical_catalog=self.empirical_catalog(),
                curated_tables=self.curated_tables_index(),
                output_path=output_path,
            )
        cached = read_scientific_query_layer(self.root, output_path=output_path)
        if cached:
            return cached
        return write_scientific_query_layer(
            self.root,
            empirical_catalog=self.empirical_catalog(),
            curated_tables=self.curated_tables_index(),
            output_path=output_path,
        )

    def write_scientific_query_layer(self, output_path: Path | None = None) -> dict:
        payload = self.scientific_query_layer(force_refresh=True, output_path=output_path)
        self.log_event(
            "scientific_query",
            "Wrote mounted scientific query layer.",
            payload={
                "path": str(output_path or default_scientific_query_path(self.root)),
                "queryable_count": payload.get("queryable_count", 0),
                "curated_view_count": payload.get("curated_view_count", 0),
            },
        )
        return payload

    def dataset_catalog_shell(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_dataset_catalog_shell(
                self.root,
                empirical_catalog=self.empirical_catalog(),
                scientific_query=self.scientific_query_layer(),
                entity_registry=self.entity_registry(),
                output_path=output_path,
            )
        cached = read_dataset_catalog_shell(self.root, output_path=output_path)
        if cached:
            return cached
        return write_dataset_catalog_shell(
            self.root,
            empirical_catalog=self.empirical_catalog(),
            scientific_query=self.scientific_query_layer(),
            entity_registry=self.entity_registry(),
            output_path=output_path,
        )

    def write_dataset_catalog_shell(self, output_path: Path | None = None) -> dict:
        payload = self.dataset_catalog_shell(force_refresh=True, output_path=output_path)
        self.log_event(
            "dataset_catalog",
            "Wrote Oracle dataset catalog shell.",
            payload={
                "path": str(output_path or default_dataset_catalog_path(self.root)),
                "dataset_count": payload.get("dataset_count", 0),
                "mission_refinement_count": payload.get("mission_refinement_count", 0),
            },
        )
        return payload

    def query_scientific_table(
        self,
        table_name: str,
        *,
        limit: int = 25,
        filters: list[dict] | None = None,
        columns: list[str] | None = None,
    ) -> dict:
        return execute_scientific_query(
            self.root,
            table_name=table_name,
            limit=limit,
            filters=filters,
            columns=columns,
            query_layer=self.scientific_query_layer(),
        )

    def query_scientific_table_tap(self, request: dict) -> dict:
        return execute_tap_like_query(
            self.root,
            request=request,
            query_layer=self.scientific_query_layer(),
        )

    def columnar_handoff(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_columnar_handoff(
                self.root,
                empirical_catalog=self.empirical_catalog(),
                knowns_registry=self.knowns_registry(),
                output_path=output_path,
            )
        cached = read_columnar_handoff(self.root, output_path=output_path)
        if cached:
            return cached
        return write_columnar_handoff(
            self.root,
            empirical_catalog=self.empirical_catalog(),
            knowns_registry=self.knowns_registry(),
            output_path=output_path,
        )

    def write_columnar_handoff(self, output_path: Path | None = None) -> dict:
        payload = self.columnar_handoff(force_refresh=True, output_path=output_path)
        self.log_event(
            "columnar_handoff",
            "Wrote columnar handoff bundle for structured floor exchange.",
            payload={
                "path": str(output_path or default_columnar_handoff_path(self.root)),
                "table_count": payload.get("table_count", 0),
            },
        )
        return payload

    def unit_validation_report(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_unit_validation_report(
                self.root,
                empirical_catalog=self.empirical_catalog(),
                curated_tables=self.curated_tables_index(),
                scientific_query=self.scientific_query_layer(),
                output_path=output_path,
            )
        cached = read_unit_validation_report(self.root, output_path=output_path)
        if cached:
            return cached
        return write_unit_validation_report(
            self.root,
            empirical_catalog=self.empirical_catalog(),
            curated_tables=self.curated_tables_index(),
            scientific_query=self.scientific_query_layer(),
            output_path=output_path,
        )

    def write_unit_validation_report(self, output_path: Path | None = None) -> dict:
        payload = self.unit_validation_report(force_refresh=True, output_path=output_path)
        self.log_event(
            "unit_validation",
            "Wrote scientific unit validation coverage report.",
            payload={
                "path": str(output_path or default_unit_validation_path(self.root)),
                "dataset_count": payload.get("dataset_count", 0),
                "table_count": payload.get("table_count", 0),
            },
        )
        return payload

    def knowns_promotion_ledger(self, output_path: Path | None = None) -> dict:
        return read_knowns_promotion_ledger(
            self.root,
            output_path=output_path or default_knowns_promotion_ledger_path(self.root),
        )

    def knowns_declassification_audit(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_knowns_declassification_audit(
                self.root,
                registry_payload=self.knowns_registry(),
                queue_payload=self.knowns_proofing_queue(),
                ledger_payload=self.knowns_promotion_ledger(),
                output_path=output_path,
            )
        cached = read_knowns_declassification_audit(
            self.root,
            output_path=output_path or default_knowns_declassification_audit_path(self.root),
        )
        if cached:
            return cached
        return write_knowns_declassification_audit(
            self.root,
            registry_payload=self.knowns_registry(),
            queue_payload=self.knowns_proofing_queue(),
            ledger_payload=self.knowns_promotion_ledger(),
            output_path=output_path,
        )

    def write_knowns_declassification_audit(self, output_path: Path | None = None) -> dict:
        payload = self.knowns_declassification_audit(force_refresh=True, output_path=output_path)
        self.log_event(
            "knowns_declassification",
            "Wrote Oracle doctrine declassification audit.",
            payload={
                "path": str(output_path or default_knowns_declassification_audit_path(self.root)),
                "candidate_count": payload.get("candidate_count", 0),
                "ready_count": payload.get("ready_count", 0),
                "duplicate_group_count": payload.get("duplicate_group_count", 0),
            },
        )
        return payload

    def promote_knowns_queue(
        self,
        *,
        entry_ids: list[str] | None = None,
        destinations: list[str] | None = None,
        max_entries: int | None = None,
        queue_path: Path | None = None,
        ledger_path: Path | None = None,
    ) -> dict:
        registry_payload = self.knowns_registry()
        queue_payload = self.knowns_proofing_queue(output_path=queue_path)
        payload = promote_knowns_entries(
            self.root,
            registry_payload,
            queue_payload,
            entry_ids=entry_ids,
            destinations=destinations,
            max_entries=max_entries,
            queue_path=queue_path or default_knowns_proofing_queue_path(self.root),
            ledger_path=ledger_path or default_knowns_promotion_ledger_path(self.root),
        )
        self.log_event(
            "knowns_promotion",
            "Promoted proofed doctrine entries into Oracle and lab destinations.",
            payload={
                "queue_path": payload.get("queue_path"),
                "ledger_path": payload.get("ledger_path"),
                "promoted_count": payload.get("promoted_count", 0),
                "destinations": payload.get("destination_counts", {}),
            },
        )
        return payload

    def smith_router_state(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_smith_router_state(
                self.root,
                execution_queues=self.execution_queues(),
                output_path=output_path,
            )
        cached = read_smith_router_state(
            self.root,
            output_path=output_path or default_smith_router_path(self.root),
        )
        if cached:
            return cached
        return write_smith_router_state(
            self.root,
            execution_queues=self.execution_queues(),
            output_path=output_path,
        )

    def write_smith_router_state(self, output_path: Path | None = None) -> dict:
        payload = self.smith_router_state(force_refresh=True, output_path=output_path)
        self.log_event(
            "smith_router",
            "Wrote Smith cross-floor routing state.",
            payload={
                "path": str(output_path or default_smith_router_path(self.root)),
                "job_count": payload.get("job_count", 0),
                "queued_count": payload.get("queued_count", 0),
                "completed_count": payload.get("completed_count", 0),
            },
        )
        return payload

    def queue_smith_job(
        self,
        *,
        job_type: str,
        source_floor: str,
        workspace_id: str = "romer",
        project_id: str = "Romer",
        payload: dict | None = None,
        target_floor: str | None = None,
        priority: int = 3,
        note: str = "",
        output_path: Path | None = None,
    ) -> dict:
        result = enqueue_smith_job(
            self.root,
            job_type,
            source_floor=source_floor,
            workspace_id=self.canonical_workspace_id(workspace_id),
            project_id=project_id,
            payload=payload,
            target_floor=target_floor,
            priority=priority,
            note=note,
            execution_queues=self.execution_queues(),
            output_path=output_path or default_smith_router_path(self.root),
        )
        if result.get("queued"):
            self.log_event(
                "smith_router",
                f"Queued Smith job {result.get('job_id')}.",
                payload={
                    "job_type": job_type,
                    "source_floor": source_floor,
                    "target_floor": result.get("target_floor"),
                    "router_path": result.get("router_path"),
                },
            )
        return result

    def complete_smith_job(
        self,
        job_id: str,
        *,
        result_ref: str | None = None,
        note: str = "",
        output_path: Path | None = None,
    ) -> dict:
        result = finalize_smith_job(
            self.root,
            job_id,
            result_ref=result_ref,
            note=note,
            execution_queues=self.execution_queues(),
            output_path=output_path or default_smith_router_path(self.root),
        )
        if result.get("updated"):
            self.log_event(
                "smith_router",
                f"Completed Smith job {job_id}.",
                payload={
                    "job_id": job_id,
                    "result_ref": result_ref,
                    "router_path": result.get("router_path"),
                },
            )
        return result

    def validate_contract(self, contract_kind: str, payload: dict) -> dict:
        return validate_contract_payload(contract_kind, payload)

    def generated_layout_audit(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_generated_layout_audit(
                self.root,
                output_path=output_path or default_generated_layout_audit_path(self.root),
            )
        return build_generated_layout_audit(self.root)

    def write_generated_layout_audit(self, output_path: Path | None = None) -> dict:
        payload = self.generated_layout_audit(force_refresh=True, output_path=output_path)
        self.log_event(
            "generated_layout_audit",
            "Wrote generated layout audit.",
            payload={
                "path": str(output_path or default_generated_layout_audit_path(self.root)),
                "legacy_operations_can_be_declassified": payload.get("legacy_operations_can_be_declassified"),
            },
        )
        return payload

    def smart_floor_assimilation(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if not self.registry.manifests():
            self.register_configured_sources()
        manifests = [manifest.to_dict() for manifest in self.registry.manifests()]
        if force_refresh:
            return write_assimilation_report(
                self.root,
                manifests=manifests,
                output_path=output_path or default_assimilation_report_path(self.root),
            )
        path = output_path or default_assimilation_report_path(self.root)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return build_assimilation_report(self.root, manifests=manifests)

    def write_smart_floor_assimilation(self, output_path: Path | None = None) -> dict:
        payload = self.smart_floor_assimilation(force_refresh=True, output_path=output_path)
        self.log_event(
            "smart_floor_assimilation",
            "Wrote smart-floor assimilation report.",
            payload={
                "path": str(output_path or default_assimilation_report_path(self.root)),
                "external_source_count": payload.get("external_source_count", 0),
            },
        )
        return payload

    def migrate_smart_floor_outputs(self, output_path: Path | None = None) -> dict:
        payload = migrate_smart_floor_outputs(
            self.root,
            output_path=output_path or default_assimilation_migration_path(self.root),
        )
        self.log_event(
            "smart_floor_migration",
            "Migrated legacy flat outputs into smart-floor roots.",
            payload={
                "path": str(output_path or default_assimilation_migration_path(self.root)),
                "copied_file_count": payload.get("copied_file_count", 0),
            },
        )
        return payload

    def rehome_legacy_roots(self, output_path: Path | None = None) -> dict:
        payload = rehome_legacy_roots(
            self.root,
            output_path=output_path or default_legacy_rehome_path(self.root),
        )
        self.log_event(
            "legacy_root_rehome",
            "Rehomed legacy root directories into smart-floor storage.",
            payload={
                "path": str(output_path or default_legacy_rehome_path(self.root)),
                "moved_count": payload.get("moved_count", 0),
                "conflict_count": payload.get("conflict_count", 0),
            },
        )
        return payload

    def assimilate_external_roots(self, output_path: Path | None = None) -> dict:
        payload = assimilate_external_roots(
            self.root,
            output_path=output_path or default_external_root_assimilation_path(self.root),
        )
        self.registry = ReservoirRegistry()
        self.register_configured_sources()
        self.write_empirical_catalog(output_path=default_empirical_catalog_path(self.root))
        self.write_knowns_registry(output_path=default_knowns_registry_path(self.root))
        self.write_entity_registry(output_path=default_entity_registry_path(self.root))
        self.write_curated_tables_index(output_path=default_curated_tables_index_path(self.root))
        self.write_columnar_handoff(output_path=default_columnar_handoff_path(self.root))
        self.write_knowns_proofing_queue(output_path=default_knowns_proofing_queue_path(self.root))
        self.log_event(
            "external_root_assimilation",
            "Rehomed outer LightSpeed Consolidated roots into smart-floor reservoirs.",
            payload={
                "path": str(output_path or default_external_root_assimilation_path(self.root)),
                "moved_count": payload.get("moved_count", 0),
                "conflict_count": payload.get("conflict_count", 0),
                "updated_source_ids": payload.get("updated_source_ids", []),
            },
        )
        return payload

    def compaction_plan(
        self,
        *,
        force_refresh: bool = False,
        output_path: Path | None = None,
        manifest_threshold: int = 1000,
    ) -> dict:
        if force_refresh:
            return write_compaction_plan(self.root, output_path=output_path, manifest_threshold=manifest_threshold)
        cached = read_compaction_plan(self.root, output_path=output_path)
        if cached:
            return cached
        return write_compaction_plan(self.root, output_path=output_path, manifest_threshold=manifest_threshold)

    def write_compaction_plan(self, output_path: Path | None = None, *, manifest_threshold: int = 1000) -> dict:
        return self.compaction_plan(
            force_refresh=True,
            output_path=output_path,
            manifest_threshold=manifest_threshold,
        )

    def compaction_indexes(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_compaction_indexes(self.root, output_path=output_path)
        cached = read_compaction_indexes(self.root, output_path=output_path)
        if cached:
            return cached
        return write_compaction_indexes(self.root, output_path=output_path)

    def write_compaction_indexes(self, output_path: Path | None = None) -> dict:
        return self.compaction_indexes(force_refresh=True, output_path=output_path)

    def write_yearly_rollups(self, output_dir: Path | None = None) -> dict:
        return write_yearly_rollups(self.root, output_dir=output_dir)

    def archive_workflow(
        self,
        *,
        tool_name: str = "oracle_ingest_file",
        force_refresh: bool = False,
        output_path: Path | None = None,
        batch_size: int = 50000,
    ) -> dict:
        if force_refresh:
            return write_archive_workflow(
                self.root,
                output_path=output_path,
                tool_name=tool_name,
                batch_size=batch_size,
            )
        cached = read_archive_workflow(self.root, output_path=output_path, tool_name=tool_name)
        if cached:
            return cached
        return write_archive_workflow(
            self.root,
            output_path=output_path,
            tool_name=tool_name,
            batch_size=batch_size,
        )

    def write_archive_workflow(
        self,
        *,
        tool_name: str = "oracle_ingest_file",
        output_path: Path | None = None,
        batch_size: int = 50000,
    ) -> dict:
        return self.archive_workflow(
            tool_name=tool_name,
            force_refresh=True,
            output_path=output_path,
            batch_size=batch_size,
        )

    def archive_execution_state(
        self,
        *,
        tool_name: str = "oracle_ingest_file",
        force_refresh: bool = False,
        output_path: Path | None = None,
    ) -> dict:
        if force_refresh:
            return write_archive_execution_state(self.root, output_path=output_path, tool_name=tool_name)
        cached = read_archive_execution_state(self.root, output_path=output_path, tool_name=tool_name)
        if cached:
            return cached
        return write_archive_execution_state(self.root, output_path=output_path, tool_name=tool_name)

    def write_archive_execution_state(
        self,
        *,
        tool_name: str = "oracle_ingest_file",
        output_path: Path | None = None,
    ) -> dict:
        return self.archive_execution_state(
            tool_name=tool_name,
            force_refresh=True,
            output_path=output_path,
        )

    def stage_next_archive_batch(
        self,
        *,
        tool_name: str = "oracle_ingest_file",
        year: str | None = None,
        batch_number: int | None = None,
    ) -> dict:
        payload = stage_archive_batch(
            self.root,
            tool_name=tool_name,
            year=year,
            batch_number=batch_number,
        )
        self.log_event(
            "archive_batch_staged",
            f"Archive batch staging attempted for {tool_name}.",
            payload={
                "tool_name": tool_name,
                "year": year,
                "batch_number": batch_number,
                "staged": payload.get("staged"),
                "receipt_path": payload.get("receipt_path"),
            },
        )
        return payload

    def complete_staged_archive_batch(
        self,
        *,
        tool_name: str = "oracle_ingest_file",
        year: str | None = None,
        batch_number: int | None = None,
    ) -> dict:
        payload = complete_archive_batch(
            self.root,
            tool_name=tool_name,
            year=year,
            batch_number=batch_number,
        )
        self.log_event(
            "archive_batch_completed",
            f"Archive batch completion attempted for {tool_name}.",
            payload={
                "tool_name": tool_name,
                "year": year,
                "batch_number": batch_number,
                "completed": payload.get("completed"),
                "receipt_path": payload.get("receipt_path"),
            },
        )
        return payload

    def complete_archive_batch(
        self,
        *,
        tool_name: str = "oracle_ingest_file",
        year: str | None = None,
        batch_number: int | None = None,
        label: str | None = None,
        note: str | None = None,
    ) -> dict:
        return complete_archive_batch(
            self.root,
            tool_name=tool_name,
            year=year,
            batch_number=batch_number,
            label=label,
            note=note,
        )

    def legacy_runtime_diff(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_legacy_runtime_diff(self.root, output_path=output_path)
        return build_legacy_runtime_diff(self.root)

    def legacy_runtime_audit(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_legacy_runtime_audit(self.root, output_path=output_path)
        return build_legacy_runtime_audit(self.root)

    def cleanup_report(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_cleanup_report(self.root, output_path=output_path)
        return build_cleanup_report(self.root)

    def cleanup_candidate_report(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if force_refresh:
            return write_cleanup_candidate_report(self.root, output_path=output_path)
        return build_cleanup_candidate_report(self.root)

    def remove_safe_cache_dirs(self) -> dict:
        return remove_safe_cache_dirs(self.root)

    def sync_legacy_runtime_bundle(self, output_path: Path | None = None) -> dict:
        return sync_legacy_runtime_bundle(
            self.root,
            output_path=output_path or default_legacy_sync_path(self.root),
        )

    def remove_duplicate_legacy_exports(self, output_path: Path | None = None) -> dict:
        return remove_duplicate_legacy_exports(
            self.root,
            output_path=output_path or default_legacy_export_cleanup_path(self.root),
        )

    def remove_duplicate_generated_shell_files(self, output_path: Path | None = None) -> dict:
        return remove_duplicate_generated_shell_files(
            self.root,
            output_path=output_path or default_generated_shell_cleanup_path(self.root),
        )

    def dataindex_reduction(self, output_path: Path | None = None, *, apply: bool = False) -> dict:
        payload = reduce_dataindex_duplication(
            self.root,
            output_path=output_path or default_dataindex_reduction_path(self.root),
            apply=apply,
        )
        self.log_event(
            "dataindex_reduction",
            "Reduced dataindex duplication." if apply else "Planned dataindex reduction.",
            payload={
                "path": payload.get("report_path"),
                "applied": payload.get("applied", False),
                "moved_count": payload.get("moved_count", 0),
                "planned_move_count": payload.get("planned_move_count", 0),
            },
        )
        return payload

    def closure_readiness(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if not force_refresh:
            cached = read_closure_readiness(self.root, output_path=output_path)
            if cached:
                return cached
        return write_closure_readiness(self.root, output_path=output_path or default_closure_readiness_path(self.root))

    def write_closure_readiness(self, output_path: Path | None = None) -> dict:
        payload = self.closure_readiness(force_refresh=True, output_path=output_path)
        self.log_event(
            "closure_readiness",
            "Wrote closure readiness report.",
            payload={
                "path": str(output_path or default_closure_readiness_path(self.root)),
                "outer_safe_remove_count": len(payload.get("safe_remove_candidates", []) or []),
                "outer_manual_review_count": len(payload.get("manual_review_items", []) or []),
            },
        )
        return payload

    def remove_outer_zero_byte_placeholders(self, output_path: Path | None = None) -> dict:
        payload = remove_outer_zero_byte_placeholders(
            self.root,
            output_path=output_path or default_closure_readiness_path(self.root),
        )
        self.log_event(
            "closure_readiness_cleanup",
            "Removed safe outer zero-byte placeholders.",
            payload={
                "path": payload.get("report_path"),
                "removed_count": len(payload.get("removed", []) or []),
                "failed_count": len(payload.get("failed", []) or []),
            },
        )
        return payload

    def finalization_overview(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if not force_refresh:
            cached = read_finalization_overview(self.root, output_path=output_path)
            if cached:
                return cached
        execution_queues = self.execution_queues(force_refresh=force_refresh)
        cleanup = self.cleanup_report(force_refresh=force_refresh)
        cleanup_candidates = self.cleanup_candidate_report(force_refresh=force_refresh)
        try:
            assimilation = self.smart_floor_assimilation(force_refresh=force_refresh)
        except Exception:
            assimilation = {}
        layout = self.generated_layout_audit(force_refresh=force_refresh)
        dataindex = self.dataindex_reduction(apply=False)
        workflow_state = self.resumable_workflow_state(force_refresh=force_refresh)
        smith_router = self.smith_router_state(force_refresh=force_refresh)
        closure = self.closure_readiness(force_refresh=force_refresh)
        activity_tables = self.activity_tables(force_refresh=force_refresh)
        return write_finalization_overview(
            self.root,
            output_path=output_path or default_finalization_overview_path(self.root),
            execution_queues=execution_queues,
            cleanup_report=cleanup,
            cleanup_candidates=cleanup_candidates,
            assimilation=assimilation,
            generated_layout_audit=layout,
            dataindex_reduction=dataindex,
            workflow_state=workflow_state,
            smith_router=smith_router,
            closure_readiness=closure,
            activity_tables=activity_tables,
        )

    def write_finalization_overview(self, output_path: Path | None = None) -> dict:
        payload = self.finalization_overview(force_refresh=True, output_path=output_path)
        self.log_event(
            "finalization_overview",
            "Wrote consolidated finalization overview.",
            payload={
                "path": str(output_path or default_finalization_overview_path(self.root)),
                "completed_actions": (payload.get("status") or {}).get("completed_actions", 0),
                "pending_actions": (payload.get("status") or {}).get("pending_actions", 0),
                "source_root_kind": payload.get("source_root_kind"),
            },
        )
        return payload

    def execution_control(self, *, force_refresh: bool = False, output_path: Path | None = None) -> dict:
        if not force_refresh:
            cached = read_execution_control(self.root, output_path=output_path)
            if cached:
                return cached
        execution_queues = self.execution_queues()
        overview = self.finalization_overview()
        workflow_state = self.resumable_workflow_state()
        return write_execution_control(
            self.root,
            output_path=output_path or default_execution_control_path(self.root),
            execution_queues=execution_queues,
            finalization_overview=overview,
            workflow_state=workflow_state,
        )

    def write_execution_control(self, output_path: Path | None = None) -> dict:
        payload = self.execution_control(force_refresh=True, output_path=output_path)
        self.log_event(
            "execution_control",
            "Wrote Architect execution control surface.",
            payload={
                "path": str(output_path or default_execution_control_path(self.root)),
                "completed_actions": (payload.get("completion") or {}).get("completed_actions", 0),
                "pending_actions": (payload.get("completion") or {}).get("pending_actions", 0),
                "queue_root_kind": payload.get("queue_root_kind"),
            },
        )
        return payload

    def write_finalization_reports(self) -> dict:
        """Write the compact finalization pack with canonical source and snapshot destinations."""
        summary = self.write_generated_data_summary(output_path=default_summary_path(self.root))
        plan = self.write_compaction_plan(output_path=default_compaction_plan_path(self.root))
        indexes = self.write_compaction_indexes(output_path=default_compaction_index_path(self.root))
        rollups = self.write_yearly_rollups()
        archive = self.write_archive_workflow(output_path=default_archive_workflow_path(self.root))
        archive_state = self.write_archive_execution_state(output_path=default_archive_execution_state_path(self.root))
        ingestion = self.write_ingestion_preparation(output_path=default_ingestion_preparation_path(self.root))
        empirical = self.write_empirical_catalog(output_path=default_empirical_catalog_path(self.root))
        simulation_presets = self.write_simulation_presets(output_path=default_simulation_presets_path(self.root))
        knowns = self.write_knowns_registry(output_path=default_knowns_registry_path(self.root))
        definitions = self.write_oracle_definition_library(output_path=default_oracle_definition_library_path(self.root))
        it_dictionary = self.write_it_dictionary(output_path=default_it_dictionary_path(self.root))
        entity_registry = self.write_entity_registry(output_path=default_entity_registry_path(self.root))
        curated_tables = self.write_curated_tables_index(output_path=default_curated_tables_index_path(self.root))
        table_validation = self.write_table_validation_report(output_path=default_table_validation_report_path(self.root))
        bellcurve_overlay = self.write_bellcurve_overlay(output_path=default_bellcurve_overlay_path(self.root))
        scientific_query = self.write_scientific_query_layer(output_path=default_scientific_query_path(self.root))
        columnar_handoff = self.write_columnar_handoff(output_path=default_columnar_handoff_path(self.root))
        unit_validation = self.write_unit_validation_report(output_path=default_unit_validation_path(self.root))
        ui_alignment = self.write_ui_experience_alignment(output_path=default_ui_experience_alignment_path(self.root))
        ui_polish = self.write_ui_polish_contract(output_path=default_ui_polish_contract_path(self.root))
        operator_os = self.write_operator_os_contract(output_path=default_operator_os_contract_path(self.root))
        romer_web = self.write_romer_web_integration(output_path=default_romer_web_integration_path(self.root))
        bridge_health = self.write_bridge_health(output_path=default_bridge_health_path(self.root))
        walkthrough = self.write_walkthrough_readiness(output_path=default_walkthrough_readiness_path(self.root))
        knowns_queue = self.write_knowns_proofing_queue(output_path=default_knowns_proofing_queue_path(self.root))
        knowns_queue_objects = self.write_knowns_queue_objects(output_path=default_knowns_queue_objects_path(self.root))
        knowns_audit = self.write_knowns_declassification_audit(
            output_path=default_knowns_declassification_audit_path(self.root)
        )
        execution_queues = self.write_execution_queues(output_path=default_execution_queue_path(self.root))
        smith_router = self.write_smith_router_state(output_path=default_smith_router_path(self.root))
        workflow_state = self.write_resumable_workflow_state(output_path=default_workflow_state_path(self.root))
        romer_reference = self.write_romer_reference_path(output_path=default_romer_reference_path(self.root))
        layout = self.write_generated_layout_audit(output_path=default_generated_layout_audit_path(self.root))
        legacy_diff = self.legacy_runtime_diff(
            force_refresh=True,
            output_path=default_legacy_diff_path(self.root),
        )
        legacy_audit = self.legacy_runtime_audit(
            force_refresh=True,
            output_path=default_legacy_audit_path(self.root),
        )
        cleanup_candidates = self.cleanup_candidate_report(
            force_refresh=True,
            output_path=default_cleanup_candidates_path(self.root),
        )
        cleanup = self.cleanup_report(
            force_refresh=True,
            output_path=default_cleanup_report_path(self.root),
        )
        assimilation = self.write_smart_floor_assimilation()
        dataindex_reduction = self.dataindex_reduction(apply=False)
        closure_readiness = self.write_closure_readiness(output_path=default_closure_readiness_path(self.root))
        activity_tables = self.write_activity_tables(output_path=default_activity_tables_path(self.root))
        finalization_overview = write_finalization_overview(
            self.root,
            output_path=default_finalization_overview_path(self.root),
            execution_queues=execution_queues,
            cleanup_report=cleanup,
            cleanup_candidates=cleanup_candidates,
            assimilation=assimilation,
            generated_layout_audit=layout,
            dataindex_reduction=dataindex_reduction,
            workflow_state=workflow_state,
            smith_router=smith_router,
            closure_readiness=closure_readiness,
            activity_tables=activity_tables,
        )
        execution_control = write_execution_control(
            self.root,
            output_path=default_execution_control_path(self.root),
            execution_queues=execution_queues,
            finalization_overview=finalization_overview,
            workflow_state=workflow_state,
        )
        external_assimilation_path = str(default_external_root_assimilation_path(self.root))
        legacy_rehome_path = str(default_legacy_rehome_path(self.root))
        self.log_event(
            "finalization_reports",
            "Wrote finalization and cleanup reports.",
            payload={
                "summary_path": str(default_summary_path(self.root)),
                "ingestion_preparation_path": str(default_ingestion_preparation_path(self.root)),
                "empirical_catalog_path": str(default_empirical_catalog_path(self.root)),
                "simulation_presets_path": str(default_simulation_presets_path(self.root)),
                "knowns_registry_path": str(default_knowns_registry_path(self.root)),
                "oracle_definition_library_path": str(default_oracle_definition_library_path(self.root)),
                "it_dictionary_path": str(default_it_dictionary_path(self.root)),
                "entity_registry_path": str(default_entity_registry_path(self.root)),
                "dataset_manifest_index_path": str(default_dataset_manifest_index_path(self.root)),
                "curated_tables_index_path": str(default_curated_tables_index_path(self.root)),
                "table_validation_report_path": str(default_table_validation_report_path(self.root)),
                "bellcurve_overlay_path": str(default_bellcurve_overlay_path(self.root)),
                "scientific_query_layer_path": str(default_scientific_query_path(self.root)),
                "columnar_handoff_path": str(default_columnar_handoff_path(self.root)),
                "unit_validation_path": str(default_unit_validation_path(self.root)),
                "ui_experience_alignment_path": str(default_ui_experience_alignment_path(self.root)),
                "ui_polish_contract_path": str(default_ui_polish_contract_path(self.root)),
                "operator_os_contract_path": str(default_operator_os_contract_path(self.root)),
                "romer_web_integration_path": str(default_romer_web_integration_path(self.root)),
                "bridge_health_path": str(default_bridge_health_path(self.root)),
                "walkthrough_readiness_path": str(default_walkthrough_readiness_path(self.root)),
                "knowns_proofing_queue_path": str(default_knowns_proofing_queue_path(self.root)),
                "knowns_queue_objects_path": str(default_knowns_queue_objects_path(self.root)),
                "knowns_declassification_audit_path": str(default_knowns_declassification_audit_path(self.root)),
                "execution_queue_path": str(default_execution_queue_path(self.root)),
                "smith_router_path": str(default_smith_router_path(self.root)),
                "workflow_state_path": str(default_workflow_state_path(self.root)),
                "romer_reference_path": str(default_romer_reference_path(self.root)),
                "generated_layout_audit_path": str(default_generated_layout_audit_path(self.root)),
                "finalization_overview_path": str(default_finalization_overview_path(self.root)),
                "execution_control_path": str(default_execution_control_path(self.root)),
                "closure_readiness_path": str(default_closure_readiness_path(self.root)),
                "smart_floor_assimilation_path": str(default_assimilation_report_path(self.root)),
                "external_root_assimilation_path": external_assimilation_path,
                "legacy_rehome_path": legacy_rehome_path,
            },
        )
        return {
            "summary_path": str(default_summary_path(self.root)),
            "compaction_plan_path": str(default_compaction_plan_path(self.root)),
            "compaction_index_path": str(default_compaction_index_path(self.root)),
            "archive_workflow_path": str(default_archive_workflow_path(self.root)),
            "archive_execution_state_path": str(default_archive_execution_state_path(self.root)),
            "ingestion_preparation_path": str(default_ingestion_preparation_path(self.root)),
            "empirical_catalog_path": str(default_empirical_catalog_path(self.root)),
            "simulation_presets_path": str(default_simulation_presets_path(self.root)),
            "knowns_registry_path": str(default_knowns_registry_path(self.root)),
            "oracle_definition_library_path": str(default_oracle_definition_library_path(self.root)),
            "it_dictionary_path": str(default_it_dictionary_path(self.root)),
            "entity_registry_path": str(default_entity_registry_path(self.root)),
            "dataset_manifest_index_path": str(default_dataset_manifest_index_path(self.root)),
            "curated_tables_index_path": str(default_curated_tables_index_path(self.root)),
            "table_validation_report_path": str(default_table_validation_report_path(self.root)),
            "bellcurve_overlay_path": str(default_bellcurve_overlay_path(self.root)),
            "scientific_query_layer_path": str(default_scientific_query_path(self.root)),
            "columnar_handoff_path": str(default_columnar_handoff_path(self.root)),
            "unit_validation_path": str(default_unit_validation_path(self.root)),
            "ui_experience_alignment_path": str(default_ui_experience_alignment_path(self.root)),
            "ui_polish_contract_path": str(default_ui_polish_contract_path(self.root)),
            "operator_os_contract_path": str(default_operator_os_contract_path(self.root)),
            "romer_web_integration_path": str(default_romer_web_integration_path(self.root)),
            "bridge_health_path": str(default_bridge_health_path(self.root)),
            "walkthrough_readiness_path": str(default_walkthrough_readiness_path(self.root)),
            "knowns_proofing_queue_path": str(default_knowns_proofing_queue_path(self.root)),
            "knowns_queue_objects_path": str(default_knowns_queue_objects_path(self.root)),
            "knowns_declassification_audit_path": str(default_knowns_declassification_audit_path(self.root)),
            "smith_router_path": str(default_smith_router_path(self.root)),
            "workflow_state_path": str(default_workflow_state_path(self.root)),
            "romer_reference_path": str(default_romer_reference_path(self.root)),
            "generated_layout_audit_path": str(default_generated_layout_audit_path(self.root)),
            "finalization_overview_path": str(default_finalization_overview_path(self.root)),
            "execution_control_path": str(default_execution_control_path(self.root)),
            "closure_readiness_path": str(default_closure_readiness_path(self.root)),
            "activity_tables_path": str(default_activity_tables_path(self.root)),
            "legacy_runtime_diff_path": str(default_legacy_diff_path(self.root)),
            "legacy_runtime_audit_path": str(default_legacy_audit_path(self.root)),
            "legacy_runtime_sync_path": str(default_legacy_sync_path(self.root)),
            "legacy_export_cleanup_path": str(default_legacy_export_cleanup_path(self.root)),
            "legacy_root_rehome_path": legacy_rehome_path,
            "cleanup_candidates_path": str(default_cleanup_candidates_path(self.root)),
            "cleanup_report_path": str(default_cleanup_report_path(self.root)),
            "smart_floor_assimilation_path": str(default_assimilation_report_path(self.root)),
            "external_root_assimilation_path": external_assimilation_path,
            "summary": summary,
            "compaction_plan": plan,
            "compaction_indexes": indexes,
            "rollups": rollups,
            "archive_workflow": archive,
            "archive_execution_state": archive_state,
            "ingestion_preparation": ingestion,
            "empirical_catalog": empirical,
            "simulation_presets": simulation_presets,
            "knowns_registry": knowns,
            "oracle_definition_library": definitions,
            "it_dictionary": it_dictionary,
            "entity_registry": entity_registry,
            "curated_tables": curated_tables,
            "table_validation": table_validation,
            "bellcurve_overlay": bellcurve_overlay,
            "scientific_query": scientific_query,
            "columnar_handoff": columnar_handoff,
            "unit_validation": unit_validation,
            "ui_experience_alignment": ui_alignment,
            "ui_polish_contract": ui_polish,
            "operator_os_contract": operator_os,
            "romer_web_integration": romer_web,
            "bridge_health": bridge_health,
            "walkthrough_readiness": walkthrough,
            "knowns_proofing_queue": knowns_queue,
            "knowns_queue_objects": knowns_queue_objects,
            "knowns_declassification_audit": knowns_audit,
            "execution_queues": execution_queues,
            "smith_router": smith_router,
            "workflow_state": workflow_state,
            "romer_reference_path_payload": romer_reference,
            "generated_layout_audit": layout,
            "dataindex_reduction": dataindex_reduction,
            "closure_readiness": closure_readiness,
            "activity_tables": activity_tables,
            "finalization_overview": finalization_overview,
            "execution_control": execution_control,
            "legacy_runtime_diff": legacy_diff,
            "legacy_runtime_audit": legacy_audit,
            "cleanup_candidates": cleanup_candidates,
            "cleanup_report": cleanup,
            "smart_floor_assimilation": assimilation,
        }

    def migrate_legacy_runtime_bundle(self) -> dict:
        legacy_root = legacy_runtime_exports_root(self.root)
        summary = {
            "legacy_root": str(legacy_root),
            "runtime_exports": [],
            "publish_packages": [],
            "migrated": False,
        }
        if not legacy_root.exists():
            return summary

        runtime_target = self.runtime_export_root() / "legacy_bundle"
        publish_target = self.publish_root() / "legacy_bundle"
        runtime_target.mkdir(parents=True, exist_ok=True)
        publish_target.mkdir(parents=True, exist_ok=True)

        for relative in (
            Path("reservoir_snapshot.json"),
            Path("website") / "romer_manifest.json",
        ):
            source = legacy_root / relative
            if not source.exists():
                continue
            destination = runtime_target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            summary["runtime_exports"].append(str(destination))

        packages_root = legacy_root / "packages"
        if packages_root.exists():
            for package_dir in sorted(path for path in packages_root.iterdir() if path.is_dir()):
                destination = publish_target / package_dir.name
                shutil.copytree(package_dir, destination, dirs_exist_ok=True)
                summary["publish_packages"].append(str(destination))

        if summary["runtime_exports"] or summary["publish_packages"]:
            summary["migrated"] = True
        return summary
