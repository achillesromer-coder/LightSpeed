from __future__ import annotations

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
