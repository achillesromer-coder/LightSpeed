from __future__ import annotations
import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from capability_router import plan_request,plan_one_mint_per_referent
from bridge_engine import resolve

@pytest.fixture()
def graph():
 return json.loads((ROOT/"MIRROR_GRAPH_REVIEW_V2.json").read_text(encoding="utf-8"))

def node(graph,key):
 return next(x for x in graph["nodes"] if x["identity_key"]==key)

def test_bibliography_lookup_is_reference_only(graph):
 n=node(graph,"book:leffler-design-4.3bsd-1989")
 r=plan_request(graph,n["id"],"inspect_bibliography",viewer_domain="media")
 assert r["data_use"]=="METADATA_REFERENCE_ONLY"
 assert not r["source_text_hydrated"] and not r["tool_dispatch_authorized"]
 assert r["typed_capability"]=="load.catalog_locator"

def test_packet_hash_is_deterministic(graph):
 n=node(graph,"standard:ncsc-tg-005-1987")
 a=plan_request(graph,n["id"],"inspect_provenance")
 b=plan_request(graph,n["id"],"inspect_provenance")
 assert a==b and len(a["packet_sha256"])==64

def test_fictional_technology_does_not_become_executable(graph):
 n=node(graph,"fictional-entity:hitchhikers-electronic-guide")
 x=plan_request(graph,n["id"],"simulate_or_execute")
 assert x["data_use"]=="BLOCKED_REQUIRES_NEW_INDEPENDENT_IMPLEMENTATION"
 assert not x["tool_dispatch_authorized"]

def test_language_learning_is_real_practice_but_content_rights_gated(graph):
 n=node(graph,"language:klingon-marc-okrands-conlang")
 x=plan_request(graph,n["id"],"learn_language")
 assert x["data_use"]=="REFERENCE_AVAILABLE_PRACTICE_CONTENT_NOT_LICENSED"
 assert x["rights_review_required"] and not x["source_text_hydrated"]

def test_real_book_cannot_be_automatically_trained(graph):
 n=node(graph,"book:norton-ibm-pc-1985")
 x=plan_request(graph,n["id"],"machine_train")
 assert x["data_use"]=="RIGHTS_AND_SIGNED_EXECUTION_LEASE_REQUIRED"
 assert not x["model_training_started"] and not x["native_mint_authorized"]

def test_fictional_guide_cannot_pretend_to_be_spoken_language(graph):
 n=node(graph,"fictional-entity:hitchhikers-electronic-guide")
 with pytest.raises(ValueError,match="language practice"):
  plan_request(graph,n["id"],"learn_language")

def test_scoped_domain_validation(graph):
 n=graph["nodes"][0]
 with pytest.raises(ValueError,match="untrusted viewer"):
  plan_request(graph,n["id"],"identify",viewer_domain="unknown_remote_root")

def test_unverified_referent_cannot_be_minted(graph):
 with pytest.raises(ValueError,match="unverified"):
  plan_one_mint_per_referent(graph,["cgx:invented:ref"])

def test_duplicate_mentions_do_not_create_duplicate_objects(graph):
 posix=node(graph,"standard:ieee-1003.1-1990")
 tni=node(graph,"standard:ncsc-tg-005-1987")
 p=plan_one_mint_per_referent(graph,[posix["id"],tni["id"],posix["id"],posix["id"]])
 assert p["input_reference_count"]==4
 assert p["unique_referents"]==2
 assert len(p["identities"])==2
 assert p["duplicate_mint_count"]==0 and p["native_objects_written"]==0
 assert next(x for x in p["identities"] if x["referent_id"]==posix["id"])["referenced_from_edge_count"]>=2

def test_unknown_reference_remains_frontier_not_proposal_to_mint(graph):
 r=resolve(graph,"Unknown Engineering Manual",context_id=None)
 assert r["resolution"]=="frontier" and r["candidates"]==[]
 p=plan_one_mint_per_referent(graph,[])
 assert not p["identities"] and p["native_objects_written"]==0

def test_unlisted_action_fails_closed(graph):
 with pytest.raises(ValueError,match="unknown capability"):
  plan_request(graph,graph["nodes"][0]["id"],"financial_issuance")

def test_missing_provenance_fails_closed(graph):
 modified=copy.deepcopy(graph)
 modified["nodes"][0]["source_ids"]=[]
 with pytest.raises(ValueError,match="unproven referent"):
  plan_request(modified,modified["nodes"][0]["id"],"identify")

def test_full_text_requires_separate_rights(graph):
 n=node(graph,"book:aho-sethi-ullman-compilers-1986")
 r=plan_request(graph,n["id"],"read_full_text")
 assert r["rights_review_required"] and not r["source_text_hydrated"]
 assert r["data_use"]=="RIGHTS_AND_SIGNED_EXECUTION_LEASE_REQUIRED"