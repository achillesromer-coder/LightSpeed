from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import pytest

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "recovery", BASE / "scripts/achilles_lsgo_recovery_snapshot.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(tmp_path: Path) -> Path:
    path = tmp_path / "native.db"
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE jobs(id INTEGER PRIMARY KEY,job_type TEXT,status TEXT,result_json TEXT);
            CREATE TABLE tasks(id INTEGER PRIMARY KEY,status TEXT);
            CREATE TABLE ls_go_command_identities(command_id TEXT,queue_state TEXT,job_id INTEGER);
        """)
        db.executemany("INSERT INTO jobs VALUES (?,?,?,NULL)", [
            (1,"ls_go_command","completed"), (2,"ls_go_command","held"),
            (3,"ls_go_command","blocked"), (4,"external","completed")
        ])
        db.executemany("INSERT INTO tasks VALUES (?,?)",
                       [(1,"active"),(2,"pending")])
        db.executemany("INSERT INTO ls_go_command_identities VALUES (?,?,?)", [
            ("A","queued",None),("B","queued",1),
            ("C","review",2),("D","queued",3)
        ])
    return path


def test_no_running_with_unlinked_identity_is_review_hold_and_no_db_change(tmp_path):
    p = fixture(tmp_path)
    before = hashlib.sha256(p.read_bytes()).hexdigest()
    out = module.inspect_database(p)
    assert out["command_identities"] == 4
    assert out["unlinked_identity_count"] == 1
    assert out["unresolved_running_jobs"] == 0
    assert out["state"] == "UNLINKED_COMMAND_IDENTITY_REVIEW_HOLD"
    assert out["native_modified"] is False
    assert out["consumer_restart_authorized"] is False
    assert out["jobs_dispatched"] == 0
    assert hashlib.sha256(p.read_bytes()).hexdigest() == before



def test_unassigned_identity_is_not_misreported_as_a_broken_job_reference(tmp_path):
    p = fixture(tmp_path)
    r = module.inspect_database(p)
    assert r["unassigned_identity_count"] == 1
    assert r["dangling_job_reference_count"] == 0
    assert any(x["class"] == "UNASSIGNED" and x["count"] == 1
               for x in r["linkage_class_counts"])
    assert r["state"] == "UNLINKED_COMMAND_IDENTITY_REVIEW_HOLD"
    assert not r["consumer_restart_authorized"]


def test_missing_job_reference_is_distinct_and_stays_held(tmp_path):
    p = fixture(tmp_path)
    with sqlite3.connect(p) as db:
        db.execute("UPDATE ls_go_command_identities SET job_id=999 "
                   "WHERE command_id='A'")
    r = module.inspect_database(p)
    assert r["unassigned_identity_count"] == 0
    assert r["dangling_job_reference_count"] == 1
    assert any(x["class"] == "DANGLING_JOB_REF" and x["count"] == 1
               for x in r["linkage_class_counts"])
    assert r["state"] == "UNLINKED_COMMAND_IDENTITY_REVIEW_HOLD"
    assert not r["consumer_restart_authorized"]


def test_mixed_unassigned_and_dangling_linkage_sum_matches_unlinked(tmp_path):
    p = fixture(tmp_path)
    with sqlite3.connect(p) as db:
        db.execute("INSERT INTO ls_go_command_identities "
                   "VALUES ('Z','review',999)")
    r = module.inspect_database(p)
    assert r["command_identities"] == 5
    assert r["unlinked_identity_count"] == 2
    assert r["unassigned_identity_count"] == 1
    assert r["dangling_job_reference_count"] == 1
    assert r["jobs_dispatched"] == 0


def test_running_job_holds_even_with_completed_terminal_rows(tmp_path):
    p = fixture(tmp_path)
    with sqlite3.connect(p) as db:
        db.execute("UPDATE jobs SET status='running' WHERE id=2")
    report = module.inspect_database(p)
    assert report["unresolved_running_jobs"] == 1
    assert report["state"] == "UNRESOLVED_RUNNING_JOB_HOLD"


def test_foreign_job_type_is_not_accepted_as_consumed(tmp_path):
    p = fixture(tmp_path)
    with sqlite3.connect(p) as db:
        db.execute("UPDATE ls_go_command_identities SET job_id=4 WHERE command_id='A'")
    out = module.inspect_database(p)
    assert out["foreign_job_link_count"] == 1
    assert out["state"] == "FOREIGN_JOB_LINK_HOLD"


def test_null_job_type_is_foreign_not_completed(tmp_path):
    """SQLite NULL comparisons must not disguise a non-LS-GO job as completed."""
    p = fixture(tmp_path)
    with sqlite3.connect(p) as db:
        db.execute("UPDATE jobs SET job_type=NULL WHERE id=4")
        db.execute("UPDATE ls_go_command_identities SET job_id=4 WHERE command_id='A'")
    report = module.inspect_database(p)
    assert report["foreign_job_link_count"] == 1
    assert report["state"] == "FOREIGN_JOB_LINK_HOLD"
    assert report["consumer_restart_authorized"] is False
    assert report["jobs_dispatched"] == 0


def test_all_linked_still_requires_independent_lease_and_dbr(tmp_path):
    p = fixture(tmp_path)
    with sqlite3.connect(p) as db:
        db.execute("UPDATE ls_go_command_identities SET job_id=1 WHERE command_id='A'")
    out = module.inspect_database(p)
    assert out["unlinked_identity_count"] == 0
    assert out["state"] == "INDEPENDENT_SIGNED_LEASE_AND_DBR_HOLD"
    assert out["consumer_restart_authorized"] is False


def test_duplicate_identity_is_not_accepted(tmp_path):
    p = fixture(tmp_path)
    with sqlite3.connect(p) as db:
        db.execute("UPDATE ls_go_command_identities SET command_id='B' WHERE command_id='A'")
    out = module.inspect_database(p)
    assert out["duplicate_command_identities"] == 1
    assert out["state"] == "DUPLICATE_COMMAND_IDENTITY_HOLD"


def test_missing_database_and_schema_hold(tmp_path):
    with pytest.raises(module.RecoveryHold, match="NATIVE_DB_MISSING"):
        module.inspect_database(tmp_path / "absent.db")
    empty = tmp_path / "empty.db"
    sqlite3.connect(empty).close()
    with pytest.raises(module.RecoveryHold, match="REQUIRED_NATIVE_TABLES"):
        module.inspect_database(empty)


def test_unsupported_symlink_refused(tmp_path):
    p = fixture(tmp_path)
    alias = tmp_path / "alias.db"
    try:
        alias.symlink_to(p)
    except (OSError, NotImplementedError):
        pytest.skip("OS denies symlink creation")
    with pytest.raises(module.RecoveryHold, match="REDIRECTED"):
        module.inspect_database(alias)

def test_running_status_not_hidden_by_group_display_limit(tmp_path):
    p = fixture(tmp_path)
    with sqlite3.connect(p) as db:
        db.execute("DELETE FROM jobs")
        db.execute("DELETE FROM ls_go_command_identities")
        db.executemany("INSERT INTO jobs(id,job_type,status) VALUES (?,?,?)",
                       [(i + 1, "ls_go_command", f"a{i:03}") for i in range(45)]
                       + [(46, "ls_go_command", "running")])
    report = module.inspect_database(p)
    assert len(report["ls_go_job_status"]) == 40
    assert all(x["state"] != "running" for x in report["ls_go_job_status"])
    assert report["unresolved_running_jobs"] == 1
    assert report["state"] == "UNRESOLVED_RUNNING_JOB_HOLD"
    assert report["consumer_restart_authorized"] is False
    assert report["jobs_dispatched"] == 0
