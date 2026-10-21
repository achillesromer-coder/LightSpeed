"""Pinned upstream catalogue: verified source bytes -> bounded noncanonical R1."""
import copy
import hashlib
import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
PATH=ROOT/"cgx"/"portable_node"/"pinned_catalogue_source_intake.py"
SPEC=importlib.util.spec_from_file_location("cgx_pinned_catalogue_source_intake",PATH)
module=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

README=(b"# Sample catalogue\n\n"
        b"- **Demo Engine** - documentation [[source]](https://github.com/example/demo)\n"
        b"- **Second Engine** - detail [[source]](https://github.com/example/second)\n")
LICENSE=b"Creative Commons Legal Code\nCC0 1.0 Universal\n"
COMMIT="a"*40
def sha(x): return hashlib.sha256(x).hexdigest()
def blob(x): return hashlib.sha1(b"blob "+str(len(x)).encode()+b"\0"+x).hexdigest()
def group():
    return {
      "origin":{"name":"sample/engines","type":"ENGINE_INDEX","commit":COMMIT,
                "readme_blob":blob(README),"index_licence":"CC0-1.0"},
      "source_lines":2,
      "records":[
          {"line":3,"title":"Demo Engine","sources":["https://github.com/example/demo"],
           "rights":"UPSTREAM_LICENSE_UNVERIFIED","state":"DISCOVERY_REFERENCE_ONLY"},
          {"line":4,"title":"Second Engine","sources":["https://github.com/example/second"],
           "rights":"UPSTREAM_LICENSE_UNVERIFIED","state":"DISCOVERY_REFERENCE_ONLY"},
      ],
    }
def run(readme=README,license_bytes=LICENSE,source_group=None,**overrides):
    params=dict(expected_source_sha256=sha(README),
                expected_license_sha256=sha(LICENSE),
                expected_license_git_blob=blob(LICENSE))
    params.update(overrides)
    return module.stage_pinned_catalogue(
        readme,license_bytes,group() if source_group is None else source_group,**params)

class CatalogueSourceIntakeTests(unittest.TestCase):
    def test_verified_r0_identity_and_r1_structure(self):
        payload=run()
        source=payload["source_envelope"]
        receipt=payload["conversion_receipt"]
        self.assertEqual(source["schema"],"CGX-SOURCE-ENVELOPE/0.1")
        self.assertEqual(source["sha256"],sha(README))
        self.assertEqual(source["byte_length"],len(README))
        self.assertEqual(source["native_preservation"]["source_byte_length"],len(README))
        self.assertEqual(source["native_preservation"]["round_trip_claim"],"LOSSLESS_FOR_DECLARED_FIELDS")
        self.assertFalse(source["native_preservation"]["source_bytes_embedded"])
        self.assertEqual(len(source["projections"]),1)
        self.assertEqual(source["projections"][0]["indexed_entries"],2)
        self.assertEqual(receipt["conversion_classes_used"],["R0_EXACT","R1_SEMANTIC_REVERSIBLE"])
        self.assertEqual(receipt["authority_state"],"NONCANONICAL_REVIEW_ONLY")
        self.assertFalse(receipt["native_dbr_verified"])
        self.assertFalse(receipt["source_bytes_persisted_by_this_adapter"])

    def test_exact_line_offsets_and_selected_fields(self):
        entries=run()["source_envelope"]["projections"][0]["entries"]
        self.assertEqual([e["source_line"] for e in entries],[3,4])
        for row in entries:
            raw=README[row["source_byte_start"]:row["source_byte_end"]]
            self.assertEqual(sha(raw),row["raw_line_sha256"])
            self.assertIn(row["label"].encode("utf-8"),raw)
            self.assertTrue(all(u.encode("utf-8") in raw for u in row["source_links"]))
            self.assertIsNone(row["object_id"])
            self.assertIsNone(row["project_content_hash"])
            self.assertFalse(row["project_bytes_acquired"])

    def test_deterministic_independent_of_records_order(self):
        original=run()
        g=group()
        g["records"].reverse()
        reordered=run(source_group=g)
        self.assertEqual(original,reordered)

    def test_source_byte_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):
            run(readme=README+b"tamper")
        with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):
            run(license_bytes=LICENSE+b"tamper")
        with self.assertRaisesRegex(ValueError,"Git blob identity"):
            run(expected_source_sha256=sha(README),source_group={**group(),"origin":{**group()["origin"],"readme_blob":"b"*40}})

    def test_upstream_license_does_not_promote_engine(self):
        g=group()
        g["records"][0]["rights"]="PERMITTED"
        with self.assertRaisesRegex(ValueError,"implicitly promoted"):
            run(source_group=g)
        g=group()
        g["records"][0]["state"]="SOURCE_VERIFIED"
        with self.assertRaisesRegex(ValueError,"implicitly promoted"):
            run(source_group=g)

    def test_wrong_line_or_title_fails_closed(self):
        g=group();g["records"][0]["title"]="Some Other Engine"
        with self.assertRaisesRegex(ValueError,"source line"):
            run(source_group=g)
        g=group();g["records"][0]["line"]=5
        with self.assertRaises(ValueError):
            run(source_group=g)
        g=group();g["records"][1]["line"]=3
        with self.assertRaisesRegex(ValueError,"duplicate line"):
            run(source_group=g)

    def test_untrusted_credential_url_even_when_present_in_original(self):
        link="https://private.example/path?token=SECRET"
        bad=b"# Sample\n\n- **Demo Engine** - [[source]]("+link.encode()+b")\n"
        g={"origin":{**group()["origin"],"readme_blob":blob(bad)},"source_lines":1,
           "records":[{"line":3,"title":"Demo Engine","sources":[link],
                       "rights":"UPSTREAM_LICENSE_UNVERIFIED","state":"DISCOVERY_REFERENCE_ONLY"}]}
        with self.assertRaisesRegex(ValueError,"credential-bearing"):
            run(readme=bad,source_group=g,expected_source_sha256=sha(bad))

    def test_declared_source_envelope_required_fields_and_receipt(self):
        from json import loads
        contract=loads((ROOT/"cgx"/"domain_templates"/"source_envelope_contract.json").read_text())
        conversion=loads((ROOT/"cgx"/"domain_templates"/"file_conversion_contract.json").read_text())
        payload=run()
        self.assertTrue(set(contract["required_envelope_fields"])<=set(payload["source_envelope"]))
        self.assertTrue(set(conversion["required_receipt_fields"])<=set(payload["conversion_receipt"]))

    def test_actual_upstream_engine_index_source_receipt(self):
        import json
        source_path=ROOT/"cgx"/"review"/"alexandria_engine_catalogue_real_source_envelope_20261020.json"
        index_path=ROOT/"cgx"/"review"/"alexandria_external_reference_intake_20261020.json"
        receipt=json.loads(source_path.read_text(encoding="utf-8"))
        groups=json.loads(index_path.read_text(encoding="utf-8"))["groups"]
        group=next(g for g in groups if g["origin"]["name"]=="bobeff/open-source-engines")
        envelope=receipt["source_envelope"]
        projection=envelope["projections"][0]
        conversion=receipt["conversion_receipt"]
        self.assertEqual(envelope["schema"],"CGX-SOURCE-ENVELOPE/0.1")
        self.assertEqual(conversion["schema"],"CGX-FILE-CONVERSION-RECEIPT/0.1")
        self.assertEqual(envelope["sha256"],"075c794da0482a7bff6f46d67956ef2e62486a1914fc78cda3d239bbf3a54a92")
        self.assertEqual(envelope["byte_length"],7891)
        self.assertEqual(envelope["lineage"]["license_sha256"],"a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499")
        self.assertEqual(envelope["lineage"]["pinned_readme_git_blob"],group["origin"]["readme_blob"])
        self.assertEqual(envelope["lineage"]["license_git_blob"],"0e259d42c996742e9e3cba14c677129b2c1b6311")
        self.assertEqual(projection["indexed_entries"],46)
        self.assertEqual(len(projection["entries"]),46)
        self.assertEqual(projection["total_lines"],143)
        self.assertFalse(envelope["native_preservation"]["source_bytes_embedded"])
        self.assertFalse(conversion["native_dbr_verified"])
        self.assertFalse(conversion["source_bytes_persisted_by_this_adapter"])
        self.assertEqual(receipt["upstream_project_bytes_acquired"],0)
        self.assertEqual(conversion["authority_state"],"NONCANONICAL_REVIEW_ONLY")
        self.assertEqual(conversion["output_hashes"]["r1_structure_sha256"],
                         sha(json.dumps(projection,sort_keys=True,ensure_ascii=False,
                                        separators=(",",":")).encode("utf-8")))
        source_rows={r["line"]:r for r in group["records"]}
        for row in projection["entries"]:
            original=source_rows[row["source_line"]]
            self.assertEqual(row["label"],original["title"])
            self.assertEqual(row["source_links"],original["sources"])
            self.assertEqual(row["upstream_rights"],"UNVERIFIED")
            self.assertIsNone(row["object_id"])
            self.assertFalse(row["project_bytes_acquired"])
            self.assertTrue(0<=row["source_byte_start"]<row["source_byte_end"]<=7891)
            self.assertEqual(len(row["raw_line_sha256"]),64)

    def test_hydrate_selected_line_only_after_independent_access_and_exact_cache(self):
        staged=run()
        selected=staged["source_envelope"]["projections"][0]["entries"][0]["candidate_ref"]
        view=module.hydrate_catalogue_selection(staged,selected,source_bytes=README,access_granted=True)
        self.assertEqual(view["status"],"SOURCE_PROVEN_R1_VIEW_CANDIDATE")
        self.assertEqual(view["title"],"Demo Engine")
        self.assertEqual(view["source_line"],3)
        self.assertEqual(view["source_sha256"],sha(README))
        self.assertEqual(view["upstream_reference_urls"],["https://github.com/example/demo"])
        self.assertEqual(view["licence"],"CC0-1.0")
        self.assertEqual(view["linked_project_licence"],"UNVERIFIED")
        self.assertIsNone(view["object_id"])
        for flag in ("canonical_admission","authenticated","source_bytes_embedded",
                     "executable_capability","published"):
            self.assertFalse(view[flag])

    def test_hydration_withheld_before_content_validation(self):
        staged=run()
        selected=staged["source_envelope"]["projections"][0]["entries"][0]["candidate_ref"]
        denied=module.hydrate_catalogue_selection(staged,selected,source_bytes=README,
                                                  access_granted=False)
        self.assertEqual(denied["status"],"WITHHELD")
        self.assertNotIn("source_sha256",denied)
        self.assertNotIn("title",denied)
        denied_public=module.hydrate_catalogue_selection(staged,selected,
                            source_bytes=README,access_granted=True,audience="PUBLIC")
        self.assertEqual(denied_public["status"],"WITHHELD")
        self.assertNotIn("candidate_ref",denied_public)

    def test_hydration_missing_source_and_wrong_bytes_fail_closed(self):
        staged=run()
        selected=staged["source_envelope"]["projections"][0]["entries"][0]["candidate_ref"]
        self.assertEqual(module.hydrate_catalogue_selection(
            staged,selected,access_granted=True)["status"],"NOT_CACHED")
        wrong=module.hydrate_catalogue_selection(
            staged,selected,source_bytes=README+b"X",access_granted=True)
        self.assertEqual(wrong["status"],"SOURCE_MISMATCH")
        self.assertNotIn("title",wrong)
        badline=copy.deepcopy(staged)
        badline["source_envelope"]["projections"][0]["entries"][0]["raw_line_sha256"]="b"*64
        mismatch=module.hydrate_catalogue_selection(
            badline,selected,source_bytes=README,access_granted=True)
        self.assertEqual(mismatch["status"],"PROJECTION_MISMATCH")

    def test_hydration_unknown_selection_or_source_substitution(self):
        staged=run()
        self.assertEqual(module.hydrate_catalogue_selection(
            staged,"another:unknown",source_bytes=README,access_granted=True)["status"],
            "UNRESOLVED_SELECTION")
        second=staged["source_envelope"]["projections"][0]["entries"][1]["candidate_ref"]
        view=module.hydrate_catalogue_selection(
            staged,second,source_bytes=README,access_granted=True)
        self.assertEqual(view["title"],"Second Engine")
        altered=copy.deepcopy(staged)
        altered["conversion_receipt"]["source_sha256"]="c"*64
        self.assertEqual(module.hydrate_catalogue_selection(
            altered,second,source_bytes=README,access_granted=True)["status"],
            "INVALID_ENVELOPE")

    def test_licence_byte_identity_and_rights_boundary(self):
        record=run()["source_envelope"]["lineage"]
        self.assertEqual(record["license_sha256"],sha(LICENSE))
        self.assertEqual(record["license_git_blob"],blob(LICENSE))
        self.assertEqual(record["catalogue_license"],"CC0-1.0")
        self.assertEqual(record["upstream_project_license"],"UNVERIFIED")
        with self.assertRaisesRegex(ValueError,"catalogue rights"):
            invalid=b"NO LICENCE"
            run(license_bytes=invalid,expected_license_sha256=sha(invalid),
                expected_license_git_blob=blob(invalid))

if __name__=="__main__":
    unittest.main()
