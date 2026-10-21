"""Source-scoped libjuice evidence along the libdatachannel→Hypersomnia lineage.

Only bounded original Git blobs and four cryptographically reconstructed Git
directory objects are accepted. No C execution, native network handshake,
full-code licensing assertion, downstream distribution or DBR promotion.
"""
from __future__ import annotations

import hashlib

from cgx.portable_node.project_gitlink_evidence import _git_tree, _git_blob

SOURCE_COMMIT = "b89c792e3612faf2f12cf35bcc56857313a06be3"
SOURCE_ROOT = "git:paullouisageneau/libjuice@" + SOURCE_COMMIT
SOURCE_TREE = "3fced355fcfc050641cf2723cb7e2b6a392de4a2"
PARENT_PATH = "deps/libjuice"
BLOBS = {
    "LICENSE": "14e2f777f6c395e7e04ab4aa306bbcc4b0c1120e",
    "README.md": "b48490661ec71856e2764014f3b0b94e189495c9",
    "src/juice.c": "074823c86386c1d3946b8dc87a51cd0bf9267f2d",
    "src/picohash.h": "4fda232f12087204a2deab67444569890289c709",
    "include/juice/juice.h": "e43db6cbe98687db79f6be0e89b109c2381b5177",
}

def _lookup(tree: dict, name: str, mode: str) -> str:
    matched = [x for x in tree["entries"]
               if x["path"] == name and x["mode"] == mode]
    if len(matched) != 1:
        raise ValueError("missing exact original Git directory entry: " + name)
    return matched[0]["sha"]

def compile_libjuice_scope(parent: dict, trees: dict, originals: dict[str, bytes]) -> dict:
    if (not isinstance(parent, dict)
        or parent.get("schema") != "CGX-ALEXANDRIA-LIBDATACHANNEL-SOURCE-SCOPE/0.1"
        or parent.get("source_root") !=
            "git:paullouisageneau/libdatachannel@6b1e2e620f1e37f0eafeee702eaea0043cb305fd"
        or parent.get("native_dbr_verified") is not False
        or parent.get("nested_gitlink_count") != 5):
        raise ValueError("untrusted parent source-scope receipt")
    links = [e for e in parent.get("nested_gitlinks", [])
             if isinstance(e, dict) and e.get("path") == PARENT_PATH]
    if (len(links) != 1 or links[0].get("pinned_commit_sha1") != SOURCE_COMMIT
        or links[0].get("source_url") != "https://github.com/paullouisageneau/libjuice.git"
        or links[0].get("source_acquired") is not False):
        raise ValueError("pinned libjuice source ancestry not established")
    if (not isinstance(trees, dict)
        or trees.get("schema") != "CGX-LIBJUICE-PINNED-GIT-TREES/0.1"
        or trees.get("repo") != "paullouisageneau/libjuice"
        or trees.get("commit") != SOURCE_COMMIT
        or trees.get("root_tree_sha") != SOURCE_TREE):
        raise ValueError("untrusted upstream Git tree")
    checked = {}
    for key in ("root","src","include","include_juice"):
        value = trees.get(key)
        if not isinstance(value,dict) or value.get("truncated") is not False:
            raise ValueError("incomplete original Git tree")
        if value.get("sha") != _git_tree(value):
            raise ValueError("original Git tree SHA-1 mismatch: " + key)
        checked[key] = value
    if (checked["root"]["sha"] != SOURCE_TREE
        or _lookup(checked["root"],"src","040000") != checked["src"]["sha"]
        or _lookup(checked["root"],"include","040000") != checked["include"]["sha"]
        or _lookup(checked["include"],"juice","040000") != checked["include_juice"]["sha"]):
        raise ValueError("original parent-child Git tree ancestry mismatch")
    if not isinstance(originals,dict) or set(originals) != set(BLOBS):
        raise ValueError("exact five original source files required")
    records=[]
    texts={}
    for name in sorted(BLOBS):
        raw=originals[name]
        if type(raw) is not bytes or not raw or len(raw) > 65536:
            raise ValueError("bounded original bytes required: " + name)
        if _git_blob(raw) != BLOBS[name]:
            raise ValueError("original source Git blob mismatch: " + name)
        if name in ("LICENSE","README.md"):
            parent_tree, entry = checked["root"], name
        elif name.startswith("src/"):
            parent_tree, entry = checked["src"], name.split("/",1)[1]
        else:
            parent_tree, entry = checked["include_juice"], name.rsplit("/",1)[-1]
        if _lookup(parent_tree, entry, "100644") != BLOBS[name]:
            raise ValueError("source blob not in pinned original tree")
        texts[name]=raw.decode("utf-8", errors="strict")
        records.append({"path":name, "bytes":len(raw),
                        "git_blob_sha1":BLOBS[name],
                        "sha256":hashlib.sha256(raw).hexdigest(),
                        "original_r0_in_test_fixture":True,
                        "embedded_in_r1":False})
    if (not texts["LICENSE"].startswith("Mozilla Public License Version 2.0")
        or "License: MPL 2.0" not in texts["README.md"]
        or "libjuice is licensed under MPL 2.0" not in texts["README.md"]
        or not all("Mozilla Public" in texts[p][:500] and "License, v. 2.0" in texts[p][:500]
                   for p in ("src/juice.c","include/juice/juice.h"))):
        raise ValueError("first-party MPL notices unsupported by original bytes")
    picohash=texts["src/picohash.h"][:1200]
    if (not picohash.startswith("/*")
        or "The code is placed under public domain by Kazuho Oku" not in picohash
        or "MD5 implementation is based on a public domain implementation" not in picohash
        or "SHA224/SHA256 implementation is based on a public domain implementation" not in picohash):
        raise ValueError("picohash bundled distinct attribution notice mismatch")
    return {
        "schema":"CGX-ALEXANDRIA-LIBJUICE-SOURCE-SCOPE/0.1",
        "status":"FIVE_ORIGINAL_BLOBS_FOUR_GIT_TREES_PARTIAL_RIGHTS",
        "source_root":SOURCE_ROOT,
        "parent_source_root":parent["source_root"],
        "parent_gitlink_path":PARENT_PATH,
        "root_git_tree_sha1":SOURCE_TREE,
        "original_file_proofs":records,
        "original_file_count":len(records),
        "license_scopes":{
            "libjuice_first_party_mpl_2_0":{"original_license":True,
                "readme_claim":True, "two_original_code_header_notices":True,
                "all_repository_file_licences_reviewed":False},
            "bundled_picohash":{"claim":"PUBLIC_DOMAIN_AUTHOR_ASSERTION",
                "distinct_attributions":True,
                "independent_legal_validation":False,
                "rights_automatically_inherited_from_libjuice":False},
            "other_third_party_rights":"UNKNOWN",
            "distribution_approved":False,
        },
        "capability_descriptor":{
            "category":"C_UDP_ICE_NAT_TRAVERSAL",
            "evidence":"README_AND_DECLARED_API_SOURCE_ONLY",
            "build_executed":False,
            "network_connection_tested":False,
            "operational_transport_registered":False},
        "complete_repository_acquired":False,
        "complete_build_deps_qualified":False,
        "native_dbr_verified":False,
        "canonical_object_id":None,
        "source_bytes_embedded":False,
        "frontier":[
            "REVIEW_LIBJUICE_ALL_SOURCE_NOTICE_HEADERS",
            "VALIDATE_PICOHASH_PUBLIC_DOMAIN_STATEMENTS_BY_JURISDICTION",
            "REVIEW_OPTIONAL_NETTLE_DEPENDENCY_AND_PLATFORM_LICENSES",
            "SANDBOX_BUILD_AND_TEST_ICE_STUN_TURN_INTEROPERABILITY",
            "RECEIPTED_OWNER_SIGNED_CGX_NODE_READBACK"],
    }
