"""Reconcile connector-delivered Drive bytes with an existing local source.

This preflight produces the existing intake payload, not a second queue or a
Drive credential store. Provider text is metadata, never execution authority.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from lightspeed_runtime.source_intake import SourceIntakeError
from lightspeed_runtime.source_intake_executor import MAX_SOURCE_BYTES, validate_intake_payload


def reconcile_drive_source(*, metadata: dict, downloaded: bytes, local_source: Path,
                           allowed_roots: list[Path], declared_source_name: str | None = None) -> dict:
    """Verify exact bytes and retain only non-secret provenance fields.

    The caller obtains a fresh connector response. A provider revision/hash is
    not inferred when the connector omits it. Reuse requires full byte identity;
    names, MIME types and sizes alone never authorize deduplication or deletion.
    """
    file_id = metadata.get("id")
    if not isinstance(file_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", file_id):
        raise SourceIntakeError("invalid Drive file identity")
    size = metadata.get("size")
    if isinstance(size, bool) or not re.fullmatch(r"[0-9]{1,12}", str(size)):
        raise SourceIntakeError("Drive byte size is required")
    if len(downloaded) > MAX_SOURCE_BYTES or int(size) != len(downloaded):
        raise SourceIntakeError("Drive size mismatch or extraction budget exceeded")
    source = Path(local_source).resolve(strict=True)
    roots = [Path(p).resolve(strict=True) for p in allowed_roots]
    if not source.is_file() or not any(source.is_relative_to(p) for p in roots):
        raise SourceIntakeError("source is outside the configured intake roots")
    with source.open("rb") as stream:
        local = stream.read(MAX_SOURCE_BYTES + 1)
    if local != downloaded:
        raise SourceIntakeError("Drive and local bytes differ; retain both for reconciliation")
    digest = hashlib.sha256(local).hexdigest()
    payload = {"source_path": str(source), "source_sha256": digest}
    if declared_source_name is not None:
        payload["declared_source_name"] = declared_source_name
    payload = validate_intake_payload(payload)
    return {
        "schema": "lightspeed-drive-source-reconciliation-v1",
        "status": "EXACT_BYTES_REUSED",
        "provider": "google_drive",
        "source_url": f"https://drive.google.com/file/d/{file_id}",
        "provider_file_id": file_id,
        "provider_revision": None,
        "provider_revision_state": "NOT_VERIFIED",
        "source_sha256": digest,
        "bytes": len(local),
        "intake_payload": payload,
        "queue_dispatched": False,
        "semantic_acceptance": "requires_independent_review",
        "canonical_mutation": False,
        "deletion_eligible": False,
        "evidence_ceiling": "One fetched byte snapshot matches one local file; not a durable backup, rights clearance or corpus-completeness proof.",
    }
