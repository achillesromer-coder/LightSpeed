"""Review-only deterministic keyed fileset manifest planner for UniSpace.

Do not mistake this for native CGX admission, signature verification or an encryption service.
Reference-only pointers are not copies or authenticated grants.
"""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any

HASH = re.compile(r"^[a-f0-9]{64}$")
FILESET = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.:_/-]{2,191}$")
MAX_COMPONENTS = 512
MAX_TOTAL_BYTES = 2**40
AUDIENCES = {"PUBLIC", "REGISTERED_USER", "COLLABORATOR", "INSTITUTIONAL", "PRIVATE_OWNER", "RESTRICTED"}

def _stable_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()

def propose_fileset(spec: dict, *, proven_local_hashes=()) -> dict[str, Any]:
    """Construct public-safe reference manifest or plan an offline pack.

    No bytes are retrieved. A caller claiming local blobs must separately verify their
    size and SHA-256. A digest string in proven_local_hashes is only a caller assertion.
    """
    if not isinstance(spec, dict) or spec.get("schema") != "CGX-FILESET-SOURCE-PROPOSAL/0.1":
        raise ValueError("unsupported input contract")
    key = spec.get("fileset_id")
    if not isinstance(key, str) or not FILESET.fullmatch(key) or ".." in key or "//" in key:
        raise ValueError("invalid fileset identifier")
    mode = spec.get("mode")
    if mode not in ("REFERENCES_ONLY", "PUBLIC_OFFLINE_PACK", "PRIVATE_OFFLINE_PACK"):
        raise ValueError("unsupported delivery mode")
    audience = spec.get("audience")
    if audience not in AUDIENCES:
        raise ValueError("unknown audience")
    if mode == "PUBLIC_OFFLINE_PACK" and audience != "PUBLIC":
        raise ValueError("public pack requires public audience")
    if mode == "PRIVATE_OFFLINE_PACK" and audience == "PUBLIC":
        raise ValueError("private pack must have non-public audience")
    for forbidden in ("private_key", "auth_token", "password", "oauth_token", "access_token", "profile_id", "personal_identity"):
        if forbidden in spec:
            raise ValueError(f"forbidden secret/identity field: {forbidden}")
    components = spec.get("components")
    if not isinstance(components, list) or not (1 <= len(components) <= MAX_COMPONENTS):
        raise ValueError("bounded nonempty component list required")
    local = set(proven_local_hashes)
    if any(not isinstance(x, str) or not HASH.fullmatch(x) for x in local):
        raise ValueError("invalid local-availability digest")
    distinct = {}
    refs = []
    total = 0
    for item in components:
        if not isinstance(item, dict):
            raise ValueError("component must be an object")
        source_id, digest, size = item.get("source_id"), item.get("sha256"), item.get("byte_length")
        if not isinstance(source_id, str) or not source_id or len(source_id) > 256:
            raise ValueError("missing source identity")
        if not isinstance(digest, str) or not HASH.fullmatch(digest):
            raise ValueError("full SHA-256 source digest required")
        if type(size) is not int or not (0 <= size <= MAX_TOTAL_BYTES):
            raise ValueError("invalid source size")
        rights = item.get("redistribution")
        if rights not in ("PERMITTED", "UNVERIFIED", "PROHIBITED"):
            raise ValueError("redistribution state must be explicit")
        if source_id in (x["source_id"] for x in refs):
            raise ValueError("duplicate source_id must not be overwritten")
        if digest in distinct and distinct[digest] != size:
            raise ValueError("same SHA-256 cannot have contradictory lengths")
        distinct[digest] = size
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError("excessive source manifest size")
        if mode != "REFERENCES_ONLY" and rights != "PERMITTED":
            raise ValueError("cannot bundle unlicensed or unreviewed source")
        if mode != "REFERENCES_ONLY" and digest not in local:
            raise ValueError("offline pack missing locally verified source")
        refs.append({
            "source_id": source_id,
            "content_sha256": digest,
            "byte_length": size,
            "redistribution": rights,
            "present_in_receiver": False,
            "source_locator": item.get("source_locator") if mode == "REFERENCES_ONLY" else None
        })
    out = {
        "schema": "CGX-KEYED-FILESET-PLAN/0.1", "status": "SOURCE_ONLY_NOT_PUBLISHED",
        "fileset_id": key, "semantic_root": "Cognigrex.cgx",
        "mode": mode, "audience": audience, "components": refs,
        "unique_blob_count": len(distinct), "source_reference_count": len(refs),
        "declared_total_source_bytes": total,
        "declared_unique_source_bytes": sum(distinct.values()),
        "has_any_embedded_bytes": False, "has_access_grant": False,
        "has_signature": False, "profile_links_disclosed": False,
        "receiver_cache_verified": False, "trusted_issuer_verified": False,
        "rights_review_complete": mode != "REFERENCES_ONLY",
        "delivery_ready": False,
        "owner_approval_required": True, "release_gate": "HOLD_ISSUES_158_161",
        "warnings": [
            "Key is public locator, not an authentication credential.",
            "This manifest hash is not a digital signature.",
            "Offline source presence/rights must be independently proven by a packaging executor.",
            "A registered profile or jurisdiction cannot silently rewrite global content."
        ]
    }
    out["manifest_sha256"] = _stable_hash(out)
    return out

if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("input_json", help="read-only input proposal path")
    a=parser.parse_args()
    with open(a.input_json, encoding="utf-8") as f:
        p=propose_fileset(json.load(f))
    print(json.dumps(p, indent=2, ensure_ascii=False))
