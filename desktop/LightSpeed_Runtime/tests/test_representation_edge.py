from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import sys

import pytest

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.operational_store import default_operational_db_path
from lightspeed_runtime.representation_edge import (
    FEATURE_FLAG,
    RELATIONS,
    RepresentationEdgeDisabled,
    RepresentationEdgeStore,
    RepresentationValidationError,
    classify_confidence,
    content_sha256,
    default_review_paths,
    feature_enabled,
)

_SEEDED_DB_BYTES: bytes | None = None
_SEEDED_QUEUE_TEXT: str | None = None
_SEEDED_OUTBOX: dict[str, str] | None = None
_SEEDED_RESULT: dict | None = None


def make_store(tmp_path: Path, *, seed: bool = True):
    global _SEEDED_DB_BYTES, _SEEDED_QUEUE_TEXT, _SEEDED_OUTBOX, _SEEDED_RESULT
    database_path = default_operational_db_path(tmp_path)
    database_path.parent.mkdir(parents=True)
    if seed and _SEEDED_DB_BYTES is not None:
        database_path.write_bytes(_SEEDED_DB_BYTES)
    else:
        sqlite3.connect(database_path).close()
    store = RepresentationEdgeStore(database_path, enabled=True)
    queue, decisions, outbox = default_review_paths(tmp_path)
    if not (seed and _SEEDED_DB_BYTES is not None):
        store.apply_migration()
    result = None
    if seed:
        if _SEEDED_DB_BYTES is None:
            result = store.seed_proof_graphs(
                review_queue_path=queue,
                decision_path=decisions,
                local_outbox=outbox,
            )
            _SEEDED_DB_BYTES = database_path.read_bytes()
            _SEEDED_QUEUE_TEXT = queue.read_text(encoding="utf-8")
            _SEEDED_OUTBOX = {
                path.name: path.read_text(encoding="utf-8")
                for path in outbox.glob("*.json")
            }
            _SEEDED_RESULT = json.loads(json.dumps(result))
        else:
            queue.parent.mkdir(parents=True, exist_ok=True)
            queue.write_text(_SEEDED_QUEUE_TEXT or "", encoding="utf-8")
            outbox.mkdir(parents=True, exist_ok=True)
            for name, text in (_SEEDED_OUTBOX or {}).items():
                (outbox / name).write_text(text, encoding="utf-8")
            result = json.loads(json.dumps(_SEEDED_RESULT))
    return store, queue, decisions, outbox, result


def representation(
    representation_id: str,
    object_id: str,
    *,
    representation_type: str = "artifact",
    locator_type: str = "logical",
    locator: dict | None = None,
    content_hash: str | None = None,
    state: str = "candidate",
    evidence_class: str = "test",
    horizon_id: str | None = None,
) -> dict:
    return {
        "representation_id": representation_id,
        "object_id": object_id,
        "representation_type": representation_type,
        "locator_type": locator_type,
        "locator": locator or {"schema_id": "test"},
        "content_sha256": content_hash,
        "schema_id": "test",
        "source_authority": "test",
        "confidence_numeric": 0.5,
        "confidence_class": "moderate",
        "evidence_class": evidence_class,
        "horizon_id": horizon_id,
        "state": state,
        "claim_boundary": "Test boundary.",
    }


def test_feature_flag_is_disabled_by_default(monkeypatch, tmp_path):
    monkeypatch.delenv(FEATURE_FLAG, raising=False)
    path = default_operational_db_path(tmp_path)
    store = RepresentationEdgeStore(path)

    assert feature_enabled({}) is False
    assert store.status()["enabled"] is False
    assert path.exists() is False
    with pytest.raises(RepresentationEdgeDisabled):
        store.apply_migration()


def test_forward_migration_is_idempotent_and_uses_existing_database(tmp_path):
    store, queue, decisions, outbox, _ = make_store(tmp_path, seed=False)
    first = store.apply_migration()
    second = store.apply_migration()

    assert first["schema_sha256"] == second["schema_sha256"]
    assert store.status()["migration_applied"] is True
    assert store.database_path == default_operational_db_path(tmp_path)
    assert list(tmp_path.rglob("*.db")) == [store.database_path]
    assert queue.parent == decisions.parent
    assert outbox.parent == queue.parent


def test_migration_rollback_removes_only_edge_tables_and_retains_receipts(tmp_path):
    store, queue, _decisions, outbox, result = make_store(tmp_path)
    packet = outbox / f"{result['review_packet_ids'][0]}.json"
    assert packet.is_file()

    rollback = store.rollback_migration()

    with sqlite3.connect(store.database_path) as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert "canonical_objects" not in names
    assert "representation_schema_migrations" in names
    assert queue.is_file()
    assert packet.is_file()
    assert rollback["retained_receipt_history"] is True


def test_three_proof_graphs_render_with_one_parent_per_representation(tmp_path):
    store, _queue, _decisions, _outbox, result = make_store(tmp_path)
    graphs = store.list_graphs()

    assert result["graphs"] == [
        "ASPHA.0001",
        "engineering-twin:rfs-emff-sandbox",
        "de-sporte-05d89c2a",
    ]
    assert len(graphs) == 3
    assert all(graph["representations"] for graph in graphs)
    assert all(row["object_id"] for graph in graphs for row in graph["representations"])
    assert all("missing" in graph and "conflicts" in graph for graph in graphs)


def test_seed_is_idempotent_and_produces_exactly_three_review_packets(tmp_path):
    store, queue, decisions, outbox, first = make_store(tmp_path)
    first_hashes = {
        row["review_id"]: row["graph_sha256"]
        for row in store.list_reviews()
    }
    second = store.seed_proof_graphs(
        review_queue_path=queue,
        decision_path=decisions,
        local_outbox=outbox,
    )

    assert second["review_packet_ids"] == first["review_packet_ids"]
    assert len(store.list_reviews()) == 3
    assert {
        row["review_id"]: row["graph_sha256"]
        for row in store.list_reviews()
    } == first_hashes
    queue_rows = [json.loads(line) for line in queue.read_text(encoding="utf-8").splitlines()]
    assert len(queue_rows) == 3
    assert len(list(outbox.glob("LSGO-REVIEW-*.json"))) == 3


def test_idempotent_startup_preserves_review_and_staged_target_state(tmp_path):
    store, queue, decisions, outbox, result = make_store(tmp_path)
    review_id = result["review_packet_ids"][0]
    decision = store.record_decision(
        review_id=review_id,
        decision="approve",
        actor="Nathaniel",
        scope="identity",
        note="Fixture approval.",
        edge_ids=[],
        decision_path=decisions,
        local_outbox=outbox,
    )
    promotion = next(
        row for row in store.list_promotions() if row["object_id"] == "ASPHA.0001"
    )
    store.stage_promotion_target(
        promotion_id=promotion["promotion_id"],
        expected_parent="drive-folder:canonical-object-graphs",
        decision_id=decision["decision_id"],
    )

    store.seed_proof_graphs(
        review_queue_path=queue,
        decision_path=decisions,
        local_outbox=outbox,
    )

    review = next(row for row in store.list_reviews() if row["review_id"] == review_id)
    promotion = next(
        row for row in store.list_promotions() if row["object_id"] == "ASPHA.0001"
    )
    assert review["review_stage"] == "edges"
    assert review["state"] == "approved_pending_drive_readback"
    assert promotion["state"] == "approved_target_pending_drive_write"
    assert promotion["expected_parent"] == "drive-folder:canonical-object-graphs"
    assert promotion["decision_id"] == decision["decision_id"]


def test_apophis_identity_and_workbook_missing_key_are_retained(tmp_path):
    store, *_ = make_store(tmp_path)
    graph = store.graph("ASPHA.0001")

    identifiers = {(row["namespace"], row["identifier_value"]) for row in graph["identifiers"]}
    assert identifiers == {
        ("human_name", "Apophis"),
        ("jpl", "99942"),
        ("provisional_designation", "2004 MN4"),
        ("romer", "ASPHA.0001"),
    }
    workbook_row = next(
        row for row in graph["representations"] if row["representation_id"] == "rep:apophis:raw-workbook-row"
    )
    assert workbook_row["state"] == "missing"
    assert workbook_row["locator"]["sheet_name"] == "4_Asteroid_Master"
    assert workbook_row["locator"]["stable_key"] is None
    assert workbook_row["locator"]["missing_state"] == "awaiting_stable_workbook_key"


def test_identifier_collision_creates_review_and_never_merges(tmp_path):
    store, *_ = make_store(tmp_path)
    store._upsert_object(
        {
            "object_id": "asteroid:collision",
            "object_type": "asteroid",
            "canonical_name": "Collision candidate",
            "authority": "test",
            "identity_confidence_numeric": 0.1,
            "identity_confidence_class": "low",
            "state": "candidate",
        }
    )

    result = store.add_identifier(
        {
            "identifier_id": "identifier:collision:jpl",
            "object_id": "asteroid:collision",
            "namespace": "jpl",
            "identifier_value": "99942",
            "identifier_type": "empirical_authority",
            "authority": "test",
        }
    )

    assert result["collision"] is True
    with sqlite3.connect(store.database_path) as connection:
        owner = connection.execute(
            "SELECT object_id FROM object_identifiers WHERE namespace='jpl' AND identifier_value='99942'"
        ).fetchone()[0]
    assert owner == "ASPHA.0001"
    assert any(review["event_type"] == "identifier_collision" for review in store.list_reviews())


def test_multiple_identifiers_and_mission_unit_human_name_can_coexist(tmp_path):
    store, *_ = make_store(tmp_path)
    store._upsert_object(
        {
            "object_id": "deployed-unit:m1a",
            "object_type": "deployed_unit",
            "canonical_name": "M1A",
            "display_name": "Gregory",
            "authority": "Nathaniel",
            "identity_confidence_numeric": 1.0,
            "identity_confidence_class": "confirmed",
            "state": "candidate",
        }
    )
    for identifier_id, namespace, value, kind in (
        ("id:m1a:unit", "mission_unit", "M1A", "mission_unit"),
        ("id:m1a:name", "display_name", "Gregory", "display_name"),
    ):
        assert store.add_identifier(
            {
                "identifier_id": identifier_id,
                "object_id": "deployed-unit:m1a",
                "namespace": namespace,
                "identifier_value": value,
                "identifier_type": kind,
                "authority": "Nathaniel",
            }
        )["collision"] is False
    graph = store.graph("deployed-unit:m1a")
    assert {row["identifier_value"] for row in graph["identifiers"]} == {"M1A", "Gregory"}


def test_physical_system_and_digital_twin_remain_separate(tmp_path):
    store, *_ = make_store(tmp_path)
    for object_id, object_type in (
        ("physical-system:test", "physical_system"),
        ("engineering-twin:test", "engineering_twin"),
    ):
        store._upsert_object(
            {
                "object_id": object_id,
                "object_type": object_type,
                "canonical_name": object_id,
                "authority": "test",
                "identity_confidence_numeric": 0.8,
                "identity_confidence_class": "high",
                "state": "candidate",
            }
        )
        store._upsert_evidence_bundle(
            {
                "evidence_bundle_id": f"evidence:{object_id}",
                "title": "Identity link evidence",
                "evidence_items": [],
                "claim_boundary": "Identity relation only.",
            }
        )
        store._upsert_representation(
            representation(f"rep:{object_id}", object_id, content_hash=content_sha256(object_id))
        )
    store._upsert_edge(
        {
            "edge_id": "edge:test:digital-twin",
            "from_representation_id": "rep:engineering-twin:test",
            "to_representation_id": "rep:physical-system:test",
            "relation": "digital_twin_of",
            "evidence_bundle_id": "evidence:engineering-twin:test",
            "confidence_numeric": 0.8,
            "confidence_class": "high",
            "claim_boundary": "Separate identities retained.",
            "created_by_floor": "Architect",
            "review_state": "pending",
        }
    )
    assert store.graph("engineering-twin:test")["object"]["object_id"] != "physical-system:test"


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, "unknown"), (0.2, "low"), (0.5, "moderate"), (0.9, "high")],
)
def test_confidence_mapping_is_configurable(value, expected):
    assert classify_confidence(value) == expected
    if value is not None:
        assert classify_confidence(value, thresholds={"low_upper": 0.1, "moderate_upper": 0.2}) == "high"


def test_workbook_row_rejects_row_number_only(tmp_path):
    store, *_ = make_store(tmp_path)
    value = representation(
        "rep:test:workbook-row",
        "ASPHA.0001",
        representation_type="workbook_row",
        locator_type="drive_workbook_row",
        locator={
            "drive_file_id": "drive-id",
            "sheet_name": "Sheet1",
            "current_row_number": 2,
        },
        state="missing",
    )
    with pytest.raises(RepresentationValidationError, match="stable key|row number"):
        store._upsert_representation(value)


def test_invalid_sha_and_unbounded_illustrative_visual_are_rejected(tmp_path):
    store, *_ = make_store(tmp_path)
    with pytest.raises(RepresentationValidationError, match="SHA-256"):
        store._upsert_representation(
            representation("rep:test:bad-hash", "ASPHA.0001", content_hash="abc")
        )
    with pytest.raises(RepresentationValidationError, match="illustrative visual"):
        store._upsert_representation(
            representation(
                "rep:test:visual",
                "ASPHA.0001",
                representation_type="visual",
                locator={"evidence_class": "illustrative_only"},
                content_hash=None,
            )
        )


def test_recommendation_requires_horizon(tmp_path):
    store, *_ = make_store(tmp_path)
    with pytest.raises(RepresentationValidationError, match="horizon"):
        store._upsert_representation(
            representation(
                "rep:test:recommendation",
                "ASPHA.0001",
                representation_type="recommendation",
                locator={"next_highest_value_question": "What next?"},
                content_hash=content_sha256("recommendation"),
            )
        )


def test_relation_and_evidence_bundle_rules_reject_invalid_edges(tmp_path):
    store, *_ = make_store(tmp_path)
    with pytest.raises(RepresentationValidationError, match="unsupported relation"):
        store._upsert_edge(
            {
                "edge_id": "edge:invalid",
                "from_representation_id": "rep:apophis:jpl-horizons",
                "to_representation_id": "rep:apophis:recommendation",
                "relation": "invented",
                "confidence_numeric": 0.5,
                "confidence_class": "moderate",
            }
        )
    with pytest.raises(RepresentationValidationError, match="evidence bundle"):
        store._upsert_edge(
            {
                "edge_id": "edge:no-evidence",
                "from_representation_id": "rep:apophis:jpl-horizons",
                "to_representation_id": "rep:apophis:recommendation",
                "relation": "derived_from",
                "confidence_numeric": 0.5,
                "confidence_class": "moderate",
            }
        )
    assert "contradicts" in RELATIONS


def test_database_foreign_keys_reject_dangling_edges(tmp_path):
    store, *_ = make_store(tmp_path)
    with pytest.raises(sqlite3.IntegrityError):
        store._upsert_edge(
            {
                "edge_id": "edge:dangling",
                "from_representation_id": "rep:not-there",
                "to_representation_id": "rep:also-not-there",
                "relation": "depends_on",
                "confidence_numeric": 0.1,
                "confidence_class": "low",
                "claim_boundary": "test",
                "review_state": "pending",
            }
        )


def test_duplicate_and_shared_lineage_evidence_do_not_increase_confidence():
    result = RepresentationEdgeStore.evidence_confidence_effect(
        [
            {
                "underlying_source_fingerprint": "primary-a",
                "independence_status": "independent",
                "authors": ["A"],
                "publication_or_observation_date": "2020",
            },
            {
                "underlying_source_fingerprint": "primary-a",
                "independence_status": "shared_lineage",
                "authors": ["B"],
                "publication_or_observation_date": "2021",
            },
            {
                "underlying_source_fingerprint": "copy",
                "independence_status": "independent",
                "duplicate": True,
            },
        ]
    )
    assert result["independence_group_count"] == 1
    assert result["duplicate_reference_count"] == 1
    assert result["confidence_effect"] == 0.0


def test_independent_corroboration_may_increase_confidence_and_outlier_remains_flagged():
    result = RepresentationEdgeStore.evidence_confidence_effect(
        [
            {
                "underlying_source_fingerprint": "method-a-2020",
                "independence_status": "independent",
                "authors": ["A"],
                "publication_or_observation_date": "2020",
            },
            {
                "underlying_source_fingerprint": "method-a-2024",
                "independence_status": "independent",
                "authors": ["A"],
                "publication_or_observation_date": "2024",
            },
            {
                "underlying_source_fingerprint": "method-b",
                "independence_status": "independent",
                "authors": ["B"],
                "outlier": True,
            },
        ],
        independent_increment=0.1,
    )
    assert result["independence_group_count"] == 3
    assert result["confidence_effect"] == pytest.approx(0.2)
    assert result["outlier_count"] == 1


def test_held_rfs_evidence_and_mathematics_cannot_promote_capability(tmp_path):
    store, *_ = make_store(tmp_path)
    with pytest.raises(RepresentationValidationError, match="held evidence"):
        store._upsert_representation(
            representation(
                "rep:rfs-emff:bad-capability",
                "engineering-twin:rfs-emff-sandbox",
                evidence_class="held_empirical_capability",
                state="active",
                content_hash=content_sha256("bad"),
            )
        )
    with pytest.raises(RepresentationValidationError, match="mathematics"):
        store._upsert_representation(
            representation(
                "rep:rfs-emff:bad-equation",
                "engineering-twin:rfs-emff-sandbox",
                representation_type="equation",
                evidence_class="empirical_capability",
                content_hash=content_sha256("equation"),
            )
        )


def test_controlled_unpack_blocks_path_traversal_secrets_and_excess(tmp_path):
    valid = RepresentationEdgeStore.validate_controlled_unpack_manifest(
        [{"path": "docs/readme.txt", "size_bytes": 20}]
    )
    assert valid["source_mutated"] is False
    with pytest.raises(RepresentationValidationError, match="path traversal"):
        RepresentationEdgeStore.validate_controlled_unpack_manifest(
            [{"path": "../escape.txt", "size_bytes": 1}]
        )
    with pytest.raises(RepresentationValidationError, match="secret scan"):
        RepresentationEdgeStore.validate_controlled_unpack_manifest(
            [{"path": "credentials.json", "size_bytes": 1}]
        )
    with pytest.raises(RepresentationValidationError, match="file-count"):
        RepresentationEdgeStore.validate_controlled_unpack_manifest(
            [{"path": "a"}, {"path": "b"}], max_files=1
        )


def test_horizon_changes_preserve_prior_rationale_and_are_resource_gated(tmp_path):
    store, *_ = make_store(tmp_path)
    enrichment = store.propose_horizon(
        parent_horizon_id="horizon:one",
        accepted_inputs={"note": "non-conflicting enrichment"},
        material_change=False,
        changed_engines=["route"],
    )
    changed = store.propose_horizon(
        parent_horizon_id="horizon:one",
        accepted_inputs={"fleet": 8},
        material_change=True,
        changed_engines=["route", "capacity"],
        resource_state="critical",
    )
    assert enrichment["rerun_required"] is False
    assert changed["state"] == "resource_held"
    assert changed["rerun_authorized"] is False
    assert changed["prior_rationale_label"] == "rational under the earlier accepted horizon"


def test_identity_review_precedes_edges_and_owner_actions_are_enforced(tmp_path):
    store, _queue, decisions, outbox, result = make_store(tmp_path)
    review_id = result["review_packet_ids"][0]
    edge_id = store.graph("ASPHA.0001")["edges"][0]["edge_id"]

    with pytest.raises(RepresentationValidationError, match="identity review"):
        store.record_decision(
            review_id=review_id,
            decision="hold",
            actor="Achilles",
            scope="edges",
            note="",
            edge_ids=[edge_id],
            decision_path=decisions,
            local_outbox=outbox,
        )
    with pytest.raises(PermissionError, match="Nathaniel"):
        store.record_decision(
            review_id=review_id,
            decision="approve",
            actor="Achilles",
            scope="identity",
            note="",
            edge_ids=[],
            decision_path=decisions,
            local_outbox=outbox,
        )
    identity = store.record_decision(
        review_id=review_id,
        decision="provisional_approve",
        actor="Achilles",
        scope="identity",
        note="Identity is provisional.",
        edge_ids=[],
        decision_path=decisions,
        local_outbox=outbox,
    )
    edge = store.record_decision(
        review_id=review_id,
        decision="hold",
        actor="Nathaniel",
        scope="edges",
        note="Stable workbook key remains absent.",
        edge_ids=[edge_id],
        decision_path=decisions,
        local_outbox=outbox,
    )
    assert identity["applies_external_write"] is False
    assert edge["edge_ids"] == [edge_id]


@pytest.mark.parametrize(
    ("decision", "actor"),
    [
        ("approve", "Nathaniel"),
        ("provisional_approve", "Achilles"),
        ("hold", "Nathaniel"),
        ("reject", "Nathaniel"),
        ("request_evidence", "Nathaniel"),
        ("supersede", "Nathaniel"),
    ],
)
def test_all_review_actions_produce_bounded_nonwriting_receipts(
    tmp_path, decision, actor
):
    store, _queue, decisions, outbox, result = make_store(tmp_path)
    review_id = result["review_packet_ids"][0]

    receipt = store.record_decision(
        review_id=review_id,
        decision=decision,
        actor=actor,
        scope="identity",
        note=f"Bounded {decision} fixture.",
        edge_ids=[],
        decision_path=decisions,
        local_outbox=outbox,
    )

    assert receipt["decision"] == decision
    assert receipt["edge_ids"] == []
    assert receipt["applies_external_write"] is False
    assert (outbox / f"{review_id}_{receipt['decision_id']}.json").is_file()


def test_drive_promotions_stay_noncanonical_without_exact_readback(tmp_path):
    store, *_ = make_store(tmp_path)
    promotions = store.list_promotions()
    assert len(promotions) == 3
    assert all(item["drive_write_executed"] is False for item in promotions)
    apophis = next(item for item in promotions if item["object_id"] == "ASPHA.0001")
    with pytest.raises(RepresentationValidationError, match="exact Drive readback"):
        store.confirm_drive_readback(apophis["promotion_id"], {})


def test_drive_readback_requires_owner_decision_exact_parent_metadata_and_hashes(tmp_path):
    store, _queue, decisions, outbox, result = make_store(tmp_path)
    review_id = result["review_packet_ids"][0]
    decision = store.record_decision(
        review_id=review_id,
        decision="approve",
        actor="Nathaniel",
        scope="identity",
        note="Fixture owner approval.",
        edge_ids=[],
        decision_path=decisions,
        local_outbox=outbox,
    )
    promotion = next(
        row for row in store.list_promotions() if row["object_id"] == "ASPHA.0001"
    )
    staged = store.stage_promotion_target(
        promotion_id=promotion["promotion_id"],
        expected_parent="drive-folder:canonical-object-graphs",
        decision_id=decision["decision_id"],
    )
    readback = {
        "drive_object_id": "drive-file:apophis-graph",
        "drive_revision_id": "drive-revision:1",
        "expected_parent": staged["expected_parent"],
        "metadata": promotion["expected_metadata"],
        "object_id": "ASPHA.0001",
        "decision_id": decision["decision_id"],
        "graph_sha256": promotion["graph_sha256"],
        "no_source_mutation": True,
        "no_secret_or_private_data_violation": True,
    }
    with pytest.raises(RepresentationValidationError, match="normalized workbook"):
        store.confirm_drive_readback(promotion["promotion_id"], readback)
    readback["normalized_content_sha256"] = content_sha256("normalized fixture workbook")

    receipt = store.confirm_drive_readback(promotion["promotion_id"], readback)

    assert receipt["canonical"] is True
    assert store.graph("ASPHA.0001")["object"]["state"] == "active"


def test_de_sporte_is_private_metadata_only_and_cannot_promote(tmp_path):
    store, *_ = make_store(tmp_path)
    graph = store.graph("de-sporte-05d89c2a")
    registry = next(
        row for row in graph["representations"] if row["representation_id"] == "rep:de-sporte:registry"
    )
    promotion = next(
        item for item in store.list_promotions() if item["object_id"] == "de-sporte-05d89c2a"
    )

    assert registry["locator"]["path_exposed"] is False
    assert graph["object"]["metadata"]["content_assimilated"] is False
    assert promotion["state"] == "held_personal_private_no_business_promotion"
    with pytest.raises(RepresentationValidationError, match="personal/private"):
        store.confirm_drive_readback(
            promotion["promotion_id"],
            {
                "drive_object_id": "drive",
                "drive_revision_id": "revision",
                "expected_parent": "folder",
                "metadata": {},
                "object_id": "de-sporte-05d89c2a",
                "decision_id": "decision",
            },
        )


def test_review_and_promotion_packets_contain_no_secrets_or_private_paths(tmp_path):
    store, queue, _decisions, outbox, result = make_store(tmp_path)
    payload = queue.read_text(encoding="utf-8")
    for path in outbox.glob("*.json"):
        payload += path.read_text(encoding="utf-8")
    lowered = payload.casefold()
    assert "api_key" not in lowered
    assert "password" not in lowered
    assert "d:\\de sporte" not in lowered
    assert result["drive_write_executed"] is False
