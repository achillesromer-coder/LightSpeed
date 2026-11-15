from __future__ import annotations

"""Read-only CGX object-context resolver.

Resolves a user/object name into the existing digital-twin lineage, child-domain
identity, Operations binding, source owner and representation/evidence boundary.
It does not create objects, mutate workbooks, promote evidence, or infer missing
semantic identities.
"""

from copy import deepcopy
import json
import hashlib
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
    return _resolve_context_documents(query,domain,lineage,manifest,identities)


def _resolve_context_documents(query,domain,lineage,manifest,identities,*,exact_twin=False):
    # Do not silently overwrite duplicate occurrence records.
    for rows in (lineage.get("records"),manifest.get("assets")):
        if (type(rows) is not list or not 1<=len(rows)<=2048
                or any(type(row) is not dict or type(row.get("twin_id")) is not str
                       or not row["twin_id"] for row in rows)
                or len({row["twin_id"] for row in rows})!=len(rows)):
            raise CGXObjectContextError("invalid or duplicate twin occurrences")
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
    direct=[r for r in records if r["twin_id"]==query and
            (not requested_domain or r.get("semantic_domain")==requested_domain)]
    if exact_twin or direct:
        records=direct
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
        if (a == b or (a[0]==1000 and b[0]==1000)):
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


def _bound_twin_sources():
    sources={"lineage":DEFAULT_LINEAGE_PATH,"manifest":DEFAULT_MANIFEST_PATH,
             "identity":DEFAULT_DOMAIN_IDENTITY_PATH}
    parsed={};stamps={}
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise CGXObjectContextError("duplicate source JSON key")
            result[key]=value
        return result
    for name,path in sources.items():
        if not path.resolve().is_relative_to(REPO_ROOT.resolve()):
            raise CGXObjectContextError("twin source outside repository")
        with path.open("rb") as stream:raw=stream.read(5*1024*1024+1)
        if not 1<=len(raw)<=5*1024*1024:raise CGXObjectContextError("twin source budget")
        try:doc=json.loads(raw,object_pairs_hook=unique)
        except (ValueError,UnicodeError,RecursionError) as exc:
            raise CGXObjectContextError("invalid twin source") from exc
        if type(doc) is not dict:raise CGXObjectContextError("invalid twin source shape")
        parsed[name]=doc;stamps[name]=hashlib.sha256(raw).hexdigest()
    return parsed,stamps


def _canonical_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),
        ensure_ascii=True,allow_nan=False).encode("ascii")).hexdigest()


def twin_source_review_index():
    """Review identities and source hashes only; no object mint or provider grant."""
    docs,stamps=_bound_twin_sources()
    lineage=docs["lineage"];manifest=docs["manifest"];identities=docs["identity"]
    refs={};aliases={}
    if type(lineage.get("records")) is not list or not 1<=len(lineage["records"])<=2048:
        raise CGXObjectContextError("invalid lineage shape")
    for row in lineage["records"]:
        if type(row) is not dict or type(row.get("twin_id")) is not str or type(row.get("semantic_domain")) is not str:
            raise CGXObjectContextError("invalid twin identity")
        twin=row["twin_id"];domain=row["semantic_domain"]
        if twin in refs:raise CGXObjectContextError("duplicate twin identity")
        context=_resolve_context_documents(twin,domain,lineage,manifest,identities,exact_twin=True)
        sid=context["semantic_resolution"]["semantic_object_id"]
        if sid is not None:
            if type(sid) is not str or not sid:raise CGXObjectContextError("invalid semantic identity")
            aliases.setdefault((domain,sid),[]).append(twin)
        refs[twin]={"semantic_domain":domain,"semantic_object_id":sid,
            "resolution_state":context["semantic_resolution"]["state"],
            "occurrence_sha256":_canonical_digest(context),
            "representation_class":context["representation"]["representation_class"]}
    index={"schema":"CGX-TWIN-SOURCE-REVIEW/0.1","source_sha256":stamps,
        "references":dict(sorted(refs.items())),
        "shared_semantic_identities":[{"domain":d,"semantic_object_id":sid,"occurrences":sorted(rows)}
            for (d,sid),rows in sorted(aliases.items()) if len(rows)>1],
        "execution_authorized":False,"native_admitted":False}
    return {**index,"review_sha256":_canonical_digest(index)}


def resolve_scoped_twin_context(twin_id,*,task_id,scope_revision,expected_index_sha256,
                               expected_occurrence_sha256,authorise):
    """Reconstruct the exact selected twin under independently provided scope.

    Source bytes are read locally from fixed repository locations. Callback
    authorization is not provider authentication; no live authority is inferred.
    """
    token=lambda v:type(v) is str and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}",v))
    stamp=lambda v:type(v) is str and bool(re.fullmatch(r"[a-f0-9]{64}",v))
    if not all(token(x) for x in (twin_id,task_id,scope_revision)) or not all(stamp(x) for x in (expected_index_sha256,expected_occurrence_sha256)):
        raise CGXObjectContextError("invalid scoped twin request")
    def check():
        if authorise(task_id,twin_id,scope_revision,expected_index_sha256,expected_occurrence_sha256) is not True:
            raise PermissionError("twin occurrence denied or revoked")
    check()
    index=twin_source_review_index()
    ref=index["references"].get(twin_id)
    if (index["review_sha256"]!=expected_index_sha256 or ref is None
            or ref["occurrence_sha256"]!=expected_occurrence_sha256):
        raise CGXObjectContextError("twin occurrence revision mismatch")
    check()
    docs,stamps=_bound_twin_sources()
    if stamps!=index["source_sha256"]:raise CGXObjectContextError("twin source changed during review")
    context=_resolve_context_documents(twin_id,ref["semantic_domain"],docs["lineage"],
        docs["manifest"],docs["identity"],exact_twin=True)
    if _canonical_digest(context)!=expected_occurrence_sha256:
        raise CGXObjectContextError("twin resolved context mismatch")
    check()
    return context,{"task_id":task_id,"scope_revision":scope_revision,"twin_id":twin_id,
        "index_sha256":expected_index_sha256,"occurrence_sha256":expected_occurrence_sha256,
        "source_sha256":stamps,"provider_authentication_performed":False,
        "execution_authorized":False,"native_admitted":False}


__all__ = ["CGXObjectContextError", "resolve_object_context",
           "twin_source_review_index","resolve_scoped_twin_context"]
