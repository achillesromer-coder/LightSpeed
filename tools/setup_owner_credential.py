#!/usr/bin/env python
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import getpass
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parent
RUNTIME_CANDIDATES = (
    SCRIPT_ROOT.parent / "Core",
    SCRIPT_ROOT.parent / "desktop" / "LightSpeed_Runtime",
    SCRIPT_ROOT.parents[1] / "desktop" / "LightSpeed_Runtime",
)
for runtime_root in RUNTIME_CANDIDATES:
    if (runtime_root / "lightspeed_runtime" / "owner_credentials.py").is_file():
        if str(runtime_root) not in sys.path:
            sys.path.insert(0, str(runtime_root))
        break

from lightspeed_runtime.owner_credentials import (  # noqa: E402
    CredentialStore,
    write_achilles_credential_reference,
)


class SQLiteCredentialDatabase:
    def __init__(self, path: Path):
        self.path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def execute_query(self, query: str, params: tuple = ()) -> list[dict[str, Any]]:
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(query, params).fetchall()]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        with self._connect() as connection:
            cursor = connection.execute(query, params)
            return int(cursor.rowcount)


def utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a first-login owner credential without embedding plaintext in source."
    )
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--username", default="NCNB")
    parser.add_argument("--achilles-reference", type=Path, required=True)
    parser.add_argument("--receipt-dir", type=Path, required=True)
    parser.add_argument("--replace-existing", action="store_true")
    args = parser.parse_args()

    database_path = args.database.resolve()
    if not database_path.is_file():
        raise SystemExit(f"Database not found: {database_path}")
    database = SQLiteCredentialDatabase(database_path)
    table = database.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='auth_credentials'"
    )
    if not table:
        raise SystemExit("Dedicated auth_credentials migration is not applied")

    password = getpass.getpass("Bootstrap password: ")
    confirmation = getpass.getpass("Confirm bootstrap password: ")
    if password != confirmation:
        raise SystemExit("Bootstrap passwords did not match")

    store = CredentialStore(database)
    status = store.bootstrap(
        args.username,
        password,
        replace_existing=args.replace_existing,
    )
    verified = store.authenticate(args.username, password)
    if not verified.get("must_change"):
        raise SystemExit("Bootstrap verification failed: first-login change is not enforced")

    reference = write_achilles_credential_reference(
        args.achilles_reference,
        status=status,
        event="bootstrap",
    )
    args.receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = args.receipt_dir / f"owner_credential_bootstrap_{utc_stamp()}.json"
    receipt = {
        "schema_version": "lightspeed-owner-credential-bootstrap-receipt-v1",
        "recorded_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "username": status.get("username"),
        "credential_key_id": status.get("credential_key_id"),
        "rotation_sequence": status.get("rotation_sequence"),
        "must_change": status.get("must_change"),
        "reminder_due_utc": status.get("reminder_due_utc"),
        "mandatory_due_utc": status.get("mandatory_due_utc"),
        "password_persisted_as_hash_only": True,
        "plaintext_password_stored": False,
        "bootstrap_authentication_verified": True,
        "achilles_reference": str(reference),
        "database": str(database_path),
        "canonical_write": "local_operational_database_only",
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "receipt": str(receipt_path), "credential": status}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
