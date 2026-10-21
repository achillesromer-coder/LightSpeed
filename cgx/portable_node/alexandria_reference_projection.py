"""Reference-only Alexandria catalogue projection over existing pinned intake.

Deliberately NOT R0 acquisition, semantic admission, licence grant, a downloader,
or a new canonical store. Stable candidate IDs identify catalogue ROWS, not
domain-owned CGX Object_IDs or upstream software objects.
"""
from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urlsplit

HEX40 = re.compile(r"^[0-9a-f]{40}$")
SECRET_KEYS = ("token=", "access_key=", "secret=", "password=", "apikey=", "api_key=")


def _public_reference_url(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ValueError("bounded source URL required")
    parsed = urlsplit(value)
    if (parsed.scheme not in ("https", "http") or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.hostname.lower() in ("localhost", "127.0.0.1", "::1")
            or any(k in value.lower() for k in SECRET_KEYS)):
        raise ValueError("unsupported or credential-bearing source URL")
    return value


def compile_reference_index(source: dict) -> dict:
    if not isinstance(source, dict) or source.get("schema") != "ALEXANDRIA-EXTERNAL-REFERENCE-INTAKE-CANDIDATE/0.1":
        raise ValueError("unexpected intake schema")
    if source.get("status") != "DISCOVERY_INDEX_NOT_DOWNLOADED_NOT_PLAYABLE":
        raise ValueError("requires discovery-only input")
    groups = source.get("groups")
    nasa = source.get("nasa_sources")
    historical = source.get("historical_web")
    if not (isinstance(groups, list) and isinstance(nasa, list) and isinstance(historical, list)):
        raise ValueError("missing external reference families")
    rows = []
    seen = set()
    unresolved_lines = 0
    for group in sorted(groups, key=lambda g: g["origin"]["name"]):
        origin = group["origin"]
        for field in ("commit", "readme_blob"):
            if not isinstance(origin.get(field), str) or not HEX40.fullmatch(origin[field]):
                raise ValueError("catalogue origin requires pinned commit and README blob")
        _public_reference_url(origin["url"])
        records = group["records"]
        if len(records) != group["source_lines"]:
            raise ValueError("catalogue row count mismatch")
        unresolved_lines += group["unresolved_unlinked_line_count"]
        for rec in sorted(records, key=lambda x: x["line"]):
            if (type(rec.get("line")) is not int or rec["line"] < 1
                    or not isinstance(rec.get("title"), str) or not rec["title"].strip()
                    or rec.get("state") != "DISCOVERY_REFERENCE_ONLY"
                    or rec.get("rights") != "UPSTREAM_LICENSE_UNVERIFIED"):
                raise ValueError("unverified catalogue reference format")
            urls = rec.get("sources")
            if not isinstance(urls, list):
                raise ValueError("catalogue source URLs must be a list")
            verified_urls = [_public_reference_url(x) for x in urls]
            candidate = f"alexandria:external:index:{origin['commit']}:{rec['line']}"
            if candidate in seen:
                raise ValueError("duplicate source-catalogue line")
            seen.add(candidate)
            hint = rec.get("related_engine")
            engine_hint = None
            if hint is not None:
                if not isinstance(hint, dict) or not isinstance(hint.get("name"), str):
                    raise ValueError("engine hint malformed")
                engine_hint = {"label": hint["name"], "source_url": _public_reference_url(hint["url"]),
                               "relation": "UNVERIFIED_ENGINE_ASSOCIATION"}
            rows.append({"candidate_ref": candidate,
                         "candidate_kind": origin["type"],
                         "label": rec["title"],
                         "category": rec.get("category", ""),
                         "source_index": {"provider": origin["name"],
                                          "pinned_commit": origin["commit"],
                                          "readme_blob": origin["readme_blob"],
                                          "line": rec["line"], "reference_url": origin["url"]},
                         "upstream_reference_urls": verified_urls,
                         "engine_hint": engine_hint,
                         "rights": "UPSTREAM_LICENSE_UNVERIFIED",
                         "evidence_state": "DISCOVERY_ONLY_NOT_R0",
                         "object_id": None, "content_sha256": None,
                         "source_bytes_acquired": False,
                         "canonical_admission": False})
    for item in sorted(nasa, key=lambda x: x["url"]):
        url = _public_reference_url(item["url"])
        candidate = "alexandria:external:nasa:" + hashlib.sha256(url.encode()).hexdigest()[:24]
        if candidate in seen:
            raise ValueError("duplicate NASA catalogue URL")
        seen.add(candidate)
        rows.append({"candidate_ref": candidate, "candidate_kind": "NASA_DISCOVERY",
                     "label": item["role"], "upstream_reference_urls": [url],
                     "evidence_state": item["status"],
                     "rights": "SOURCE_RIGHTS_UNVERIFIED",
                     "object_id": None, "content_sha256": None,
                     "source_bytes_acquired": False, "canonical_admission": False})
    for item in sorted(historical, key=lambda x: x["origin"]):
        url = _public_reference_url(item["origin"])
        candidate = "alexandria:external:archive:" + hashlib.sha256(url.encode()).hexdigest()[:24]
        if candidate in seen:
            raise ValueError("duplicate historical source")
        seen.add(candidate)
        rows.append({"candidate_ref": candidate, "candidate_kind": "ARCHIVE_DISCOVERY",
                     "label": item["provider"], "upstream_reference_urls": [url],
                     "evidence_state": "CAPTURE_NOT_VERIFIED",
                     "rights": item["rights"], "object_id": None,
                     "content_sha256": None, "source_bytes_acquired": False,
                     "canonical_admission": False})
    rows.sort(key=lambda row: row["candidate_ref"])
    out = {"schema": "CGX-ALEXANDRIA-REFERENCE-PROJECTION/0.1",
           "status": "REVIEW_ONLY_REFERENCES_NOT_INGESTED",
           "identity_rule": "candidate_ref addresses a pinned catalogue row; not an Object_ID",
           "library_entrypoint": "Cognigrex.cgx:/ccc",
           "source_attestations": "PINNED_CATALOGUE_POINTERS_NOT_ORIGINAL_BYTES",
           "semantic_promotion": False, "fileset_published": False,
           "components": rows,
           "counts": {"indexed_games": sum(x["candidate_kind"] == "GAME_INDEX" for x in rows),
                      "indexed_engines": sum(x["candidate_kind"] == "ENGINE_INDEX" for x in rows),
                      "nasa_discovery": len(nasa), "archive_discovery": len(historical),
                      "unlinked_catalogue_lines": unresolved_lines,
                      "source_files_acquired": 0, "r2_admissions": 0,
                      "qualified_executable_capabilities": 0},
           "gates": ["UPSTREAM_SOURCE_BYTES_AND_SHA", "UPSTREAM_RIGHTS_AND_LICENSE",
                     "CGX_SOURCE_ENVELOPE", "OWNER_OBJECT_ID_REVIEW",
                     "NATIVE_DBR_ROOT_READBACK", "ISSUES_158_161"]}
    out["projection_sha256"] = hashlib.sha256(json.dumps(out, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()
    return out


if __name__ == "__main__":
    from pathlib import Path
    import sys
    src = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(compile_reference_index(src), indent=2, ensure_ascii=False))
