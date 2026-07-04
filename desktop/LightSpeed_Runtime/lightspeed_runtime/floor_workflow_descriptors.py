from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class DescriptorContract:
    name: str
    floor: str
    descriptor_type: str
    fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _base_descriptor(name: str, floor: str, descriptor_type: str, **fields: Any) -> dict[str, Any]:
    return DescriptorContract(
        name=name,
        floor=floor,
        descriptor_type=descriptor_type,
        fields=fields,
    ).to_dict()


def oracle_morpheus_split_view_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "oracle_morpheus_split_view",
        "Oracle",
        "split_view",
        owner_floor="Oracle",
        source_policy={
            "originals": "canonical_source_of_truth",
            "extracted_components": "derived_working_components",
            "edit_rules": ["preserve_originals", "write_extracted_components_only_when_proved"],
        },
        proof_status={
            "originals": "proof_required",
            "extracted_components": "proofed_or_pending_proof",
            "review_floor": "Morpheus",
        },
        panes=[
            {"pane": "originals", "mode": "read_only", "title": "Original Sources"},
            {"pane": "extracted_components", "mode": "workbench", "title": "Extracted Components"},
        ],
        routing={
            "originals_target": "Oracle",
            "extracted_target": "Morpheus",
            "handoff": "Oracle_to_Morpheus",
        },
    )


def smith_receipt_state_table_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "smith_receipt_state_table",
        "Smith",
        "state_table",
        owner_floor="Smith",
        states=[
            {"state": "received", "meaning": "receipt_confirmed"},
            {"state": "updated", "meaning": "receipt_modified"},
            {"state": "completed", "meaning": "receipt_closed"},
            {"state": "deleted", "meaning": "receipt_removed"},
            {"state": "declassified", "meaning": "receipt_unsealed"},
            {"state": "failed", "meaning": "receipt_failed"},
        ],
        columns=[
            "receipt_id",
            "source_floor",
            "state",
            "timestamp",
            "actor",
            "notes",
        ],
        receipt_policy={
            "terminal_states": ["completed", "deleted", "failed"],
            "review_required": ["updated", "declassified"],
        },
    )


def construct_simulation_artifact_rerun_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "construct_simulation_artifact_rerun",
        "TheConstruct",
        "rerun_metadata",
        owner_floor="TheConstruct",
        parameters={
            "scenario_id": None,
            "case_id": None,
            "timestep": None,
            "integration_window": None,
        },
        ephemerides={
            "source": None,
            "epoch": None,
            "reference_frame": None,
        },
        engine={
            "name": None,
            "version": None,
            "mode": "simulation_rerun",
        },
        export_targets=[
            {"target": "parquet", "status": "available"},
            {"target": "json", "status": "available"},
            {"target": "gmat_bundle", "status": "available"},
        ],
        rerun_status={
            "state": "queued",
            "last_run_id": None,
            "last_export_id": None,
        },
    )


def construct_heliocentric_zoning_summary_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "construct_heliocentric_zoning_summary",
        "TheConstruct",
        "summary_widget",
        owner_floor="TheConstruct",
        zones={
            "bands": [],
            "bands_source": "heliocentric_zoning_grid",
        },
        clusters={
            "cluster_strategy": ["kmeans", "hdbscan", "histogram_peaks"],
            "high_value_clusters": [],
        },
        target_shortlist={
            "top_n": 0,
            "targets": [],
        },
        gmat_batch_export={
            "enabled": True,
            "export_format": "gmat_batch",
            "status": "available",
        },
        validation_fields={
            "zone_count": 0,
            "cluster_count": 0,
            "target_count": 0,
            "last_validated_at": None,
        },
    )


def construct_visual_render_engine_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "construct_visual_render_engine",
        "TheConstruct",
        "render_runtime",
        owner_floor="TheConstruct",
        default_surface="ambient_embed",
        render_modes=[
            {"mode": "ambient_embed", "target_fps": 33, "boot_default": True},
            {"mode": "tower_overlay", "target_fps": 45, "boot_default": False},
            {"mode": "immersive_full", "target_fps": 60, "manual_only": True},
        ],
        resource_guards={
            "max_visible_widgets": 36,
            "max_live_texture_panels": 8,
            "max_parallel_render_jobs": 1,
            "max_background_simulations": 1,
        },
        data_policy={
            "bulk_datasets": "reference_c_until_rehome",
            "runtime_exports": "d_drive_only",
            "publish_gate": "architect_approval_required",
        },
        surfaces=[
            {"surface": "immersive_3d_engine", "role": "ambient_or_manual_full_world"},
            {"surface": "cognigrex_3d_environment", "role": "tower_and_widget_overlay"},
            {"surface": "z_tower_renderer", "role": "tower_core_renderer"},
            {"surface": "floor_widgets_3d", "role": "interactive_floor_panels"},
        ],
    )


def construct_virtual_space_smoke_test_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "construct_virtual_space_smoke_test",
        "TheConstruct",
        "virtual_space_test_matrix",
        owner_floor="TheConstruct",
        smoke_lanes=[
            {"lane_id": "construct_boot_contract", "surface": "runtime_profile"},
            {"lane_id": "ambient_embed_smoke", "surface": "immersive_3d_engine"},
            {"lane_id": "tower_overlay_smoke", "surface": "cognigrex_3d_environment"},
            {"lane_id": "widget_panel_texture_smoke", "surface": "floor_widgets_3d"},
        ],
        manual_lanes=[
            {"lane_id": "immersive_full_launch", "surface": "immersive_3d_engine"},
            {"lane_id": "dataset_attach_and_scenario_preview", "surface": "scenario_lab"},
        ],
        success_contract={
            "ambient_embed": "renders_without_input_capture",
            "tower_overlay": "renders_with_bounded_widget_budget",
            "immersive_full": "manual_launch_and_clean_return",
        },
        failure_policy={
            "route_to": "Merovingian",
            "evidence": ["logs", "runtime_profile", "test_matrix"],
        },
    )


def trinity_single_interface_lane_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "trinity_single_interface_lane",
        "Trinity",
        "lane_shell",
        owner_floor="Trinity",
        interface_mode="single_surface_bento_shell",
        intake_mode="single_operator_surface",
        approval_input_mode="y_n_and_review_artifacts",
        avoid_patterns=[
            "hyper_tabs",
            "duplicate_portals",
            "parallel_popup_workflows",
            "unbounded_background_actions",
        ],
        attached_floors=["Trinity", "Neo", "Smith", "Architect"],
        operator_contract={
            "entry_surface": "N.py -> Trinity operator surface",
            "queue_visibility": "required",
            "approval_visibility": "required",
            "settings_visibility": "required",
        },
    )


def smart_floor_population_space_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "smart_floor_population_space",
        "TheConstruct",
        "population_space",
        owner_floor="TheConstruct",
        population_contract="empty_expansive_spaces_attach_only_proofed_sets",
        single_interface_goal="each_floor_operates_as_one_lab_or_workbench",
        no_risk_entry=True,
        default_spaces=[
            {"floor": "Trinity", "space": "Operator Atrium", "default_view": "lane_overview"},
            {"floor": "Smith", "space": "Route Foundry", "default_view": "build_task_queue"},
            {"floor": "Oracle", "space": "Reservoir Library", "default_view": "source_library"},
            {"floor": "Morpheus", "space": "Review Chamber", "default_view": "evidence_split_view"},
            {"floor": "TheConstruct", "space": "Digital Twin Atrium", "default_view": "ambient_embed"},
        ],
        population_inputs=["proofed_datasets", "scenario_manifests", "render_runtime", "review_packets"],
    )


def smith_gated_build_task_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "smith_gated_build_task",
        "Smith",
        "build_queue",
        owner_floor="Smith",
        default_state="ready_no_risk_seed",
        execution_mode="agent_assist_with_manual_y_n_gate",
        approval_policy={
            "input_mode": "y_n",
            "artifact_review_required": True,
            "write_scope": "owned_floor_paths_only",
            "external_publish_blocked": True,
        },
        covered_lanes=[
            "operator_shell",
            "knowledge_library",
            "review_and_corroboration",
            "simulation_twin",
            "publish_and_governance",
        ],
        risk_contract={
            "default_risk_level": "low",
            "publish_actions": "manual_gate_only",
            "destructive_actions": "manual_gate_only",
        },
    )


def architect_publish_snapshot_descriptor() -> dict[str, Any]:
    return _base_descriptor(
        "architect_publish_snapshot",
        "Architect",
        "publish_snapshot",
        owner_floor="Architect",
        packaging_policy={
            "d_root": "overwrite_only_snapshot",
            "c_root": "live_source_of_truth",
            "preserve_live_source": True,
        },
        snapshot_targets=[
            {"root": "D-root", "purpose": "published_snapshot"},
            {"root": "C-root", "purpose": "live_source"},
        ],
        publication_state={
            "status": "draft",
            "overwrite_only": True,
            "snapshot_locked": False,
        },
        audit_fields={
            "published_at": None,
            "published_by": None,
            "source_revision": None,
        },
    )


def build_floor_workflow_descriptor_catalog() -> dict[str, dict[str, Any]]:
    return {
        "OracleMorpheusSplitView": oracle_morpheus_split_view_descriptor(),
        "SmithReceiptStateTable": smith_receipt_state_table_descriptor(),
        "TrinitySingleInterfaceLane": trinity_single_interface_lane_descriptor(),
        "SmartFloorPopulationSpace": smart_floor_population_space_descriptor(),
        "SmithGatedBuildTask": smith_gated_build_task_descriptor(),
        "ConstructSimulationArtifactRerun": construct_simulation_artifact_rerun_descriptor(),
        "ConstructHeliocentricZoningSummary": construct_heliocentric_zoning_summary_descriptor(),
        "ConstructVisualRenderEngine": construct_visual_render_engine_descriptor(),
        "ConstructVirtualSpaceSmokeTest": construct_virtual_space_smoke_test_descriptor(),
        "ArchitectPublishSnapshot": architect_publish_snapshot_descriptor(),
    }
