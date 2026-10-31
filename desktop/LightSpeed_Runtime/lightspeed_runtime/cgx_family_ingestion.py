"""Read-only CGX Family Set ingestion for the existing LightSpeed operator bridge.

Only current semantic identities and SOURCE-ONLY LOAD registry metadata are indexed.
No Object_ID creation, source-body hydration, DBR acceptance or host write occurs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
import sqlite3
from typing import Any

SCHEMA = "CGX-LS-FAMILY-OVERSIGHT/0.1"
IDENTITY_SCHEMA = "CGX-DOMAIN-CHILD-IDENTITY/0.1"
LOAD_SCHEMA = "LOAD-ALEXANDRIA-SOURCE-REGISTRY-PROJECTION/0.1"
ROOT_ID = "cgx:root:cognigrex"
CATEGORIES = frozenset({
    "conversion_source", "format_adapter", "toolkit", "selector",
    "filespace_action", "ccc_route", "function_family",
})
MAX_JSON_BYTES = 4 * 1024 * 1024


class CGXFamilyIngestionError(ValueError):
    """Evidence or configuration is untrusted or incomplete."""


def _json_file(path: Path) -> dict[str, Any]:
    file = Path(path)
    if not file.is_file() or file.stat().st_size > MAX_JSON_BYTES:
        raise CGXFamilyIngestionError("INPUT_JSON_MISSING_OR_EXCEEDS_BOUND")
    with file.open("rb") as handle:
        raw = handle.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise CGXFamilyIngestionError("INPUT_JSON_EXCEEDS_BOUND")
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CGXFamilyIngestionError("INPUT_JSON_INVALID") from exc
    if not isinstance(data, dict):
        raise CGXFamilyIngestionError("INPUT_JSON_NOT_OBJECT")
    return data


def _identity_rows(registry: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    root = registry.get("root")
    children = registry.get("children")
    if (registry.get("schema") != IDENTITY_SCHEMA or not isinstance(root, dict)
            or not isinstance(children, dict) or not children
            or root.get("semantic_object_id") != ROOT_ID
            or root.get("filespace") != "Cognigrex.cgx"):
        raise CGXFamilyIngestionError("CANONICAL_FAMILY_IDENTITY_MISMATCH")
    ids = {ROOT_ID}
    filespaces = {root["filespace"]}
    rows = []
    for key, child in sorted(children.items()):
        if not isinstance(child, dict) or child.get("domain_id") != key:
            raise CGXFamilyIngestionError("FAMILY_DOMAIN_ID_MISMATCH")
        semantic = child.get("semantic_object_id")
        parent = child.get("parent_semantic_object_id")
        filespace = child.get("filespace")
        if (not isinstance(semantic, str) or not semantic.startswith("cgx:domain:")
                or semantic in ids or not isinstance(filespace, str)
                or not filespace.endswith(".cgx") or filespace in filespaces
                or not isinstance(parent, str)):
            raise CGXFamilyIngestionError("FAMILY_IDENTITY_COLLISION_OR_INVALID")
        ids.add(semantic)
        filespaces.add(filespace)
        rows.append({
            "domain": key, "semantic_object_id": semantic,
            "parent_semantic_object_id": parent, "filespace": filespace,
        })
    if any(row["parent_semantic_object_id"] not in ids for row in rows):
        raise CGXFamilyIngestionError("FAMILY_PARENT_NOT_IN_SET")
    parent_of = {row["semantic_object_id"]: row["parent_semantic_object_id"] for row in rows}
    for row in rows:
        seen = {row["semantic_object_id"]}
        ancestor = row["parent_semantic_object_id"]
        while ancestor != ROOT_ID:
            if ancestor in seen or ancestor not in parent_of:
                raise CGXFamilyIngestionError("FAMILY_PARENT_CYCLE_OR_ORPHAN")
            seen.add(ancestor)
            ancestor = parent_of[ancestor]
    return root, rows


def _load_counts(projection: dict[str, Any], domains: set[str]) -> dict[str, Any]:
    summary = projection.get("summary")
    records = projection.get("records")
    registries = projection.get("source_registries")
    frontier = projection.get("frontier")
    if (projection.get("schema") != LOAD_SCHEMA
            or projection.get("state") != "GIT_SOURCE_ONLY_NOT_CANONICAL"
            or projection.get("parent") != "Cognigrex.cgx"
            or projection.get("file_space") != "LOAD.cgx"
            or not isinstance(summary, dict) or not isinstance(records, list)
            or not isinstance(registries, dict) or not isinstance(frontier, list)
            or summary.get("native_accepted") != 0
            or summary.get("native_host_verified") is not False
            or summary.get("source_bodies_copied") != 0
            or len(records) > 10000 or len(frontier) > 1000):
        raise CGXFamilyIngestionError("LOAD_NOT_SOURCE_ONLY_OR_INVALID")
    keys = set()
    categories: Counter[str] = Counter()
    domains_count: Counter[str] = Counter()
    for record in records:
        if not isinstance(record, dict):
            raise CGXFamilyIngestionError("LOAD_RECORD_INVALID")
        cat = record.get("category")
        key = record.get("source_key")
        reference = record.get("source_registry")
        proof = record.get("source_git_blob")
        if (cat not in CATEGORIES or not isinstance(key, str) or not key
                or not re.fullmatch(r"[a-z0-9][a-z0-9_.:/-]{0,199}", key, re.I)
                or (cat, key) in keys
                or not isinstance(reference, str) or reference not in registries
                or not isinstance(registries[reference], dict)
                or registries[reference].get("git_blob") != proof
                or not isinstance(proof, str)
                or re.fullmatch(r"[0-9a-f]{40}", proof) is None
                or record.get("admission") != "SOURCE_REGISTRY_ONLY"
                or record.get("canonical_object_id") is not None
                or record.get("native_absorbed") not in (None, False)
                or record.get("installed_online") not in (None, False)):
            raise CGXFamilyIngestionError("LOAD_RECORD_PROOF_OR_ADMISSION_MISMATCH")
        keys.add((cat, key))
        categories[cat] += 1
        domain = record.get("owner_domain")
        if domain in domains:
            domains_count[domain] += 1
    if (summary.get("record_count") != len(keys)
            or summary.get("record_categories") != dict(categories)
            or summary.get("frontier_count") != len(frontier)
            or len(registries) != summary.get("source_registry_count", len(registries))):
        raise CGXFamilyIngestionError("LOAD_SUMMARY_MISMATCH")
    return {
        "state": "SOURCE_REFERENCES_ONLY_NOT_ADMITTED",
        "reference_count": len(keys),
        "source_registry_count": len(registries),
        "frontier_count": len(frontier),
        "categories": dict(sorted(categories.items())),
        "by_domain": dict(sorted(domains_count.items())),
        "source_bodies_copied": 0,
        "native_accepted": 0,
        "provider_fetch_executed": False,
    }


def _operational_rows(db_path: Path, semantic_ids: list[str]) -> dict[str, dict[str, Any]]:
    file = Path(db_path)
    if not file.is_file():
        raise CGXFamilyIngestionError("CANONICAL_DB_MISSING")
    try:
        connection = sqlite3.connect(file.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
        connection.execute("PRAGMA query_only=ON")
        try:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"canonical_objects", "object_identifiers", "object_representations"} <= tables:
                raise CGXFamilyIngestionError("REPRESENTATION_EDGE_SCHEMA_UNAVAILABLE")
            result = {}
            for identity in semantic_ids:
                rows = connection.execute(
                    "SELECT i.object_id, i.state, c.state "
                    "FROM object_identifiers i LEFT JOIN canonical_objects c "
                    "ON c.object_id=i.object_id "
                    "WHERE i.identifier_value=? LIMIT 3", (identity,)
                ).fetchall()
                if len(rows) > 1:
                    result[identity] = {
                        "resolution": "IDENTITY_COLLISION_HOLD", "operational_state": "UNRESOLVED",
                        "identifier_state": "UNRESOLVED", "representation_count": 0,
                    }
                    continue
                if not rows or rows[0][2] is None:
                    result[identity] = {
                        "resolution": "NO_NATIVE_OBJECT_MATCH", "operational_state": "UNRESOLVED",
                        "identifier_state": "UNRESOLVED", "representation_count": 0,
                    }
                    continue
                object_id, identifier_state, object_state = rows[0]
                count = connection.execute(
                    "SELECT COUNT(*) FROM object_representations WHERE object_id=?",
                    (object_id,)
                ).fetchone()[0]
                result[identity] = {
                    "resolution": "OPERATIONAL_ROW_OBSERVED_NOT_DBR_ADMISSION",
                    "operational_state": object_state,
                    "identifier_state": identifier_state,
                    "representation_count": count,
                }
            return result
        finally:
            connection.close()
    except sqlite3.Error as exc:
        raise CGXFamilyIngestionError("CANONICAL_DB_READ_ONLY_QUERY_FAILED") from exc


def _carrier_binding(root_registry_path: Path | None, carrier_path: Path | None) -> dict[str, Any]:
    if not root_registry_path or not carrier_path:
        return {"state": "NOT_SUPPLIED", "byte_binding_match": False}
    root = _json_file(root_registry_path)
    expected = root.get("root_carrier")
    if not isinstance(expected, dict) or not isinstance(expected.get("sha256"), str):
        raise CGXFamilyIngestionError("HOST_ROOT_CARRIER_BINDING_MISSING")
    file = Path(carrier_path)
    if not file.is_file() or file.stat().st_size > 128 * 1024 * 1024:
        raise CGXFamilyIngestionError("CARRIER_MISSING_OR_SIZE_BOUND")
    sha = hashlib.sha256()
    with file.open("rb") as data:
        for chunk in iter(lambda: data.read(1024 * 1024), b""):
            sha.update(chunk)
    matched = sha.hexdigest() == expected["sha256"]
    return {
        "state": "LOCAL_BYTES_MATCH_REGISTRY" if matched else "CARRIER_HASH_HOLD",
        "byte_binding_match": matched,
        "root_carrier_object_id": expected.get("object_id"),
        "cryptographically_signed_authority_verified": False,
        "native_dbr_receiver_verified": False,
    }


def build_oversight(
    *,
    family_registry_path: Path,
    database_path: Path,
    load_registry_path: Path | None = None,
    root_registry_path: Path | None = None,
    carrier_path: Path | None = None,
) -> dict[str, Any]:
    root, children = _identity_rows(_json_file(family_registry_path))
    load = (
        _load_counts(_json_file(load_registry_path), {c["domain"] for c in children})
        if load_registry_path else {
            "state": "LOAD_SOURCE_PROJECTION_NOT_CONFIGURED",
            "reference_count": 0, "source_registry_count": 0,
            "frontier_count": 0, "categories": {}, "by_domain": {},
            "native_accepted": 0, "source_bodies_copied": 0,
        }
    )
    native = _operational_rows(
        database_path,
        [ROOT_ID, *[c["semantic_object_id"] for c in children]],
    )
    family_rows = []
    for row in children:
        observation = native[row["semantic_object_id"]]
        family_rows.append({
            **row,
            "operational": observation,
            "load_source_reference_count": load["by_domain"].get(row["domain"], 0),
            "native_child_accepted": False,
            "scope_owner_acl_verified": False,
            "load_alias_admitted": False,
            "runtime_capability_installed": False,
        })
    carrier = _carrier_binding(root_registry_path, carrier_path)
    return {
        "schema": SCHEMA,
        "mode": "OWNER_PRIVATE_READ_ONLY_NATIVE_AND_SOURCE_INDEX",
        "parent": {
            "semantic_object_id": root["semantic_object_id"],
            "filespace": root["filespace"],
            "operational": native[ROOT_ID],
            "carrier": carrier,
            "native_parent_admitted": False,
        },
        "families": family_rows,
        "load_alexandria": load,
        "unispace": {
            "role": "NON_AUTHORITATIVE_OWNER_INTERFACE",
            "native_source_authority": False, "private_hydration": False,
            "public_release": False,
        },
        "authority": {
            "owner_session_authenticated_by_this_module": False,
            "signed_lease_verified": False,
            "rights_and_acl_verified": False,
            "native_dbr_acceptance_verified": False,
            "independent_receiver_verified": False,
        },
        "effects": {
            "canonical_db_writes": 0, "source_bytes_copied": 0,
            "object_ids_minted": 0, "network_fetches": 0,
            "capabilities_installed": 0, "public_release": False,
        },
        "next_gate": "OWNER_AUTHENTICATED_RECEIPTS_LEASE_DBR_AND_CHILD_ACL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only CGX family oversight; no setup mutation")
    parser.add_argument("--family-registry", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--load-registry", type=Path)
    parser.add_argument("--root-registry", type=Path)
    parser.add_argument("--carrier", type=Path)
    args = parser.parse_args()
    try:
        result = build_oversight(
            family_registry_path=args.family_registry, database_path=args.database,
            load_registry_path=args.load_registry, root_registry_path=args.root_registry,
            carrier_path=args.carrier,
        )
    except CGXFamilyIngestionError as exc:
        print(json.dumps({"schema": SCHEMA, "state": "HOLD", "reason": str(exc)}))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
