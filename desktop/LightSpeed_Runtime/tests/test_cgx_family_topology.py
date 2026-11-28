from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.cgx_family_topology import build_cgx_family_topology


def test_uses_all_existing_selector_profiles_without_executable_grants(tmp_path):
    surface = build_cgx_family_topology(tmp_path)
    assert surface["selector_count"] == 9
    selectors = {x["selector"] for x in surface["selectors"]}
    assert {"achilles", "neo", "athene", "raphael",
            "cognigrex", "romer-grex", "eco-grex",
            "emassc", "lightspeed"} == selectors
    assert all(x["registered_shortcalls"] > 0 and
               x["native_execution_verified"] is False
               for x in surface["selectors"])
    assert surface["installed_carrier_state"] == "OBSERVED_READ_ONLY"
    assert surface["installed_carrier_count"] == 0
    assert not surface["native_mint_verified"]


def test_content_equal_carriers_are_aliases_not_new_objects(tmp_path):
    (tmp_path / "LightSpeed.cgx").write_bytes(b"same carrier")
    (tmp_path / "LS.cgx").write_bytes(b"same carrier")
    (tmp_path / "Eco.cgx").write_bytes(b"independent source")
    (tmp_path / "not-a-carrier.txt").write_text("ignored")
    result = build_cgx_family_topology(tmp_path)
    assert result["installed_carrier_count"] == 3
    assert result["unique_carrier_hash_count"] == 2
    assert [x["names"] for x in result["hash_equal_aliases"]] == [
        ["LS.cgx", "LightSpeed.cgx"]
    ]
    assert all(x["mint_admitted"] is False and
               x["contents_exposed"] is False
               for x in result["carriers"])


def test_missing_installation_remains_unverified(tmp_path):
    surface = build_cgx_family_topology(tmp_path / "not-mounted")
    assert surface["installed_carrier_state"] == "UNAVAILABLE"
    assert surface["installed_carrier_count"] == 0
    assert not surface["data_space_network_mint_verified"]


def test_family_topology_route_requires_verifiable_owner(tmp_path, monkeypatch):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient
    from lightspeed_runtime import ls_go_bridge

    class DummyDB:
        def execute_query(self, *args, **kwargs):
            return []
        def execute_update(self, *args, **kwargs):
            return 0

    monkeypatch.setattr(ls_go_bridge, "_try_get_services",
                        lambda root: (DummyDB(), object()))
    monkeypatch.setattr(ls_go_bridge, "CredentialStore", lambda db: object())

    def verify_owner(_confirmation, *, session_token=None, **_kwargs):
        if session_token != "valid-test-session":
            raise HTTPException(status_code=403, detail="Owner denied")
        return "owner"

    monkeypatch.setattr(ls_go_bridge, "_verified_owner_actor", verify_owner)
    monkeypatch.setattr(ls_go_bridge, "build_cgx_family_topology",
                        lambda: build_cgx_family_topology(tmp_path))
    with TestClient(ls_go_bridge.create_app(tmp_path)) as client:
        path = "/api/v1/cgx/family/topology"
        assert client.get(path).status_code == 403
        assert client.get(path, headers={
            "X-LightSpeed-Session": "forged"
        }).status_code == 403
        response = client.get(path, headers={
            "X-LightSpeed-Session": "valid-test-session"
        })
        assert response.status_code == 200
        body = response.json()
        assert body["selector_count"] == 9
        assert body["database_write_performed"] is False
        assert body["native_mint_verified"] is False
        assert response.headers.get("cache-control") == "no-store"


def test_grouped_content_projection_collapses_alias_cards_but_preserves_names(tmp_path):
    for name, payload in {
        "LightSpeed.cgx": b"identical",
        "LS.cgx": b"identical",
        "Eco.cgx": b"different",
    }.items():
        (tmp_path / name).write_bytes(payload)
    (tmp_path / "not-accepted.cgx").write_bytes(b"")
    group = build_cgx_family_topology(tmp_path)
    assert group["unique_carrier_hash_count"] == 2
    assert len(group["content_groups"]) == 2
    assert group["collapsed_alias_card_count"] == 1
    assert group["retained_empty_carrier_names"] == ["not-accepted.cgx"]
    assert group["safe_delete_candidates"] == []
    assert group["deletion_performed"] is False
    content = next(x for x in group["content_groups"] if x["collapsed_alias_count"])
    assert content["reference_names"] == ["LightSpeed.cgx", "LS.cgx"]
    assert content["display_name"] == "LightSpeed.cgx"
    assert content["bytes"] == len(b"identical")
    assert content["same_bytes_not_semantic_equivalence"] is True
    assert content["safe_to_delete_aliases"] is False
    assert content["native_object_identity_verified"] is False
    assert len({ref for card in group["content_groups"] for ref in card["reference_names"]}) == 3


def test_cgx_group_presentation_cannot_resolve_missing_root_to_mint(tmp_path):
    result = build_cgx_family_topology(tmp_path / "absent")
    assert result["content_groups"] == []
    assert result["retained_empty_carrier_names"] == []
    assert result["storage_root_is_alias"] is False
    assert result["safe_delete_candidates"] == []
    assert not result["native_mint_verified"]
