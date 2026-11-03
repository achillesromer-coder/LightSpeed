#!/usr/bin/env python3
"""Read-only Achilles P.A task-packet preparation via the existing CGX/LightSpeed runtime.

Not a second agent, scheduler, inference provider, approval mechanism, DBR writer
or mint. Never writes instruction bodies or private source IDs into the packet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / "cgx" / "domain_templates" / "achilles_owner_operator_profile.json"
RUNTIME_ROOT = REPO_ROOT / "desktop" / "LightSpeed_Runtime"
PROFILE_SCHEMA = "CGX-ACHILLES-OWNER-OPERATOR-PROFILE/0.1"
PACKET_SCHEMA = "CGX-ACHILLES-OWNER-REVIEW-PACKET/0.1"


class ProfileHold(ValueError):
    """Reject missing or conflicting identity, route or privilege contracts."""


def load_profile(path: Path = PROFILE_PATH) -> dict[str, Any]:
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(profile, dict) or profile.get("schema") != PROFILE_SCHEMA:
        raise ProfileHold("ACHILLES_PROFILE_SCHEMA_HOLD")
    if profile.get("selector") != "achilles" or profile.get("status") != "REVIEW_ONLY_UNMINTED":
        raise ProfileHold("ACHILLES_PROFILE_STATE_HOLD")
    identity = profile.get("identity")
    authority = profile.get("authority")
    lifecycle = profile.get("lifecycle")
    if not all(isinstance(section, dict) for section in (identity, authority, lifecycle)):
        raise ProfileHold("ACHILLES_PROFILE_SECTION_SHAPE_HOLD")
    # An altered review profile must not silently suppress standing HOLD gates.
    issues = profile.get("open_issues")
    if (not isinstance(issues, list)
        or any(type(issue) is not int for issue in issues)
        or not {40, 154, 158, 161, 209}.issubset(set(issues))):
        raise ProfileHold("ACHILLES_PROFILE_HOLD_REGISTER_HOLD")
    if not isinstance(identity.get("proposed_profile_name"), str) or not identity["proposed_profile_name"]:
        raise ProfileHold("ACHILLES_PROFILE_NAME_HOLD")
    if (identity.get("agent") != "Achilles"
        or identity.get("canonical_semantic_parent") != "cgx:root:cognigrex"
        or identity.get("principal_domain") != "emassc"):
        raise ProfileHold("ACHILLES_IDENTITY_AUTHORITY_HOLD")
    if (authority.get("agent_can_self_approve") is not False
        or authority.get("automatic_release") is not False
        or authority.get("automatic_merge") is not False
        or authority.get("automatic_rights_grants") is not False
        or authority.get("default_execution_class") != "READ_ONLY"
        or lifecycle.get("stage") != "PRE_MINT_REVIEW"
        or lifecycle.get("evidence_ceiling") != "SOURCE_ONLY"
        or lifecycle.get("active_host_installation") != "UNVERIFIED"
        or lifecycle.get("native_dbr_admission") is not False
        or lifecycle.get("release_authorized") is not False):
        raise ProfileHold("ACHILLES_PRIVILEGE_ESCALATION_HOLD")
    return profile


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _resolve_plan(instruction: str, task_id: str, planner: Callable | None) -> dict[str, Any]:
    """Resolve the existing Neo supervisor, never fabricate live receipts."""
    if planner is None:
        if str(RUNTIME_ROOT) not in sys.path:
            sys.path.insert(0, str(RUNTIME_ROOT))
        try:
            from lightspeed_runtime.cognigrex_supervisor import build_workflow_plan
        except ImportError:
            return {"state": "RUNTIME_NOT_AVAILABLE", "floor_sequence": [], "execution": False}
        planner = build_workflow_plan
    plan = planner(instruction, task_id=task_id)
    payload = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan)
    sequence = payload.get("floor_sequence") or []
    # The existing Neo supervisor only routes through these specialist floors.
    # An unrecognised intermediate floor or repeated gate is not review-safe.
    permitted_specialists = {"Merovingian", "Trinity", "TheConstruct", "Smith", "Oracle", "Architect"}
    if (not isinstance(sequence, (list, tuple)) or len(sequence) < 3
        or sequence[0] != "Neo" or sequence[-1] != "Morpheus"
        or any(not isinstance(floor, str) or floor not in permitted_specialists
               for floor in sequence[1:-1])
        or len(set(sequence)) != len(sequence)):
        raise ProfileHold("ACHILLES_SUPERVISOR_ROUTE_HOLD")
    if payload.get("proof_required") is not True:
        raise ProfileHold("ACHILLES_SUPERVISOR_PROOF_HOLD")
    # A claimed Neo plan without an exact instruction binding is not proof.
    # Only the explicit RUNTIME_NOT_AVAILABLE fallback may omit this digest.
    if payload.get("instruction_sha256") != _hash(instruction):
        raise ProfileHold("ACHILLES_SUPERVISOR_INSTRUCTION_BINDING_HOLD")
    if (payload.get("canonical_promotion_authorized") is not False
        or payload.get("public_publish_authorized") is not False):
        raise ProfileHold("ACHILLES_SELF_PROMOTION_HOLD")
    return {
        "state": "EXISTING_NEO_SUPERVISOR_PLAN",
        "floor_sequence": list(sequence),
        "instruction_sha256": payload.get("instruction_sha256"),
        "execution": False,
    }


def prepare_packet(
    instruction: str,
    task_id: str,
    *,
    project_id: str = "UniSpace",
    private_source_ids: tuple[str, ...] = (),
    profile_path: Path = PROFILE_PATH,
    planner: Callable | None = None,
) -> dict[str, Any]:
    profile = load_profile(profile_path)
    instruction = instruction.strip()
    if not instruction or len(instruction) > 65536:
        raise ProfileHold("ACHILLES_INSTRUCTION_SIZE_HOLD")
    if not task_id or len(task_id) > 128 or any(x in task_id for x in "\r\n\x00"):
        raise ProfileHold("ACHILLES_TASK_ID_HOLD")
    if not project_id or len(project_id) > 128 or any(x in project_id for x in "\r\n\x00"):
        raise ProfileHold("ACHILLES_PROJECT_ID_HOLD")
    if len(private_source_ids) > 100 or not all(isinstance(s, str) for s in private_source_ids):
        raise ProfileHold("ACHILLES_SOURCE_SET_HOLD")
    # Never serialise stable digests of private source identifiers: enumerable
    # identifiers can be recovered by dictionary attack or cross-packet joins.
    # The fingerprint deliberately binds only task/project/instruction/count;
    # a private, authorised consumer MUST independently compare exact source
    # identities and rights before treating this review packet as actionable.
    source_count = len(set(private_source_ids))
    instruction_digest = _hash(instruction)
    fingerprint = _hash(json.dumps(
        [task_id, project_id, instruction_digest, source_count],
        separators=(",", ":"),
    ))
    plan = _resolve_plan(instruction, task_id, planner)
    if plan.get("instruction_sha256") not in (None, instruction_digest):
        raise ProfileHold("ACHILLES_INSTRUCTION_ROUTE_HASH_HOLD")
    return {
        "schema": PACKET_SCHEMA,
        "state": "REVIEW_ONLY_NOT_DISPATCHED",
        "output_classification": "PRIVATE_OWNER_REVIEW_ONLY",
        "public_projection_authorized": False,
        "private_source_set_binding": "NOT_INCLUDED_REQUIRES_PRIVATE_REVALIDATION",
        "profile": profile["identity"]["proposed_profile_name"],
        "selector": "achilles",
        "authority_domain": "emassc",
        "semantic_parent": "cgx:root:cognigrex",
        "Task_ID": task_id,
        "project_id": project_id,
        "idempotency_fingerprint": fingerprint,
        "instruction_sha256": instruction_digest,
        "raw_instruction_persisted": False,
        "private_source_count": source_count,
        "source_admission": "NOT_INFERRED_FROM_IDENTIFIERS_OR_DIGESTS",
        "supervisor": plan,
        "existing_execution_entrypoint": "scripts/run_cgx_agent_runtime.py",
        "execution_request": {
            "agent_id": "Achilles", "domain": "emassc",
            "execution_depth": "inspect", "execution_class": "READ_ONLY",
            "cascade_class": "C0", "execute": False,
            "preflight_only": True,
            "instruction_transfer": "private controlled local file; never public packet",
        },
        "authorization": {
            "owner_decision": "PENDING",
            "private_source_set_approved": False,
            "lease_verified": False,
            "effective_tool_permissions": [],
            "native_dbr_admitted": False,
            "canonical_promotion_authorized": False,
            "external_release_authorized": False,
            "no_self_approval": True,
        },
        "handoff": {
            "operational_owner": "Neo / existing LightSpeed",
            "domain_authority": "existing Grex owner",
            "review_owner": "Achilles / independent owner authority",
            "next": "compare existing GO Task_ID and last receipt before dispatch; do not duplicate",
            "dependency": "current signed lease / host / private ACL / native DBR evidence",
        },
        "open_holds": profile["open_issues"],
        "runtime_host_readback": "NOT_PERFORMED",
        "status_evidence": "source-only proposed composition; no CGX mint or installed agent",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--instruction", help="Avoid for private data; visible in process argument lists")
    source.add_argument("--instruction-file", type=Path, help="Private local file, never copied into packet")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--project-id", default="UniSpace")
    parser.add_argument("--private-source-id", action="append", default=[])
    parser.add_argument("--profile", type=Path, default=PROFILE_PATH)
    parser.add_argument("--output", type=Path, help="Optional review metadata JSON, not raw instruction")
    args = parser.parse_args(argv)
    try:
        instruction = (args.instruction if args.instruction is not None
                       else args.instruction_file.read_text(encoding="utf-8"))
        packet = prepare_packet(instruction, args.task_id,
                                project_id=args.project_id,
                                private_source_ids=tuple(args.private_source_id),
                                profile_path=args.profile)
    except (ProfileHold, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"state": "HOLD", "reason": str(exc)}), file=sys.stderr)
        return 3
    text = json.dumps(packet, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
