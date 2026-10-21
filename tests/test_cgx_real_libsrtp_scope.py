"""Exact libsrtp source identity, Cisco notice and no-crypto-claim tests."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.libsrtp_source_scope import (
    BLOBS, GIT_TREE, SOURCE_REV, compile_libsrtp_scope,
)
from cgx.portable_node.project_gitlink_evidence import _git_blob, _git_tree

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "alexandria_libsrtp"
PARENT = ROOT / "cgx" / "review" / "alexandria_libdatachannel_source_scope_20261021.json"


def inputs():
    return (
        json.loads(PARENT.read_text(encoding="utf-8")),
        json.loads((FIX / "git_tree_chain.json").read_text(encoding="utf-8")),
        {name: (FIX / name).read_bytes() for name in BLOBS},
    )


class LibSrtpSourceTests(unittest.TestCase):
    def test_pinned_tree_recomputes_exactly_and_matches_parent(self):
        parent, trees, original = inputs()
        self.assertEqual(trees["root"]["sha"], GIT_TREE)
        for key in ("root", "include", "crypto", "crypto_include"):
            with self.subTest(key=key):
                self.assertFalse(trees[key]["truncated"])
                self.assertEqual(_git_tree(trees[key]), trees[key]["sha"])
        link = next(x for x in parent["nested_gitlinks"] if x["path"] == "deps/libsrtp")
        self.assertEqual(link["pinned_commit_sha1"], SOURCE_REV)
        self.assertEqual(compile_libsrtp_scope(parent, trees, original)["parent_gitlink_path"],
                         "deps/libsrtp")

    def test_license_requires_three_conditions_and_no_unverified_spdx_promotion(self):
        receipt = compile_libsrtp_scope(*inputs())
        self.assertEqual(receipt["source_root"], "git:cisco/libsrtp@" + SOURCE_REV)
        self.assertEqual(receipt["original_file_count"], 5)
        self.assertEqual(receipt["licence_scopes"]["repository_notice"],
                         "CISCO_BSD_THREE_CONDITION_STYLE")
        self.assertFalse(receipt["licence_scopes"]["spdx_identification_authoritative"])
        self.assertTrue(receipt["licence_scopes"]["nonendorsement_condition"])
        self.assertTrue(receipt["licence_scopes"]["required_notice_reproduction"])
        self.assertFalse(receipt["licence_scopes"]["distribution_approved"])
        self.assertFalse(receipt["licence_scopes"]["all_source_files_reviewed"])
        self.assertEqual(receipt["licence_scopes"]["optional_openssl_nss_backend_rights"],
                         "UNQUALIFIED")
        self.assertFalse(receipt["capability_evidence"]["cryptography_validated"])
        self.assertFalse(receipt["capability_evidence"]["network_interoperability_tested"])
        self.assertFalse(receipt["capability_evidence"]["cgx_network_transport_registered"])
        self.assertFalse(receipt["native_dbr_verified"])
        self.assertFalse(receipt["third_party_dependencies_qualified"])
        self.assertIsNone(receipt["canonical_object_id"])

    def test_source_files_exact_git_blobs_sha_and_deterministic_order(self):
        p, t, raw = inputs()
        result = compile_libsrtp_scope(p, t, raw)
        self.assertEqual(result, compile_libsrtp_scope(p, t, dict(reversed(list(raw.items())))))
        for item in result["original_file_proofs"]:
            value = raw[item["path"]]
            self.assertEqual(item["bytes"], len(value))
            self.assertEqual(item["git_blob_sha1"], _git_blob(value))
            self.assertEqual(item["sha256"], hashlib.sha256(value).hexdigest())
            self.assertFalse(item["bytes_embedded_in_r1"])

    def test_committed_source_free_receipt_rebuilds_exactly_from_R0(self):
        saved=ROOT/"cgx"/"review"/"alexandria_libsrtp_source_scope_20261021.json"
        persisted=json.loads(saved.read_text(encoding="utf-8"))
        rebuilt=compile_libsrtp_scope(*inputs())
        self.assertEqual(persisted,rebuilt)
        self.assertFalse(persisted["licence_scopes"]["distribution_approved"])
        self.assertFalse(persisted["capability_evidence"]["cryptography_validated"])
        self.assertFalse(persisted["native_dbr_verified"])

    def test_modified_file_or_unknown_extra_file_refused(self):
        p, t, raw = inputs()
        for name in BLOBS:
            corrupted = dict(raw)
            corrupted[name] += b"\n// modified"
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Git blob mismatch"):
                compile_libsrtp_scope(p, t, corrupted)
        missing = dict(raw)
        del missing["LICENSE"]
        with self.assertRaisesRegex(ValueError, "exact five"):
            compile_libsrtp_scope(p, t, missing)
        extra = dict(raw, **{"private.txt": b"not a source"})
        with self.assertRaisesRegex(ValueError, "exact five"):
            compile_libsrtp_scope(p, t, extra)

    def test_modified_tree_and_forged_parent_ref_refused(self):
        p, t, raw = inputs()
        changed = copy.deepcopy(t)
        changed["crypto_include"]["entries"][0]["sha"] = "f"*40
        with self.assertRaisesRegex(ValueError, "Git tree SHA-1 mismatch"):
            compile_libsrtp_scope(p, changed, raw)
        forged = copy.deepcopy(p)
        next(x for x in forged["nested_gitlinks"] if x["path"] == "deps/libsrtp")[
            "pinned_commit_sha1"] = "a"*40
        with self.assertRaisesRegex(ValueError, "exact original libSRTP Gitlink"):
            compile_libsrtp_scope(forged, t, raw)

    def test_claimed_server_or_canonical_proof_is_not_produced(self):
        result = compile_libsrtp_scope(*inputs())
        self.assertEqual(result["status"],
                         "FIVE_PINNED_R0_BLOBS_FOUR_GIT_TREES_PARTIAL_RIGHTS")
        self.assertFalse(result["complete_repository_acquired"])
        self.assertFalse(result["source_bytes_embedded"])
        self.assertFalse(result["capability_evidence"]["compiled_or_executed"])
        self.assertIn("QUALIFY_SELECTED_OPENSSL_NSS_BACKEND_LICENSES", result["frontier"])


if __name__ == "__main__":
    unittest.main()
