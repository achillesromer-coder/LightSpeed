"""Read-only, deterministic cleanup eligibility for one living CGX installation.

Never mutates source, working trees, installed carriers, databases or releases.
Hash-identical bytes may share a *presentation card* but are not proof of
semantic-equivalent objects or permission to erase either reference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "desktop/LightSpeed_Runtime"))
from lightspeed_runtime.cgx_family_topology import build_cgx_family_topology

SCHEMA = "CGX-LIVING-CONSOLIDATION-REVIEW/0.1"


def _tracked(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z"], capture_output=True,
        timeout=25, check=False,
    )
    if result.returncode:
        raise ValueError("tracked Git scope unavailable; no cleanup can be authorized")
    return sorted(x.decode("utf-8") for x in result.stdout.split(b"\x00") if x)


def _classify_empty(relative: str) -> str:
    name = Path(relative).name
    if name == "__init__.py":
        return "RETAIN_PYTHON_PACKAGE_MARKER"
    lowered = relative.casefold().replace("\\", "/")
    if "/raphael/" in lowered or "/natural_phenonema/" in lowered:
        return "RETAIN_UNVERIFIED_RESEARCH_SCAFFOLD"
    return "RETAIN_UNRESOLVED_ZERO_BYTE_ASSET"


def build_living_consolidation_review(repo: Path, installed_root: Path) -> dict:
    repo = Path(repo).resolve(strict=True)
    installed_root = Path(installed_root).absolute()
    tracked = _tracked(repo)
    empty = []
    for relative in tracked:
        path = repo / relative
        if path.is_symlink() or not path.is_file():
            continue
        if not path.resolve().is_relative_to(repo):
            continue
        if path.stat().st_size == 0:
            empty.append({"path": relative, "disposition": _classify_empty(relative),
                          "deletion_eligible": False})
    topology = build_cgx_family_topology(installed_root)
    buckets = Counter(item["disposition"] for item in empty)
    root_alias = installed_root.is_dir() and installed_root.resolve() != installed_root
    manifest = {
        "schema": SCHEMA,
        "cgx_root": "cgx://cgx.cgx",
        "reference_root": str(installed_root),
        "physical_storage_root": str(installed_root.resolve()) if installed_root.is_dir() else None,
        "root_is_existing_alias": bool(root_alias),
        "tracked_source_count": len(tracked),
        "tracked_zero_byte_count": len(empty),
        "retained_zero_byte_source": empty,
        "retained_zero_by_kind": dict(sorted(buckets.items())),
        "installed_carrier_count": topology["installed_carrier_count"],
        "unique_carrier_hash_count": topology["unique_carrier_hash_count"],
        "one_card_per_unique_content": topology["content_groups"],
        "collapsed_display_aliases": topology["collapsed_alias_card_count"],
        "zero_byte_carrier_holds": topology["retained_empty_carrier_names"],
        "safe_delete_candidates": [],
        "no_semantic_equivalence_inferred": True,
        "no_new_database_or_runtime": True,
        "source_modification_performed": False,
        "file_deletion_performed": False,
        "native_mint_performed": False,
        "dataspace_network_mint_performed": False,
        "next_gate": "OWNER_VERIFIED_REFERENCE_GRAPH_AND_TESTED_ARCHIVE_BEFORE_ANY_REMOVAL",
    }
    receipt = json.dumps(manifest, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":")).encode("ascii")
    manifest["review_sha256"] = hashlib.sha256(receipt).hexdigest()
    return manifest


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--repo", type=Path, default=REPO_ROOT)
    cli.add_argument("--carriers", type=Path, default=Path("C:/UniSpace"))
    args = cli.parse_args()
    output = build_living_consolidation_review(args.repo, args.carriers)
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
