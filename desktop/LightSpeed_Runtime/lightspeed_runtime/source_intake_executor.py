"""Bounded native-source extraction for the existing LS GO job consumer."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any, Callable
import zipfile

from lightspeed_runtime.source_intake import SourceIntakeError, build_source_envelope
from lightspeed_runtime.storage_paths import neo_actions_root

MAX_SOURCE_BYTES = 64 * 1024 * 1024


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
    check_active: Callable[[], None] | None = None,
    frontier_budget: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preserve one exact byte snapshot and derived envelope; never modify a carrier.

    Allowed roots are operator configuration, never fields supplied by the job.
    The consumer owns replay detection. Existing output directories are immutable.
    """
    started_ns = time.monotonic_ns()
    if frontier_budget is not None:
        required = {"max_elapsed_s", "max_tokens", "max_tool_calls", "max_retries"}
        if (not isinstance(frontier_budget, dict) or not required.issubset(frontier_budget)
                or any(type(frontier_budget[key]) is not int or frontier_budget[key] < 0
                       for key in required)
                or frontier_budget["max_elapsed_s"] < 1
                or frontier_budget["max_tokens"] < 1
                or frontier_budget["max_tool_calls"] < 1
                or ("max_cost_usd" in frontier_budget
                    and (isinstance(frontier_budget["max_cost_usd"], bool)
                         or not isinstance(frontier_budget["max_cost_usd"], (int, float))
                         or frontier_budget["max_cost_usd"] <= 0))):
            raise SourceIntakeError("frontier intake budget is invalid")
    request = validate_intake_payload(payload)
    source = Path(request["source_path"]).resolve(strict=True)
    roots = [Path(root).resolve(strict=True) for root in allowed_roots]
    if not roots or not source.is_file() or not any(source.is_relative_to(root) for root in roots):
        raise SourceIntakeError("source is outside the configured intake roots")
    def active() -> None:
        if check_active is not None:
            check_active()
        if (frontier_budget is not None
                and time.monotonic_ns() - started_ns >= frontier_budget["max_elapsed_s"] * 1_000_000_000):
            raise SourceIntakeError("frontier intake wall-clock ceiling reached")

    active()
    chunks = []
    size = 0
    with source.open("rb") as stream:
        while True:
            active()
            chunk = stream.read(min(1024 * 1024, MAX_SOURCE_BYTES + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > MAX_SOURCE_BYTES:
                raise SourceIntakeError("source exceeds bounded extraction budget")
    data = b"".join(chunks)
    if len(data) > MAX_SOURCE_BYTES:
        raise SourceIntakeError("source exceeds bounded extraction budget")
    digest = hashlib.sha256(data).hexdigest()
    if digest != request["source_sha256"]:
        raise SourceIntakeError("source changed or does not match the requested hash")
    _bounded_archive(data)
    active()
    envelope = build_source_envelope(source_name=source.name, data=data, source_ref=str(source))
    active()
    envelope_bytes = (json.dumps(envelope, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    parent = neo_actions_root(shell_root) / "intake"
    destination = parent / hashlib.sha256(command_id.encode("utf-8")).hexdigest()
    parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise SourceIntakeError("immutable intake outputs already exist; reconcile the existing receipt")
    stage = Path(tempfile.mkdtemp(prefix=".intake-", dir=parent))
    artifacts = []
    for name, content in (("source.native", data), ("source-envelope.json", envelope_bytes)):
        active()
        path = stage / name
        with path.open("wb") as output:
            for offset in range(0, len(content), 1024 * 1024):
                active()
                output.write(content[offset:offset + 1024 * 1024])
        readback = hashlib.sha256()
        with path.open("rb") as persisted:
            while True:
                active()
                chunk = persisted.read(1024 * 1024)
                if not chunk:
                    break
                readback.update(chunk)
        actual = readback.hexdigest()
        if actual != hashlib.sha256(content).hexdigest():
            raise SourceIntakeError("persisted intake artifact failed readback")
        artifacts.append({"path": str(destination / name), "sha256": actual, "bytes": len(content)})
    active()
    frontier_usage = None
    if frontier_budget is not None:
        elapsed_ns = time.monotonic_ns() - started_ns
        frontier_usage = {
            "prepublish_elapsed_ms": (elapsed_ns + 999_999) // 1_000_000,
            "tokens": 0, "tool_calls": 1, "retries": 0, "cost_usd": 0,
            "metering": "local_monotonic_clock_and_one_deterministic_intake_call",
            "wall_clock_enforcement": "cooperative_checkpoints_before_publish",
        }
    receipt = {
        "schema": "lightspeed-source-intake-receipt-v1", "command_id": command_id,
        "status": "completed", "source_path": str(source), "source_sha256": digest,
        "source_name": source.name, "source_id": envelope["source_id"],
        "adapter_id": envelope["adapter_id"], "artifacts": artifacts,
        "warnings": envelope["warnings"], "unresolved": envelope["unresolved"],
        "evidence_class": "derived_extraction", "semantic_acceptance": "requires_independent_review",
        "source_modified": False, "canonical_mutation": False, "external_action_performed": False,
        **({"frontier_usage": frontier_usage} if frontier_usage is not None else {}),
        "receipt_path": str(destination / "receipt.json"),
    }
    (stage / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    # Publish the complete bundle together. On failure retain staging for inspection.
    active()
    os.rename(stage, destination)
    return json.loads((destination / "receipt.json").read_text(encoding="utf-8"))
