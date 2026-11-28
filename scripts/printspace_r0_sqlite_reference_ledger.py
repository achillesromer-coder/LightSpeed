#!/usr/bin/env python3
"""Test-only reference for atomic, durable R0 nonce conflict detection.

NOT a production owner DBR, authenticator, key store, native FileSpace, or
an authorised persistent service. All inputs are already SHA-256 digests.
Atomic INSERT OR IGNORE in SQLite is used to demonstrate concurrent workers
and process restart. There is deliberately no TTL-based deletion: challenge
age must be verified by the three-role upstream verifier first.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

REQUEST_SCHEMA = "CGX-PRINTSPACE-R0-NONCE-INSERT-REQUEST/0.1"
ACK_SCHEMA = "CGX-PRINTSPACE-R0-NONCE-INSERT-ACK/0.1"
HEX = re.compile(r"[0-9a-f]{64}\Z")
COLS = {"schema", "nonce_digest_sha256", "review_receipt_sha256", "product_facet_sha256", "plan_sha256", "expires_at_seconds"}


def validate(payload: object) -> dict:
    if not isinstance(payload, dict) or set(payload) != COLS or payload.get("schema") != REQUEST_SCHEMA:
        raise ValueError("LEDGER_REQUEST_SCHEMA")
    if any(not isinstance(payload.get(key), str) or HEX.fullmatch(payload[key]) is None
           for key in ("nonce_digest_sha256", "review_receipt_sha256", "plan_sha256")):
        raise ValueError("LEDGER_SHA256_DIGEST_REQUIRED")
    facet = payload.get("product_facet_sha256")
    if not isinstance(facet, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", facet):
        raise ValueError("LEDGER_CONTENT_ADDRESS_REQUIRED")
    expiry = payload["expires_at_seconds"]
    if type(expiry) is not int or expiry < 1 or expiry > 2**53 - 1:
        raise ValueError("LEDGER_EXPIRY_SCHEMA")
    return payload


def connect(db: Path) -> sqlite3.Connection:
    if not db.is_absolute() or not db.parent.is_dir():
        raise ValueError("ABSOLUTE_EXISTING_TEST_DIRECTORY_REQUIRED")
    conn = sqlite3.connect(db, timeout=15, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=15000")
    conn.execute("PRAGMA synchronous=FULL")
    return conn


def create(db: Path) -> dict:
    with connect(db) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""CREATE TABLE IF NOT EXISTS cgx_r0_nonce_reference (
            nonce_sha256 TEXT PRIMARY KEY NOT NULL,
            review_sha256 TEXT NOT NULL,
            product_sha256 TEXT NOT NULL,
            plan_sha256 TEXT NOT NULL,
            expires_at_seconds INTEGER NOT NULL
        ) WITHOUT ROWID""")
    return {"state": "INITIALISED_REFERENCE_ONLY"}


def consume(db: Path, raw: object) -> dict:
    p = validate(raw)
    with connect(db) as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute("""INSERT OR IGNORE INTO cgx_r0_nonce_reference
                (nonce_sha256,review_sha256,product_sha256,plan_sha256,expires_at_seconds)
                VALUES (?,?,?,?,?)""", (p["nonce_digest_sha256"], p["review_receipt_sha256"],
                p["product_facet_sha256"],p["plan_sha256"],p["expires_at_seconds"]))
            inserted = cursor.rowcount == 1
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {"schema": ACK_SCHEMA, "state": "INSERTED" if inserted else "ALREADY_PRESENT",
            "nonce_digest_sha256": p["nonce_digest_sha256"],
            "review_receipt_sha256": p["review_receipt_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("init", "consume"))
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    try:
        db = Path(args.db)
        if args.action == "init":
            response = create(db)
        else:
            raw = sys.stdin.buffer.read(4097)
            if len(raw) > 4096:
                raise ValueError("LEDGER_INPUT_SIZE_BUDGET")
            response = consume(db, json.loads(raw))
    except (OSError, ValueError, sqlite3.Error, json.JSONDecodeError) as error:
        print(json.dumps({"state": "HOLD", "error_class": type(error).__name__}), file=sys.stderr)
        return 2
    print(json.dumps(response, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
