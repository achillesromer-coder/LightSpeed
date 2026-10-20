"""Offline-positive owner-authenticated Alexandria route check.

This fixture contains only the original CC0 source catalogue README and licence
at pinned upstream bobeff/open-source-engines commit, NOT the engines it lists.
No external network, local host, private Drive content, or production tokens.
"""
from __future__ import annotations
import base64
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"desktop"/"LightSpeed_Runtime"))
from lightspeed_runtime.owner_credentials import CredentialStore
from lightspeed_runtime import ls_go_bridge

FIXTURE=ROOT/"tests"/"fixtures"/"alexandria_engine_catalogue"
README=FIXTURE/"README.md"
LICENSE=FIXTURE/"LICENSE"
RECEIPT=ROOT/"cgx"/"review"/"alexandria_engine_catalogue_real_source_envelope_20261020.json"
REF="alexandria:external:index:4d54f3995140e64beebef6575760996bf14324ec:21"
EXPECTED_SOURCE_SHA="075c794da0482a7bff6f46d67956ef2e62486a1914fc78cda3d239bbf3a54a92"
EXPECTED_LICENSE_SHA="a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499"


class TestDB:
    __test__=False
    def __init__(self,path:Path):
        self.path=path
        with sqlite3.connect(path) as db:
            db.executescript("""
                CREATE TABLE users (
                  id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
                  role TEXT, clearance INTEGER
                );
                CREATE TABLE user_preferences (
                  user_id TEXT PRIMARY KEY, preferences_json TEXT, updated_at TEXT
                );
                CREATE TABLE auth_credentials (
                  username TEXT PRIMARY KEY, schema_version TEXT NOT NULL,
                  alg TEXT NOT NULL, iterations INTEGER NOT NULL,
                  salt_b64 TEXT NOT NULL, hash_b64 TEXT NOT NULL,
                  credential_key_id TEXT NOT NULL UNIQUE,
                  rotation_sequence INTEGER NOT NULL, changed_utc TEXT NOT NULL,
                  reminder_due_utc TEXT NOT NULL, mandatory_due_utc TEXT NOT NULL,
                  must_change INTEGER NOT NULL, bootstrap_credential INTEGER NOT NULL,
                  updated_at TEXT
                );
                INSERT INTO users (username,role,clearance) VALUES('test-owner','main',3);
                INSERT INTO user_preferences (user_id,preferences_json,updated_at)
                VALUES ('test-owner','{}',CURRENT_TIMESTAMP);
            """)

    def execute_query(self,query,params=()):
        with sqlite3.connect(self.path) as db:
            db.row_factory=sqlite3.Row
            return [dict(row) for row in db.execute(query,params).fetchall()]

    def execute_update(self,query,params=()):
        with sqlite3.connect(self.path) as db:
            return db.execute(query,params).rowcount


def test_offline_fixture_is_exact_pinned_cc0_catalogue_not_engine_source():
    readme=README.read_bytes()
    licence=LICENSE.read_bytes()
    assert len(readme)==7891
    assert len(licence)==7048
    assert hashlib.sha256(readme).hexdigest()==EXPECTED_SOURCE_SHA
    assert hashlib.sha256(licence).hexdigest()==EXPECTED_LICENSE_SHA
    def git_blob(data:bytes)->str:
        return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
    assert git_blob(readme)=="f315c4b33c4369db78cda7c6dbf8c407342f64f7"
    assert git_blob(licence)=="0e259d42c996742e9e3cba14c677129b2c1b6311"
    packet=json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert packet["source_envelope"]["sha256"]==EXPECTED_SOURCE_SHA
    assert packet["source_envelope"]["lineage"]["catalogue_license"]=="CC0-1.0"
    assert packet["source_envelope"]["lineage"]["upstream_project_license"]=="UNVERIFIED"
    assert packet["upstream_project_bytes_acquired"]==0


def test_actual_owner_session_hydrates_real_source_then_revocation_blocks(tmp_path,monkeypatch):
    db=TestDB(tmp_path/"credentials.db")
    credentials=CredentialStore(db)
    credentials.bootstrap("test-owner","temporary-test-secret")
    credentials.change_password("test-owner","temporary-test-secret","Rotated-Test-Password-2026!")
    monkeypatch.setattr(ls_go_bridge,"_try_get_services",lambda _: (db,object()))
    monkeypatch.setenv(ls_go_bridge.OWNER_CONFIRMATION_ENV,"untrusted-legacy")
    client=TestClient(ls_go_bridge.create_app(tmp_path/"unlinked-test-root"))
    endpoint="/api/v1/alexandria/catalogue/hydrate"
    readme=README.read_bytes()
    encoded=base64.b64encode(readme).decode("ascii")
    request={"candidate_ref":REF,"source_base64":encoded}

    # No source bytes or titles returned to an unauthenticated browser.
    denied=client.post(endpoint,json=request)
    assert denied.status_code==403
    assert "raylib" not in denied.text
    assert EXPECTED_SOURCE_SHA not in denied.text
    legacy=client.post(endpoint,json=request,
                       headers={"X-LightSpeed-Owner-Confirmation":"untrusted-legacy"})
    assert legacy.status_code==403

    login=client.post("/api/v1/auth/login",
                      json={"username":"test-owner","password":"Rotated-Test-Password-2026!"})
    assert login.status_code==200
    assert login.json()["authenticated"] is True
    session=login.json()["session_token"]
    headers={"X-LightSpeed-Session":session}

    proven=client.post(endpoint,json=request,headers=headers)
    assert proven.status_code==200,proven.text
    assert proven.headers["cache-control"]=="no-store"
    data=proven.json()
    assert data["schema"]=="CGX-ALEXANDRIA-SOURCE-LENS/0.1"
    assert data["status"]=="SOURCE_PROVEN_R1_VIEW_CANDIDATE"
    assert data["title"]=="raylib"
    assert data["candidate_ref"]==REF
    assert data["source_line"]==21
    assert data["source_byte_range"]==[293,447]
    assert data["source_sha256"]==EXPECTED_SOURCE_SHA
    assert data["upstream_reference_urls"]==["https://github.com/raysan5/raylib"]
    assert data["licence"]=="CC0-1.0"
    assert data["linked_project_licence"]=="UNVERIFIED"
    assert data["authenticated"] is False
    assert data["canonical_admission"] is False
    assert data["executable_capability"] is False
    assert data["published"] is False
    assert "source_base64" not in data
    assert "source_bytes" not in data
    assert data["source_bytes_embedded"] is False

    # Same authenticated user with no source cache or wrong source root.
    missing=client.post(endpoint,json={"candidate_ref":REF},headers=headers)
    assert missing.status_code==200
    assert missing.json()["status"]=="NOT_CACHED"
    malformed=client.post(endpoint,json={"candidate_ref":REF,"source_base64":"invalid%%%"},
                          headers=headers)
    assert malformed.status_code==400
    wrong=client.post(endpoint,json={"candidate_ref":REF,
                  "source_base64":base64.b64encode(readme+b"x").decode("ascii")},
                  headers=headers)
    assert wrong.status_code==200
    assert wrong.json()["status"]=="SOURCE_MISMATCH"
    assert "title" not in wrong.json()
    injection=client.post(endpoint,json={"candidate_ref":REF,"source_path":"C:/Documents"},
                          headers=headers)
    assert injection.status_code==400

    logout=client.post("/api/v1/auth/logout",headers=headers)
    assert logout.status_code==200
    revoked=client.post(endpoint,json=request,headers=headers)
    assert revoked.status_code==403
    assert "raylib" not in revoked.text
    assert EXPECTED_SOURCE_SHA not in revoked.text
