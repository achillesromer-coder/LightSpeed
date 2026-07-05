from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from lightspeed_runtime.storage_paths import neo_actions_root


BRISBANE_TZ = timezone(timedelta(hours=10))


@dataclass(frozen=True)
class AgentRole:
    name: str
    role: str
    focus: str
    write_scope: tuple[str, ...]
    outputs: tuple[str, ...]
    handoff: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_agent_roles() -> list[AgentRole]:
    return [
        AgentRole(
            name="Sagan",
            role="unresolved_task_delegator",
            focus="Find unresolved tasks, cracks, file moves, culls, smoke gaps, and delegation priorities.",
            write_scope=(
                "dataindex/23_UNRESOLVED_TASKS_DELEGATION_QUEUE.md",
                "Z Axis/Z+1_Architect/data/finalization/unresolved_task_queue.json",
            ),
            outputs=("top_blockers", "delegation_queue", "handoff_recommendations"),
            handoff="Architect finalization queue and Neo operator brief",
        ),
        AgentRole(
            name="Peirce",
            role="primary_executor_fidelity",
            focus="Bind shared smart-floor contracts into functional project-wall and Bento descriptors.",
            write_scope=(
                "lightspeed_runtime/smart_floor_visuals.py",
                "lightspeed_runtime/project_component_wall.py",
                "tests/test_smart_floor_visuals.py",
                "tests/test_project_component_wall.py",
            ),
            outputs=("functional_patch", "targeted_tests", "remaining_code_gaps"),
            handoff="Trinity project wall and Merovingian smoke checks",
        ),
        AgentRole(
            name="Dewey",
            role="aesthetic_alignment_executor",
            focus="Align Bento, theme, loading, background, Z-floor dropdown, charts, maps, and simulation UI notes.",
            write_scope=(
                "lightspeed_runtime/ui_polish.py",
                "dataindex/13_UX_AMALGAMATION_PASS.md",
                "dataindex/22_SMART_FLOOR_VISUAL_ANALYSIS.md",
                "Z Axis/Z+3_Trinity/data/ui/*.json",
            ),
            outputs=("ui_alignment_patch", "visual_binding_tasks", "interaction_notes"),
            handoff="Trinity settings library and project wall renderer backlog",
        ),
    ]


def next_deadline(now: datetime, *, deadline: time = time(hour=8), tz=BRISBANE_TZ) -> datetime:
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    now = now.astimezone(tz)
    target = datetime.combine(now.date(), deadline, tzinfo=tz)
    if now >= target:
        target += timedelta(days=1)
    return target


def build_orchestration_window(
    root: Path,
    *,
    now: datetime | None = None,
    deadline: time = time(hour=8),
) -> dict[str, Any]:
    root = Path(root)
    current = now or datetime.now(BRISBANE_TZ)
    if current.tzinfo is None:
        current = current.replace(tzinfo=BRISBANE_TZ)
    current = current.astimezone(BRISBANE_TZ)
    target = next_deadline(current, deadline=deadline)
    remaining = max(0, int((target - current).total_seconds() // 60))
    cadence = 30 if remaining >= 180 else 15 if remaining >= 60 else 10

    return {
        "generated_at": current.isoformat(timespec="seconds"),
        "deadline": target.isoformat(timespec="seconds"),
        "minutes_remaining": remaining,
        "cadence_minutes": cadence,
        "root": str(root),
        "roles": [role.to_dict() for role in default_agent_roles()],
        "local_critical_path": [
            "keep process count clean and avoid unbounded recursive scans",
            "integrate only non-overlapping agent outputs",
            "run targeted tests after each accepted patch",
            "regenerate Trinity/dataindex catalogs after descriptor changes",
            "record residual blockers as finalization queue items instead of loose logs",
        ],
        "resource_rules": {
            "token_budget": "summarize large logs and generated files; inspect only the current patch surface",
            "process_budget": "prefer bounded tests; stop long silent runs after a useful wait window",
            "ui_budget": "descriptor-first for heavy maps/charts/sims; lazy-load renderers until opened",
            "filesystem_budget": "no destructive culls without explicit path guard and proof of preserved information",
        },
        "progress_bars": {
            "overall": {"done": 3, "total": 4, "label": "agents assigned, local bindings verified"},
            "current": {"done": 5, "total": 5, "label": "smart-floor widget binding verified"},
        },
        "outputs": {
            "neo_plan": str(default_orchestration_plan_path(root)),
            "dataindex_report": str(default_orchestration_report_path(root)),
        },
    }


def default_orchestration_plan_path(root: Path) -> Path:
    return neo_actions_root(root) / "orchestration_8am_plan.json"


def default_orchestration_report_path(root: Path) -> Path:
    return Path(root) / "dataindex" / "24_8AM_ORCHESTRATION_RUN.md"


def write_orchestration_window(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    payload = build_orchestration_window(root, now=now)
    plan_path = Path(payload["outputs"]["neo_plan"])
    report_path = Path(payload["outputs"]["dataindex_report"])

    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# 8am Orchestration Run",
        "",
        f"Generated: {payload['generated_at']}",
        f"Deadline: {payload['deadline']}",
        f"Minutes remaining: {payload['minutes_remaining']}",
        f"Cadence: every {payload['cadence_minutes']} minutes",
        "",
        "## Roles",
        "",
    ]
    for role in payload["roles"]:
        lines.append(f"- {role['name']} ({role['role']}): {role['focus']}")
    lines.extend(["", "## Local Critical Path", ""])
    lines.extend(f"- {item}" for item in payload["local_critical_path"])
    lines.extend(["", "## Resource Rules", ""])
    lines.extend(f"- {key}: {value}" for key, value in payload["resource_rules"].items())
    lines.append("")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return payload
