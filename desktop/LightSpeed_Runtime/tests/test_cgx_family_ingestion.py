from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from lightspeed_runtime.cgx_family_ingestion import (
    CGXFamilyIngestionError, build_oversight,
)

ROOT = "cgx:root:cognigrex"
PARENT = "cgx:phase-a:42d99b46c0d322f08b59b7b7"
S92_SHA = "722558c274416c8e3d7e555575fb7fa43e0538aca72d6875ee06bb1486175db5"


def write_json(path: Path, payload: dict):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def identity():
    return {
        "schema": "CGX-DOMAIN-CHILD-IDENTITY/0.1",
        "root": {"semantic_object_id": ROOT, "filespace": "Cognigrex.cgx"},
        "children": {
            "romer": {
                "domain_id": "romer", "semantic_object_id": "cgx:domain:romer",
                "parent_semantic_object_id": ROOT, "filespace": "Romer.cgx",
            },
            "eco": {
                "domain_id": "eco", "semantic_object_id": "cgx:domain:eco",
                "parent_semantic_object_id": ROOT, "filespace": "Eco.cgx",
            },
            "emassc": {
                "domain_id": "emassc", "semantic_object_id": "cgx:domain:emassc",
                "parent_semantic_object_id": ROOT, "filespace": "EMASSC.cgx",
            },
            "lightspeed": {
                "domain_id": "lightspeed", "semantic_object_id": "cgx:domain:lightspeed",
                "parent_semantic_object_id": "cgx:domain:emassc", "filespace": "LS.cgx",
            },
        },
    }


def load_projection():
    proof = "a" * 40
    source = "cgx/domain_templates/first_file_conversion_registry.json"
    return {
        "schema": "LOAD-ALEXANDRIA-SOURCE-REGISTRY-PROJECTION/0.1",
        "state": "GIT_SOURCE_ONLY_NOT_CANONICAL",
        "parent": "Cognigrex.cgx", "file_space": "LOAD.cgx",
        "source_registries": {source: {"git_blob": proof}},
        "summary": {
            "record_count": 1, "record_categories": {"conversion_source": 1},
            "frontier_count": 0, "native_accepted": 0,
            "selector_route_counts": {"achilles": 31, "neo": 27},
            "native_host_verified": False, "source_bodies_copied": 0,
        },
        "records": [{
            "category": "conversion_source", "source_key": "FF-MARK3-XLSX-001",
            "display": "Mark_III_Digital_Twin_v0_1.xlsx",
            "source_registry": source, "source_git_blob": proof,
            "admission": "SOURCE_REGISTRY_ONLY", "owner_domain": "romer",
            "provider_locator": "PRIVATE_DO_NOT_EXPOSE",
        }],
        "frontier": [],
    }


def database(path):
    with sqlite3.connect(path) as con:
        con.executescript("""
        CREATE TABLE canonical_objects(object_id TEXT PRIMARY KEY, state TEXT);
        CREATE TABLE object_identifiers(identifier_value TEXT, object_id TEXT, state TEXT);
        CREATE TABLE object_representations(representation_id TEXT, object_id TEXT, state TEXT);
        """)
        con.execute(
            "INSERT INTO canonical_objects VALUES (?,?)", (PARENT, "candidate")
        )
        con.execute(
            "INSERT INTO object_identifiers VALUES (?,?,?)",
            (ROOT, PARENT, "active"),
        )
        con.execute(
            "INSERT INTO object_representations VALUES (?,?,?)",
            ("rep:root:r0", PARENT, "candidate"),
        )
    return path


def fixture(tmp_path):
    family = write_json(tmp_path / "family.json", identity())
    load = write_json(tmp_path / "load.json", load_projection())
    db = database(tmp_path / "native.db")
    return family, load, db


def test_read_only_family_ingestion_uses_one_parent_and_child_hierarchy(tmp_path):
    family, load, db = fixture(tmp_path)
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    result = build_oversight(
        family_registry_path=family, database_path=db, load_registry_path=load
    )
    assert result["parent"]["semantic_object_id"] == ROOT
    assert result["parent"]["operational"]["operational_state"] == "candidate"
    assert result["parent"]["native_parent_admitted"] is False
    assert len(result["families"]) == 4
    descendants = {item["domain"]: item for item in result["families"]}
    assert descendants["lightspeed"]["parent_semantic_object_id"] == "cgx:domain:emassc"
    assert descendants["romer"]["load_source_reference_count"] == 1
    assert descendants["eco"]["load_source_reference_count"] == 0
    assert all(x["native_child_accepted"] is False for x in result["families"])
    assert result["load_alexandria"]["reference_count"] == 1
    assert result["load_alexandria"]["native_accepted"] == 0
    assert result["load_alexandria"]["selector_source_route_counts"]["achilles"] == 31
    assert result["load_alexandria"]["selector_routes_are_installed"] is False
    assert "PRIVATE_DO_NOT_EXPOSE" not in json.dumps(result)
    assert result["effects"]["canonical_db_writes"] == 0
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before


def test_missing_load_registry_preserves_canonical_family_metadata(tmp_path):
    family, _load, db = fixture(tmp_path)
    result = build_oversight(family_registry_path=family, database_path=db)
    assert result["load_alexandria"]["state"] == "LOAD_SOURCE_PROJECTION_NOT_CONFIGURED"
    assert result["load_alexandria"]["reference_count"] == 0
    assert result["families"][0]["native_child_accepted"] is False


@pytest.mark.parametrize("mutate", [
    lambda x: x["children"]["lightspeed"].update(parent_semantic_object_id="cgx:root:other"),
    lambda x: x["children"]["eco"].update(semantic_object_id="cgx:domain:romer"),
    lambda x: x["children"]["emassc"].update(parent_semantic_object_id="cgx:domain:lightspeed"),
])
def test_family_parent_collisions_or_cycles_fail_closed(tmp_path, mutate):
    family, load, db = fixture(tmp_path)
    payload = identity()
    mutate(payload)
    write_json(family, payload)
    with pytest.raises(CGXFamilyIngestionError):
        build_oversight(
            family_registry_path=family, database_path=db, load_registry_path=load
        )


@pytest.mark.parametrize("mutation", [
    lambda x: x["summary"].update(native_accepted=1),
    lambda x: x["summary"].update(record_count=2),
    lambda x: x["records"][0].update(admission="NATIVE_ACCEPTED"),
    lambda x: x["records"][0].update(source_git_blob="0" * 40),
    lambda x: x["records"][0].update(installed_online=True),
    lambda x: x["summary"].update(selector_route_counts={"neo": "installed"}),
])
def test_load_source_only_provenance_and_install_claims_fail_closed(tmp_path, mutation):
    family, load, db = fixture(tmp_path)
    payload = load_projection()
    mutation(payload)
    write_json(load, payload)
    with pytest.raises(CGXFamilyIngestionError):
        build_oversight(
            family_registry_path=family, database_path=db, load_registry_path=load
        )


def test_native_semantic_identifier_collision_remains_hold(tmp_path):
    family, load, db = fixture(tmp_path)
    with sqlite3.connect(db) as con:
        con.execute(
            "INSERT INTO object_identifiers VALUES (?,?,?)",
            (ROOT, "another-native-object", "candidate"),
        )
    result = build_oversight(
        family_registry_path=family, database_path=db, load_registry_path=load
    )
    assert result["parent"]["operational"]["resolution"] == "IDENTITY_COLLISION_HOLD"
    assert result["parent"]["native_parent_admitted"] is False


def test_source_registry_and_carrier_byte_binding_not_signature_or_admission(tmp_path):
    family, load, db = fixture(tmp_path)
    carrier = tmp_path / "Cognigrex.cgx"
    carrier.write_bytes(b"native-carrier-test-bytes")
    root = write_json(tmp_path / "root.json", {
        "root_carrier": {
            "object_id": PARENT,
            "sha256": hashlib.sha256(carrier.read_bytes()).hexdigest(),
        },
    })
    result = build_oversight(
        family_registry_path=family, database_path=db, load_registry_path=load,
        root_registry_path=root, carrier_path=carrier,
    )
    observed = result["parent"]["carrier"]
    assert observed["byte_binding_match"] is True
    assert observed["native_dbr_receiver_verified"] is False
    assert observed["cryptographically_signed_authority_verified"] is False
    assert result["authority"]["signed_lease_verified"] is False


def test_missing_canonical_database_holds_instead_of_creating_it(tmp_path):
    family, _load, db = fixture(tmp_path)
    db.unlink()
    with pytest.raises(CGXFamilyIngestionError, match="CANONICAL_DB_MISSING"):
        build_oversight(family_registry_path=family, database_path=db)
    assert not db.exists()
