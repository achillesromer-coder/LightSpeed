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
        profile = audience == "profile_authenticated" and (
            row["profile_scope"] is None or row["profile_scope"] == "profile")
        # Fail closed for restricted owner data; owner gets metadata only.
        metadata_visible = public or owner or profile
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
