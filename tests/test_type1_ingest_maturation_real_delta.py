import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def test_real_atlas_delta_replays_into_current_projection_without_physical_uplift():
    proof = load("cgx/component_atlas/type1_ingest_maturation_real_delta_proof_20261011.json")
    atlas = load("cgx/component_atlas/component_geometry_atlas_v0_1.json")
    review = load("apps/lightspeed-go/public/data/cgx_object_review_catalogue.json")

    assert proof["artifact_id"] == "UTP-150-PROOF-001"
    assert proof["trigger"] == "source_revision_or_hash_changed"
    assert proof["source_before"]["record_count"] == 407
    assert proof["source_after"]["record_count"] == 411
    assert proof["source_before"]["git_blob_sha"] != proof["source_after"]["git_blob_sha"]

    assert atlas["record_count"] == proof["source_after"]["record_count"]
    assert review["coverage"]["printable_4d_archetypes"] == atlas["record_count"]
    assert review["maturity_projection"]["artifact_id"] == "UTP-150"

    assert proof["numeric_route"] == "NUMERIC"
    assert "record counts" in proof["numeric_basis"]
    assert proof["maturity_delta"]["physical_evidence"] == "UNCHANGED / PHYSICAL_NOT_RUN"
    assert proof["authority_ceiling"].endswith("PHYSICAL_NOT_RUN")
    assert proof["carriers_changed"] is False
    assert proof["physical_execution"] is False
    assert proof["public_release"] is False
    assert proof["next_witness_or_hold"].startswith("P0_IDENTITY")
