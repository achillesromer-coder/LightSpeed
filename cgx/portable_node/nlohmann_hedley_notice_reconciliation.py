"""Nlohmann Hedley path/REUSE/SPDX source reconciliation, candidate only.

Two original upstream Hedley blobs, two full subtree Git objects, and the
previously proven nlohmann parent root are required. Does not edit upstream
metadata or give distribution/relicensing authority from file-path inference.
"""
from __future__ import annotations

import hashlib
from typing import Any

from cgx.portable_node.project_gitlink_evidence import _git_blob, _git_tree
from cgx.portable_node.nlohmann_json_source_scope import (
    ORIGIN, PINNED_COMMIT, ROOT_TREE, BLOBS as BASE_BLOBS,
)

TREE_SHAS = {
    "thirdparty": "f7fa48b51f9c60f824ca358da5078d93fa672c1e",
    "hedley": "d3804e2faaf3e564a130281b081944c32449f15e",
}
HEADERS = {
    "include/nlohmann/thirdparty/hedley/hedley.hpp": "fb0b073b0c65ff2651e2fdab03006c47cb67ef31",
    "include/nlohmann/thirdparty/hedley/hedley_undef.hpp": "ad86d11f22cc2ffbddb872f7caeb0a13896ad7ca",
}
STALE_DEP5_PATH = "include/nlohmann/thirdparty/hedley.hpp"
SOURCE_ROOT = f"git:{ORIGIN}@{PINNED_COMMIT}"


def _lookup(tree: dict[str, Any], name: str, mode: str) -> str:
    found = [e for e in tree["entries"] if e["path"] == name and e["mode"] == mode]
    if len(found) != 1:
        raise ValueError("missing or duplicated Git tree entry: " + name)
    return found[0]["sha"]


def resolve_hedley_notice(
    old_source_scope: dict[str, Any],
    old_trees: dict[str, Any],
    new_trees: dict[str, Any],
    dep5_original: bytes,
    headers: dict[str, bytes],
) -> dict[str, Any]:
    if (not isinstance(old_source_scope, dict)
        or old_source_scope.get("schema") != "CGX-ALEXANDRIA-NLOHMANN-SOURCE-SCOPE/0.1"
        or old_source_scope.get("source_root") != SOURCE_ROOT
        or old_source_scope.get("native_dbr_verified") is not False
        or old_source_scope.get("licensing_review", {}).get("distribution_approved") is not False):
        raise ValueError("missing source-scope predecessor")
    if (not isinstance(old_trees, dict) or old_trees.get("root_sha") != ROOT_TREE
        or not isinstance(old_trees.get("trees"), dict)):
        raise ValueError("missing original Git tree ancestry")
    # Establish root -> include -> nlohmann -> thirdparty -> hedley without
    # accepting an arbitrary, untrusted directory/alias returned by a caller.
    old = old_trees["trees"]
    if not all(name in old for name in ("root", "include", "include_nlohmann")):
        raise ValueError("incomplete original ancestor trees")
    for name in ("root", "include", "include_nlohmann"):
        if _git_tree(old[name]) != old[name].get("sha"):
            raise ValueError("original ancestor Git tree hash mismatch")
    if (old["root"]["sha"] != ROOT_TREE
        or _lookup(old["root"], "include", "040000") != old["include"]["sha"]
        or _lookup(old["include"], "nlohmann", "040000") != old["include_nlohmann"]["sha"]):
        raise ValueError("original Git root ancestry mismatch")
    if (not isinstance(new_trees, dict)
        or new_trees.get("schema") != "CGX-NLOHMANN-HEDLEY-PINNED-TREE/0.1"
        or new_trees.get("source_repo") != ORIGIN
        or new_trees.get("commit") != PINNED_COMMIT
        or new_trees.get("upstream_root_git_tree_sha1") != ROOT_TREE):
        raise ValueError("Hedley source identity mismatch")
    descendants = {}
    for name, expected_sha in TREE_SHAS.items():
        item = new_trees.get(name)
        if not isinstance(item, dict) or item.get("sha") != expected_sha:
            raise ValueError("unverified Hedley subtree identity")
        if _git_tree(item) != expected_sha:
            raise ValueError("Hedley subtree Git hash mismatch")
        descendants[name] = item
    if (_lookup(old["include_nlohmann"], "thirdparty", "040000") != TREE_SHAS["thirdparty"]
        or _lookup(descendants["thirdparty"], "hedley", "040000") != TREE_SHAS["hedley"]):
        raise ValueError("Git ancestry does not prove actual Hedley path")
    if type(dep5_original) is not bytes or _git_blob(dep5_original) != BASE_BLOBS[".reuse/dep5"]:
        raise ValueError("REUSE original byte identity mismatch")
    old_rows = old_source_scope.get("selected_original_files", [])
    dep_row = next((x for x in old_rows if x.get("path") == ".reuse/dep5"), None)
    if (not isinstance(dep_row, dict)
        or dep_row.get("sha256") != hashlib.sha256(dep5_original).hexdigest()):
        raise ValueError("REUSE source not bound to predecessor digest")
    declaration = dep5_original.decode("utf-8", errors="strict")
    # Exact standalone DEP-5 stanza; never silently reinterpret a glob to
    # include differently nested actual files.
    stanzas = declaration.strip().split("\n\n")
    matching = [block for block in stanzas
                if ("Files: " + STALE_DEP5_PATH) in block.splitlines()]
    if len(matching) != 1 or "License: CC0" not in matching[0].splitlines():
        raise ValueError("source REUSE Hedley declaration not found")
    if any(e["path"] == "hedley.hpp" for e in descendants["thirdparty"]["entries"]):
        raise ValueError("stale path unexpectedly exists; conclusion no longer valid")
    if not isinstance(headers, dict) or set(headers) != set(HEADERS):
        raise ValueError("exact pair of original Hedley headers required")
    proofs = []
    for path in sorted(HEADERS):
        original = headers[path]
        expected = HEADERS[path]
        if (type(original) is not bytes or not original or len(original) > 128_000
            or _git_blob(original) != expected):
            raise ValueError("pinned Hedley header blob mismatch")
        if _lookup(descendants["hedley"], path.rsplit("/", 1)[-1], "100644") != expected:
            raise ValueError("header not in the pinned Git tree")
        lines = original.decode("utf-8", errors="strict").splitlines()[:24]
        claims = [line.split("SPDX-License-Identifier:", 1)[1].strip()
                  for line in lines if "SPDX-License-Identifier:" in line]
        if claims != ["MIT"]:
            raise ValueError("unexpected SPDX header license declaration")
        proofs.append({
            "path": path, "original_git_blob_sha1": expected,
            "sha256": hashlib.sha256(original).hexdigest(),
            "bytes": len(original), "spdx_in_source_header": claims[0],
            "source_bytes_embedded": False,
        })
    return {
        "schema": "CGX-ALEXANDRIA-HEDLEY-NOTICE-RECONCILIATION/0.1",
        "status": "REUSE_PATH_MISMATCH_AND_SOURCE_SPDX_CONFLICT_CONFIRMED",
        "source_root": SOURCE_ROOT,
        "root_git_tree_sha1": ROOT_TREE,
        "source_dep5_git_blob_sha1": BASE_BLOBS[".reuse/dep5"],
        "source_dep5_sha256": hashlib.sha256(dep5_original).hexdigest(),
        "dep5_path_declared_as_cc0": STALE_DEP5_PATH,
        "dep5_exact_path_exists_in_pinned_tree": False,
        "actual_header_paths_and_claims": proofs,
        "conflict": {
            "kind": "NONMATCHING_DEP5_FILE_PATH_VS_REAL_HEADER_PATH_AND_SPDX",
            "dep5_source_claim": "CC0",
            "real_header_spdx_claim": "MIT",
            "claimed_cc0_applied_to_real_files": False,
            "effective_legal_relicensing_conclusion": "NOT_DETERMINED",
            "requires_source_owner_or_legal_review": True,
        },
        "related_original_nlohmann_scope": SOURCE_ROOT,
        "source_bytes_embedded": False,
        "whole_repository_licence_audit_complete": False,
        "distribution_approved": False,
        "native_dbr_verified": False,
        "canonical_object_id": None,
        "frontier": [
            "CONFIRM_HEDLEY_REUSE_DEP5_PATH_CORRECTION_WITH_UPSTREAM",
            "AUDIT_ADDITIONAL_HEDLEY_AND_THIRD_PARTY_LICENCE_PROVENANCE",
            "DO_NOT_RELICENSE_OR_PUBLISH_BASED_ON_STALE_DEP5_CLAIM",
            "NATIVE_OWNER_SOURCE_ROOT_DBR_READBACK",
        ],
    }
