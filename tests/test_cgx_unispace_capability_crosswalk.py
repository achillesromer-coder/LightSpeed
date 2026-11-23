"""Review-only LOAD/Alexandria <> PrintSpace one-root capability crosswalk."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools.cgx_unispace_capability_crosswalk import (
    ROOT, SOURCE_SPECS, CrosswalkHold, _file_bytes, build, validate_contracts,
)

def fixture():
    documents = {}
    for key, (path, *_rest) in SOURCE_SPECS.items():
        documents[key] = json.loads((ROOT/path).read_text(encoding="utf-8"))
    registry = json.loads(
        (ROOT/"cgx/review/unispace_crossspace_gate_register_v0_1.json").read_text("utf-8"))
    return documents, registry

class CapabilityCrosswalkTests(unittest.TestCase):
    def test_exact_source_git_blob_readback(self):
        report = build(ROOT)
        self.assertEqual(report["canonical_root"], "cgx:root:cognigrex")
        self.assertEqual(report["status"], "SOURCE_ONLY_CAPABILITY_FOLD_NOT_NATIVE_ADMISSION")
        self.assertEqual(len(report["source_contracts"]),5)
        self.assertEqual(report["gate_register_sha256"],
            "748c18632d6e2ce0a685da5498d83ed585cfc1f5af8b1658eec2128db82403a1")
        self.assertFalse(report["native_dbr_performed"])
        self.assertFalse(report["archive_deleted"])
        self.assertFalse(report["published"])

    def test_existing_root_and_source_action_set(self):
        docs,gates=fixture()
        report=validate_contracts(docs,gates)
        self.assertEqual(report["library"]["alias"],"LOAD.cgx")
        self.assertEqual(len(report["library"]["actions"]),10)
        self.assertTrue(all(not a["execution_authorised"] for a in report["library"]["actions"]))
        self.assertEqual(report["library"]["hydration_stages"],["h0","h1","h2","h3","h4"])

    def test_original_printspace_gates_remain_open(self):
        docs,gates=fixture()
        report=validate_contracts(docs,gates)
        self.assertEqual(len(report["manufacturing"]["workstreams"]),16)
        self.assertEqual(report["manufacturing"]["physical_proof"],"UNMEASURED")
        self.assertTrue(report["gate_groups_all_open"])
        self.assertFalse(report["manufacturing"]["independent_software_acceptance"])
        self.assertFalse(report["manufacturing"]["real_print_executed"])

    def test_readout_is_deterministic(self):
        self.assertEqual(build(ROOT)["review_sha256"],build(ROOT)["review_sha256"])

    def test_reject_load_identity_mint(self):
        d,r=fixture();d["load_activation"]["canonical_object_id"]="cgx:minted:secret"
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_load_parent_alias_duplicate(self):
        d,r=fixture();d["load_catalogue"]["alias"]["one_instance_reference_binding"]=False
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_load_network_fetch_activation(self):
        d,r=fixture();d["load_activation"]["network_fetch"]="ALLOW_ALL"
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_implicit_load_execution(self):
        d,r=fixture();d["load_catalogue"]["actions"]["load.attach"]["mode"]="execute"
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_load_action_census_change(self):
        d,r=fixture();d["load_catalogue"]["actions"]["new.privileged"]={"mode":"read","label":"unsafe","targets":["filespace"]}
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_foreign_viewport_root(self):
        d,r=fixture();d["load_viewport"]["authority"]["root"]="Different.cgx"
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_expanded_compute_ceiling(self):
        d,r=fixture();d["load_viewport"]["default_budget"]["max_nodes"]=999999
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_printer_release(self):
        d,r=fixture();d["print_handoff"]["conclusions"]["unispace_launch_authorised"]=True
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_new_scheduler(self):
        d,r=fixture();d["print_handoff"]["automation_mode"]["new_scheduler_allowed"]=True
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_material_claim(self):
        d,r=fixture();d["print_handoff"]["conclusions"]["physical_product_qualified"]=True
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_print_workstream_promotion(self):
        d,r=fixture();d["print_handoff"]["open_workstreams"][0]["independently_verified"]=True
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_physical_witness_promotion(self):
        d,r=fixture();d["print_witness"]["evidence_state"]="MEASURED"
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_machine_ir_configuration_claim(self):
        d,r=fixture();d["print_witness"]["manufacturing_ir_configuration_hash"]="0"*64
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_print_witness_forged_digest(self):
        d,r=fixture();d["print_witness"]["region_selections"][0]["directional_sha256"]="not-a-digest"
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_reject_duplicate_crossspace_task(self):
        d,r=fixture();r["task_groups"][0]["id"]=r["task_groups"][1]["id"]
        with self.assertRaises(ValueError):validate_contracts(d,r)

    def test_missing_contract_held(self):
        d,r=fixture();del d["print_witness"]
        with self.assertRaises(CrosswalkHold):validate_contracts(d,r)

    def test_blob_drift_is_held(self):
        path,_,_,_=SOURCE_SPECS["load_activation"]
        with self.assertRaises(CrosswalkHold):
            _file_bytes(ROOT,path,"f"*40,{path})

    def test_original_families_not_duplicated(self):
        obj=build(ROOT)
        self.assertTrue(obj["single_root"])
        self.assertTrue(obj["no_new_scheduler"])
        self.assertFalse(obj["source_bytes_hydrated"])
        self.assertFalse(obj["trained"])

if __name__=="__main__":
    unittest.main()
