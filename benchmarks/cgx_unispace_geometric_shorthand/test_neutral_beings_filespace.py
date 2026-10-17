import copy
import unittest
from pathlib import Path

from neutral_beings_filespace import (
    CatalogueHold, load_index, validate_index, resolve_lens,
    resolve_seed, safe_intent, summary, build_review_html
)
INDEX=Path(__file__).with_name("neutral_beings_source_index.json")

class NeutralBeingsFileSpaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.doc=load_index(INDEX)

    def test_source_count_and_lineage(self):
        report=summary(self.doc)
        self.assertEqual((report["product_concepts"],report["primitive_refs"],report["printer_families"]),(80,70,17))
        self.assertEqual(report["groups"],9)
        self.assertEqual(report["qualified_products"],0)
        self.assertFalse(report["public_release"])
        self.assertIn("CROSS_GREX_PRODUCT_ATLAS", self.doc["source_refs"]["product_atlas"]["path"])

    def test_printer_and_product_qualification_is_never_inferred(self):
        for row in self.doc["products"]:
            self.assertEqual(row["source_state"],"UNQUALIFIED_PRODUCT_CONCEPT")
            self.assertFalse(row["production_approved"])
            self.assertFalse(row["physical_tested"])
        for row in self.doc["printer_families"]:
            self.assertFalse(row["physically_qualified"])

    def test_phone_watch_butterbot_and_micro_printer_ids_are_existing(self):
        for x in ["FU-01","FW-01","FO-01","FD-01","FD-02","FD-03","FD-05"]:
            result=resolve_lens(self.doc,x,"identity")
            self.assertEqual(result["status"],"SOURCE_METADATA_ONLY")
            self.assertFalse(result["public_release_authorized"])

    def test_unregistered_codex_pet_retained_as_semantic_candidate(self):
        p=resolve_seed(self.doc,"Codex Pet companion")
        self.assertEqual(p["semantic_state"],"NEW_SEMANTIC_CONCEPT_UNREGISTERED")
        self.assertFalse(p["manufacturing_qualified"])
        self.assertIsNone(p["machine_code"])

    def test_diodes_not_falsely_equated_with_qualified_semiconductors(self):
        p=resolve_seed(self.doc,"Diode / functional electronics")
        self.assertEqual(p["status"],"PROPOSED_CONCEPT_REVIEW")
        self.assertFalse(p["manufacturing_qualified"])
        self.assertIn("PT-040",p["source_technology_refs"])

    def test_geometry_is_unknown_without_qualified_source_adapter(self):
        r=resolve_lens(self.doc,"FU-01","geometry")
        self.assertEqual(r["status"],"ADAPTER_REQUIRED")
        self.assertEqual(r["units"],"UNKNOWN")

    def test_dataspace_cannot_infer_peer_or_lease(self):
        r=resolve_lens(self.doc,"FW-01","dataspace")
        self.assertEqual(r["status"],"NOT_CONNECTED")
        self.assertFalse(r["peer_authenticated"])
        self.assertFalse(r["lease_verified"])

    def test_printspace_never_runs_from_metadata(self):
        r=resolve_lens(self.doc,"FD-03","printspace")
        self.assertEqual(r["status"],"PHYSICAL_NOT_RUN")
        self.assertFalse(r["manufacturing_output_authorized"])
        self.assertFalse(r["machine_qualified"])

    def test_public_projection_never_discloses_unreleased_source_entries(self):
        # Restricted, benign and missing identifiers are equally withheld.
        for key in ["FB-07","FU-01","NO-PRODUCT"]:
            r=resolve_lens(self.doc,key,"identity",audience="public")
            self.assertEqual(r,{"status":"WITHHELD","canonical_promotion_authorized":False})

    def test_wrong_prior_source_root_fails_closed(self):
        r=resolve_lens(self.doc,"FU-01","identity",advertised_source_sha="0"*40)
        self.assertEqual(r["status"],"CONTEXT_MISMATCH")

    def test_unknown_is_not_zero_or_a_made_up_product(self):
        self.assertEqual(resolve_lens(self.doc,"NO-PRODUCT","identity")["status"],"UNKNOWN")
        self.assertEqual(resolve_lens(self.doc,"FU-01","neural-device")["status"],"UNSUPPORTED_VIEW")

    def test_unsafe_intents_excluded(self):
        for intent in ["weapons","weapon components","explosive","harm","assault"]:
            self.assertEqual(safe_intent(intent)["status"],"EXCLUDED_WEAPON_INTENT")
        self.assertEqual(safe_intent("creative")["status"],"INTENT_REVIEW_CANDIDATE_ONLY")
        self.assertFalse(safe_intent("creative")["manufacture_allowed"])
        self.assertEqual(safe_intent("dual-use process")["status"],"HOLD_HUMAN_SAFETY_REVIEW")

    def test_duplicate_or_reclassified_sources_are_rejected(self):
        d=copy.deepcopy(self.doc)
        d["products"][1]["source_product_id"]=d["products"][0]["source_product_id"]
        with self.assertRaises(CatalogueHold):validate_index(d)
        d=copy.deepcopy(self.doc);d["products"][0]["physical_tested"]=True
        with self.assertRaises(CatalogueHold):validate_index(d)
        d=copy.deepcopy(self.doc);d["authority"]["public_release"]=True
        with self.assertRaises(CatalogueHold):validate_index(d)
        d=copy.deepcopy(self.doc);d["source_refs"]["product_atlas"]["blob_sha"]="DUMMY"
        with self.assertRaises(CatalogueHold):validate_index(d)

    def test_review_html_is_local_and_non_operational(self):
        result=build_review_html(self.doc)
        self.assertIn("Neutral Beings",result)
        self.assertIn("OWNER",result.upper())
        self.assertIn("Restricted source review",result)
        self.assertIn('"id":"FU-01"',result)
        self.assertNotIn("fetch(",result)
        self.assertNotIn("WebSocket(",result)
        self.assertNotIn("https://",result)
        self.assertNotIn("G-code",result)
        self.assertIn("No", "No")  # live transport remains absent

if __name__=="__main__":
    unittest.main()
