"""Fail-closed preflight/apply helper for the additive LS GO visitor schema.

This module never runs from a web request or bridge startup. Dry-run is the default.
Live apply requires an explicit owner decision reference, expected database SHA-256,
a verified SQLite backup, and a receipt path.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_TABLE_COLUMNS = {
    "ls_go_visitor_invites": {
        "invite_id", "reviewer_id", "token_sha256", "expiry_utc", "redeemed_utc", "revoked_utc",
    },
    "ls_go_visitor_profiles": {
        "reviewer_id", "name", "theme", "lens", "handshake_json", "consent_utc",
    },
    "ls_go_visitor_sessions": {
        "session_sha256", "reviewer_id", "expires_utc", "revoked_utc",
    },
    "ls_go_visitor_events": {
        "sequence", "event_id", "reviewer_id", "event_type", "recorded_utc",
        "payload_json", "previous_hash", "event_hash", "event_hmac",
    },
}
EXPECTED_INDEXES = {"idx_ls_go_visitor_events_reviewer"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
OWNER_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/#-]{2,239}$")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _schema_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _statements(schema_text: str) -> list[str]:
    without_comments = "\n".join(
        line for line in schema_text.splitlines() if not line.lstrip().startswith("--")
    )
    return [statement.strip() for statement in without_comments.split(";") if statement.strip()]


def _validate_additive_schema(schema_text: str) -> dict[str, Any]:
    statements = _statements(schema_text)
    if not statements:
        raise ValueError("visitor schema is empty")

    table_names: set[str] = set()
    index_names: set[str] = set()
    table_re = re.compile(
        r"^CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(ls_go_visitor_[A-Za-z0-9_]+)\s*\(",
        re.IGNORECASE | re.DOTALL,
    )
    index_re = re.compile(
        r"^CREATE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+(idx_ls_go_visitor_[A-Za-z0-9_]+)\s+ON\s+"
        r"(ls_go_visitor_[A-Za-z0-9_]+)\s*\(",
        re.IGNORECASE | re.DOTALL,
    )

    for statement in statements:
        forbidden = re.search(
            r"\b(DROP|ALTER|DELETE|UPDATE|INSERT|REPLACE|ATTACH|DETACH|VACUUM|PRAGMA|TRIGGER)\b",
            statement,
            re.IGNORECASE,
        )
        if forbidden:
            raise ValueError(f"non-additive visitor schema statement: {forbidden.group(1).upper()}")
        table_match = table_re.match(statement)
        if table_match:
            table_names.add(table_match.group(1))
            continue
        index_match = index_re.match(statement)
        if index_match:
            index_names.add(index_match.group(1))
            if index_match.group(2) not in EXPECTED_TABLE_COLUMNS:
                raise ValueError("visitor index targets an unexpected table")
            continue
        raise ValueError("visitor schema contains an unapproved statement family")

    if table_names != set(EXPECTED_TABLE_COLUMNS):
        raise ValueError(
            f"visitor schema tables mismatch: expected {sorted(EXPECTED_TABLE_COLUMNS)}, got {sorted(table_names)}"
        )
    if index_names != EXPECTED_INDEXES:
        raise ValueError(
            f"visitor schema indexes mismatch: expected {sorted(EXPECTED_INDEXES)}, got {sorted(index_names)}"
        )
    return {
        "statement_count": len(statements),
        "tables": sorted(table_names),
        "indexes": sorted(index_names),
    }


def _quick_check(connection: sqlite3.Connection) -> str:
    row = connection.execute("PRAGMA quick_check").fetchone()
    return str(row[0]) if row else "missing"


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f'PRAGMA table_info("{table}")').fetchall()}


def _verify_expected_schema(connection: sqlite3.Connection) -> dict[str, Any]:
    mismatches: dict[str, Any] = {}
    for table, expected in EXPECTED_TABLE_COLUMNS.items():
        columns = _table_columns(connection, table)
        if not expected <= columns:
            mismatches[table] = {
                "missing": sorted(expected - columns),
                "observed": sorted(columns),
            }
    indexes = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_ls_go_visitor_%'"
        ).fetchall()
    }
    missing_indexes = sorted(EXPECTED_INDEXES - indexes)
    if mismatches or missing_indexes:
        raise ValueError(
            json.dumps({"table_mismatches": mismatches, "missing_indexes": missing_indexes}, sort_keys=True)
        )
    return {
        "tables": sorted(EXPECTED_TABLE_COLUMNS),
        "indexes": sorted(EXPECTED_INDEXES),
    }


def _clone_preflight(database_path: Path, schema_text: str) -> dict[str, Any]:
    source = sqlite3.connect(str(database_path))
    clone = sqlite3.connect(":memory:")
    try:
        source.backup(clone)
        before_quick = _quick_check(clone)
        if before_quick != "ok":
            raise ValueError(f"database clone quick_check failed before schema: {before_quick}")
        clone.executescript(schema_text)
        after_quick = _quick_check(clone)
        if after_quick != "ok":
            raise ValueError(f"database clone quick_check failed after schema: {after_quick}")
        verified = _verify_expected_schema(clone)
        return {
            "before_quick_check": before_quick,
            "after_quick_check": after_quick,
            "post_schema": verified,
        }
    finally:
        clone.close()
        source.close()


def assess_visitor_schema(database_path: Path, schema_path: Path) -> dict[str, Any]:
    database_path = Path(database_path).resolve()
    schema_path = Path(schema_path).resolve()
    if not database_path.is_file():
        raise FileNotFoundError(f"database not found: {database_path}")
    if database_path.suffix.lower() not in {".db", ".sqlite", ".sqlite3"}:
        raise ValueError("visitor migration target must be a SQLite database file")
    if not schema_path.is_file() or schema_path.suffix.lower() != ".sql":
        raise FileNotFoundError(f"visitor schema not found: {schema_path}")

    schema_text = schema_path.read_text(encoding="utf-8")
    additive = _validate_additive_schema(schema_text)
    clone = _clone_preflight(database_path, schema_text)
    return {
        "schema": "LS-GO-VISITOR-MIGRATION-PREFLIGHT/0.1",
        "state": "DRY_RUN_COMPATIBLE",
        "checked_utc": _utc(),
        "database_path": str(database_path),
        "database_sha256": _sha256(database_path),
        "database_bytes": database_path.stat().st_size,
        "schema_path": str(schema_path),
        "schema_sha256": _schema_sha256(schema_text),
        "additive_contract": additive,
        "clone_preflight": clone,
        "mutation_performed": False,
    }


def _backup_sqlite(database_path: Path, backup_path: Path) -> dict[str, Any]:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix="ls-go-visitor-backup-", suffix=".db", dir=backup_path.parent, delete=False
    ) as handle:
        raw_backup = Path(handle.name)
    try:
        source = sqlite3.connect(str(database_path))
        destination = sqlite3.connect(str(raw_backup))
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()

        with sqlite3.connect(str(raw_backup)) as verification:
            quick = _quick_check(verification)
            if quick != "ok":
                raise ValueError(f"backup quick_check failed: {quick}")
        content_sha = _sha256(raw_backup)
        with raw_backup.open("rb") as source, gzip.open(backup_path, "wb", compresslevel=6) as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
        return {
            "path": str(backup_path),
            "archive_sha256": _sha256(backup_path),
            "content_sha256": content_sha,
            "archive_bytes": backup_path.stat().st_size,
            "quick_check": quick,
        }
    finally:
        raw_backup.unlink(missing_ok=True)


def apply_visitor_schema_migration(
    database_path: Path,
    schema_path: Path,
    backup_path: Path,
    receipt_path: Path,
    *,
    owner_decision_ref: str,
    expected_database_sha256: str,
) -> dict[str, Any]:
    if not OWNER_REF_RE.fullmatch(owner_decision_ref or ""):
        raise ValueError("explicit bounded owner decision reference is required")
    expected = (expected_database_sha256 or "").lower()
    if not SHA256_RE.fullmatch(expected):
        raise ValueError("expected database SHA-256 is required")

    preflight = assess_visitor_schema(database_path, schema_path)
    if preflight["database_sha256"] != expected:
        raise ValueError("database changed since the accepted preflight")

    database_path = Path(database_path).resolve()
    schema_path = Path(schema_path).resolve()
    backup_path = Path(backup_path).resolve()
    receipt_path = Path(receipt_path).resolve()
    if backup_path == database_path or receipt_path == database_path:
        raise ValueError("backup/receipt must not overwrite the database")
    if backup_path.exists() or receipt_path.exists():
        raise FileExistsError("backup or receipt path already exists")

    schema_text = schema_path.read_text(encoding="utf-8")
    backup = _backup_sqlite(database_path, backup_path)

    connection = sqlite3.connect(str(database_path), timeout=30)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("BEGIN IMMEDIATE")
        try:
            for statement in _statements(schema_text):
                connection.execute(statement)
            post_schema = _verify_expected_schema(connection)
            quick = _quick_check(connection)
            if quick != "ok":
                raise ValueError(f"post-migration quick_check failed: {quick}")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    finally:
        connection.close()

    receipt = {
        "schema": "LS-GO-VISITOR-MIGRATION-RECEIPT/0.1",
        "state": "APPLIED_ADDATIVE_SCHEMA_WITH_BACKUP",
        "applied_utc": _utc(),
        "owner_decision_ref": owner_decision_ref,
        "database_path": str(database_path),
        "database_sha256_before": preflight["database_sha256"],
        "database_sha256_after": _sha256(database_path),
        "schema_path": str(schema_path),
        "schema_sha256": preflight["schema_sha256"],
        "backup": backup,
        "post_schema": post_schema,
        "post_quick_check": quick,
        "rollback_instruction": "Restore the verified backup snapshot only under an explicit owner rollback decision.",
        "canonical_cgx_mutation": False,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    receipt["receipt_sha256"] = _sha256(receipt_path)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preflight the additive LS GO visitor schema.")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--owner-decision-ref", default="")
    parser.add_argument("--expected-database-sha256", default="")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--receipt", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if not args.apply:
        print(json.dumps(assess_visitor_schema(args.database, args.schema), indent=2, ensure_ascii=False))
        return 0
    if args.backup is None or args.receipt is None:
        raise SystemExit("--apply requires --backup and --receipt")
    result = apply_visitor_schema_migration(
        args.database,
        args.schema,
        args.backup,
        args.receipt,
        owner_decision_ref=args.owner_decision_ref,
        expected_database_sha256=args.expected_database_sha256,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
