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
    "official_references": "cgx/review/alexandria_official_reference_roots_20261020.json",
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
    official,official_source=_read(root,CATALOGUES["official_references"])
    project,project_file=_read(root,"cgx/review/alexandria_hypersomnia_project_source_scope_20261021.json")
    channel,channel_file=_read(root,"cgx/review/alexandria_libdatachannel_source_scope_20261021.json")
    records=new.get("repositories")
    official_records=official.get("official_references")
    groups=old.get("groups")
    if not isinstance(records,list) or not isinstance(groups,list) or not isinstance(official_records,list):
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
    if any(x.get("public_kit_inclusion")!="REFERENCE_ONLY_HOLD" or x.get("rights_verified_for_pack") is not False or x.get("content_downloaded") is not False for x in official_records):
        raise ValueError("unverified official source cannot be embedded")
    if len({x.get("url") for x in official_records}) != len(official_records):
        raise ValueError("duplicate official source reference")
    for track in new.get("learning_tracks",[]):
        for r in track.get("repos",[]):
            if r.lower() not in index: raise ValueError("learning track has missing source: "+r)
    if (project.get("canonical_object_id") is not None
        or project.get("canon_admitted") is not False
        or project.get("all_assets_acquired") is not False
        or project.get("licence_release_approved") is not False
        or project.get("source_file_count") != 4
        or not project.get("related_game_index_ref", "").startswith("alexandria:external:index:")):
        raise ValueError("project scope improperly upgraded or loses pinned source")
    if (channel.get("canonical_object_id") is not None
        or channel.get("parent_source_root") != project.get("source_root")
        or channel.get("original_file_count") != 5
        or channel.get("all_project_source_acquired") is not False
        or channel.get("native_dbr_verified") is not False
        or channel.get("capability_claims",{}).get("network_interoperability_tested") is not False):
        raise ValueError("network dependency sample cannot become native accepted peer")
    samples = [
        {"domain":"Games","source_root":project["source_root"],
         "index_reference":project["related_game_index_ref"],
         "status":project["status"],"source_files_proved":4,
         "authority":"PARTIAL_R0_SAMPLE_ONLY","public_distribution":False,
         "executable":False,"canonical_promotion":False},
        {"domain":"Native peer transport","source_root":channel["source_root"],
         "parent_source_root":channel["parent_source_root"],
         "status":channel["status"],"source_files_proved":5,
         "authority":"PARTIAL_DEPENDENCY_SOURCE_ONLY","public_distribution":False,
         "executable":False,"canonical_promotion":False}
    ]
    return {
        "schema":"CGX-ALEXANDRIA-INTERDOMAIN-INDEX-PROJECTION/0.1",
        "status":"DERIVED_DISCOVERY_ONLY_NO_PROVIDER_EXECUTION",
        "semantic_parent":"Cognigrex.cgx",
        "source_roots":{"legacy_games_engines":orig,"curated_upstream":added,"official_references":official_source,"hypersomnia_sample":project_file,"libdatachannel_sample":channel_file},
        "counts":{
            "legacy_list_entries":sum(len(g["records"]) for g in groups),
            "curated_repository_entries":len(records),
            "official_reference_roots":len(official_records),
            "original_source_samples":len(samples),
            "verified_original_sample_files":sum(x["source_files_proved"] for x in samples),
            "raw_external_source_links":legacy_links,
            "qualified_github_homepages":legacy_homepages,
            "non_homepage_source_links":legacy_unknown,
            "unique_normalized_upstream_repo_candidates":len(index),
            "curated_also_in_prior_catalogues":len(matched),
            "learning_tracks":len(new.get("learning_tracks",[]))
        },
        "domain_counts":dict(sorted(domains.items())),
        "official_domains":dict(sorted(Counter(x["domain"] for x in official_records).items())),
        "cross_catalogue_links":sorted(matched),
        "source_qualified_samples":samples,
        "source_identity_reference_count":sum(len(x["sources"]) for x in index.values()),
        "all_upstreams_without_release_grants":True,
        "all_upstreams_without_runtime_acceptance":True,
        "identity_policy":"Normalized repository is only a source-location candidate. Exact commit/blob digests and semantic identity remain separate.",
        "download_policy":"No software binaries, official datasets, textbook bodies, assets, model weights or archived media copied.",
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
