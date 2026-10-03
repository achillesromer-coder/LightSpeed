from __future__ import annotations

"""Read-only CGX object-context resolver.

Resolves a user/object name into the existing digital-twin lineage, child-domain
identity, Operations binding, source owner and representation/evidence boundary.
It does not create objects, mutate workbooks, promote evidence, or infer missing
semantic identities.
"""

from copy import deepcopy
import json
from pathlib import Path
import re
import unicodedata
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LINEAGE_PATH = REPO_ROOT / "data" / "digital-twin" / "twin_record_source_lineage_2026-09-14.json"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "data" / "digital-twin" / "complete_digital_asset_manifest_2026-09-12.json"
DEFAULT_DOMAIN_IDENTITY_PATH = REPO_ROOT / "cgx" / "domain_templates" / "domain_child_identity_registry.json"


class CGXObjectContextError(ValueError):
    """Raised when an object-context request cannot be resolved safely."""


def _read_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CGXObjectContextError(f"expected JSON object: {path}")
    return payload


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _tokens(value: Any) -> set[str]:
    return {token for token in _norm(value).split() if token}


def _record_aliases(record: dict[str, Any], asset: dict[str, Any]) -> list[str]:
    binding = record.get("operations_binding") or {}
    values: list[Any] = [
        record.get("twin_id"),
        record.get("semantic_object_id"),
        record.get("source_name"),
        asset.get("asset_id"),
        binding.get("current_object_id"),
        binding.get("object_id"),
        *(binding.get("lineage_object_ids") or []),
    ]
    aliases = {
        "solar_hull": ["solar hull"],
        "free_flow_batteries": ["free flow battery", "free flow batteries"],
        "free_flow_capacitors": ["free flow capacitor", "free flow capacitors"],
        "free_flow_solenoid_stack": ["free flow solenoid", "solenoid stack"],
        "rfs_emff": ["rfs", "emff", "rfs emff"],
        "mark_1p": ["mark 1p"],
        "mark_i": ["mark i", "mark one", "terrestrial test chamber"],
        "mark_iii": ["mark iii", "mark 3", "mark three"],
        "luke_family": ["luke", "luke family", "luke ii", "apostle"],
        "maglev_luke_iv": ["luke iv", "maglev luke iv", "maglev"],
        "embedded_bio_blocks": ["bio blocks", "bio block", "embedded bio blocks"],
        "second_cycle": ["second cycle"],
        "intersol": ["intersol", "intersol hub"],
        "watchtower": ["watchtower", "watch tower"],
        "m1_elevated_bypass": ["m1", "m1 elevated bypass", "m1 smart hyperway", "t1 m1"],
        "romer_spaceport": ["romer spaceport", "spaceport"],
    }
    values.extend(aliases.get(str(record.get("twin_id")), []))
    return [str(value) for value in values if value not in (None, "")]


def _score(query: str, aliases: list[str]) -> tuple[int, int]:
    qn = _norm(query)
    qt = _tokens(query)
    best_exact = 0
    best_overlap = 0
    for alias in aliases:
        an = _norm(alias)
        if not an:
            continue
        if qn == an:
            best_exact = max(best_exact, 1000)
        elif qn and (qn in an or an in qn):
            best_exact = max(best_exact, 300)
        best_overlap = max(best_overlap, len(qt & _tokens(alias)))
    return best_exact, best_overlap


def _normalise_domain(domain: str | None) -> str | None:
    if domain is None:
        return None
    value = _norm(domain).replace(" ", "-")
    aliases = {
        "romer-grex": "romer",
        "romer": "romer",
        "eco-grex": "eco",
        "eco": "eco",
        "emassc": "emassc",
        "lightspeed": "lightspeed",
        "ls": "lightspeed",
    }
    return aliases.get(value, value)


def resolve_object_context(
    query: str,
    *,
    domain: str | None = None,
    lineage_path: Path = DEFAULT_LINEAGE_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    domain_identity_path: Path = DEFAULT_DOMAIN_IDENTITY_PATH,
) -> dict[str, Any]:
    query = str(query or "").strip()
    if not query:
        raise CGXObjectContextError("query must be non-empty")

    lineage = _read_object(lineage_path)
    manifest = _read_object(manifest_path)
    identities = _read_object(domain_identity_path)

    assets = {
        str(item["twin_id"]): item
        for item in (manifest.get("assets") or [])
        if isinstance(item, dict) and item.get("twin_id")
    }
    records = [
        item for item in (lineage.get("records") or [])
        if isinstance(item, dict) and item.get("twin_id") in assets
    ]
    requested_domain = _normalise_domain(domain)

    candidates: list[dict[str, Any]] = []
    for record in records:
        semantic_domain = str(record.get("semantic_domain") or "")
        if requested_domain and semantic_domain != requested_domain:
            continue
        asset = assets[str(record["twin_id"])]
        aliases = _record_aliases(record, asset)
        exact_score, overlap_score = _score(query, aliases)
        if exact_score or overlap_score:
            candidates.append({
                "record": record,
                "asset": asset,
                "aliases": aliases,
                "exact_score": exact_score,
                "overlap_score": overlap_score,
            })

    candidates.sort(
        key=lambda item: (
            -int(item["exact_score"]),
            -int(item["overlap_score"]),
            str(item["record"]["twin_id"]),
        )
    )
    if not candidates:
        raise CGXObjectContextError(f"no current object match for {query!r}")

    top = candidates[0]
    if len(candidates) > 1:
        a = (top["exact_score"], top["overlap_score"])
        b = (candidates[1]["exact_score"], candidates[1]["overlap_score"])
        if a == b and a[0] < 1000:
            raise CGXObjectContextError(
                "ambiguous object query; use a twin_id, semantic Object_ID, or more specific name"
            )

    record = deepcopy(top["record"])
    asset = deepcopy(top["asset"])
    semantic_domain = record.get("semantic_domain")
    child = ((identities.get("children") or {}).get(semantic_domain) or {})
    binding = deepcopy(record.get("operations_binding") or {})

    exact_semantic_id = record.get("semantic_object_id")
    resolution_state = "exact_semantic_object" if exact_semantic_id else "family_bound_only"
    if exact_semantic_id is None and binding.get("current_object_id"):
        # Operations family IDs are routing/context, not silently promoted semantic identity.
        resolution_state = "family_bound_only"

    return {
        "schema": "CGX-OBJECT-CONTEXT/0.1",
        "query": query,
        "resolved_twin_id": record["twin_id"],
        "semantic_domain": semantic_domain,
        "domain_identity": {
            "semantic_object_id": record.get("domain_semantic_object_id") or child.get("semantic_object_id"),
            "filespace": child.get("filespace"),
            "namespace": child.get("namespace"),
        },
        "semantic_resolution": {
            "state": resolution_state,
            "semantic_object_id": exact_semantic_id,
            "operations_current_object_id": binding.get("current_object_id") or binding.get("object_id"),
            "rule": (
                "Operations family/current IDs support routing and context but do not become an "
                "exact semantic Object_ID unless the lineage explicitly binds them."
            ),
        },
        "operations_binding": binding,
        "canonical_owner": deepcopy(record.get("canonical_owner") or {}),
        "source_name": record.get("source_name"),
        "family_state": record.get("family_state"),
        "representation": {
            "asset_id": asset.get("asset_id"),
            "file": asset.get("file"),
            "format": asset.get("format"),
            "representation_class": asset.get("representation_class"),
            "units": asset.get("units"),
            "vertices": asset.get("vertices"),
            "faces": asset.get("faces"),
            "watertight": asset.get("watertight"),
            "note": asset.get("note"),
            "sources": deepcopy(asset.get("sources") or []),
        },
        "geometry_authority": record.get("geometry_authority"),
        "lineage": {
            "generated_date": lineage.get("generated_date"),
            "last_reconciled_date": lineage.get("last_reconciled_date"),
            "record_count": lineage.get("record_count"),
            "representation_counts": deepcopy(lineage.get("representation_counts") or {}),
        },
        "evidence_boundary": (
            "Representation, Operations binding and source provenance do not promote engineering, "
            "manufacturing, physical-validation, site, regulatory, professional or release authority."
        ),
        "automatic_execution": False,
        "canonical_mutation": False,
    }


__all__ = ["CGXObjectContextError", "resolve_object_context"]
