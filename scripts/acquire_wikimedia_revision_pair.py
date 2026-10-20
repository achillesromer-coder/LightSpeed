"""Bounded, opt-in Wikimedia R0 snapshot intake for Alexandria.

Runs ONLY when an operator explicitly invokes this script in an authorised,
private workspace with network access. No background service, database, or new
source authority. API responses are retained exactly; derived R1 is source-free.
Never point --output into public/, dist/, a web root or a shared folder.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cgx.portable_node.wikimedia_revision_pair import (
    _strict_json, compile_wikimedia_pair, ITEM_ID, MAX_RESPONSE_BYTES, TIMESTAMP)

USER_AGENT = "UniSpaceCGX-Alexandria-Research/0.1 (https://github.com/achillesromer-coder/LightSpeed)"
ORIGINS = ("https://www.wikidata.org/w/api.php",
           "https://en.wikipedia.org/w/api.php",
           "https://fr.wikipedia.org/w/api.php")
MAX_CAPTURE = MAX_RESPONSE_BYTES


def request_url(origin: str, params: dict) -> str:
    if origin not in ORIGINS:
        raise ValueError("unapproved source origin")
    return origin + "?" + urlencode(params)


def fetch_verified_url(url: str) -> bytes:
    requested = urlsplit(url)
    if requested.scheme != "https" or requested.hostname not in {
        "www.wikidata.org", "en.wikipedia.org", "fr.wikipedia.org"
    } or requested.username or requested.password:
        raise ValueError("source URL not allowlisted")
    req = Request(url, headers={"User-Agent": USER_AGENT,
                                "Accept": "application/json"})
    with urlopen(req, timeout=15) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != requested.hostname:
            raise ValueError("unexpected cross-origin redirect")
        if response.status != 200:
            raise ValueError("unexpected upstream source status")
        payload = response.read(MAX_CAPTURE + 1)
        if len(payload) > MAX_CAPTURE:
            raise ValueError("upstream response larger than capture bound")
        _strict_json(payload)
        return payload


def acquire_wikimedia_pair(
    qid: str,
    as_of_utc: str,
    output_dir: Path,
    *,
    fetcher=fetch_verified_url,
) -> dict:
    if not isinstance(qid, str) or not ITEM_ID.fullmatch(qid):
        raise ValueError("Wikidata Q-item required")
    if not isinstance(as_of_utc, str) or not TIMESTAMP.fullmatch(as_of_utc):
        raise ValueError("explicit UTC revision cutoff required")
    output = Path(output_dir).absolute()
    if any(part.lower() in {"public", "dist", ".git"} for part in output.parts):
        raise ValueError("will not write original text into a public/build directory")
    if output.exists() or output.is_symlink():
        raise ValueError("private target must not already exist")

    wikidata_url = request_url(ORIGINS[0], {
        "action": "wbgetentities", "ids": qid,
        "props": "sitelinks|info", "format": "json", "formatversion": 2})
    wd = fetcher(wikidata_url)
    entity = _strict_json(wd).get("entities", {}).get(qid)
    if not isinstance(entity, dict) or entity.get("id") != qid:
        raise ValueError("Wikidata item/identity not returned")
    sitelinks = entity.get("sitelinks", {})
    titles = []
    for site in ("enwiki", "frwiki"):
        sl = sitelinks.get(site)
        if not isinstance(sl, dict) or sl.get("site") != site or not isinstance(sl.get("title"), str):
            raise ValueError("Wikidata sitelink unavailable")
        titles.append(sl["title"])
    requests = []
    for origin, title in zip(ORIGINS[1:], titles):
        requests.append(request_url(origin, {
            "action": "query", "titles": title,
            "prop": "pageprops|revisions", "ppprop": "wikibase_item",
            "rvstart": as_of_utc, "rvdir": "older", "rvlimit": 1,
            "rvslots": "main", "rvprop": "ids|timestamp|content|sha1",
            "format": "json", "formatversion": 2}))
    en, fr = (fetcher(requests[0]), fetcher(requests[1]))
    result = compile_wikimedia_pair(en, fr, wd, requested_item=qid)
    if not result["pages"][0]["revision_timestamp"] <= as_of_utc or not result["pages"][1]["revision_timestamp"] <= as_of_utc:
        raise ValueError("revision timestamp exceeds requested cutoff")
    captured = (("wikidata_api.json", wd, wikidata_url),
                ("enwiki_api.json", en, requests[0]),
                ("frwiki_api.json", fr, requests[1]))
    manifest = {
        "schema": "CGX-WIKIMEDIA-OWNER-R0-CAPTURE/0.1",
        "status": "LOCAL_OPERATOR_CAPTURE_NOT_NATIVE_ADMISSION",
        "wikidata_item": qid, "revision_cutoff_utc": as_of_utc,
        "records": [
            {"file": name, "source_url": url, "bytes": len(data),
             "sha256": hashlib.sha256(data).hexdigest()}
            for name, data, url in captured],
        "native_dbr_verified": False,
        "provider_origin_independently_attested": False,
        "licensing_review_required": True,
    }
    # No filesystem changes are made until every source and pair check succeeds.
    output.mkdir(parents=True, exist_ok=False)
    for name, data, _ in captured:
        (output / name).write_bytes(data)
        if (output / name).read_bytes() != data:
            raise ValueError("source R0 readback mismatch")
    (output / "r1_candidate.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "r0_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--item", required=True, help="Wikidata Q-item, e.g. Q42")
    parser.add_argument("--as-of-utc", required=True, help="UTC: YYYY-MM-DDTHH:MM:SSZ")
    parser.add_argument("--output", required=True, help="new owner-private path (not public/dist)")
    args=parser.parse_args()
    print(json.dumps(acquire_wikimedia_pair(args.item, args.as_of_utc,
                 Path(args.output)), indent=2, ensure_ascii=False))
