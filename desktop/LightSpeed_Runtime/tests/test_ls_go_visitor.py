from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from lightspeed_runtime.ls_go_visitor import register_visitor_routes


class LocalDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        schema = Path(__file__).resolve().parents[1] / "lightspeed_runtime" / "ls_go_visitor_schema.sql"
        self.conn.executescript(schema.read_text(encoding="utf-8"))

    def execute_query(self, sql, params=()):
        return [dict(row) for row in self.conn.execute(sql, params).fetchall()]

    def execute_update(self, sql, params=()):
        with self.conn:
            return self.conn.execute(sql, params).rowcount


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("LIGHTSPEED_VISITOR_REVIEW_ENABLED", "1")
    monkeypatch.setenv("LIGHTSPEED_VISITOR_RECEIPT_KEY", "A" * 48)
    app = FastAPI()
    register_visitor_routes(app, LocalDatabase(), lambda token: "NCNB" if token == "OWNER" else (_ for _ in ()).throw(HTTPException(403, "owner session missing")))
    return TestClient(app)


def test_visitor_is_not_anonymous_operator(client):
    assert client.get("/api/v1/visitor/capabilities").status_code == 200
    assert client.get("/api/v1/visitor/me").status_code == 401
    assert client.post("/api/v1/visitor/interaction", json={"kind": "question", "lens": "neo", "text": "Hello"}).status_code == 401
    assert client.get("/api/v1/visitor/owner-review").status_code != 200


def test_bounded_four_seats_and_consent(client):
    invites = []
    for _ in range(4):
        r = client.post("/api/v1/visitor/invites", json={}, headers={"X-LightSpeed-Session": "OWNER"})
        assert r.status_code == 200
        invites.append(r.json())
    assert client.post("/api/v1/visitor/invites", json={}, headers={"X-LightSpeed-Session": "OWNER"}).status_code == 409
    registration = {"invite_token": invites[0]["invite_token"], "name": "Reviewer One",
                    "theme": "forest", "lens": "neo", "consent": True,
                    "background": "Engineering", "intent": "Independent assessment"}
    assert client.post("/api/v1/visitor/enroll", json={**registration, "consent": False}).status_code == 400
    response = client.post("/api/v1/visitor/enroll", json=registration)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["identity_assurance"] == "INVITATION_POSSESSION_ONLY"
    assert client.post("/api/v1/visitor/enroll", json=registration).status_code == 403
    session = {"X-LightSpeed-Visitor-Session": data["visitor_session"]}
    me = client.get("/api/v1/visitor/me", headers=session)
    assert me.status_code == 200
    assert me.json()["handshake"]["background"] == "Engineering"
    interaction = client.post("/api/v1/visitor/interaction",
        json={"kind": "model_request", "lens": "neo", "text": "Show a geometric model"},
        headers=session)
    assert interaction.status_code == 200
    assert interaction.json()["status"] == "PENDING_PUBLIC_SAFE_RESOLVER"
    assert interaction.json()["model"] is None
    assert interaction.json()["answer"] is None
    assert interaction.json()["receipt"]["canonical_cgx_ingestion"] is False
    owner = client.get("/api/v1/visitor/owner-review", headers={"X-LightSpeed-Session": "OWNER"})
    assert owner.status_code == 200
    assert owner.json()["canonical_cgx_ingestion"] is False
    assert len(owner.json()["events"]) == 2
    assert owner.json()["chain_verified"] is True
    assert client.post("/api/v1/visitor/logout", headers=session).status_code == 200
    assert client.get("/api/v1/visitor/me", headers=session).status_code == 401


def test_privacy_withdrawal_revokes_session_and_records_request(client):
    invitation = client.post("/api/v1/visitor/invites", json={}, headers={"X-LightSpeed-Session": "OWNER"}).json()
    enrollment = client.post("/api/v1/visitor/enroll", json={
        "invite_token": invitation["invite_token"], "name": "A reviewer",
        "consent": True, "theme": "orbit", "lens": "alexandria",
    }).json()
    headers = {"X-LightSpeed-Visitor-Session": enrollment["visitor_session"]}
    wrong = client.post("/api/v1/visitor/privacy-request", json={"action": "nothing"}, headers=headers)
    assert wrong.status_code == 400
    copy = client.post("/api/v1/visitor/privacy-request", json={"action": "export"}, headers=headers)
    assert copy.status_code == 200
    assert copy.json()["state"] == "OWNER_REVIEW_REQUIRED"
    assert copy.json()["automated_deletion_performed"] is False
    withdraw = client.post("/api/v1/visitor/privacy-request", json={"action": "withdraw_consent"}, headers=headers)
    assert withdraw.status_code == 200
    assert client.get("/api/v1/visitor/me", headers=headers).status_code == 401
    review = client.get("/api/v1/visitor/owner-review", headers={"X-LightSpeed-Session": "OWNER"}).json()
    assert review["chain_verified"] is True
    assert any(event["event_type"] == "privacy_request" for event in review["events"])


def test_reissue_retains_seat_and_revokes_prior_unused_invite(client):
    original = client.post("/api/v1/visitor/invites", json={"reviewer_id":"RV-A"}, headers={"X-LightSpeed-Session":"OWNER"}).json()
    newer = client.post("/api/v1/visitor/invites", json={"reviewer_id":"RV-A"}, headers={"X-LightSpeed-Session":"OWNER"}).json()
    assert newer["reviewer_id"] == original["reviewer_id"]
    response = client.post("/api/v1/visitor/enroll", json={"invite_token":original["invite_token"],"name":"A reviewer","theme":"orbit","lens":"neo","consent":True})
    assert response.status_code == 403


def test_linked_url_is_unverified_and_never_retrieved(client):
    invite = client.post("/api/v1/visitor/invites", json={}, headers={"X-LightSpeed-Session": "OWNER"}).json()
    account = client.post("/api/v1/visitor/enroll", json={
        "invite_token": invite["invite_token"], "name":"A reviewer",
        "theme":"orbit", "lens":"alexandria", "consent":True}).json()
    head = {"X-LightSpeed-Visitor-Session": account["visitor_session"]}
    for bad in ("http://example.org/profile","https://127.0.0.1/profile",
                "https://internal.local/account", "https://example.org/profile?token=secret"):
        response = client.post("/api/v1/visitor/interaction", json={
            "kind":"linked_url", "lens":"alexandria", "provider":"github", "text":bad}, headers=head)
        assert response.status_code == 400
    accepted = client.post("/api/v1/visitor/interaction", json={
        "kind":"linked_url", "lens":"alexandria", "provider":"github",
        "text":"https://github.com/example"}, headers=head)
    assert accepted.status_code == 200
    assert accepted.json()["link_verification_state"] == "LINK_SUBMITTED_UNVERIFIED"
    assert accepted.json()["answer"] is None
    assert accepted.json()["model"] is None


def test_missing_signing_key_fails_closed(monkeypatch):
    monkeypatch.setenv("LIGHTSPEED_VISITOR_REVIEW_ENABLED", "1")
    monkeypatch.delenv("LIGHTSPEED_VISITOR_RECEIPT_KEY", raising=False)
    app = FastAPI()
    register_visitor_routes(app, LocalDatabase(), lambda _: "owner")
    response = TestClient(app).post("/api/v1/visitor/enroll", json={})
    assert response.status_code == 503


def test_public_projection_requires_exact_public_release_and_hash(monkeypatch, tmp_path):
    payload = {
        "title": "Public CGX object",
        "summary": "Owner-approved source-backed public projection.",
        "evidence_stage": "SOURCE_BACKED",
        "limitations": ["Derived public lens; not canonical authority or physical qualification."],
        "citations": [{
            "label": "Public evidence",
            "url": "https://example.org/evidence",
            "source_sha256": "a" * 64,
            "revision": "public-rev-1",
        }],
        "model": {
            "kind": "mesh",
            "url": "https://example.org/public/model.glb",
            "sha256": "b" * 64,
            "media_type": "model/gltf-binary",
            "representation_class": "PUBLIC_REVIEW_PROXY",
        },
    }
    payload_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    projection = {
        "projection_id": "PUB-OBJ-001",
        "object_id": "cgx:test:public-object",
        "lens": "achilles",
        "source_sha256": "c" * 64,
        "source_revision": "public-source-rev-1",
        "projection_sha256": payload_hash,
        "release": {
            "release_class": "Public",
            "target_visibility": "public",
            "release_approval_state": "APPROVED",
            "source_release_classes": ["Public"],
            "contains_restricted_material": False,
            "release_receipt_ref": "public-receipt:fixture-001",
        },
        "payload": payload,
    }
    manifest = tmp_path / "public-projections.json"

    def write_manifest(items):
        manifest.write_text(json.dumps({
            "schema": "CGX-LS-GO-PUBLIC-PROJECTION-SET/0.1",
            "state": "OWNER_SUPPLIED_PUBLIC_SAFE_PROJECTION_SET",
            "projections": items,
        }), encoding="utf-8")

    write_manifest([projection])
    monkeypatch.setenv("LIGHTSPEED_VISITOR_REVIEW_ENABLED", "1")
    monkeypatch.setenv("LIGHTSPEED_VISITOR_RECEIPT_KEY", "A" * 48)
    monkeypatch.setenv("LIGHTSPEED_VISITOR_PUBLIC_PROJECTION_MANIFEST", str(manifest))
    app = FastAPI()
    register_visitor_routes(
        app, LocalDatabase(),
        lambda token: "NCNB" if token == "OWNER" else (_ for _ in ()).throw(HTTPException(403, "owner session missing")),
    )
    local = TestClient(app)
    capabilities = local.get("/api/v1/visitor/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.json()["projection_manifest_configured"] is True
    assert str(manifest) not in capabilities.text

    invitation = local.post(
        "/api/v1/visitor/invites", json={}, headers={"X-LightSpeed-Session": "OWNER"}
    ).json()
    enrollment = local.post("/api/v1/visitor/enroll", json={
        "invite_token": invitation["invite_token"], "name": "Public reviewer",
        "theme": "blueprint", "lens": "achilles", "consent": True,
    }).json()
    head = {"X-LightSpeed-Visitor-Session": enrollment["visitor_session"]}

    model = local.post("/api/v1/visitor/interaction", json={
        "kind": "model_request", "lens": "achilles", "text": "Show the released model",
        "object_id": "cgx:test:public-object",
    }, headers=head)
    assert model.status_code == 200
    assert model.json()["status"] == "PUBLIC_SAFE_PROJECTION"
    assert model.json()["public_safe"] is True
    assert model.json()["model"]["sha256"] == "b" * 64
    assert model.json()["projection_sha256"] == payload_hash
    assert model.json()["release_receipt_ref"] == "public-receipt:fixture-001"

    answer = local.post("/api/v1/visitor/interaction", json={
        "kind": "question", "lens": "achilles", "text": "What is this?",
        "object_id": "cgx:test:public-object",
    }, headers=head)
    assert answer.status_code == 200
    assert answer.json()["status"] == "PUBLIC_SAFE_PROJECTION"
    assert answer.json()["answer"] == payload["summary"]
    assert answer.json()["model"] is None

    internal = json.loads(json.dumps(projection))
    internal["release"]["release_class"] = "Internal"
    internal["release"]["source_release_classes"] = ["Internal"]
    write_manifest([internal])
    held = local.post("/api/v1/visitor/interaction", json={
        "kind": "question", "lens": "achilles", "text": "Try internal projection",
        "object_id": "cgx:test:public-object",
    }, headers=head)
    assert held.status_code == 200
    assert held.json()["status"] == "PENDING_PUBLIC_SAFE_RESOLVER"
    assert held.json()["answer"] is None
    assert held.json()["public_safe"] is False

    bad_hash = json.loads(json.dumps(projection))
    bad_hash["projection_sha256"] = "0" * 64
    write_manifest([bad_hash])
    held_hash = local.post("/api/v1/visitor/interaction", json={
        "kind": "model_request", "lens": "achilles", "text": "Try mismatched bytes",
        "object_id": "cgx:test:public-object",
    }, headers=head)
    assert held_hash.json()["status"] == "PENDING_PUBLIC_SAFE_RESOLVER"
    assert held_hash.json()["model"] is None

    private_path = json.loads(json.dumps(projection))
    private_path["payload"]["summary"] = r"Private path C:\\Cognigrex\\internal must never project."
    private_path["projection_sha256"] = hashlib.sha256(
        json.dumps(private_path["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    write_manifest([private_path])
    held_private = local.post("/api/v1/visitor/interaction", json={
        "kind": "question", "lens": "achilles", "text": "Try private path",
        "object_id": "cgx:test:public-object",
    }, headers=head)
    assert held_private.json()["status"] == "PENDING_PUBLIC_SAFE_RESOLVER"
    assert held_private.json()["answer"] is None

    write_manifest([projection, projection])
    ambiguous = local.post("/api/v1/visitor/interaction", json={
        "kind": "question", "lens": "achilles", "text": "Try ambiguous duplicate",
        "object_id": "cgx:test:public-object",
    }, headers=head)
    assert ambiguous.json()["status"] == "PENDING_PUBLIC_SAFE_RESOLVER"
    assert ambiguous.json()["answer"] is None
