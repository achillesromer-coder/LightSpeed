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
