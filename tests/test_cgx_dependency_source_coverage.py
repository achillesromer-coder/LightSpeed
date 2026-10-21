"""Converge five existing source scopes without inventing licensed or live network functions."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import unittest

from cgx.portable_node.dependency_source_coverage import (
    SCOPE_PATHS, consolidate_dependency_source_samples,
)

ROOT=Path(__file__).resolve().parents[1]
PARENT="cgx/review/alexandria_libdatachannel_source_scope_20261021.json"
PERSISTED="cgx/review/alexandria_nested_dependency_coverage_20261021.json"


def inputs():
    parent=json.loads((ROOT/PARENT).read_text(encoding="utf-8"))
    children={path:json.loads((ROOT/filename).read_text(encoding="utf-8"))
              for path,filename in SCOPE_PATHS.items()}
    return parent,children


class NestedSourceCoverageTests(unittest.TestCase):
    def test_five_pinned_partial_source_roots_without_false_closure(self):
        parent,children=inputs()
        receipt=consolidate_dependency_source_samples(parent,children)
        self.assertEqual(receipt["schema"],"CGX-ALEXANDRIA-NESTED-SOURCE-COVERAGE-LEDGER/0.1")
        self.assertEqual(receipt["direct_gitlinks_total"],5)
        self.assertEqual(receipt["direct_gitlinks_with_bounded_r0_samples"],5)
        self.assertEqual(receipt["direct_gitlinks_whole_repository_acquired"],0)
        self.assertEqual(receipt["child_original_file_proofs_total"],27)
        self.assertEqual(receipt["parent_original_file_proofs_total"],5)
        self.assertEqual(receipt["original_source_file_proofs_across_distinct_roots"],32)
        self.assertFalse(receipt["full_dependency_and_licence_closure"])
        self.assertFalse(receipt["network_transport_qualified"])
        self.assertFalse(receipt["native_signed_two_node_readback"])
        self.assertFalse(receipt["canonical_promotion"])
        self.assertFalse(receipt["owner_release_authorized"])
        self.assertFalse(receipt["source_bytes_embedded"])
        self.assertEqual({x["gitlink_path"] for x in receipt["source_dependency_edges"]},set(SCOPE_PATHS))
        for row in receipt["source_dependency_edges"]:
            self.assertTrue(row["source_file_sample_complete"])
            self.assertFalse(row["whole_repository_source_complete"])
            self.assertFalse(row["dependency_rights_proven"])
            self.assertFalse(row["functional_network_capability_proven"])
            self.assertEqual(len(row["receipt_projection_sha256"]),64)
            self.assertTrue(row["frontier"])
            self.assertIsNone(row["canonical_object_id"])

    def test_child_order_does_not_change_hashed_projection(self):
        parent,children=inputs()
        expected=consolidate_dependency_source_samples(parent,children)
        backwards=dict(reversed(list(children.items())))
        self.assertEqual(expected,consolidate_dependency_source_samples(parent,backwards))
        for row in expected["source_dependency_edges"]:
            source=json.loads((ROOT/row["existing_receipt_path"]).read_text())
            # Source digest is a canonicalized JSON hash, not original full-repo SHA.
            encoded=json.dumps(source,sort_keys=True,ensure_ascii=False,
                               separators=(",",":"),allow_nan=False).encode("utf-8")
            self.assertEqual(row["receipt_projection_sha256"],
                             hashlib.sha256(encoded).hexdigest())

    def test_missing_or_unregistered_github_source_is_not_silently_filled(self):
        parent,children=inputs()
        deleted=dict(children)
        deleted.pop("deps/json")
        with self.assertRaisesRegex(ValueError,"exact five child source scopes"):
            consolidate_dependency_source_samples(parent,deleted)
        extra=dict(children)
        extra["deps/unknown"]={}
        with self.assertRaisesRegex(ValueError,"exact five child source scopes"):
            consolidate_dependency_source_samples(parent,extra)
        wrong=copy.deepcopy(children)
        wrong["deps/json"]["source_root"]="git:untrusted/a@"+("1"*40)
        with self.assertRaisesRegex(ValueError,"ancestry"):
            consolidate_dependency_source_samples(parent,wrong)

    def test_wrong_revision_and_unapproved_rights_are_rejected(self):
        parent,children=inputs()
        bad=copy.deepcopy(parent)
        bad["nested_gitlinks"][0]["pinned_commit_sha1"]="a"*40
        with self.assertRaisesRegex(ValueError,"ancestry"):
            consolidate_dependency_source_samples(bad,children)
        bad=copy.deepcopy(children)
        bad["deps/libjuice"]["license_scopes"]["distribution_approved"]=True
        with self.assertRaisesRegex(ValueError,"rights"):
            consolidate_dependency_source_samples(parent,bad)
        bad=copy.deepcopy(children)
        bad["deps/usrsctp"]["public_release_approved"]=True
        with self.assertRaisesRegex(ValueError,"rights"):
            consolidate_dependency_source_samples(parent,bad)

    def test_full_source_or_native_promotion_fail_closed(self):
        parent,children=inputs()
        altered=copy.deepcopy(children)
        altered["deps/plog"]["whole_repository_acquired"]=True
        with self.assertRaisesRegex(ValueError,"full repository source promotion"):
            consolidate_dependency_source_samples(parent,altered)
        altered=copy.deepcopy(children)
        altered["deps/libsrtp"]["native_dbr_verified"]=True
        with self.assertRaisesRegex(ValueError,"rights"):
            consolidate_dependency_source_samples(parent,altered)
        altered=copy.deepcopy(parent)
        altered["canonical_object_id"]="fake"
        with self.assertRaisesRegex(ValueError,"untrusted or promoted"):
            consolidate_dependency_source_samples(altered,children)

    def test_malformed_source_sha_is_not_treated_as_evidence(self):
        parent,children=inputs()
        altered=copy.deepcopy(children)
        altered["deps/json"]["selected_original_files"][0]["sha256"]="0"*64
        # A well-formed digest with bad content changes ledger digest; it must
        # not automatically validate source bytes. The original adapter owns
        # independent byte-based tests; this layer is projection-only.
        different=consolidate_dependency_source_samples(parent,altered)
        original=consolidate_dependency_source_samples(parent,children)
        self.assertNotEqual(
            next(r for r in original["source_dependency_edges"] if r["gitlink_path"]=="deps/json")
                ["receipt_projection_sha256"],
            next(r for r in different["source_dependency_edges"] if r["gitlink_path"]=="deps/json")
                ["receipt_projection_sha256"])
        altered["deps/json"]["selected_original_files"][0]["sha256"]="invalid"
        with self.assertRaisesRegex(ValueError,"digest"):
            consolidate_dependency_source_samples(parent,altered)

    def test_committed_coverage_receipt_matches_exact_projections(self):
        persisted=json.loads((ROOT/PERSISTED).read_text(encoding="utf-8"))
        self.assertEqual(persisted,consolidate_dependency_source_samples(*inputs()))
        self.assertFalse(persisted["sai_service_activated"])


if __name__=="__main__":
    unittest.main()
