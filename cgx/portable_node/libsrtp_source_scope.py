"""Bounded pinned libSRTP source and licence evidence under libdatachannel.

Reads exact upstream Git objects supplied as byte fixtures. This is not a
cryptographic implementation, interoperability test, audited dependency graph,
licence approval, live transport route, or canonical CGX object.
"""
from __future__ import annotations

import hashlib
from typing import Any

from cgx.portable_node.project_gitlink_evidence import _git_blob, _git_tree

PARENT_SOURCE = "git:paullouisageneau/libdatachannel@6b1e2e620f1e37f0eafeee702eaea0043cb305fd"
PARENT_PATH = "deps/libsrtp"
SOURCE_REV = "24b3bf8f19b6f5ab4cd2bcceb4f4064efca86fd5"
SOURCE_ROOT = f"git:cisco/libsrtp@{SOURCE_REV}"
GIT_TREE = "e49fe9508826d56c4932cacabc491e37fbcc37bb"
BLOBS = {
    "LICENSE": "af0a2ac312708a0f9d15aa68472e6863de0156ff",
    "README.md": "66a0013072f74dfd5303fc52334475d6e788ab42",
    "CMakeLists.txt": "01f007fd3196f54f11f43143fec7479dbf9ee6b6",
    "include/srtp_priv.h": "ee20d63c4f35fb45a2ea6b41a6d2b1a1e42a3d7b",
    "crypto/include/cipher.h": "43d453e6fe5460f2907a1fac9c687d555c8772c5",
}
DIRS = ("root", "include", "crypto", "crypto_include")
MAX_FILE_BYTES = 65536


def _entry(tree: dict, path: str, mode: str) -> str:
    found = [e for e in tree["entries"] if e["path"] == path and e["mode"] == mode]
    if len(found) != 1:
        raise ValueError("pinned Git file/directory entry missing")
    return found[0]["sha"]


def compile_libsrtp_scope(parent: dict, trees: dict, raw_files: dict[str, bytes]) -> dict[str, Any]:
    if (not isinstance(parent, dict)
        or parent.get("schema") != "CGX-ALEXANDRIA-LIBDATACHANNEL-SOURCE-SCOPE/0.1"
        or parent.get("source_root") != PARENT_SOURCE
        or parent.get("native_dbr_verified") is not False
        or parent.get("nested_gitlink_count") != 5):
        raise ValueError("untrusted pinned parent dependency ancestry")
    matches = [e for e in parent.get("nested_gitlinks", [])
               if isinstance(e, dict) and e.get("path") == PARENT_PATH]
    if (len(matches) != 1 or matches[0].get("pinned_commit_sha1") != SOURCE_REV
        or matches[0].get("source_acquired") is not False
        or matches[0].get("source_url") != "https://github.com/cisco/libsrtp.git"):
        raise ValueError("exact original libSRTP Gitlink identity mismatch")
    if (not isinstance(trees, dict)
        or trees.get("schema") != "CGX-LIBSRTP-PINNED-GIT-TREES/0.1"
        or trees.get("repo") != "cisco/libsrtp" or trees.get("commit") != SOURCE_REV
        or trees.get("root_tree_sha") != GIT_TREE):
        raise ValueError("untrusted original libSRTP tree")
    checked = {}
    for key in DIRS:
        value = trees.get(key)
        if not isinstance(value, dict) or value.get("truncated") is not False:
            raise ValueError("missing complete original Git tree")
        if value.get("sha") != _git_tree(value):
            raise ValueError("original Git tree SHA-1 mismatch")
        checked[key] = value
    if (checked["root"]["sha"] != GIT_TREE
        or _entry(checked["root"], "include", "040000") != checked["include"]["sha"]
        or _entry(checked["root"], "crypto", "040000") != checked["crypto"]["sha"]
        or _entry(checked["crypto"], "include", "040000") != checked["crypto_include"]["sha"]):
        raise ValueError("pinned Git tree ancestry mismatch")
    if not isinstance(raw_files, dict) or set(raw_files) != set(BLOBS):
        raise ValueError("exact five original R0 files required")
    records, content = [], {}
    for path in sorted(BLOBS):
        data = raw_files[path]
        if type(data) is not bytes or not data or len(data) > MAX_FILE_BYTES:
            raise ValueError("bounded original bytes required")
        if _git_blob(data) != BLOBS[path]:
            raise ValueError("original Git blob mismatch: " + path)
        if "/" not in path:
            folder, leaf = checked["root"], path
        elif path.startswith("include/"):
            folder, leaf = checked["include"], path.removeprefix("include/")
        elif path.startswith("crypto/include/"):
            folder, leaf = checked["crypto_include"], path.removeprefix("crypto/include/")
        else:
            raise ValueError("unsupported source fixture path")
        if _entry(folder, leaf, "100644") != BLOBS[path]:
            raise ValueError("original source absent from pinned Git tree")
        content[path] = data.decode("utf-8", errors="strict")
        records.append({
            "path": path,
            "bytes": len(data),
            "git_blob_sha1": BLOBS[path],
            "sha256": hashlib.sha256(data).hexdigest(),
            "original_r0_fixture": True,
            "bytes_embedded_in_r1": False,
        })
    license_text = content["LICENSE"]
    if not (license_text.startswith("/*")
            and "Copyright (c) 2001-2017 Cisco Systems, Inc." in license_text
            and "Redistribution and use in source and binary forms" in license_text
            and "Neither the name of the Cisco Systems, Inc." in license_text
            and "THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS" in license_text):
        raise ValueError("source licence notice is not as claimed")
    for path in ("include/srtp_priv.h", "crypto/include/cipher.h"):
        header = content[path][:2000]
        if ("Copyright (c) 2001-2017 Cisco Systems, Inc." not in header
                or "Neither the name of the Cisco Systems, Inc." not in header):
            raise ValueError("source header licence scope differs from root")
    readme = content["README.md"]
    build = content["CMakeLists.txt"]
    if (not ("libSRTP is distributed under the following license" in readme
             and "Secure Real-time" in readme
             and "3rd party (ie openssl/nss/etc) crypto backend" in readme
             and "project(libsrtp2 VERSION 2.8.0 LANGUAGES C)" in build)):
        raise ValueError("library description or optional crypto backend evidence missing")
    return {
        "schema": "CGX-ALEXANDRIA-LIBSRTP-SOURCE-SCOPE/0.1",
        "status": "FIVE_PINNED_R0_BLOBS_FOUR_GIT_TREES_PARTIAL_RIGHTS",
        "source_root": SOURCE_ROOT,
        "upstream_root_git_tree_sha1": GIT_TREE,
        "parent_source_root": PARENT_SOURCE,
        "parent_gitlink_path": PARENT_PATH,
        "original_file_count": len(records),
        "original_file_proofs": records,
        "licence_scopes": {
            "repository_notice": "CISCO_BSD_THREE_CONDITION_STYLE",
            "spdx_identification_authoritative": False,
            "original_license_text_verified": True,
            "two_internal_code_headers_verified": True,
            "all_source_files_reviewed": False,
            "required_notice_reproduction": True,
            "nonendorsement_condition": True,
            "optional_openssl_nss_backend_rights": "UNQUALIFIED",
            "whole_tree_third_party_rights": "UNQUALIFIED",
            "distribution_approved": False,
        },
        "capability_evidence": {
            "category": "C_SRTP_TRANSPORT_CRYPTO_LIBRARY",
            "description_from": "README_ONLY",
            "build_target_declared": "libsrtp2 VERSION 2.8.0 LANGUAGES C",
            "cryptography_validated": False,
            "compiled_or_executed": False,
            "network_interoperability_tested": False,
            "cgx_network_transport_registered": False,
        },
        "complete_repository_acquired": False,
        "third_party_dependencies_qualified": False,
        "source_bytes_embedded": False,
        "native_dbr_verified": False,
        "canonical_object_id": None,
        "frontier": [
            "AUDIT_FULL_TREE_AND_THIRD_PARTY_FILE_LICENSES",
            "QUALIFY_SELECTED_OPENSSL_NSS_BACKEND_LICENSES",
            "TEST_CRYPTO_AND_SRTP_WITH_APPROVED_BUILD_MATRIX",
            "REPRODUCE_FULL_SOURCE_DEPENDENCY_CLOSURE",
            "OWNER_APPROVED_SIGNED_NATIVE_CGX_DBR_READBACK",
        ],
    }
