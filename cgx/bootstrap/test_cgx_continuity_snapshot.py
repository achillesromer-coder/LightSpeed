"""Negative tests for committed-only CGX cross-chat continuity checkpoint."""
import importlib.util
import json
from pathlib import Path
import unittest

P = Path(__file__).with_name("cgxContinuitySnapshot.py")
S = importlib.util.spec_from_file_location("cgx_continuity", P)
mod = importlib.util.module_from_spec(S)
S.loader.exec_module(mod)
SHA = "a" * 40


def fixture():
    f = {
        mod.PATHS[0]: ("# Cross-chat / cross-platform continuity and approval boundaries\n"
                       "No source promotion by review.").encode(),
        mod.PATHS[1]: json.dumps({
            "source_repo": "achillesromer-coder/LightSpeed",
            "state": "SOURCE_REVIEW_ONLY", "open": []
        }).encode(),
        mod.PATHS[2]: json.dumps({
            "schema": "CGX-PHASE-ACCEPTANCE-REVIEW-GRAMMAR/0.1",
            "parent": "cgx:root:cognigrex",
            "state": "SOURCE_ONLY_REVIEW_NOT_CANONICAL",
            "premint_integration_design_v01": {
                "canonical_parent": "cgx:root:cognigrex",
                "sole_resolver": "LOAD.cgx",
                "status": "APPROVED_DESIGN_ONLY__NO_NATIVE_OR_PUBLIC_AUTHORITY",
                "authority_gate_status": {g: "HOLD" for g in mod.REQUIRED_HOLDS}
            }
        }).encode(),
        mod.PATHS[3]: json.dumps({
            "schema": "CGX-MANUAL-INTAKE-PREPOPULATION-REVIEW/0.1",
            "canonical_parent": "cgx:root:cognigrex",
            "sole_load_resolver": "LOAD.cgx",
            "source_receipt_sha256": "c" * 64,
            "intake": {"records_reviewed": 3296},
            "duplicates": {"deletion_eligible": 0},
            "states": {
                "native_mint": "HOLD", "independent_dbr": "HOLD",
                "public_release": "HOLD", "automatic_deletion": False
            }
        }).encode()
    }
    return f


def modify(f, idx, mutate):
    d = json.loads(f[mod.PATHS[idx]])
    mutate(d)
    f[mod.PATHS[idx]] = json.dumps(d).encode()
    return f


class SnapshotTests(unittest.TestCase):
    def test_deterministic_source_only_no_private_payload(self):
        a = mod.from_committed_sources(fixture(), SHA)
        b = mod.from_committed_sources(fixture(), SHA)
        self.assertEqual(a, b)
        self.assertEqual(a["commit_sha"], SHA)
        self.assertEqual(a["intake_review_entries_at_receipt"], 3296)
        self.assertTrue(a["all_documentary_authority_holds"])
        for key in ("native_mint", "source_deletion", "deployment",
                    "signing", "independent_dbr_verified",
                    "live_remote_head_verified", "installed_runtime_verified"):
            self.assertFalse(a[key], key)
        out = json.dumps(a)
        self.assertNotIn("private/", out)
        self.assertNotIn("source_paths", out)
        self.assertNotIn("original_path", out)

    def test_missing_or_fake_commit_denied(self):
        f = fixture()
        with self.assertRaisesRegex(ValueError, "COMMIT_SHA_INVALID"):
            mod.from_committed_sources(f, "HEAD")
        del f[mod.PATHS[1]]
        with self.assertRaisesRegex(ValueError, "MISSING_COMMITTED"):
            mod.from_committed_sources(f, SHA)

    def test_unauthorised_gate_release_denied(self):
        for gate in mod.REQUIRED_HOLDS:
            f = fixture()
            modify(f, 2, lambda d: d["premint_integration_design_v01"]
                   ["authority_gate_status"].__setitem__(gate, "APPROVED"))
            with self.subTest(gate=gate), self.assertRaisesRegex(
                    ValueError, "UNQUALIFIED_AUTHORITY"):
                mod.from_committed_sources(f, SHA)

    def test_undeclared_parent_resolver_and_phase_denied(self):
        for key, val in (("parent", "cgx:new:root"),
                         ("state", "NATIVE_ADMITTED")):
            f = fixture()
            modify(f, 2, lambda d: d.__setitem__(key, val))
            with self.subTest(key=key), self.assertRaisesRegex(
                    ValueError, "ROOT_OR_PHASE"):
                mod.from_committed_sources(f, SHA)
        f = fixture()
        modify(f, 2, lambda d: d["premint_integration_design_v01"]
               .__setitem__("sole_resolver", "OTHER.cgx"))
        with self.assertRaisesRegex(ValueError, "REVIEW_DESIGN"):
            mod.from_committed_sources(f, SHA)

    def test_source_deletion_rights_and_intake_promotions_denied(self):
        changes = [
            lambda d: d["states"].__setitem__("automatic_deletion", True),
            lambda d: d["states"].__setitem__("native_mint", "APPROVED"),
            lambda d: d["states"].__setitem__("independent_dbr", "APPROVED"),
            lambda d: d["duplicates"].__setitem__("deletion_eligible", 45),
        ]
        for action in changes:
            f = fixture()
            modify(f, 3, action)
            with self.assertRaisesRegex(ValueError, "SOURCE_INTAKE"):
                mod.from_committed_sources(f, SHA)

    def test_unqualified_source_receipt_digest_denied(self):
        f = fixture()
        modify(f, 3, lambda d: d.__setitem__(
            "source_receipt_sha256", "Z" * 64))
        with self.assertRaisesRegex(ValueError, "SOURCE_RECEIPT_POINTER"):
            mod.from_committed_sources(f, SHA)

    def test_stale_context_without_read_order_denied(self):
        f = fixture()
        f[mod.PATHS[0]] = b"historical unqualified status document"
        with self.assertRaisesRegex(ValueError, "CONTINUITY_READ_ORDER_MISSING"):
            mod.from_committed_sources(f, SHA)

    def test_real_committed_only_readback_does_not_claim_live(self):
        a = mod.checkpoint()
        self.assertEqual(a["state"], "COMMITTED_SOURCE_CHECKPOINT_ONLY")
        self.assertFalse(a["live_remote_head_verified"])
        self.assertEqual(len(a["commit_sha"]), 40)


if __name__ == "__main__":
    unittest.main()
