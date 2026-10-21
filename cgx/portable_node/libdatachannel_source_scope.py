"""Bounded source/rights evidence for Hypersomnia's pinned libdatachannel.

Verifies the exact *parent* Gitlink, full root/deps Git tree objects, five
original first-party files and five nested Gitlink SHAs. This does not grant
rights to third-party nested dependency sources, binaries or CGX networking.
"""
from __future__ import annotations

import configparser
import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit

from cgx.portable_node.project_gitlink_evidence import _git_tree, _git_blob

PARENT_COMMIT = "ca177a1a9a73e9e4bf5bb00a00ff1a1905483bee"
PINNED_COMMIT = "6b1e2e620f1e37f0eafeee702eaea0043cb305fd"
ROOT_SHA = "5c8e8876492dde5196e2fc9e40e82a0d2f737f7c"
DEPS_SHA = "66c5f5feb1a0257f561f5112dbc6cfb36d2f6fe0"
ORIGIN = "paullouisageneau/libdatachannel"
PATH_IN_PARENT = "src/3rdparty/libdatachannel"
BLOBS = {
    "LICENSE": "14e2f777f6c395e7e04ab4aa306bbcc4b0c1120e",
    "README.md": "a9f3af9e81791cf3d8be495ba13222b1cd842c2d",
    ".gitmodules": "b7604c2fae62db7046edfd688cefc273dd31bd86",
    "include/rtc/rtc.hpp": "7f97941dec316f9405aa9732d28aa162dbe1c881",
    "src/peerconnection.cpp": "135f4585b4a59879fc19ecd85e9b85709ee0ace8",
}

def compile_libdatachannel_scope(
    parent_receipt: dict, trees: dict, blobs: dict[str, bytes]
) -> dict:
    if (not isinstance(parent_receipt, dict)
        or parent_receipt.get("schema") != "CGX-ALEXANDRIA-PINNED-GITLINK-EVIDENCE/0.1"
        or parent_receipt.get("source_project_root") !=
            f"git:TeamHypersomnia/Hypersomnia@{PARENT_COMMIT}"
        or parent_receipt.get("verified_gitlink_count") != 11
        or parent_receipt.get("canonical_promotion") is not False):
        raise ValueError("untrusted parent Gitlink receipt")
    links = [e for e in parent_receipt.get("resolved_gitlinks", [])
             if isinstance(e, dict) and e.get("declared_path") == PATH_IN_PARENT]
    if (len(links) != 1 or links[0].get("pinned_gitlink_commit") != PINNED_COMMIT
        or links[0].get("source_url") !=
        "https://github.com/paullouisageneau/libdatachannel.git"):
        raise ValueError("libdatachannel must match exact parent Gitlink")
    if (not isinstance(trees, dict)
        or trees.get("schema") != "CGX-LIBDATACHANNEL-PINNED-GIT-TREES/0.1"
        or trees.get("repo") != ORIGIN or trees.get("commit") != PINNED_COMMIT
        or trees.get("root_tree_sha") != ROOT_SHA):
        raise ValueError("untrusted libdatachannel tree provenance")
    root, deps = trees.get("root"), trees.get("deps")
    if not isinstance(root, dict) or not isinstance(deps, dict):
        raise ValueError("missing original Git tree")
    if (_git_tree(root) != ROOT_SHA or _git_tree(deps) != DEPS_SHA
        or root.get("sha") != ROOT_SHA or deps.get("sha") != DEPS_SHA):
        raise ValueError("Git tree source bytes or root mismatch")
    deps_dirs = [x for x in root["entries"]
                 if x.get("path") == "deps" and x.get("mode") == "040000"]
    if len(deps_dirs) != 1 or deps_dirs[0]["sha"] != DEPS_SHA:
        raise ValueError("nested deps tree is not linked to root")

    if not isinstance(blobs, dict) or set(blobs) != set(BLOBS):
        raise ValueError("exact five original project files required")
    texts = {}
    file_proofs = []
    for name in sorted(BLOBS):
        content = blobs[name]
        if (type(content) is not bytes or not content or len(content) > 65536
            or _git_blob(content) != BLOBS[name]):
            raise ValueError("original source Git blob mismatch: " + name)
        texts[name] = content.decode("utf-8", errors="strict")
        file_proofs.append({
            "path": name, "git_blob_sha1": BLOBS[name],
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content), "original_available_as_r0_fixture": True,
            "embedded_in_r1": False,
        })
    if (not texts["LICENSE"].startswith("Mozilla Public License Version 2.0")
        or "License: MPL 2.0" not in texts["README.md"]
        or "licensed under MPL 2.0 since version 0.18" not in texts["README.md"]
        or not all("Mozilla Public" in texts[p][:600] and "License, v. 2.0" in texts[p][:600]
                   for p in ("include/rtc/rtc.hpp", "src/peerconnection.cpp"))):
        raise ValueError("first-party MPL-2.0 notice mismatch")

    config = configparser.ConfigParser(interpolation=None, strict=True)
    config.read_string(texts[".gitmodules"])
    declared = []
    for section in config.sections():
        if not section.startswith('submodule "') or not section.endswith('"'):
            raise ValueError("unrecognised nested submodule")
        path = config.get(section, "path")
        url = config.get(section, "url")
        if not path.startswith("deps/") or ".." in Path(path).parts:
            raise ValueError("invalid nested path")
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            raise ValueError("invalid submodule URL")
        refs = [x for x in deps["entries"]
                if x.get("path") == path.removeprefix("deps/")
                and x.get("mode") == "160000"]
        if len(refs) != 1:
            raise ValueError("declared nested gitlink not in Git tree")
        declared.append({
            "path": path,
            "source_url": url,
            "pinned_commit_sha1": refs[0]["sha"],
            "source_acquired": False,
            "licence_verified": False,
        })
    actual = {"deps/" + x["path"] for x in deps["entries"] if x["mode"] == "160000"}
    if len(declared) != 5 or {x["path"] for x in declared} != actual:
        raise ValueError("nested Gitlink set differs from .gitmodules")
    declared.sort(key=lambda x: x["path"])
    return {
        "schema": "CGX-ALEXANDRIA-LIBDATACHANNEL-SOURCE-SCOPE/0.1",
        "status": "FIVE_R0_FILES_AND_FIVE_NESTED_GITLINKS_VERIFIED",
        "source_root": f"git:{ORIGIN}@{PINNED_COMMIT}",
        "upstream_root_git_tree_sha1": ROOT_SHA,
        "parent_source_root": parent_receipt["source_project_root"],
        "parent_gitlink_path": PATH_IN_PARENT,
        "original_file_proofs": file_proofs,
        "original_file_count": 5,
        "nested_gitlinks": declared,
        "nested_gitlink_count": len(declared),
        "first_party_licensing": {
            "declared": "MPL-2.0",
            "original_text_verified": True,
            "two_source_file_headers_verified": True,
            "all_source_file_headers_verified": False,
            "third_party_licences_verified": False,
            "release_rights_approved": False,
        },
        "capability_claims": {
            "described": "WebRTC/Data Channels, media transport and WebSockets",
            "evidence": "README_ONLY",
            "compiled": False, "network_interoperability_tested": False,
            "canonical_capability_admitted": False,
        },
        "all_project_source_acquired": False,
        "nested_dependencies_acquired": False,
        "media_assets_qualified": False,
        "source_bytes_embedded": False,
        "native_dbr_verified": False,
        "canonical_object_id": None,
        "frontier": [
            "CHECK_ALL_FIRST_PARTY_CODE_HEADERS_AND_NOTICE_FILES",
            "RESOLVE_NESTED_FIVE_DEPENDENCY_SOURCE_AND_LICENCES",
            "CHECK_MPL_NOTICE_COPYRIGHT_FILE_LEVEL_OBLIGATIONS",
            "BUILD_AND_TEST_REAL_WEBRTC_WITH_APPROVED_TOOLCHAIN",
            "NATIVE_SIGNED_OWNER_DBR_READBACK",
        ],
    }
