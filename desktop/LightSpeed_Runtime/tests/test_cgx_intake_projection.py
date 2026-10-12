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
