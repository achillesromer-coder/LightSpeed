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


def _asset_path(repo: Path, relative: str, tracked: set[str]) -> Path | None:
    if (not isinstance(relative, str) or not relative or
            "\\" in relative or relative.startswith("/") or
            relative.startswith("../") or "/../" in relative or
            relative not in tracked):
        return None
    path = repo / relative
    if (path.is_symlink() or not path.is_file() or
            not path.resolve().is_relative_to(repo)):
        return None
    return path


def _asset_record(repo: Path, relative: str, tracked: set[str]) -> dict:
    path = _asset_path(repo, relative, tracked)
    if path is None:
        return {"path": relative, "state": "HOLD_MISSING_OR_UNTRACKED", "sha256": None}
    if not path.stat().st_size:
        return {"path": relative, "state": "HOLD_EMPTY", "sha256": None}
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": relative, "state": "OBSERVED_SOURCE_BYTES",
            "size_bytes": path.stat().st_size, "sha256": digest.hexdigest(),
            "production_or_scientific_authority": False}


def review_digital_twin_assets(repo: Path, tracked: list[str]) -> dict:
    """Read-only asset relationships from the existing digital-twin manifest.

    A mesh or visual preview being present never confers CAD tolerances,
    fabrication certification, scientific verification or mint authority.
    """
    name = "data/digital-twin/complete_digital_asset_manifest_2026-09-12.json"
    source = _asset_path(repo, name, set(tracked))
    if source is None:
        return {"state": "HOLD_MANIFEST_UNAVAILABLE", "manifest_path": name,
                "linked_assets": [], "missing_asset_paths": [],
                "duplicate_byte_groups": [], "promotion_authorized": False}
    document = json.loads(source.read_text(encoding="utf-8"))
    if (not isinstance(document, dict) or
            document.get("schema") != "achilles_complete_digital_asset_bundle_v1"
            or not isinstance(document.get("assets"), list)
            or len(document["assets"]) > 100):
        raise ValueError("invalid digital-twin asset manifest; review held")
    tracked_set = set(tracked)
    ids: set[str] = set()
    linked = []
    all_files = []
    expected_names = set()
    for entry in document["assets"]:
        if not isinstance(entry, dict):
            raise ValueError("invalid digital-twin object entry")
        twin = entry.get("twin_id")
        mesh_ref = entry.get("file")
        if (not isinstance(twin, str) or not twin or
                not all(c.islower() or c.isdigit() or c == "_" for c in twin) or
                twin in ids):
            raise ValueError("invalid or duplicated digital-twin identity")
        ids.add(twin)
        if mesh_ref != f"assets/models/{twin}.obj":
            raise ValueError("unexpected or unbounded mesh reference")
        refs = [("mesh", mesh_ref),
                ("preview", f"assets/previews/{twin}_six_view.png")]
        refs.extend((f"type1_svg_{i:02d}", f"assets/type1-svg/{twin}/T1-{i:02d}.svg")
                    for i in range(8))
        files = []
        for role, relative in refs:
            if relative in expected_names:
                raise ValueError("multiple twin entries reference same asset path")
            expected_names.add(relative)
            record = _asset_record(repo, relative, tracked_set)
            record["role"] = role
            files.append(record)
            all_files.append(record)
        readiness = ("COMPLETE_SOURCE_REFERENCES"
                     if all(record["state"] == "OBSERVED_SOURCE_BYTES" for record in files)
                     else "HOLD_MISSING_OR_EMPTY_LAYERS")
        linked.append({"twin_id": twin, "asset_id": entry.get("asset_id"),
                       "representation_class": entry.get("representation_class"),
                       "status": readiness, "files": files,
                       "native_mesh_verified": False,
                       "fabrication_authorized": False,
                       "licence_verified": False})
    digest_groups: dict[str, list[str]] = {}
    for rec in all_files:
        if rec["sha256"]:
            digest_groups.setdefault(rec["sha256"], []).append(rec["path"])
    duplicates = [
        {"sha256": digest, "paths": sorted(names), "safe_to_delete": False}
        for digest, names in sorted(digest_groups.items()) if len(names) > 1
    ]
    missing = sorted(rec["path"] for rec in all_files
                     if rec["state"] != "OBSERVED_SOURCE_BYTES")
    linked.sort(key=lambda x: x["twin_id"])
    return {"state": "OBSERVED_READ_ONLY" if not missing else "HOLD_ASSET_GAPS",
            "manifest_path": name,
            "manifest_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "asset_family_count": len(linked),
            "layer_path_count": len(all_files),
            "observed_layer_count": len(all_files) - len(missing),
            "linked_assets": linked,
            "missing_asset_paths": missing,
            "duplicate_byte_groups": duplicates,
            "linked_files_are_source_proxies_only": True,
            "promotion_authorized": False,
            "deletion_authorized": False}


def review_cgx_domain_contracts(repo: Path, tracked: list[str]) -> dict:
    """Reconcile parent/child contracts by stable domain ID, not carrier hash."""
    folder = "cgx/domain_templates/"
    tracked_set = set(tracked)
    names = ("domains.json", "domain_child_identity_registry.json",
             "cognigrex_parent_topology.json")
    source = {}
    parsed = {}
    for name in names:
        relative = folder + name
        asset = _asset_record(repo, relative, tracked_set)
        source[name] = asset
        if asset["state"] != "OBSERVED_SOURCE_BYTES":
            return {"state": "HOLD_MISSING_PARENT_CONTRACT",
                    "sources": source, "children": [], "shared_contracts": [],
                    "missing_source_paths": [relative],
                    "semantic_authority_verified": False,
                    "native_mint_authorized": False}
        parsed[name] = json.loads((repo / relative).read_text(encoding="utf-8"))
    manifest = parsed["domains.json"]
    identity = parsed["domain_child_identity_registry.json"]
    topology = parsed["cognigrex_parent_topology.json"]
    if (not isinstance(manifest, dict) or not isinstance(identity, dict) or
            not isinstance(topology, dict) or
            not isinstance(manifest.get("domains"), dict) or
            not isinstance(manifest.get("shared_contracts"), dict) or
            not isinstance(identity.get("children"), dict) or
            not isinstance(topology.get("root"), dict) or
            manifest.get("parent_filespace", {}).get("file") != "Cognigrex.cgx" or
            identity.get("root", {}).get("semantic_object_id") != "cgx:root:cognigrex"):
        raise ValueError("invalid or mismatched CGX domain parent contracts")
    expected = ("romer", "eco", "emassc")
    if set(manifest["domains"]) != set(expected):
        raise ValueError("unexpected domain families in parent registry")
    child_refs = []
    missing = []
    root_children = topology["root"].get("children")
    if not isinstance(root_children, list):
        raise ValueError("parent topology children unavailable")
    known = {row.get("id"): row for row in root_children if isinstance(row, dict)}
    if set(known) != set(expected):
        raise ValueError("parent topology domain identities disagree")
    domain_count = 0
    for domain in expected:
        d = manifest["domains"][domain]
        ident = identity["children"].get(domain)
        ref = known[domain]
        if not isinstance(d, dict) or not isinstance(ident, dict):
            raise ValueError("invalid child domain definition")
        if any(ident.get(k) != v for k, v in {
            "domain_id": domain,
            "semantic_object_id": "cgx:domain:" + domain,
            "filespace": d.get("file"),
            "namespace": d.get("namespace"),
            "parent_semantic_object_id": "cgx:root:cognigrex",
        }.items()) or ref.get("file") != d.get("file"):
            raise ValueError("inconsistent child semantic identity or carrier filename")
        if ref.get("principal_agent") != d.get("principal_agent"):
            raise ValueError("child principal agent disagreement")
        entry = {}
        for k in ("semantic_library", "type_registry", "relation_registry"):
            value = d.get(k)
            if not isinstance(value, str) or "/" in value or "\\" in value:
                raise ValueError("invalid child registry reference")
            relative = folder + value
            record = _asset_record(repo, relative, tracked_set)
            entry[k] = record
            if record["state"] != "OBSERVED_SOURCE_BYTES":
                missing.append(relative)
        domain_count += len(entry)
        child_refs.append({
            "domain": domain,
            "semantic_object_id": ident["semantic_object_id"],
            "filespace": ident["filespace"],
            "principal_agent": ref["principal_agent"],
            "registries": entry,
            "domain_semantic_authority_proven": False,
            "source_readback_only": True,
        })
    nested = manifest["domains"]["emassc"].get("children", {}).get("lightspeed")
    ls_identity = identity["children"].get("lightspeed")
    if (not isinstance(nested, dict) or not isinstance(ls_identity, dict) or
            nested.get("file") != "LS.cgx" or
            ls_identity.get("filespace") != nested["file"] or
            ls_identity.get("parent_semantic_object_id") != "cgx:domain:emassc" or
            ls_identity.get("semantic_object_id") != "cgx:domain:lightspeed"):
        raise ValueError("LightSpeed child-parent identity mismatch")
    shared_refs = []
    values = manifest["shared_contracts"]
    for key, value in sorted(values.items()):
        if (not isinstance(key, str) or not key or
                not isinstance(value, str) or not value.endswith((".json", ".md")) or
                "/" in value or "\\" in value):
            raise ValueError("unsafe shared parent contract filename")
        relative = folder + value
        record = _asset_record(repo, relative, tracked_set)
        shared_refs.append({"id": key, **record})
        if record["state"] != "OBSERVED_SOURCE_BYTES":
            missing.append(relative)
    if len({item["path"] for item in shared_refs}) != len(shared_refs):
        raise ValueError("shared parent contracts must have unique paths")
    return {
        "state": "SOURCE_REFERENCES_PRESENT" if not missing else "HOLD_MISSING_CONTRACTS",
        "parent_semantic_object_id": "cgx:root:cognigrex",
        "parent_carrier": "Cognigrex.cgx",
        "contract_sources": source,
        "children": child_refs,
        "child_domain_count": len(child_refs),
        "child_registry_count": domain_count,
        "nested_lightspeed": {
            "semantic_object_id": ls_identity["semantic_object_id"],
            "filespace": nested["file"], "parent_id": "cgx:domain:emassc",
            "native_admitted": False,
        },
        "shared_contract_count": len(shared_refs),
        "shared_contracts": shared_refs,
        "missing_source_paths": sorted(set(missing)),
        "source_hash_readback_only": True,
        "semantic_authority_verified": False,
        "native_mint_authorized": False,
        "source_grants_verified": False,
        "cross_grex_mutation_performed": False,
        "no_duplicate_registries_created": True,
    }


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
        "digital_twin_asset_linkage": review_digital_twin_assets(repo, tracked),
        "cross_grex_contract_linkage": review_cgx_domain_contracts(repo, tracked),
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
