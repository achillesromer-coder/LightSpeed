from __future__ import annotations

from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.floor_workflow_descriptors import (
    architect_publish_snapshot_descriptor,
    build_floor_workflow_descriptor_catalog,
    construct_heliocentric_zoning_summary_descriptor,
    construct_simulation_artifact_rerun_descriptor,
    oracle_morpheus_split_view_descriptor,
    smith_receipt_state_table_descriptor,
)


def test_oracle_morpheus_split_view_descriptor_has_owner_policy_and_proof_status() -> None:
    descriptor = oracle_morpheus_split_view_descriptor()

    assert descriptor["floor"] == "Oracle"
    assert descriptor["fields"]["owner_floor"] == "Oracle"
    assert descriptor["fields"]["source_policy"]["originals"] == "canonical_source_of_truth"
    assert descriptor["fields"]["source_policy"]["extracted_components"] == "derived_working_components"
    assert descriptor["fields"]["proof_status"]["review_floor"] == "Morpheus"
    assert {pane["pane"] for pane in descriptor["fields"]["panes"]} == {"originals", "extracted_components"}


def test_smith_receipt_state_table_descriptor_covers_requested_states() -> None:
    descriptor = smith_receipt_state_table_descriptor()

    states = {state["state"] for state in descriptor["fields"]["states"]}
    assert descriptor["floor"] == "Smith"
    assert descriptor["fields"]["owner_floor"] == "Smith"
    assert states == {"received", "updated", "completed", "deleted", "declassified", "failed"}
    assert "receipt_id" in descriptor["fields"]["columns"]
    assert descriptor["fields"]["receipt_policy"]["terminal_states"] == ["completed", "deleted", "failed"]


def test_construct_simulation_artifact_rerun_descriptor_includes_rerun_metadata() -> None:
    descriptor = construct_simulation_artifact_rerun_descriptor()

    assert descriptor["floor"] == "TheConstruct"
    assert descriptor["fields"]["owner_floor"] == "TheConstruct"
    assert set(descriptor["fields"]["parameters"]) == {"scenario_id", "case_id", "timestep", "integration_window"}
    assert set(descriptor["fields"]["ephemerides"]) == {"source", "epoch", "reference_frame"}
    assert descriptor["fields"]["engine"]["mode"] == "simulation_rerun"
    assert {target["target"] for target in descriptor["fields"]["export_targets"]} == {
        "parquet",
        "json",
        "gmat_bundle",
    }
    assert descriptor["fields"]["rerun_status"]["state"] == "queued"


def test_construct_heliocentric_zoning_summary_descriptor_includes_validation_and_exports() -> None:
    descriptor = construct_heliocentric_zoning_summary_descriptor()

    assert descriptor["floor"] == "TheConstruct"
    assert descriptor["fields"]["owner_floor"] == "TheConstruct"
    assert descriptor["fields"]["zones"]["bands_source"] == "heliocentric_zoning_grid"
    assert "kmeans" in descriptor["fields"]["clusters"]["cluster_strategy"]
    assert descriptor["fields"]["gmat_batch_export"]["enabled"] is True
    assert set(descriptor["fields"]["validation_fields"]) == {
        "zone_count",
        "cluster_count",
        "target_count",
        "last_validated_at",
    }


def test_architect_publish_snapshot_descriptor_preserves_c_root_and_overwrites_d_root() -> None:
    descriptor = architect_publish_snapshot_descriptor()

    assert descriptor["floor"] == "Architect"
    assert descriptor["fields"]["owner_floor"] == "Architect"
    assert descriptor["fields"]["packaging_policy"]["d_root"] == "overwrite_only_snapshot"
    assert descriptor["fields"]["packaging_policy"]["c_root"] == "live_source_of_truth"
    assert descriptor["fields"]["packaging_policy"]["preserve_live_source"] is True
    assert descriptor["fields"]["publication_state"]["overwrite_only"] is True


def test_floor_workflow_descriptor_catalog_includes_all_floor_descriptors() -> None:
    catalog = build_floor_workflow_descriptor_catalog()

    assert set(catalog) == {
        "OracleMorpheusSplitView",
        "SmithReceiptStateTable",
        "TrinitySingleInterfaceLane",
        "SmartFloorPopulationSpace",
        "SmithGatedBuildTask",
        "ConstructSimulationArtifactRerun",
        "ConstructHeliocentricZoningSummary",
        "ConstructVisualRenderEngine",
        "ConstructVirtualSpaceSmokeTest",
        "ArchitectPublishSnapshot",
    }
