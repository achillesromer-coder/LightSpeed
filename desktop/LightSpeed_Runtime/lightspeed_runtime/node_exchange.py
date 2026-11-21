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
    writable_root_registered: bool = False,
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
            "typed_transfer_queue_ready": bool(host_root_registry_ready and writable_root_registered),
            "peer_compute_queue_ready": bool(host_root_registry_ready and peers),
        },
        "claim_boundary": (
            "Mounted carrier readback and local compute are distinct proofs; "
            "peer compute remains unproven until an independently connected compute node returns a receipted result."
        ),
        "authority_transfer": False,
        "canonical_promotion_authorized": False,
    }



def _health_token(value, maximum=128):
    import re
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", value) or len(value)>maximum:
        raise NodeExchangeError("invalid health review identifier")
    return value


def _health_time(value):
    if type(value) is not str or len(value)>40:
        raise NodeExchangeError("invalid health timestamp")
    try:
        t=datetime.fromisoformat(value)
        if t.tzinfo is None:
            raise ValueError("offset required")
        return t.astimezone(UTC)
    except (ValueError,OverflowError) as exc:
        raise NodeExchangeError("invalid health timestamp") from exc


def prepare_remote_health_review(selector, *, expected_view_sha256, task_id,
                                 target_ref, scope_revision, nonce, issued_at):
    """Prepare one fixed read-only provider evidence request; never dispatch."""
    from lightspeed_runtime.cgx_capability_registry import capability_interop_review
    import re
    for value in (task_id,target_ref,scope_revision):
        _health_token(value)
    if type(nonce) is not str or not re.fullmatch(r"[0-9a-f]{32}",nonce):
        raise NodeExchangeError("invalid health challenge")
    _health_time(issued_at)
    surface=capability_interop_review(selector,reference="surface:remote-desktop",
                                      expected_view_sha256=expected_view_sha256)
    route=capability_interop_review(selector,reference="route:ops.health",
                                    expected_view_sha256=expected_view_sha256)
    if ("Remote_Desktop_Commander" not in surface["metadata"]["provider_candidates"]
            or "route:ops.health" not in surface["metadata"]["route_refs"]
            or route["metadata"].get("ro") is not True):
        raise NodeExchangeError("health review route unavailable")
    request={"schema":"CGX-REMOTE-HEALTH-REVIEW/0.1","operation":"read_supervisor_health",
             "provider":"Remote_Desktop_Commander","selector":surface["selector"],
             "task_id":task_id,"target_ref":target_ref,"scope_revision":scope_revision,
             "nonce":nonce,"issued_at":issued_at,"view_sha256":expected_view_sha256,
             "route_sha256":route["descriptor"]["sha256"],
             "surface_sha256":surface["descriptor"]["sha256"],
             "execution_authorized":False,"authority_transfer":False}
    return request,_canonical_json_sha256(request)


def reconcile_remote_health_review(request, observation, *, expected_request_sha256,
                                   authorise, now):
    """Validate a caller-supplied fixed health observation, not provider authentication.

    The trusted caller must establish device identity, live account scope and
    provenance of the observation. A challenge/hash is not signed evidence.
    No remote command, provider credential, or general executor is accepted.
    """
    import math
    if type(request) is not dict or type(observation) is not dict:
        raise NodeExchangeError("health review object required")
    expected_keys={"schema","operation","provider","selector","task_id","target_ref",
                   "scope_revision","nonce","issued_at","view_sha256","route_sha256",
                   "surface_sha256","execution_authorized","authority_transfer"}
    if set(request)!=expected_keys or any(type(v) not in (str,bool) or
            (type(v) is str and len(v)>256) for v in request.values()):
        raise NodeExchangeError("invalid health request shape")
    if _canonical_json_sha256(request)!=expected_request_sha256:
        raise NodeExchangeError("health request digest mismatch")
    rebuilt,_=prepare_remote_health_review(request["selector"],
        expected_view_sha256=request["view_sha256"],task_id=request["task_id"],
        target_ref=request["target_ref"],scope_revision=request["scope_revision"],
        nonce=request["nonce"],issued_at=request["issued_at"])
    if request!=rebuilt:
        raise NodeExchangeError("health request contract mismatch")
    if authorise(request["target_ref"],request["scope_revision"],request["task_id"]) is not True:
        raise PermissionError("health review scope denied or revoked")
    fields={"target_ref","nonce","observed_at","heartbeat_at","supervisor_pid",
            "free_ram_gib","minimum_free_ram_gib","logical_processors","reserved_logical",
            "ceiling_percent"}
    if set(observation)!=fields:
        raise NodeExchangeError("unexpected health observation fields")
    if observation["target_ref"]!=request["target_ref"] or observation["nonce"]!=request["nonce"]:
        raise NodeExchangeError("health target or challenge mismatch")
    issued=_health_time(request["issued_at"])
    observed=_health_time(observation["observed_at"])
    heartbeat=_health_time(observation["heartbeat_at"])
    current=_health_time(now)
    if not (0 <= (current-issued).total_seconds() <= 300
            and 0 <= (observed-issued).total_seconds() <= 300
            and -5 <= (current-observed).total_seconds() <= 60
            and -5 <= (observed-heartbeat).total_seconds() <= 180):
        raise NodeExchangeError("stale health request or observation")
    for key in ("supervisor_pid","logical_processors","reserved_logical","ceiling_percent"):
        if type(observation[key]) is not int:
            raise NodeExchangeError("invalid health integer")
    pid,cores,reserved,ceiling=(observation[k] for k in
        ("supervisor_pid","logical_processors","reserved_logical","ceiling_percent"))
    if not (1<=pid<=2**31-1 and 1<=cores<=4096 and 0<=reserved<cores and 1<=ceiling<=100):
        raise NodeExchangeError("invalid health integer range")
    for key in ("free_ram_gib","minimum_free_ram_gib"):
        v=observation[key]
        if type(v) not in (int,float) or not 0<=v<=1048576 or not math.isfinite(v):
            raise NodeExchangeError("invalid health memory metric")
    if authorise(request["target_ref"],request["scope_revision"],request["task_id"]) is not True:
        raise PermissionError("health review scope denied or revoked")
    receipt={"schema":"CGX-REMOTE-HEALTH-REVIEW-RECEIPT/0.1",
             "request_sha256":expected_request_sha256,
             "observation_sha256":_canonical_json_sha256(observation),
             "state":"SOURCE_BOUND_OBSERVATION_REVIEW",
             "reserve_satisfied":observation["free_ram_gib"]>=observation["minimum_free_ram_gib"],
             "provider_authentication_performed":False,"execution_performed":False,
             "authority_transfer":False,"native_admitted":False}
    receipt["review_sha256"]=_canonical_json_sha256(receipt)
    return receipt



def plan_transport_handshake(*, links, allowed, payload_bytes, max_metered_bytes=0,
                             heartbeat_seconds=60):
    """Select a transport proposal only; observations never grant authority."""
    modes = ("lan", "bluetooth", "https_relay")
    if type(allowed) is not list or len(allowed) > 3 or any(
        type(x) is not str or x not in modes for x in allowed
    ) or len(set(allowed)) != len(allowed):
        raise NodeExchangeError("invalid transport policy")
    for value, limit in ((payload_bytes, 512*1024*1024),
                         (max_metered_bytes, 512*1024*1024)):
        if type(value) is not int or not 0 <= value <= limit:
            raise NodeExchangeError("invalid transfer budget")
    if type(heartbeat_seconds) is not int or not 15 <= heartbeat_seconds <= 3600:
        raise NodeExchangeError("invalid heartbeat interval")
    if type(links) is not list or len(links) > 3:
        raise NodeExchangeError("invalid link observations")
    seen, candidates = set(), []
    for link in links:
        if type(link) is not dict or set(link) != {
            "mode", "available", "permission_granted", "metered", "max_payload_bytes"
        }:
            raise NodeExchangeError("invalid link observation")
        mode = link["mode"]
        if type(mode) is not str or mode not in modes or mode in seen:
            raise NodeExchangeError("invalid or duplicate link")
        seen.add(mode)
        if any(type(link[k]) is not bool for k in
               ("available", "permission_granted", "metered")):
            raise NodeExchangeError("invalid link flag")
        cap = link["max_payload_bytes"]
        if type(cap) is not int or not 0 <= cap <= 512*1024*1024:
            raise NodeExchangeError("invalid link capacity")
        if (mode in allowed and link["available"] and link["permission_granted"]
            and payload_bytes <= cap and
            (not link["metered"] or payload_bytes <= max_metered_bytes)):
            candidates.append(mode)
    selected = next((mode for mode in allowed if mode in candidates), "offline")
    plan = {"schema": "CGX-TRANSPORT-PLAN/0.1", "mode": selected,
            "payload_bytes": payload_bytes, "heartbeat_seconds": heartbeat_seconds,
            "state": "queue_local" if selected == "offline" else "await_peer_authentication",
            "peer_authenticated": False, "transport_activated": False,
            "execution_authorized": False, "authority_transfer": False}
    plan["plan_sha256"] = _canonical_json_sha256(plan)
    return plan



def bind_transport_offer(envelope, *, links, allowed, scope_revision, nonce,
                         issued_at, max_metered_bytes=0, heartbeat_seconds=60):
    """Bind a route proposal to an immutable transfer intent, not a grant."""
    import re
    if type(envelope) is not dict or envelope.get("schema_version") != TRANSFER_SCHEMA:
        raise NodeExchangeError("invalid transfer envelope")
    identity = {}
    for k in ("transfer_id","source_node_id","target_node_id","source_root_id",
              "target_root_id"):
        identity[k] = _health_token(envelope.get(k),96)
    if identity["source_node_id"] == identity["target_node_id"]:
        raise NodeExchangeError("peer offer requires distinct nodes")
    digest = envelope.get("source_sha256")
    if type(digest) is not str or not re.fullmatch(r"[0-9a-f]{64}",digest):
        raise NodeExchangeError("invalid transfer digest")
    identity["source_sha256"] = digest
    identity["size_bytes"] = envelope.get("size_bytes")
    for k in ("source_ref","target_relative_path"):
        v = envelope.get(k)
        if type(v) is not str or not v or len(v)>1000:
            raise NodeExchangeError("invalid transfer reference")
        identity[k] = v
    _health_token(scope_revision)
    if type(nonce) is not str or not re.fullmatch(r"[0-9a-f]{32}",nonce):
        raise NodeExchangeError("invalid offer challenge")
    _health_time(issued_at)
    plan = plan_transport_handshake(links=links,allowed=allowed,
        payload_bytes=identity["size_bytes"],max_metered_bytes=max_metered_bytes,
        heartbeat_seconds=heartbeat_seconds)
    offer = {"schema":"CGX-TRANSPORT-OFFER/0.1",
             "transfer_identity_sha256":_canonical_json_sha256(identity),
             "source_node_id":identity["source_node_id"],
             "target_node_id":identity["target_node_id"],
             "scope_revision":scope_revision,"nonce":nonce,"issued_at":issued_at,
             "plan":plan,"authority_transfer":False,"execution_authorized":False}
    offer["offer_sha256"] = _canonical_json_sha256(offer)
    return offer


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
    "plan_transport_handshake",
    "bind_transport_offer",
    "prepare_remote_health_review",
    "reconcile_remote_health_review",
    "build_transfer_envelope",
    "load_node_root_registry",
    "resolve_node_root",
    "build_transfer_envelope_from_manifest",
    "execute_local_compute",
    "execute_local_transfer",
    "sha256_file",
]
