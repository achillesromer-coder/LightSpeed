"""Read-only nine-selector CGX/UniSpace family linkage from one registry.

Installed .cgx carriers are observed by exact hashed bytes, not imported,
copied, parsed as executable code, qualified or minted. Hash-equal names are
recorded as aliases, never independent objects.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from pathlib import Path
from typing import Any

from lightspeed_runtime.cgx_capability_registry import (
    DEFAULT_ROUTES_PATH,
    DEFAULT_SHORTCALLS_PATH,
    load_capability_routes,
    load_selector_shortcalls,
    selector_profile,
)

SCHEMA = "CGX-UNISPACE-FAMILY-TOPOLOGY/0.1"
MAX_CARRIERS = 32
MAX_CARRIER_BYTES = 16 * 1024 * 1024


def build_cgx_family_topology(
    installed_root: Path = Path(r"C:\UniSpace"),
) -> dict[str, Any]:
    """Classify registered selectors and local carrier names without hydration."""
    routes = load_capability_routes()
    catalogue = load_selector_shortcalls()
    profiles = []
    for name in sorted(catalogue["selectors"]):
        profile = selector_profile(name, routes=routes, shortcalls=catalogue)
        states = Counter(str(route["state"]) for route in profile["routes"].values())
        profiles.append({
            "selector": name,
            "registered_shortcalls": len(profile["shortcalls"]),
            "available_routes": states.get("available", 0),
            "gated_routes": states.get("gated", 0),
            "other_routes": sum(n for state, n in states.items() if state not in {"available", "gated"}),
            "preferred_floors": list(profile.get("floors") or []),
            "toolkits": list(profile.get("toolkits") or []),
            "native_execution_verified": False,
            "native_mint_verified": False,
        })

    root = Path(installed_root).expanduser()
    carrier_status = "UNAVAILABLE"
    carriers: list[dict] = []
    excluded: list[str] = []
    empty_carrier_names: list[str] = []
    if root.is_dir() and not root.is_symlink():
        carrier_status = "OBSERVED_READ_ONLY"
        names = sorted((p for p in root.iterdir() if p.suffix.lower() == ".cgx"),
                       key=lambda p: p.name.lower())
        if len(names) > MAX_CARRIERS:
            raise ValueError("CGX installed carrier count exceeds bounded review")
        for p in names:
            if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
                excluded.append(p.name)
                continue
            stat = p.stat()
            if stat.st_size == 0:
                empty_carrier_names.append(p.name)
                excluded.append(p.name)
                continue
            if not 0 < stat.st_size <= MAX_CARRIER_BYTES:
                excluded.append(p.name)
                continue
            h = hashlib.sha256()
            with p.open("rb") as stream:
                for block in iter(lambda: stream.read(262144), b""):
                    h.update(block)
            carriers.append({
                "name": p.name,
                "sha256": h.hexdigest(),
                "bytes": stat.st_size,
                "source_observed": True,
                "contents_exposed": False,
                "mint_admitted": False,
            })
    groups: dict[str, list[str]] = {}
    for carrier in carriers:
        groups.setdefault(carrier["sha256"], []).append(carrier["name"])
    aliases = [
        {"sha256": digest, "names": sorted(names)}
        for digest, names in sorted(groups.items())
        if len(names) > 1
    ]
    by_name = {item["name"]: item for item in carriers}
    content_groups = []
    for digest, names in sorted(groups.items()):
        ordered = sorted(names, key=lambda name: (name.casefold(), name))
        representative = ordered[0]
        content_groups.append({
            "sha256": digest,
            "display_name": representative,
            "reference_names": ordered,
            "bytes": by_name[representative]["bytes"],
            "collapsed_alias_count": len(ordered) - 1,
            "same_bytes_not_semantic_equivalence": True,
            "native_object_identity_verified": False,
            "safe_to_delete_aliases": False,
            "presentation_only": True,
        })
    content_groups.sort(key=lambda item: item["display_name"].casefold())
    root_source_sha = {
        "capability_routes": hashlib.sha256(DEFAULT_ROUTES_PATH.read_bytes()).hexdigest(),
        "selector_shortcalls": hashlib.sha256(DEFAULT_SHORTCALLS_PATH.read_bytes()).hexdigest(),
    }
    return {
        "schema": SCHEMA,
        "registry_source_sha256": root_source_sha,
        "selector_count": len(profiles),
        "selectors": profiles,
        "installed_carrier_state": carrier_status,
        "installed_carrier_count": len(carriers),
        "unique_carrier_hash_count": len(groups),
        "carriers": carriers,
        "hash_equal_aliases": aliases,
        "content_groups": content_groups,
        "collapsed_alias_card_count": len(carriers) - len(content_groups),
        "excluded_carrier_names": excluded,
        "retained_empty_carrier_names": empty_carrier_names,
        "storage_root_is_alias": root.is_dir() and root.absolute() != root.resolve(),
        "safe_delete_candidates": [],
        "deletion_performed": False,
        "source_observation_only": True,
        "carrier_write_performed": False,
        "database_write_performed": False,
        "grex_source_permissions_inferred": False,
        "native_mint_verified": False,
        "data_space_network_mint_verified": False,
        "general_intelligence_verified": False,
    }
