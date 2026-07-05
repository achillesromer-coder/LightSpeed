from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lightspeed_runtime.storage_paths import architect_root


@dataclass(frozen=True)
class ConsolidationRecord:
    area: str
    owner_floor: str
    final_runtime_files: tuple[str, ...]
    final_data_outputs: tuple[str, ...]
    merged_attempts: tuple[str, ...]
    superseded_patterns: tuple[str, ...]
    final_call_chain: tuple[str, ...]
    refinement_status: str
    packaging_gate: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CONSOLIDATION_RECORDS: tuple[ConsolidationRecord, ...] = (
    ConsolidationRecord(
        area="Project Bento wall and smart widgets",
        owner_floor="Trinity",
        final_runtime_files=(
            "lightspeed_runtime/project_component_wall.py",
            "lightspeed_runtime/smart_floor_visuals.py",
            "lightspeed_runtime/ui_polish.py",
        ),
        final_data_outputs=(
            "Z Axis/Z+3_Trinity/data/ui/smart_floor_widget_export.json",
            "Z Axis/Z+3_Trinity/data/ui/smart_floor_visual_catalog.json",
            "dataindex/22_SMART_FLOOR_VISUAL_ANALYSIS.md",
        ),
        merged_attempts=(
            "dataindex/18_COMPLETED_LIVE_PROJECT_WALL_UI.md",
            "dataindex/19_COMPLETED_LIVE_PROJECT_WALL_UI_2.md",
            "dataindex/19_COMPLETED_PROJECT_WALL_MODEL_2.md",
            "dataindex/13_UX_AMALGAMATION_PASS.md",
        ),
        superseded_patterns=(
            "standalone floor feature pages for every interaction",
            "static-only project icon boards without smart widget contracts",
            "untyped preview/open actions hard-coded only in UI handlers",
        ),
        final_call_chain=(
            "Trinity shell selects project",
            "project_component_wall.ensure_project_wall creates component sets",
            "smart_floor_visuals.project_wall_smart_widget_descriptors provides floor widgets",
            "project wall preview/drawer/action descriptors expose edit, fullscreen, and Z Direct actions",
        ),
        refinement_status="implemented_and_tested",
        packaging_gate="Bind live renderers for PDF/image/map/simulation tiles before V0.10.0 walkthrough.",
    ),
    ConsolidationRecord(
        area="Smart-floor visual, chart, 3D map, and simulation contracts",
        owner_floor="Trinity + TheConstruct",
        final_runtime_files=("lightspeed_runtime/smart_floor_visuals.py",),
        final_data_outputs=(
            "Z Axis/Z+3_Trinity/data/ui/smart_floor_visual_catalog.json",
            "Z Axis/Z+3_Trinity/data/ui/smart_floor_widget_export.json",
            "dataindex/22_SMART_FLOOR_VISUAL_ANALYSIS.md",
        ),
        merged_attempts=(
            "dataindex/08_SMART_FLOOR_ASSIMILATION.md",
            "dataindex/20_COMPLETED_FLOOR_WORKFLOW_DESCRIPTORS.md",
            "dataindex/21_ROLLING_35_COMPLETE.md",
        ),
        superseded_patterns=(
            "floor-specific chart/map ideas documented but not discoverable by the UI",
            "Construct simulation features detached from project wall artifacts",
            "bulk asteroid mapping before zoning/cluster/gmat target separation",
        ),
        final_call_chain=(
            "smart_floor_visuals.FLOOR_VISUAL_CONTRACTS defines all 8 floor surfaces",
            "visual catalog exposes widgets, charts, 3D maps, tools, simulation hooks, and smoke checks",
            "widget export converts floor contracts into project-wall Bento smart widgets",
            "fidelity matrix verifies Construct, Oracle, Morpheus, Smith, and Merovingian critical flows",
        ),
        refinement_status="implemented_and_tested",
        packaging_gate="Attach renderer implementations to descriptor routes: chart panel, map panel, Construct simulation preview.",
    ),
    ConsolidationRecord(
        area="Oracle ingestion, dictionary, datatables, and Morpheus proofing",
        owner_floor="Oracle + Morpheus",
        final_runtime_files=(
            "lightspeed_runtime/floor_workflow_descriptors.py",
            "lightspeed_runtime/smart_floor_visuals.py",
            "lightspeed_runtime/project_component_wall.py",
        ),
        final_data_outputs=(
            "Z Axis/Z+3_Trinity/data/ui/smart_floor_visual_catalog.json",
            "dataindex/20_COMPLETED_FLOOR_WORKFLOW_DESCRIPTORS.md",
        ),
        merged_attempts=(
            "dataindex/15_COMPLETED_TASKS_DICTIONARY.md",
            "dataindex/18_COMPLETED_PREVIEW_MODEL.md",
            "dataindex/21_ROLLING_35_COMPLETE.md",
        ),
        superseded_patterns=(
            "dictionary terms mentioned in prose but not searchable as data",
            "Oracle originals mixed with proofed derived working components",
            "proof status hidden inside free-text logs",
        ),
        final_call_chain=(
            "Oracle keeps original_file and extracted_component records",
            "project wall previews preserve Oracle provenance tags",
            "Morpheus owns proof_record, claim_record, source comparison, and confidence widgets",
            "proofed knowns return to Oracle dictionary, datatables, library, and encyclopedia surfaces",
        ),
        refinement_status="contracted_and_partially_bound",
        packaging_gate="Bind Dictionary.IT search/add-category UI to the Oracle/Morpheus data contracts.",
    ),
    ConsolidationRecord(
        area="Z Direct handoff, Smith receipts, and dependency approvals",
        owner_floor="Smith",
        final_runtime_files=(
            "lightspeed_runtime/project_component_wall.py",
            "lightspeed_runtime/floor_workflow_descriptors.py",
            "lightspeed_runtime/dependency_approvals.py",
        ),
        final_data_outputs=(
            "Z Axis/Z+3_Trinity/data/ui/smart_floor_widget_export.json",
            "dataindex/18_COMPLETED_BACKGROUND_DEPENDENCIES.md",
        ),
        merged_attempts=(
            "dataindex/16_RECURSIVE_ALIGNMENT_QUEUE.md",
            "dataindex/17_3_AGENT_15_COMPLETE_35_QUEUE.md",
            "dataindex/21_ROLLING_35_COMPLETE.md",
        ),
        superseded_patterns=(
            "untracked task handoffs without receipt state",
            "automatic dependency installation without approval",
            "multiple queue notes not connected to project artifacts",
        ),
        final_call_chain=(
            "project wall create_z_direct_handoff writes project-local receipt JSON",
            "Smith receipt state table defines received, updated, completed, deleted, declassified, failed",
            "dependency_approvals creates approval-gated install/tool requests",
            "Merovingian audits queue results and diagnostics",
        ),
        refinement_status="implemented_and_tested",
        packaging_gate="Connect live Smith queue UI to the descriptor-backed receipt states.",
    ),
    ConsolidationRecord(
        area="Trinity settings, theme/background builder, startup, and controls",
        owner_floor="Trinity",
        final_runtime_files=(
            "lightspeed_runtime/ui_polish.py",
            "lightspeed_runtime/background_application.py",
            "lightspeed_runtime/startup_options.py",
            "lightspeed_runtime/ui_experience.py",
        ),
        final_data_outputs=(
            "Z Axis/Z+3_Trinity/data/ui/ui_polish_contract.json",
            "Z Axis/Z+3_Trinity/data/ui/ui_experience_alignment.json",
            "dataindex/13_UX_AMALGAMATION_PASS.md",
        ),
        merged_attempts=(
            "theme manager attempts",
            "settings wizard attempts",
            "first-run/startup controls",
            "Holospace button / workspace button overlap",
        ),
        superseded_patterns=(
            "separate theme manager, settings page, and wizard state",
            "Holospace as a duplicate top-level workspace button",
            "hidden primary-click settings interactions",
        ),
        final_call_chain=(
            "Trinity settings library owns shared UI configuration",
            "first-run wizard, Ctrl+Shift+S, widget settings, and page settings call the same contract",
            "single Z-floor dropdown handles floor navigation and active-floor handoff",
            "background/theme tokens propagate to shell, Bento, preview drawer, charts, maps, and simulations",
        ),
        refinement_status="contracted_and_partially_bound",
        packaging_gate="Apply background/theme tokens inside live chart/map/simulation renderers.",
    ),
    ConsolidationRecord(
        area="Release clean, publish snapshot, D-root packaging, and file culls",
        owner_floor="Architect + Merovingian",
        final_runtime_files=(
            "lightspeed_runtime/release_clean.py",
            "lightspeed_runtime/publish_snapshot.py",
            "lightspeed_runtime/storage_paths.py",
        ),
        final_data_outputs=(
            "dataindex/20_COMPLETED_RELEASE_PUBLISH_CULL.md",
            "dataindex/21_ROLLING_35_COMPLETE.md",
        ),
        merged_attempts=(
            "W6/w6 cleanup requests",
            "runtime/canonical runtime relocation requests",
            "D-root snapshot clarification",
        ),
        superseded_patterns=(
            "using D-root as a live working copy",
            "w6 as active runtime floor",
            "deleting old files without proof of preserved information",
        ),
        final_call_chain=(
            "C-root remains live source of truth",
            "Architect publish_snapshot writes overwrite-only D-root snapshot when approved",
            "Merovingian release_clean identifies cull candidates and report state",
            "AI logs and launch-readiness reports move to the outer consolidated archive only after the complete final pass",
            "Smith executes approved filesystem actions only after receipt/approval",
        ),
        refinement_status="implemented_as_dry_run_contract",
        packaging_gate="Run final release-clean dry run, then move AI logs/reports to the outer LightSpeed Consolidated archive before package write.",
    ),
    ConsolidationRecord(
        area="8am orchestration, progress bars, and process/token budget",
        owner_floor="Neo",
        final_runtime_files=("lightspeed_runtime/orchestration_window.py",),
        final_data_outputs=(
            "Z Axis/Z+2_Neo/data/actions/orchestration_8am_plan.json",
            "dataindex/24_8AM_ORCHESTRATION_RUN.md",
        ),
        merged_attempts=(
            "three-agent orchestration requests",
            "live progress bar requests",
            "process count warnings",
        ),
        superseded_patterns=(
            "unbounded recursive scans",
            "long silent full test runs without process cleanup",
            "loose agent instructions not represented as runtime plan",
        ),
        final_call_chain=(
            "Neo plan records agent roles, deadline, cadence, resource rules, and progress bars",
            "local critical path stops stalled processes and uses bounded tests",
            "results flow into dataindex and Architect finalization instead of loose logs",
        ),
        refinement_status="implemented_and_tested",
        packaging_gate="After usage limit resets, rerun unresolved-task delegation from the persisted plan if needed.",
    ),
    ConsolidationRecord(
        area="Readiness, diagnostics, assets, and smoke proofing",
        owner_floor="Merovingian",
        final_runtime_files=(
            "verify_launch_ready.py",
            "Z Axis/Z+3_Trinity/diagnostics/complete_diagnostic_system.py",
            "lightspeed_runtime/consolidation_registry.py",
        ),
        final_data_outputs=(
            "Z Axis/Z-4_Merovingian/data/reports/launch_readiness",
            "dataindex/25_CONSOLIDATION_REFINEMENT_PASS.md",
        ),
        merged_attempts=(
            "previous smoke report failures",
            "asset manager missing module warnings",
            "calculator_modules table and AI logs directory checks",
        ),
        superseded_patterns=(
            "console-only test output not written into finalization context",
            "diagnostic warnings accepted without owner floor or next gate",
            "generated cache files left after tests",
        ),
        final_call_chain=(
            "verify_launch_ready.py proves structure, entrypoints, floors, and core services",
            "complete_diagnostic_system.py proves assets, database, UI, integrations, and performance",
            "consolidation registry proves canonical files exist and records packaging gates",
        ),
        refinement_status="implemented_and_tested",
        packaging_gate="Run final diagnostics immediately before V0.10.0 packaging and record result path.",
    ),
    ConsolidationRecord(
        area="Protocol sequences, shared controls, external web hooks, and LightSpeed GO",
        owner_floor="Trinity + Neo + Smith",
        final_runtime_files=(
            "lightspeed_runtime/protocol_sequence_registry.py",
            "lightspeed_runtime/web_integration.py",
            "lightspeed_runtime/operator_os.py",
        ),
        final_data_outputs=(
            "Z Axis/Z+3_Trinity/data/ui/protocol_sequence_registry.json",
            "Z Axis/Z+2_Neo/data/actions/achilles_external_handoff.json",
            "dataindex/26_PROTOCOL_SEQUENCE_REFINEMENT.md",
        ),
        merged_attempts=(
            "shared settings/color control requests",
            "Z Direct cache/preload requests",
            "website/Sheets/webhook integration requests",
            "Future LightSpeed GO phone dash request",
        ),
        superseded_patterns=(
            "separate color functions for each UI surface",
            "floor-to-floor calls that reload heavy artifacts instead of cached descriptors",
            "external Sheet/webhook ideas not represented as operator handoff contracts",
        ),
        final_call_chain=(
            "Trinity owns shared color/loading/control protocols",
            "Smith owns Z Direct cache/preload and external row write queue",
            "Neo owns Achilles external handoff and future LightSpeed GO task intent",
            "Oracle/Morpheus/Architect gate source, proof, and publish state before external writes",
        ),
        refinement_status="implemented_and_tested",
        packaging_gate="Before packaging, confirm external writes remain approval-gated and no Drive/Sheets payloads are bundled into the app.",
    ),
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_consolidation_json_path(root: Path) -> Path:
    return architect_root(root) / "finalization" / "consolidation_register.json"


def default_consolidation_report_path(root: Path) -> Path:
    return Path(root) / "dataindex" / "25_CONSOLIDATION_REFINEMENT_PASS.md"


def _path_status(root: Path, relative_path: str) -> dict[str, Any]:
    path = Path(root) / relative_path
    exists = path.exists()
    return {
        "path": relative_path,
        "exists": exists,
        "kind": "directory" if path.is_dir() else "file" if path.is_file() else "missing",
        "size_bytes": path.stat().st_size if path.is_file() else None,
    }


def build_consolidation_register(root: Path) -> dict[str, Any]:
    root = Path(root)
    records = []
    missing_canonical: list[str] = []
    for record in CONSOLIDATION_RECORDS:
        runtime_status = [_path_status(root, path) for path in record.final_runtime_files]
        output_status = [_path_status(root, path) for path in record.final_data_outputs]
        for item in runtime_status + output_status:
            if not item["exists"]:
                missing_canonical.append(item["path"])
        payload = record.to_dict()
        payload["runtime_status"] = runtime_status
        payload["output_status"] = output_status
        payload["canonical_complete"] = not any(not item["exists"] for item in runtime_status + output_status)
        records.append(payload)

    return {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "purpose": "Executable consolidation map for overlapping LightSpeed build attempts before final run and packaging.",
        "record_count": len(records),
        "canonical_complete_count": sum(1 for record in records if record["canonical_complete"]),
        "missing_canonical": sorted(set(missing_canonical)),
        "records": records,
        "next_packaging_sequence": [
            "Regenerate visual catalog, widget export, UI polish contract, orchestration plan, and consolidation register.",
            "Run focused runtime tests for consolidation, smart-floor visuals, project wall, UI polish, and orchestration.",
            "Run launch readiness and complete diagnostics.",
            "Run release-clean dry run and review stale roots before D-root publish snapshot.",
            "After the complete final pass, move AI logs and non-package reports to the outer LightSpeed Consolidated archive.",
            "Confirm protocol registry and Achilles external handoff are generated and external writes remain approval-gated.",
            "Package V0.10.0 only after all warnings have an owner floor and packaging gate.",
        ],
    }


def write_consolidation_register(
    root: Path,
    *,
    json_path: Path | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    root = Path(root)
    payload = build_consolidation_register(root)
    json_destination = json_path or default_consolidation_json_path(root)
    report_destination = report_path or default_consolidation_report_path(root)

    json_destination.parent.mkdir(parents=True, exist_ok=True)
    json_destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Consolidation Refinement Pass",
        "",
        f"Generated: {payload['generated_at']}",
        f"Canonical complete: {payload['canonical_complete_count']}/{payload['record_count']}",
        "",
        "## Akin Files And Final Owners",
        "",
        "| Area | Owner | Runtime | Outputs | Status | Packaging gate |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in payload["records"]:
        runtime = "<br>".join(record["final_runtime_files"])
        outputs = "<br>".join(record["final_data_outputs"])
        status = "complete" if record["canonical_complete"] else "missing"
        lines.append(
            f"| {record['area']} | {record['owner_floor']} | {runtime} | {outputs} | {status} | {record['packaging_gate']} |"
        )

    lines.extend(["", "## Superseded Double-Ups", ""])
    for record in payload["records"]:
        lines.append(f"### {record['area']}")
        for pattern in record["superseded_patterns"]:
            lines.append(f"- {pattern}")

    lines.extend(["", "## Next Packaging Sequence", ""])
    lines.extend(f"- {item}" for item in payload["next_packaging_sequence"])
    if payload["missing_canonical"]:
        lines.extend(["", "## Missing Canonical Files", ""])
        lines.extend(f"- {item}" for item in payload["missing_canonical"])

    report_destination.parent.mkdir(parents=True, exist_ok=True)
    report_destination.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload["json_path"] = str(json_destination)
    payload["report_path"] = str(report_destination)
    return payload
