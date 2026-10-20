"""Alexandria read-only multi-source catalogue normalization for CGX / UniSpace.

Only works over previously registered source references. Does not mirror code,
read private files, import engines, resolve semantic Object_ID or attest licences.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
CATALOGUES = {
    "legacy_games_engines": "cgx/review/alexandria_external_reference_intake_20261020.json",
    "curated_upstream": "cgx/review/alexandria_curated_upstream_tools_20261020.json",
}

def github_repo_identity(url: str) -> str | None:
    """Normalize only an exact GitHub owner/repo homepage, never a file/branch URL."""
    if not isinstance(url, str) or len(url)>2048:
        return None
    try: u=urlsplit(url)
    except ValueError: return None
    if u.scheme!="https" or u.hostname!="github.com" or u.username or u.password or u.port or u.query or u.fragment:
        return None
    parts=[x for x in u.path.strip("/").split("/") if x]
    if len(parts)!=2 or any(x in (".","..") or not x or len(x)>100 for x in parts):
        return None
    owner, project=parts
    if project.lower().endswith(".git"):
        project=project[:-4]
    allowed="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    if not owner or not project or any(c not in allowed for c in owner+project):
        return None
    return (owner+"/"+project).lower()

def _read(root: Path, rel: str) -> tuple[dict,dict]:
    path=root/rel
    raw=path.read_bytes()
    if len(raw)>5_000_000:
        raise ValueError("catalogue above bounded source-review ceiling")
    obj=json.loads(raw)
    if not isinstance(obj,dict):
        raise ValueError("catalogue must be object")
    return obj,{"path":rel,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}

def project_alexandria_index(root: Path=ROOT) -> dict:
    old,orig=_read(root,CATALOGUES["legacy_games_engines"])
    new,added=_read(root,CATALOGUES["curated_upstream"])
    records=new.get("repositories")
    groups=old.get("groups")
    if not isinstance(records,list) or not isinstance(groups,list):
        raise ValueError("expected upstream catalogue entries")
    if any(x.get("admission")!="REFERENCE_ONLY_HOLD"
           or x.get("redistribution_authorised") is not False
           or x.get("installed") is not False
           or x.get("license_file_verified") is not False for x in records):
        raise ValueError("unverified external assets cannot auto-promote")
    domains=Counter()
    index:dict[str,dict]={}
    for rec in records:
        key=github_repo_identity(rec.get("url",""))
        if not key or key!=rec.get("repository","").lower():
            raise ValueError("upstream repository path mismatch")
        if key in index: raise ValueError("duplicate curated identity")
        domains[rec["domain"]]+=1
        index[key]={"sources":[{"catalogue":"curated_upstream","record_id":rec["record_id"]}],
                    "domains":[rec["domain"]],"rights":"REVIEW_REQUIRED",
                    "downloaded":False,"installed":False,"confirmed_capability":False}
    legacy_links=0
    legacy_homepages=0
    legacy_unknown=0
    matched=set()
    for group in groups:
        if group.get("origin",{}).get("commit") is None: raise ValueError("legacy origin not pinned")
        for item in group.get("records",[]):
            if item.get("rights")!="UPSTREAM_LICENSE_UNVERIFIED":
                raise ValueError("legacy game/engine rights improperly promoted")
            for link in item.get("sources",[]):
                legacy_links+=1
                key=github_repo_identity(link)
                if not key:
                    legacy_unknown+=1
                    continue
                legacy_homepages+=1
                info=index.setdefault(key,{
                    "sources":[],"domains":[],"rights":"REVIEW_REQUIRED",
                    "downloaded":False,"installed":False,"confirmed_capability":False})
                info["sources"].append({"catalogue":group["origin"]["name"],
                                        "list_commit":group["origin"]["commit"],
                                        "line":item.get("line"),"source_url":link})
                if key in {r["repository"].lower() for r in records}:
                    matched.add(key)
    if len(index)>10_000: raise ValueError("excessive indices")
    for track in new.get("learning_tracks",[]):
        for r in track.get("repos",[]):
            if r.lower() not in index: raise ValueError("learning track has missing source: "+r)
    return {
        "schema":"CGX-ALEXANDRIA-INTERDOMAIN-INDEX-PROJECTION/0.1",
        "status":"DERIVED_DISCOVERY_ONLY_NO_PROVIDER_EXECUTION",
        "semantic_parent":"Cognigrex.cgx",
        "source_roots":{"legacy_games_engines":orig,"curated_upstream":added},
        "counts":{
            "legacy_list_entries":sum(len(g["records"]) for g in groups),
            "curated_repository_entries":len(records),
            "raw_external_source_links":legacy_links,
            "qualified_github_homepages":legacy_homepages,
            "non_homepage_source_links":legacy_unknown,
            "unique_normalized_upstream_repo_candidates":len(index),
            "curated_also_in_prior_catalogues":len(matched),
            "learning_tracks":len(new.get("learning_tracks",[]))
        },
        "domain_counts":dict(sorted(domains.items())),
        "cross_catalogue_links":sorted(matched),
        "source_identity_reference_count":sum(len(x["sources"]) for x in index.values()),
        "all_upstreams_without_release_grants":True,
        "all_upstreams_without_runtime_acceptance":True,
        "identity_policy":"Normalized repository is only a source-location candidate. Exact commit/blob digests and semantic identity remain separate.",
        "download_policy":"No software binaries, assets, model weights or archived media copied.",
        "qualification_backlog":[
            "Resolve upstream LICENSE/COPYING/NOTICE and asset/data/weight licences independently",
            "Pin exact commit/tree/blob plus dependencies and ABI before reuse",
            "Verify permissions and optional offline redistribution for selected assets",
            "Run equivalent capability tests and source-byte readback in owned execution sandbox",
            "Attach findings through existing CGX-CCC owner review and DBR, not auto canonical promotion"
        ]
    }
if __name__=="__main__":
    print(json.dumps(project_alexandria_index(),indent=2))
