"""Bounded nlohmann/json R0 files -> noncanonical R1 source-and-rights candidate.

Only original selected Git blobs and complete ancestor Git trees are admitted.
Licence assertions are file-scoped; no compiler invocation or bytecode execution.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from cgx.portable_node.project_gitlink_evidence import _git_blob, _git_tree

ORIGIN = "nlohmann/json"
PINNED_COMMIT = "55f93686c01528224f448c19128836e7df245f72"
ROOT_TREE = "1eb780542e829bf1615828ed0d5f407497bbce7b"
PARENT = "git:paullouisageneau/libdatachannel@6b1e2e620f1e37f0eafeee702eaea0043cb305fd"
GITLINK_PATH = "deps/json"
BLOBS = {
    ".reuse/dep5": "06b1d37c1b2026bc363ae399a7a99bddec685ac6",
    "CITATION.cff": "8a70c17bc295dbe59ed2e717e87f47364959629c",
    "CMakeLists.txt": "88ef6f6617caabe54da1db240fb307678c5158ba",
    "LICENSE.MIT": "a1dacc8dbbd907c4b622ff1f08e279c27465dcbc",
    "LICENSES/BSD-3-Clause.txt": "ea890afbc70c94011b765722a95e2c8c7d4f1233",
    "include/nlohmann/detail/conversions/to_json.hpp": "ead45665f1be4c7dad58216210783b4ba03efe2a",
    "include/nlohmann/json_fwd.hpp": "a595ae4abf56705f609a654f4fa3a692dd45ced0",
}
TREE_PATHS = {
    "root": (),
    "include": ("include",),
    "include_nlohmann": ("include", "nlohmann"),
    "include_nlohmann_detail": ("include", "nlohmann", "detail"),
    "include_nlohmann_detail_conversions": ("include", "nlohmann", "detail", "conversions"),
    "reuse": (".reuse",),
    "licenses": ("LICENSES",),
}

def _find(tree: dict, path: str, mode: str) -> dict:
    matches = [e for e in tree["entries"] if e["path"] == path and e["mode"] == mode]
    if len(matches) != 1:
        raise ValueError("missing or duplicate exact Git tree entry " + path)
    return matches[0]

def compile_nlohmann_source_scope(parent: dict, tree_packet: dict,
                                  original: dict[str, bytes]) -> dict[str, Any]:
    if (not isinstance(parent, dict)
        or parent.get("schema") != "CGX-ALEXANDRIA-LIBDATACHANNEL-SOURCE-SCOPE/0.1"
        or parent.get("source_root") != PARENT
        or parent.get("nested_gitlink_count") != 5
        or parent.get("native_dbr_verified") is not False
        or parent.get("all_project_source_acquired") is not False):
        raise ValueError("untrusted parent source root/authority")
    matches = [x for x in parent.get("nested_gitlinks", [])
               if isinstance(x, dict) and x.get("path") == GITLINK_PATH]
    if (len(matches) != 1
        or matches[0].get("pinned_commit_sha1") != PINNED_COMMIT
        or matches[0].get("source_url") != "https://github.com/nlohmann/json.git"
        or matches[0].get("source_acquired") is not False):
        raise ValueError("missing exact upstream JSON Gitlink")
    if (not isinstance(tree_packet, dict)
        or tree_packet.get("schema") != "CGX-NLOHMANN-PINNED-GIT-TREE/0.1"
        or tree_packet.get("source_repo") != ORIGIN
        or tree_packet.get("commit") != PINNED_COMMIT
        or tree_packet.get("root_sha") != ROOT_TREE):
        raise ValueError("source Git tree identity mismatch")
    trees = tree_packet.get("trees")
    if not isinstance(trees, dict) or set(trees) != set(TREE_PATHS):
        raise ValueError("incomplete ancestor Git tree coverage")
    for name, parts in TREE_PATHS.items():
        tree = trees[name]
        if not isinstance(tree, dict) or _git_tree(tree) != tree.get("sha"):
            raise ValueError("original Git tree SHA-1 mismatch: " + name)
        if name == "root":
            if tree["sha"] != ROOT_TREE:
                raise ValueError("root Git tree SHA-1 mismatch")
        else:
            previous = "root"
            for step in parts[:-1]:
                previous = next(
                    (k for k, v in TREE_PATHS.items() if v == parts[:parts.index(step)+1]),
                    None,
                )
                if previous is None:
                    raise ValueError("ancestor tree path missing")
            parent_name = next((k for k, v in TREE_PATHS.items() if v == parts[:-1]), None)
            if parent_name is None:
                raise ValueError("unresolved Git tree parent")
            if _find(trees[parent_name], parts[-1], "040000")["sha"] != tree["sha"]:
                raise ValueError("Git parent/child tree chain mismatch: " + name)

    if not isinstance(original, dict) or set(original) != set(BLOBS):
        raise ValueError("exact seven original source files required")
    text = {}
    file_rows = []
    for path in sorted(BLOBS):
        raw = original[path]
        if (type(raw) is not bytes or not raw or len(raw) > 128_000
            or _git_blob(raw) != BLOBS[path]):
            raise ValueError("original Git blob mismatch " + path)
        path_components = path.split("/")
        parent_parts = tuple(path_components[:-1])
        parent_name = next((k for k, v in TREE_PATHS.items() if v == parent_parts), None)
        if parent_name is None:
            raise ValueError("missing source tree for selected path " + path)
        if _find(trees[parent_name], path_components[-1], "100644")["sha"] != BLOBS[path]:
            raise ValueError("source file absent from pinned Git tree")
        text[path] = raw.decode("utf-8", errors="strict")
        file_rows.append({
            "path": path, "original_git_blob_sha1": BLOBS[path],
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "source_bytes_in_projection": False,
        })

    manifest = text[".reuse/dep5"]
    if (not text["LICENSE.MIT"].startswith("MIT License")
        or "Copyright (c) 2013-2025 Niels Lohmann" not in text["LICENSE.MIT"]
        or "project(nlohmann_json VERSION 3.12.0 LANGUAGES CXX)" not in text["CMakeLists.txt"]
        or "version: 3.12.0" not in text["CITATION.cff"]
        or not all("SPDX-License-Identifier: MIT" in text[p][:550]
                   for p in ("include/nlohmann/json_fwd.hpp",
                             "include/nlohmann/detail/conversions/to_json.hpp"))):
        raise ValueError("first-party version/MIT licence claims do not match original files")
    notice_patterns = (
        ("*", "MIT"),
        ("include/nlohmann/thirdparty/hedley.hpp", "CC0"),
        ("tests/thirdparty/Fuzzer/*", "Apache-2.0"),
        ("tests/thirdparty/imapdl/*", "GPL-3.0-only"),
        ("tools/amalgamate/*", "BSD-3-Clause"),
    )
    for pattern, licence in notice_patterns:
        if f"Files: {pattern}\n" not in manifest:
            raise ValueError("missing REUSE source scope for " + pattern)
        block = manifest.split(f"Files: {pattern}\n", 1)[1].split("\nFiles:", 1)[0]
        if f"License: {licence}" not in block:
            raise ValueError("REUSE licence field mismatch " + pattern)
    if "Redistribution and use in source and binary forms" not in text["LICENSES/BSD-3-Clause.txt"]:
        raise ValueError("bundled BSD redistribution conditions missing")

    return {
        "schema": "CGX-ALEXANDRIA-NLOHMANN-SOURCE-SCOPE/0.1",
        "status": "SEVEN_ORIGINAL_R0_FILES_PINNED_R1_CANDIDATE",
        "source_root": f"git:{ORIGIN}@{PINNED_COMMIT}",
        "source_git_root_tree_sha1": ROOT_TREE,
        "parent_source_root": PARENT,
        "parent_gitlink_path": GITLINK_PATH,
        "version_declared": "3.12.0",
        "selected_original_files": file_rows,
        "selected_original_file_count": len(file_rows),
        "source_tree_ancestor_sha_verified": True,
        "repository_licence_declaration": "MIT",
        "scoped_reuse_declarations": [
            {"source_glob": pattern, "licence_declared": licence,
             "file_contents_qualified": pattern == "*"}
            for pattern, licence in notice_patterns],
        "licensing_review": {
            "first_party_mit_original_and_two_headers_verified": True,
            "third_party_hedley_manifest_path_consistency_verified": False,
            "tooling_and_test_file_licenses_qualified": False,
            "all_files_and_asset_licences_qualified": False,
            "distribution_approved": False,
        },
        "capability": {"descriptor": "C++ JSON parsing/serialization library",
                       "evidence": "SOURCE_HEADER_AND_CMAKE_DECLARATION_ONLY",
                       "compiled": False, "parsed_json_tested": False,
                       "runtime_interoperability_verified": False,
                       "canonical_capability_admitted": False},
        "whole_repository_source_acquired": False,
        "source_bytes_embedded": False,
        "native_dbr_verified": False,
        "canonical_object_id": None,
        "frontier": [
            "RECONCILE_REUSE_HEDLEY_PATH_VS_ORIGINAL_SOURCE_HEADERS",
            "QUALIFY_ALL_THIRD_PARTY_SOURCE_AND_TOOLING_LICENSES",
            "TEST_REAL_CXX_TOOLCHAIN_BUILD_AND_JSON_ROUNDTRIP",
            "VERIFY_NATIVE_SIGNED_OWNER_DBR_READBACK",
        ],
    }
