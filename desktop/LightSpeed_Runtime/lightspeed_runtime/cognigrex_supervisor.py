from __future__ import annotations

"""Neo-supervised Cognigrex workflow over the existing LightSpeed floor runtime.

This module is intentionally additive. It does not create a second runtime,
queue, model server, canonical library, or publication path. It composes the
existing local_floor_runner with a task-specific temporary contract, writes
receipt-backed aggregate state into Neo's private output area, and keeps
Achilles outside the local execution sequence as the canonical/release gate.

Persisted learning is operational metadata only: instruction hashes, routes,
statuses and bounded success statistics. Raw instructions and source content
are not retained in the learning state.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any, Callable, Iterable

from lightspeed_runtime.local_floor_runner import (
    DEFAULT_CONTRACT_PATH,
    LocalFloorRunnerError,
    load_contract,
    resolve_contract_shell_root,
    run_floor,
)


SUPERVISOR_SCHEMA = "lightspeed-cognigrex-supervisor-v1"
LEARNING_SCHEMA = "lightspeed-cognigrex-learning-v1"
LEARNING_ALPHA = 0.2

FloorRunner = Callable[..., dict[str, Any]]

SPECIALIST_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Merovingian",
        (
            "runtime",
            "process",
            "service",
            "storage",
            "recovery",
            "persist",
            "persistence",
            "downtime",
            "health",
            "resource",
            "memory",
            "database",
            "bridge",
            "localhost",
        ),
    ),
    (
        "Trinity",
        (
            "ui",
            "ux",
            "interface",
            "visual",
            "web",
            "website",
            "screen",
            "layout",
            "interaction",
            "accessibility",
        ),
    ),
    (
        "TheConstruct",
        (
            "cad",
            "mesh",
            "3d",
            "digital twin",
            "simulation",
            "simulate",
            "step",
            "stl",
            "3mf",
            "glb",
            "geometry",
            "render",
        ),
    ),
    (
        "Smith",
        (
            "code",
            "build",
            "test",
            "schema",
            "transform",
            "compile",
            "git",
            "repo",
            "repository",
            "data pipeline",
            "export",
            "artifact",
        ),
    ),
    (
        "Oracle",
        (
            "source",
            "evidence",
            "research",
            "citation",
            "reference",
            "known",
            "document",
            "library",
            "provenance source",
        ),
    ),
    (
        "Architect",
        (
            "architecture",
            "project",
            "plan",
            "dependency",
            "topology",
            "workflow",
            "system",
            "scope",
            "roadmap",
            "design",
        ),
    ),
)

PROOF_KEYWORDS = (
    "proof",
    "verify",
    "verification",
    "validate",
    "validation",
    "audit",
    "claim",
    "conflict",
    "contradiction",
    "confidence",
    "supersed",
    "canonical",
    "canon",
    "publish",
    "release",
)


@dataclass(frozen=True)
class WorkflowPlan:
    workflow_id: str
    instruction_sha256: str
    primary_floors: tuple[str, ...]
    floor_sequence: tuple[str, ...]
    proof_required: bool
    canonical_promotion_authorized: bool = False
    public_publish_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "instruction_sha256": self.instruction_sha256,
            "primary_floors": list(self.primary_floors),
            "floor_sequence": list(self.floor_sequence),
            "proof_required": self.proof_required,
            "canonical_promotion_authorized": self.canonical_promotion_authorized,
            "public_publish_authorized": self.public_publish_authorized,
        }


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def instruction_hash(instruction: str) -> str:
    return hashlib.sha256(instruction.strip().encode("utf-8")).hexdigest()


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def classify_primary_floors(instruction: str) -> tuple[str, ...]:
    """Return a bounded ordered specialist set for Neo to coordinate.

    The classifier is deliberately deterministic. Persisted operational learning
    may later inform a secondary recommendation, but it does not silently change
    the route or authority model.
    """
    text = instruction.strip().casefold()
    if not text:
        return ("Architect",)

    matched: list[str] = []
    for floor, keywords in SPECIALIST_KEYWORDS:
        if _contains_any(text, keywords):
            matched.append(floor)

    if not matched:
        matched.append("Architect")
    return tuple(matched)


def build_workflow_plan(
    instruction: str,
    *,
    task_id: str | None = None,
) -> WorkflowPlan:
    digest = instruction_hash(instruction)
    suffix = digest[:12]
    stable_task = (task_id or "ad-hoc").strip() or "ad-hoc"
    workflow_id = f"cognigrex-{stable_task}-{suffix}"
    primary = classify_primary_floors(instruction)
    text = instruction.strip().casefold()
    proof_required = bool(_contains_any(text, PROOF_KEYWORDS)) or True

    sequence: list[str] = ["Neo"]
    for floor in primary:
        if floor != "Neo" and floor not in sequence:
            sequence.append(floor)

    # Morpheus is the bounded contradiction/provenance proof stage for every
    # completed task. Oracle/Smith are included only when the task actually
    # routes through their specialist capabilities.
    if proof_required and "Morpheus" not in sequence:
        sequence.append("Morpheus")

    return WorkflowPlan(
        workflow_id=workflow_id,
        instruction_sha256=digest,
        primary_floors=primary,
        floor_sequence=tuple(sequence),
        proof_required=proof_required,
    )


def supervisor_output_dir(contract: dict[str, Any]) -> Path:
    return (
        resolve_contract_shell_root(contract)
        / "Z Axis"
        / "Z+2_Neo"
        / "data"
        / "temp_shells"
        / "outputs"
    )


def supervisor_receipt_paths(contract: dict[str, Any], workflow_id: str) -> tuple[Path, Path]:
    root = supervisor_output_dir(contract)
    safe_id = "".join(character if character.isalnum() or character in "-_." else "_" for character in workflow_id)
    return (
        root / f"cognigrex_supervisor_receipt_{safe_id}.json",
        root / "cognigrex_supervisor_receipt_latest.json",
    )


def learning_state_path(contract: dict[str, Any]) -> Path:
    return supervisor_output_dir(contract) / "cognigrex_learning_state.json"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _task_contract_overlay(
    contract: dict[str, Any],
    *,
    plan: WorkflowPlan,
    instruction: str,
    task_id: str | None,
    project_id: str | None,
) -> dict[str, Any]:
    """Return a temporary task-aware contract without mutating canonical files."""
    overlay = json.loads(json.dumps(contract))
    overlay["contract_id"] = f"{contract.get('contract_id', 'lightspeed')}::{plan.workflow_id}"
    overlay["cognigrex_supervisor"] = {
        "schema_version": SUPERVISOR_SCHEMA,
        "workflow_id": plan.workflow_id,
        "task_id": task_id,
        "project_id": project_id,
        "instruction_sha256": plan.instruction_sha256,
        "raw_instruction_persisted": False,
        "authority": {
            "operational_head": "Neo",
            "canonical_release_gate": "Achilles",
        },
    }

    for floor in overlay.get("floors") or []:
        if not isinstance(floor, dict):
            continue
        floor_name = str(floor.get("floor") or "")
        if floor_name not in plan.floor_sequence:
            continue
        training = dict(floor.get("training_context") or {})
        existing_goal = str(training.get("wake_goal") or "").strip()
        existing_role = str(training.get("assimilation_role") or "").strip()
        task_line = (
            f"Bounded Cognigrex task {task_id or plan.workflow_id}: {instruction.strip()}"
        )
        role_line = (
            f"Project {project_id or 'unresolved'}; return only your specialist result, "
            "evidence boundary, blocker and safe artifact/receipt route to Neo."
        )
        training["wake_goal"] = f"{existing_goal} {task_line}".strip()
        training["assimilation_role"] = f"{existing_role} {role_line}".strip()
        floor["training_context"] = training
    return overlay


def _validate_plan_against_contract(plan: WorkflowPlan, contract: dict[str, Any]) -> None:
    available = {
        str(item.get("floor"))
        for item in contract.get("floors") or []
        if isinstance(item, dict) and item.get("floor")
    }
    missing = [floor for floor in plan.floor_sequence if floor not in available]
    if missing:
        raise LocalFloorRunnerError(
            "Cognigrex workflow contract is missing required floor(s): " + ", ".join(missing)
        )


def _learning_default() -> dict[str, Any]:
    return {
        "schema_version": LEARNING_SCHEMA,
        "policy": {
            "scope": "private_local_operational_metadata_only",
            "raw_instruction_persisted": False,
            "raw_source_content_persisted": False,
            "canonical_write_authorized": False,
            "public_publish_authorized": False,
            "adaptive_routing_mode": "advisory_only",
        },
        "executed_observations": 0,
        "dry_run_observations": 0,
        "floors": {},
        "last_workflow": None,
    }


def update_learning_state(
    contract: dict[str, Any],
    aggregate: dict[str, Any],
) -> dict[str, Any]:
    """Persist privacy-bounded online routing statistics.

    This is an intentionally small online-learning surface: each specialist
    accumulates route frequency and an EWMA completion score. It is advisory
    only and cannot alter canonical or publication state.
    """
    path = learning_state_path(contract)
    state = _read_json(path) or _learning_default()
    if state.get("schema_version") != LEARNING_SCHEMA:
        state = _learning_default()

    requested_execution = bool(aggregate.get("requested_execution"))
    counter = "executed_observations" if requested_execution else "dry_run_observations"
    state[counter] = int(state.get(counter) or 0) + 1

    floor_state = state.setdefault("floors", {})
    for row in aggregate.get("floors") or []:
        if not isinstance(row, dict):
            continue
        floor = str(row.get("floor") or "unknown")
        current = dict(floor_state.get(floor) or {})
        current["route_count"] = int(current.get("route_count") or 0) + 1
        current["last_status"] = row.get("status")
        current["last_seen_at"] = aggregate.get("created_at")
        if requested_execution:
            completed = 1.0 if row.get("status") == "completed" else 0.0
            previous = current.get("ewma_completion")
            current["executed_count"] = int(current.get("executed_count") or 0) + 1
            current["completed_count"] = int(current.get("completed_count") or 0) + int(completed)
            current["ewma_completion"] = (
                completed
                if previous is None
                else round((1.0 - LEARNING_ALPHA) * float(previous) + LEARNING_ALPHA * completed, 6)
            )
        floor_state[floor] = current

    state["last_workflow"] = {
        "workflow_id": aggregate.get("workflow_id"),
        "instruction_sha256": aggregate.get("instruction_sha256"),
        "created_at": aggregate.get("created_at"),
        "requested_execution": requested_execution,
        "floor_sequence": [row.get("floor") for row in aggregate.get("floors") or []],
        "status": aggregate.get("status"),
    }
    _atomic_write_json(path, state)
    state["state_path"] = str(path)
    return state


def run_supervised_workflow(
    instruction: str,
    *,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    task_id: str | None = None,
    project_id: str | None = None,
    dry_run: bool = True,
    allow_heavy: bool = False,
    receipt_target: str = "neo",
    stop_on_failure: bool = True,
    runner: FloorRunner = run_floor,
    persist_learning: bool = True,
) -> dict[str, Any]:
    if not instruction.strip():
        raise LocalFloorRunnerError("Cognigrex supervised workflow requires a non-empty instruction")

    contract = load_contract(contract_path)
    plan = build_workflow_plan(instruction, task_id=task_id)
    _validate_plan_against_contract(plan, contract)
    overlay = _task_contract_overlay(
        contract,
        plan=plan,
        instruction=instruction,
        task_id=task_id,
        project_id=project_id,
    )

    rows: list[dict[str, Any]] = []
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix="cognigrex_task_contract_",
        encoding="utf-8",
        delete=False,
    ) as handle:
        json.dump(overlay, handle, indent=2, sort_keys=True)
        handle.write("\n")
        overlay_path = Path(handle.name)

    try:
        for sequence, floor in enumerate(plan.floor_sequence, start=1):
            receipt = runner(
                contract_path=overlay_path,
                floor=floor,
                dry_run=dry_run,
                allow_heavy=allow_heavy,
                receipt_target=receipt_target,
            )
            row = {
                "sequence": sequence,
                "floor": floor,
                "status": receipt.get("status"),
                "receipt_id": receipt.get("receipt_id"),
                "receipt_path": receipt.get("receipt_path"),
                "model": receipt.get("model"),
                "resource_state": (receipt.get("resource_preflight") or {}).get("execution_state"),
                "elapsed_ms": receipt.get("elapsed_ms"),
            }
            rows.append(row)
            if stop_on_failure and receipt.get("status") in {"failed", "blocked"}:
                break
    finally:
        try:
            overlay_path.unlink()
        except FileNotFoundError:
            pass

    statuses = [str(row.get("status") or "unknown") for row in rows]
    complete = len(rows) == len(plan.floor_sequence)
    failed = any(status in {"failed", "blocked"} for status in statuses)
    aggregate_status = "failed" if failed else ("complete" if complete else "partial")

    aggregate: dict[str, Any] = {
        "schema_version": SUPERVISOR_SCHEMA,
        "workflow_id": plan.workflow_id,
        "created_at": utc_now_iso(),
        "task_id": task_id,
        "project_id": project_id,
        "instruction_sha256": plan.instruction_sha256,
        "raw_instruction_persisted": False,
        "requested_execution": not dry_run,
        "allow_heavy": allow_heavy,
        "status": aggregate_status,
        "complete_workflow": complete,
        "operational_head": "Neo",
        "canonical_release_gate": "Achilles",
        "primary_floors": list(plan.primary_floors),
        "floor_sequence": list(plan.floor_sequence),
        "floors": rows,
        "canonical_promotion_authorized": False,
        "public_publish_authorized": False,
        "de_sporte_content_ingest_authorized": False,
        "next_gate": "Achilles/ACR3 review of durable receipts before canonical promotion or release",
    }

    timestamped, latest = supervisor_receipt_paths(contract, plan.workflow_id)
    _atomic_write_json(timestamped, aggregate)
    _atomic_write_json(latest, aggregate)
    aggregate["receipt_path"] = str(timestamped)
    aggregate["latest_receipt_path"] = str(latest)

    if persist_learning:
        learning = update_learning_state(contract, aggregate)
        aggregate["learning_state_path"] = learning.get("state_path")
        aggregate["learning_mode"] = "private_operational_metadata_advisory_only"

    return aggregate


__all__ = [
    "LEARNING_SCHEMA",
    "SUPERVISOR_SCHEMA",
    "WorkflowPlan",
    "build_workflow_plan",
    "classify_primary_floors",
    "instruction_hash",
    "learning_state_path",
    "run_supervised_workflow",
    "supervisor_receipt_paths",
    "update_learning_state",
]
