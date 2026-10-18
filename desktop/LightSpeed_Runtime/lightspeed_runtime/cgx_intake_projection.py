"""Bounded source-intake projection for existing CGX/FileSpace and UniSpace.

Pure adapter: no new canon, database, scheduler, credentials, command, peer
handshake, physical proof or public release. Reuse node_exchange for transfer.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import PurePosixPath
from typing import Any, Mapping

SCHEMA = "cgx.unispace.intake-projection/1"
DOMAINS = {"cgx", "romer", "eco", "emassc", "lightspeed"}
VISIBILITIES = {"PRIVATE", "INTERNAL_ONLY", "CONTROLLED_SHARE", "PUBLIC_SAFE"}
EXT = {
    ".cgx": "application/x-cgx", ".csv": "text/csv",
    ".json": "application/json", ".txt": "text/plain",
    ".md": "text/markdown", ".html": "text/html",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pdf": "application/pdf", ".stl": "model/stl",
    ".step": "model/step", ".stp": "model/step",
    ".fcstd": "application/x-freecad", ".obj": "model/obj",
    ".svg": "image/svg+xml", ".png": "image/png",
    ".jpg": "image/jpeg", ".zip": "application/zip",
    ".wad": "application/x-doom-wad",
}
REQUIRED = ("provider", "provider_file_id", "provider_revision", "source_name",
            "source_ref", "owner_domain", "licence", "visibility")


class IntakeError(ValueError):
    pass


def required_text(value: Any, label: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise IntakeError(f"{label} requires bounded nonblank text")
    return value.strip()


def recognize(content: bytes, name: str) -> dict[str, Any]:
    suffix = PurePosixPath(name.lower().replace("\\", "/")).suffix
    response: dict[str, Any] = {
        "format_hint": EXT.get(suffix, "application/octet-stream"),
        "recognition": "EXTENSION_HINT_ONLY",
        "known_structure": None,
    }
    if suffix == ".json":
        if len(content) > 2 * 1024 * 1024:
            response["recognition"] = "BOUNDED_INSPECTION_DEFERRED"
            return response
        try:
            parsed = json.loads(content.decode("utf-8"))
            if isinstance(parsed, dict):
                keys = list(parsed)[:64]
                structure = {"kind": "json-object", "keys": keys,
                             "truncated": len(parsed) > len(keys)}
            elif isinstance(parsed, list):
                structure = {"kind": "json-array", "length": len(parsed)}
            else:
                structure = {"kind": "json-scalar"}
            response.update(recognition="DECODED_STRUCTURE_ONLY",
                            known_structure=structure)
        except (UnicodeError, ValueError):
            response["recognition"] = "FORMAT_HINT_UNVERIFIED"
    elif suffix == ".csv":
        try:
            header = next(csv.reader(io.StringIO(content[:65536].decode("utf-8-sig"))), [])
            if header and len(header) <= 128:
                response.update(recognition="DECODED_HEADER_ONLY",
                                known_structure={"kind": "csv-columns", "columns": header,
                                                 "partial_read": len(content) > 65536})
        except (UnicodeError, csv.Error):
            response["recognition"] = "FORMAT_HINT_UNVERIFIED"
    return response


def project_intake(content: bytes, source: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(content, bytes) or len(content) > 128 * 1024 * 1024:
        raise IntakeError("source must be bounded raw bytes")
    if not isinstance(source, Mapping):
        raise IntakeError("source metadata must be a mapping")
    s = {name: required_text(source.get(name), name,
                             1024 if name == "source_ref" else 512)
         for name in REQUIRED}
    if s["owner_domain"] not in DOMAINS:
        raise IntakeError("unknown source owner domain")
    if s["visibility"] not in VISIBILITIES:
        raise IntakeError("unknown security visibility")
    digest = hashlib.sha256(content).hexdigest()
    if source.get("expected_sha256") is not None and (
        required_text(source["expected_sha256"], "expected_sha256", 64).lower() != digest
    ):
        raise IntakeError("source hash differs from retrieved bytes")
    object_id = source.get("object_id")
    if object_id is not None:
        object_id = required_text(object_id, "object_id", 160)
    assertions = source.get("semantic_assertions", [])
    if not isinstance(assertions, list) or len(assertions) > 32:
        raise IntakeError("semantic assertions must be bounded list")
    normalized = []
    for item in assertions:
        if not isinstance(item, dict):
            raise IntakeError("invalid semantic assertion")
        value = item.get("value")
        if not isinstance(value, (str, int, float, bool, type(None))) or (
            isinstance(value, float) and not math.isfinite(value)
        ):
            value = None
        normalized.append({
            "label": required_text(item.get("label"), "assertion label", 180),
            "value": value,
            "unit": item.get("unit") if isinstance(item.get("unit"), str) and item.get("unit").strip() else None,
            "evidence_ref": required_text(item["evidence_ref"], "evidence_ref", 256)
                if item.get("evidence_ref") is not None else None,
            "state": "SOURCE_ASSERTION_UNVERIFIED",
        })
    detection = recognize(content, s["source_name"])
    return {
        "schema": SCHEMA,
        "status": "INTAKE_CANDIDATE_NOT_CANONICAL",
        "identity": {
            "object_id": object_id,
            "candidate_key": "CANDIDATE/" + digest[:20],
            "owner_domain": s["owner_domain"],
            "parent": "Cognigrex.cgx",
            "source_sha256": digest, "source_size_bytes": len(content),
        },
        "source": {k: s[k] for k in ("provider", "provider_file_id", "provider_revision",
                                     "source_name", "source_ref", "licence")},
        "security": {
            "visibility": s["visibility"],
            "acl_ref": source.get("acl_ref"),
            "admission_receipt": source.get("admission_receipt"),
        },
        "recognition": detection,
        "semantics": {
            "assertions": normalized,
            "verified_semantics": False,
            "unknown_dimensions": ["geometry", "units", "relationships",
                                   "model", "physical_evidence"],
        },
        "layers": {
            "R0_bytes": "SHA256_VERIFIED_LOCALLY",
            "R1_recognition": detection["recognition"],
            "R2_typed_semantics": "CANDIDATE" if normalized else "UNKNOWN",
            "R3_geometry": "UNKNOWN", "R4_state_rules": "UNKNOWN",
            "R5_reconstruction": "NOT_RUN",
            "R6_independent_verification": "NOT_RUN",
            "R7_peer_exchange": "NOT_RUN",
        },
        "gates": {
            "native_source_adapter": "NOT_VERIFIED",
            "canonical_dbr_commit": "HOLD",
            "signed_node_identity": "HOLD",
            "public_release": "HOLD",
            "physical_qualification": "HOLD",
        },
        "authority_transfer": False,
        "canonical_promotion_authorized": False,
        "public_publish_authorized": False,
    }


def plan_two_node_exchange(
    record: Mapping[str, Any], desktop: Mapping[str, Any], mobile: Mapping[str, Any]
) -> dict[str, Any]:
    """Create existing Node Exchange envelope only; no authenticated transport."""
    from .node_exchange import build_transfer_envelope_from_manifest
    if record.get("schema") != SCHEMA or record.get("status") != "INTAKE_CANDIDATE_NOT_CANONICAL":
        raise IntakeError("invalid intake projection")
    host_id = required_text(desktop.get("node_id"), "desktop node_id", 96)
    phone_id = required_text(mobile.get("node_id"), "mobile node_id", 96)
    if host_id == phone_id:
        raise IntakeError("two nodes must have different independently enrolled identities")
    if desktop.get("device_kind") != "desktop_host" or mobile.get("device_kind") != "mobile_touch":
        raise IntakeError("device-kind mismatch")
    identity, source = record["identity"], record["source"]
    envelope = build_transfer_envelope_from_manifest(
        source_ref=source["source_ref"],
        source_sha256=identity["source_sha256"],
        size_bytes=identity["source_size_bytes"],
        file_name=source["source_name"],
        source_node_id=host_id, target_node_id=phone_id,
        source_root_id=required_text(desktop.get("root_id"), "desktop root_id", 96),
        target_root_id=required_text(mobile.get("root_id"), "mobile root_id", 96),
        object_id=identity["object_id"],
    )
    return {
        "schema": "cgx.unispace.two-node-plan/1",
        "state": "HOLD_AUTHENTICATED_PEER_ADMISSION",
        "nodes": [{"role": "source", "id": host_id, "kind": "desktop_host"},
                  {"role": "target", "id": phone_id, "kind": "mobile_touch"}],
        "transfer_envelope": envelope,
        "readback_required": {
            "sha256": identity["source_sha256"],
            "size_bytes": identity["source_size_bytes"],
            "state_root": "REQUIRES_AUTHENTICATED_AGREEMENT",
            "dbr_root": "REQUIRES_RECEIPT",
        },
        "protocol_gates": [
            "real_peer_identity", "signature_verification", "lease_scope",
            "sequence_anti_replay", "interrupted_resume",
            "source_and_target_hash_readback", "offline_conflict_preservation",
            "revocation", "negative_unauthorised_access",
        ],
        "authenticated": False, "signed": False,
        "peer_transport_verified": False,
        "authority_transfer": False, "canonical_promotion_authorized": False,
    }


def project_public_preview(
    record: Mapping[str, Any], public_fields: Mapping[str, Any]
) -> dict[str, Any]:
    """Only an unpublished, explicitly PUBLIC_SAFE domain preview."""
    if record.get("schema") != SCHEMA or record.get("status") != "INTAKE_CANDIDATE_NOT_CANONICAL":
        raise IntakeError("unknown source projection")
    if record.get("security", {}).get("visibility") != "PUBLIC_SAFE":
        return {"schema": "cgx.unispace.public-preview/1",
                "state": "HOLD_NOT_PUBLIC_SAFE", "published": False}
    return {
        "schema": "cgx.unispace.public-preview/1",
        "state": "PENDING_OWNER_RELEASE_VERIFICATION",
        "domain": record["identity"]["owner_domain"],
        "title": required_text(public_fields.get("title"), "public title", 150),
        "summary": required_text(public_fields.get("summary"), "public summary", 1200),
        "evidence": "DESCRIPTIVE_CANDIDATE",
        "publication_scope": "PUBLIC_ORIENTATION_ONLY",
        "published": False, "source_owner_validation": "NOT_PERFORMED",
        "release_receipt": None, "canonical_promotion_authorized": False,
    }


def project_native_envelope_candidate(
    content: bytes, envelope: Mapping[str, Any], source: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind existing native source-envelope bytes to an R0-only FileSpace candidate.

    Verifies internal envelope consistency and original bytes, NOT provider
    identity, rights, a conversion-plan admission, owner authority or DBR.
    Neither a hash-matched envelope nor a PUBLIC_SAFE label publishes content.
    """
    if not isinstance(content, bytes) or not isinstance(envelope, Mapping):
        raise IntakeError("native envelope requires bytes and mapping")
    if not isinstance(source, Mapping):
        raise IntakeError("native envelope requires explicit provider metadata")
    if envelope.get("schema") != "CGX-SOURCE-ENVELOPE/0.1":
        raise IntakeError("source envelope schema mismatch")
    native = envelope.get("native_preservation")
    lineage = envelope.get("lineage")
    if not isinstance(native, Mapping) or not isinstance(lineage, Mapping):
        raise IntakeError("native preservation and lineage are required")
    if lineage.get("canonical_mutation") is not False or lineage.get("projection_only") is not True:
        raise IntakeError("source envelope cannot assert canonical mutation or authority")
    digest = hashlib.sha256(content).hexdigest()
    if (envelope.get("sha256") != digest
            or envelope.get("source_id") != "src:" + digest
            or native.get("source_sha256") != digest
            or type(envelope.get("byte_length")) is not int
            or envelope["byte_length"] != len(content)
            or type(native.get("source_byte_length")) is not int
            or native["source_byte_length"] != len(content)):
        raise IntakeError("native source byte identity mismatch")
    source_ref = required_text(source.get("source_ref"), "source_ref", 1024)
    source_name = required_text(source.get("source_name"), "source_name")
    if (envelope.get("source_name") != source_name
            or native.get("source_ref") != source_ref):
        raise IntakeError("native envelope source reference mismatch")
    declared = envelope.get("envelope_sha256")
    if not isinstance(declared, str) or len(declared) != 64:
        raise IntakeError("native envelope digest missing")
    try:
        body = {key: value for key, value in envelope.items()
                if key != "envelope_sha256"}
        actual = hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8")).hexdigest()
    except (TypeError, ValueError) as exc:
        raise IntakeError("native envelope not canonically serializable") from exc
    if actual != declared:
        raise IntakeError("native envelope digest mismatch")
    if (source.get("visibility") == "PUBLIC_SAFE"
            and str(envelope.get("release_class", "")).casefold()
            not in {"public", "public_safe"}):
        raise IntakeError("internal source envelope cannot become PUBLIC_SAFE")
    record = project_intake(content, source)
    record["native_envelope_binding"] = {
        "source_id": envelope["source_id"],
        "envelope_sha256": declared,
        "adapter_id": native.get("adapter_version"),
        "round_trip_claim": native.get("round_trip_claim"),
        "evidence_state": envelope.get("evidence_state"),
        "release_class": envelope.get("release_class"),
        "verification": "LOCAL_BYTES_AND_ENVELOPE_CONSISTENCY_ONLY",
        "provider_revision_verified": False,
        "source_rights_verified": False,
    }
    record["layers"]["R0_bytes"] = "SOURCE_ENVELOPE_BYTE_HASH_MATCH"
    record["layers"]["R1_admission"] = "REQUIRES_SEPARATE_CONVERSION_PLAN"
    record["gates"]["native_source_adapter"] = "R0_ENVELOPE_CONSISTENCY_VERIFIED"
    return record
