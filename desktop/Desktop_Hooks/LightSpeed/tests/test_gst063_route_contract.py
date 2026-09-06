from __future__ import annotations

from lightspeed_runtime.web_integration import LS_WEB_GO_ROUTES, build_romer_web_integration


CANONICAL_WORKSPACE_ROUTES = {
    "/operations/w1",
    "/operations/w2",
    "/operations/w3",
    "/operations/w4",
    "/operations/w5",
    "/operations/w6",
}

AUTH_GATED_DATASPACE_ROUTES = {
    "/w1/data",
    "/w2/data",
    "/w3/data",
    "/w4/data",
    "/w5/data",
    "/w6/data",
}

SUPERSEDED_WORKSPACE_ALIASES = {
    "/w1/work",
    "/w2/work",
    "/w3/work",
    "/w4/work",
    "/w5/work",
    "/w6/work",
}



def test_gst063_workspace_routes_use_operations_namespace(tmp_path) -> None:
    payload = build_romer_web_integration(tmp_path / "LightSpeed")
    staged_routes = {item["route"] for item in payload["squarespace_routes"]}

    assert CANONICAL_WORKSPACE_ROUTES <= staged_routes
    assert staged_routes.isdisjoint(SUPERSEDED_WORKSPACE_ALIASES)



def test_gst063_dataspace_routes_preserve_claim_gated_w_namespace(tmp_path) -> None:
    payload = build_romer_web_integration(tmp_path / "LightSpeed")
    website_routes = {item["route"]: item for item in payload["website_routes"]}

    for route in AUTH_GATED_DATASPACE_ROUTES:
        assert route in website_routes
        assert website_routes[route]["observed_status"] == "requires_auth_401"



def test_gst063_calculator_hub_uses_canonical_library_surface() -> None:
    staged_routes = {route for route, _group, _title, _gate in LS_WEB_GO_ROUTES}

    assert "/library" in staged_routes
    assert "/tools/calculators" not in staged_routes
