"""Source-lineage and review-only contracts for the opt-in PR173 observer fold."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"desktop/LightSpeed_Runtime"))
from lightspeed_runtime.node_exchange import project_rolling_observer_window

def get(path):return json.loads((ROOT/path).read_text(encoding="utf-8"))

class ObserverFacetConvergenceTests(unittest.TestCase):
    def test_exact_seven_owner_blobs(self):
        index=get("cgx/review/observer_facet_subset_fold_20261020.json")
        self.assertEqual(index["source_pr"],173)
        self.assertEqual(len(index["carried_source_files"]),7)
        for rec in index["carried_source_files"]:
            raw=(ROOT/rec["path"]).read_bytes()
            digest=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
            self.assertEqual(digest,rec["git_blob_sha1"],rec["path"])
    def test_current_desktop_source_manifest_keeps_intake_identity_and_observer(self):
        d=get("desktop/source-manifest.json")
        m={x["path"]:x for x in d["records"]}
        self.assertEqual(len(m),735)
        for path in [
            "LightSpeed_Runtime/lightspeed_runtime/cgx_object_context.py",
            "LightSpeed_Runtime/lightspeed_runtime/cgx_intake_projection.py",
            "LightSpeed_Runtime/lightspeed_runtime/node_exchange.py"
        ]:
            f=ROOT/"desktop"/path
            data=f.read_bytes()
            self.assertEqual(m[path]["bytes"],len(data))
            self.assertEqual(m[path]["sha256"],hashlib.sha256(data).hexdigest())
    def test_n_observer_cannot_cryptographically_attest_itself(self):
        kwargs={"object_id":"cgx:test:reader","geometry_root":"a"*64,"semantic_root":"a"*64,
                "model_root":"a"*64,"prior_state_root":"a"*64,
                "selected_nodes":["alpha","beta","gamma"],"end_ms":60000}
        samples=[
          {"observer_id":n,"independence_group":g,"timestamp_ms":60000,
           "state":1,"receipt_verified":True}
          for n,g in zip(["alpha","beta","gamma"],["x","y","z"])
        ]
        v=project_rolling_observer_window(**kwargs,samples=samples)
        self.assertEqual(len(v["lenses"]),9)
        self.assertFalse(v["cryptographically_authenticated_by_this_function"])
        self.assertFalse(v["canonical_promotion_authorized"])
        self.assertFalse(v["physical_actuation_authorized"])
    def test_fkc_contract_never_acts_as_an_authority_token(self):
        x=get("cgx/domain_templates/node_exchange_contract.json")
        d=get("cgx/domain_templates/depth_profiles.json")
        names=[t["id"] for t in d["hydration_planes"]]
        f=x["hydration_and_fract_key_contract"]
        self.assertEqual(names,f["plane_order"])
        self.assertEqual(len(names),10)
        self.assertEqual(f["fract_key"]["code_prefix"],"FK1")
        self.assertFalse(f["canonical_mutation"])
        self.assertFalse(f["public_release"])
        self.assertFalse(f["physical_authority"])
        self.assertIn("NOT_CACHED",f["scatter_gather"]["unknown_rule"])
    def test_sai_retains_original_cgx_parent_and_all_release_gates(self):
        topology=get("cgx/domain_templates/cognigrex_parent_topology.json")
        self.assertEqual(topology["root"]["file"],"Cognigrex.cgx")
        self.assertEqual(topology["programme_authority_crosswalk"]["release_status"],"REVIEW_HOLD")
        x=get("cgx/domain_templates/node_exchange_contract.json")
        self.assertTrue(x["sai_aus_capacity_application"]["no_public_auto_release"])
        self.assertFalse(x["configurable_n_dataspace_facet"]["canonical_promotion_authorized"])

if __name__=="__main__": unittest.main()
