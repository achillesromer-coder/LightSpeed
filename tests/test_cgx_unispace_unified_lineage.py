"""Negative-path and exact-dedup tests for one-root source-only facet fold."""
import copy

import pytest

from tools.cgx_unispace_facet_mesh import FACETS, ROOT_ID, SCHEMA as MESH_SCHEMA
from tools.cgx_unispace_unified_lineage import (
    LineageHold, fold_unispace_lineage, ternary_shape_token,
)


def mesh():
    return {
        "schema": MESH_SCHEMA,
        "canonical_root_id": ROOT_ID,
        "state": "SOURCE_CONTRACT_MESH_OBSERVED",
        "facet_count": 5,
        "facets": [{"id": k} for k in FACETS],
    }


def record(**updates):
    result = {
        "object_id": "cgx:source:example",
        "revision": "v1",
        "kind": "external_engine_reference",
        "source_uri": "https://example.org/engine",
        "sha256": None,
        "facets": ["intelligence_space", "print_space"],
        "rights": "verified_metadata_only",
        "licence": "MIT",
        "training": "not_assessed",
        "t173_position": None,
        "supersedes": None,
        "profile_scope": None,
    }
    result.update(updates)
    return result


def test_exact_references_coalesce_without_new_store():
    output = fold_unispace_lineage(mesh(), [record(), record()], view="immersive")
    assert output["canonical_root_id"] == ROOT_ID
    assert output["source_revision_count"] == 1
    assert output["exact_duplicate_references_coalesced"] == 1
    assert output["records"][0]["facets"] == ["intelligence_space", "print_space"]
    assert not any(output[key] for key in (
        "engine_code_ingested", "training_executed", "model_weights_modified",
        "native_admitted", "mint_authorized", "deployment_authorized",
        "publication_authorized", "canonical_store_written",
    ))


def test_same_version_different_hash_is_held():
    base = record(sha256="a" * 64)
    altered = record(sha256="b" * 64)
    with pytest.raises(LineageHold, match="conflicting"):
        fold_unispace_lineage(mesh(), [base, altered])


def test_history_preserved_across_distinct_revisions():
    output = fold_unispace_lineage(mesh(), [
        record(revision="v2", supersedes="v1"),
        record(revision="v1"),
    ])
    assert output["source_revision_count"] == 2
    assert output["records"][1]["supersedes"] == "v1"


def test_missing_parent_history_held():
    with pytest.raises(LineageHold, match="unresolved"):
        fold_unispace_lineage(mesh(), [record(revision="v2", supersedes="v1")])


def test_lineage_cycle_held():
    with pytest.raises(LineageHold, match="cycle"):
        fold_unispace_lineage(mesh(), [
            record(revision="v1", supersedes="v2"),
            record(revision="v2", supersedes="v1"),
        ])


def test_geometry_index_ternary_round_trip_and_sentinel():
    for index in (1, 2, 3, 27, 81, 172, 173):
        token = ternary_shape_token(index)
        assert len(token["ternary_index"]) == 5
        assert int(token["ternary_index"], 3) == index
        assert token["verified_mesh"] is False
    for invalid in (0, 174, 243, "17", True, -1):
        with pytest.raises(LineageHold):
            ternary_shape_token(invalid)


def test_shape_reference_is_only_research_not_mesh():
    output = fold_unispace_lineage(mesh(), [record(t173_position=173)])
    assert output["records"][0]["shape"]["verified_mesh"] is False
    assert output["records"][0]["shape"]["ternary_index"]


def test_rights_cannot_be_promoted_to_training_or_distribution():
    for bad in (
        {"rights": "pending", "training": "permitted"},
        {"rights": "restricted", "training": "permitted"},
        {"rights": "cleared_distribution", "sha256": None},
        {"rights": "cleared_distribution", "licence": None},
    ):
        with pytest.raises(LineageHold):
            fold_unispace_lineage(mesh(), [record(**bad)])


def test_protected_locators_never_revealed_by_ui_audience_hint():
    private = record(
        rights="restricted", profile_scope="owner",
        source_uri="https://example.org/private-reference", sha256="a" * 64,
    )
    for audience in ("offline_guest", "profile_authenticated", "owner_review"):
        output = fold_unispace_lineage(mesh(), [private], audience=audience)
        assert output["records"][0]["source_uri"] is None
        assert output["records"][0]["sha256"] is None
        assert output["records"][0]["hydration_authorized"] is False


def test_unnamed_or_untrusted_geometry_and_facet_fail_closed():
    bad = [
        record(facets=["another_root"]),
        record(facets=["file_space", "file_space"]),
        record(t173_position=174),
        record(source_uri="javascript:alert(1)"),
        record(object_id="cgx:root:cognigrex"),
        record(licence="../"),
        record(sha256="not-a-digest"),
    ]
    for sample in bad:
        with pytest.raises(LineageHold):
            fold_unispace_lineage(mesh(), [sample])


def test_wrong_parent_and_duplicate_facets_rejected():
    modified = mesh()
    modified["canonical_root_id"] = "cgx:root:other"
    with pytest.raises(LineageHold):
        fold_unispace_lineage(modified, [record()])
    modified = mesh()
    modified["facets"].append({"id": "file_space"})
    with pytest.raises(LineageHold):
        fold_unispace_lineage(modified, [record()])


def test_output_reproducible_order_and_view_limited():
    a = record()
    b = record(object_id="cgx:source:another", facets=["file_space"])
    one = fold_unispace_lineage(mesh(), [a, b], view="graph")
    two = fold_unispace_lineage(mesh(), [b, a], view="graph")
    assert one["lineage_receipt_sha256"] == two["lineage_receipt_sha256"]
    with pytest.raises(LineageHold):
        fold_unispace_lineage(mesh(), [a], view="root-access")


def test_source_reference_bound():
    with pytest.raises(LineageHold):
        fold_unispace_lineage(mesh(), [record() for _ in range(513)])
    with pytest.raises(LineageHold):
        fold_unispace_lineage(mesh(), [dict(record(), unknown="unexpected")])


def test_empty_references_do_not_create_engines():
    output = fold_unispace_lineage(mesh(), [])
    assert output["source_revision_count"] == 0
    assert not output["training_executed"]
