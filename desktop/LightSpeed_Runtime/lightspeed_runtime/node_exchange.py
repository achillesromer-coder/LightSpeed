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
