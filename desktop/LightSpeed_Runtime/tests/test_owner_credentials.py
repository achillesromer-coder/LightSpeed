from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import sqlite3
from pathlib import Path
import sys

import pytest


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.owner_credentials import (
    ACHILLES_REFERENCE_SCHEMA,
    CredentialAuthenticationFailed,
    CredentialError,
    CredentialStore,
    OwnerSessionStore,
    create_password_record,
    credential_status,
    verify_password_record,
    write_achilles_credential_reference,
)
from lightspeed_runtime import ls_go_bridge
from fastapi.testclient import TestClient


class StubDatabase:
    def __init__(self, path: Path):
        self.path = path
        with sqlite3.connect(path) as connection:
            connection.executescript(
                """
                CREATE TABLE users (
                  id INTEGER PRIMARY KEY,
                  username TEXT NOT NULL UNIQUE,
                  role TEXT,
                  clearance INTEGER
                );
                CREATE TABLE user_preferences (
                  user_id TEXT PRIMARY KEY,
                  preferences_json TEXT,
                  updated_at TEXT
                );
                CREATE TABLE auth_credentials (
                  username TEXT PRIMARY KEY,
                  schema_version TEXT NOT NULL,
                  alg TEXT NOT NULL,
                  iterations INTEGER NOT NULL,
                  salt_b64 TEXT NOT NULL,
                  hash_b64 TEXT NOT NULL,
                  credential_key_id TEXT NOT NULL UNIQUE,
                  rotation_sequence INTEGER NOT NULL,
                  changed_utc TEXT NOT NULL,
                  reminder_due_utc TEXT NOT NULL,
                  mandatory_due_utc TEXT NOT NULL,
                  must_change INTEGER NOT NULL,
                  bootstrap_credential INTEGER NOT NULL,
                  updated_at TEXT
                );
                INSERT INTO users (username, role, clearance) VALUES ('NCNB', 'main', 3);
                INSERT INTO user_preferences (user_id, preferences_json, updated_at)
                VALUES ('NCNB', '{"okr.okrs":[]}', CURRENT_TIMESTAMP);
                """
            )

    def execute_query(self, query, params=()):
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query, params).fetchall()]

    def execute_update(self, query, params=()):
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(query, params)
            return cursor.rowcount


def test_bootstrap_record_is_hashed_and_requires_change():
    now = datetime(2026, 8, 27, tzinfo=UTC)
    record = create_password_record(
        "temporary-fixture",
        username="NCNB",
        must_change=True,
        bootstrap=True,
        now=now,
    )

    assert "temporary-fixture" not in json.dumps(record)
    assert verify_password_record(record, "temporary-fixture") is True
    assert verify_password_record(record, "wrong") is False
    status = credential_status(record, now=now)
    assert status["must_change"] is True
    assert status["reminder_due_utc"] == "2026-11-25T00:00:00+00:00"
    assert status["mandatory_due_utc"] == "2027-08-27T00:00:00+00:00"


def test_store_preserves_preferences_and_rotates_key(tmp_path):
    now = datetime(2026, 8, 27, tzinfo=UTC)
    database = StubDatabase(tmp_path / "auth.db")
    store = CredentialStore(database)

    bootstrap = store.bootstrap("NCNB", "temporary-fixture", now=now)
    assert bootstrap["must_change"] is True
    first_key = bootstrap["credential_key_id"]
    assert store.authenticate("NCNB", "temporary-fixture", now=now)["must_change"] is True

    changed = store.change_password(
        "NCNB",
        "temporary-fixture",
        "Stronger-Rotation-2026!",
        now=now + timedelta(minutes=1),
    )
    assert changed["must_change"] is False
    assert changed["rotation_sequence"] == 2
    assert changed["credential_key_id"] != first_key
    with pytest.raises(CredentialAuthenticationFailed):
        store.authenticate("NCNB", "temporary-fixture", now=now)
    assert store.authenticate("NCNB", "Stronger-Rotation-2026!", now=now)["configured"] is True

    rows = database.execute_query("SELECT preferences_json FROM user_preferences WHERE user_id = ?", ("NCNB",))
    preferences = json.loads(rows[0]["preferences_json"])
    assert preferences["okr.okrs"] == []
    credential_rows = database.execute_query("SELECT * FROM auth_credentials WHERE username = ?", ("NCNB",))
    assert "Stronger-Rotation-2026!" not in json.dumps(credential_rows)


def test_pin_policy_four_minimum_six_recommended_without_character_rules(tmp_path):
    database = StubDatabase(tmp_path / "auth.db")
    store = CredentialStore(database)

    with pytest.raises(CredentialError, match="at least 4"):
        store.bootstrap("NCNB", "123")

    store.bootstrap("NCNB", "temporary-fixture")
    with pytest.raises(CredentialError, match="at least 4"):
        store.change_password("NCNB", "temporary-fixture", "123")

    # A numeric PIN is sufficient; no letter, symbol or character-class rule.
    result = store.change_password("NCNB", "temporary-fixture", "8642")
    assert result["must_change"] is False
    assert result["policy"]["minimum_password_length"] == 4
    assert result["policy"]["recommended_password_length"] == 6
    assert result["policy"]["numeric_pin_allowed"] is True
    assert result["policy"]["character_classes_required"] is False
    assert store.authenticate("NCNB", "8642")["configured"] is True
    assert "8642" not in json.dumps(database.execute_query("SELECT * FROM auth_credentials"))


def test_owner_login_attempts_limited_then_expire():
    current = [100.0]
    gate = ls_go_bridge.OwnerLoginAttemptLimiter(clock=lambda: current[0])
    for i in range(5):
        assert gate.retry_after_seconds() == 0
        gate.note_failure()
    assert gate.retry_after_seconds() == 900
    current[0] += 899
    assert gate.retry_after_seconds() == 1
    current[0] += 1
    assert gate.retry_after_seconds() == 0
    gate.note_failure()
    gate.note_success()
    assert gate.retry_after_seconds() == 0


def test_bridge_login_blocks_repeated_failures_before_correct_pin(tmp_path, monkeypatch):
    database = StubDatabase(tmp_path / "auth.db")
    CredentialStore(database).bootstrap("NCNB", "8642")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (database, object()))
    client = TestClient(ls_go_bridge.create_app(tmp_path / "App"))
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json={"username": "NCNB", "password": "wrong"}).status_code == 401
    blocked = client.post("/api/v1/auth/login", json={"username": "NCNB", "password": "8642"})
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_sessions_are_memory_only_and_expire():
    now = datetime(2026, 8, 27, tzinfo=UTC)
    sessions = OwnerSessionStore(lifetime=timedelta(minutes=5))
    token, _ = sessions.issue(username="NCNB", credential_key_id="LSCRED-1", now=now)

    assert sessions.verify(token, now=now).username == "NCNB"
    with pytest.raises(CredentialAuthenticationFailed):
        sessions.verify(token, now=now + timedelta(minutes=6))


def test_password_change_session_cannot_authorize_owner_action():
    sessions = OwnerSessionStore()
    token, _ = sessions.issue(
        username="NCNB",
        credential_key_id="LSCRED-1",
        scope="password_change",
    )

    with pytest.raises(CredentialAuthenticationFailed, match="scope"):
        sessions.verify(token, required_scope="owner")


def test_achilles_reference_is_non_secret_and_append_only(tmp_path):
    destination = tmp_path / "credential_NCNB.json"
    first = {
        "username": "NCNB",
        "credential_key_id": "LSCRED-FIRST",
        "rotation_sequence": 1,
        "changed_utc": "2026-08-27T00:00:00+00:00",
        "reminder_due_utc": "2026-11-25T00:00:00+00:00",
        "mandatory_due_utc": "2027-08-27T00:00:00+00:00",
        "must_change": True,
    }
    second = {**first, "credential_key_id": "LSCRED-SECOND", "rotation_sequence": 2}
    write_achilles_credential_reference(destination, status=first, event="bootstrap")
    write_achilles_credential_reference(destination, status=second, event="rotation")

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["schema_version"] == ACHILLES_REFERENCE_SCHEMA
    assert payload["grants_authentication"] is False
    assert [item["credential_key_id"] for item in payload["history"]] == [
        "LSCRED-FIRST",
        "LSCRED-SECOND",
    ]
    assert "hash" not in json.dumps(payload).lower()
    assert "salt" not in json.dumps(payload).lower()


def test_bridge_first_login_is_change_only_then_issues_owner_session(tmp_path, monkeypatch):
    database = StubDatabase(tmp_path / "auth.db")
    CredentialStore(database).bootstrap("NCNB", "temporary-fixture")
    monkeypatch.setattr(ls_go_bridge, "_try_get_services", lambda _root: (database, object()))
    monkeypatch.delenv(ls_go_bridge.OWNER_CONFIRMATION_ENV, raising=False)
    client = TestClient(ls_go_bridge.create_app(tmp_path / "App"))

    first_login = client.post(
        "/api/v1/auth/login",
        json={"username": "NCNB", "password": "temporary-fixture"},
    )
    assert first_login.status_code == 200
    assert first_login.json()["authenticated"] is False
    assert first_login.json()["change_required"] is True
    assert "session_token" not in first_login.json()
    change_token = first_login.json()["password_change_token"]

    held = client.get(
        "/api/v1/results/LSGO-RESULT-MISSING",
        headers={"X-LightSpeed-Session": change_token},
    )
    assert held.status_code == 403

    changed = client.post(
        "/api/v1/auth/change-password",
        headers={"X-LightSpeed-Password-Change": change_token},
        json={
            "username": "NCNB",
            "current_password": "temporary-fixture",
            "new_password": "Stronger-Rotation-2026!",
        },
    )
    assert changed.status_code == 200
    assert changed.json()["authenticated"] is True
    owner_token = changed.json()["session_token"]

    authenticated_missing = client.get(
        "/api/v1/results/LSGO-RESULT-MISSING",
        headers={"X-LightSpeed-Session": owner_token},
    )
    assert authenticated_missing.status_code == 404
    assert client.get("/api/v1/status").json()["auth"]["mode"] == "username_password_session"


def test_desktop_and_migration_keep_auth_fail_closed_and_separate_from_tailoring():
    repository = RUNTIME_ROOT.parents[1]
    desktop_source = (repository / "desktop" / "Desktop_Hooks" / "LightSpeed" / "N.py").read_text(
        encoding="utf-8"
    )
    migration_source = (
        repository
        / "desktop"
        / "Desktop_Hooks"
        / "LightSpeed"
        / "Z Axis"
        / "Z+3_Trinity"
        / "tools"
        / "initialize_database.py"
    ).read_text(encoding="utf-8")
    credential_source = (
        RUNTIME_ROOT / "lightspeed_runtime" / "owner_credentials.py"
    ).read_text(encoding="utf-8")

    assert "CredentialStore(self.db).authenticate(username, password or \"\")" in desktop_source
    assert "Continuing without password persistence" not in desktop_source
    assert "CREATE TABLE IF NOT EXISTS auth_credentials" in migration_source
    assert "user_preferences" not in credential_source
