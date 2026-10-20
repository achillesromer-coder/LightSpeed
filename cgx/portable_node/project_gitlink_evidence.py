"""Source-backed Hypersomnia Gitlink dependency proof and one bounded OpenAL notice scope.

No full repository checkout, binary execution, third-party licence grant,
asset publication, canonical Object_ID, node admission or network session.
Verifies Git tree contents cryptographically, not merely displayed API SHAs.
"""
from __future__ import annotations

import configparser
import hashlib
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

PROJECT_COMMIT = "ca177a1a9a73e9e4bf5bb00a00ff1a1905483bee"
PROJECT_TREE = "fa8072faa28931a0940ce3599d4cfdfea529f88a"
PROJECT_ROOT = f"git:TeamHypersomnia/Hypersomnia@{PROJECT_COMMIT}"
LINKED_OPENAL_COMMIT = "b2c48f7718ef3fcf67921a8b6534c4914e328970"
OPENAL_TREE = "6db1a18dffdcd9a7022c979354f99417581e5dd0"
OPENAL_ORIGIN = "kcat/openal-soft"
OPENAL_BLOBS = {
    "COPYING": "8d5d0000656d57b6fc8118c1078aa3172b7c02ec",
    "README.md": "09f9ec24d909c2fe10b4aacff6c87bd3a7aeda68",
    "LICENSE-pffft": "5f1a8493f23e2823e9f27f05215954da158b760c",
}
FIXTURE_TREE_NAMES = ("root", "src", "cmake", "src_3rdparty")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _git_tree(tree: dict) -> str:
    if not isinstance(tree, dict) or not isinstance(tree.get("entries"), list):
        raise ValueError("bounded original Git tree entries required")
    entries = tree["entries"]
    if not 0 < len(entries) <= 2000 or tree.get("truncated") is not False:
        raise ValueError("incomplete or oversized Git tree")
    seen = set()
    parts = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "mode", "type", "sha"}:
            raise ValueError("invalid Git tree record")
        path, mode, kind, sha = (entry[k] for k in ("path", "mode", "type", "sha"))
        if (not isinstance(path, str) or not path or "/" in path
            or path in (".", "..") or "\0" in path or path in seen
            or type(mode) is not str or mode not in ("100644", "100755", "120000", "040000", "160000")
            or kind != {"040000": "tree", "160000": "commit",
                        "100644": "blob", "100755": "blob", "120000": "blob"}[mode]
            or not isinstance(sha, str) or not HEX40.fullmatch(sha)):
            raise ValueError("invalid Git tree identity, path or mode")
        seen.add(path)
        rawname = path.encode("utf-8")
        sortname = rawname + (b"/" if kind == "tree" else b"")
        # Git serializes tree modes without the leading zero: 040000 -> 40000.
        record = f"{int(mode, 8):o}".encode() + b" " + rawname + b"\0" + bytes.fromhex(sha)
        parts.append((sortname, record))
    body = b"".join(record for _, record in sorted(parts))
    return hashlib.sha1(b"tree " + str(len(body)).encode() + b"\0" + body).hexdigest()


def _tree_lookup(tree: dict, path: str, mode: str) -> str:
    matches = [e for e in tree["entries"] if e["path"] == path and e["mode"] == mode]
    if len(matches) != 1:
        raise ValueError("missing exact Git path: " + path)
    return matches[0]["sha"]


def compile_submodule_scope(tree_fixture: dict, gitmodules: bytes,
                            openal_files: dict[str, bytes], base_scope: dict) -> dict[str, Any]:
    if (not isinstance(tree_fixture, dict)
        or tree_fixture.get("schema") != "CGX-UPSTREAM-PINNED-GIT-TREES-FIXTURE/0.1"
        or tree_fixture.get("source_commit") != PROJECT_COMMIT
        or tree_fixture.get("root_tree_sha") != PROJECT_TREE):
        raise ValueError("project tree origin mismatch")
    if (not isinstance(base_scope, dict) or base_scope.get("source_root") != PROJECT_ROOT
        or base_scope.get("git_commit") != PROJECT_COMMIT
        or base_scope.get("source_file_count") != 4
        or base_scope.get("canon_admitted") is not False):
        raise ValueError("existing source-scope ancestry invalid")
    trees = {}
    for name in FIXTURE_TREE_NAMES:
        tree = tree_fixture.get(name)
        if not isinstance(tree, dict) or not isinstance(tree.get("sha"), str):
            raise ValueError("missing pinned source tree")
        computed = _git_tree(tree)
        if computed != tree["sha"]:
            raise ValueError("Git tree object SHA-1 mismatch")
        trees[name] = tree
    if (trees["root"]["sha"] != PROJECT_TREE
        or _tree_lookup(trees["root"], "src", "040000") != trees["src"]["sha"]
        or _tree_lookup(trees["root"], "cmake", "040000") != trees["cmake"]["sha"]
        or _tree_lookup(trees["src"], "3rdparty", "040000") != trees["src_3rdparty"]["sha"]):
        raise ValueError("Git tree parent-child chain mismatch")
    if type(gitmodules) is not bytes:
        raise ValueError("original .gitmodules bytes required")
    source_entry = next((f for f in base_scope.get("source_files", [])
                         if f.get("path") == ".gitmodules"), None)
    if (not isinstance(source_entry, dict)
        or hashlib.sha256(gitmodules).hexdigest() != source_entry.get("sha256")
        or _git_blob(gitmodules) != source_entry.get("upstream_git_blob_sha1")):
        raise ValueError("Git submodule declarations are not original pinned bytes")
    config = configparser.ConfigParser(interpolation=None, strict=True)
    config.read_string(gitmodules.decode("utf-8", errors="strict"))
    mappings = []
    for section in config.sections():
        if not (section.startswith('submodule "') and section.endswith('"')):
            raise ValueError("unrecognised gitmodule section")
        path, url = config.get(section, "path"), config.get(section, "url")
        if not isinstance(path, str) or not isinstance(url, str):
            raise ValueError("missing dependency declaration")
        if path.startswith("src/3rdparty/"):
            name = path.removeprefix("src/3rdparty/")
            gitlink = _tree_lookup(trees["src_3rdparty"], name, "160000")
        elif path.startswith("cmake/"):
            name = path.removeprefix("cmake/")
            gitlink = _tree_lookup(trees["cmake"], name, "160000")
        else:
            raise ValueError("undeclared upstream gitlink path family")
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or parsed.username or parsed.password
            or not parsed.hostname or ".." in Path(path).parts):
            raise ValueError("invalid submodule URL")
        mappings.append({"declared_path": path, "source_url": url,
                         "pinned_gitlink_commit": gitlink,
                         "proof": "PARENT_ROOT_TO_SUBTREE_TO_GITLINK_SHA1_VERIFIED",
                         "third_party_source_complete": False,
                         "licence_release_approved": False})
    if len(mappings) != 11 or len({x["declared_path"] for x in mappings}) != 11:
        raise ValueError("missing or duplicate pinned gitlink")
    expected_links = {x["declared_path"] for x in mappings}
    actual_links = {"cmake/" + e["path"] for e in trees["cmake"]["entries"] if e["mode"] == "160000"}
    actual_links.update({"src/3rdparty/" + e["path"] for e in trees["src_3rdparty"]["entries"] if e["mode"] == "160000"})
    if expected_links != actual_links:
        raise ValueError("declared gitlinks differ from complete pinned trees")
    mappings.sort(key=lambda x: x["declared_path"])
    openal_link = next(x for x in mappings if x["declared_path"] == "src/3rdparty/openal-soft")
    if (openal_link["pinned_gitlink_commit"] != LINKED_OPENAL_COMMIT
        or openal_link["source_url"] != "https://github.com/kcat/openal-soft.git"):
        raise ValueError("OpenAL licence evidence not tied to pinned project link")
    if not isinstance(openal_files, dict) or set(openal_files) != set(OPENAL_BLOBS):
        raise ValueError("exact three-file licence-notice scope required")
    original = {}
    for name, sha in OPENAL_BLOBS.items():
        raw = openal_files[name]
        if type(raw) is not bytes or not raw or len(raw) > 128 * 1024 or _git_blob(raw) != sha:
            raise ValueError("OpenAL original notice Git blob mismatch: " + name)
        original[name] = raw.decode("utf-8", errors="strict")
    if (not original["COPYING"].lstrip().startswith("GNU LIBRARY GENERAL PUBLIC LICENSE")
        or "Version 2, June 1991" not in original["COPYING"]
        or "LGPL-licensed" not in original["README.md"]
        or "A modified PFFFT is included" not in original["LICENSE-pffft"]):
        raise ValueError("distinct license scope is not supported by pinned sources")
    notices = [{"path": name, "git_blob_sha1": OPENAL_BLOBS[name],
                "sha256": hashlib.sha256(openal_files[name]).hexdigest(),
                "byte_length": len(openal_files[name])} for name in sorted(OPENAL_BLOBS)]
    return {
        "schema": "CGX-ALEXANDRIA-PINNED-GITLINK-EVIDENCE/0.1",
        "status": "PARENT_GITLINKS_VERIFIED_OPENAL_NOTICES_PARTIAL",
        "source_project_root": PROJECT_ROOT,
        "pinned_project_tree": PROJECT_TREE,
        "resolved_gitlinks": mappings,
        "verified_gitlink_count": len(mappings),
        "openal_source_ref": f"git:{OPENAL_ORIGIN}@{LINKED_OPENAL_COMMIT}",
        "openal_upstream_tree_pointer": OPENAL_TREE,
        "openal_notice_originals": notices,
        "openal_licensing": {
            "readme_claim": "LGPL-licensed OpenAL Soft implementation",
            "bundled_copying_text": "GNU Library General Public License version 2",
            "separate_pffft_notice": "redistribution-with-notice-conditions",
            "exact_source_code_licence_for_every_file": "UNVERIFIED",
            "other_third_party_licences_and_artwork": "UNVERIFIED",
            "distribution_approved": False,
        },
        "all_11_dependency_sources_acquired": False,
        "all_11_dependency_licences_qualified": False,
        "all_game_assets_rights_qualified": False,
        "live_build_executed": False,
        "native_dbr_verified": False,
        "canonical_promotion": False,
        "source_bytes_embedded": False,
        "frontier": [
            "AUDIT_OPENAL_CODE_FILE_HEADERS_AND_REMAINING_NOTICES",
            "RESOLVE_OTHER_10_SUBMODULE_RIGHTS_AT_PINNED_COMMITS",
            "QUALIFY_GAME_ART_AUDIO_MAPS_FONTS_RIGHTS",
            "BUILD_IN_ISOLATED_TOOLCHAIN_AND_MEASURE",
            "NATIVE_SIGNED_OWNER_SOURCE_DBR_READBACK",
        ],
    }
