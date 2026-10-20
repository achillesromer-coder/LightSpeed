"""Source-stage private review endpoint contract; owner auth mocked only for route isolation."""
import hashlib
from pathlib import Path
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from lightspeed_runtime import ls_go_bridge

def fixture(tmp_path):
    root=tmp_path/"cgx_private_review"
    (root/"data").mkdir(parents=True)
    (root/"review"/"renders").mkdir(parents=True)
    (root/"review"/"mesh").mkdir()
    (root/"data"/"cgx_object_review_catalogue.json").write_bytes(b'{"status":"INTERNAL_REVIEW"}')
    (root/"data"/"component_geometry_atlas_public_review.json").write_bytes(b'{"record_count":411}')
    (root/"review"/"renders"/"diode.svg").write_bytes(b"<svg/>")
    (root/"review"/"mesh"/"diode.json").write_bytes(b'{"vertices":[]}')
    return root

@pytest.mark.parametrize("path",[
    "/api/v1/private-object-review/catalogue/cgx_object_review_catalogue.json",
    "/api/v1/private-object-review/atlas/component_geometry_atlas_public_review.json",
    "/api/v1/private-object-review/renders/diode.svg",
    "/api/v1/private-object-review/mesh/diode.json",
])
def test_all_private_endpoints_reject_missing_owner_token(tmp_path,monkeypatch,path):
    root=fixture(tmp_path)
    monkeypatch.setenv("CGX_PRIVATE_REVIEW_ROOT",str(root))
    client=TestClient(ls_go_bridge.create_app(tmp_path))
    r=client.get(path,headers={"X-LightSpeed-Owner-Confirmation":"legacy-confirmation-is-not-enough"})
    assert r.status_code==403
    assert b"INTERNAL_REVIEW" not in r.content
    assert r.headers.get("cache-control") != "public"

def test_mocked_owner_route_serves_only_allowlisted_private_assets(tmp_path,monkeypatch):
    root=fixture(tmp_path)
    monkeypatch.setenv("CGX_PRIVATE_REVIEW_ROOT",str(root))
    # This mock tests endpoint logic only, not the real credential/session store.
    def verify(_confirmation,*,session_token=None,**_kwargs):
        if session_token!="test-owner-session":
            raise HTTPException(status_code=403,detail="Revoked or invalid")
        return "test-owner"
    monkeypatch.setattr(ls_go_bridge,"_verified_owner_actor",verify)
    client=TestClient(ls_go_bridge.create_app(tmp_path))
    headers={"X-LightSpeed-Session":"test-owner-session"}
    for path in [
        "/api/v1/private-object-review/catalogue/cgx_object_review_catalogue.json",
        "/api/v1/private-object-review/atlas/component_geometry_atlas_public_review.json",
        "/api/v1/private-object-review/renders/diode.svg",
        "/api/v1/private-object-review/mesh/diode.json",
    ]:
        response=client.get(path,headers=headers)
        assert response.status_code==200,response.text
        assert response.headers["cache-control"]=="no-store, private"
        assert response.headers["x-content-type-options"]=="nosniff"
        assert response.headers["x-cgx-source-sha256"]==hashlib.sha256(response.content).hexdigest()
    bad=client.get("/api/v1/private-object-review/mesh/diode.svg",headers=headers)
    assert bad.status_code==404
    assert "private" not in bad.text.lower() or "review asset" in bad.text.lower()
    denied=client.get("/api/v1/private-object-review/mesh/diode.json",
                      headers={"X-LightSpeed-Session":"revoked"})
    assert denied.status_code==403

def test_no_configured_private_root_is_not_served_from_public_fallback(tmp_path,monkeypatch):
    monkeypatch.delenv("CGX_PRIVATE_REVIEW_ROOT",raising=False)
    monkeypatch.setattr(ls_go_bridge,"_verified_owner_actor",lambda *_args,**_kwargs:"owner")
    client=TestClient(ls_go_bridge.create_app(tmp_path))
    r=client.get("/api/v1/private-object-review/renders/diode.svg",
                 headers={"X-LightSpeed-Session":"mock-valid"})
    assert r.status_code==503
    assert "not available" in r.json()["detail"]
