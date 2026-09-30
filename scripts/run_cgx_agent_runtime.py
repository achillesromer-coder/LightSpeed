#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
RUNTIME_ROOT = ROOT / "desktop" / "LightSpeed_Runtime"
for p in (SCRIPTS, RUNTIME_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from cgx_assurance_route import route as assurance_route, CASCADE
from cgx_assurance_preflight import assess as assurance_assess
from resolve_cgx_extensions import resolve as custodial_resolve
from cgx_custodial_preflight import assess_custodial
from lightspeed_runtime.cognigrex_supervisor import build_workflow_plan, run_supervised_workflow
from lightspeed_runtime.local_floor_runner import DEFAULT_CONTRACT_PATH

SCHEMA = "CGX-AGENT-EXECUTION-ENVELOPE/0.2"
EXECUTION_CLASS_RANK = {
    "READ_ONLY": 0,
    "COMPUTE_ONLY": 1,
    "DIGITAL_WRITE": 2,
    "EXTERNAL_ACTION": 3,
    "PHYSICAL_ACTUATION": 4,
}

def now_utc() -> datetime:
    return datetime.now(UTC)

def iso_now() -> str:
    return now_utc().isoformat(timespec="seconds")

def parse_time(value: str) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("lease timestamp must be timezone-aware")
    return dt.astimezone(UTC)

def instruction_text(args: argparse.Namespace) -> str:
    if args.instruction_file:
        return args.instruction_file.read_text(encoding="utf-8").strip()
    if args.instruction:
        return args.instruction.strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise SystemExit("Provide --instruction, --instruction-file, or pipe task text on stdin.")

def load_optional(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload

def subset_scope(name: str, allowed: list[str] | None, requested: str | None, reasons: list[str]) -> None:
    if not allowed:
        return
    if not requested:
        reasons.append(f"lease-scope-requires-{name}")
    elif requested not in set(map(str, allowed)):
        reasons.append(f"lease-{name}-out-of-scope:{requested}")

def validate_lease(
    lease: dict[str, Any] | None,
    *,
    agent_id: str,
    domain: str,
    execution_depth: str,
    cascade_class: str,
    task_id: str | None,
    project_id: str | None,
    action_class: str,
    execution_class: str,
    planned_floors: list[str],
    consequential: bool,
) -> tuple[bool, list[str], dict[str, Any]]:
    reasons: list[str] = []
    summary: dict[str, Any] = {}
    if lease is None:
        return False, ["execution-lease-missing"], summary

    lease_class = str(lease.get("lease_class") or "")
    summary = {
        "lease_id": lease.get("lease_id"),
        "lease_class": lease_class,
        "state": lease.get("state"),
        "issued_by": lease.get("issued_by"),
        "subject_agent": lease.get("subject_agent"),
        "valid_until": lease.get("valid_until"),
        "authority_phase": lease.get("authority_phase"),
        "authority_phase_ref": lease.get("authority_phase_ref"),
    }
    if lease_class not in EXECUTION_CLASS_RANK:
        reasons.append("lease-class-invalid")
    elif EXECUTION_CLASS_RANK[lease_class] < EXECUTION_CLASS_RANK[execution_class]:
        reasons.append(f"lease-class-insufficient:{lease_class}<{execution_class}")
    if lease.get("state") != "ACTIVE":
        reasons.append(f"lease-not-active:{lease.get('state','UNKNOWN')}")
    if str(lease.get("subject_agent") or "") != agent_id:
        reasons.append("lease-subject-agent-mismatch")
    try:
        start = parse_time(str(lease["valid_from"]))
        end = parse_time(str(lease["valid_until"]))
        current = now_utc()
        if end <= start:
            reasons.append("lease-invalid-time-window")
        elif not (start <= current <= end):
            reasons.append("lease-outside-validity-window")
    except (KeyError, ValueError, TypeError):
        reasons.append("lease-time-invalid")
    if domain not in set(map(str, lease.get("domains") or [])):
        reasons.append(f"lease-domain-out-of-scope:{domain}")
    if execution_depth not in set(map(str, lease.get("execution_depths") or [])):
        reasons.append(f"lease-execution-depth-out-of-scope:{execution_depth}")
    ceiling = str(lease.get("max_cascade_class") or "")
    if ceiling not in CASCADE:
        reasons.append("lease-cascade-ceiling-invalid")
    elif CASCADE[cascade_class] > CASCADE[ceiling]:
        reasons.append(f"lease-cascade-exceeded:{cascade_class}>{ceiling}")

    allowed_floors = set(map(str, lease.get("allowed_floors") or []))
    if not allowed_floors:
        reasons.append("lease-allowed-floors-empty")
    else:
        missing = [floor for floor in planned_floors if floor not in allowed_floors]
        if missing:
            reasons.append("lease-floor-out-of-scope:" + ",".join(missing))

    scope = lease.get("scope") or {}
    subset_scope("task", scope.get("task_ids"), task_id, reasons)
    subset_scope("project", scope.get("project_ids"), project_id, reasons)
    subset_scope("action-class", scope.get("action_classes"), action_class, reasons)

    if lease.get("revocable") is not True:
        reasons.append("lease-not-revocable")
    phase = str(lease.get("authority_phase") or "")
    if phase not in {"PRE_LAUNCH","LAUNCH_TRANSITION","DISTRIBUTED_OPERATION","SUCCESSION_OR_RECOVERY"}:
        reasons.append("lease-authority-phase-invalid")
    if not lease.get("authority_phase_ref"):
        reasons.append("lease-authority-phase-ref-missing")
    if EXECUTION_CLASS_RANK[execution_class] >= EXECUTION_CLASS_RANK["DIGITAL_WRITE"]:
        if not lease.get("rollback_or_recovery_ref"):
            reasons.append("lease-rollback-or-recovery-ref-missing")
    if EXECUTION_CLASS_RANK[execution_class] >= EXECUTION_CLASS_RANK["EXTERNAL_ACTION"]:
        if not lease.get("stop_authority_ref"):
            reasons.append("lease-stop-authority-missing")
        if not lease.get("safe_state_ref"):
            reasons.append("lease-safe-state-missing")
    if consequential:
        for field in ("assurance_receipt_ref", "custodial_receipt_ref", "risk_acceptance_ref"):
            if not lease.get(field):
                reasons.append("lease-" + field.replace("_", "-") + "-missing")
        if phase in {"PRE_LAUNCH","LAUNCH_TRANSITION"} and not lease.get("root_authority_receipt_ref"):
            reasons.append("lease-root-authority-receipt-ref-missing")
    if execution_depth == "publish" and not lease.get("release_receipt_ref"):
        reasons.append("lease-release-receipt-ref-missing")
    return not reasons, reasons, summary

def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)

def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Guarded Cognigrex agent-runtime entrypoint. The script invokes the "
            "reasoning/specialist runtime; effectful actions remain behind a downstream tool gate."
        )
    )
    source = ap.add_mutually_exclusive_group()
    source.add_argument("--instruction")
    source.add_argument("--instruction-file", type=Path)
    ap.add_argument("--task-id")
    ap.add_argument("--project-id")
    ap.add_argument("--agent-id", default="Neo")
    ap.add_argument("--domain", required=True, choices=["romer", "eco", "emassc", "lightspeed"])
    ap.add_argument("--execution-depth", required=True, choices=["inspect", "propose", "simulate", "execute", "build", "publish"])
    ap.add_argument("--reasoning-depth", default="standard")
    ap.add_argument("--cascade-class", default="C0", choices=["C0", "C1", "C2", "C3", "C4"])
    ap.add_argument("--tags", default="")
    ap.add_argument("--action-class")
    ap.add_argument("--execution-class", default="COMPUTE_ONLY", choices=list(EXECUTION_CLASS_RANK))
    ap.add_argument("--assurance-assessment-json", type=Path)
    ap.add_argument("--custodial-assessment-json", type=Path)
    ap.add_argument("--execution-lease-json", type=Path)
    ap.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--execute", action="store_true", help="Invoke the bounded model/specialist runtime. Does not itself perform external writes or physical actuation.")
    ap.add_argument("--allow-heavy", action="store_true")
    ap.add_argument("--continue-on-failure", action="store_true")
    ap.add_argument("--receipt-json", type=Path)
    args = ap.parse_args()

    instruction = instruction_text(args)
    if not instruction:
        raise SystemExit("Instruction is empty.")
    tags = sorted({x.strip().lower() for x in args.tags.split(",") if x.strip()})
    action_class = args.action_class or args.execution_depth
    effectful = EXECUTION_CLASS_RANK[args.execution_class] >= EXECUTION_CLASS_RANK["DIGITAL_WRITE"]
    consequential = effectful and (
        args.execution_depth in {"execute", "build", "publish"}
        or CASCADE[args.cascade_class] >= CASCADE["C2"]
    )

    plan = build_workflow_plan(instruction, task_id=args.task_id)
    assurance_resolution = assurance_route(args.domain, args.execution_depth, args.cascade_class, tags)
    assurance_assessment = load_optional(args.assurance_assessment_json)
    assurance_decision, assurance_reasons = assurance_assess(assurance_resolution, assurance_assessment)
    custodial_resolution = custodial_resolve(args.domain, args.execution_depth, args.reasoning_depth, args.cascade_class, tags)
    custodial_assessment = load_optional(args.custodial_assessment_json)
    custodial_decision, custodial_reasons = assess_custodial(custodial_resolution, custodial_assessment)

    preflight_holds: list[str] = []
    if assurance_decision == "HOLD":
        preflight_holds += ["assurance:" + x for x in assurance_reasons]
    if custodial_decision == "HOLD":
        preflight_holds += ["custodial:" + x for x in custodial_reasons]

    lease_payload = load_optional(args.execution_lease_json)
    if args.execute:
        lease_ok, lease_reasons, lease_summary = validate_lease(
            lease_payload,
            agent_id=args.agent_id,
            domain=args.domain,
            execution_depth=args.execution_depth,
            cascade_class=args.cascade_class,
            task_id=args.task_id,
            project_id=args.project_id,
            action_class=action_class,
            execution_class=args.execution_class,
            planned_floors=list(plan.floor_sequence),
            consequential=consequential,
        )
    else:
        lease_ok, lease_reasons, lease_summary = False, [], {}

    supervisor_receipt: dict[str, Any] | None = None
    exit_code = 0
    if args.execute and effectful and preflight_holds:
        decision = "HOLD"
        exit_code = 3
    elif args.execute and not lease_ok:
        decision = "HOLD"
        exit_code = 4
    elif args.preflight_only:
        decision = "HOLD_FOR_EFFECTFUL_ACTION" if preflight_holds else "CLEARED_FOR_AUTHORITY_GATE"
        exit_code = 3 if preflight_holds else 0
    else:
        # COMPUTE_ONLY may produce the evidence needed to close an effectful-action
        # blocker. No side-effectful provider or actuator is invoked by this entrypoint.
        supervisor_receipt = run_supervised_workflow(
            instruction,
            contract_path=args.contract,
            task_id=args.task_id,
            project_id=args.project_id,
            dry_run=not args.execute,
            allow_heavy=args.allow_heavy,
            stop_on_failure=not args.continue_on_failure,
        )
        if args.execute:
            if effectful:
                decision = "MODEL_PLAN_COMPLETE_CLEARED_FOR_TOOL_GATE"
            else:
                decision = "COMPUTE_EXECUTED_WITH_ACTION_BLOCKERS" if preflight_holds else "COMPUTE_EXECUTED_CLEAN"
            exit_code = 0 if supervisor_receipt.get("status") != "failed" else 2
        else:
            decision = "DRY_RUN_WITH_BLOCKERS" if preflight_holds else "DRY_RUN_CLEARED"
            exit_code = 0 if supervisor_receipt.get("status") != "failed" else 2

    receipt = {
        "schema": SCHEMA,
        "created_at": iso_now(),
        "Task_ID": args.task_id,
        "project_id": args.project_id,
        "agent_id": args.agent_id,
        "instruction_sha256": hashlib.sha256(instruction.encode("utf-8")).hexdigest(),
        "raw_instruction_persisted": False,
        "context": {
            "domain": args.domain,
            "execution_depth": args.execution_depth,
            "reasoning_depth": args.reasoning_depth,
            "cascade_class": args.cascade_class,
            "tags": tags,
            "action_class": action_class,
            "execution_class": args.execution_class,
        },
        "planned_floors": list(plan.floor_sequence),
        "decision": decision,
        "execution_requested": args.execute,
        "preflight_only": args.preflight_only,
        "preflight_holds": preflight_holds,
        "assurance": {"decision": assurance_decision, "hold_reasons": assurance_reasons, "resolution": assurance_resolution},
        "custodial": {"decision": custodial_decision, "hold_reasons": custodial_reasons, "resolution": custodial_resolution},
        "execution_lease": {
            "required": args.execute,
            "valid": lease_ok if args.execute else None,
            "reasons": lease_reasons,
            "summary": lease_summary,
            "tool_scope_enforcement": (
                "lease bounds model/runtime entrypoint and floor plan; this wrapper does not execute external or physical effects. "
                "Side-effectful tools require a downstream tool gate using this receipt plus the same lease."
            ),
        },
        "supervisor_receipt": supervisor_receipt,
        "authority_limit": (
            "This envelope gates model/runtime invocation and may clear an effectful plan for a downstream tool gate. "
            "It does not itself execute provider writes or physical actuation and cannot create semantic authority, risk acceptance, certification, or tool privileges."
        ),
    }
    if args.receipt_json:
        atomic_write(args.receipt_json, receipt)
        receipt["receipt_path"] = str(args.receipt_json)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
