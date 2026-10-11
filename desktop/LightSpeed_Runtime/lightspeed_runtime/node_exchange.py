from __future__ import annotations

"""Content-addressed transfer and leased-compute helpers for the existing LightSpeed runtime.

This module is not a transport server and does not create a second runtime.
Network/peer adapters must call these bounded contracts and return receipts.
"""

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, Callable, Iterable
import uuid

TRANSFER_SCHEMA = "cgx-node-transfer-envelope-v1"
TRANSFER_RECEIPT_SCHEMA = "cgx-node-transfer-receipt-v1"
COMPUTE_SCHEMA = "cgx-node-compute-request-v1"
COMPUTE_RECEIPT_SCHEMA = "cgx-node-compute-receipt-v1"
STATUS_SCHEMA = "cgx-node-exchange-status-v1"
ROOT_REGISTRY_SCHEMA = "cgx-node-root-registry-v1"
_ALLOWED_LEASE_CLASSES = {
    "COMPUTE_ONLY",
    "DIGITAL_WRITE",
    "EXTERNAL_ACTION",
    "PHYSICAL_ACTUATION",
}
_WRITE_LEASE_CLASSES = {
    "DIGITAL_WRITE",
    "EXTERNAL_ACTION",
    "PHYSICAL_ACTUATION",
}


class NodeExchangeError(ValueError):
    """Raised when a node exchange envelope violates a bounded contract."""


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _bounded(value: Any, maximum: int, *, required: bool = False) -> str:
    text = " ".join(str(value or "").split()).strip()[:maximum]
    if required and not text:
        raise NodeExchangeError("required node-exchange field is missing")
    return text


def _canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _within(path: Path, roots: Iterable[Path | str], *, label: str) -> Path:
    resolved = path.resolve(strict=True)
    allowed = [Path(root).resolve(strict=True) for root in roots]
    if not allowed:
        raise NodeExchangeError(f"{label} allowlist is empty")
    for root in allowed:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    raise NodeExchangeError(f"{label} is outside approved roots: {resolved}")


def _target_path(target_root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise NodeExchangeError("target_relative_path must be a bounded relative path")
    root = target_root.resolve(strict=True)
    candidate = (root / rel).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise NodeExchangeError("target path escapes approved root") from exc
    return candidate


def load_node_root_registry(path: Path | str) -> dict[str, Any]:
    registry_path = Path(path)
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NodeExchangeError(f"node root registry unavailable: {registry_path}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != ROOT_REGISTRY_SCHEMA:
        raise NodeExchangeError("node root registry schema is invalid")
    node_id = _bounded(payload.get("node_id"), 96, required=True)
    roots = payload.get("roots")
    if not isinstance(roots, list) or len(roots) > 128:
        raise NodeExchangeError("node root registry roots must be a bounded list")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in roots:
        if not isinstance(row, dict):
            raise NodeExchangeError("node root registry entry must be an object")
        root_id = _bounded(row.get("root_id"), 96, required=True)
        if root_id in seen:
            raise NodeExchangeError(f"duplicate node root id: {root_id}")
        access = str(row.get("access") or "").strip()
        if access not in {"read", "read_write"}:
            raise NodeExchangeError(f"invalid node root access: {root_id}")
        raw_path = Path(_bounded(row.get("path"), 1000, required=True))
        if not raw_path.is_absolute():
            raise NodeExchangeError(f"node root path must be absolute: {root_id}")
        resolved = raw_path.resolve(strict=True)
        if not resolved.is_dir():
            raise NodeExchangeError(f"node root path is not a directory: {root_id}")
        normalized.append(
            {
                "root_id": root_id,
                "path": str(resolved),
                "access": access,
                "kind": _bounded(row.get("kind") or "local", 64),
            }
        )
        seen.add(root_id)
    return {
        "schema_version": ROOT_REGISTRY_SCHEMA,
        "node_id": node_id,
        "roots": normalized,
        "source_ref": str(registry_path.resolve(strict=True)),
    }


def resolve_node_root(
    registry: dict[str, Any],
    *,
    node_id: str,
    root_id: str,
    require_write: bool = False,
) -> Path:
    if registry.get("schema_version") != ROOT_REGISTRY_SCHEMA:
        raise NodeExchangeError("node root registry schema is invalid")
    if str(registry.get("node_id") or "") != str(node_id):
        raise NodeExchangeError("node root registry does not belong to requested node")
    for row in registry.get("roots") or []:
        if not isinstance(row, dict) or row.get("root_id") != root_id:
            continue
        if require_write and row.get("access") != "read_write":
            raise NodeExchangeError(f"node root is not write-enabled: {root_id}")
        return Path(str(row["path"])).resolve(strict=True)
    raise NodeExchangeError(f"node root is not registered: {root_id}")


def build_transfer_envelope_from_manifest(
    *,
    source_ref: str,
    source_sha256: str,
    size_bytes: int,
    file_name: str,
    source_node_id: str,
    target_node_id: str,
    source_root_id: str,
    target_root_id: str,
    object_id: str | None = None,
    transfer_id: str | None = None,
    max_bytes: int = 512 * 1024 * 1024,
) -> dict[str, Any]:
    digest = str(source_sha256 or "").strip().lower()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise NodeExchangeError("source_sha256 must be a lowercase/uppercase 64-character hex digest")
    size = int(size_bytes)
    if size < 0 or size > int(max_bytes):
        raise NodeExchangeError("transfer source exceeds bounded size")
    safe_name = Path(_bounded(file_name, 255, required=True)).name
    if safe_name in {"", ".", ".."}:
        raise NodeExchangeError("transfer file_name is invalid")
    tid = transfer_id or f"NXFER-{digest[:16]}-{uuid.uuid4().hex[:8]}"
    relative = Path("transfers") / digest / safe_name
    return {
        "schema_version": TRANSFER_SCHEMA,
        "transfer_id": _bounded(tid, 96, required=True),
        "created_utc": utc_now_iso(),
        "state": "planned",
        "source_node_id": _bounded(source_node_id, 96, required=True),
        "target_node_id": _bounded(target_node_id, 96, required=True),
        "source_root_id": _bounded(source_root_id, 96, required=True),
        "target_root_id": _bounded(target_root_id, 96, required=True),
        "source_ref": _bounded(source_ref, 1000, required=True),
        "source_sha256": digest,
        "size_bytes": size,
        "object_id": _bounded(object_id, 160) if object_id else None,
        "target_relative_path": relative.as_posix(),
        "authority_transfer": False,
        "canonical_promotion_authorized": False,
        "public_publish_authorized": False,
    }


def build_transfer_envelope(
    source_path: Path | str,
    *,
    source_node_id: str,
    target_node_id: str,
    source_root_id: str,
    target_root_id: str,
    object_id: str | None = None,
    transfer_id: str | None = None,
    max_bytes: int = 512 * 1024 * 1024,
) -> dict[str, Any]:
    source = Path(source_path)
    if not source.is_file():
        raise NodeExchangeError("transfer source must be a file")
    size = source.stat().st_size
    if size < 0 or size > int(max_bytes):
        raise NodeExchangeError("transfer source exceeds bounded size")
    digest = sha256_file(source)
    tid = transfer_id or f"NXFER-{digest[:16]}-{uuid.uuid4().hex[:8]}"
    relative = Path("transfers") / digest / source.name
    return {
        "schema_version": TRANSFER_SCHEMA,
        "transfer_id": _bounded(tid, 96, required=True),
        "created_utc": utc_now_iso(),
        "state": "planned",
        "source_node_id": _bounded(source_node_id, 96, required=True),
        "target_node_id": _bounded(target_node_id, 96, required=True),
        "source_root_id": _bounded(source_root_id, 96, required=True),
        "target_root_id": _bounded(target_root_id, 96, required=True),
        "source_ref": str(source.absolute()),
        "source_sha256": digest,
        "size_bytes": size,
        "object_id": _bounded(object_id, 160) if object_id else None,
        "target_relative_path": relative.as_posix(),
        "authority_transfer": False,
        "canonical_promotion_authorized": False,
        "public_publish_authorized": False,
    }


def execute_local_transfer(
    envelope: dict[str, Any],
    *,
    target_root: Path | str,
    allowed_source_roots: Iterable[Path | str],
    allowed_target_roots: Iterable[Path | str],
    lease_validation: dict[str, Any],
) -> dict[str, Any]:
    if envelope.get("schema_version") != TRANSFER_SCHEMA:
        raise NodeExchangeError("unsupported transfer envelope schema")
    if lease_validation.get("valid") is not True:
        raise NodeExchangeError("current scoped DIGITAL_WRITE lease did not validate")
    if str(lease_validation.get("lease_class") or "") not in _WRITE_LEASE_CLASSES:
        raise NodeExchangeError("validated lease class does not permit digital transfer")
    bound_lease = envelope.get("lease_ref")
    if bound_lease and str(lease_validation.get("lease_id") or "") != str(bound_lease):
        raise NodeExchangeError("transfer envelope lease_ref does not match validated lease")
    source = _within(Path(str(envelope.get("source_ref") or "")), allowed_source_roots, label="source")
    root = _within(Path(target_root), allowed_target_roots, label="target root")
    destination = _target_path(root, str(envelope.get("target_relative_path") or ""))
    source_hash = sha256_file(source)
    source_size = source.stat().st_size
    if source_hash != envelope.get("source_sha256") or source_size != int(envelope.get("size_bytes") or -1):
        raise NodeExchangeError("source changed after transfer envelope was created")

    reused = False
    if destination.exists():
        if not destination.is_file():
            raise NodeExchangeError("transfer target exists and is not a file")
        if destination.stat().st_size != source_size or sha256_file(destination) != source_hash:
            raise NodeExchangeError("non-identical transfer target already exists")
        reused = True
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.tmp.{os.getpid()}")
        try:
            shutil.copyfile(source, temporary)
            if temporary.stat().st_size != source_size or sha256_file(temporary) != source_hash:
                raise NodeExchangeError("target staging readback failed")
            os.replace(temporary, destination)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    target_hash = sha256_file(destination)
    exact = target_hash == source_hash and destination.stat().st_size == source_size
    if not exact:
        raise NodeExchangeError("target readback failed")
    return {
        "schema_version": TRANSFER_RECEIPT_SCHEMA,
        "transfer_id": envelope["transfer_id"],
        "completed_utc": utc_now_iso(),
        "state": "verified",
        "source_node_id": envelope["source_node_id"],
        "target_node_id": envelope["target_node_id"],
        "source_sha256": source_hash,
        "received_sha256": target_hash,
        "size_bytes": source_size,
        "exact_readback": True,
        "reused_existing_payload": reused,
        "target_ref": str(destination),
        "authority_transfer": False,
        "canonical_promotion_authorized": False,
        "public_publish_authorized": False,
    }
def build_compute_request(
    instruction: str,
    *,
    task_id: str,
    run_id: str,
    target_node_id: str,
    capability_id: str,
    lease_ref: str,
    input_receipts: Iterable[dict[str, Any]] = (),
    project_id: str | None = None,
    resource_budget: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bounded_instruction = _bounded(instruction, 8000, required=True)
    receipts = [dict(row) for row in input_receipts if isinstance(row, dict)]
    manifest = [
        {
            "transfer_id": row.get("transfer_id"),
            "source_sha256": row.get("source_sha256"),
            "received_sha256": row.get("received_sha256"),
            "size_bytes": row.get("size_bytes"),
            "exact_readback": row.get("exact_readback"),
            "state": row.get("state"),
        }
        for row in receipts
    ]
    budget = {
        "max_wall_seconds": 300,
        "max_memory_mb": 8192,
        "max_input_bytes": 512 * 1024 * 1024,
        "allow_heavy": False,
        **(resource_budget or {}),
    }
    if budget.get("allow_heavy") is not False:
        raise NodeExchangeError("node compute v1 does not permit heavy execution")
    return {
        "schema_version": COMPUTE_SCHEMA,
        "request_id": f"NCOMP-{uuid.uuid4().hex[:16]}",
        "created_utc": utc_now_iso(),
        "task_id": _bounded(task_id, 128, required=True),
        "run_id": _bounded(run_id, 128, required=True),
        "project_id": _bounded(project_id, 128) if project_id else None,
        "target_node_id": _bounded(target_node_id, 96, required=True),
        "capability_id": _bounded(capability_id, 160, required=True),
        "instruction": bounded_instruction,
        "instruction_sha256": hashlib.sha256(bounded_instruction.encode("utf-8")).hexdigest(),
        "input_manifest_sha256": _canonical_json_sha256(manifest),
        "input_receipts": receipts,
        "lease_ref": _bounded(lease_ref, 200, required=True),
        "resource_budget": budget,
        "authority_transfer": False,
    }
def _assert_compute_inputs_verified(request: dict[str, Any]) -> None:
    for row in request.get("input_receipts") or []:
        if not isinstance(row, dict):
            raise NodeExchangeError("compute input receipt must be an object")
        if row.get("state") != "verified" or row.get("exact_readback") is not True:
            raise NodeExchangeError("compute input is not backed by verified target readback")
        if row.get("source_sha256") != row.get("received_sha256"):
            raise NodeExchangeError("compute input hash mismatch")


def execute_local_compute(
    request: dict[str, Any],
    *,
    local_node_id: str,
    lease_validation: dict[str, Any],
    runner: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    if request.get("schema_version") != COMPUTE_SCHEMA:
        raise NodeExchangeError("unsupported compute request schema")
    if str(request.get("target_node_id") or "") != str(local_node_id):
        raise NodeExchangeError("target is not the local compute node")
    if lease_validation.get("valid") is not True:
        raise NodeExchangeError("current scoped execution lease did not validate")
    if str(lease_validation.get("lease_id") or "") != str(request.get("lease_ref") or ""):
        raise NodeExchangeError("compute request lease_ref does not match validated lease")
    if str(lease_validation.get("lease_class") or "") not in _ALLOWED_LEASE_CLASSES:
        raise NodeExchangeError("validated lease class does not permit compute")
    _assert_compute_inputs_verified(request)

    workflow = runner(
        str(request["instruction"]),
        task_id=str(request["task_id"]),
        project_id=str(request.get("project_id") or "NODE-EXCHANGE"),
        dry_run=False,
        allow_heavy=False,
        receipt_target="neo",
        stop_on_failure=True,
    )
    if not isinstance(workflow, dict):
        raise NodeExchangeError("compute runner returned an invalid result")
    complete = bool(workflow.get("complete_workflow")) and workflow.get("status") == "complete"
    return {
        "schema_version": COMPUTE_RECEIPT_SCHEMA,
        "request_id": request["request_id"],
        "completed_utc": utc_now_iso(),
        "task_id": request["task_id"],
        "run_id": request["run_id"],
        "node_id": local_node_id,
        "capability_id": request["capability_id"],
        "lease_ref": request["lease_ref"],
        "instruction_sha256": request["instruction_sha256"],
        "input_manifest_sha256": request["input_manifest_sha256"],
        "status": "complete" if complete else "blocked",
        "workflow_receipt": workflow,
        "raw_instruction_persisted_in_receipt": False,
        "authority_transfer": False,
        "canonical_promotion_authorized": False,
        "public_publish_authorized": False,
    }


def build_exchange_status(
    *,
    local_node_id: str,
    local_compute_ready: bool,
    verified_carriers: Iterable[str] = (),
    peer_nodes: Iterable[str] = (),
    host_root_registry_ready: bool = False,
) -> dict[str, Any]:
    peers = [str(item) for item in peer_nodes if str(item).strip()]
    carriers = [str(item) for item in verified_carriers if str(item).strip()]
    return {
        "schema_version": STATUS_SCHEMA,
        "node_id": _bounded(local_node_id, 96, required=True),
        "transport": {
            "mode": "content_addressed_verified_readback",
            "verified_carriers": carriers,
            "peer_transport_verified": bool(peers),
        },
        "compute": {
            "local_ready": bool(local_compute_ready),
            "peer_nodes": peers,
            "peer_compute_verified": bool(peers),
            "lease_required": True,
            "heavy_execution_default": False,
        },
        "activation": {
            "host_root_registry_ready": bool(host_root_registry_ready),
            "typed_transfer_queue_ready": bool(host_root_registry_ready),
            "peer_compute_queue_ready": bool(host_root_registry_ready and peers),
        },
        "claim_boundary": (
            "Mounted carrier readback and local compute are distinct proofs; "
            "peer compute remains unproven until an independently connected compute node returns a receipted result."
        ),
        "authority_transfer": False,
        "canonical_promotion_authorized": False,
    }


__all__ = [
    "COMPUTE_RECEIPT_SCHEMA",
    "COMPUTE_SCHEMA",
    "NodeExchangeError",
    "ROOT_REGISTRY_SCHEMA",
    "STATUS_SCHEMA",
    "TRANSFER_RECEIPT_SCHEMA",
    "TRANSFER_SCHEMA",
    "build_compute_request",
    "build_exchange_status",
    "build_transfer_envelope",
    "load_node_root_registry",
    "resolve_node_root",
    "build_transfer_envelope_from_manifest",
    "execute_local_compute",
    "execute_local_transfer",
    "sha256_file",
]


# Optional read-only Psi-DataSpace observation facet; not a transport or a new runtime.
ROLLING_OBSERVER_FACET = "cgx-node-exchange-rolling-observer-facet-v1"
ROLLING_OBSERVER_LENSES = (
    "state", "transition", "persistence", "stability", "activity",
    "oscillation", "spatial_corroboration", "evidence_quality", "release_projection",
)


def project_rolling_observer_window(
    *, object_id: str, geometry_root: str, semantic_root: str, model_root: str,
    prior_state_root: str, selected_nodes: list[str],
    samples: list[dict], end_ms: int,
    phase_slots: tuple[int, ...] = (0, 1, 3, 4, 6, 7, 9, 10, 11),
) -> dict:
    """Project nine non-authoritative lenses from a bounded 60-second observation window.

    Caller must obtain sensor states from authenticated/calibrated receipt adapters.
    Receipt markers are prerequisites, never cryptographic verification by this
    function. Three agreeing origins do not prove physical independence.
    Missing samples are unknown, not zero and not an unchanged state.
    """
    if not isinstance(object_id, str) or not object_id.strip() or len(object_id) > 160:
        raise NodeExchangeError("rolling observer requires bounded object_id")
    roots = (geometry_root, semantic_root, model_root, prior_state_root)
    if any(not isinstance(r, str) or len(r) != 64 or any(c not in "0123456789abcdef" for c in r) for r in roots):
        raise NodeExchangeError("rolling observer requires lowercase SHA-256 context roots")
    if (not isinstance(selected_nodes, list) or not 3 <= len(selected_nodes) <= 16 or
            any(not isinstance(n, str) or not n.strip() or len(n) > 96 for n in selected_nodes) or
            len(selected_nodes) != len(set(selected_nodes))):
        raise NodeExchangeError("selected observer roster must contain 3..16 unique bounded nodes")
    if (not isinstance(phase_slots, tuple) or len(phase_slots) != 9 or
            len(set(phase_slots)) != 9 or
            any(type(s) is not int or s < 0 or s >= 12 for s in phase_slots)):
        raise NodeExchangeError("nine distinct five-second phase slots required")
    if type(end_ms) is not int or end_ms < 60000 or end_ms % 1000:
        raise NodeExchangeError("end_ms requires aligned one-second grid and complete window")
    if not isinstance(samples, list) or len(samples) > 4096:
        raise NodeExchangeError("rolling window sample list exceeds bounded size")
    start_ms = end_ms - 60000
    node_set = set(selected_nodes)
    by_time = {}
    seen = set()
    for row in samples:
        if not isinstance(row, dict):
            raise NodeExchangeError("sample must be a record")
        node = row.get("observer_id")
        time = row.get("timestamp_ms")
        state = row.get("state")
        group = row.get("independence_group")
        if node not in node_set or type(time) is not int or not start_ms <= time <= end_ms or time % 1000:
            raise NodeExchangeError("sample node/time outside negotiated observer window")
        if state is not None and (type(state) is not int or state not in (-1, 0, 1)):
            raise NodeExchangeError("invalid ternary state; erasure must be null")
        if not isinstance(group, str) or not group.strip() or len(group) > 96:
            raise NodeExchangeError("sample needs a bounded provenance independence group")
        if row.get("receipt_verified") is not True:
            raise NodeExchangeError("sample lacks adapter-verified receipt")
        key = (node, time)
        if key in seen:
            raise NodeExchangeError("duplicate node/time sample")
        seen.add(key)
        by_time.setdefault(time, []).append((node, state, group))
    trajectory = []
    conflict_times = []
    agreeing = 0
    for t in range(start_ms, end_ms + 1, 1000):
        rows = by_time.get(t, [])
        known = [(n, s, g) for n, s, g in rows if s is not None]
        groups = [g for _, _, g in known]
        unique_groups = len(set(groups)) == len(groups)
        signs = {s for _, s, _ in known}
        if len(signs) > 1:
            conflict_times.append(t)
        quorum = len(known) >= 3 and unique_groups and len(signs) == 1
        value = next(iter(signs)) if quorum else None
        if quorum:
            agreeing += 1
        trajectory.append(value)
    changes, flips = 0, 0
    prev = None
    for state in trajectory:
        if state is None:
            prev = None
            continue
        if prev is not None and state != prev:
            changes += 1
            if state * prev == -1:
                flips += 1
        prev = state
    current = trajectory[-1]
    previous = trajectory[-2]
    persistence = 0
    if current is not None:
        for state in reversed(trajectory):
            if state != current:
                break
            persistence += 1
    known_states = [state for state in trajectory if state is not None]
    transition = ("UNKNOWN" if current is None or previous is None else
                  "SAME" if current == previous else f"{previous}->{current}")
    lens_values = {
        "state": current,
        "transition": transition,
        "persistence": {"samples": persistence, "minimum_ms": max(0, persistence - 1) * 1000},
        "stability": ("UNKNOWN" if len(known_states) < 2 or len(known_states) != len(trajectory)
                      else "STABLE" if len(set(known_states)) == 1 else "VARIED"),
        "activity": {"changes": changes},
        "oscillation": {"direct_sign_flips": flips},
        "spatial_corroboration": {
            "agreement_ticks": agreeing, "conflicts": len(conflict_times), "independence_validated": False,
        },
        "evidence_quality": {
            "observed_rows": len(samples), "resolved_ticks": len(known_states),
            "possible_ticks": 61, "unknown_ticks": 61 - len(known_states),
        },
        "release_projection": {"status": "WITHHELD", "publication_authorised": False},
    }
    if tuple(lens_values) != ROLLING_OBSERVER_LENSES:
        raise NodeExchangeError("lens ordering mismatch")
    slot = (end_ms % 60000) // 5000
    return {
        "schema_version": ROLLING_OBSERVER_FACET,
        "object_id": object_id,
        "geometry_root": geometry_root,
        "semantic_root": semantic_root,
        "model_root": model_root,
        "prior_state_root": prior_state_root,
        "selected_nodes": selected_nodes,
        "window_ms": 60000,
        "fast_step_ms": 1000,
        "slow_step_ms": 5000,
        "end_ms": end_ms,
        "phase_slots": list(phase_slots),
        "active_phase_index": phase_slots.index(slot) if slot in phase_slots else None,
        "sample_digest": _canonical_json_sha256(samples),
        "lenses": lens_values,
        "trajectory": trajectory,  # Local-only projection; not a transport wire frame.
        "epistemic_status": "OBSERVATIONAL_CANDIDATE",
        "cryptographically_authenticated_by_this_function": False,
        "authority_transfer": False,
        "canonical_promotion_authorized": False,
        "public_publish_authorized": False,
        "physical_actuation_authorized": False,
    }


__all__.extend((
    "ROLLING_OBSERVER_FACET",
    "ROLLING_OBSERVER_LENSES",
    "project_rolling_observer_window",
))


# Configurable N-node DataSpace profiles are read-only projections of existing CGX.
DATASPACE_PROFILE_FACET = "cgx-dataspace-config-facet-v1"
DATASPACE_DELTA_FACET = "cgx-dataspace-compact-delta-candidate-v1"
_DATASPACE_VISIBILITY = {"public", "restricted", "private"}
_DATASPACE_KINDS = {"spatial", "temporal", "electrical", "electromagnetic", "acoustic", "logical"}
_DATASPACE_TRANSPORTS = {
    "offline", "wired", "ip", "wifi", "lpwan", "ambient_backscatter",
    "optical", "delay_tolerant",
}
_DATASPACE_RELATIONS = {"OBSERVES", "DEPENDS_ON", "INTERPRETS", "CORRELATES", "MEASURED_LINK"}


def _dataspace_sha256_root(value: object) -> str:
    return _canonical_json_sha256(value)


def _dataspace_check_root(value: object, label: str) -> None:
    if (not isinstance(value, str) or len(value) != 64 or
            any(ch not in "0123456789abcdef" for ch in value)):
        raise NodeExchangeError(f"{label} must be a lowercase SHA-256 root")


def _dataspace_index(rows: object, kind: str, minimum: int, maximum: int) -> dict:
    if not isinstance(rows, list) or not minimum <= len(rows) <= maximum:
        raise NodeExchangeError(f"DataSpace {kind} count outside supported bounds")
    indexed = {}
    for row in rows:
        if not isinstance(row, dict):
            raise NodeExchangeError(f"DataSpace {kind} item must be a record")
        ident = row.get("id")
        if (not isinstance(ident, str) or not ident or len(ident) > 96 or
                ident in indexed):
            raise NodeExchangeError(f"DataSpace {kind} identifiers must be unique and bounded")
        indexed[ident] = row
    return indexed


def validate_dataspace_profile(profile: dict) -> dict:
    """Validate one *local* CGX DataSpace profile, not access permission or RF rights.

    Profiles contain private node identifiers and MUST NOT be published, logged to
    public status, transmitted in cleartext or treated as encryption keys.
    """
    if not isinstance(profile, dict) or profile.get("schema_version") != DATASPACE_PROFILE_FACET:
        raise NodeExchangeError("unsupported DataSpace profile schema")
    if not isinstance(profile.get("object_id"), str) or not 1 <= len(profile["object_id"]) <= 160:
        raise NodeExchangeError("DataSpace profile requires bounded canonical Object_ID")
    for key in ("geometry_root", "semantic_root", "model_root", "state_root"):
        _dataspace_check_root(profile.get(key), key)
    nodes = _dataspace_index(profile.get("nodes"), "nodes", 1, 128)
    interfaces = _dataspace_index(profile.get("interfaces"), "interfaces", 0, 128)
    derivables = _dataspace_index(profile.get("derivables"), "derivables", 1, 128)
    relationships = _dataspace_index(profile.get("relationships"), "relationships", 0, 256)
    lenses = _dataspace_index(profile.get("semantic_lenses"), "semantic_lenses", 1, 64)
    transports = _dataspace_index(profile.get("transports"), "transports", 0, 16)
    chosen = profile.get("selection")
    if not isinstance(chosen, dict):
        raise NodeExchangeError("DataSpace profile requires node selection")
    includes, excludes = chosen.get("include"), chosen.get("exclude")
    if (not isinstance(includes, list) or not isinstance(excludes, list) or
            any(not isinstance(i, str) for i in includes + excludes) or
            len(set(includes)) != len(includes) or len(set(excludes)) != len(excludes) or
            set(includes) & set(excludes) or
            (set(includes) | set(excludes)) != set(nodes) or not includes):
        raise NodeExchangeError("DataSpace include/exclude nodes must form a disjoint complete partition")
    expected = profile.get("expected_counts")
    count_map = {
        "nodes": len(nodes), "selected_nodes": len(includes),
        "interfaces": len(interfaces), "derivables": len(derivables),
        "relationships": len(relationships), "semantic_lenses": len(lenses),
        "transports": len(transports),
    }
    if (not isinstance(expected, dict) or set(expected) != set(count_map) or
            any(type(expected[k]) is not int or expected[k] != count_map[k] for k in count_map)):
        raise NodeExchangeError("DataSpace declared counts must exactly match configured objects")
    for nid, row in nodes.items():
        if row.get("visibility") not in _DATASPACE_VISIBILITY:
            raise NodeExchangeError("node visibility invalid")
        if not isinstance(row.get("owner_ref"), str) or not row["owner_ref"]:
            raise NodeExchangeError("node owner reference required, even for public data")
        if nid in includes and (not isinstance(row.get("access_policy_ref"), str)
                                or not row["access_policy_ref"]):
            raise NodeExchangeError("selected nodes need an external access policy reference")
    for iid, row in interfaces.items():
        selected = row.get("nodes")
        if (row.get("kind") not in _DATASPACE_KINDS or
                not isinstance(selected, list) or not 1 <= len(selected) <= 16 or
                len(selected) != len(set(selected)) or any(n not in includes for n in selected) or
                not isinstance(row.get("model_ref"), str) or not row["model_ref"]):
            raise NodeExchangeError("interface geometry must reference authorised selected nodes and model")
    for did, row in derivables.items():
        inputs = row.get("inputs")
        if (not isinstance(inputs, list) or not inputs or
                len(inputs) > 32 or any(i not in interfaces for i in inputs) or
                not isinstance(row.get("function_ref"), str) or not row["function_ref"] or
                not isinstance(row.get("unit"), str) or not row["unit"]):
            raise NodeExchangeError("derivable requires registered function, unit and known interfaces")
    typed = ({f"node:{n}" for n in nodes} |
             {f"interface:{n}" for n in interfaces} |
             {f"derivable:{n}" for n in derivables})
    for row in relationships.values():
        if (row.get("kind") not in _DATASPACE_RELATIONS or
                row.get("source") not in typed or row.get("target") not in typed or
                row["source"] == row["target"] or
                not isinstance(row.get("evidence_ref"), str) or not row["evidence_ref"]):
            raise NodeExchangeError("relationship requires typed endpoints, category and evidence")
    for row in lenses.values():
        if (row.get("derivable_id") not in derivables or
                not isinstance(row.get("registered_view_ref"), str) or not row["registered_view_ref"]):
            raise NodeExchangeError("semantic lens must bind a derivable and an existing registered view")
    for row in transports.values():
        if row.get("kind") not in _DATASPACE_TRANSPORTS:
            raise NodeExchangeError("invalid transport kind")
        for key in ("throughput_bps", "spectral_bandwidth_hz"):
            v = row.get(key)
            if type(v) not in (int, float) or not 0 <= v <= 1000000000000 or v != v:
                raise NodeExchangeError("transport requires finite bounded throughput and spectral bandwidth")
        occupancy = row.get("observed_occupancy_fraction")
        if type(occupancy) not in (int, float) or not 0 <= occupancy <= 1:
            raise NodeExchangeError("transport occupancy must be in [0,1]")
        if row.get("transmit_permission") not in ("NOT_VERIFIED", "LISTEN_ONLY", "EXTERNALLY_QUALIFIED"):
            raise NodeExchangeError("transmit permission must be expressly classified")
        if (row["transmit_permission"] == "EXTERNALLY_QUALIFIED" and
                (not isinstance(row.get("licence_or_class_ref"), str) or
                 not row.get("licence_or_class_ref"))):
            raise NodeExchangeError("qualified transport needs external licensing evidence reference")
    cadence = profile.get("cadence")
    if (not isinstance(cadence, dict) or cadence.get("window_ms") != 60000 or
            cadence.get("sample_ms") not in (1000, 5000) or
            cadence.get("phase_ms") != 5000):
        raise NodeExchangeError("rolling cadence must use negotiated 60s/1s-or-5s/5s profile")
    return {
        "schema_version": DATASPACE_PROFILE_FACET,
        "profile_root": _dataspace_sha256_root(profile),
        "object_id": profile["object_id"],
        "count_summary": count_map,
        "privacy": "LOCAL_ONLY",
        "access_authority_verified": False,
        "transmit_authorised_by_this_function": False,
        "canonical_promotion_authorized": False,
    }


def _dataspace_validate_state(state: object, derivables: set[str]) -> None:
    if not isinstance(state, dict) or set(state) != derivables:
        raise NodeExchangeError("DataSpace state must include exact derivable IDs")
    for value in state.values():
        if value is not None and (type(value) is not int or value not in (-1, 0, 1)):
            raise NodeExchangeError("DataSpace state values must be ternary or erasure")


def build_dataspace_delta_candidate(
    *, profile: dict, prior_state: dict, new_state: dict, sequence: int,
    window_end_ms: int,
) -> dict:
    """Prepare a deterministic change candidate for an EXISTING secure adapter.

    It is neither a wire transport nor authentication, key exchange, sensor proof,
    a publishing policy or a permission to access selected private nodes.
    """
    info = validate_dataspace_profile(profile)
    ids = set(row["id"] for row in profile["derivables"])
    _dataspace_validate_state(prior_state, ids)
    _dataspace_validate_state(new_state, ids)
    prior_root = _dataspace_sha256_root(prior_state)
    if prior_root != profile["state_root"]:
        raise NodeExchangeError("DataSpace prior state does not match negotiated state root")
    if type(sequence) is not int or sequence < 1 or sequence >= 2**63:
        raise NodeExchangeError("DataSpace sequence out of range")
    if type(window_end_ms) is not int or window_end_ms < 60000 or window_end_ms % 1000:
        raise NodeExchangeError("DataSpace window_end_ms invalid")
    updates = [{"id": key, "state": new_state[key]} for key in sorted(ids)
               if prior_state[key] != new_state[key]]
    return {
        "schema_version": DATASPACE_DELTA_FACET,
        "object_id": info["object_id"],
        "profile_root": info["profile_root"],
        "prior_state_root": prior_root,
        "result_state_root": _dataspace_sha256_root(new_state),
        "sequence": sequence,
        "window_end_ms": window_end_ms,
        "updates": updates,
        "wire_ready": False,
        "cryptographically_authenticated": False,
        "publication_authorised": False,
        "canonical_promotion_authorized": False,
    }


def apply_dataspace_delta_candidate(
    *, profile: dict, prior_state: dict, candidate: dict,
    expected_sequence: int,
) -> dict:
    """Local, bounded reconstruction; caller enforces authenticated lease/nonce."""
    info = validate_dataspace_profile(profile)
    ids = set(row["id"] for row in profile["derivables"])
    _dataspace_validate_state(prior_state, ids)
    if not isinstance(candidate, dict) or candidate.get("schema_version") != DATASPACE_DELTA_FACET:
        raise NodeExchangeError("DataSpace delta schema mismatch")
    if candidate.get("profile_root") != info["profile_root"] or candidate.get("object_id") != profile["object_id"]:
        raise NodeExchangeError("DataSpace context mismatch; reconcile profile before delta")
    if (type(expected_sequence) is not int or
            type(candidate.get("sequence")) is not int or
            candidate["sequence"] != expected_sequence):
        raise NodeExchangeError("DataSpace sequence/replay mismatch")
    if candidate.get("prior_state_root") != _dataspace_sha256_root(prior_state):
        raise NodeExchangeError("DataSpace prior root mismatch")
    update_rows = candidate.get("updates")
    if not isinstance(update_rows, list) or len(update_rows) > len(ids):
        raise NodeExchangeError("DataSpace delta updates invalid")
    out = dict(prior_state)
    seen = set()
    for row in update_rows:
        if not isinstance(row, dict) or set(row) != {"id", "state"}:
            raise NodeExchangeError("DataSpace invalid delta entry")
        key = row["id"]
        if key not in ids or key in seen:
            raise NodeExchangeError("DataSpace unknown or duplicate delta identifier")
        seen.add(key)
        if row["state"] is not None and (type(row["state"]) is not int or row["state"] not in (-1, 0, 1)):
            raise NodeExchangeError("DataSpace invalid ternary delta value")
        out[key] = row["state"]
    if _dataspace_sha256_root(out) != candidate.get("result_state_root"):
        raise NodeExchangeError("DataSpace resulting state root mismatch")
    return {
        "candidate_state": out,
        "candidate_state_root": candidate["result_state_root"],
        "status": "RECONSTRUCTED_UNTRUSTED_CANDIDATE",
        "verified_transport": False,
        "canonical_promotion_authorized": False,
    }


__all__.extend((
    "DATASPACE_PROFILE_FACET", "DATASPACE_DELTA_FACET",
    "validate_dataspace_profile", "build_dataspace_delta_candidate",
    "apply_dataspace_delta_candidate",
))
