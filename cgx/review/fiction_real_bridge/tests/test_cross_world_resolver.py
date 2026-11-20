from __future__ import annotations
import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from bridge_engine import compile_graph,normalise,resolve,stable_review_id,travel

@pytest.fixture()
def graph():
 return json.loads((ROOT/"MIRROR_GRAPH_REVIEW_V2.json").read_text(encoding="utf-8"))

def fid(graph,name):
 return next(x["id"] for x in graph["nodes"] if x["identity_key"]==name)
def get(graph,key):
 return next(x for x in graph["mentions"] if x["identity_key"]==key)

def test_deterministic_hash_and_one_parent(graph):
 v=compile_graph(graph)
 assert v["graph_sha256"]==graph["graph_sha256"]
 assert v["parent"]=="cgx:root:cognigrex"
 assert not v["native_admission"]
 assert all(n["admission_state"]=="proposed" and n["canonical_object_minted"] is False
            for n in v["nodes"])

@pytest.mark.parametrize("key,expected",[
 ("mention:hackers-books-green","frontier"),
 ("mention:hackers-books-orange","review-supported"),
 ("mention:hackers-books-pink","review-supported"),
 ("mention:hackers-books-devil","review-supported"),
 ("mention:hackers-books-dragon","review-supported"),
 ("mention:hackers-books-red","ambiguous"),
])
def test_six_film_references_are_qualified(graph,key,expected):
 m=get(graph,key)
 r=resolve(graph,m["label"],context_id=m["context_node"])
 assert r["resolution"]==expected
 assert r["native_mint"] is False

def test_green_unknown_is_not_false_or_fictional(graph):
 m=get(graph,"mention:hackers-books-green")
 r=resolve(graph,"International UNIX Environments",context_id=m["context_node"])
 assert r["resolution"]=="frontier" and not r["candidates"]
 assert len(r["source_ids"])>=1

def test_red_conflation_retains_two_real_referents(graph):
 m=get(graph,"mention:hackers-books-red")
 r=resolve(graph,"Red Book",context_id=m["context_node"])
 assert len(r["candidates"])==2
 names={x["title"] for x in r["candidates"]}
 assert any("Trusted Network Interpretation" in t for t in names)
 assert any("POSIX" in t for t in names)
 assert len({x["id"] for x in r["candidates"]})==2
 assert all(x["facets"]["empirical_work"] for x in r["candidates"])

def test_hitchhikers_same_title_never_auto_merges(graph):
 r=resolve(graph,"The Hitchhiker's Guide to the Galaxy")
 assert r["resolution"]=="ambiguous"
 assert len(r["candidates"])==2
 assert {x["kind"] for x in r["candidates"]}=={"fictional_entity","real_work"}
 assert len({x["id"] for x in r["candidates"]})==2

def test_hitchhikers_in_world_context_picks_diegetic_guide(graph):
 novel=fid(graph,"book:adams-hitchhikers-guide-1979")
 r=resolve(graph,"Hitchhiker's Guide",context_id=novel)
 assert r["resolution"]=="review-supported" and len(r["candidates"])==1
 assert r["candidates"][0]["kind"]=="fictional_entity"

def test_real_constructed_language_crosses_world_usage_not_physical_species(graph):
 k=resolve(graph,"Klingon language")
 assert k["resolution"]=="review-supported"
 assert len(k["candidates"])==1
 f=k["candidates"][0]["facets"]
 assert f["fictional_origin"] and f["real_world_usage"] and f["spoken_by_humans"]
 assert f["not_evidence_of_fictional_species"]

def test_unknown_is_frontier_not_invented_placeholder(graph):
 x=resolve(graph,"Totally Unknown Storybook I Just Invented")
 assert x["resolution"]=="frontier" and x["candidates"]==[]

def test_cross_domain_edges_never_transfer_authority(graph):
 assert graph["edges"] and all(e["authority_transfer"] is False for e in graph["edges"])
 assert all(e["admission_state"]=="proposed" for e in graph["edges"])
 assert all(e["equivalence"] is None for e in graph["edges"])

def test_forbid_incorrect_owl_sameas(graph):
 bad=copy.deepcopy(graph);bad["edges"][0]["equivalence"]="owl:sameAs"
 with pytest.raises(ValueError,match="identity equivalence"):
  compile_graph(bad)

def test_forged_source_locator_rejected(graph):
 bad=copy.deepcopy(graph);bad["sources"][0]["sha256"]="0"*64
 with pytest.raises(ValueError,match="digest must be null"):
  compile_graph(bad)

def test_missing_edge_provenance_rejected(graph):
 bad=copy.deepcopy(graph);bad["edges"][0]["source_ids"]=[]
 with pytest.raises(ValueError,match="no valid provenance"):
  compile_graph(bad)

def test_missing_source_referent_rejected(graph):
 bad=copy.deepcopy(graph);bad["nodes"][0]["source_ids"]=["invented"]
 with pytest.raises(ValueError,match="unproved referent"):
  compile_graph(bad)

def test_unresolved_must_have_no_binding(graph):
 bad=copy.deepcopy(graph)
 m=next(x for x in bad["mentions"] if x["status"]=="unresolved")
 m["candidate_ids"]=[bad["nodes"][1]["id"]]
 with pytest.raises(ValueError,match="unresolved must not"):
  compile_graph(bad)

def test_malformed_context_fails_without_expansion(graph):
 with pytest.raises(ValueError,match="unknown context"):
  resolve(graph,"Dragon Book",context_id="cgx:fake:domain")

def test_travel_uses_edge_ids_without_any_mint(graph):
 m=get(graph,"mention:hackers-books-red")
 r=travel(graph,m["id"],max_hops=2)
 assert r["no_new_mints"]
 assert len(r["node_ids"])==3
 assert len(r["edges"])==2
 assert len({e["id"] for e in r["edges"]})==2

def test_travel_bound_enforced(graph):
 with pytest.raises(ValueError,match="unsafe"):
  travel(graph,graph["nodes"][0]["id"],max_hops=99)

def test_duplicate_node_identity_rejected(graph):
 bad=copy.deepcopy(graph);bad["nodes"].append(copy.deepcopy(bad["nodes"][0]))
 with pytest.raises(ValueError,match="duplicate referent"):
  compile_graph(bad)

def test_normalisation_is_linguistic_alias_not_identity_proof():
 assert normalise("  The Dragon-Book!")=="the dragon book"
 assert stable_review_id("node","book:dragon-1986")!=stable_review_id("node","book:dragon-1977")

def test_no_copy_of_external_page_bodies(graph):
 assert all(not s["source_bytes_hydrated"] and s["sha256"] is None for s in graph["sources"])
 assert graph["metadata_only"] is True


def test_constructed_language_one_identity_with_real_practice_crossing(graph):
 lang=fid(graph,"language:klingon-marc-okrands-conlang")
 practice=fid(graph,"practice:klingon-human-speakers")
 assert lang != practice
 paths=[e for e in graph["edges"] if e["from"]==lang and e["to"]==practice]
 assert len(paths)==1 and paths[0]["type"]=="HAS_REAL_WORLD_PRACTICE"
 assert paths[0]["source_ids"]==["klingon-institute"]
 assert paths[0]["authority_transfer"] is False
 journey=travel(graph,lang,max_hops=1)
 assert practice in journey["node_ids"] and journey["no_new_mints"]
 assert sum(n["identity_key"]=="language:klingon-marc-okrands-conlang" for n in graph["nodes"])==1
