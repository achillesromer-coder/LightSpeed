from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.dataset_catalog import build_dataset_catalog_shell
from lightspeed_runtime.definition_library import build_oracle_definition_library, proof_definition_for_theme
from lightspeed_runtime.empirical import build_empirical_catalog
from lightspeed_runtime.entity_registry import build_entity_registry
from lightspeed_runtime.ingestion import build_ingestion_preparation
from lightspeed_runtime.contracts import ReservoirManifest
from lightspeed_runtime.knowns import (
    build_knowns_declassification_audit,
    build_knowns_proofing_queue,
    build_knowns_queue_objects,
    build_knowns_registry,
    promote_knowns_entries,
)
from lightspeed_runtime.scientific_query import build_scientific_query_layer
from lightspeed_runtime.labs.presets import build_simulation_presets
from lightspeed_runtime.labs.zoning import run_heliocentric_zoning
from lightspeed_runtime.labs.manager import LabManager


def _manifest(root: Path, *, source_id: str, source_type: str = "dataset_bundle", floor_owner: str = "Oracle") -> ReservoirManifest:
    return ReservoirManifest(
        source_id=source_id,
        root_path=str(root),
        source_type=source_type,
        classification="reference",
        floor_owner=floor_owner,
        workspace_tags=["romer"],
        project_tags=["Romer"],
        trusted_documents=["asteroids", "alignment"],
        extractors=["json"],
    )


def _write_empirical_source(root: Path) -> Path:
    source_dir = root / "Mounted" / "Empirical"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "asteroids.json").write_text(
        json.dumps([{"id": 1, "name": "Psyche", "a": 2.9, "e": 0.14, "i": 3.1}]),
        encoding="utf-8",
    )
    return source_dir


def test_knowns_registry_prefers_proofed_definitions(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    source_dir = root / "Mounted" / "Doctrine"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "alignment_note.md").write_text(
        "Achilles governs the operator model. Oracle proofs definitions before reuse.",
        encoding="utf-8",
    )

    registry = build_knowns_registry(root, [_manifest(source_dir, source_id="doctrine_notes", source_type="document_bundle")])
    queue = build_knowns_proofing_queue(root, registry)

    first_theme = registry["themes"][0]
    assert first_theme["proofed_definition"]
    assert first_theme["operator_notes"]
    assert first_theme["summary"] == first_theme["proofed_definition"]
    assert first_theme["source_label"]
    assert registry["report_path"].endswith("knowns_registry.json")

    first_entry = queue["entries"][0]
    assert first_entry["source_label"]
    assert first_entry["proofed_definition"]
    assert first_entry["definition_basis"] in {"curated_oracle_dictionary", "theme_summary"}
    assert first_entry["definition_confidence"] in {"high", "medium"}
    assert queue["report_path"].endswith("knowns_proofing_queue.json")

    library = build_oracle_definition_library(root, knowns_registry=registry)
    assert library["theme_definition_count"] >= 1
    assert library["theme_definitions"][0]["operator_notes"]


def test_knowns_queue_objects_and_promotion_records_preserve_definition_fidelity(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    source_dir = root / "Mounted" / "Doctrine"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "alignment_note.md").write_text(
        "Achilles governs the operator model. Oracle proofs definitions before reuse.",
        encoding="utf-8",
    )

    registry = build_knowns_registry(root, [_manifest(source_dir, source_id="doctrine_notes", source_type="document_bundle")])
    queue = build_knowns_proofing_queue(root, registry)
    queue_objects = build_knowns_queue_objects(root, queue_payload=queue, registry_payload=registry)
    assert queue_objects["objects"]
    first_object = queue_objects["objects"][0]
    assert first_object["owner_floor"] == "Oracle"
    assert first_object["review_floor"] == "Morpheus"
    assert first_object["next_definition"]

    result = promote_knowns_entries(root, registry, queue, destinations=["knowns"], max_entries=1)
    assert result["promoted_count"] == 1
    promoted_path = Path(result["promoted"][0]["target_path"])
    promoted_record = json.loads(promoted_path.read_text(encoding="utf-8"))
    assert promoted_record["definition_basis"] in {"curated_oracle_dictionary", "theme_summary"}
    assert promoted_record["definition_confidence"] in {"high", "medium"}
    assert promoted_record["owner_floor"] == "Oracle"
    assert result["report_path"].endswith("knowns_proofing_queue.json")


def test_empirical_catalog_and_dataset_catalog_surface_owner_and_usage_role(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    source_dir = _write_empirical_source(root)
    manifests = [_manifest(source_dir, source_id="library_empirical_data", source_type="empirical_dataset_bundle", floor_owner="TheConstruct")]

    empirical = build_empirical_catalog(root, manifests)
    dataset_record = empirical["dataset_table"][0]
    assert dataset_record["source_label"] == "library_empirical_data"
    assert dataset_record["owner_floor"] == "TheConstruct"
    assert dataset_record["usage_role"] in {"reference", "simulation_input"}
    assert dataset_record["source_type_definition"]
    assert empirical["headline_knowns"][0]["source_label"] == "library_empirical_data"
    assert empirical["headline_knowns"][0]["operator_notes"]

    catalog = build_dataset_catalog_shell(root, empirical_catalog=empirical, scientific_query={"queryables": []}, entity_registry={})
    dataset = catalog["datasets"][0]
    assert catalog["report_path"].endswith("dataset_catalog_shell.json")
    assert dataset["owner_floor"] == "TheConstruct"
    assert dataset["usage_role"] in {"reference", "simulation_input"}
    assert dataset["source_label"] == "library_empirical_data"
    assert dataset["source_type_definition"]
    assert dataset["source_provenance_summary"]
    assert "owned by TheConstruct" in dataset["description"]
    assert empirical["clusterable_input_summary"]["count"] >= 1
    assert empirical["headline_knowns_summary"]["count"] >= 1


def test_scientific_query_layer_prefers_curated_review_and_readable_source_fields(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    source_dir = _write_empirical_source(root)
    manifests = [_manifest(source_dir, source_id="library_empirical_data", source_type="empirical_dataset_bundle", floor_owner="Oracle")]

    empirical = build_empirical_catalog(root, manifests)
    curated_tables = {
        "tables": [
            {
                "table_name": "oracle_knowns_review",
                "manifest_path": str(root / "curated" / "oracle_knowns_review.json"),
                "row_count": 2,
                "actual_format": "json",
                "json_path": str(root / "curated" / "oracle_knowns_review.json"),
            }
        ]
    }
    (root / "curated").mkdir(parents=True, exist_ok=True)
    (root / "curated" / "oracle_knowns_review.json").write_text(json.dumps({"columns": ["name", "confidence_score"]}), encoding="utf-8")

    query_layer = build_scientific_query_layer(root, empirical_catalog=empirical, curated_tables=curated_tables)
    assert query_layer["query_templates"][0]["template_id"] == "tap_like_curated_review"
    assert query_layer["queryables"][0]["owner_floor"] == "Oracle"
    assert query_layer["queryables"][0]["source_label"] == "library_empirical_data"
    assert query_layer["summary"].startswith("Curated-first scientific query layer")
    assert query_layer["report_path"].endswith("scientific_query_layer.json")


def test_ingestion_preparation_propagates_source_type_notes(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    source_dir = _write_empirical_source(root)
    manifests = [
        _manifest(source_dir, source_id="library_empirical_data", source_type="empirical_dataset_bundle", floor_owner="TheConstruct"),
        _manifest(root / "Mounted" / "Doctrine", source_id="achilles_alignment_notes", source_type="document_bundle", floor_owner="Oracle"),
    ]
    prep = build_ingestion_preparation(root, manifests)

    assert prep["source_count"] == 2
    first_source = prep["sources"][0]
    assert first_source["source_label"]
    assert first_source["source_type_definition"]
    assert first_source["fallback_description"]
    assert first_source["operator_notes"]
    assert first_source["usage_role"] == "source_proofing"
    assert prep["canonical_targets"]["knowns"]["owner_floor"] == "Oracle"


def test_operator_simulation_context_uses_empirical_summary(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    source_dir = _write_empirical_source(root)
    manifests = [_manifest(source_dir, source_id="library_empirical_data", source_type="empirical_dataset_bundle", floor_owner="Oracle")]
    empirical = build_empirical_catalog(root, manifests)
    doctrine_dir = root / "Mounted" / "Doctrine"
    doctrine_dir.mkdir(parents=True, exist_ok=True)
    (doctrine_dir / "alignment_note.md").write_text(
        "Achilles governs the operator model. Oracle proofs definitions before reuse.",
        encoding="utf-8",
    )
    registry = build_knowns_registry(root, [_manifest(doctrine_dir, source_id="doctrine_notes", source_type="document_bundle")])

    manager = LabManager()
    context = manager.build_operator_simulation_context(
        workspace_id="romer",
        project_id="Romer",
        query="zoning",
        knowns_payload=registry,
        empirical_payload=empirical,
        dataset_catalog=empirical["dataset_table"],
        limit=5,
    )
    assert context["scenario_id"] == "heliocentric_zoning_grid"
    assert context["empirical_headline_summary"]["count"] >= 1
    assert context["empirical_headline_count"] >= 1
    assert context["priority_queue"][0]["action"] == "Review proofed doctrine"


def test_simulation_presets_and_entity_registry_prefer_proofed_sources_and_compact_provenance(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    source_dir = _write_empirical_source(root)
    manifests = [_manifest(source_dir, source_id="library_empirical_data", source_type="empirical_dataset_bundle", floor_owner="Oracle")]
    empirical = build_empirical_catalog(root, manifests)
    registry = build_knowns_registry(root, [_manifest(root / "Mounted" / "Doctrine", source_id="doctrine_notes", source_type="document_bundle")])
    simulation_presets = build_simulation_presets(root, empirical)
    entity_registry, manifest_index = build_entity_registry(root, manifests, empirical_catalog=empirical, knowns_registry=registry)
    audit = build_knowns_declassification_audit(root, registry_payload=registry)

    first_preset = next(preset for preset in simulation_presets["presets"] if preset["recommended_inputs"])
    first_ref = first_preset["recommended_inputs"][0]
    assert simulation_presets["report_path"].endswith("simulation_presets.json")
    assert simulation_presets["summary"].startswith("Romer-first simulation presets derived from empirical and proofed sources")
    assert simulation_presets["source_provenance_links"]
    assert simulation_presets["source_provenance_summary"]
    assert first_preset["owner_floor"] == "TheConstruct"
    assert simulation_presets["proofed_source_count"] >= 1
    assert first_ref["source_label"]
    assert first_ref["owner_floor"] == "TheConstruct" or first_ref["owner_floor"] == "Oracle"
    assert first_ref["provenance_links"]
    assert "absolute_path" not in first_ref
    assert first_ref["provenance_links"][0]["path"]
    dataset_entity = next(item for item in entity_registry["entities"] if item["entity_kind"] == "dataset")
    assert dataset_entity["metadata"]["source_provenance_summary"]
    assert entity_registry["report_path"].endswith("entity_registry.json")
    assert manifest_index["report_path"].endswith("dataset_manifest_index.json")
    assert audit["report_path"].endswith("knowns_declassification_audit.json")
    assert "corroboration-only" in audit["summary"]
    if audit["candidates"]:
        assert audit["candidates"][0]["provenance_links"]
        assert audit["candidates"][0]["evidence_summary"]


def test_definition_confidence_labels_normalize(tmp_path: Path) -> None:
    definition = proof_definition_for_theme(
        {
            "theme_id": "custom_theme",
            "title": "Custom Theme",
            "summary": "Custom summary",
            "definition_confidence": "Strong",
        }
    )
    assert definition["confidence"] == "high"


def test_zoning_outputs_surface_publishability_and_provenance_metadata(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed"
    source_dir = _write_empirical_source(root)
    result = run_heliocentric_zoning(source_dir / "asteroids.json", root / "zoning_out", source_label="library_empirical_data")

    shortlist = result["targets_shortlist"]
    gmat_batch = result["gmat_target_batch"]
    assert result["report_path"].endswith("run_summary.json")
    assert shortlist
    assert shortlist[0]["publishability_state"] == "handoff_candidate"
    assert shortlist[0]["owner_floor"] == "TheConstruct"
    assert shortlist[0]["source_provenance_summary"]
    assert "source_owner" not in gmat_batch
    assert gmat_batch["owner_floor"] == "TheConstruct"
    assert gmat_batch["source_provenance_summary"]
    assert gmat_batch["targets"][0]["source_label"]
