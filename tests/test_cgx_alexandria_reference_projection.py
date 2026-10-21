"""Alexandria pinned external reference projection: discovery is not ingestion."""
from __future__ import annotations
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
PATH=ROOT/"cgx"/"portable_node"/"alexandria_reference_projection.py"
SRC=ROOT/"cgx"/"review"/"alexandria_external_reference_intake_20261020.json"
spec=importlib.util.spec_from_file_location("cgx_alexandria_reference_projection",PATH)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def intake():
    return json.loads(SRC.read_text(encoding="utf-8"))


class AlexandriaReferenceProjectionTests(unittest.TestCase):
    def test_expected_external_family_counts_are_not_content_admission(self):
        result=module.compile_reference_index(intake())
        self.assertEqual(len(result["components"]),214)
        self.assertEqual(result["counts"]["indexed_games"],161)
        self.assertEqual(result["counts"]["indexed_engines"],46)
        self.assertEqual(result["counts"]["nasa_discovery"],5)
        self.assertEqual(result["counts"]["archive_discovery"],2)
        self.assertEqual(result["counts"]["unlinked_catalogue_lines"],27)
        self.assertEqual(result["counts"]["source_files_acquired"],0)
        self.assertEqual(result["counts"]["qualified_executable_capabilities"],0)
        self.assertFalse(result["semantic_promotion"])
        self.assertFalse(result["fileset_published"])
        for record in result["components"]:
            self.assertIsNone(record["object_id"])
            self.assertIsNone(record["content_sha256"])
            self.assertFalse(record["source_bytes_acquired"])
            self.assertFalse(record["canonical_admission"])

    def test_candidate_rows_are_stably_sorted_and_dont_merge_upstream_urls(self):
        original=intake()
        reversed_copy=copy.deepcopy(original)
        reversed_copy["groups"].reverse()
        for group in reversed_copy["groups"]:
            group["records"].reverse()
        reversed_copy["nasa_sources"].reverse()
        reversed_copy["historical_web"].reverse()
        left=module.compile_reference_index(original)
        right=module.compile_reference_index(reversed_copy)
        self.assertEqual(left["projection_sha256"],right["projection_sha256"])
        self.assertEqual([r["candidate_ref"] for r in left["components"]],
                         [r["candidate_ref"] for r in right["components"]])
        self.assertEqual(len(set(r["candidate_ref"] for r in left["components"])),214)

    def test_unverified_associations_cannot_promote_engines(self):
        result=module.compile_reference_index(intake())
        associations=[r["engine_hint"] for r in result["components"] if r.get("engine_hint")]
        self.assertEqual(len(associations),14)
        self.assertTrue(all(x["relation"]=="UNVERIFIED_ENGINE_ASSOCIATION" for x in associations))

    def test_unknown_upstream_source_or_catalogue_integrity_fails(self):
        cases=[]
        x=intake();x["groups"][0]["origin"]["commit"]="unknown";cases.append(x)
        x=intake();x["groups"][0]["records"][0]["state"]="R0_ACQUIRED";cases.append(x)
        x=intake();x["groups"][0]["records"].append(copy.deepcopy(x["groups"][0]["records"][0]));x["groups"][0]["source_lines"]+=1;cases.append(x)
        x=intake();x["groups"][0]["records"][0]["sources"]=["https://private.example/?token=SECRET"];cases.append(x)
        x=intake();x["groups"][0]["records"][0]["sources"]=["file:///C:/Cognigrex/private"];cases.append(x)
        for i,payload in enumerate(cases):
            with self.subTest(i=i),self.assertRaises(ValueError):
                module.compile_reference_index(payload)

    def test_independent_upstream_catalogue_receipt_is_not_project_admission(self):
        receipt_path=ROOT/"cgx"/"review"/"alexandria_pinned_catalogue_readback_20261020.json"
        receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
        families={g["origin"]["name"]:g for g in intake()["groups"]}
        self.assertEqual(receipt["totals"]["matched_line_source_urls"],207)
        self.assertEqual(receipt["totals"]["matched_line_titles"],207)
        self.assertEqual(receipt["totals"]["external_projects_r0_verified"],0)
        self.assertFalse(receipt["canonical_admission"])
        self.assertFalse(receipt["release_ready"])
        for item in receipt["roots"]:
            group=families[item["origin"]]
            self.assertEqual(item["commit"],group["origin"]["commit"])
            self.assertEqual(item["readme_git_blob"],group["origin"]["readme_blob"])
            self.assertEqual(item["indexed_entries"],group["source_lines"])
            self.assertEqual(item["matched_line_titles"],item["indexed_entries"])
            self.assertEqual(item["matched_line_source_urls"],item["indexed_entries"])
            self.assertEqual(item["license_git_blob"],"0e259d42c996742e9e3cba14c677129b2c1b6311")
            self.assertEqual(item["linked_project_license"],"UNVERIFIED")

    def test_archival_history_not_upgraded_to_redistributable_content(self):
        rows=module.compile_reference_index(intake())["components"]
        history=[r for r in rows if r["candidate_kind"]=="ARCHIVE_DISCOVERY"]
        self.assertEqual(len(history),2)
        for entry in history:
            self.assertEqual(entry["evidence_state"],"CAPTURE_NOT_VERIFIED")
            self.assertFalse(entry["source_bytes_acquired"])
            self.assertEqual(entry["rights"],"ORIGINAL_GAME_ASSETS_UNVERIFIED")

if __name__=="__main__":
    unittest.main()
