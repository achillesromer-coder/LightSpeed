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
from lightspeed_runtime.storage_paths import neo_actions_root

MAX_SOURCE_BYTES = 64 * 1024 * 1024


def configured_intake_roots() -> list[Path]:
    config = Path(__file__).resolve().parents[1] / "config" / "agent_home.json"
    home = json.loads(config.read_text(encoding="utf-8"))
    root = (home.get("environment") or {}).get("assimilation_source_root")
    return [Path(root)] if isinstance(root, str) and Path(root).is_absolute() else []


def validate_upload_name(name: str) -> str:
    reserved = {"CON", "PRN", "AUX", "NUL"} | {f"{prefix}{n}" for prefix in ("COM", "LPT") for n in range(1, 10)}
    if (not isinstance(name, str) or not 1 <= len(name) <= 180 or name != name.rstrip(" .")
            or any(c in '<>:"/\\|?*' or ord(c) < 32 for c in name)
            or name.split(".")[0].upper() in reserved or name in {".", ".."}):
        raise SourceIntakeError("file name must be a portable basename")
    return name


def stage_source_bytes(name: str, data: bytes, expected_sha256: str, roots: list[Path]) -> dict[str, Any]:
    """Persist an authenticated upload; staging grants no execution authority."""
    name = validate_upload_name(name)
    if not roots:
        raise SourceIntakeError("no operator-configured intake root")
    if len(data) > MAX_SOURCE_BYTES:
        raise SourceIntakeError("source exceeds bounded staging budget")
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise SourceIntakeError("uploaded bytes do not match the requested hash")
    root = roots[0].resolve(strict=True)
    parent = (root / ".lightspeed-intake").resolve()
    if not root.is_dir() or not parent.is_relative_to(root):
        raise SourceIntakeError("staging destination is outside the configured intake root")
    parent.mkdir(exist_ok=True)
    identity = hashlib.sha256((digest + "\0" + name).encode("utf-8")).hexdigest()
    destination = parent / identity
    path = destination / "native" / name
    if destination.exists():
        if not path.resolve().is_relative_to(root):
            raise SourceIntakeError("existing staged source is outside the configured intake root")
        with path.open("rb") as stream:
            existing = stream.read(MAX_SOURCE_BYTES + 1)
        if len(existing) > MAX_SOURCE_BYTES or hashlib.sha256(existing).hexdigest() != digest:
            raise SourceIntakeError("existing staged source failed readback")
        return {"state": "staged", "source_name": name, "source_path": str(path), "source_sha256": digest,
                "byte_length": len(data), "queue_dispatched": False, "canonical_mutation": False}
    stage = Path(tempfile.mkdtemp(prefix=".upload-", dir=parent))
    (stage / "native").mkdir()
    (stage / "native" / name).write_bytes(data)
    if hashlib.sha256((stage / "native" / name).read_bytes()).hexdigest() != digest:
        raise SourceIntakeError("staged source failed readback")
    receipt = {"state": "staged", "source_name": name, "source_path": str(path), "source_sha256": digest,
               "byte_length": len(data), "queue_dispatched": False, "canonical_mutation": False}
    (stage / "upload-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    os.rename(stage, destination)
    return receipt


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
    parent = neo_actions_root(shell_root) / "intake"
    destination = parent / hashlib.sha256(command_id.encode("utf-8")).hexdigest()
    parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise SourceIntakeError("immutable intake outputs already exist; reconcile the existing receipt")
    stage = Path(tempfile.mkdtemp(prefix=".intake-", dir=parent))
    artifacts = []
    for name, content in (("source.native", data), ("source-envelope.json", envelope_bytes)):
        path = stage / name
        path.write_bytes(content)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != hashlib.sha256(content).hexdigest():
            raise SourceIntakeError("persisted intake artifact failed readback")
        artifacts.append({"path": str(destination / name), "sha256": actual, "bytes": len(content)})
    receipt = {
        "schema": "lightspeed-source-intake-receipt-v1", "command_id": command_id,
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
