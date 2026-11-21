#!/usr/bin/env python3
"""Neutral Beings: source-bound FileSpace projection, never a manufacturing compiler.

An OPTIONAL, read-only metadata/lens adapter over the EXISTING Raphael source
atlas. No alternate Object_ID master, public publishing, independent PrintSpace
qualification, hardware actuation or authorisation from device/cache hints.
"""
from __future__ import annotations
from collections import Counter
from html import escape
import json
from pathlib import Path
import re

SCHEMA = "cgx.unispace.filespace.neutral_beings.source_index.candidate.v1"
GROUPS = {"wearable","usable","operable","backend","eco","civil","romer","research","operations"}
READ_LENSES = {"identity","geometry","function","dataspace","printspace","provenance","frontier"}
INTENTS = {"creative","education","accessibility","repair","ecological-monitoring","community-aid"}
MAX_QUERY = 100

class CatalogueHold(ValueError):
    pass

def load_index(path: Path | str) -> dict:
    raw = Path(path).read_bytes()
    if len(raw)>1024*1024:
        raise CatalogueHold("index too large")
    try:
        doc=json.loads(raw)
    except (UnicodeDecodeError,ValueError) as exc:
        raise CatalogueHold("invalid catalogue bytes") from exc
    validate_index(doc)
    return doc

def validate_index(doc: dict) -> None:
    if not isinstance(doc,dict) or doc.get("schema") != SCHEMA:
        raise CatalogueHold("unrecognised FileSpace catalogue schema")
    if doc.get("status")!="OWNER_REVIEW_METADATA_ONLY":
        raise CatalogueHold("source index cannot be marked released")
    if doc.get("authority",{}).get("canonical_mutation") is not False:
        raise CatalogueHold("FileSpace candidate must never mutate canon")
    if doc.get("authority",{}).get("public_release") is not False:
        raise CatalogueHold("public release needs independent owner authority")
    refs=doc.get("source_refs")
    if not isinstance(refs,dict) or set(refs)!={"product_atlas","primitive_atlas","printceptor_family"}:
        raise CatalogueHold("missing verified source reference slots")
    for item in refs.values():
        sha=item.get("blob_sha")
        if not isinstance(sha,str) or not re.fullmatch(r"[0-9a-f]{40}",sha):
            raise CatalogueHold("invalid Git source revision pointer")
        if item.get("repository")!="NCNBOUWER/Raphael":
            raise CatalogueHold("unexpected catalogue owner")
    products=doc.get("products")
    if not isinstance(products,list) or len(products)!=80:
        raise CatalogueHold("not the source-bound 80-concept atlas")
    groups=Counter()
    ids=set()
    for item in products:
        key=item.get("source_product_id")
        if not isinstance(key,str) or not re.fullmatch(r"F[A-Z]-[0-9]{2}",key) or key in ids:
            raise CatalogueHold("invalid, duplicate or invented Product_ID")
        ids.add(key)
        if item.get("group") not in GROUPS:
            raise CatalogueHold("unknown group")
        groups[item["group"]]+=1
        if item.get("source_state")!="UNQUALIFIED_PRODUCT_CONCEPT" or item.get("physical_tested") is not False or item.get("production_approved") is not False:
            raise CatalogueHold("source evidence ceiling cannot be raised")
        if item.get("current_publication")!="HOLD_LICENSE_AND_SAFETY_REVIEW":
            raise CatalogueHold("invalid product public release gate")
        if not isinstance(item.get("label"),str) or not 1<=len(item["label"])<=140:
            raise CatalogueHold("invalid display name")
    if set(groups)!=GROUPS:
        raise CatalogueHold("source categories incomplete")
    primitives=doc.get("primitives")
    families=doc.get("printer_families")
    if not isinstance(primitives,list) or len(primitives)!=70 or not isinstance(families,list) or len(families)!=17:
        raise CatalogueHold("source primitives/family crosswalk incomplete")
    if len({x.get("technology_id") for x in primitives})!=70 or any(x.get("physical_qualified") is not False for x in primitives):
        raise CatalogueHold("primitive source class mismatch")
    if len({x.get("family_id") for x in families})!=17 or any(x.get("physically_qualified") is not False for x in families):
        raise CatalogueHold("printer hardware evidence cannot be raised")
    if doc.get("safety_policy",{}).get("device_key_is_not_permission") is not True:
        raise CatalogueHold("missing independent rights rule")
    if doc.get("evidence",{}).get("source_licence_cleared_for_republication") is not False:
        raise CatalogueHold("licence statement cannot be auto-promoted")

def resolve_lens(doc: dict, source_product_id: str, lens: str, *,
                 audience: str = "owner_review", advertised_source_sha: str | None = None) -> dict:
    """No source leakage to public; no semantic inference from name or URI."""
    validate_index(doc)
    if lens not in READ_LENSES:
        return {"status":"UNSUPPORTED_VIEW","canonical_promotion_authorized":False}
    if audience not in {"owner_review","public"}:
        return {"status":"NOT_AUTHORISED","canonical_promotion_authorized":False}
    if audience=="public":
        return {"status":"WITHHELD","canonical_promotion_authorized":False}
    upstream=doc["source_refs"]["product_atlas"]
    if advertised_source_sha is not None and advertised_source_sha!=upstream["blob_sha"]:
        return {"status":"CONTEXT_MISMATCH","canonical_promotion_authorized":False}
    product=next((p for p in doc["products"] if p["source_product_id"]==source_product_id),None)
    if product is None:
        return {"status":"UNKNOWN","canonical_promotion_authorized":False}
    base={"source_product_id":product["source_product_id"],"source_locator":product["source_locators"][0],
          "upstream_source_blob_sha":upstream["blob_sha"],"status":"SOURCE_METADATA_ONLY",
          "evidence":"UNQUALIFIED_PRODUCT_CONCEPT","model_verified":False,
          "independent_device_verified":False,"hardware_fabricated":False,
          "device_authorized":False,"canonical_promotion_authorized":False,"public_release_authorized":False}
    if lens=="identity":
        return {**base,"label":product["label"],"group":product["group"],"provenance":"SOURCE_REFERENCE_ONLY"}
    if lens=="provenance":
        return {**base,"owner":doc["source_owner"],"licence":"UNKNOWN_FOR_REDISTRIBUTION",
                "source_repository":upstream["repository"],"source_path":upstream["path"],"evidence_state":product["source_state"]}
    if lens=="geometry":
        return {**base,"status":"ADAPTER_REQUIRED","geometry":"NOT_PRESENT_IN_THIS_METADATA_INDEX","units":"UNKNOWN"}
    if lens=="function":
        return {**base,"status":"SOURCE_MODEL_REQUIRED","functional_definition":"REFER_TO_UPSTREAM_ATLAS"}
    if lens=="dataspace":
        return {**base,"status":"NOT_CONNECTED","peer_authenticated":False,"lease_verified":False,"changed_state":"UNKNOWN"}
    if lens=="printspace":
        return {**base,"status":"PHYSICAL_NOT_RUN","machine_qualified":False,"material_lot_qualified":False,
                "process_route_qualified":False,"manufacturing_output_authorized":False}
    return {**base,"status":"FRONTIER_UNKNOWN","unknown":"No registered semantic interpretation provided"}

def resolve_seed(doc: dict,label: str) -> dict:
    validate_index(doc)
    item=next((x for x in doc["proposed_public_seeds"] if x["label"]==label),None)
    if item is None:return {"status":"UNKNOWN_SEED"}
    ids={p["source_product_id"] for p in doc["products"]}
    t={p["technology_id"] for p in doc["primitives"]}
    if any(x not in ids for x in item["source_product_refs"]) or any(x not in t for x in item.get("source_technology_refs",[])):
        raise CatalogueHold("concept refers to unknown product/technology source ID")
    return {"status":"PROPOSED_CONCEPT_REVIEW","label":label,"source_product_refs":item["source_product_refs"],
            "source_technology_refs":item.get("source_technology_refs",[]),"semantic_state":item["status"],
            "notes":item["clarification"],"machine_code":None,"manufacturing_qualified":False,
            "public_release_authorized":False}

def safe_intent(intent: str) -> dict:
    if not isinstance(intent,str) or len(intent)>MAX_QUERY:
        return {"status":"HOLD_UNKNOWN_INTENT"}
    normalized=intent.casefold().strip()
    if any(word in normalized for word in ("weapon","explosive","harm","assault","munition")):
        return {"status":"EXCLUDED_WEAPON_INTENT"}
    if normalized not in INTENTS:
        return {"status":"HOLD_HUMAN_SAFETY_REVIEW"}
    return {"status":"INTENT_REVIEW_CANDIDATE_ONLY","manufacture_allowed":False}

def summary(doc: dict)->dict:
    validate_index(doc)
    return {"schema":SCHEMA,"status":"OWNER_REVIEW_METADATA_ONLY","product_concepts":len(doc["products"]),
            "groups":len(doc["groups"]),"primitive_refs":len(doc["primitives"]),
            "printer_families":len(doc["printer_families"]),"qualified_products":0,
            "qualified_printer_families":0,"public_release":False,"production":False,
            "source_owner":doc["source_owner"]}

def build_review_html(doc: dict) -> str:
    """Bounded self-contained OWNER REVIEW rendering; never includes recipes/asset bytes."""
    validate_index(doc)
    rows=[{"id":p["source_product_id"],"name":p["label"],"group":p["group"],
           "state":"Unqualified concept","safety":p["current_publication"],
           "restricted":p["display_scope"]=="RESTRICTED_REVIEW"} for p in doc["products"]]
    safe_json=json.dumps(rows,ensure_ascii=True,separators=(",",":")).replace("<","\\u003c")
    group_options="".join('<option value="'+escape(x["id"])+'">'+escape(x["title"])+"</option>" for x in doc["groups"])
    # Data interpolation is from validated source records. No external scripts or runtime API.
    return """<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Neutral Beings | UniSpace FileSpace review</title>
<style>:root{font:16px system-ui;color-scheme:dark;background:#090f18;color:#edf5f5}*{box-sizing:border-box}
body{max-width:1180px;padding:25px;margin:auto}header{border-bottom:1px solid #31516a;padding-bottom:20px}small,.dim{color:#9cb6c3}
h1{font-size:clamp(32px,6vw,55px);margin:15px 0 4px}p{line-height:1.58}
header strong{color:#80dfc7}label{display:block;margin-bottom:8px}input,select{background:#142837;color:#fff;border:1px solid #446376;border-radius:7px;padding:12px;width:100%}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:18px}
article{background:#14232e;border:1px solid #2d4e5f;border-radius:12px;padding:17px}
article strong{display:block;font-size:17px;margin:8px 0}article code{color:#8edaca}article p{font-size:13px;color:#a6c2cf;margin:0}
.controls{display:grid;grid-template-columns:2fr 1fr;gap:12px;margin:30px 0}
.flag{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:#f3c88f}
.diagram{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:20px 0}
.diagram div{background:#102c36;border:1px solid #326078;border-radius:10px;padding:16px}
.diagram b{display:block;color:#b9ebdf}.diagram span{font-size:12px;color:#b0c6d1}
footer{border-top:1px solid #304a59;margin-top:30px;padding-top:18px}
@media(max-width:540px){.controls,.diagram{grid-template-columns:1fr}}</style></head><body>
<header><strong>UniSpace · Powered by CGX</strong><h1>Neutral Beings</h1>
<p>Owner-review FileSpace catalogue lens across existing PrintSpace source concepts. This is not a product store, printable instruction library, authenticated device interface or proof of hardware manufacture.</p>
<p class="flag">Source-owner review · 80 concepts · 70 primitive refs · 17 printer-family refs · 0 qualified products</p></header>
<section class="diagram" aria-label="One object and three capabilities">
<div><b>FileSpace</b><span>Source · identity · geometry · semantic claims · uncertainty</span></div>
<div><b>DataSpace</b><span>Selective exchange · qualified state · independently verified devices</span></div>
<div><b>PrintSpace</b><span>Material route · tool · cure · measurement · physical gates</span></div></section>
<p class="dim">An unqualified concept can be inspected, not manufactured or published on these records alone. Safety exclusion: no weapons or weapon-directed build outputs; licensing, material, machine and independent release review required.</p>
<div class="controls"><div><label for="q">Find concept by name or upstream ID</label><input id="q" type="search" placeholder="Watch, phone, ecology, printer…"></div>
<div><label for="group">Source domain</label><select id="group"><option value="">All nine groups</option>""" + group_options + """</select></div></div>
<p id="count" aria-live="polite"></p><main class="grid" id="cards"></main>
<footer><p><strong>Proof boundary:</strong> The files remain governed by their existing Raphael / CGX source owners. Nothing here asserts licensed public redistribution, printability, human-use safety, qualification or deployment.</p></footer>
<script id="catalogue" type="application/json">""" + safe_json + """</script>
<script>(function(){'use strict';const all=JSON.parse(document.getElementById('catalogue').textContent);
const q=document.getElementById('q'),g=document.getElementById('group'),out=document.getElementById('cards'),count=document.getElementById('count');
function show(){let name=q.value.trim().toLowerCase(),group=g.value;let rows=all.filter(x=>(!group||x.group===group)&&(!name||(x.name+' '+x.id).toLowerCase().includes(name)));
out.textContent='';for(const x of rows){const card=document.createElement('article');const id=document.createElement('code');id.textContent=x.id;const title=document.createElement('strong');title.textContent=x.restricted?'Restricted source review':x.name;
const type=document.createElement('p');type.textContent=x.restricted?'WITHHELD — further owner review required':x.group+' · Unqualified source concept';
card.append(id,title,type);out.append(card);}count.textContent=rows.length+' source concepts (review only)';}
q.addEventListener('input',show);g.addEventListener('change',show);show();})();</script></body></html>"""

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("source",type=Path);p.add_argument("--html",type=Path);args=p.parse_args()
    doc=load_index(args.source);print(json.dumps(summary(doc),indent=2))
    if args.html:
        if args.html.exists():raise CatalogueHold("No overwrite")
        args.html.write_text(build_review_html(doc),encoding="utf8")
