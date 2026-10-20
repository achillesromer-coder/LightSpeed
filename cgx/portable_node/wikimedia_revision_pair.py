"""Bounded Alexandria R0 API-response -> R1 multilingual source graph candidate.

Provider bytes must be supplied by the existing authenticated source intake.
The adapter is offline, does not fetch, publish, translate, or execute wikitext.
A SHA-256 of caller-supplied bytes does NOT independently prove provider origin.
"""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any

API_SCHEMA = "CGX-ALEXANDRIA-WIKIMEDIA-API-PAIR/0.1"
MAX_RESPONSE_BYTES = 1_000_000
TIMESTAMP = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
ITEM_ID = re.compile(r"^Q[1-9][0-9]{0,15}$")
SITES = (("enwiki", "en", "en.wikipedia.org"),
         ("frwiki", "fr", "fr.wikipedia.org"))


def _digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _strict_json(blob: bytes) -> dict:
    if type(blob) is not bytes or not blob or len(blob) > MAX_RESPONSE_BYTES:
        raise ValueError("bounded original API response bytes required")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON member")
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError("unsupported nonfinite JSON value: " + value)
    value = json.loads(blob.decode("utf-8", errors="strict"),
                       object_pairs_hook=pairs, parse_constant=reject_constant)
    if not isinstance(value, dict):
        raise ValueError("API response must be object")
    return value


def _revision_page(response: dict, site: str, language: str, host: str, qid: str, raw: bytes) -> dict:
    query = response.get("query")
    if not isinstance(query, dict) or not isinstance(query.get("pages"), list):
        raise ValueError("missing page query")
    pages = query["pages"]
    if len(pages) != 1 or not isinstance(pages[0], dict):
        raise ValueError("exactly one source page per response")
    page = pages[0]
    pageid, title = page.get("pageid"), page.get("title")
    if (type(pageid) is not int or pageid <= 0 or page.get("ns") != 0
            or not isinstance(title, str) or not title.strip()
            or page.get("pageprops", {}).get("wikibase_item") != qid):
        raise ValueError("invalid page id, namespace, title or Wikidata identity")
    revisions = page.get("revisions")
    if not isinstance(revisions, list) or len(revisions) != 1:
        raise ValueError("exactly one revision required")
    revision = revisions[0]
    if not isinstance(revision, dict):
        raise ValueError("invalid revision")
    rid, stamp = revision.get("revid"), revision.get("timestamp")
    if type(rid) is not int or rid <= 0 or not isinstance(stamp, str) or not TIMESTAMP.fullmatch(stamp):
        raise ValueError("missing pinned revision identity and time")
    slots = revision.get("slots", {})
    main = slots.get("main") if isinstance(slots, dict) else None
    content = main.get("content") if isinstance(main, dict) else None
    if not isinstance(content, str) or not content:
        raise ValueError("original main-slot wikitext missing; no text extraction")
    if main.get("contentmodel") not in (None, "wikitext"):
        raise ValueError("unsupported main slot content model")
    payload = content.encode("utf-8")
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("source wikitext too large")
    # Lexical only. Transclusions, templates and redirects are NOT fully resolved.
    raw_links = re.findall(r"\[\[([^\]\n]{1,400})\]\]", content)
    lexical = sorted(set(x.split("|", 1)[0].split("#", 1)[0].strip()
                         for x in raw_links if x.strip()))
    return {
        "candidate_ref": f"alexandria:wiki:{site}:page:{pageid}:revision:{rid}",
        "language": language, "site": site, "pageid": pageid,
        "revision_id": rid, "revision_timestamp": stamp, "title": title,
        "shared_wikidata_item": qid, "content_model": "wikitext",
        "source_response_sha256": _digest(raw),
        "wikitext_utf8_bytes": len(payload), "wikitext_sha256": _digest(payload),
        "source_history_url": f"https://{host}/w/index.php?title={title.replace(' ','_')}&action=history",
        "revision_permalink": f"https://{host}/w/index.php?oldid={rid}",
        "licence": "CC-BY-SA-4.0", "attribution": "Revision permalink and full contributor history",
        "lexical_wikilink_targets": lexical[:100],
        "lexical_wikilink_count": len(lexical),
        "links_complete": False, "redirects_complete": False,
        "templates_expanded": False, "media_acquired": False,
        "source_body_embedded_in_projection": False,
        "owner_object_id": None, "canon_admitted": False
    }


def compile_wikimedia_pair(raw_en: bytes, raw_fr: bytes, raw_wikidata: bytes,
                           *, requested_item: str) -> dict[str, Any]:
    """Compile externally acquired exact API JSON bytes, without authority upgrade."""
    if not isinstance(requested_item, str) or not ITEM_ID.fullmatch(requested_item):
        raise ValueError("Wikidata Q-item required")
    wiki = [_strict_json(raw_en), _strict_json(raw_fr)]
    entity_response = _strict_json(raw_wikidata)
    entity_map = entity_response.get("entities")
    if not isinstance(entity_map, dict) or set(entity_map) != {requested_item}:
        raise ValueError("single exact Wikidata entity response required")
    entity = entity_map[requested_item]
    if not isinstance(entity, dict) or entity.get("id") != requested_item:
        raise ValueError("Wikidata entity mismatch")
    lastrevid = entity.get("lastrevid")
    if type(lastrevid) is not int or lastrevid <= 0:
        raise ValueError("Wikidata source revision required")
    sitelinks = entity.get("sitelinks")
    if not isinstance(sitelinks, dict):
        raise ValueError("Wikidata sitelinks missing")
    rows = []
    for (site, lang, host), raw, obj in zip(SITES, (raw_en, raw_fr), wiki):
        row = _revision_page(obj, site, lang, host, requested_item, raw)
        sitelink = sitelinks.get(site)
        if (not isinstance(sitelink, dict) or sitelink.get("site") != site
                or sitelink.get("title") != row["title"]):
            raise ValueError("source page and Wikidata sitelink do not agree")
        rows.append(row)
    if rows[0]["candidate_ref"] == rows[1]["candidate_ref"]:
        raise ValueError("distinct wiki revisions cannot be merged")
    return {
        "schema": API_SCHEMA,
        "status": "API_BYTES_STRUCTURALLY_VERIFIED_PROVIDER_ORIGIN_UNATTESTED",
        "requested_item": requested_item,
        "wikidata": {
            "source_response_sha256": _digest(raw_wikidata),
            "lastrevid": lastrevid, "entity_id": requested_item,
            "licence": "CC0-1.0", "sitelinks_verified_against_pages": True},
        "pages": rows,
        "edges": [{
            "relation": "WIKIDATA_SITELINK_ASSOCIATION_NOT_TRANSLATION",
            "from": rows[0]["candidate_ref"], "to": rows[1]["candidate_ref"],
            "via": requested_item, "evidence": "STRUCTURE_FROM_SUPPLIED_API_BYTES"}],
        "source_bytes_embedded": False,
        "original_api_responses_persisted_by_compiler": False,
        "provider_transport_authenticated": False,
        "wiki_corpus_complete": False, "lang_versions_complete": False,
        "translation_equivalence_proven": False,
        "native_dbr_verified": False, "canon_admitted": False,
        "licence_release_approved": False,
        "frontier": ["CONFIRM_OFFICIAL_PROVIDER_BYTES_AND_REVISION_PERMALINKS",
                     "PRESERVE_ORIGINAL_R0_RESPONSES_WITH_OWNER",
                     "ATTRIBUTION_AND_SHAREALIKE_REVIEW",
                     "TEMPLATE_REDIRECT_AND_OUTLINK_COMPLETENESS",
                     "NATIVE_SIGNED_DBR_READBACK", "FULL_DUMP_MANIFEST_AND_ZIM_PARITY"],
    }
