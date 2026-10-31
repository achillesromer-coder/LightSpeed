#!/usr/bin/env python3
"""One CGX/LightSpeed Windows setup evidence checkpoint.

Read-only: inspects the existing S92 host, LightSpeed runtime, Family Set,
SQLite operational identities, source-index declarations and loopback services.
This is diagnostic evidence, never a native mint, RootAuthority or signed lease.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
from typing import Any
from urllib.error import URLError, HTTPError
from urllib.request import Request, build_opener, ProxyHandler

SCHEMA = "CGX-WINDOWS-SETUP-AND-BOOT-EVIDENCE/0.1"
S92_INSTANCE = "cgx:phase-a:42d99b46c0d322f08b59b7b7"
S92_SHA256 = "722558c274416c8e3d7e555575fb7fa43e0538aca72d6875ee06bb1486175db5"
SEMANTIC_ROOT = "cgx:root:cognigrex"
FAMILY_IDENTITY_SCHEMA = "CGX-DOMAIN-CHILD-IDENTITY/0.1"
LOAD_SOURCE_SCHEMA = "LOAD-ALEXANDRIA-SOURCE-REGISTRY-PROJECTION/0.1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_CARRIER_BYTES = 128 * 1024 * 1024


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
        raise ValueError("JSON_NOT_FOUND_OR_SIZE_LIMIT")
    with path.open("rb") as stream:
        raw = stream.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("JSON_TOO_LARGE")
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("JSON_ROOT_NOT_OBJECT")
    return data


def _sha256(path: Path) -> str:
    if not path.is_file() or path.stat().st_size > MAX_CARRIER_BYTES:
        raise ValueError("CARRIER_MISSING_OR_TOO_LARGE")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(repo: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            timeout=8, capture_output=True, text=True, check=False,
        )
        value = result.stdout.strip().lower()
        return value if result.returncode == 0 and HEX40.fullmatch(value) else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _family_identity(path: Path) -> dict[str, Any]:
    source = _load_json(path)
    root = source.get("root")
    children = source.get("children")
    if (source.get("schema") != FAMILY_IDENTITY_SCHEMA
        or not isinstance(root, dict)
        or root.get("semantic_object_id") != SEMANTIC_ROOT
        or root.get("filespace") != "Cognigrex.cgx"
        or not isinstance(children, dict) or not children):
        raise ValueError("SINGLE_CGX_PARENT_NOT_VERIFIED")
    seen = {SEMANTIC_ROOT}
    filespaces = {"Cognigrex.cgx"}
    rows = []
    for name, child in sorted(children.items()):
        if not isinstance(child, dict):
            raise ValueError("CHILD_IDENTITY_INVALID")
        object_id = child.get("semantic_object_id")
        parent = child.get("parent_semantic_object_id")
        filespace = child.get("filespace")
        if (child.get("domain_id") != name
            or not isinstance(object_id, str) or not object_id.startswith("cgx:domain:")
            or object_id in seen or not isinstance(filespace, str)
            or not filespace.endswith(".cgx") or filespace in filespaces
            or not isinstance(parent, str)):
            raise ValueError("FAMILY_ID_COLLISION_OR_INVALID")
        seen.add(object_id)
        filespaces.add(filespace)
        rows.append({
            "domain": name, "semantic_object_id": object_id,
            "filespace": filespace, "parent_semantic_object_id": parent,
        })
    parent_map = {x["semantic_object_id"]: x["parent_semantic_object_id"] for x in rows}
    for item in rows:
        visited = {item["semantic_object_id"]}
        next_parent = item["parent_semantic_object_id"]
        while next_parent != SEMANTIC_ROOT:
            if next_parent in visited or next_parent not in parent_map:
                raise ValueError("FAMILY_PARENT_CYCLE_OR_ORPHAN")
            visited.add(next_parent)
            next_parent = parent_map[next_parent]
    if len({r["filespace"] for r in rows}) != len(rows):
        raise ValueError("DUPLICATE_FAMILY_FILESPACE")
    return {"semantic_parent": SEMANTIC_ROOT, "filespace": "Cognigrex.cgx", "children": rows}


def _sqlite_states(path: Path, ids: list[str]) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError("EXISTING_OPERATIONAL_DATABASE_MISSING")
    con = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=3)
    con.execute("PRAGMA query_only=ON")
    try:
        names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"canonical_objects", "object_identifiers", "object_representations"}
        if not required.issubset(names):
            raise ValueError("NATIVE_OPERATIONAL_SCHEMA_MISSING")
        parent = con.execute(
            "SELECT object_id,state FROM canonical_objects WHERE object_id=? LIMIT 3",
            (S92_INSTANCE,),
        ).fetchall()
        r0 = con.execute(
            "SELECT state,content_sha256 FROM object_representations "
            "WHERE object_id=? AND representation_type='R0_source' LIMIT 3",
            (S92_INSTANCE,),
        ).fetchall()
        states: dict[str, Any] = {}
        for identity in ids:
            rows = con.execute(
                "SELECT i.object_id,i.state,c.state FROM object_identifiers i "
                "LEFT JOIN canonical_objects c ON c.object_id=i.object_id "
                "WHERE i.identifier_value=? LIMIT 3",
                (identity,),
            ).fetchall()
            if len(rows) != 1 or rows[0][2] is None:
                states[identity] = {
                    "resolution": "HOLD_COLLISION" if len(rows) > 1 else "NOT_NATIVE_MATCHED",
                    "operational_state": None,
                }
            else:
                states[identity] = {
                    "resolution": "OPERATIONAL_ROW_ONLY",
                    "identifier_state": rows[0][1],
                    "operational_state": rows[0][2],
                }
        aliases = con.execute(
            "SELECT COUNT(*) FROM object_identifiers "
            "WHERE lower(identifier_value) IN (?,?,?,?)",
            ("load", "load.cgx", "alexandria", "library of alexandria"),
        ).fetchone()[0]
        return {
            "read_only": True,
            "parent_instance_state": parent[0][1] if len(parent) == 1 else "UNRESOLVED",
            "r0_state": r0[0][0] if len(r0) == 1 else "UNRESOLVED",
            "r0_sha_match": len(r0) == 1 and r0[0][1] == S92_SHA256,
            "semantic_states": states,
            "load_alias_exact_name_candidates": aliases,
            "load_alias_collision_exhaustively_proven": False,
            "native_dbr_accepted": False,
        }
    finally:
        con.close()


def _load_projection(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"state": "NOT_SUPPLIED", "source_refs": 0, "native_accepted": False}
    data = _load_json(path)
    summary, records, registries = data.get("summary"), data.get("records"), data.get("source_registries")
    if (data.get("schema") != LOAD_SOURCE_SCHEMA
        or data.get("state") != "GIT_SOURCE_ONLY_NOT_CANONICAL"
        or data.get("parent") != "Cognigrex.cgx" or data.get("file_space") != "LOAD.cgx"
        or not isinstance(summary, dict) or not isinstance(records, list)
        or not isinstance(registries, dict)
        or summary.get("native_accepted") != 0
        or summary.get("source_bodies_copied") != 0
        or summary.get("native_host_verified") is not False):
        raise ValueError("ALEXANDRIA_REFERENCE_PROJECTION_UNTRUSTED")
    unique, counts = set(), Counter()
    if len(records) > 10000 or len(registries) > 200:
        raise ValueError("ALEXANDRIA_SOURCE_LIMIT")
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("ALEXANDRIA_RECORD_INVALID")
        category, source_key = record.get("category"), record.get("source_key")
        ref, blob = record.get("source_registry"), record.get("source_git_blob")
        if (not isinstance(category, str) or not isinstance(source_key, str)
            or not isinstance(ref, str) or ref not in registries
            or not isinstance(registries[ref], dict) or registries[ref].get("git_blob") != blob
            or not isinstance(blob, str) or not HEX40.fullmatch(blob)
            or record.get("admission") != "SOURCE_REGISTRY_ONLY"
            or record.get("canonical_object_id") is not None
            or record.get("native_absorbed") not in (None, False)
            or record.get("installed_online") not in (None, False)):
            raise ValueError("ALEXANDRIA_SOURCE_PROVENANCE_OR_COLLISION_HOLD")
        key = (category, source_key)
        if key in unique:
            raise ValueError("ALEXANDRIA_SOURCE_PROVENANCE_OR_COLLISION_HOLD")
        unique.add(key)
        counts[category] += 1
    if (summary.get("record_count") != len(unique)
        or summary.get("record_categories") != dict(counts)
        or not isinstance(data.get("frontier"), list)
        or summary.get("frontier_count") != len(data["frontier"])):
        raise ValueError("ALEXANDRIA_SUMMARY_NOT_RECONCILED")
    return {
        "state": "GIT_SOURCE_ONLY_NOT_CANONICAL",
        "source_refs": len(unique),
        "categories": dict(sorted(counts.items())),
        "source_registry_count": len(registries),
        "frontier_count": len(data.get("frontier", [])) if isinstance(data.get("frontier"), list) else None,
        "native_accepted": False, "source_bodies_copied": 0,
        "provider_content_fetched": False,
    }


def _loopback_status(offline: bool) -> dict[str, Any]:
    if offline:
        return {"bridge": "NOT_QUERIED", "go": "NOT_QUERIED"}
    opener = build_opener(ProxyHandler({}))
    results: dict[str, Any] = {}
    for name, url in [
        ("bridge", "http://127.0.0.1:8765/api/v1/status"),
        ("go", "http://127.0.0.1:4173/"),
    ]:
        try:
            with opener.open(Request(url, headers={"Accept": "application/json" if name == "bridge" else "text/html"}), timeout=2) as response:
                body = response.read(65537)
                if response.status != 200 or len(body) > 65536:
                    raise ValueError("HEALTH_RESPONSE_INVALID")
                if name == "bridge":
                    parsed = json.loads(body)
                    results[name] = "LS_GO_IDENTITY_SEEN" if parsed.get("bridge") == "ls-go" else "UNRECOGNISED_SERVICE"
                else:
                    results[name] = "HTTP_200" if b"<html" in body.lower() or b"<!doctype html" in body.lower() else "UNRECOGNISED_PAGE"
        except (OSError, ValueError, URLError, HTTPError, json.JSONDecodeError):
            results[name] = "NOT_VERIFIED"
    return results


def build_evidence(
    repo: Path,
    canonical_root: Path,
    host_root: Path,
    *,
    load_registry: Path | None = None,
    offline: bool = False,
) -> dict[str, Any]:
    issues: list[str] = []
    identity: dict[str, Any] = {}
    operational: dict[str, Any] = {}
    carrier: dict[str, Any] = {}
    load: dict[str, Any] = {}
    source_commit = _git_head(repo)
    try:
        identity = _family_identity(repo / "cgx/domain_templates/domain_child_identity_registry.json")
    except (ValueError, OSError, json.JSONDecodeError, UnicodeError):
        issues.append("CANONICAL_FAMILY_REGISTRY_UNVERIFIED")
    try:
        root = _load_json(host_root / "cognigrex.root.json")
        binding = root.get("root_carrier") or {}
        bytes_sha = _sha256(host_root / "Cognigrex.cgx")
        same = (binding.get("object_id") == S92_INSTANCE
                and binding.get("sha256") == S92_SHA256
                and bytes_sha == S92_SHA256)
        carrier = {
            "binding_match": same,
            "instance": S92_INSTANCE if same else "UNVERIFIED",
            "sha256": bytes_sha,
            "semantic_root": SEMANTIC_ROOT,
            "native_signature_verified": False,
        }
        if not same:
            issues.append("S92_PARENT_CARRIER_OR_ROOT_REGISTRY_DIFFERENCE")
    except (ValueError, OSError, json.JSONDecodeError, UnicodeError):
        issues.append("HOST_S92_ROOT_CARRIER_UNAVAILABLE")
    try:
        ids = [SEMANTIC_ROOT, *(x["semantic_object_id"] for x in identity["children"])]
        operational = _sqlite_states(canonical_root / "Data/db/lightspeed_unified.db", ids)
        if operational.get("parent_instance_state") != "active":
            issues.append("OPERATIONAL_PARENT_NOT_ACTIVE")
        if not operational.get("r0_sha_match"):
            issues.append("OPERATIONAL_R0_HASH_UNVERIFIED")
    except (ValueError, OSError, sqlite3.Error, KeyError):
        issues.append("EXISTING_OPERATIONAL_DATABASE_NOT_READABLE")
    try:
        load = _load_projection(load_registry)
    except (ValueError, OSError, json.JSONDecodeError, UnicodeError):
        load = {"state": "HOLD_UNTRUSTED_REFERENCE_PROJECTION", "source_refs": 0, "native_accepted": False}
        issues.append("LOAD_SOURCE_REGISTRY_HOLD")
    runtime = {
        "managed_python": (canonical_root / "Environment/Scripts/python.exe").is_file(),
        "go_distribution": (canonical_root / "Apps/lightspeed-go/dist/index.html").is_file(),
        "canonical_runner": (canonical_root / "Automation/run_cognigrex_local_stack.py").is_file(),
        "existing_stack_launcher": (repo / "tools/launch_lightspeed.ps1").is_file(),
        "existing_family_ingestion_module": (
            repo / "desktop/LightSpeed_Runtime/lightspeed_runtime/cgx_family_ingestion.py"
        ).is_file(),
        "existing_setup_planner": (repo / "cgx/bootstrap/unifiedBootstrap.mjs").is_file(),
        "existing_setup_page": (repo / "cgx/bootstrap/smartSetup.html").is_file(),
    }
    for key in ("managed_python", "go_distribution", "canonical_runner", "existing_stack_launcher"):
        if not runtime[key]:
            issues.append("BOOT_COMPONENT_MISSING:" + key)
    if not runtime["existing_family_ingestion_module"]:
        issues.append("FAMILY_INGESTION_PR214_NOT_IN_CHECKOUT")
    if not runtime["existing_setup_planner"] or not runtime["existing_setup_page"]:
        issues.append("UNIFIED_SETUP_PR206_NOT_IN_CHECKOUT")
    if source_commit is None:
        issues.append("GIT_SOURCE_IDENTITY_UNAVAILABLE")
    services = _loopback_status(offline)
    existing_stack_ready = (
        bool(carrier.get("binding_match"))
        and bool(identity)
        and bool(operational.get("read_only"))
        and bool(operational.get("r0_sha_match"))
        and all(runtime[k] for k in ("managed_python", "go_distribution", "canonical_runner", "existing_stack_launcher"))
    )
    integrated_cgx_ready = (
        existing_stack_ready and runtime["existing_family_ingestion_module"]
        and load.get("state") == "GIT_SOURCE_ONLY_NOT_CANONICAL"
        and operational.get("parent_instance_state") == "active"
    )
    # Even perfect local inventory does not establish issuer, rights, revocation or DBR.
    issues.extend([
        "CURRENT_SIGNED_LEASE_ISSUER_AND_REVOCATION_NOT_VERIFIED",
        "ROOT_AND_CHILD_OWNER_ACL_RIGHTS_NOT_VERIFIED",
        "ATOMIC_DBR_AND_INDEPENDENT_RECEIVER_NOT_VERIFIED",
        "NATIVE_MINT_AND_CANONICAL_COMMIT_REQUIRES_OWNER_REVIEW",
    ])
    return {
        "schema": SCHEMA,
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "HOST_READ_ONLY_BOOT_AND_MINT_REVIEW",
        "source": {"git_head": source_commit, "canonical_source_promoted_by_this_run": False},
        "family": identity,
        "s92_carrier": carrier,
        "operational": operational,
        "load_alexandria": load,
        "runtime": runtime,
        "services": services,
        "boot": {
            "existing_stack_prerequisites_ready": existing_stack_ready,
            "family_source_wiring_candidate": integrated_cgx_ready,
            "complete_integrated_cgx_ready": False,
            "boot_executed_by_this_probe": False,
            "boot_requires_explicit_operator_action": True,
        },
        "mint": {
            "state": "REVIEW_PROPOSAL_ONLY_NO_MINT",
            "native_mint_authorised": False,
            "object_ids_created": 0,
            "source_bodies_copied": 0,
            "canonical_db_writes": 0,
            "github_commits_by_this_probe": 0,
            "public_release": False,
            "root_instance_for_review": S92_INSTANCE,
            "source_reference_candidates": load.get("source_refs", 0),
        },
        "holds": list(dict.fromkeys(issues)),
        "next_action": "OWNER_REVIEW_ENVIRONMENT_RECEIPT_THEN_AUTHORITATIVE_LEASE_DBR_MINT",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CGX Windows read-only setup and boot diagnostic")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--host-root", type=Path, required=True)
    parser.add_argument("--load-source-registry", type=Path)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = build_evidence(
        args.repo, args.canonical_root, args.host_root,
        load_registry=args.load_source_registry, offline=args.offline,
    )
    if args.output is not None:
        # Owner-private, exclusive-create evidence; no canonical path mutation.
        with args.output.open("x", encoding="utf-8") as destination:
            json.dump(receipt, destination, indent=2)
            destination.write("\n")
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
