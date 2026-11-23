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


def test_real_engine_reference_registry_unifies_safely():
    import json
    from pathlib import Path
    from tools.cgx_unispace_facet_mesh import build_unispace_facet_mesh
    from tools.cgx_unispace_unified_lineage import fold_engine_reference_catalogue
    root = Path(__file__).resolve().parents[1]
    actual_mesh = build_unispace_facet_mesh(root)
    catalogue = json.loads(
        (root / "cgx/review/unispace_engine_reference_candidates_v0_1.json")
        .read_text(encoding="utf-8")
    )
    result = fold_engine_reference_catalogue(actual_mesh, catalogue)
    assert result["source_revision_count"] == 6
    assert result["canonical_root_id"] == ROOT_ID
    assert result["source_revision_pins_qualified"] is False
    assert all(row["sha256"] is None and
               row["training"] == "not_assessed" and
               row["hydration_authorized"] is False
               for row in result["records"])
    assert result["model_weights_modified"] is False
    assert result["publication_authorized"] is False


def test_engine_references_reject_false_integration_training_and_duplicates():
    from tools.cgx_unispace_unified_lineage import fold_engine_reference_catalogue
    candidate = {
        "schema": "CGX-UNISPACE-EXTERNAL-ENGINE-REFERENCE-CANDIDATES/0.1",
        "canonical_root": ROOT_ID,
        "policy": {
            "source_code_embedded": False,
            "model_weights_trained": False,
            "source_commit_pin_required_before_reuse": True,
        },
        "sources": [{
            "name": "Example Engine",
            "source": "https://example.org/license",
            "declared_project_license": "MIT",
            "reference_only": True,
            "rights_qualified_for_training": False,
            "installation_verified": False,
            "integration_verified": False,
            "source_hash": None,
            "revision": "VERSION_PIN_PENDING",
            "candidate_facets": ["intelligence_space"],
        }]
    }
    first = fold_engine_reference_catalogue(mesh(), candidate)
    assert first["source_revision_count"] == 1
    for field, value in (
        ("rights_qualified_for_training", True),
        ("installation_verified", True),
        ("integration_verified", True),
        ("reference_only", False),
        ("source_hash", "a" * 64),
    ):
        altered = copy.deepcopy(candidate)
        altered["sources"][0][field] = value
        with pytest.raises(LineageHold):
            fold_engine_reference_catalogue(mesh(), altered)
    altered = copy.deepcopy(candidate)
    altered["sources"].append(copy.deepcopy(altered["sources"][0]))
    duplicate = fold_engine_reference_catalogue(mesh(), altered)
    assert duplicate["source_revision_count"] == 1
    assert duplicate["exact_duplicate_references_coalesced"] == 1


def test_ternary_bytes_all_values_reversible():
    from tools.cgx_unispace_unified_lineage import bytes_to_ternary, ternary_to_bytes
    data = bytes(range(256))
    encoded = bytes_to_ternary(data)
    assert len(encoded) == len(data) * 6
    assert set(encoded).issubset({"0", "1", "2"})
    assert ternary_to_bytes(encoded) == data
    assert bytes_to_ternary(b"") == ""
    assert ternary_to_bytes("") == b""


def test_ternary_bytes_strict_negative_inputs():
    from tools.cgx_unispace_unified_lineage import (
        MAX_CAPSULE_BYTES, bytes_to_ternary, ternary_to_bytes,
    )
    with pytest.raises(LineageHold):
        bytes_to_ternary(bytearray(b"x"))
    with pytest.raises(LineageHold):
        bytes_to_ternary(b"x" * (MAX_CAPSULE_BYTES + 1))
    for value in ("00000", "1000000", "aaa000", "222222", "1001100"):
        with pytest.raises(LineageHold):
            ternary_to_bytes(value)


def test_capsule_reference_is_only_source_lineage():
    from tools.cgx_unispace_unified_lineage import (
        compile_ternary_shape_capsule, validate_ternary_shape_capsule
    )
    import hashlib
    payload = b"canonical-owned-source-content"
    row = record(
        kind="internal_component", rights="cleared_distribution",
        sha256=hashlib.sha256(payload).hexdigest(), t173_position=173,
    )
    capsule = compile_ternary_shape_capsule(mesh(), row, position=173)
    assert capsule["canonical_root_id"] == ROOT_ID
    assert capsule["transport"] == "REFERENCE_HASH_ONLY"
    assert capsule["payload_ternary"] is None
    assert capsule["shape"]["ternary_index"] == "20102"
    verified = validate_ternary_shape_capsule(capsule)
    assert verified["integrity"] == "HASH_VERIFIED"
    assert verified["owner_signer_verified"] is False
    assert verified["shape_is_research_only"] is True


def test_capsule_embeds_only_hash_matched_approved_bytes():
    from tools.cgx_unispace_unified_lineage import (
        compile_ternary_shape_capsule, validate_ternary_shape_capsule, ternary_to_bytes
    )
    import hashlib
    payload = bytes([0, 1, 2, 254, 255])
    row = record(
        rights="cleared_distribution",
        sha256=hashlib.sha256(payload).hexdigest(),
    )
    capsule = compile_ternary_shape_capsule(
        mesh(), row, position=27, payload=payload,
        source_owned_and_embed_approved=True,
    )
    assert capsule["payload_binary_bytes"] == len(payload)
    assert ternary_to_bytes(capsule["payload_ternary"]) == payload
    assert validate_ternary_shape_capsule(capsule)[
        "source_digest_matches_embedded_payload"] is True


def test_capsule_prevents_unapproved_embedding():
    from tools.cgx_unispace_unified_lineage import compile_ternary_shape_capsule
    import hashlib
    payload = b"provenance-test"
    digest = hashlib.sha256(payload).hexdigest()
    row = record(rights="cleared_distribution", sha256=digest)
    with pytest.raises(LineageHold):
        compile_ternary_shape_capsule(mesh(), row, position=1,
                                      payload=payload)
    with pytest.raises(LineageHold):
        compile_ternary_shape_capsule(mesh(), row, position=1,
                                      source_owned_and_embed_approved=True)
    with pytest.raises(LineageHold):
        compile_ternary_shape_capsule(mesh(), record(
            sha256=digest, rights="verified_metadata_only"),
            position=1, payload=payload, source_owned_and_embed_approved=True)


def test_capsule_denies_wrong_payload_and_research_shape():
    from tools.cgx_unispace_unified_lineage import compile_ternary_shape_capsule
    import hashlib
    row = record(rights="cleared_distribution",
                 sha256=hashlib.sha256(b"real").hexdigest())
    with pytest.raises(LineageHold):
        compile_ternary_shape_capsule(mesh(), row, position=1,
                                      payload=b"fake",
                                      source_owned_and_embed_approved=True)
    for invalid in (0, 174, 243):
        with pytest.raises(LineageHold):
            compile_ternary_shape_capsule(mesh(), row, position=invalid)


def test_capsule_sorted_nested_refs_and_self_reference_hold():
    from tools.cgx_unispace_unified_lineage import (
        compile_ternary_shape_capsule, validate_ternary_shape_capsule
    )
    import hashlib
    row = record(rights="cleared_distribution",
                 sha256=hashlib.sha256(b"x").hexdigest())
    capsule = compile_ternary_shape_capsule(mesh(), row, position=1,
                 children=["cgx:object:b", "cgx:object:a"])
    assert capsule["child_object_refs"] == ["cgx:object:a", "cgx:object:b"]
    assert validate_ternary_shape_capsule(capsule)["integrity"] == "HASH_VERIFIED"
    with pytest.raises(LineageHold):
        compile_ternary_shape_capsule(mesh(), row, position=1,
                                     children=[row["object_id"]])
    with pytest.raises(LineageHold):
        compile_ternary_shape_capsule(mesh(), row, position=1,
                                     children=["cgx:object:a"] * 2)


def test_capsule_detects_tampering_and_fake_execution_flags():
    from tools.cgx_unispace_unified_lineage import (
        compile_ternary_shape_capsule, validate_ternary_shape_capsule
    )
    import hashlib
    payload = b"public-owned"
    row = record(rights="cleared_distribution",
                 sha256=hashlib.sha256(payload).hexdigest())
    capsule = compile_ternary_shape_capsule(mesh(), row, position=4,
                payload=payload, source_owned_and_embed_approved=True)
    for field, value in (
        ("mint_authorized", True),
        ("native_mesh_verified", True),
        ("network_published", True),
        ("source_sha256", "f" * 64),
        ("capsule_sha256", "a" * 64),
        ("payload_binary_bytes", len(payload) + 1),
    ):
        altered = copy.deepcopy(capsule)
        altered[field] = value
        with pytest.raises(LineageHold):
            validate_ternary_shape_capsule(altered)
    altered = copy.deepcopy(capsule)
    altered["payload_ternary"] = "222222" + altered["payload_ternary"][6:]
    with pytest.raises(LineageHold):
        validate_ternary_shape_capsule(altered)


def test_capsule_denies_unqualified_private_source_even_reference_only():
    from tools.cgx_unispace_unified_lineage import compile_ternary_shape_capsule
    row = record(rights="restricted", profile_scope="owner", sha256="f" * 64)
    with pytest.raises(LineageHold):
        compile_ternary_shape_capsule(mesh(), row, position=1)


def test_capsule_hash_order_independent_for_nesting():
    from tools.cgx_unispace_unified_lineage import compile_ternary_shape_capsule
    import hashlib
    row = record(rights="cleared_distribution",
                 sha256=hashlib.sha256(b"x").hexdigest())
    a = compile_ternary_shape_capsule(mesh(), row, position=1,
                                    children=["cgx:object:two","cgx:object:one"])
    b = compile_ternary_shape_capsule(mesh(), row, position=1,
                                    children=["cgx:object:one","cgx:object:two"])
    assert a["capsule_sha256"] == b["capsule_sha256"]
