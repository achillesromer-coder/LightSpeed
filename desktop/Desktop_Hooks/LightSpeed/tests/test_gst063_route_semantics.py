from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.web_integration import build_romer_web_integration


CANONICAL_OPERATIONS = {f"/operations/w{i}" for i in range(1, 7)}
CANONICAL_DATASPACES = {f"/w{i}/data" for i in range(1, 7)}
REMOVED_ROUTES = {"/workspaces", "/tools/calculators", *(f"/w{i}/work" for i in range(1, 7))}


def _route_set(items: list[dict]) -> set[str]:
    return {str(item["route"]) for item in items}


def test_gst063_canonical_source_route_semantics(tmp_path: Path) -> None:
    payload = build_romer_web_integration(tmp_path / "LightSpeed")
    website_routes = _route_set(payload["website_routes"])
    staged_routes = _route_set(payload["squarespace_routes"])

    assert CANONICAL_OPERATIONS <= website_routes
    assert CANONICAL_OPERATIONS <= staged_routes
    assert CANONICAL_DATASPACES <= website_routes
    assert CANONICAL_DATASPACES <= staged_routes
    assert "/library" in website_routes
    assert "/library" in staged_routes
    assert REMOVED_ROUTES.isdisjoint(website_routes)
    assert REMOVED_ROUTES.isdisjoint(staged_routes)

    route_ids = [item["route_id"] for item in payload["squarespace_routes"]]
    staged_route_list = [item["route"] for item in payload["squarespace_routes"]]
    assert len(route_ids) == len(set(route_ids))
    assert len(staged_route_list) == len(set(staged_route_list))

    dataspaces = {item["route"]: item for item in payload["website_routes"] if item["route"] in CANONICAL_DATASPACES}
    assert set(dataspaces) == CANONICAL_DATASPACES
    assert all(item["observed_status"] == "requires_auth_401" for item in dataspaces.values())


def test_gst063_committed_bridge_matches_canonical_route_semantics() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    bridge_path = repo_root / "config" / "web_drive_bridge.json"
    committed = json.loads(bridge_path.read_text(encoding="utf-8"))
    canonical = build_romer_web_integration(repo_root)

    committed_website = _route_set(committed["website_routes"])
    committed_staged = _route_set(committed["squarespace_routes"])
    canonical_website = _route_set(canonical["website_routes"])
    canonical_staged = _route_set(canonical["squarespace_routes"])

    assert committed_website == canonical_website
    assert committed_staged == canonical_staged
    assert REMOVED_ROUTES.isdisjoint(committed_website)
    assert REMOVED_ROUTES.isdisjoint(committed_staged)

    committed_data = {
        item["route"]: item["observed_status"]
        for item in committed["website_routes"]
        if item["route"] in CANONICAL_DATASPACES
    }
    assert committed_data == {route: "requires_auth_401" for route in CANONICAL_DATASPACES}
