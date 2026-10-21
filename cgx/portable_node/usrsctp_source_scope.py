"""Bounded usrsctp original-source and per-file rights evidence.

Follows libdatachannel's pinned deps/usrsctp Gitlink to its immutable Git tree.
No executable SCTP, complete source, code-header coverage or release claims.
"""
from __future__ import annotations
import hashlib
from typing import Any

from cgx.portable_node.project_gitlink_evidence import _git_blob, _git_tree

REPO = "paullouisageneau/usrsctp"
COMMIT = "fec583d54493f879d2ae44a743423bf8a04371ab"
TREE_SHA = "7da97207e08e03af2b152f378f78e46f17f17e82"
USER_TREE_SHA = "2f0482c056c7ec0bf7fe525e9a08388fcfd4bd53"
NETINET_TREE_SHA = "74f9c8c35bd664c04012d57197e600c8fd051952"
PARENT_PATH = "deps/usrsctp"
BLOBS = {
    "LICENSE.md": "a2d1f989cffa9e6e672c0a38ecf89c762c475322",
    "README.md": "3d5ba38f3514f34ec7f283e36dd6685d90971820",
    "CMakeLists.txt": "c3467f27d01af4d25caddf197be590ab2f8137a4",
    "usrsctplib/user_environment.c": "ea52f0ada743c606e52c9f52dfd6a486a71a8b5f",
    "usrsctplib/netinet/sctp.h": "6129e77f9684d84e1939670f8c6a54f56b982558",
}
FILE_NOTICE = {
    "LICENSE.md": "BSD_3_CLAUSE_STYLE_REPOSITORY_NOTICE",
    "README.md": "PROJECT_DESCRIPTION_NOT_LICENSE_PROOF",
    "CMakeLists.txt": "BSD_3_CLAUSE_STYLE_FILE_HEADER",
    "usrsctplib/user_environment.c": "BSD_2_CLAUSE_STYLE_FILE_HEADER",
    "usrsctplib/netinet/sctp.h": "BSD_3_CLAUSE_SPDX_AND_FILE_HEADER",
}


def _tree_entry(tree: dict, path: str, mode: str) -> str:
    matches = [e for e in tree["entries"]
               if isinstance(e, dict) and e.get("path") == path
               and e.get("mode") == mode]
    if len(matches) != 1:
        raise ValueError("absent/duplicated source tree entry " + path)
    return matches[0]["sha"]


def compile_usrsctp_source_scope(
    parent: dict[str, Any], tree_fixture: dict[str, Any], originals: dict[str, bytes]
) -> dict[str, Any]:
    if (not isinstance(parent, dict)
        or parent.get("schema") != "CGX-ALEXANDRIA-LIBDATACHANNEL-SOURCE-SCOPE/0.1"
        or parent.get("nested_gitlink_count") != 5
        or parent.get("native_dbr_verified") is not False
        or parent.get("source_root") !=
           "git:paullouisageneau/libdatachannel@6b1e2e620f1e37f0eafeee702eaea0043cb305fd"):
        raise ValueError("unsupported existing source ancestry")
    matches = [row for row in parent.get("nested_gitlinks", []) if
               isinstance(row, dict) and row.get("path") == PARENT_PATH]
    if (len(matches) != 1 or matches[0].get("pinned_commit_sha1") != COMMIT
        or matches[0].get("source_url") != "https://github.com/paullouisageneau/usrsctp.git"
        or matches[0].get("source_acquired") is not False):
        raise ValueError("wrong libdatachannel pinned usrsctp Gitlink")
    if (not isinstance(tree_fixture, dict)
        or tree_fixture.get("schema") != "CGX-USRSCTP-PINNED-SOURCE-TREE-CHAIN/0.1"
        or tree_fixture.get("origin") != REPO
        or tree_fixture.get("pinned_commit") != COMMIT
        or tree_fixture.get("root_tree_sha") != TREE_SHA):
        raise ValueError("wrong usrsctp tree provenance")
    trees = {}
    for name, expected in (
        ("root", TREE_SHA), ("usrsctplib", USER_TREE_SHA),
        ("netinet", NETINET_TREE_SHA)
    ):
        tree = tree_fixture.get(name)
        if not isinstance(tree, dict) or tree.get("sha") != expected:
            raise ValueError("missing pinned " + name + " tree")
        if _git_tree(tree) != expected:
            raise ValueError("cryptographic Git tree mismatch: " + name)
        trees[name] = tree
    if (_tree_entry(trees["root"], "usrsctplib", "040000") != USER_TREE_SHA
        or _tree_entry(trees["usrsctplib"], "netinet", "040000") != NETINET_TREE_SHA):
        raise ValueError("parent/child SHA ancestry mismatch")
    for path, tree, name, mode in (
        ("LICENSE.md", "root", "LICENSE.md", "100644"),
        ("README.md", "root", "README.md", "100644"),
        ("CMakeLists.txt", "root", "CMakeLists.txt", "100644"),
        ("usrsctplib/user_environment.c", "usrsctplib", "user_environment.c", "100755"),
        ("usrsctplib/netinet/sctp.h", "netinet", "sctp.h", "100755"),
    ):
        if _tree_entry(trees[tree], name, mode) != BLOBS[path]:
            raise ValueError("file blob not present in exact tree " + path)

    if not isinstance(originals, dict) or set(originals) != set(BLOBS):
        raise ValueError("exact five original source files required")
    texts = {}
    source_records = []
    for path in sorted(BLOBS):
        raw = originals[path]
        if (type(raw) is not bytes or not raw or len(raw) > 32768
            or _git_blob(raw) != BLOBS[path]):
            raise ValueError("original Git source bytes mismatch " + path)
        texts[path] = raw.decode("utf-8", errors="strict")
        source_records.append({
            "path": path, "git_blob_sha1": BLOBS[path],
            "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw),
            "notice_scope": FILE_NOTICE[path],
            "raw_bytes_in_projection": False,
        })
    if (not texts["LICENSE.md"].startswith("Copyright (c) 2015")
        or "Neither the name of usrsctp" not in texts["LICENSE.md"]
        or "Redistributions in binary form must reproduce" not in texts["LICENSE.md"]
        or "userland SCTP stack" not in texts["README.md"]
        or "project(usrsctplib C)" not in texts["CMakeLists.txt"]
        or "Neither the name of the project" not in texts["CMakeLists.txt"][:2200]
        or "Redistributions in binary form must reproduce" not in texts["usrsctplib/user_environment.c"][:1800]
        or "Neither the name" in texts["usrsctplib/user_environment.c"][:1800]
        or "SPDX-License-Identifier: BSD-3-Clause" not in texts["usrsctplib/netinet/sctp.h"][:250]
        or "Neither the name of Cisco Systems" not in texts["usrsctplib/netinet/sctp.h"][:1600]):
        raise ValueError("per-file rights evidence does not match declared scope")
    return {
        "schema": "CGX-ALEXANDRIA-USRSCTP-SOURCE-SCOPE/0.1",
        "status": "FIVE_ORIGINAL_R0_FILES_AND_THREE_GIT_TREES_VERIFIED",
        "parent_source_ref": parent["source_root"],
        "parent_gitlink": PARENT_PATH,
        "source_root": f"git:{REPO}@{COMMIT}",
        "git_commit": COMMIT,
        "git_root_tree_sha1": TREE_SHA,
        "verified_git_tree_count": 3,
        "verified_original_file_count": len(source_records),
        "source_files": source_records,
        "rights": {
            "repository_licence_statement": "BSD-3-Clause-style with no-endorsement condition",
            "selected_user_environment_source": "BSD-2-Clause-style source header",
            "selected_netinet_sctp_header": "SPDX BSD-3-Clause and notice",
            "source_notice_coverage_complete": False,
            "all_project_assets_cleared": False,
            "full_redistribution_review_complete": False,
        },
        "capability": {
            "described": "userland SCTP stack",
            "compiled": False,
            "protocol_interoperability_tested": False,
            "CGX_Natural_Network_activated": False,
            "real_node_binding": False,
        },
        "repository_source_complete": False,
        "source_bytes_embedded": False,
        "native_dbr_verified": False,
        "canonical_object_id": None,
        "public_release_approved": False,
        "frontier": [
            "VERIFY_ALL_USRSCTP_SOURCE_LICENSE_HEADERS_AND_THIRD_PARTY_NOTICES",
            "QUALIFY_REMAINING_SOURCE_FILES_AND_PLATFORM_TARGETS",
            "TEST_REAL_SCTP_PROTOCOL_WITH_SIGNED_NODES",
            "OWNER_DB_R_READBACK_REQUIRED",
            "RECONCILE_MPL_LIBDATACHANNEL_AND_UPSTREAM_BSD_FILE_OBLIGATIONS",
        ],
    }
