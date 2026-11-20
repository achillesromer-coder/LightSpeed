"""CGX fiction/empirical semantic mirror -- review-only deterministic resolver.

One proposed identity PER distinguishable referent; multiple representations / mentions.
Does not create native S92 objects, mutate SQLite, train, hydrate copyrighted works,
perform outside network calls, or transfer source/child authority.

Compatible conceptually with:
  CGX-CROSS-DOMAIN-BRIDGE-REGISTRY/0.1
  CGX-RELATION-QUALIFIER/0.2
  CGX-SEMANTIC-VIEW-LENS-REGISTRY/0.1
  CGX-SOURCE-ENVELOPE/0.1
"""
from __future__ import annotations
import hashlib,json,re
from collections import defaultdict
from typing import Any

SCHEMA="CGX-FICTION-REAL-MIRROR/0.1"
ROOT="cgx:root:cognigrex"
ALLOWED_KINDS={"real_work","fictional_entity","constructed_language","creative_work",
               "documented_standard","reference_candidate","documented_practice"}
ALLOWED_RELATIONS={"FICTION_MENTIONS_REAL_WORK","FICTION_MENTIONS_CANDIDATE",
                   "FICTION_EMBEDS_FICTIONAL_OBJECT","ALIAS_IN_CONTEXT","HAS_REAL_WORLD_PRACTICE",
                   "INSPIRED_BY","ABOUT","RELATED_NOT_IDENTICAL","DIFFERENT_REFERENT"}
ALLOWED_STATUSES={"review-supported","ambiguous","unresolved","illustrative","unverified"}
ROLE_OWNERS={"media","load","bibliography","standards","linguistics","fiction"}
ADMISSION="proposed"
def stable_review_id(kind:str,key:str)->str:
 if not re.fullmatch(r"[a-z][a-z0-9_-]{1,31}",kind):raise ValueError("bad id kind")
 if not re.fullmatch(r"[a-z0-9][a-z0-9:._-]{2,160}",key):raise ValueError("bad semantic key")
 h=hashlib.sha256((ROOT+"|"+kind+"|"+key).encode("utf-8")).hexdigest()[:24]
 return f"cgx:review-fr:{kind}:{h}"

def normalise(label:str)->str:
 return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9]+"," ",label.casefold())).strip()

def compile_graph(doc:dict[str,Any])->dict[str,Any]:
 if doc.get("schema")!=SCHEMA or doc.get("parent")!=ROOT or doc.get("native_admission") is not False:
  raise ValueError("invalid schema/root/native gate")
 if doc.get("metadata_only") is not True or doc.get("authority")!="REVIEW_ONLY":
  raise ValueError("review authority and metadata only required")
 sources={r["id"]:r for r in doc.get("sources",[])}
 if len(sources)!=len(doc.get("sources",[])):raise ValueError("duplicate source ID")
 for s in sources.values():
  if not s.get("url","").startswith("https://") or s.get("source_bytes_hydrated") is not False:
   raise ValueError("source ref must be HTTPS metadata-only")
  if s.get("sha256") is not None:
   raise ValueError("source bytes not retrieved: digest must be null")
  if not s.get("rights_note"):raise ValueError("source rights note missing")
 nodes=doc.get("nodes",[])
 identities={n["id"]:n for n in nodes}
 if len(nodes)!=len(identities):raise ValueError("duplicate referent ID")
 keys=set()
 for n in nodes:
  if n.get("kind") not in ALLOWED_KINDS or n.get("owner_domain") not in ROLE_OWNERS:
   raise ValueError("unknown node kind/owner")
  if n.get("id")!=stable_review_id("node",n["identity_key"]):raise ValueError("unstable entity ID")
  if n["identity_key"] in keys:raise ValueError("duplicate semantic key")
  keys.add(n["identity_key"])
  if n.get("admission_state")!=ADMISSION or n.get("canonical_object_minted") is not False:
   raise ValueError("review node may not assert native mint")
  if not n.get("facets") or not n.get("title"):raise ValueError("node facets/title missing")
  if not n.get("source_ids") or not set(n["source_ids"])<=set(sources):
   raise ValueError("unproved referent or unknown provenance source")
  if n["kind"]=="fictional_entity" and n["facets"].get("empirical_object") is True:
   raise ValueError("fictional object cannot masquerade as physical real object")
 mentions=doc.get("mentions",[])
 mention_ids={m["id"]:m for m in mentions}
 if len(mentions)!=len(mention_ids):raise ValueError("duplicate mention ID")
 for m in mentions:
  if m.get("id")!=stable_review_id("mention",m["identity_key"]):raise ValueError("unstable mention")
  if m["context_node"] not in identities:raise ValueError("unknown context")
  if m.get("status") not in ALLOWED_STATUSES:raise ValueError("bad mention status")
  if not m.get("source_ids") or not set(m["source_ids"])<=set(sources):
   raise ValueError("unsourced mention")
  candidates=m.get("candidate_ids",[])
  if any(x not in identities for x in candidates):raise ValueError("unknown candidate")
  if len(candidates)!=len(set(candidates)):raise ValueError("duplicate candidate for mention")
  if m["status"]=="unresolved" and candidates:
   raise ValueError("unresolved must not be silently mapped to a publication")
  if m["status"]=="ambiguous" and len(candidates)<2:
   raise ValueError("ambiguous must contain multiple candidates")
 edges=doc.get("edges",[])
 edge_ids=set()
 for e in edges:
  if e.get("type") not in ALLOWED_RELATIONS:raise ValueError("unsupported bridge relationship")
  if e.get("id")!=stable_review_id("edge",e["identity_key"]):raise ValueError("unstable edge")
  if e["id"] in edge_ids:raise ValueError("duplicate edge")
  edge_ids.add(e["id"])
  if e["from"] not in identities and e["from"] not in mention_ids:
   raise ValueError("unknown edge origin")
  if e["to"] not in identities:raise ValueError("unknown edge target")
  if not e.get("assertion_owner") or e.get("admission_state")!=ADMISSION:
   raise ValueError("bridge needs owner and review admission")
  if not e.get("source_ids") or not set(e["source_ids"])<=set(sources):
   raise ValueError("bridge has no valid provenance")
  if e.get("equivalence") in ("owl:sameAs","skos:exactMatch"):
   raise ValueError("cross-world / reference edges must not assert automatic identity equivalence")
  if e.get("authority_transfer") is not False:
   raise ValueError("cross-domain bridge never transfers authority")
  if e.get("claim_scope") not in ("screen_reference","bibliographic","fictional_world","real_world_practice","comparison"):
   raise ValueError("claim must have scoped context")
  if e.get("epistemic_state") not in ALLOWED_STATUSES:
   raise ValueError("unknown epistemic state")
 # The hash deliberately omits volatile read times. Only the candidate metadata matters.
 graph={k:v for k,v in doc.items() if k not in {"graph_sha256","compiled_at"}}
 encoded=json.dumps(graph,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
 result=dict(doc);result["graph_sha256"]=hashlib.sha256(encoded).hexdigest()
 return result

def resolve(graph:dict[str,Any],query:str,*,context_id:str|None=None,limit:int=15)->dict[str,Any]:
 key=normalise(query)
 if not key:raise ValueError("empty lookup")
 nodes={n["id"]:n for n in graph["nodes"]}
 context=nodes.get(context_id)
 if context_id is not None and context is None:raise ValueError("unknown context")
 # In an unscoped query, authoritative referent names are considered before
 # a narrative alias. Otherwise a fictional mention with a shared title
 # silently hides its real-world counterpart.
 if context_id is None:
  direct=[n for n in graph["nodes"] if key in
          {normalise(x) for x in [n["title"],*n.get("aliases",[])]}]
  if direct:
   return {"query":query,"context_id":None,
           "resolution":"review-supported" if len(direct)==1 else "ambiguous",
           "reason":"Shared titles never merge fictional and empirical referents",
           "mention_ids":[],"candidates":[_projection(n) for n in direct][:limit],
           "source_ids":sorted({v for n in direct for v in n["source_ids"]}),
           "native_mint":False}
 matches=[]
 for m in graph["mentions"]:
  if context_id is not None and m["context_node"]!=context_id:continue
  if key in {normalise(x) for x in [m["label"],*m.get("aliases",[])]}:
   matches.append(m)
 if matches:
  candidates={c for m in matches for c in m.get("candidate_ids",[])}
  unresolved=any(m["status"]=="unresolved" for m in matches)
  state="frontier" if unresolved and not candidates else "ambiguous" if len(candidates)>1 else "review-supported"
  reason=("Exact real-world edition not established" if state=="frontier"
          else "Competing referents retained; disambiguation required" if state=="ambiguous"
          else "Reference resolution supported, pending owner acceptance")
  return {"query":query,"context_id":context_id,"resolution":state,"reason":reason,
          "mention_ids":[m["id"] for m in matches],
          "candidates":[_projection(nodes[x]) for x in sorted(candidates)][:limit],
          "source_ids":sorted({s for m in matches for s in m["source_ids"]}),
          "native_mint":False}
 node_matches=[n for n in graph["nodes"] if key in
               {normalise(x) for x in [n["title"],*n.get("aliases",[])]}]
 if node_matches:
  return {"query":query,"context_id":context_id,
          "resolution":"review-supported" if len(node_matches)==1 else "ambiguous",
          "reason":"Context-specific referents are not collapsed by shared title",
          "mention_ids":[],"candidates":[_projection(n) for n in node_matches][:limit],
          "source_ids":sorted({s for n in node_matches for s in n["source_ids"]}),"native_mint":False}
 return {"query":query,"context_id":context_id,"resolution":"frontier",
         "reason":"No source-qualified target in this bounded candidate graph; do not infer nonexistent or fictional",
         "mention_ids":[],"candidates":[],"source_ids":[],"native_mint":False}
def _projection(node:dict[str,Any])->dict[str,Any]:
 return {k:node[k] for k in ("id","title","kind","owner_domain","facets","source_ids")}
def travel(graph:dict[str,Any],start_id:str,*,max_hops:int=3)->dict[str,Any]:
 if max_hops<0 or max_hops>6:raise ValueError("unsafe traversal depth")
 nodes={n["id"]:n for n in graph["nodes"]}
 mentions={m["id"]:m for m in graph["mentions"]}
 if start_id not in nodes and start_id not in mentions:raise ValueError("unknown start")
 adj=defaultdict(list)
 for e in graph["edges"]:adj[e["from"]].append(e)
 visited={start_id};frontier=[(start_id,0)];edges=[]
 while frontier:
  v,depth=frontier.pop(0)
  if depth>=max_hops:continue
  for edge in sorted(adj[v],key=lambda e:e["id"]):
   edges.append({k:edge[k] for k in ("id","from","to","type","claim_scope","source_ids","epistemic_state")})
   if edge["to"] not in visited:
    visited.add(edge["to"]);frontier.append((edge["to"],depth+1))
 return {"start":start_id,"hops":max_hops,"node_ids":sorted(visited),
         "edges":edges,"no_new_mints":True}