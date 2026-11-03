"""Read-only Wikimedia article-source → Alexandria/CGX review projection.

Never writes CGX, mints Object_ID, imports unverified claims, derives CAD geometry
from a name, fetches a network source, or changes source/legal authority.
One local export segment is at most 60 MiB. R0 original retained outside projection.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET

MAX_SEGMENT = 60 * 1024 * 1024
SCHEMA = "LOAD-WIKIMEDIA-SOURCE-PROJECTION/0.1"
ARTICLE_LINK = re.compile(r"\[\[([^\]\|\#]+)")
SAFE_PROJECT = re.compile(r"^[a-z]{2,12}wiki$")
UTC = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
LICENSE = "https://creativecommons.org/licenses/by-sa/4.0/"
def _tag(qname: str) -> str:
    return qname.rsplit("}", 1)[-1]
def _child(e: ET.Element, name: str) -> ET.Element | None:
    return next((x for x in e if _tag(x.tag) == name), None)
def _string(e: ET.Element | None) -> str | None:
    return e.text if e is not None else None
def _number(s: str | None, field: str) -> int:
    try:
        n = int(s or "")
    except ValueError as err:
        raise ValueError("INVALID_" + field.upper()) from err
    if n <= 0:
        raise ValueError("INVALID_" + field.upper())
    return n
def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
def geometric_navigation_only(source_key: str, *, levels: int = 3) -> dict:
    """A stable 12-way UI selector; NOT a proved CGX hyper-address or 3D shape."""
    if not 1 <= levels <= 8:
        raise ValueError("INVALID_LEVEL")
    stream = hashlib.shake_256(source_key.encode("utf-8")).digest(levels)
    return {
        "classification": "NONAUTHORITATIVE_DODECAHEDRAL_VIEW_SELECTOR",
        "face_path": [x % 12 for x in stream],
        "shape_basis": {"faces": 12, "edges": 30, "vertices": 20},
        "physical_geometry": None,
        "canonical_object_id": None,
        "spatial_coordinates": None,
        "mapping_validated_for_CGX": False,
    }
def article_record(page: ET.Element, *, project: str, source_sha256: str,
                   source_uri: str) -> dict | None:
    title = (_string(_child(page, "title")) or "").strip()
    namespace = (_string(_child(page, "ns")) or "").strip()
    if namespace != "0":
        return None
    if not title:
        raise ValueError("MISSING_TITLE")
    page_id = _number(_string(_child(page, "id")), "page_id")
    revision = _child(page, "revision")
    if revision is None:
        raise ValueError("MISSING_REVISION")
    revision_id = _number(_string(_child(revision, "id")), "revision_id")
    timestamp = _string(_child(revision, "timestamp"))
    if not timestamp or not UTC.match(timestamp):
        raise ValueError("INVALID_TIMESTAMP")
    source_text = _string(_child(revision, "text")) or ""
    text_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
    page_key = f"wikimedia:{project}:page:{page_id}"
    revision_key = f"{page_key}:revision:{revision_id}"
    redirect = _child(page, "redirect")
    candidate_names = []
    for term in ARTICLE_LINK.findall(source_text):
        term = term.strip().replace("_", " ")
        if term and term not in candidate_names:
            candidate_names.append(term)
        if len(candidate_names) >= 24:
            break
    return {
        "schema": SCHEMA,
        "state": "R0_HASHED_R1_PARTIAL_UNADMITTED",
        "authority": {"parent": "Cognigrex.cgx", "alexandria": "LOAD.cgx",
                      "ccc": "Cognigrex.cgx:/ccc"},
        "source": {
            "page_key": page_key, "revision_key": revision_key,
            "project": project, "page_id": page_id, "revision_id": revision_id,
            "title": title, "timestamp_utc": timestamp,
            "uri": f"https://{project[:-4]}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}" if project.endswith("wiki") else source_uri,
            "source_export_uri": source_uri,
            "original_segment_sha256": source_sha256,
            "decoded_text_sha256": text_hash,
            "rights_status": "PAGE_LICENCE_REVIEW_REQUIRED",
            "page_licence_candidate": LICENSE,
            "media_rights": "NOT_EVALUATED",
            "modification": "metadata extraction, lexical link candidates only",
            "redirect_to": redirect.attrib.get("title") if redirect is not None else None,
        },
        "resolution": {
            "semantic_entity_object_id": None,
            "wikidata_qid": None,  # Must be joined with separate provider evidence.
            "page_key_is_not_concept_identity": True,
            "lexical_link_candidates": candidate_names,
            "asserted_facts": [],
            "physics_claims_verified": False,
            "source_loss": [
                "raw wikitext not embedded (source segment retained separately)",
                "template semantics not interpreted",
                "links unverified and may represent disambiguation",
                "media and references not converted",
                "no coordinates, units or scientific shape inferred",
            ],
        },
        "navigation": geometric_navigation_only(revision_key),
        "admission": {
            "native_object_id": None, "root_authority": "UNVERIFIED",
            "dbr_receipt": None, "installed_tool": False, "canonical_write": False,
            "r3_view_status": "PLAN_ONLY",
        },
    }
def project_xml_segment(path: Path, *, project="enwiki",
                        source_uri="urn:local:mediawiki-export",
                        max_articles=1000) -> dict:
    """One bounded XML export segment. Full Wikipedia dump needs verified chunk processing."""
    if not SAFE_PROJECT.fullmatch(project):
        raise ValueError("INVALID_PROJECT")
    if not 1 <= max_articles <= 100000:
        raise ValueError("INVALID_COUNT")
    path = Path(path)
    size = path.stat().st_size
    if size > MAX_SEGMENT:
        raise ValueError("SEGMENT_LIMIT_EXCEEDED")
    if not source_uri.startswith(("urn:", "https://")):
        raise ValueError("INVALID_SOURCE_URI")
    sha = _digest(path)
    records = []
    skipped_nonarticle = 0
    for _, element in ET.iterparse(path, events=("end",)):
        if _tag(element.tag) != "page":
            continue
        rec = article_record(element, project=project, source_sha256=sha,
                             source_uri=source_uri)
        if rec is not None:
            records.append(rec)
        else:
            skipped_nonarticle += 1
        element.clear()
        if len(records) > max_articles:
            raise ValueError("ARTICLE_LIMIT_EXCEEDED")
    seen = {}
    for rec in records:
        key = rec["source"]["revision_key"]
        fingerprint = rec["source"]["decoded_text_sha256"]
        if key in seen and seen[key] != fingerprint:
            raise ValueError("REVISION_IDENTITY_COLLISION")
        if key in seen:
            raise ValueError("DUPLICATE_REVISION_IN_SEGMENT")
        seen[key] = fingerprint
    return {
        "schema": "LOAD-WIKIMEDIA-SEGMENT/0.1",
        "state": "SOURCE_REVIEW_ONLY_NOT_NATIVE",
        "source": {"uri": source_uri, "sha256": sha, "bytes": size,
                   "project": project},
        "summary": {"articles": len(records), "skipped_namespaces": skipped_nonarticle,
                    "source_payloads_mirrored": 0, "canonical_objects_created": 0},
        "records": records,
    }
def wayback_capture_reference(*, original_url: str, capture_url: str,
                              timestamp: str, http_status: int) -> dict:
    """Wayback metadata is NOT a licence to reproduce snapshot contents."""
    if not original_url.startswith("https://"):
        raise ValueError("HTTPS_ORIGINAL_REQUIRED")
    if not capture_url.startswith(("https://web.archive.org/web/", "http://web.archive.org/web/")):
        raise ValueError("WAYBACK_CAPTURE_REQUIRED")
    if not re.fullmatch(r"\d{14}", timestamp):
        raise ValueError("INVALID_CAPTURE_TIMESTAMP")
    return {
        "source_kind": "MEMENTO_SNAPSHOT_REFERENCE",
        "original_url": original_url,
        "capture_uri": capture_url,
        "capture_timestamp": timestamp,
        "http_status": http_status,
        "rights": "ORIGINAL_AND_CAPTURE_SPECIFIC_REVIEW_REQUIRED",
        "copy_source": False,
        "semantic_claims": [],
        "native_admitted": False,
    }
