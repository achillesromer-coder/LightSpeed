"""Bounded native-source extraction for the existing LS GO job consumer."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any
import zipfile

from lightspeed_runtime.source_intake import SourceIntakeError, build_source_envelope
from lightspeed_runtime.cgx_intake_projection import IntakeError, project_native_envelope_candidate
from lightspeed_runtime.storage_paths import neo_actions_root

MAX_SOURCE_BYTES = 64 * 1024 * 1024


def _filespace_candidate(data: bytes, envelope: dict[str, Any], source: Path) -> dict[str, Any]:
    """Project local custody only; a snapshot digest is not a provider revision proof."""
    digest = hashlib.sha256(data).hexdigest()
    try:
        candidate = project_native_envelope_candidate(data, envelope, {
            "provider": "local-filesystem", "provider_file_id": str(source),
            "provider_revision": "sha256:" + digest, "source_name": source.name,
            "source_ref": str(source), "owner_domain": "cgx",
            "licence": "UNKNOWN_REQUIRES_OWNER_REVIEW", "visibility": "PRIVATE",
            "expected_sha256": digest,
        })
    except IntakeError as exc:
        raise SourceIntakeError(str(exc)) from exc
    candidate["custody"] = {
        "domain_assignment": "CGX_STAGING_ONLY_NOT_SOURCE_OWNERSHIP",
        "provider_revision_kind": "LOCAL_BYTE_SNAPSHOT_NOT_PROVIDER_VERSION",
        "source_owner_verified": False,
    }
    return candidate


def validate_intake_payload(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"source_path", "source_sha256"}:
        raise SourceIntakeError("intake requires only source_path and source_sha256")
    path, digest = value["source_path"], value["source_sha256"]
    if not isinstance(path, str) or not 1 <= len(path) <= 2048 or not Path(path).is_absolute():
        raise SourceIntakeError("source_path must be a bounded absolute path")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise SourceIntakeError("source_sha256 must be a lowercase SHA-256 digest")
    return {"source_path": path, "source_sha256": digest}


def _bounded_archive(data: bytes) -> None:
    if not zipfile.is_zipfile(io.BytesIO(data)):
        return
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        if len(members) > 256 or sum(m.file_size for m in members) > MAX_SOURCE_BYTES:
            raise SourceIntakeError("archive exceeds bounded extraction budget")
        if any(m.flag_bits & 1 for m in members):
            raise SourceIntakeError("encrypted archive requires a specialist intake lane")


def readback_source_intake(
    payload: Any, *, command_id: str, shell_root: Path, allowed_roots: list[Path],
) -> dict[str, Any] | None:
    """Recover an already published intake bundle after an outer-receipt gap.

    This never repairs or rewrites a bundle. An incomplete or changed bundle is
    an error, so the consumer cannot rerun the action over uncertain output.
    """
    request = validate_intake_payload(payload)
    destination = (neo_actions_root(shell_root) / "intake"
                   / hashlib.sha256(command_id.encode("utf-8")).hexdigest())
    if not destination.exists():
        return None
    if destination.is_symlink() or not destination.is_dir():
        raise SourceIntakeError("existing intake destination is not an immutable directory")
    source = Path(request["source_path"]).resolve(strict=True)
    roots = [Path(root).resolve(strict=True) for root in allowed_roots]
    if not roots or not source.is_file() or not any(source.is_relative_to(root) for root in roots):
        raise SourceIntakeError("source is outside the configured intake roots")
    with source.open("rb") as stream:
        source_bytes = stream.read(MAX_SOURCE_BYTES + 1)
    if len(source_bytes) > MAX_SOURCE_BYTES or hashlib.sha256(source_bytes).hexdigest() != request["source_sha256"]:
        raise SourceIntakeError("source changed or exceeds the bounded intake budget")

    receipt_path = destination / "receipt.json"
    if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_size > 64 * 1024:
        raise SourceIntakeError("existing intake receipt is missing or unbounded")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SourceIntakeError("existing intake receipt is unreadable") from exc
    if not isinstance(receipt, dict) or any((
        receipt.get("schema") not in ("lightspeed-source-intake-receipt-v1", "lightspeed-source-intake-receipt-v2"),
        receipt.get("command_id") != command_id,
        receipt.get("status") != "completed",
        receipt.get("source_path") != str(source),
        receipt.get("source_sha256") != request["source_sha256"],
        receipt.get("receipt_path") != str(receipt_path),
        receipt.get("source_modified") is not False,
        receipt.get("canonical_mutation") is not False,
        receipt.get("semantic_acceptance") != "requires_independent_review",
    )):
        raise SourceIntakeError("existing intake receipt identity or scope mismatch")
    artifacts = receipt.get("artifacts")
    has_projection = receipt["schema"] == "lightspeed-source-intake-receipt-v2"
    expected_names = {"source.native", "source-envelope.json"}
    if has_projection:
        expected_names.add("filespace-candidate.json")
    if not isinstance(artifacts, list) or len(artifacts) != len(expected_names):
        raise SourceIntakeError("existing intake artifact manifest is incomplete")
    by_name = {Path(str(item.get("path"))).name: item for item in artifacts if isinstance(item, dict)}
    if set(by_name) != expected_names:
        raise SourceIntakeError("existing intake artifact names differ")
    for name, item in by_name.items():
        path = destination / name
        if (item.get("path") != str(path) or path.is_symlink() or not path.is_file()
                or type(item.get("bytes")) is not int or not 0 <= item["bytes"] <= MAX_SOURCE_BYTES * 2
                or path.stat().st_size != item["bytes"]):
            raise SourceIntakeError("existing intake artifact path or size mismatch")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            raise SourceIntakeError("existing intake artifact hash mismatch")
        if name == "source.native" and digest != request["source_sha256"]:
            raise SourceIntakeError("existing native source differs from requested source")
    try:
        envelope = json.loads((destination / "source-envelope.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SourceIntakeError("existing intake envelope is unreadable") from exc
    native = envelope.get("native_preservation") if isinstance(envelope, dict) else None
    if isinstance(envelope, dict):
        envelope_body = dict(envelope)
        declared_envelope_sha256 = envelope_body.pop("envelope_sha256", None)
        actual_envelope_sha256 = hashlib.sha256(
            json.dumps(envelope_body, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False).encode("utf-8")
        ).hexdigest()
    else:
        declared_envelope_sha256 = None
        actual_envelope_sha256 = None
    if not isinstance(native, dict) or any((
        declared_envelope_sha256 != actual_envelope_sha256,
        envelope.get("source_id") != f"src:{request['source_sha256']}",
        envelope.get("sha256") != request["source_sha256"],
        envelope.get("byte_length") != len(source_bytes),
        envelope.get("source_name") != source.name,
        native.get("source_ref") != str(source),
        native.get("source_sha256") != request["source_sha256"],
        receipt.get("source_id") != envelope.get("source_id"),
        receipt.get("adapter_id") != envelope.get("adapter_id"),
    )):
        raise SourceIntakeError("existing intake envelope lineage mismatch")
    if has_projection:
        try:
            candidate = json.loads((destination / "filespace-candidate.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SourceIntakeError("existing FileSpace candidate is unreadable") from exc
        if candidate != _filespace_candidate(source_bytes, envelope, source):
            raise SourceIntakeError("existing FileSpace candidate lineage mismatch")
    return receipt


def execute_source_intake(
    payload: Any, *, command_id: str, shell_root: Path, allowed_roots: list[Path],
) -> dict[str, Any]:
    """Preserve one exact byte snapshot and derived envelope; never modify a carrier.

    Allowed roots are operator configuration, never fields supplied by the job.
    The consumer owns replay detection. Existing output directories are immutable.
    """
    request = validate_intake_payload(payload)
    source = Path(request["source_path"]).resolve(strict=True)
    roots = [Path(root).resolve(strict=True) for root in allowed_roots]
    if not roots or not source.is_file() or not any(source.is_relative_to(root) for root in roots):
        raise SourceIntakeError("source is outside the configured intake roots")
    with source.open("rb") as stream:
        data = stream.read(MAX_SOURCE_BYTES + 1)
    if len(data) > MAX_SOURCE_BYTES:
        raise SourceIntakeError("source exceeds bounded extraction budget")
    digest = hashlib.sha256(data).hexdigest()
    if digest != request["source_sha256"]:
        raise SourceIntakeError("source changed or does not match the requested hash")
    _bounded_archive(data)
    envelope = build_source_envelope(source_name=source.name, data=data, source_ref=str(source))
    envelope_bytes = (json.dumps(envelope, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    candidate = _filespace_candidate(data, envelope, source)
    candidate_bytes = (json.dumps(candidate, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    parent = neo_actions_root(shell_root) / "intake"
    destination = parent / hashlib.sha256(command_id.encode("utf-8")).hexdigest()
    parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise SourceIntakeError("immutable intake outputs already exist; reconcile the existing receipt")
    stage = Path(tempfile.mkdtemp(prefix=".intake-", dir=parent))
    artifacts = []
    for name, content in (("source.native", data), ("source-envelope.json", envelope_bytes),
                          ("filespace-candidate.json", candidate_bytes)):
        path = stage / name
        path.write_bytes(content)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != hashlib.sha256(content).hexdigest():
            raise SourceIntakeError("persisted intake artifact failed readback")
        artifacts.append({"path": str(destination / name), "sha256": actual, "bytes": len(content)})
    receipt = {
        "schema": "lightspeed-source-intake-receipt-v2", "command_id": command_id,
        "status": "completed", "source_path": str(source), "source_sha256": digest,
        "source_name": source.name, "source_id": envelope["source_id"],
        "adapter_id": envelope["adapter_id"], "artifacts": artifacts,
        "warnings": envelope["warnings"], "unresolved": envelope["unresolved"],
        "evidence_class": "derived_extraction", "semantic_acceptance": "requires_independent_review",
        "source_modified": False, "canonical_mutation": False, "external_action_performed": False,
        "receipt_path": str(destination / "receipt.json"),
    }
    (stage / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    # Publish the complete bundle together. On failure retain staging for inspection.
    os.rename(stage, destination)
    return json.loads((destination / "receipt.json").read_text(encoding="utf-8"))
