"""Bounded R0 -> R1 source-envelope proposal for an exact pinned public catalogue.

This module accepts bytes supplied by an authorised source provider. It neither
fetches nor stores source bytes. It does not claim linked projects as acquired.
The caller must maintain a retrievable R0 source in its owner-controlled store.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SOURCE_ENVELOPE_SCHEMA = "CGX-SOURCE-ENVELOPE/0.1"
CONVERSION_RECEIPT_SCHEMA = "CGX-FILE-CONVERSION-RECEIPT/0.1"
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_CATALOGUE_RECORDS = 10000


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_blob_sha1(value: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(value)).encode("ascii") + b"\0" + value).hexdigest()


def _text_lines(original: bytes) -> list[tuple[int, int, str]]:
    # Decode-only; never evaluates Markdown, embedded scripts or link targets.
    text = original.decode("utf-8", errors="strict")
    offsets = []
    start = 0
    for line in text.splitlines(keepends=True):
        encoded = line.encode("utf-8")
        end = start + len(encoded)
        offsets.append((start, end, line.rstrip("\r\n")))
        start = end
    if start != len(original):
        raise ValueError("unable to cover all original source bytes")
    return offsets


def stage_pinned_catalogue(
    readme: bytes,
    license_bytes: bytes,
    group: dict[str, Any],
    *,
    expected_source_sha256: str,
    expected_license_sha256: str,
    expected_license_git_blob: str,
) -> dict[str, Any]:
    if not isinstance(readme, bytes) or not isinstance(license_bytes, bytes):
        raise ValueError("exact raw bytes must be supplied")
    if not readme or len(readme) > MAX_SOURCE_BYTES or not license_bytes or len(license_bytes) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds bounded admission size")
    if not isinstance(group, dict) or not isinstance(group.get("origin"), dict):
        raise ValueError("pinned catalogue identity required")
    origin = group["origin"]
    if origin.get("type") not in {"GAME_INDEX", "ENGINE_INDEX"}:
        raise ValueError("unknown catalogue family")
    if (not isinstance(expected_source_sha256, str)
        or not isinstance(expected_license_sha256, str)
        or _sha256(readme) != expected_source_sha256
        or _sha256(license_bytes) != expected_license_sha256):
        raise ValueError("original-source SHA-256 mismatch")
    if (_git_blob_sha1(readme) != origin.get("readme_blob")
        or _git_blob_sha1(license_bytes) != expected_license_git_blob):
        raise ValueError("declared pinned Git blob identity mismatch")
    if not isinstance(origin.get("commit"), str) or len(origin["commit"]) != 40:
        raise ValueError("pinned commit required")
    # Verifying a CC0 licence for the INDEX does not license linked engines.
    if b"CC0 1.0 Universal" not in license_bytes or not isinstance(origin.get("index_licence"), str) or not origin["index_licence"].startswith("CC0-1.0"):
        raise ValueError("catalogue rights could not be established")
    records = group.get("records")
    if not isinstance(records, list) or not (0 <= len(records) <= MAX_CATALOGUE_RECORDS):
        raise ValueError("invalid bounded record collection")
    if len(records) != group.get("source_lines"):
        raise ValueError("catalogue count mismatch")
    lines = _text_lines(readme)
    selected = []
    found = set()
    for record in sorted(records, key=lambda x: x["line"]):
        line_number = record.get("line")
        if type(line_number) is not int or line_number < 1 or line_number > len(lines) or line_number in found:
            raise ValueError("missing or duplicate line locator")
        found.add(line_number)
        start, end, raw_line = lines[line_number - 1]
        title = record.get("title")
        source_urls = record.get("sources")
        if (not isinstance(title, str) or not title.strip()
                or title not in raw_line
                or not isinstance(source_urls, list)
                or not source_urls
                or any(not isinstance(u, str) or u not in raw_line for u in source_urls)):
            raise ValueError("source line does not prove declared catalogue title and URLs")
        if record.get("rights") != "UPSTREAM_LICENSE_UNVERIFIED" or record.get("state") != "DISCOVERY_REFERENCE_ONLY":
            raise ValueError("linked projects cannot be implicitly promoted")
        selected.append({
            "candidate_ref": f"alexandria:external:index:{origin['commit']}:{line_number}",
            "source_line": line_number, "source_byte_start": start, "source_byte_end": end,
            "raw_line_sha256": _sha256(readme[start:end]),
            "label": title,
            "source_links": source_urls,
            "upstream_rights": "UNVERIFIED",
            "evidence_state": "CATALOGUE_LINE_VERIFIED_ONLY",
            "project_content_hash": None,
            "project_bytes_acquired": False,
            "object_id": None,
        })
    reference_id = f"git:{origin['name']}@{origin['commit']}:README.md"
    native_preservation = {
        "source_ref": reference_id, "source_sha256": expected_source_sha256,
        "source_byte_length": len(readme), "adapter_version": "catalogue-readme-stdlib-v0.1",
        "round_trip_claim": "LOSSLESS_FOR_DECLARED_FIELDS",
        "source_bytes_embedded": False,
        "original_source_locator_required_for_full_roundtrip": True,
    }
    structure = {
        "kind": "structure",
        "status": "R1_LINE_LOCATORS_CANDIDATE",
        "indexed_entries": len(selected),
        "total_lines": len(lines),
        "entries": selected,
        "unselected_source_lines": len(lines) - len(selected),
    }
    envelope = {
        "schema": SOURCE_ENVELOPE_SCHEMA, "source_id": reference_id,
        "sha256": expected_source_sha256, "byte_length": len(readme),
        "source_name": "README.md", "media_type": "text/markdown",
        "extension": ".md", "adapter_id": "catalogue-readme-stdlib-v0.1",
        "native_preservation": native_preservation,
        "authority": "ORIGINAL_UPSTREAM_PROVIDER", "evidence_state": "R0_VERIFIED_R1_CANDIDATE",
        "release_class": "INTERNAL_REVIEW_NOT_PUBLISHED",
        "projections": [structure],
        "warnings": ["CC0 covers the source catalogue only, not linked projects or executable engines.",
                     "Unselected lines, formatting and original bytes require the source provider for full retrieval."],
        "unresolved": [{"kind": "UPSTREAM_PROJECT_RIGHTS", "count": len(selected)},
                       {"kind": "CATALOGUE_UNSELECTED_LINES", "count": len(lines)-len(selected)}],
        "lineage": {"pinned_commit": origin["commit"], "pinned_readme_git_blob": origin["readme_blob"],
                    "license_source": f"git:{origin['name']}@{origin['commit']}:LICENSE",
                    "license_sha256": expected_license_sha256, "license_git_blob": expected_license_git_blob,
                    "catalogue_license": "CC0-1.0", "upstream_project_license": "UNVERIFIED"},
    }
    projection_hash = _sha256(json.dumps(structure, sort_keys=True,
                                          ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    receipt = {
        "schema": CONVERSION_RECEIPT_SCHEMA, "source_ref": reference_id,
        "source_sha256": expected_source_sha256, "media_type": "text/markdown",
        "adapter_or_capability": "catalogue-readme-stdlib-v0.1",
        "conversion_classes_used": ["R0_EXACT", "R1_SEMANTIC_REVERSIBLE"],
        "semantic_target": "Alexandria external source-index line graph; no project objects admitted",
        "loss_map": [{"scope": "unselected original source lines and formatting",
                      "action": "retain provider R0; no full-source reconstruction from R1"}],
        "frontier_items": ["UPSTREAM_PROJECT_RIGHTS", "UPSTREAM_PROJECT_SOURCE_BYTES",
                           "NATIVE_DBR_READBACK", "CANONICAL_OBJECT_ID"],
        "output_hashes": {"r1_structure_sha256": projection_hash},
        "authority_state": "NONCANONICAL_REVIEW_ONLY",
        "source_bytes_persisted_by_this_adapter": False, "native_dbr_verified": False,
        "owner_approval_required": True,
    }
    return {"source_envelope": envelope, "conversion_receipt": receipt}


if __name__ == "__main__":
    raise SystemExit("Import stage_pinned_catalogue; provider-supplied source bytes are mandatory")
