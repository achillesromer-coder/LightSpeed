"""CGX integration: registered library coverage vs independently proven capability."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PROJECTION=ROOT/"cgx"/"review"/"library_coverage_projection.py"
RESOLVER=ROOT/"desktop"/"LightSpeed_Runtime"/"lightspeed_runtime"/"cgx_object_context.py"

def load_module(path):
    spec=importlib.util.spec_from_file_location(path.stem,path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

catalogue=load_module(PROJECTION)
resolver=load_module(RESOLVER)

class LibraryIdentityConvergenceTests(unittest.TestCase):
    def test_core_library_sizes_derive_from_actual_registries(self):
        p=catalogue.build_library_coverage(ROOT)
        c=p["counts"]
        self.assertEqual(c["declared_file_profiles"],33)
        self.assertEqual(c["total_distinct_lenses"],34)
        self.assertEqual(c["bridge_types"],8)
        self.assertEqual(c["toolkits"],12)
        self.assertEqual(c["registered_capability_routes"],49)
        self.assertEqual(c["semantic_classes"],54)
        self.assertEqual(c["durable_source_families"],21)
        self.assertEqual(c["external_index_entries"],207)
        self.assertEqual(c["passive_edge_profiles"],5)
        self.assertEqual(c["first_file_mappings"],19)
        self.assertEqual(c["volumetric_kernels"],40)
        self.assertEqual(c["physical_instance_classes"],5)
    def test_no_public_or_runtime_claims_are_implicitly_promoted(self):
        p=catalogue.build_library_coverage(ROOT)
        self.assertEqual(p["status"],"DERIVED_READ_ONLY_NOT_AUTHORITY_NOT_LIVE_CAPABILITY_PROOF")
        self.assertTrue(all(not v["live_probed"] for v in p["route_catalogue"]))
        self.assertTrue(all(not v["access_verified"] for v in p["durable_owner_source_refs"]))
        self.assertTrue(all(not g["licences_checked"] and not g["payload_downloaded"] for g in p["external_reference_catalogue"]))
        self.assertIn("ISSUE_158_PUBLIC_PRIVATE_ASSET_BOUNDARY",p["activation_gates"])
        self.assertIn("ISSUE_161_SIGNED_TWO_NODE_FS_DS_CONFORMANCE",p["activation_gates"])
    def test_registered_support_status_is_not_claimed_test_result(self):
        p=catalogue.build_library_coverage(ROOT)
        self.assertGreater(p["file_type_declarations"]["status_counts"].get("capability-gated",0),0)
        self.assertTrue(all(x["execution_test"]=="NOT_PERFORMED_BY_COVERAGE_PROJECTION"
                            for x in p["file_type_declarations"]["types"]))
        self.assertIn("filespace-tree",p["lens_catalogue"])
        self.assertIn("topology-graph",p["lens_catalogue"])
        self.assertEqual(len(p["conversion_mapping_catalogue"]),19)
        self.assertTrue(all(not m["independently_retested"] for m in p["conversion_mapping_catalogue"]))
        self.assertTrue(all(k["evidence_ceiling"]=="SYMBOLIC_TOPOLOGY_NOT_PHYSICAL_QUALIFICATION" for k in p["geometry_kernel_catalogue"]))
    def test_provenance_is_pinned_to_file_content_digest(self):
        p=catalogue.build_library_coverage(ROOT)
        for item in p["source_roots"].values():
            self.assertEqual(item["source_sha256"],hashlib.sha256((ROOT/item["source_path"]).read_bytes()).hexdigest())
            self.assertEqual(item["source_bytes"],(ROOT/item["source_path"]).stat().st_size)
    def test_unregistered_cgx_identifier_cannot_match_by_semantic_tokens(self):
        for q in ("cgx:root:cognigrex","cgx:domain:romer","WT-999"):
            with self.subTest(q=q),self.assertRaisesRegex(resolver.CGXObjectContextError,"no current object match"):
                resolver.resolve_object_context(q)
    def test_registered_exact_id_and_natural_language_still_work(self):
        self.assertEqual(resolver.resolve_object_context("WT-001")["resolved_twin_id"],"watchtower")
        self.assertEqual(resolver.resolve_object_context("inspect WatchTower geometry")["resolved_twin_id"],"watchtower")
    def test_desktop_source_manifest_hash_matches_exact_resolver_bytes(self):
        manifest=json.loads((ROOT/"desktop"/"source-manifest.json").read_text(encoding="utf-8"))
        rows=[r for r in manifest["records"]
              if r["path"]=="LightSpeed_Runtime/lightspeed_runtime/cgx_object_context.py"]
        self.assertEqual(len(rows),1)
        data=RESOLVER.read_bytes()
        self.assertEqual(rows[0]["bytes"],len(data))
        self.assertEqual(rows[0]["sha256"],hashlib.sha256(data).hexdigest())
    def test_existing_source_fold_manifest_still_exact(self):
        p=ROOT/"cgx"/"review"/"unispace_source_fold_manifest_20261020.json"
        source=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(len(source["files"]),22)
        for f in source["files"]:
            raw=(ROOT/f["path"]).read_bytes()
            sha=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
            self.assertEqual(sha,f["git_blob_sha1"],f["path"])

if __name__=="__main__":
    unittest.main()
