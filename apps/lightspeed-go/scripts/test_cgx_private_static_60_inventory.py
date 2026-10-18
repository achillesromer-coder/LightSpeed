#!/usr/bin/env python3
"""Source-only integrity and fail-closed review for issue #158's 60 static leaves.

Passing this test does NOT establish deployed HTTPS non-disclosure or PUBLIC_SAFE
approval. Release remains HOLD until independent owner and deployment evidence.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("CGX_PRIVATE_STATIC_60_SOURCE_INVENTORY.json")
CATALOGUE = "apps/lightspeed-go/public/data/cgx_object_review_catalogue.json"
RENDER = "apps/lightspeed-go/public/review/renders/"
MESH = "apps/lightspeed-go/public/review/mesh/"


def tracked_leaves() -> set[str]:
    result = subprocess.check_output(
        ["git", "ls-files", "-z", "--", CATALOGUE, RENDER, MESH],
        cwd=ROOT,
    )
    return {item.decode("utf-8") for item in result.split(b"\0") if item}


def validate_source_inventory(manifest: dict, tracked: set[str]) -> None:
    if manifest.get("schema") != "CGX-PRIVATE-STATIC-60-SOURCE-INVENTORY/1":
        raise ValueError("inventory schema mismatch")
    if manifest.get("status") != "OWNER_CLASSIFICATION_PENDING_RELEASE_HOLD":
        raise ValueError("inventory release hold missing")
    if manifest.get("public_safe_approved") is not False:
        raise ValueError("PUBLIC_SAFE must remain unapproved")
    if manifest.get("owner_signatures") != [] or manifest.get("deployed_negative_receipts") != []:
        raise ValueError("unsigned or unverified release evidence must not be embedded")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or len(assets) != 60 or manifest.get("source_asset_count") != 60:
        raise ValueError("inventory must enumerate exactly 60 source leaves")
    paths = [a.get("source_path") for a in assets if isinstance(a, dict)]
    if len(paths) != 60 or len(set(paths)) != 60 or set(paths) != tracked:
        raise ValueError("missing, duplicate or unexpected tracked source leaf")
    groups = {
        "render": sum(p.startswith(RENDER) for p in paths),
        "mesh": sum(p.startswith(MESH) for p in paths),
        "catalogue": sum(p == CATALOGUE for p in paths),
    }
    if groups != {"render": 43, "mesh": 16, "catalogue": 1}:
        raise ValueError("source group counts changed")
    if manifest.get("source_groups") != groups:
        raise ValueError("declared group counts disagree")
    for asset in assets:
        p = asset["source_path"]
        if not isinstance(p, str) or p.startswith("/") or "\\" in p or ".." in Path(p).parts:
            raise ValueError("unsafe source path")
        if asset.get("public_safe_status") != "UNREVIEWED_HOLD":
            raise ValueError("unapproved public classification")
        raw = (ROOT / p).read_bytes()
        digest = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        if digest != asset.get("git_blob_sha1") or len(raw) != asset.get("source_bytes"):
            raise ValueError("source content hash or size drift")


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.tracked = tracked_leaves()

    def test_exact_source_readback(self):
        validate_source_inventory(self.manifest, self.tracked)

    def test_reject_missing_leaf(self):
        m = copy.deepcopy(self.manifest)
        m["assets"].pop()
        with self.assertRaises(ValueError):
            validate_source_inventory(m, self.tracked)

    def test_reject_duplicate_leaf(self):
        m = copy.deepcopy(self.manifest)
        m["assets"][1] = copy.deepcopy(m["assets"][0])
        with self.assertRaises(ValueError):
            validate_source_inventory(m, self.tracked)

    def test_reject_hash_drift(self):
        m = copy.deepcopy(self.manifest)
        m["assets"][0]["git_blob_sha1"] = "0" * 40
        with self.assertRaises(ValueError):
            validate_source_inventory(m, self.tracked)

    def test_reject_size_drift(self):
        m = copy.deepcopy(self.manifest)
        m["assets"][0]["source_bytes"] += 1
        with self.assertRaises(ValueError):
            validate_source_inventory(m, self.tracked)

    def test_reject_false_public_approval(self):
        m = copy.deepcopy(self.manifest)
        m["public_safe_approved"] = True
        with self.assertRaises(ValueError):
            validate_source_inventory(m, self.tracked)

    def test_reject_unsupported_signature(self):
        m = copy.deepcopy(self.manifest)
        m["owner_signatures"] = ["unverified"]
        with self.assertRaises(ValueError):
            validate_source_inventory(m, self.tracked)

    def test_reject_path_substitution(self):
        m = copy.deepcopy(self.manifest)
        m["assets"][0]["source_path"] = "apps/lightspeed-go/public/../private.json"
        with self.assertRaises(ValueError):
            validate_source_inventory(m, self.tracked)


if __name__ == "__main__":
    unittest.main()
