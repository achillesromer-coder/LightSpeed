#!/usr/bin/env python
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS auth_credentials (
    username TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    alg TEXT NOT NULL,
    iterations INTEGER NOT NULL CHECK (iterations >= 200000),
    salt_b64 TEXT NOT NULL,
    hash_b64 TEXT NOT NULL,
    credential_key_id TEXT NOT NULL UNIQUE,
    rotation_sequence INTEGER NOT NULL DEFAULT 1,
    changed_utc TEXT NOT NULL,
    reminder_due_utc TEXT NOT NULL,
    mandatory_due_utc TEXT NOT NULL,
    must_change INTEGER NOT NULL DEFAULT 1 CHECK (must_change IN (0, 1)),
    bootstrap_credential INTEGER NOT NULL DEFAULT 0 CHECK (bootstrap_credential IN (0, 1)),
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username) ON DELETE RESTRICT
)
"""

REQUIRED_COLUMNS = {
    "username",
    "schema_version",
    "alg",
    "iterations",
    "salt_b64",
    "hash_b64",
    "credential_key_id",
    "rotation_sequence",
    "changed_utc",
    "reminder_due_utc",
    "mandatory_due_utc",
    "must_change",
    "bootstrap_credential",
    "updated_at",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the additive owner credential migration.")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--receipt-dir", type=Path, required=True)
    args = parser.parse_args()

    database = args.database.resolve()
    if not database.is_file():
        raise SystemExit(f"Database not found: {database}")
    with sqlite3.connect(str(database), timeout=30.0) as connection:
        connection.execute("PRAGMA busy_timeout=30000")
        before = {
            row[1]
            for row in connection.execute("PRAGMA table_info(auth_credentials)").fetchall()
        }
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(SCHEMA_SQL)
        after = {
            row[1]
            for row in connection.execute("PRAGMA table_info(auth_credentials)").fetchall()
        }
        missing = sorted(REQUIRED_COLUMNS - after)
        if missing:
            connection.rollback()
            raise SystemExit(f"Credential migration validation failed; missing columns: {missing}")
        connection.commit()
        row_count = int(
            connection.execute("SELECT COUNT(*) FROM auth_credentials").fetchone()[0]
        )

    args.receipt_dir.mkdir(parents=True, exist_ok=True)
    recorded = datetime.now(UTC)
    receipt_path = args.receipt_dir / (
        f"owner_credentials_migration_{recorded.strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    receipt = {
        "schema_version": "lightspeed-owner-credentials-migration-receipt-v1",
        "recorded_utc": recorded.isoformat(timespec="seconds"),
        "database": str(database),
        "table": "auth_credentials",
        "state": "already_present" if before else "created",
        "columns_verified": sorted(after),
        "credential_row_count": row_count,
        "destructive_change": False,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "receipt": str(receipt_path), "state": receipt["state"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
