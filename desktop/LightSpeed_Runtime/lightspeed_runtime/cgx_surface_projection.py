"""Backend-derived UniSpace capability projection and bounded CGX review batching.

No new store, worker, authority, execution lane, signer or mint is created.
Uses the existing capability registry, role manifests and ternary composition.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

from lightspeed_runtime.cgx_capability_registry import (
    CapabilityRegistryError,
    _capability_review_snapshot,
    compose_capability_review,
)

SCHEMA = "CGX-UNISPACE-DYNAMIC-SURFACE/0.1"
BATCH_SCHEMA = "CGX-TEMPORARY-SUBAGENT-BATCH-REVIEW/0.1"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


def build_unispace_surface_manifest(selector: str = "LightSpeed") -> dict[str, Any]:
    """Derive the read-only UI surface from canonical selector/role metadata."""
    view, values = _capability_review_snapshot(selector)
    routes = []
    roles = []
    for reference in sorted(view["references"]):
        item = values[reference]
        if reference.startswith("route:"):
            routes.append({
                "id": item["route_id"],
                "state": item["state"],
                "kind": item.get("kind", "unknown"),
                "read_only": bool(item.get("ro", True)),
                "needs_review": item["state"] != "available" or not item.get("ro", True),
                "gate": str(item.get("gate") or item.get("limitation") or "")[:320],
                "execution_enabled": False,
            })
        elif reference.startswith("role:"):
            roles.append({
                "id": item["role_id"],
                "floor": item["floor"],
                "responsibility": item["responsibility"][:512],
                "execution_enabled": False,
            })
    return {
        "schema": SCHEMA,
        "selector": view["selector"],
        "source_view_sha256": view["view_sha256"],
        "route_count": len(routes),
        "routes": routes,
        "roles": roles,
        "role_source_holds": view["role_source_holds"],
        "projection": "read_only_backend_generated",
        "ternary_encoding": "existing_review_pack_nested_review_payload",
        "t173_admission": "unverified",
        "t174_zero": "reserved_nonmintable_sentinel",
        "temporary_persistence": "review_candidate_only",
        "native_mint_authorized": False,
        "execution_authorized": False,
        "source_hydration_authorized": False,
        "authority_transfer": False,
    }


def plan_temporary_subagent_batch(
    *, selector: str, task_id: str, run_id: str,
    expected_view_sha256: str, role_ids: list[str], route_ids: list[str],
    cpu_threads: int = 1, memory_mib: int = 256,
    max_jobs: int = 4, ttl_seconds: int = 900,
) -> dict[str, Any]:
    """Plan one temporary, scope-bound worker composition; never execute or persist.

    Task/run IDs must be allocated by the existing host. The TTL and resource
    envelope are review requirements, NOT enforced reservations or leases.
    """
    if any(type(x) is not str or not _ID.fullmatch(x) for x in (task_id, run_id)):
        raise CapabilityRegistryError("existing task_id and run_id are required")
    if not (type(expected_view_sha256) is str and
            re.fullmatch(r"[0-9a-f]{64}", expected_view_sha256)):
        raise CapabilityRegistryError("exact current surface revision required")
    if (type(role_ids) is not list or not 1 <= len(role_ids) <= 4 or
            any(type(x) is not str or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", x) for x in role_ids)
            or len(set(role_ids)) != len(role_ids)):
        raise CapabilityRegistryError("1..4 distinct registered role IDs required")
    if (type(route_ids) is not list or not 1 <= len(route_ids) <= 12 or
            any(type(x) is not str or not re.fullmatch(r"[a-z][a-z0-9_.-]{0,127}", x) for x in route_ids)
            or len(set(route_ids)) != len(route_ids)):
        raise CapabilityRegistryError("1..12 distinct registered route IDs required")
    cpu_ceiling = min(4, os.cpu_count() or 1)
    if (type(cpu_threads) is not int or not 1 <= cpu_threads <= cpu_ceiling
            or type(memory_mib) is not int or not 64 <= memory_mib <= 1024
            or type(max_jobs) is not int or not 1 <= max_jobs <= 16
            or type(ttl_seconds) is not int or not 60 <= ttl_seconds <= 3600):
        raise CapabilityRegistryError("bounded CPU/RAM/jobs/TTL envelope required")

    view, values = _capability_review_snapshot(selector)
    if view["view_sha256"] != expected_view_sha256:
        raise CapabilityRegistryError("stale surface revision")
    references = ["role:" + r for r in role_ids] + ["route:" + r for r in route_ids]
    if any(ref not in view["references"] for ref in references):
        raise CapabilityRegistryError("scope has no such registered role or route")
    states = {rid: values["route:" + rid]["state"] for rid in route_ids}
    if any(state == "missing" for state in states.values()):
        raise CapabilityRegistryError("missing route cannot be staged")
    composition = compose_capability_review(
        selector, task_id=task_id, expected_view_sha256=expected_view_sha256,
        references=references,
    )
    envelope = {
        "schema": BATCH_SCHEMA,
        "task_id": task_id,
        "run_id": run_id,
        "selector": view["selector"],
        "composition_sha256": composition["composition_sha256"],
        "composition_ternary_root": composition["composition_ternary_root"],
        "role_ids": sorted(role_ids),
        "route_states": dict(sorted(states.items())),
        "resource_envelope": {
            "cpu_threads_ceiling": cpu_threads,
            "memory_mib_ceiling": memory_mib,
            "max_jobs": max_jobs,
            "ttl_seconds": ttl_seconds,
            "enforcement_state": "NOT_ACTIVATED",
        },
        "persistence": "temporary_candidate_not_written",
        "binary_bridge": "sha256_identity_not_native_t173_encoding",
        "t174_zero": "reserved_nonmintable_sentinel",
        "lease_verified": False,
        "source_acl_verified": False,
        "training_performed": False,
        "execution_performed": False,
        "native_mint_authorized": False,
        "db_mutated": False,
        "authority_transfer": False,
    }
    raw = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return {**envelope, "candidate_sha256": hashlib.sha256(raw).hexdigest()}
