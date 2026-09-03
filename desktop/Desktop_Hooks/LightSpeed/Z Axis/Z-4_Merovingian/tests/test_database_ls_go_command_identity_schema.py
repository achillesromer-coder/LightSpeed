"""Focused tests for the explicitly gated LS GO identity migration."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


FLOOR_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[6]
RUNTIME_ROOT = REPO_ROOT / "desktop" / "LightSpeed_Runtime"
for import_root in (FLOOR_ROOT, RUNTIME_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from core.services.database import DatabaseService


IDENTITY_COLUMNS = [
    "command_id",
    "canonical_payload_sha256",
    "queue_state",
    "queue_occurrence_count",
    "first_queue_offset",
    "last_queue_offset",
    "task_id",
    "job_id",
    "created_at",
    "updated_at",
]

QUEUE_STATE_COLUMNS = [
    "queue_key",
    "queue_path",
    "device",
    "inode",
    "indexed_offset",
    "observed_size",
    "observed_mtime_ns",
    "complete",
    "updated_at",
]


def _objects(db_path: Path) -> list[tuple[str, str, str | None]]:
    with sqlite3.connect(db_path) as conn:
        return conn.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE name IN (
                'ls_go_command_identities',
                'ls_go_command_queue_state',
                'idx_ls_go_command_task',
                'idx_ls_go_command_job'
            )
            ORDER BY type, name
            """
        ).fetchall()


def _column_names(db_path: Path, table: str) -> list[str]:
    with sqlite3.connect(db_path) as conn:
        return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def _index_columns(db_path: Path, index: str) -> list[str]:
    with sqlite3.connect(db_path) as conn:
        return [row[2] for row in conn.execute(f"PRAGMA index_info({index})")]


def test_initialization_does_not_implicitly_run_command_identity_migration(tmp_path: Path) -> None:
    db_path = tmp_path / "lightspeed-test.db"

    DatabaseService(str(db_path))

    assert _objects(db_path) == []


def test_command_identity_migration_is_idempotent_and_complete(tmp_path: Path) -> None:
    db_path = tmp_path / "lightspeed-test.db"
    service = DatabaseService(str(db_path))

    service.ensure_ls_go_command_identity_schema()
    first_schema = _objects(db_path)
    service.ensure_ls_go_command_identity_schema()
    second_schema = _objects(db_path)

    assert first_schema == second_schema
    assert {(kind, name) for kind, name, _ in second_schema} == {
        ("table", "ls_go_command_identities"),
        ("table", "ls_go_command_queue_state"),
        ("index", "idx_ls_go_command_task"),
        ("index", "idx_ls_go_command_job"),
    }
    assert _column_names(db_path, "ls_go_command_identities") == IDENTITY_COLUMNS
    assert _column_names(db_path, "ls_go_command_queue_state") == QUEUE_STATE_COLUMNS
    assert _index_columns(db_path, "idx_ls_go_command_task") == ["task_id"]
    assert _index_columns(db_path, "idx_ls_go_command_job") == ["job_id"]

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
