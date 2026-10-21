"""Hypersomnia bounded project-source evidence, not an executable game import.

Compiles four pinned *real* Git source blobs from the already qualified game
index into a source-free, noncanonical Alexandria review receipt. It never
executes C++, resolves Git submodules, licenses artwork or fetches network data.
"""
from __future__ import annotations

import configparser
import hashlib
from pathlib import Path
from urllib.parse import urlsplit

PROJECT = "TeamHypersomnia/Hypersomnia"
PINNED_COMMIT = "ca177a1a9a73e9e4bf5bb00a00ff1a1905483bee"
PINNED_TREE = "fa8072faa28931a0940ce3599d4cfdfea529f88a"
CATALOGUE_COMMIT = "3a9ab8fc892a2cdadf8989a72ba7624a11e39cec"
CATALOGUE_REF = f"alexandria:external:index:{CATALOGUE_COMMIT}:28"
BLOBS = {
    "LICENSE.md": "dbbe3558157f5861bff35dcb37b328b679b0ccfd",
    "README.md": "aa0b39e83d1c3bc017d8ea81ab2e7e2550b7777f",
    ".gitmodules": "3c24be734f5fa84409787a4b332dc76f4877b86a",
    "src/main.cpp": "b697675c15ee4c0f1383674de85a9f4a1fa195c8",
}
SOURCE_ROOT = f"git:{PROJECT}@{PINNED_COMMIT}"
MAX_FILE_BYTES = 128 * 1024


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_project_source_candidate(blobs: dict[str, bytes], catalogue_packet: dict) -> dict:
    """Accept only four original verified blobs and one existing source index edge."""
    if not isinstance(blobs, dict) or set(blobs) != set(BLOBS):
        raise ValueError("exact four-file source scope required")
    if not isinstance(catalogue_packet, dict):
        raise ValueError("trusted catalogue receipt required")
    envelope = catalogue_packet.get("source_envelope", {})
    if not isinstance(envelope, dict):
        raise ValueError("catalogue identity invalid")
    origin = envelope.get("lineage", {})
    if (not isinstance(origin, dict) or origin.get("pinned_commit") != CATALOGUE_COMMIT
        or envelope.get("evidence_state") != "R0_VERIFIED_R1_CANDIDATE"):
        raise ValueError("game catalogue origin mismatch")
    proj = envelope.get("projections", [])
    if not isinstance(proj, list) or len(proj) != 1 or not isinstance(proj[0], dict):
        raise ValueError("missing game index projection")
    rows = proj[0].get("entries", [])
    selected = [row for row in rows if isinstance(row, dict)
                and row.get("candidate_ref") == CATALOGUE_REF]
    if (len(selected) != 1 or selected[0].get("label") != "Hypersomnia"
        or selected[0].get("source_links") != ["https://github.com/TeamHypersomnia/Hypersomnia"]
        or selected[0].get("upstream_rights") != "UNVERIFIED"
        or selected[0].get("project_bytes_acquired") is not False):
        raise ValueError("source index cannot authorize project promotion")
    docs = {}
    for path, expected_blob in BLOBS.items():
        original = blobs[path]
        if type(original) is not bytes or not original or len(original) > MAX_FILE_BYTES:
            raise ValueError("bounded exact original file bytes required")
        if _git_blob(original) != expected_blob:
            raise ValueError("upstream original Git blob mismatch for " + path)
        docs[path] = original.decode("utf-8", errors="strict")

    if (not docs["LICENSE.md"].lstrip().startswith("GNU AFFERO GENERAL PUBLIC LICENSE")
        or "Version 3, 19 November 2007" not in docs["LICENSE.md"]
        or "License: AGPL v3" not in docs["README.md"]):
        raise ValueError("AGPL repository licence assertion not independently supported")
    if not ("int main(" in docs["src/main.cpp"]
            and "hypersomnia_version" in docs["src/main.cpp"]):
        raise ValueError("bounded C++ entry-point function evidence missing")
    modules = configparser.ConfigParser(interpolation=None, strict=True)
    modules.read_string(docs[".gitmodules"])
    dependencies = []
    for section in modules.sections():
        if not section.startswith('submodule "') or not section.endswith('"'):
            raise ValueError("invalid Git submodule definition")
        path, url = modules.get(section, "path"), modules.get(section, "url")
        parsed = urlsplit(url)
        if (not path.startswith(("src/3rdparty/", "cmake/"))
            or ".." in Path(path).parts or parsed.scheme != "https"
            or not parsed.hostname or parsed.username or parsed.password):
            raise ValueError("invalid external source submodule reference")
        dependencies.append({
            "declared_path": path, "source_url": url,
            "pinned_submodule_git_commit": None,
            "licence_verified": False, "source_bytes_acquired": False,
            "evidence": "DECLARED_SUBMODULE_LINK_ONLY",
        })
    if len(dependencies) != 11:
        raise ValueError("unexpected source dependency count")

    records = [{
        "path": path, "byte_length": len(blobs[path]),
        "upstream_git_blob_sha1": BLOBS[path],
        "sha256": _sha256(blobs[path]),
        "exact_original_available_in_test_fixture": True,
        "source_bytes_in_compact_projection": False,
    } for path in sorted(BLOBS)]
    return {
        "schema": "CGX-ALEXANDRIA-PROJECT-SOURCE-SCOPE/0.1",
        "status": "PINNED_FOUR_FILE_R0_SOURCE_VERIFIED_R1_CANDIDATE",
        "repository": PROJECT,
        "source_root": SOURCE_ROOT,
        "git_commit": PINNED_COMMIT,
        "upstream_git_tree_sha1": PINNED_TREE,
        "related_game_index_ref": CATALOGUE_REF,
        "source_files": records,
        "source_file_count": len(records),
        "declared_submodules": dependencies,
        "declared_submodule_count": len(dependencies),
        "project_licence": {
            "repository_declared": "AGPL-3.0",
            "licence_text_source": f"{SOURCE_ROOT}:LICENSE.md",
            "readme_evidence_source": f"{SOURCE_ROOT}:README.md",
            "code_licence_attribution_review_required": True,
            "art_media_licensing": "UNVERIFIED",
            "third_party_dependency_licences": "UNVERIFIED",
            "distribution_and_network_copyleft_review": "REQUIRED",
        },
        "function_evidence": [{
            "kind": "CPP_PROGRAM_ENTRYPOINT_CANDIDATE",
            "evidence_file": f"{SOURCE_ROOT}:src/main.cpp",
            "textual_evidence": "int main(",
            "compiled": False,
            "executed": False,
            "physics_or_gameplay_verified": False,
            "functional_capability_admitted": False,
        }],
        "source_bytes_embedded": False,
        "whole_repository_acquired": False,
        "all_assets_acquired": False,
        "all_dependencies_acquired": False,
        "licence_release_approved": False,
        "canonical_object_id": None,
        "canon_admitted": False,
        "native_dbr_verified": False,
        "external_source_authority": "PINNED_UPSTREAM_GIT_COMMIT_NOT_LOCAL_FILE_NAME",
        "frontier": [
            "READ_GIT_TREE_FOR_SUBMODULE_GITLINK_SHA",
            "VERIFY_INDIVIDUAL_SOURCE_AND_DEPENDENCY_LICENCES",
            "VERIFY_ARTWORK_AUDIO_MAPS_FONTS_AND_THIRD_PARTY_ASSETS",
            "QUALIFY_ENGINE_BUILD_AND_RUNTIME",
            "RECEIPTED_OWNER_DB_R_READBACK",
        ],
    }
