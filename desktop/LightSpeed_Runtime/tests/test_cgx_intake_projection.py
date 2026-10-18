"""Offline tests for CGX intake; provider CI imports real Node Exchange."""
from __future__ import annotations
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.cgx_intake_projection import (
    IntakeError, project_intake, plan_two_node_exchange, project_public_preview
)

SRC = {"provider": "test-drive", "provider_file_id": "f-1",
       "provider_revision": "r-1", "source_name": "test.csv",
       "source_ref": "provider://file-1", "owner_domain": "romer",
       "licence": "owner-controlled", "visibility": "INTERNAL_ONLY"}


def test_original_source_and_semantic_frontier_are_separate():
    x = project_intake(b"distance_m,quality\n12,unknown\n", SRC)
    assert x["identity"]["object_id"] is None
    assert x["identity"]["source_size_bytes"] == len(b"distance_m,quality\n12,unknown\n")
    assert x["recognition"]["known_structure"]["columns"] == ["distance_m", "quality"]
    assert x["layers"]["R3_geometry"] == "UNKNOWN"
    assert x["gates"]["canonical_dbr_commit"] == "HOLD"


def test_domain_does_not_come_from_filename():
    x = project_intake(b"geometry", {**SRC, "owner_domain": "eco", "source_name": "Romer.stl"})
    assert x["identity"]["owner_domain"] == "eco"
    assert x["recognition"]["known_structure"] is None
    with pytest.raises(IntakeError):
        project_intake(b"ok", {**SRC, "owner_domain": "unregistered"})


def test_provider_revision_and_hash_are_not_invented():
    with pytest.raises(IntakeError):
        project_intake(b"data", {**SRC, "provider_revision": ""})
    with pytest.raises(IntakeError):
        project_intake(b"data", {**SRC, "expected_sha256": "f" * 64})


def test_json_recognition_not_physical_proof():
    x = project_intake(b'{"example": 1}', {**SRC, "source_name": "example.json",
        "semantic_assertions": [{"label": "mass", "value": 12, "unit": "kg", "evidence_ref": "source-row"}]})
    assert x["recognition"]["known_structure"]["kind"] == "json-object"
    assert x["semantics"]["assertions"][0]["state"] == "SOURCE_ASSERTION_UNVERIFIED"
    assert x["semantics"]["verified_semantics"] is False
    assert x["gates"]["physical_qualification"] == "HOLD"


def test_independent_desktop_phone_plan_remains_unsigned():
    x = project_intake(b"raw", SRC)
    a = {"node_id": "desktop-one", "root_id": "root-a", "device_kind": "desktop_host", "authenticated": True}
    b = {"node_id": "phone-two", "root_id": "root-b", "device_kind": "mobile_touch", "authenticated": True}
    plan = plan_two_node_exchange(x, a, b)
    assert plan["transfer_envelope"]["source_sha256"] == x["identity"]["source_sha256"]
    assert plan["transfer_envelope"]["target_node_id"] == "phone-two"
    assert plan["signed"] is False and plan["authenticated"] is False
    assert plan["state"].startswith("HOLD_")
    with pytest.raises(IntakeError):
        plan_two_node_exchange(x, a, {**b, "node_id": "desktop-one"})


def test_private_projection_never_leaks_any_public_title():
    x = project_intake(b"private", SRC)
    result = project_public_preview(x, {"title": "Secret", "summary": "Secret summary"})
    assert result == {"schema": "cgx.unispace.public-preview/1",
                      "state": "HOLD_NOT_PUBLIC_SAFE", "published": False}


def test_public_marking_is_not_publication():
    x = project_intake(b"public-candidate", {**SRC, "owner_domain": "eco", "visibility": "PUBLIC_SAFE"})
    preview = project_public_preview(x, {"title": "Eco-Grex", "summary": "Public research overview"})
    assert preview["published"] is False
    assert preview["release_receipt"] is None
    for key in ("source_ref", "acl_ref", "source_sha256", "provider_file_id"):
        assert key not in preview


def test_bounds_and_no_source_rights_fabrication():
    with pytest.raises(IntakeError):
        project_intake("string not bytes", SRC)
    with pytest.raises(IntakeError):
        project_intake(b"data", {**SRC, "licence": ""})


def test_native_source_envelope_to_filespace_candidate_keeps_r0_boundary():
    from lightspeed_runtime.source_intake import build_source_envelope
    raw = b"mass_kg,value\n12,unknown\n"
    env = build_source_envelope(
        source_name=SRC["source_name"], data=raw, source_ref=SRC["source_ref"],
        release_class="Internal",
    )
    from lightspeed_runtime.cgx_intake_projection import project_native_envelope_candidate
    result = project_native_envelope_candidate(raw, env, SRC)
    assert result["identity"]["source_sha256"] == env["sha256"]
    assert result["native_envelope_binding"]["envelope_sha256"] == env["envelope_sha256"]
    assert result["native_envelope_binding"]["provider_revision_verified"] is False
    assert result["layers"]["R1_admission"] == "REQUIRES_SEPARATE_CONVERSION_PLAN"
    assert result["gates"]["canonical_dbr_commit"] == "HOLD"
    assert result["gates"]["public_release"] == "HOLD"
    assert "projections" not in result["native_envelope_binding"]


@pytest.mark.parametrize("change", ["different_bytes", "changed_name", "changed_ref",
                                    "changed_sha", "changed_size", "tampered_envelope",
                                    "mutating_lineage", "missing_lineage", "wrong_schema"])
def test_native_source_envelope_rejects_unbound_or_modified_inputs(change):
    from lightspeed_runtime.source_intake import build_source_envelope
    from lightspeed_runtime.cgx_intake_projection import project_native_envelope_candidate
    raw = b"original,1\n"
    env = build_source_envelope(
        source_name=SRC["source_name"], data=raw, source_ref=SRC["source_ref"],
    )
    data, metadata = raw, dict(SRC)
    if change == "different_bytes":
        data += b"x"
    elif change == "changed_name":
        metadata["source_name"] = "new.csv"
    elif change == "changed_ref":
        metadata["source_ref"] = "provider://moved"
    elif change == "changed_sha":
        env["native_preservation"]["source_sha256"] = "0" * 64
    elif change == "changed_size":
        env["byte_length"] += 1
    elif change == "tampered_envelope":
        env["evidence_state"] = "EMPIRICAL"
    elif change == "mutating_lineage":
        env["lineage"]["canonical_mutation"] = True
    elif change == "missing_lineage":
        env.pop("lineage")
    else:
        env["schema"] = "untrusted"
    with pytest.raises(IntakeError):
        project_native_envelope_candidate(data, env, metadata)


def test_native_envelope_visibility_does_not_escalate_to_public_release():
    from lightspeed_runtime.source_intake import build_source_envelope
    from lightspeed_runtime.cgx_intake_projection import project_native_envelope_candidate
    raw = b"private"
    env = build_source_envelope(
        source_name=SRC["source_name"], data=raw, source_ref=SRC["source_ref"],
        release_class="Internal",
    )
    with pytest.raises(IntakeError):
        project_native_envelope_candidate(raw, env, {**SRC, "visibility": "PUBLIC_SAFE"})
    public_env = build_source_envelope(
        source_name=SRC["source_name"], data=raw, source_ref=SRC["source_ref"],
        release_class="Public",
    )
    preview_only = project_native_envelope_candidate(
        raw, public_env, {**SRC, "visibility": "PUBLIC_SAFE"},
    )
    assert preview_only["public_publish_authorized"] is False
    assert preview_only["gates"]["public_release"] == "HOLD"

def _r1_fixture(raw=b"a,b\\n1,2\\n", name="test.csv"):
    from lightspeed_runtime.source_intake import build_source_envelope
    meta = {**SRC, "source_name": name}
    env = build_source_envelope(source_name=name, data=raw, source_ref=meta["source_ref"])
    profiles = {
        "schema": "CGX-FILE-TYPE-CONVERSION-REGISTRY/0.1",
        "types": [
            {"id": "text/csv", "extensions": ["csv"], "r1": "table", "adapter": "csv-stdlib-v0.1", "status": "supported"},
            {"id": "application/json", "extensions": ["json"], "r1": "JSON tree", "adapter": "json-stdlib-v0.1", "status": "supported"},
            {"id": "model/step", "extensions": ["step"], "r1": None, "adapter": "step-part21-stdlib-v0.1", "status": "specialist-adapter-required"},
        ],
    }
    contract = {"schema": "CGX-FILE-CONVERSION-CONTRACT/0.1"}
    return raw, env, meta, profiles, contract


def test_native_r1_plan_connects_existing_registered_adapter_but_not_acceptance():
    from lightspeed_runtime.cgx_intake_projection import plan_native_r1_review
    raw, env, meta, types, contract = _r1_fixture()
    result = plan_native_r1_review(raw, env, meta, type_registry=types, conversion_contract=contract)
    assert result["state"] == "R1_PLAN_READY_INDEPENDENT_RECONSTRUCTION_REQUIRED"
    assert result["conversion_plan"]["stages"][0]["class"] == "R0_EXACT"
    assert result["conversion_plan"]["stages"][1]["class"] == "R1_SEMANTIC_REVERSIBLE"
    assert result["conversion_plan"]["execution_performed"] is False
    assert result["identity"]["source_id"] == env["source_id"]
    assert result["identity"]["plan_sha256"] == result["conversion_plan"]["plan_sha256"]
    for flag in ("independent_r1_round_trip_verified", "provider_revision_verified",
                 "source_rights_verified", "r2_semantics_admitted", "dbr_receipt_issued",
                 "signed_peer_verified", "owner_approval_verified", "canonical_mutation",
                 "public_release_authorized", "physical_qualification"):
        assert result[flag] is False
    assert not any(stage["class"] == "R2_RECONSTRUCTED" for stage in result["conversion_plan"]["stages"])


def test_native_r1_plan_holds_mismatched_adapter_and_unregistered_type():
    from lightspeed_runtime.cgx_intake_projection import plan_native_r1_review
    raw, env, meta, types, contract = _r1_fixture()
    types["types"][0]["adapter"] = "unverified-parallel-csv"
    result = plan_native_r1_review(raw, env, meta, type_registry=types, conversion_contract=contract)
    assert result["state"] == "HOLD_ADAPTER_IDENTITY_MISMATCH"
    types["types"] = []
    result = plan_native_r1_review(raw, env, meta, type_registry=types, conversion_contract=contract)
    assert result["state"] == "HOLD_UNREGISTERED_R1_ADAPTER"


def test_native_r1_plan_holds_malformed_json_even_with_registered_adapter():
    from lightspeed_runtime.cgx_intake_projection import plan_native_r1_review
    raw, env, meta, types, contract = _r1_fixture(b'{"bad": NaN,', "source.json")
    assert env["warnings"] or env["unresolved"]
    result = plan_native_r1_review(raw, env, meta, type_registry=types, conversion_contract=contract)
    assert result["state"] == "HOLD_NATIVE_PROJECTION_UNRESOLVED"
    assert result["canonical_mutation"] is False


def test_native_r1_plan_requires_consistent_source_hash_and_explicit_registries():
    from lightspeed_runtime.cgx_intake_projection import plan_native_r1_review
    raw, env, meta, types, contract = _r1_fixture()
    with pytest.raises(IntakeError):
        plan_native_r1_review(raw + b"x", env, meta, type_registry=types, conversion_contract=contract)
    with pytest.raises(IntakeError):
        plan_native_r1_review(raw, env, meta, type_registry=None, conversion_contract=contract)
    with pytest.raises(IntakeError):
        plan_native_r1_review(raw, env, meta, type_registry=types,
                              conversion_contract={"schema": "UNKNOWN"})


def test_native_r1_plan_preserves_original_source_authority_when_reading_cad():
    from lightspeed_runtime.cgx_intake_projection import plan_native_r1_review
    raw, env, meta, types, contract = _r1_fixture(
        b"ISO-10303-21;\\nHEADER;\\nENDSEC;\\nDATA;\\nENDSEC;\\nEND-ISO-10303-21;", "test.step",
    )
    result = plan_native_r1_review(raw, env, meta, type_registry=types, conversion_contract=contract)
    assert result["state"] == "HOLD_UNREGISTERED_R1_ADAPTER"
    assert result["r0_candidate"]["identity"]["source_sha256"] == env["sha256"]
    assert result["public_release_authorized"] is False
