"""Typed, non-executing LOAD/CCC routing for cross-world mirrors.
A reference can reveal a *capability request*, not automatically execute one.
"""
from __future__ import annotations
from hashlib import sha256
import json
from typing import Any

ALLOWED_INTENTS={"identify","inspect_bibliography","inspect_provenance","learn_language",
                 "read_full_text","machine_train","simulate_or_execute"}
RULES={
 "identify":{"capability":"load.identity_resolver","read_only":True,"requires_rights":False},
 "inspect_bibliography":{"capability":"load.catalog_locator","read_only":True,"requires_rights":False},
 "inspect_provenance":{"capability":"oracle.source_provenance","read_only":True,"requires_rights":False},
 "learn_language":{"capability":"linguistics.learning_route","read_only":True,"requires_rights":True},
 "read_full_text":{"capability":"load.licensed_hydration","read_only":False,"requires_rights":True},
 "machine_train":{"capability":"smith.model_training_workflow","read_only":False,"requires_rights":True},
 "simulate_or_execute":{"capability":"ls.typed_simulation","read_only":False,"requires_rights":True}
}
def plan_request(graph:dict[str,Any],target_id:str,intent:str,*,viewer_domain="unispace")->dict[str,Any]:
 if intent not in ALLOWED_INTENTS:raise ValueError("unknown capability")
 if viewer_domain not in {"unispace","fiction","media","bibliography","load","standards","linguistics"}:
  raise ValueError("untrusted viewer domain")
 matches=[n for n in graph["nodes"] if n["id"]==target_id]
 if len(matches)!=1:raise ValueError("referent unresolved or not unique")
 n=matches[0]
 rule=RULES[intent]
 evidence=list(dict.fromkeys(n["source_ids"]))
 if not evidence:raise ValueError("unproven referent")
 if intent=="learn_language" and (n["kind"]!="constructed_language" or
                                  n.get("facets",{}).get("real_world_usage") is not True):
  raise ValueError("language practice requires documented living usage")
 if intent=="simulate_or_execute" and n["kind"] in {"fictional_entity","creative_work"}:
  # A fictional construct may inform a separately authored real-world simulation,
  # but never becomes hardware or an executable capability automatically.
  state="BLOCKED_REQUIRES_NEW_INDEPENDENT_IMPLEMENTATION"
 elif intent in {"read_full_text","machine_train","simulate_or_execute"}:
  state="RIGHTS_AND_SIGNED_EXECUTION_LEASE_REQUIRED"
 elif intent=="learn_language":
  state="REFERENCE_AVAILABLE_PRACTICE_CONTENT_NOT_LICENSED"
 else:state="METADATA_REFERENCE_ONLY"
 packet={"schema":"CGX-CCC-CROSS-DOMAIN-ROUTE/0.1","parent":graph["parent"],
  "source_graph_sha256":graph["graph_sha256"],"referent_id":n["id"],
  "source_owner":n["owner_domain"],"requesting_domain":viewer_domain,
  "intent":intent,"typed_capability":rule["capability"],
  "candidate_source_ids":evidence,"data_use":state,
  "rights_review_required":rule["requires_rights"],
  "native_mint_authorized":False,"tool_dispatch_authorized":False,
  "source_text_hydrated":False,"semantic_claim_accepted":False,
  "authority_transfer":False,"model_training_started":False}
 packet["packet_sha256"]=sha256(json.dumps(packet,sort_keys=True,separators=(",",":")).encode()).hexdigest()
 return packet

def plan_one_mint_per_referent(graph:dict[str,Any],object_ids:list[str])->dict[str,Any]:
 """Return only a deduplicated *candidate* plan, never a mint action."""
 unique=sorted(set(object_ids))
 if len(unique)!=len(object_ids):
  # Duplicate references are allowed; the mint plan explicitly deduplicates them.
  pass
 nodes={n["id"]:n for n in graph["nodes"]}
 if any(x not in nodes for x in unique):raise ValueError("unverified object ID")
 candidates=[]
 for ref in unique:
  node=nodes[ref]
  inbound=[e["id"] for e in graph["edges"] if e["to"]==ref]
  candidates.append({"referent_id":ref,"title":node["title"],"owner_domain":node["owner_domain"],
    "evidence_locator_ids":node["source_ids"],"referenced_from_edge_count":len(inbound),
    "mint_state":"NOT_MINTED","root_signed_authority_required":True,
    "new_canonical_id_assignment":"DEFER_TO_AUTHORITATIVE_ROOT_REGISTRY",
    "data_rights_review_required":True})
 result={"schema":"CGX-ONE-MINT-MANY-USES-CANDIDATE/0.1","parent":graph["parent"],
         "graph_sha256":graph["graph_sha256"],"identities":candidates,
         "input_reference_count":len(object_ids),"unique_referents":len(unique),
         "duplicate_mint_count":0,"native_objects_written":0,
         "signed_root_lease_present":False,"db_mutation_authorized":False}
 return result