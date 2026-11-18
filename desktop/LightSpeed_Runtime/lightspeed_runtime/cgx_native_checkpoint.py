"""Canonical-database temporary Cognigrex checkpoint review.

Stores only task/run-bound *metadata* in existing operational_events.
No source bytes, role-label permissions, standalone family.sqlite3, worker,
model-weight training, lease issue, CGX mint or external transfer.
The caller MUST supply current owner-session verification; no CLI writer.
"""
from __future__ import annotations

import hashlib
import json
import re
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from lightspeed_runtime.operational_store import (
    OperationalStore, OperationalConflict, default_operational_db_path,
)
from lightspeed_runtime.cgx_surface_projection import BATCH_SCHEMA

SCHEMA = "CGX-CANONICAL-TEMPORARY-CHECKPOINT/0.1"
KIND = "cgx_temporary_checkpoint_review_v1"
REVOKE_KIND = "cgx_temporary_checkpoint_revoke_v1"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")


class NativeCheckpointError(ValueError):
    pass


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def _key(task_id: str, run_id: str) -> str:
    if any(type(x) is not str or not _ID.fullmatch(x) for x in (task_id, run_id)):
        raise NativeCheckpointError("valid host task and run identities required")
    return hashlib.sha256((task_id + "\0" + run_id).encode()).hexdigest()


def _event_id(task_id: str, run_id: str, revoke: bool = False) -> str:
    prefix = "cgx-temp-revoke:" if revoke else "cgx-temp-checkpoint:"
    return prefix + _key(task_id, run_id)


def _candidate_record(candidate: dict) -> dict:
    if type(candidate) is not dict or candidate.get("schema") != BATCH_SCHEMA:
        raise NativeCheckpointError("backend-derived candidate required")
    claimed = candidate.get("candidate_sha256")
    raw_candidate = {k: v for k, v in candidate.items() if k != "candidate_sha256"}
    if type(claimed) is not str or not _SHA.fullmatch(claimed) or (
        hashlib.sha256(_canonical(raw_candidate)).hexdigest() != claimed
    ):
        raise NativeCheckpointError("candidate identity changed")
    if any(candidate.get(key) is not False for key in (
        "lease_verified", "source_acl_verified", "training_performed",
        "execution_performed", "native_mint_authorized", "db_mutated",
        "authority_transfer",
    )):
        raise NativeCheckpointError("candidate attempts authority transfer")
    resource = candidate.get("resource_envelope")
    if (type(resource) is not dict or resource.get("enforcement_state") != "NOT_ACTIVATED"
            or any(type(resource.get(key)) is not int for key in (
                "cpu_threads_ceiling", "memory_mib_ceiling", "max_jobs", "ttl_seconds"))
            or not 1 <= resource["cpu_threads_ceiling"] <= 4
            or not 64 <= resource["memory_mib_ceiling"] <= 1024
            or not 1 <= resource["max_jobs"] <= 16
            or not 60 <= resource["ttl_seconds"] <= 3600):
        raise NativeCheckpointError("unreviewed resource envelope")
    for key in ("composition_sha256", "composition_ternary_root"):
        if type(candidate.get(key)) is not str or not _SHA.fullmatch(candidate[key]):
            raise NativeCheckpointError("composition identity missing")
    if type(candidate.get("role_ids")) is not list or type(candidate.get("route_states")) is not dict:
        raise NativeCheckpointError("role or route scope invalid")
    if any(state != "available" for state in candidate["route_states"].values()):
        raise NativeCheckpointError("gated or missing route cannot be made persistent")
    # Intentionally no source excerpt, model weight, credential, path, or arbitrary caller payload.
    return {
        "schema": SCHEMA,
        "task_id": candidate["task_id"],
        "run_id": candidate["run_id"],
        "selector": candidate["selector"],
        "candidate_sha256": claimed,
        "composition_sha256": candidate["composition_sha256"],
        "composition_ternary_root": candidate["composition_ternary_root"],
        "role_ids": candidate["role_ids"],
        "route_ids": sorted(candidate["route_states"]),
        "resource_limits": {
            "cpu_threads": resource["cpu_threads_ceiling"],
            "memory_mib": resource["memory_mib_ceiling"],
            "max_jobs": resource["max_jobs"],
            "ttl_seconds": resource["ttl_seconds"],
        },
        "source_view_sha256": None,  # Supplied candidate hash includes the source revision.
        "execution_enabled": False,
        "source_content_granted": False,
        "native_mint_authorized": False,
        "data_space_network_identity": None,
    }


def _verify(verify_owner: Callable[[], str], expected_actor: str | None = None) -> str:
    if not callable(verify_owner):
        raise PermissionError("verified owner-session callback required")
    actor = verify_owner()
    if type(actor) is not str or not actor or (
        expected_actor is not None and actor != expected_actor
    ):
        raise PermissionError("authenticated owner scope changed")
    return actor


def _row(store: OperationalStore, event_id: str) -> dict | None:
    # Bounded indexed lookup through the existing OperationalStore connection.
    with closing(store._connect()) as db:
        row = db.execute(
            "SELECT event_id,kind,payload_json,payload_sha256,created_utc "
            "FROM operational_events WHERE event_id = ?", (event_id,),
        ).fetchone()
    return dict(row) if row else None


def _verify_row(row: dict, expected_kind: str) -> dict:
    if row["kind"] != expected_kind:
        raise NativeCheckpointError("unexpected operational event kind")
    raw = row["payload_json"]
    if hashlib.sha256(raw.encode("utf-8")).hexdigest() != row["payload_sha256"]:
        raise NativeCheckpointError("canonical event integrity mismatch")
    event = json.loads(raw)
    if event.get("event_id") != row["event_id"] or event.get("kind") != expected_kind:
        raise NativeCheckpointError("canonical event identity mismatch")
    return event


def _host_store(root: Path) -> OperationalStore:
    path = default_operational_db_path(root)
    if not path.is_file() or path.is_symlink():
        raise NativeCheckpointError("canonical operational database unavailable")
    # Prevent implicit migration/creation via OperationalStore.__init__.
    import sqlite3
    try:
        with closing(sqlite3.connect("file:" + str(path) + "?mode=ro", uri=True,
                                     timeout=2)) as db:
            tables = {row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('operational_events','operational_routes')"
            ).fetchall()}
    except sqlite3.Error as exc:
        raise NativeCheckpointError("canonical schema probe unavailable") from exc
    if tables != {"operational_events", "operational_routes"}:
        raise NativeCheckpointError("canonical operational schema not admitted")
    return OperationalStore(path)


def host_checkpoint_store(root: Path) -> OperationalStore:
    """Only use through the verified host owner-session route."""
    return _host_store(Path(root).absolute())


def persist_checkpoint(
    store: OperationalStore, candidate: dict, *, verify_owner: Callable[[], str],
    now: datetime | None = None,
) -> dict[str, Any]:
    actor = _verify(verify_owner)
    meta = _candidate_record(candidate)
    checkpoint_id = _event_id(meta["task_id"], meta["run_id"])
    event = {
        "event_id": checkpoint_id,
        "kind": KIND,
        "source": "UniSpace",
        "target": "Cognigrex",
        "priority": "normal",
        "risk": "low",
        "status": "REVIEW_ONLY",
        "checkpoint": meta,
    }
    if _row(store, _event_id(meta["task_id"], meta["run_id"], revoke=True)):
        raise NativeCheckpointError("revoked run cannot be reactivated")
    try:
        result = store.record_event(event)
    except OperationalConflict as exc:
        raise NativeCheckpointError("run identity already binds different content") from exc
    _verify(verify_owner, actor)
    readback = read_checkpoint(store, meta["task_id"], meta["run_id"],
                               verify_owner=verify_owner, now=now)
    if readback["candidate_sha256"] != meta["candidate_sha256"]:
        raise NativeCheckpointError("persistence readback does not match candidate")
    return {**readback, "inserted": result["inserted"]}


def read_checkpoint(
    store: OperationalStore, task_id: str, run_id: str, *,
    verify_owner: Callable[[], str], now: datetime | None = None,
) -> dict[str, Any]:
    actor = _verify(verify_owner)
    event_id = _event_id(task_id, run_id)
    row = _row(store, event_id)
    if row is None:
        raise NativeCheckpointError("checkpoint not found")
    event = _verify_row(row, KIND)
    meta = event.get("checkpoint")
    if type(meta) is not dict or (
        meta.get("task_id") != task_id or meta.get("run_id") != run_id
    ):
        raise NativeCheckpointError("stored checkpoint scope mismatch")
    claimed = meta["candidate_sha256"]
    if type(claimed) is not str or not _SHA.fullmatch(claimed):
        raise NativeCheckpointError("stored candidate identity malformed")
    created = datetime.fromisoformat(row["created_utc"].replace("Z", "+00:00"))
    current = now or datetime.now(UTC)
    if created.tzinfo is None or current.tzinfo is None:
        raise NativeCheckpointError("timezone-aware clock required")
    duration = meta["resource_limits"]["ttl_seconds"]
    expires = created + timedelta(seconds=duration)
    revoked_row = _row(store, _event_id(task_id, run_id, revoke=True))
    if revoked_row:
        revoked = _verify_row(revoked_row, REVOKE_KIND)
        if revoked.get("candidate_sha256") != claimed:
            raise NativeCheckpointError("revocation chain mismatch")
    state = "REVOKED" if revoked_row else "EXPIRED" if current >= expires else "REVIEW_ONLY"
    _verify(verify_owner, actor)
    return {
        "schema": SCHEMA,
        "task_id": task_id,
        "run_id": run_id,
        "candidate_sha256": claimed,
        "composition_ternary_root": meta["composition_ternary_root"],
        "event_sha256": row["payload_sha256"],
        "created_utc": created.isoformat(),
        "expires_utc": expires.isoformat(),
        "state": state,
        "native_metadata_persisted": True,
        "exact_readback_verified": True,
        "execution_enabled": False,
        "source_content_granted": False,
        "lease_verified": False,
        "native_mint_authorized": False,
        "network_identity_issued": False,
    }


def revoke_checkpoint(
    store: OperationalStore, task_id: str, run_id: str, *,
    expected_candidate_sha256: str, verify_owner: Callable[[], str],
) -> dict[str, Any]:
    actor = _verify(verify_owner)
    current = read_checkpoint(store, task_id, run_id, verify_owner=verify_owner)
    if current["candidate_sha256"] != expected_candidate_sha256:
        raise NativeCheckpointError("candidate revision changed")
    event = {
        "event_id": _event_id(task_id, run_id, revoke=True),
        "kind": REVOKE_KIND,
        "source": "UniSpace",
        "target": "Cognigrex",
        "priority": "normal",
        "risk": "low",
        "status": "REVOKED",
        "candidate_sha256": expected_candidate_sha256,
    }
    store.record_event(event)
    _verify(verify_owner, actor)
    return read_checkpoint(store, task_id, run_id, verify_owner=verify_owner)
