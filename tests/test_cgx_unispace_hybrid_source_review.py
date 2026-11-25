"""Single-root CGX source-hybridisation regression tests."""
import json
import unittest
from copy import deepcopy
import hashlib
from tools.cgx_unispace_hybrid_source_review import HybridHold
from tools.cgx_unispace_crossspace_review import CrossSpaceHold
from pathlib import Path
from tools.cgx_unispace_hybrid_source_review import compose, HybridHold
from tools.cgx_unispace_branch_convergence import ConvergenceHold
from tools.cgx_unispace_overlap_review import OverlapHold

BASE = Path(__file__).resolve().parents[1] / "cgx/review"

def real():
    pr=json.loads((BASE/"unispace_git_pr_source_snapshot_20261122.json").read_text("utf-8"))
    overlap=json.loads((BASE/"unispace_source_path_overlap_20261122.json").read_text("utf-8"))
    return pr,overlap

def gate():
    return {"schema":"CGX-UNISPACE-CROSSSPACE-GATE-REGISTRY/0.1",
            "canonical_root":"cgx:root:cognigrex","source_count":51,
            "task_groups":[{"id":f"G-{i:02}","space":"FileSpace",
                            "state":"OPEN_REVIEW_ONLY","owner_approval_observed":False,
                            "effectful_action_authorised":False,
                            "proposed_dependencies":[]} for i in range(51)]}

def observed():
    return {"schema":"CGX-AUTOMATION-ARCHIVE-OBSERVATIONS/0.1",
            "canonical_root":"cgx:root:cognigrex","observations":[]}

def original_gates():
    p=Path(__file__).resolve().parents[1]/"cgx/review/unispace_crossspace_gate_register_v0_1.json"
    raw=p.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()

def synthetic_source_mesh():
    """Source-contract shape fixture; independently built real mesh is checked by CI."""
    ids=("file_space","data_space","social_space","print_space","intelligence_space")
    return {"mesh":{
        "schema":"CGX-UNISPACE-SINGLE-ROOT-FACET-MESH/0.1",
        "canonical_root_id":"cgx:root:cognigrex",
        "state":"SOURCE_CONTRACT_MESH_OBSERVED",
        "facet_count":5,"unique_contract_count":12,"unique_service_count":7,
        "new_root_created":False,"new_database_created":False,
        "model_weights_modified":False,"native_execution_authorized":False,
        "mint_or_network_authorized":False,"source_hydration_performed":False,
        "facets":[{"id":id,"state":"SOURCE_CONTRACTS_PRESENT",
                   "execution_authorized":False,"independent_native_admission":False}
                  for id in ids]
    }}

class HybridSourceTests(unittest.TestCase):
    def test_real_sources_one_canonical_parent(self):
        p,f=real();a=compose(p,f)
        self.assertEqual(a["canonical_root"],"cgx:root:cognigrex")
        self.assertEqual(a["open_pr_records"],74)
        self.assertEqual(a["overlap_pairs"],5)
        self.assertEqual(len(a["facets"]),5)
        self.assertFalse(a["native_dbr_performed"])
        self.assertFalse(a["merge_performed"])
        self.assertFalse(a["model_trained"])

    def test_closed_gui_candidate_is_not_new_authority(self):
        p,f=real();a=compose(p,f)
        self.assertIn(235,a["historic_prs_in_comparison"])
        self.assertFalse(a["publish_performed"])

    def test_stale_review_snapshot_reported_not_silent(self):
        p,f=real();a=compose(p,f)
        self.assertIn("PINNED_HEAD_PARITY",{x["id"] for x in a["pending_conditions"]})
        self.assertIn(230,[x["pr"] for x in a["source_head_mismatches"]])

    def test_missing_automation_history_explicit(self):
        p,f=real();a=compose(p,f)
        self.assertIn("AUTOMATION_HISTORY",{x["id"] for x in a["pending_conditions"]})

    def test_present_empty_automation_not_claimed_complete(self):
        p,f=real();a=compose(p,f,observations=observed())
        self.assertIsNotNone(a["source_reviews"]["automation_review_sha256"])
        self.assertFalse(a["historic_automation_run_history_complete"])

    def test_canonical_gate_register_merges_only_as_review(self):
        p,f=real();a=compose(p,f,gates=gate())
        self.assertEqual(a["cross_space_gates_read_back"],51)
        self.assertNotIn("CROSSSPACE_REGISTER",{x["id"] for x in a["pending_conditions"]})
        self.assertFalse(a["native_dbr_performed"])

    def test_gate_promotion_prohibited(self):
        p,f=real();g=gate();g["task_groups"][0]["owner_approval_observed"]=True
        with self.assertRaises(ConvergenceHold):compose(p,f,gates=g)

    def test_duplicate_pr_fails(self):
        p,f=real();p["records"].append(deepcopy(p["records"][0]))
        p["total_open_prs"]+=1
        with self.assertRaises(ConvergenceHold):compose(p,f)

    def test_source_path_tamper_fails(self):
        p,f=real();f["overlapping_pairs"]=[]
        with self.assertRaises(OverlapHold):compose(p,f)

    def test_no_secondary_root(self):
        p,f=real();f["canonical_root"]="cgx:root:another"
        with self.assertRaises(OverlapHold):compose(p,f)

    def test_review_receipt_reproducible(self):
        p,f=real()
        self.assertEqual(compose(p,f)["review_sha256"],compose(p,f)["review_sha256"])


    def test_exact_original_register_is_bound_to_existing_mesh_shape(self):
        p,f=real()
        g,sha=original_gates()
        result=compose(p,f,gates=g,source_mesh=synthetic_source_mesh(),
                       source_register_sha256=sha)
        self.assertTrue(result["exact_crossspace_mesh_bound"])
        self.assertEqual(result["original_crossspace_review"]["task_count"],51)
        self.assertEqual(result["original_crossspace_review"]["source_mesh_observed"],True)
        self.assertFalse(result["original_crossspace_review"]["native_admitted"])

    def test_wrong_source_bytes_digest_is_held(self):
        p,f=real()
        g,_=original_gates()
        with self.assertRaises(HybridHold):
            compose(p,f,gates=g,source_mesh=synthetic_source_mesh(),
                    source_register_sha256="0"*64)

    def test_crossspace_mesh_wrong_root_fails_closed(self):
        p,f=real();g,sha=original_gates()
        mesh=synthetic_source_mesh()
        mesh["mesh"]["canonical_root_id"]="cgx:root:unauthorised"
        with self.assertRaises(CrossSpaceHold):
            compose(p,f,gates=g,source_mesh=mesh,source_register_sha256=sha)

    def test_mesh_without_original_registry_is_held(self):
        p,f=real()
        with self.assertRaises(HybridHold):
            compose(p,f,source_mesh=synthetic_source_mesh())

    def test_registry_only_source_review_remains_not_mesh_qualified(self):
        p,f=real();g,_=original_gates()
        item=compose(p,f,gates=g)
        self.assertFalse(item["exact_crossspace_mesh_bound"])
        self.assertIn("SOURCE_FACET_MESH",{x["id"] for x in item["pending_conditions"]})

if __name__=="__main__":
    unittest.main()
