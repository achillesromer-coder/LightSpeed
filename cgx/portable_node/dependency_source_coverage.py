"""Source-only consolidation of the five already-qualified libdatachannel gitlinks.

This is a deterministic materialized VIEW of existing R0/R1 evidence receipts,
not another source store, canonical graph, permission system or network engine.
The five original project samples are NOT complete dependency closure.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

PARENT_ROOT = "git:paullouisageneau/libdatachannel@6b1e2e620f1e37f0eafeee702eaea0043cb305fd"
SCOPE_PATHS = {
    "deps/json": "cgx/review/alexandria_nlohmann_json_source_scope_20261021.json",
    "deps/libjuice": "cgx/review/alexandria_libjuice_source_scope_20261021.json",
    "deps/libsrtp": "cgx/review/alexandria_libsrtp_source_scope_20261021.json",
    "deps/plog": "cgx/review/alexandria_plog_source_scope_20261021.json",
    "deps/usrsctp": "cgx/review/alexandria_usrsctp_source_scope_20261021.json",
}
EXPECTED_REPOSITORIES = {
    "deps/json": "nlohmann/json",
    "deps/libjuice": "paullouisageneau/libjuice",
    "deps/libsrtp": "cisco/libsrtp",
    "deps/plog": "SergiusTheBest/plog",
    "deps/usrsctp": "paullouisageneau/usrsctp",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _sha256_json(data: dict[str, Any]) -> str:
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_rows(scope: dict) -> tuple[int, list[dict]]:
    if "selected_original_files" in scope:
        return scope.get("selected_original_file_count"), scope["selected_original_files"]
    if "source_files" in scope:
        return scope.get("verified_original_file_count"), scope["source_files"]
    return scope.get("original_file_count"), scope.get("original_file_proofs")


def _partial_licensing(scope: dict) -> bool:
    # Every branch must remain fail-closed when a licence review is promoted.
    if "licensing_review" in scope:
        return scope["licensing_review"].get("distribution_approved") is False
    if "license_scopes" in scope:
        return scope["license_scopes"].get("distribution_approved") is False
    if "licence_scopes" in scope:
        return scope["licence_scopes"].get("distribution_approved") is False
    if "licensing" in scope:
        return scope["licensing"].get("distribution_approved") is False
    if "rights" in scope:
        return (scope.get("public_release_approved") is False
                and scope["rights"].get("full_redistribution_review_complete") is False)
    return False


def consolidate_dependency_source_samples(parent: dict, children: dict[str, dict]) -> dict:
    """Reject missing source ancestors, receipt tampering and rights promotion.

    SHA-256 receipts commit to supplied *projection JSON*, not the complete
    original source blobs. Original bytes must remain available at their
    existing upstream/fixture roots with independently verified adapters.
    """
    if (not isinstance(parent, dict)
        or parent.get("schema") != "CGX-ALEXANDRIA-LIBDATACHANNEL-SOURCE-SCOPE/0.1"
        or parent.get("source_root") != PARENT_ROOT
        or parent.get("upstream_root_git_tree_sha1") != "5c8e8876492dde5196e2fc9e40e82a0d2f737f7c"
        or parent.get("nested_gitlink_count") != 5
        or parent.get("native_dbr_verified") is not False
        or parent.get("canonical_object_id") is not None
        or parent.get("source_bytes_embedded") is not False
        or parent.get("all_project_source_acquired") is not False
        or parent.get("nested_dependencies_acquired") is not False
        or parent.get("first_party_licensing", {}).get("release_rights_approved") is not False):
        raise ValueError("untrusted or promoted libdatachannel parent")
    if not isinstance(children, dict) or set(children) != set(SCOPE_PATHS):
        raise ValueError("exact five child source scopes required")
    links = parent.get("nested_gitlinks")
    if not isinstance(links, list) or len(links) != 5:
        raise ValueError("incomplete pinned parent links")
    parent_by_path = {}
    for link in links:
        if not isinstance(link, dict):
            raise ValueError("invalid pinned link")
        path, commit = link.get("path"), link.get("pinned_commit_sha1")
        if (path in parent_by_path or path not in SCOPE_PATHS
            or not isinstance(commit, str) or not HEX40.fullmatch(commit)
            or link.get("source_acquired") is not False
            or link.get("licence_verified") is not False):
            raise ValueError("untrusted or promoted pinned child link")
        expected_url = "https://github.com/" + EXPECTED_REPOSITORIES[path] + ".git"
        if link.get("source_url") != expected_url:
            raise ValueError("child source origin does not match gitlink")
        parent_by_path[path] = link
    if set(parent_by_path) != set(children):
        raise ValueError("child link root set mismatch")

    rows = []
    for path in sorted(SCOPE_PATHS):
        scope = children[path]
        link = parent_by_path[path]
        if not isinstance(scope, dict):
            raise ValueError("invalid child receipt")
        expected_root = ("git:" + EXPECTED_REPOSITORIES[path] + "@"
                         + link["pinned_commit_sha1"])
        parent_ref = scope.get("parent_source_root", scope.get("parent_source_ref"))
        child_path = scope.get("parent_gitlink_path", scope.get("parent_gitlink"))
        count, source_rows = _source_rows(scope)
        if (scope.get("source_root") != expected_root
            or parent_ref != PARENT_ROOT
            or child_path != path
            or scope.get("native_dbr_verified") is not False
            or scope.get("canonical_object_id") is not None
            or scope.get("source_bytes_embedded") is not False
            or not isinstance(scope.get("frontier"), list)
            or not scope["frontier"]
            or not _partial_licensing(scope)
            or type(count) is not int or count < 1 or count > 50
            or not isinstance(source_rows, list) or len(source_rows) != count):
            raise ValueError("child ancestry, rights or declared source sample mismatch: " + path)
        filenames = set()
        for source in source_rows:
            if not isinstance(source, dict):
                raise ValueError("invalid original file proof: " + path)
            name = source.get("path")
            git = source.get("git_blob_sha1", source.get("original_git_blob_sha1"))
            sha = source.get("sha256")
            if (not isinstance(name, str) or not name or name in filenames
                or not isinstance(git, str) or not HEX40.fullmatch(git)
                or not isinstance(sha, str) or not HEX64.fullmatch(sha)):
                raise ValueError("missing or duplicated original file digest: " + path)
            filenames.add(name)
        # Remaining R0 samples are evidence of *part* of the repo, not closure.
        for full_flag in ("complete_repository_acquired", "whole_repository_acquired",
                          "whole_repository_source_acquired", "repository_source_complete"):
            if full_flag in scope and scope[full_flag] is not False:
                raise ValueError("unproven full repository source promotion: " + path)
        rows.append({
            "gitlink_path": path,
            "pinned_commit_sha1": link["pinned_commit_sha1"],
            "source_root": expected_root,
            "existing_receipt_path": SCOPE_PATHS[path],
            "receipt_projection_sha256": _sha256_json(scope),
            "original_files_with_byte_proofs": count,
            "source_file_sample_complete": True,
            "whole_repository_source_complete": False,
            "source_licence_scope": "PARTIAL_NOT_RELEASE_APPROVED",
            "dependency_rights_proven": False,
            "functional_network_capability_proven": False,
            "frontier": sorted(set(scope["frontier"])),
            "canonical_object_id": None,
        })

    return {
        "schema": "CGX-ALEXANDRIA-NESTED-SOURCE-COVERAGE-LEDGER/0.1",
        "status": "ALL_FIVE_GITLINKS_HAVE_PARTIAL_ORIGINAL_SOURCE_EVIDENCE",
        "authority": "NONCANONICAL_READ_ONLY_PROJECTION_OF_EXISTING_RECEIPTS",
        "parent_source_root": PARENT_ROOT,
        "parent_receipt_projection_sha256": _sha256_json(parent),
        "parent_existing_receipt_path":
            "cgx/review/alexandria_libdatachannel_source_scope_20261021.json",
        "source_dependency_edges": rows,
        "direct_gitlinks_total": 5,
        "direct_gitlinks_with_bounded_r0_samples": 5,
        "direct_gitlinks_whole_repository_acquired": 0,
        "child_original_file_proofs_total": sum(x["original_files_with_byte_proofs"] for x in rows),
        "parent_original_file_proofs_total": parent["original_file_count"],
        "original_source_file_proofs_across_distinct_roots":
            parent["original_file_count"] + sum(x["original_files_with_byte_proofs"] for x in rows),
        "full_dependency_and_licence_closure": False,
        "network_transport_qualified": False,
        "native_signed_two_node_readback": False,
        "sai_service_activated": False,
        "source_bytes_embedded": False,
        "canonical_promotion": False,
        "owner_release_authorized": False,
        "next_gates": [
            "REVIEW_FULL_CODE_TREE_AND_3RD_PARTY_ASSETS_PER_DEPENDENCY",
            "RESOLVE_HEDLEY_AND_PICOHASH_FILE_LEVEL_LICENCES",
            "BUILD_AND_TEST_SELECTED_DEPENDENCIES_IN_ISOLATED_TOOLCHAIN",
            "VERIFY_CGX_SIGNED_NODE_EXCHANGE_WITH_REAL_TWO_NODE_READBACK",
            "VERIFY_PUBLIC_PRIVATE_SEPARATION_BEFORE_SITE_RELEASE",
        ],
    }
