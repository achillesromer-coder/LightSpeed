#!/usr/bin/env python3
"""Read-only LS GO command-to-job recovery review.

No command body, private GPT content, service restart, lock mutation, queue
dispatch, signed authority issuance, native admission, or database writes.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

SCHEMA = "CGX-ACHILLES-LSGO-NATIVE-RECONCILIATION/0.1"
TABLES = ("jobs", "tasks", "ls_go_command_identities")


class RecoveryHold(ValueError):
    pass


def _columns(db: sqlite3.Connection, name: str) -> set[str]:
    return {row[1] for row in db.execute("PRAGMA table_info('" + name + "')")}


def _groups(db: sqlite3.Connection, table: str, field: str,
            *, ls_go_only: bool = False) -> list[dict]:
    sql = f'SELECT "{field}",COUNT(*) FROM "{table}" '
    params: tuple[str, ...] = ()
    if ls_go_only:
        sql += "WHERE job_type=? "
        params = ("ls_go_command",)
    sql += f'GROUP BY "{field}" ORDER BY "{field}" LIMIT 40'
    return [{"state": str(state), "count": int(count)}
            for state, count in db.execute(sql, params)]


def inspect_database(path: Path) -> dict:
    path = Path(path).absolute()
    if not path.is_file() or path.is_symlink():
        raise RecoveryHold("NATIVE_DB_MISSING_OR_REDIRECTED_HOLD")
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=3)) as db:
            db.execute("PRAGMA query_only=ON")
            names = {row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if not set(TABLES).issubset(names):
                raise RecoveryHold("REQUIRED_NATIVE_TABLES_MISSING_HOLD")
            jobs = _columns(db, "jobs")
            tasks = _columns(db, "tasks")
            identities = _columns(db, "ls_go_command_identities")
            if not ({"id", "job_type", "status"}.issubset(jobs)
                    and {"status"}.issubset(tasks)
                    and {"job_id", "command_id", "queue_state"}.issubset(identities)):
                raise RecoveryHold("REQUIRED_NATIVE_COLUMNS_MISSING_HOLD")
            job_groups = _groups(db, "jobs", "status", ls_go_only=True)
            identity_groups = _groups(db, "ls_go_command_identities", "queue_state")
            task_groups = _groups(db, "tasks", "status")
            matches = [
                {"queue_state": str(queue), "job_state": str(job), "count": int(n)}
                for queue, job, n in db.execute(
                    "SELECT i.queue_state,"
                    "CASE WHEN j.id IS NULL THEN 'UNLINKED' "
                    "WHEN j.job_type<>'ls_go_command' THEN 'FOREIGN_JOB_TYPE' "
                    "ELSE COALESCE(j.status,'UNKNOWN') END,COUNT(*) "
                    "FROM ls_go_command_identities i LEFT JOIN jobs j ON j.id=i.job_id "
                    "GROUP BY 1,2 ORDER BY 1,2 LIMIT 60"
                )
            ]
            total = db.execute("SELECT COUNT(*) FROM ls_go_command_identities").fetchone()[0]
            duplicates = db.execute(
                "SELECT COUNT(*)-COUNT(DISTINCT command_id) FROM ls_go_command_identities"
            ).fetchone()[0]
            running = next((row["count"] for row in job_groups
                            if row["state"] == "running"), 0)
            unlinked = sum(x["count"] for x in matches if x["job_state"] == "UNLINKED")
            foreign = sum(x["count"] for x in matches if x["job_state"] == "FOREIGN_JOB_TYPE")
            if sum(x["count"] for x in matches) != total:
                raise RecoveryHold("INCOMPLETE_IDENTITY_LINKAGE_HOLD")
            verdict = ("UNRESOLVED_RUNNING_JOB_HOLD" if running else
                       "FOREIGN_JOB_LINK_HOLD" if foreign else
                       "DUPLICATE_COMMAND_IDENTITY_HOLD" if duplicates else
                       "UNLINKED_COMMAND_IDENTITY_REVIEW_HOLD" if unlinked else
                       "INDEPENDENT_SIGNED_LEASE_AND_DBR_HOLD")
            return {
                "schema": SCHEMA, "state": verdict,
                "command_identities": total, "duplicate_command_identities": duplicates,
                "ls_go_job_status": job_groups,
                "canonical_queue_state": identity_groups,
                "task_status": task_groups,
                "identity_to_job_linkage": matches,
                "unlinked_identity_count": unlinked,
                "foreign_job_link_count": foreign,
                "unresolved_running_jobs": running,
                "body_fields_read": False, "native_modified": False,
                "commands_replayed": False, "jobs_dispatched": 0,
                "singleton_lock_modified": False, "owner_lease_verified": False,
                "consumer_restart_authorized": False, "native_cgx_admitted": False,
                "public_release": False,
            }
    except sqlite3.Error as exc:
        raise RecoveryHold("NATIVE_SQLITE_READ_HOLD") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect_database(args.database), sort_keys=True))
    except RecoveryHold as exc:
        print(json.dumps({"schema": SCHEMA, "state": str(exc),
                          "native_modified": False, "jobs_dispatched": 0},
                         sort_keys=True))
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
