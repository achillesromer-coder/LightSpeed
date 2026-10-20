"""UniSpace cross-family source convergence assertions; candidate only."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
def load(path):
    path = ROOT / path
    spec=importlib.util.spec_from_file_location(path.stem,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

node=load("cgx/portable_node/passive_node_plan.py")
keys=load("cgx/portable_node/keyed_fileset_plan.py")
archive=load("cgx/portable_node/archive_claim_reconciliation_plan.py")
from cgx.manufacturing.modular_facility_packing import compile_facility
from cgx.manufacturing.modular_deployment_logistics import build_deployment_review
from cgx.manufacturing.modular_facility_projection import render_svg

class UniSpaceFoldConvergence(unittest.TestCase):
    def test_provenance_preserves_original_22_blob_hashes(self):
        index=json.loads((ROOT/"cgx/review/unispace_source_fold_manifest_20261020.json").read_text(encoding="utf-8"))
        self.assertEqual(index["source_prs"],[179,180,181])
        self.assertEqual(len(index["files"]),22)
        self.assertEqual(len({f["path"] for f in index["files"]}),22)
        for f in index["files"]:
            with self.subTest(source_pr=f["source_pr"],path=f["path"]):
                raw=(ROOT/f["path"]).read_bytes()
                gitblob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
                self.assertEqual(gitblob,f["git_blob_sha1"])

    def test_one_exact_blob_two_source_references_no_promotion(self):
        f=ROOT/"cgx/manufacturing/fixtures/five_unit_relief_synthetic_v0_1.json"
        raw=f.read_bytes()
        h=hashlib.sha256(raw).hexdigest()
        component=lambda name:{"source_id":name,"sha256":h,"byte_length":len(raw),"redistribution":"UNVERIFIED"}
        inp={"schema":"CGX-FILESET-SOURCE-PROPOSAL/0.1",
            "fileset_id":"cgx:review:five-unit-public-index","audience":"PUBLIC",
            "mode":"REFERENCES_ONLY",
            "components":[component("cgx:review:geometry"),component("cgx:review:composite")]}
        out=keys.propose_fileset(inp)
        self.assertEqual(out["unique_blob_count"],1)
        self.assertEqual(out["source_reference_count"],2)
        self.assertEqual(out["declared_unique_source_bytes"],len(raw))
        self.assertFalse(out["delivery_ready"])
        with self.assertRaises(ValueError):
            inp["mode"]="PUBLIC_OFFLINE_PACK"
            keys.propose_fileset(inp,proven_local_hashes=[h])

    def test_no_device_discovery_or_authority_via_public_fileset(self):
        p=node.plan_passive_node("WEB_CONNECTED",budget_bytes=65536,origin="https://cgx.example.org")
        self.assertFalse(p["connected"])
        self.assertEqual(p["eligibility"],"HOLD_SERVER_AUTH_SESSION")
        self.assertFalse(p["authority_transfer"])
        self.assertIsNone(p["node_id"])

    def test_synthetic_facility_stays_unqualified_despite_complete_projection(self):
        fixture=json.loads((ROOT/"cgx/manufacturing/fixtures/five_unit_relief_synthetic_v0_1.json").read_text(encoding="utf-8"))
        out=compile_facility(fixture)
        logistics=build_deployment_review(fixture)
        ET.fromstring(render_svg(fixture))
        self.assertEqual(out["unit_count"],5)
        self.assertFalse(out["shipment_authorised"])
        self.assertFalse(logistics["qualified_operational_delivery"])
        self.assertTrue(any("HOLD_SITE_TOPOGRAPHY" in x for x in out["holds"]))
        self.assertEqual(sum(x["distinct_instance_count"] for x in logistics["bill_of_materials"]),10)

    def test_archive_contradiction_retained_as_frontier_not_manifest_rewrite(self):
        v={"claim_id":"a","source_ref":"source:a","sha256":"a"*64,
           "object_id":"cgx:component:1","field":"mass","unit":"kg","value":12}
        w=dict(v,claim_id="b",source_ref="source:b",sha256="b"*64,value=13)
        out=archive.classify_claim_pair(v,w)
        self.assertEqual(out["classification"],"CONTRADICTORY_HOLD")
        self.assertTrue(out["preserve_originals"])
        self.assertFalse(out["promote_canon"])

    def test_catalogue_remains_reference_only_and_no_source_relicensing(self):
        d=json.loads((ROOT/"cgx/review/alexandria_external_reference_intake_20261020.json").read_text(encoding="utf-8"))
        self.assertEqual(len(d["groups"]),2)
        self.assertEqual(sum(x["source_lines"] for x in d["groups"]),207)
        self.assertTrue(all(r["rights"]=="UPSTREAM_LICENSE_UNVERIFIED" for g in d["groups"] for r in g["records"]))

if __name__=="__main__":
    unittest.main()
