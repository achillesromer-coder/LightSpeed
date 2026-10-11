from __future__ import annotations

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


def test_missing_signing_key_fails_closed(monkeypatch):
    monkeypatch.setenv("LIGHTSPEED_VISITOR_REVIEW_ENABLED", "1")
    monkeypatch.delenv("LIGHTSPEED_VISITOR_RECEIPT_KEY", raising=False)
    app = FastAPI()
    register_visitor_routes(app, LocalDatabase(), lambda _: "owner")
    response = TestClient(app).post("/api/v1/visitor/enroll", json={})
    assert response.status_code == 503
