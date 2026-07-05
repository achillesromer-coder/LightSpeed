from __future__ import annotations

import gzip
import json
import sqlite3
from pathlib import Path

import pytest

from lightspeed_runtime.release_clean import (
    DATABASE_TABLES_TO_CLEAR,
    build_smoke_checklist,
    duplicate_surface_audit_descriptors,
    dry_run_cleanup_summary,
    generated_cache_temp_cleanup_plan,
    launch_setup_cleanup_plan,
    protected_release_paths,
    post_final_pass_relocation_plan,
    release_cleanup_table_plan,
    stale_runtime_row_cleanup_plan,
    resolve_within_root,
    project_workspace_root,
    cache_cleanup_roots,
    execute_clean_slate,
)


def _bootstrap_root(root: Path) -> None:
    (root / "Z Axis" / "Z+1_Architect" / "projects" / "Alpha").mkdir(parents=True, exist_ok=True)
    (root / "Z Axis" / "Z+1_Architect" / "projects" / "Beta").mkdir(parents=True, exist_ok=True)
    (root / ".pytest_cache").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "__pycache__").mkdir(parents=True, exist_ok=True)
    (root / "N.py").write_text("print('ok')", encoding="utf-8")
    (root / "Z Axis" / "Z-2_Oracle" / "data" / "library").mkdir(parents=True, exist_ok=True)
    (root / "Z Axis" / "Z-2_Oracle" / "data" / "encyclopedia").mkdir(parents=True, exist_ok=True)
    (root / "Z Axis" / "Z-2_Oracle" / "data" / "datatables").mkdir(parents=True, exist_ok=True)
    (root / "Z Axis" / "Z-2_Oracle" / "data" / "legacy" / "ai_logs").mkdir(parents=True, exist_ok=True)
    (root / "Z Axis" / "Z-4_Merovingian" / "data" / "reports" / "launch_readiness").mkdir(parents=True, exist_ok=True)


def _bootstrap_database(root: Path) -> Path:
    db_path = root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        for table in (
            "artifacts",
            "files",
            "jobs",
            "system_logs",
            "telemetry_data",
            "oracle_ingestion_tasks",
            "projects",
            "users",
            "z_contexts",
            "encyclopedia_entries",
        ):
            connection.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY, value TEXT)')
            connection.execute(f'INSERT INTO "{table}" (value) VALUES (?)', (f"{table}-value",))
    return db_path


def test_release_cleanup_plan_lists_runtime_tables_and_preserved_paths(tmp_path: Path) -> None:
    _bootstrap_root(tmp_path)
    plan = release_cleanup_table_plan(tmp_path)

    assert plan["database"]["path"].endswith(r"Z Axis\Z-4_Merovingian\data\db\lightspeed_unified.db")
    assert [table["name"] for table in plan["database"]["tables"]] == [table["name"] for table in DATABASE_TABLES_TO_CLEAR]
    assert str(tmp_path / "N.py") in plan["preserved_paths"]
    assert str(tmp_path / "Z Axis" / "Z-2_Oracle" / "data" / "library") in plan["preserved_paths"]


def test_path_guards_reject_outside_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-root"
    outside.mkdir(exist_ok=True)

    with pytest.raises(ValueError):
        resolve_within_root(tmp_path, outside)


def test_dry_run_summary_reports_workspace_entries_and_cache_candidates(tmp_path: Path) -> None:
    _bootstrap_root(tmp_path)
    summary = dry_run_cleanup_summary(tmp_path)

    assert summary["project_workspace"]["path"] == str(project_workspace_root(tmp_path))
    assert summary["project_workspace"]["entry_count"] == 2
    assert len(summary["project_workspace"]["entries"]) == 2
    assert summary["cache_cleanup"]["candidate_count"] == len(cache_cleanup_roots(tmp_path))
    assert any(item["path"].endswith(".pytest_cache") for item in summary["cache_cleanup"]["candidates"])
    assert any(item["exists"] is True for item in summary["cache_cleanup"]["candidates"])


def test_protected_paths_include_application_and_vault_roots(tmp_path: Path) -> None:
    _bootstrap_root(tmp_path)
    protected = {str(path) for path in protected_release_paths(tmp_path)}

    assert str(tmp_path / "N.py") in protected
    assert str(tmp_path / "Z Axis") in protected
    assert str(tmp_path / "Z Axis" / "Z-2_Oracle" / "data" / "library") in protected
    assert str(tmp_path / "Z Axis" / "Z-2_Oracle" / "data" / "datatables") in protected


def test_smoke_checklist_shape() -> None:
    checklist = build_smoke_checklist(Path.cwd())

    assert [step["order"] for step in checklist] == [1, 2, 3, 4, 5, 6]
    assert [step["name"] for step in checklist] == [
        "Compile",
        "Targeted Tests",
        "Full Tests",
        "Launch Readiness",
        "Diagnostics",
        "Blank-State Verification",
    ]
    assert all("command" in step and "purpose" in step for step in checklist)


def test_launch_and_setup_cleanup_plan_is_dry_run_only(tmp_path: Path) -> None:
    plan = launch_setup_cleanup_plan(tmp_path)

    assert plan["dry_run_only"] is True
    assert plan["launch_state"]["scope"] == "blank_release_prep"
    assert any(item["key"] == "first_run_complete" for item in plan["launch_state"]["keys"])
    assert plan["setup_state"]["scope"] == "guided_setup_prep"
    assert any(item["key"] == "active_floors" for item in plan["setup_state"]["keys"])


def test_stale_runtime_row_cleanup_plan_targets_user_project_company_rows(tmp_path: Path) -> None:
    plan = stale_runtime_row_cleanup_plan(tmp_path)

    table_names = [item["name"] for item in plan["target_tables"]]
    assert plan["dry_run_only"] is True
    assert plan["trigger"] == "after_proof_runs"
    assert set(table_names) >= {"projects", "companies", "users", "user_preferences"}


def test_generated_cache_temp_cleanup_plan_is_path_guarded(tmp_path: Path) -> None:
    (tmp_path / ".pytest_cache").mkdir(parents=True, exist_ok=True)
    plan = generated_cache_temp_cleanup_plan(tmp_path)

    assert plan["dry_run_only"] is True
    assert plan["candidate_count"] == len(plan["candidates"])
    assert all(item["within_root"] is True for item in plan["candidates"])
    assert any(item["path"].endswith(".pytest_cache") for item in plan["candidates"])


def test_duplicate_surface_audit_descriptors_cover_common_duplicate_entrypoints(tmp_path: Path) -> None:
    descriptors = duplicate_surface_audit_descriptors(tmp_path)

    assert any(item["entrypoint"] == "Legacy Theme Manager" and item["action"] == "cull_later" for item in descriptors)
    assert any(item["entrypoint"] == "Startup Wizard" and item["status"] == "primary" for item in descriptors)
    assert any(item["entrypoint"] == "Floating Popup Panel" for item in descriptors)


def test_post_final_pass_relocation_plan_moves_logs_outside_package_after_final_pass(tmp_path: Path) -> None:
    _bootstrap_root(tmp_path)
    plan = post_final_pass_relocation_plan(tmp_path)

    assert plan["dry_run_only"] is True
    assert plan["trigger"] == "after_complete_final_pass_before_v0_10_0_package"
    assert all(item["destination_inside_package"] is False for item in plan["relocations"])
    assert any(item["id"] == "oracle_ai_logs" and item["ready"] is True for item in plan["relocations"])
    assert any(item["id"] == "launch_readiness_reports" and item["ready"] is True for item in plan["relocations"])
    assert any(item["id"] == "test_caches" for item in plan["package_exclusions"])


def test_cache_cleanup_roots_accept_exact_split_runtime_but_reject_other_external_paths(tmp_path: Path) -> None:
    consolidation_root = tmp_path / "LightSpeed_Consolidated"
    app_root = consolidation_root / "Desktop_Hooks" / "LightSpeed"
    split_cache = consolidation_root / "LightSpeed_Runtime" / "lightspeed_runtime" / "__pycache__"
    split_cache.mkdir(parents=True)
    app_root.mkdir(parents=True)

    candidates = cache_cleanup_roots(app_root)

    assert split_cache.resolve() in candidates
    with pytest.raises(ValueError):
        resolve_within_root(app_root, consolidation_root / "unrelated-cache")


def test_execute_clean_slate_backs_up_and_clears_only_approved_state(tmp_path: Path) -> None:
    consolidation_root = tmp_path / "LightSpeed_Consolidated"
    app_root = consolidation_root / "Desktop_Hooks" / "LightSpeed"
    _bootstrap_root(app_root)
    db_path = _bootstrap_database(app_root)
    protected_config = app_root / "config" / "floor_contract.json"
    protected_config.parent.mkdir(parents=True)
    protected_config.write_text('{"floor":"Neo"}', encoding="utf-8")
    cache_file = app_root / ".pytest_cache" / "cache.bin"
    cache_file.write_bytes(b"cache")

    result = execute_clean_slate(
        app_root,
        consolidation_root=consolidation_root,
        run_id="20260706T010203Z",
        dry_run=False,
    )

    manifest_path = Path(result["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    backup_path = Path(manifest["database"]["backup_path"])
    assert backup_path.suffix == ".gz"
    with gzip.open(backup_path, "rb") as source:
        assert source.read(16) == b"SQLite format 3\x00"
    with sqlite3.connect(db_path) as connection:
        cleared = {
            table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in (
                "artifacts",
                "files",
                "jobs",
                "system_logs",
                "telemetry_data",
                "oracle_ingestion_tasks",
                "projects",
                "users",
            )
        }
        retained = {
            table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in ("z_contexts", "encyclopedia_entries")
        }
    assert set(cleared.values()) == {0}
    assert retained == {"z_contexts": 1, "encyclopedia_entries": 1}
    assert protected_config.read_text(encoding="utf-8") == '{"floor":"Neo"}'
    assert not cache_file.exists()
    assert not (app_root / "Z Axis" / "Z+1_Architect" / "projects" / "Alpha").exists()
    assert (Path(manifest["project_workspace"]["quarantine_path"]) / "Alpha").exists()
    assert manifest["database"]["source_sha256"]
    assert manifest["database"]["backup_sha256"]
    assert manifest["status"] == "completed"
