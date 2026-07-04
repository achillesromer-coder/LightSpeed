from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.orchestration_window import (
    build_orchestration_window,
    default_agent_roles,
    next_deadline,
    write_orchestration_window,
)


def test_next_deadline_targets_same_day_before_8am_and_next_day_after() -> None:
    tz = timezone(timedelta(hours=10))

    before = next_deadline(datetime(2026, 4, 13, 7, 30, tzinfo=tz))
    after = next_deadline(datetime(2026, 4, 13, 23, 50, tzinfo=tz))

    assert before.isoformat() == "2026-04-13T08:00:00+10:00"
    assert after.isoformat() == "2026-04-14T08:00:00+10:00"


def test_default_agent_roles_match_requested_three_lane_orchestration() -> None:
    roles = default_agent_roles()

    assert [role.name for role in roles] == ["Sagan", "Peirce", "Dewey"]
    assert roles[0].role == "unresolved_task_delegator"
    assert roles[1].role == "primary_executor_fidelity"
    assert roles[2].role == "aesthetic_alignment_executor"
    assert all(role.write_scope for role in roles)


def test_build_orchestration_window_sets_resource_rules_and_progress() -> None:
    tz = timezone(timedelta(hours=10))
    payload = build_orchestration_window(
        RUNTIME_ROOT,
        now=datetime(2026, 4, 13, 23, 50, tzinfo=tz),
    )

    assert payload["minutes_remaining"] == 490
    assert payload["cadence_minutes"] == 30
    assert len(payload["roles"]) == 3
    assert payload["progress_bars"]["overall"]["done"] == 3
    assert payload["progress_bars"]["overall"]["total"] == 4
    assert payload["progress_bars"]["current"]["done"] == 5
    assert "process_budget" in payload["resource_rules"]
    assert "no destructive culls" in payload["resource_rules"]["filesystem_budget"]


def test_write_orchestration_window_persists_neo_plan_and_report(tmp_path: Path) -> None:
    tz = timezone(timedelta(hours=10))
    payload = write_orchestration_window(
        tmp_path,
        now=datetime(2026, 4, 13, 23, 50, tzinfo=tz),
    )

    plan_path = Path(payload["outputs"]["neo_plan"])
    report_path = Path(payload["outputs"]["dataindex_report"])

    assert plan_path.exists()
    assert report_path.exists()
    assert "8am Orchestration Run" in report_path.read_text(encoding="utf-8")
    assert "Sagan" in plan_path.read_text(encoding="utf-8")
