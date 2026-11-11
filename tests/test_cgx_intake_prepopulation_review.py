import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts"/"cgx_intake_prepopulation_review.py"
spec=importlib.util.spec_from_file_location("prepop",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture(tmp: Path):
    core=tmp/"plugins"/"source"/"core-skills"/"cgx-handshake"
    core.mkdir(parents=True, exist_ok=True)
    (core/"SKILL.md").write_bytes(b"canonical")
    package=tmp/"plugins"/"packages"/"romer-grex"/"skills"/"cgx-handshake"
    package.mkdir(parents=True, exist_ok=True)
    (package/"SKILL.md").write_bytes(b"canonical")
    profile=tmp/"cgx"/"domain_templates"
    profile.mkdir(parents=True, exist_ok=True)
    (profile/"romer_semantic_library.json").write_text("{}")
    entry={"schema":"CGX-MANUAL-INTAKE-SOURCE-REVIEW/0.1",
           "relative":"Romer Projected/design.txt","disposition":"TEXT_SOURCE_REVIEWED_NOT_ACCEPTED",
           "native_admission":False,"executable_authority":False}
    private={"schema":"CGX-MANUAL-INTAKE-SOURCE-REVIEW/0.1",
             "relative":"Codex/private-client-folder/user_secret.txt",
             "disposition":"BINARY_OR_UNKNOWN_FORMAT_UNRESOLVED",
             "native_admission":False,"executable_authority":False}
    return {"schema":"CGX-INTAKE-EQUIVALENCE-REVIEW/0.1",
            "native_mint_authorized":False,"canonical_write":False,
            "sources_changed":0,"sources_deleted":0,"source_head":"abc123",
            "verified_groups":1,
            "duplicate_groups":[{"sha256":"0"*64,"sources":[{"path":"secret a"},{"path":"secret b"}],
                                 "byte_equivalence_verified":True}],
            "source_dispositions":{json.dumps(entry):2,json.dumps(private):3}}


class PrepopulationTests(unittest.TestCase):
    def test_deterministic_aggregate_only_and_safe_defaults(self):
        with TemporaryDirectory() as td:
            root=Path(td);receipt=fixture(root)
            a=mod.project(receipt,b"source receipt",root)
            b=mod.project(receipt,b"source receipt",root)
            self.assertEqual(a,b)
            self.assertEqual(a["intake"]["records_reviewed"],5)
            self.assertEqual(a["intake"]["route_candidates"]["Romer"],2)
            self.assertEqual(a["intake"]["route_candidates"]["UNASSIGNED_REQUIRES_SOURCE_QUALIFICATION"],3)
            self.assertEqual(sum(a["intake"]["provenance_triage"].values()),5)
            self.assertEqual(a["intake"]["provenance_triage"]["NAMED_FAMILY_ROOT_REVIEW"],2)
            self.assertEqual(a["intake"]["provenance_triage"]["CODEX_OTHER_PROVENANCE_REVIEW"],3)
            self.assertEqual(a["skills"]["canonical_core_count"],1)
            self.assertEqual(a["skills"]["distributed_count"],1)
            self.assertEqual(a["duplicates"]["verified_groups"],1)
            self.assertEqual(a["duplicates"]["deletion_eligible"],0)
            self.assertEqual(a["states"]["native_mint"],"HOLD")
            self.assertFalse(a["states"]["automatic_deletion"])
            serialised=json.dumps(a)
            self.assertNotIn("private-client-folder",serialised)
            self.assertNotIn("user_secret",serialised)
            self.assertNotIn("secret a",serialised)
            self.assertNotIn('"group_hashes"',serialised)
    def test_rejects_unverified_duplicates_and_native_authority(self):
        with TemporaryDirectory() as td:
            root=Path(td);receipt=fixture(root)
            receipt["duplicate_groups"][0]["byte_equivalence_verified"]=False
            with self.assertRaisesRegex(ValueError,"UNVERIFIED_DUPLICATE"):
                mod.project(receipt,b"x",root)
            receipt=fixture(root)
            receipt["native_mint_authorized"]=True
            with self.assertRaisesRegex(ValueError,"NATIVE_OR_CANONICAL"):
                mod.project(receipt,b"x",root)
    def test_generated_codex_output_is_triaged_not_minted_or_deleted(self):
        with TemporaryDirectory() as td:
            root=Path(td);receipt=fixture(root)
            entry={"schema":"CGX-MANUAL-INTAKE-SOURCE-REVIEW/0.1",
                   "relative":"Codex/2026-07-20/blease-run-a-quick-check-through/outputs/temp.pdf",
                   "disposition":"BINARY_OR_UNKNOWN_FORMAT_UNRESOLVED",
                   "native_admission":False,"executable_authority":False}
            receipt["source_dispositions"][json.dumps(entry)]=7
            a=mod.project(receipt,b"x",root)
            self.assertEqual(a["intake"]["provenance_triage"]["CODEX_GENERATED_OR_TRANSIENT_REVIEW"],7)
            self.assertEqual(a["intake"]["route_candidates"]["UNASSIGNED_REQUIRES_SOURCE_QUALIFICATION"],10)
            self.assertEqual(a["duplicates"]["deletion_eligible"],0)
            self.assertNotIn("temp.pdf",json.dumps(a))

    def test_detects_skill_distribution_drift_without_deleting(self):
        with TemporaryDirectory() as td:
            root=Path(td);receipt=fixture(root)
            p=root/"plugins/packages/romer-grex/skills/cgx-handshake/SKILL.md"
            p.write_bytes(b"changed distribution")
            a=mod.project(receipt,b"x",root)
            self.assertEqual(a["skills"]["drifted_distributed_skills"],["romer-grex/cgx-handshake"])
            self.assertFalse(a["states"]["automatic_source_move"])


if __name__=="__main__":
    unittest.main()
