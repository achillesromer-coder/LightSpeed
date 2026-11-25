#!/usr/bin/env python3
"""Mint nine *ephemeral source fixtures* and exercise deterministic sandbox roles.

This is a bounded rehearsal of existing CGX selectors, NOT native Object_ID
admission, an agent process launch, a model inference, a wallet transaction or
an independent signature. The four cartesian quadrants are logical source
partitions, not OS/VM network isolation or physical spatial fields.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

from tools.cgx_unispace_agent_model_projection import build as source_projection, SELECTORS

SCHEMA = "CGX-QUADRANT-TEST-MINT/0.1"
OBJECT_SCHEMA = "CGX-ISOLATED-AGENT-TEST-OBJECT/0.1"
ROOT = "cgx:root:cognigrex"
RUN_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")
# Symbolic geometric routing only. The physical host remains unaffected.
QUADRANTS = {
    "cognigrex": ("QI", 1, 1),
    "raphael": ("QI", 2, 1),
    "emassc": ("QI", 1, 2),
    "neo": ("QII", -1, 1),
    "romer-grex": ("QII", -2, 1),
    "lightspeed": ("QIII", -1, -1),
    "eco-grex": ("QIII", -2, -1),
    "achilles": ("QIV", 1, -1),
    "athene": ("QIV", 2, -1),
}
BOUNDARIES = {
    "QI": "source_lineage_and_geometric_research",
    "QII": "bounded_runtime_and_engineering_simulation",
    "QIII": "interface_and_communication_projections",
    "QIV": "assurance_evidence_and_safety_review",
}
AUTHORITY = {
    "native_admitted": False,
    "native_canonical_write": False,
    "signed_dbr": False,
    "independent_peer_verified": False,
    "model_inference_executed": False,
    "agent_process_launched": False,
    "model_weights_changed": False,
    "agent_self_replication": False,
    "chain_mint_executed": False,
    "public_publish_authorized": False,
    "external_provider_writes_authorized": False,
    "physical_actuation_authorized": False,
}
MAX_OUTPUT_BYTES = 1000000


class QuadrantTestHold(ValueError):
    """Refuse a source-identity, boundary, or output tamper."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_quadrants() -> None:
    if set(QUADRANTS) != set(SELECTORS) or len(QUADRANTS) != 9:
        raise QuadrantTestHold("quadrant set must match the original nine selector sources")
    seen: set[tuple[int,int]] = set()
    for selector, (quadrant, x, y) in QUADRANTS.items():
        if quadrant not in BOUNDARIES or not all(type(v) is int for v in (x,y)):
            raise QuadrantTestHold("invalid geometric quadrant")
        if x == 0 or y == 0 or abs(x) > 3 or abs(y) > 3 or (x,y) in seen:
            raise QuadrantTestHold("origin, unbounded or overlapping geometric cell")
        observed = ("QI" if x>0 and y>0 else "QII" if x<0 and y>0
                    else "QIII" if x<0 and y<0 else "QIV")
        if quadrant != observed:
            raise QuadrantTestHold("coordinate does not match declared quadrant")
        seen.add((x,y))


def make_batch(repo: Path, *, run_id: str = "UOS-20261123") -> dict[str, Any]:
    if not isinstance(run_id,str) or not RUN_ID.fullmatch(run_id):
        raise QuadrantTestHold("bounded stable test Run_ID required")
    validate_quadrants()
    projection = source_projection(Path(repo))
    if (projection.get("canonical_root_id") != ROOT
            or projection.get("selector_count") != 9
            or projection.get("state") != "SOURCE_AGENT_MODEL_PROJECTION_ONLY"
            or projection.get("native_dbr_authorized") is not False
            or projection.get("agent_spawned") is not False):
        raise QuadrantTestHold("unqualified source or source claimed native authority")
    rows = projection.get("selectors")
    if not isinstance(rows,list) or len(rows) != 9 or {r.get("selector") for r in rows} != set(SELECTORS):
        raise QuadrantTestHold("original selector identities incomplete")
    objects = []
    for row in rows:
        name = row["selector"]
        q,x,y = QUADRANTS[name]
        source_sha = row.get("plugin_source_sha256")
        if not isinstance(source_sha,str) or not re.fullmatch(r"[0-9a-f]{64}",source_sha):
            raise QuadrantTestHold("missing source pin")
        if (row.get("native_executed") is not False
                or row.get("model_installed_verified") is not False
                or row.get("facets_granted_by_projection") != []):
            raise QuadrantTestHold("source claims live privilege")
        # Actual deterministic computation performed by each logical test role.
        work = {
            "source_proof": source_sha,
            "route_count": row["route_count"],
            "route_set_sha256": digest(sorted(row["route_ids"])),
            "source_crosswalk_sha256": projection["source_projection_sha256"],
        }
        ref = digest({"test":SCHEMA,"root":ROOT,"run":run_id,"selector":name,
                      "source":source_sha,"quadrant":q})
        candidate = {
            "schema":OBJECT_SCHEMA,
            "object_id":"cgx:test-mint:"+name+":"+ref[:24],
            "root":ROOT, "run_id":run_id,
            "selector":name, "identity_kind":row["kind"],
            "quadrant":q, "coordinates":{"frame":"synthetic-cartesian","x":x,"y":y},
            "quadrant_purpose":BOUNDARIES[q],
            "test_namespace":"ISOLATED_SOURCE_TEST_NOT_NATIVE",
            "status":"TEST_SOURCE_OBJECT_MINTED_IN_FIXTURE",
            "source_plugin_sha256":source_sha,
            "simulation":{"executed":True,"algorithm":"deterministic_source_digest_v1",
                          "work_result":work,"work_result_sha256":digest(work)},
            "lease":{"mode":"NO_LIVE_EXECUTION_LEASE","max_concurrent_model_jobs":0,
                     "max_effectful_jobs":0,"bounded_test_operations":1,
                     "ttl_seconds":3600,"cpu_threads_budget":1,
                     "memory_mib_budget":256,
                     "budgets_are_declarations_not_os_enforcement":True},
            "authority":dict(AUTHORITY),
            "promotable_without_independent_review":False,
        }
        candidate["record_sha256"] = digest(candidate)
        objects.append(candidate)
    if len({x["object_id"] for x in objects})!=9:
        raise QuadrantTestHold("Object_ID collision in test namespace")
    batch={
        "schema":SCHEMA,"root":ROOT,"run_id":run_id,
        "state":"TEST_SOURCE_FIXTURES_VERIFIED_PENDING_ACTUAL_AGENT_LAUNCH",
        "count":len(objects),"quadrant_count":4,
        "source_projection_sha256":projection["source_projection_sha256"],
        "source_frontier_count":len(projection["routing_frontier"]),
        "source_variances_remain_held":True,
        "simulation_steps_executed":len(objects),
        "native_agents_launched":0,
        "model_calls":0,
        "native_dbr_receipts":0,
        "onchain_transactions":0,
        "actual_os_network_isolation_proven":False,
        "actual_signer_or_peer_verified":False,
        "existing_agent_runtime_entrypoint":"scripts/run_cgx_agent_runtime.py",
        "native_activation_after_test":"HELD_UNTIL_INDEPENDENT_SCOPED_SIGNED_LEASE_AND_PEER",
        "test_is_not_cryptographic_attestation":True,
        "objects":[{"selector":x["selector"],"object_id":x["object_id"],
                    "quadrant":x["quadrant"],"record_sha256":x["record_sha256"]}
                   for x in objects],
        "global_authority":dict(AUTHORITY),
    }
    batch["batch_sha256"]=digest(batch)
    return {"manifest":batch,"records":objects}


def expected_files(payload: dict[str, Any]) -> dict[str,bytes]:
    names={"manifest.json":canonical(payload["manifest"])+b"\n"}
    for row in payload["records"]:
        names["agents/"+row["selector"]+".json"]=canonical(row)+b"\n"
    if len(names)!=10 or sum(map(len,names.values()))>MAX_OUTPUT_BYTES:
        raise QuadrantTestHold("bounded nine-agent test fixture requirement violated")
    return names


def publish(payload: dict[str,Any], out: Path, *, verify_only: bool=False) -> dict[str,Any]:
    out=Path(out).absolute()
    if out.is_symlink() or out.parent.is_symlink() or not out.parent.is_dir():
        raise QuadrantTestHold("unsafe or missing isolated output parent")
    expected=expected_files(payload)
    newly_created=False
    if not out.exists():
        if verify_only:
            raise QuadrantTestHold("mint fixtures absent")
        # Only create a new isolated review directory, never overwrite an existing one.
        try:
            out.mkdir(mode=0o700)
            newly_created=True
            (out/"agents").mkdir(mode=0o700)
            for rel,raw in expected.items():
                target=out/rel
                with target.open("xb") as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise QuadrantTestHold("concurrent output was created") from exc
    if not out.is_dir() or (out/"agents").is_symlink():
        raise QuadrantTestHold("test fixture directory replaced")
    present={p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
    if present!=set(expected) or any(p.is_symlink() for p in out.rglob("*")):
        raise QuadrantTestHold("unknown/missing output or redirected file")
    for rel,raw in expected.items():
        file=out/rel
        if file.is_symlink() or file.stat().st_size!=len(raw) or file.read_bytes()!=raw:
            raise QuadrantTestHold("test fixture readback hash or bytes mismatch")
    return {
        "status":"PASS_ISOLATED_SOURCE_TEST_MINT",
        "source_records":9,"quadrants":4,
        "newly_created":newly_created,
        "readback":True,
        "manifest_sha256":hashlib.sha256(expected["manifest.json"]).hexdigest(),
        "signed_native_mint":False,
        "onchain_mint":False,
        "native_agents_started":0,
        "model_calls":0,
    }


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--run-id",default="UOS-20261123")
    parser.add_argument("--verify-only",action="store_true")
    args=parser.parse_args()
    report=publish(make_batch(args.repo,run_id=args.run_id),args.out,verify_only=args.verify_only)
    print(json.dumps(report,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
