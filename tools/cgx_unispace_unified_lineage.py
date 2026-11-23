"""Single-root UniSpace source-lineage projection; no new store or runtime.

Uses the existing five-facet mesh as authority for known workspace facets.
Preserves source histories and external-engine references without absorbing source,
training on it, transferring rights or altering canonical objects.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from tools.cgx_unispace_facet_mesh import FACETS, ROOT_ID, SCHEMA as MESH_SCHEMA

SCHEMA = "CGX-UNISPACE-UNIFIED-SOURCE-LINEAGE/0.1"
ID = re.compile(r"^cgx:(?:source|object):[a-z0-9][a-z0-9_.:/-]{0,119}$")
REV = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.:/+-]{0,95}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
LICENSE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+(). -]{0,79}$")
SOURCE = re.compile(r"^(?:https://[^\s<>\\]{1,350}|(?:cgx|git):[a-zA-Z0-9_./:#-]{1,350})$")
VIEWS = {"classic", "top_down", "immersive", "ar_hud", "simulation", "graph"}
KINDS = {"internal_component", "external_engine_reference", "render_reference",
         "research_reference", "training_candidate", "original_asset_reference"}
RIGHTS = {"pending", "verified_metadata_only", "restricted", "cleared_distribution"}
TRAINING = {"not_assessed", "permission_pending", "permitted", "prohibited"}
AUDIENCES = {"offline_guest", "profile_authenticated", "owner_review"}
STATE_PUBLIC = {"verified_metadata_only", "cleared_distribution"}


class LineageHold(ValueError):
    """Source or authority invariant not qualified."""


def _checked_text(value: Any, pattern: re.Pattern, name: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise LineageHold("invalid " + name)
    return value


def ternary_shape_token(position: int) -> dict[str, Any]:
    """Reversible T173 catalogue-index representation, NOT admitted 3D geometry.

    1..173 have five base-3 trits; index 174 is reserved and forbidden.
    """
    if type(position) is not int or not 1 <= position <= 173:
        raise LineageHold("T173 position not admitted; position 174 is reserved")
    value = position
    trits = ""
    for _ in range(5):
        trits = str(value % 3) + trits
        value //= 3
    assert value == 0 and int(trits, 3) == position
    return {"catalogue_index": position, "ternary_index": trits,
            "source_qualification": "RESEARCH_INDEX_ONLY",
            "verified_mesh": False, "physical_execution": False}


def fold_unispace_lineage(mesh: dict[str, Any], records: list[dict[str, Any]],
                         audience: str = "offline_guest",
                         view: str = "classic") -> dict[str, Any]:
    """Deterministic metadata-only fold across existing facet boundaries.

    Identity conflict fails closed. Byte-equivalent inputs with different
    object IDs remain independent until authorized equivalence is proven.
    A source's rights/evidence ceiling cannot be increased by view selection.
    """
    if (not isinstance(mesh, dict) or mesh.get("schema") != MESH_SCHEMA
            or mesh.get("canonical_root_id") != ROOT_ID
            or mesh.get("state") != "SOURCE_CONTRACT_MESH_OBSERVED"
            or mesh.get("facet_count") != len(FACETS)):
        raise LineageHold("verified existing facet-mesh source required")
    facet_ids = [r.get("id") for r in mesh.get("facets", []) if isinstance(r, dict)]
    if set(facet_ids) != set(FACETS) or len(facet_ids) != len(FACETS):
        raise LineageHold("inconsistent original facet identity")
    if audience not in AUDIENCES or view not in VIEWS:
        raise LineageHold("unknown audience or viewport")
    if not isinstance(records, list) or len(records) > 512:
        raise LineageHold("unbounded or invalid source references")

    unique: dict[tuple[str, str], dict[str, Any]] = {}
    duplicate_references = 0
    for raw in records:
        if not isinstance(raw, dict) or set(raw) != {
            "object_id", "revision", "kind", "source_uri", "sha256",
            "facets", "rights", "licence", "training", "t173_position",
            "supersedes", "profile_scope"
        }:
            raise LineageHold("invalid source envelope")
        obj = _checked_text(raw["object_id"], ID, "object_id")
        revision = _checked_text(raw["revision"], REV, "revision")
        kind = raw["kind"]
        if kind not in KINDS:
            raise LineageHold("unknown source kind")
        source = _checked_text(raw["source_uri"], SOURCE, "source_uri")
        digest = raw["sha256"]
        if digest is not None:
            _checked_text(digest, SHA, "sha256")
        rights, training = raw["rights"], raw["training"]
        if rights not in RIGHTS or training not in TRAINING:
            raise LineageHold("rights/training state unknown")
        if rights in {"restricted", "pending"} and training == "permitted":
            raise LineageHold("training cannot exceed source rights")
        licence = raw["licence"]
        if licence is not None:
            _checked_text(licence, LICENSE, "licence")
        if rights == "cleared_distribution" and (not licence or not digest):
            raise LineageHold("distribution requires verified source digest and licence")
        facets = raw["facets"]
        if (not isinstance(facets, list) or not 1 <= len(facets) <= 5
                or len(set(facets)) != len(facets)
                or any(x not in FACETS for x in facets)):
            raise LineageHold("unknown or duplicate facet")
        shape = raw["t173_position"]
        if shape is not None:
            ternary_shape_token(shape)
        supersedes = raw["supersedes"]
        if (supersedes is not None and
                (not isinstance(supersedes, str) or not REV.fullmatch(supersedes)
                 or supersedes == revision)):
            raise LineageHold("invalid lineage predecessor")
        scope = raw["profile_scope"]
        if scope is not None and (
            not isinstance(scope, str) or not 1 <= len(scope) <= 64
            or not re.fullmatch(r"[a-z][a-z0-9_.:-]{0,63}", scope)
        ):
            raise LineageHold("invalid profile scope")
        clean = dict(raw)
        clean["facets"] = sorted(facets)
        key = (obj, revision)
        prior = unique.get(key)
        if prior is not None:
            if prior != clean:
                raise LineageHold("conflicting exact object revision")
            duplicate_references += 1
        unique[key] = clean
    # Ensure lineage pointers cannot fabricate an existing revision or loop.
    for (obj, rev), row in unique.items():
        predecessor = row["supersedes"]
        if predecessor is not None and (obj, predecessor) not in unique:
            raise LineageHold("unresolved predecessor lineage")
        visited = {rev}
        while predecessor:
            if predecessor in visited:
                raise LineageHold("lineage cycle")
            visited.add(predecessor)
            predecessor = unique[(obj, predecessor)]["supersedes"]
    projected = []
    for (obj, rev), row in sorted(unique.items()):
        public = row["rights"] in STATE_PUBLIC and row["profile_scope"] is None
        owner = audience == "owner_review"
        # Audience is merely a presentation hint, NOT a signed ProfileSpace
        # session. Never expose nonpublic source locators from this planner.
        # A host must independently enforce the scoped signed hydration gate.
        metadata_visible = public
        projected.append({
            "object_id": obj, "revision": rev, "kind": row["kind"],
            "facets": row["facets"], "rights": row["rights"],
            "source_uri": row["source_uri"] if metadata_visible else None,
            "sha256": row["sha256"] if metadata_visible else None,
            "licence": row["licence"] if metadata_visible else None,
            "training": row["training"] if metadata_visible else "not_disclosed",
            "supersedes": row["supersedes"] if metadata_visible else None,
            "shape": ternary_shape_token(row["t173_position"])
                     if metadata_visible and row["t173_position"] is not None else None,
            "profile_scope": row["profile_scope"] if owner else None,
            "metadata_visible": metadata_visible,
            "hydration_authorized": False,
            "runtime_attached": False,
        })
    fingerprints = [(r["object_id"], r["revision"], r["sha256"])
                    for r in projected]
    receipt = hashlib.sha256(json.dumps(fingerprints, separators=(",", ":"),
                                       ensure_ascii=True).encode("utf-8")).hexdigest()
    return {
        "schema": SCHEMA, "canonical_root_id": ROOT_ID,
        "state": "SOURCE_METADATA_FOLD_ONLY",
        "audience": audience, "view": view,
        "canonical_facets": sorted(FACETS),
        "source_revision_count": len(projected),
        "exact_duplicate_references_coalesced": duplicate_references,
        "lineage_receipt_sha256": receipt,
        "records": projected,
        "engine_code_ingested": False, "training_executed": False,
        "model_weights_modified": False, "native_admitted": False,
        "mint_authorized": False, "deployment_authorized": False,
        "publication_authorized": False, "canonical_store_written": False,
    }


def fold_engine_reference_catalogue(mesh: dict[str, Any],
                                   registry: dict[str, Any]) -> dict[str, Any]:
    """Bind referenced external engines to the EXISTING single-root facet graph.

    Project labels and upstream licence pointers only. Reject attempts to
    smuggle bundled engines, training rights, downloaded code or installed
    capacities into a supposedly reference-only registry.
    """
    if (not isinstance(registry, dict)
            or registry.get("schema") !=
            "CGX-UNISPACE-EXTERNAL-ENGINE-REFERENCE-CANDIDATES/0.1"
            or registry.get("canonical_root") != ROOT_ID
            or not isinstance(registry.get("sources"), list)
            or len(registry["sources"]) > 64):
        raise LineageHold("unqualified engine reference registry")
    policy = registry.get("policy")
    if (not isinstance(policy, dict)
            or policy.get("source_code_embedded") is not False
            or policy.get("model_weights_trained") is not False
            or policy.get("source_commit_pin_required_before_reuse") is not True):
        raise LineageHold("engine reference rights policy not preserved")
    records: list[dict[str, Any]] = []
    for source in registry["sources"]:
        if not isinstance(source, dict):
            raise LineageHold("invalid external engine reference")
        name = source.get("name")
        if not isinstance(name, str) or not 1 <= len(name) <= 80:
            raise LineageHold("invalid external engine name")
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        if not slug or len(slug) > 80:
            raise LineageHold("invalid external engine alias")
        if (source.get("reference_only") is not True
                or source.get("rights_qualified_for_training") is not False
                or source.get("installation_verified") is not False
                or source.get("integration_verified") is not False
                or source.get("source_hash") is not None
                or source.get("revision") != "VERSION_PIN_PENDING"):
            raise LineageHold("external reference claims unsupported authority")
        records.append({
            "object_id": "cgx:source:external-engine:" + slug,
            "revision": "VERSION_PIN_PENDING",
            "kind": "external_engine_reference",
            "source_uri": source.get("source"),
            "sha256": None,
            "facets": source.get("candidate_facets"),
            "rights": "verified_metadata_only",
            "licence": source.get("declared_project_license"),
            "training": "not_assessed",
            "t173_position": None,
            "supersedes": None,
            "profile_scope": None,
        })
    result = fold_unispace_lineage(mesh, records)
    result["engine_reference_catalogue"] = "REFERENCE_ONLY_NO_SOURCE_BYTES"
    result["source_revision_pins_qualified"] = False
    return result


# Ternary is a reversible DIGITAL transport selection. A T173 catalogue
# position does not itself encode a proven 3-D solid, source licence, model
# capability or physical storage medium.
TRIT_BYTE_WIDTH = 6  # 3**5 < 256 <= 3**6
MAX_CAPSULE_BYTES = 8192


def bytes_to_ternary(payload: bytes) -> str:
    """Lossless fixed-width digital ternary for approved small source bytes.

    No compression claim; source bytes are six trits each and ordinary JSON,
    GPU, network and host APIs continue to use binary encodings.
    """
    if not isinstance(payload, bytes) or len(payload) > MAX_CAPSULE_BYTES:
        raise LineageHold("ternary payload must be bounded binary bytes")
    return "".join(
        "".join(str((byte // (3 ** power)) % 3)
                for power in (5, 4, 3, 2, 1, 0))
        for byte in payload
    )


def ternary_to_bytes(trits: str) -> bytes:
    """Reject malformed, overlong or noncanonical ternary byte groups."""
    if (not isinstance(trits, str) or len(trits) % TRIT_BYTE_WIDTH
            or len(trits) > MAX_CAPSULE_BYTES * TRIT_BYTE_WIDTH
            or any(digit not in "012" for digit in trits)):
        raise LineageHold("invalid ternary binary bridge")
    output = bytearray()
    for offset in range(0, len(trits), TRIT_BYTE_WIDTH):
        value = int(trits[offset:offset + TRIT_BYTE_WIDTH], 3)
        if value > 255:
            raise LineageHold("noncanonical ternary byte")
        output.append(value)
    return bytes(output)


def compile_ternary_shape_capsule(
    mesh: dict[str, Any], source_record: dict[str, Any],
    *, position: int, children: list[str] | None = None,
    payload: bytes | None = None,
    source_owned_and_embed_approved: bool = False,
) -> dict[str, Any]:
    """Compose source-linked shape/code into ONE existing CGX facet lineage.

    Default is an R0 reference capsule (no source bytes). Embedding only
    supports explicitly owner-approved, hash-matched, licenced source bytes.
    The shape index is research-only: never a verified solid geometry, mint,
    peer-sync receipt, independent model training or machine instruction.
    """
    folded = fold_unispace_lineage(mesh, [source_record], audience="offline_guest",
                                  view="graph")
    if folded["source_revision_count"] != 1:
        raise LineageHold("ambiguous source identity for capsule")
    row = folded["records"][0]
    if row["source_uri"] is None or row["sha256"] is None:
        raise LineageHold("capsule requires qualified public source digest")
    shape = ternary_shape_token(position)
    if source_record["t173_position"] not in (None, position):
        raise LineageHold("source shape position mismatch")
    if children is None:
        children = []
    if (not isinstance(children, list) or len(children) > 64
            or any(not isinstance(x, str) or not ID.fullmatch(x)
                   or x == row["object_id"] for x in children)
            or len(set(children)) != len(children)):
        raise LineageHold("invalid child reference set")
    if payload is None:
        if source_owned_and_embed_approved:
            raise LineageHold("empty owner embedding attestation")
        transport = "REFERENCE_HASH_ONLY"
        trits = None
        payload_size = None
    else:
        if (not source_owned_and_embed_approved
                or source_record["rights"] != "cleared_distribution"
                or not source_record["licence"]):
            raise LineageHold("source embedding not explicitly rights-qualified")
        trits = bytes_to_ternary(payload)
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise LineageHold("source payload differs from provenance digest")
        if ternary_to_bytes(trits) != payload:
            raise LineageHold("ternary round-trip integrity failure")
        payload_size = len(payload)
        transport = "BOUNDED_RIGHTS_APPROVED_DIGITAL_EMBED"
    core = {
        "schema": "CGX-UNISPACE-TERNARY-SHAPE-CAPSULE/0.1",
        "canonical_root_id": ROOT_ID,
        "object_id": row["object_id"],
        "revision": row["revision"],
        "source_uri": row["source_uri"],
        "source_sha256": row["sha256"],
        "facets": row["facets"],
        "rights": row["rights"],
        "licence": row["licence"],
        "shape": shape,
        "child_object_refs": sorted(children),
        "transport": transport,
        "payload_binary_bytes": payload_size,
        "payload_ternary": trits,
        "source_lineage_receipt_sha256": folded["lineage_receipt_sha256"],
        "source_metadata_only_for_unqualified_third_parties": True,
        "native_mesh_verified": False,
        "physical_shape_embedding_verified": False,
        "training_executed": False,
        "mint_authorized": False,
        "canonical_write_authorized": False,
        "network_published": False,
    }
    digest = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return {**core, "capsule_sha256": digest}


def validate_ternary_shape_capsule(capsule: dict[str, Any]) -> dict[str, Any]:
    """Independent integrity check, without trusting flags as authority."""
    if not isinstance(capsule, dict) or set(capsule) != {
        "schema", "canonical_root_id", "object_id", "revision",
        "source_uri", "source_sha256", "facets", "rights", "licence",
        "shape", "child_object_refs", "transport", "payload_binary_bytes",
        "payload_ternary", "source_lineage_receipt_sha256",
        "source_metadata_only_for_unqualified_third_parties",
        "native_mesh_verified", "physical_shape_embedding_verified",
        "training_executed", "mint_authorized", "canonical_write_authorized",
        "network_published", "capsule_sha256"
    }:
        raise LineageHold("invalid shape capsule fields")
    if capsule["schema"] != "CGX-UNISPACE-TERNARY-SHAPE-CAPSULE/0.1" or (
        capsule["canonical_root_id"] != ROOT_ID
        or not isinstance(capsule["shape"], dict)
        or capsule["shape"] != ternary_shape_token(
            capsule["shape"].get("catalogue_index"))
        or any(capsule[x] is not False for x in (
            "native_mesh_verified", "physical_shape_embedding_verified",
            "training_executed", "mint_authorized", "canonical_write_authorized",
            "network_published"))
        or capsule["source_metadata_only_for_unqualified_third_parties"] is not True
    ):
        raise LineageHold("shape capsule authority or catalogue mismatch")
    if (not isinstance(capsule["object_id"], str)
            or not ID.fullmatch(capsule["object_id"])
            or not isinstance(capsule["revision"], str)
            or not REV.fullmatch(capsule["revision"])
            or not isinstance(capsule["source_uri"], str)
            or not SOURCE.fullmatch(capsule["source_uri"])
            or not isinstance(capsule["source_sha256"], str)
            or not SHA.fullmatch(capsule["source_sha256"])
            or not isinstance(capsule["source_lineage_receipt_sha256"], str)
            or not SHA.fullmatch(capsule["source_lineage_receipt_sha256"])
            or not isinstance(capsule["facets"], list)
            or len(capsule["facets"]) == 0
            or len(set(capsule["facets"])) != len(capsule["facets"])
            or any(f not in FACETS for f in capsule["facets"])
            or not isinstance(capsule["child_object_refs"], list)
            or len(capsule["child_object_refs"]) > 64
            or len(set(capsule["child_object_refs"]))
               != len(capsule["child_object_refs"])
            or capsule["child_object_refs"] != sorted(capsule["child_object_refs"])
            or any(not isinstance(c, str) or not ID.fullmatch(c)
                   or c == capsule["object_id"]
                   for c in capsule["child_object_refs"])
            or capsule["rights"] not in RIGHTS
            or not isinstance(capsule["licence"], str)
            or not LICENSE.fullmatch(capsule["licence"])):
        raise LineageHold("invalid shape capsule source identity")
    transport = capsule["transport"]
    if transport == "REFERENCE_HASH_ONLY":
        if capsule["payload_binary_bytes"] is not None or (
                capsule["payload_ternary"] is not None):
            raise LineageHold("reference capsule secretly contains source bytes")
        payload_matches = None
    elif transport == "BOUNDED_RIGHTS_APPROVED_DIGITAL_EMBED":
        length = capsule["payload_binary_bytes"]
        if (capsule["rights"] != "cleared_distribution"
                or type(length) is not int
                or not 0 <= length <= MAX_CAPSULE_BYTES):
            raise LineageHold("embedded payload rights or length invalid")
        decoded = ternary_to_bytes(capsule["payload_ternary"])
        if len(decoded) != length:
            raise LineageHold("embedded source length mismatch")
        payload_matches = hashlib.sha256(decoded).hexdigest() == capsule["source_sha256"]
        if not payload_matches:
            raise LineageHold("embedded source SHA-256 mismatch")
    else:
        raise LineageHold("unknown shape capsule transport")
    core = {k: v for k, v in capsule.items() if k != "capsule_sha256"}
    digest = hashlib.sha256(json.dumps(core, sort_keys=True,
                             separators=(",", ":"), ensure_ascii=True
                             ).encode("utf-8")).hexdigest()
    if digest != capsule["capsule_sha256"]:
        raise LineageHold("capsule integrity SHA-256 mismatch")
    return {"schema": capsule["schema"], "integrity": "HASH_VERIFIED",
            "source_digest_matches_embedded_payload": payload_matches,
            "canonical_root_id": ROOT_ID,
            "shape_is_research_only": True, "native_admitted": False,
            "owner_signer_verified": False, "mint_authorized": False}
