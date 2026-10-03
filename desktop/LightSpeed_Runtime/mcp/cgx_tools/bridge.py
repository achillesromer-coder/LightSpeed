from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
RUNTIME_ROOT = HERE.parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.bridge_health import build_bridge_health
from lightspeed_runtime.cgx_capability_registry import capability_summary, resolve_shortcall
from lightspeed_runtime.cgx_cross_analysis import build_cross_analysis_plan
from lightspeed_runtime.cgx_extension_planner import plan_tool_extension
from lightspeed_runtime.cgx_object_context import resolve_object_context
from lightspeed_runtime.cgx_preflight import build_consequence_preflight
from lightspeed_runtime.cognigrex_supervisor import run_supervised_workflow
from lightspeed_runtime.freecad_adapter import (
    extract_freecad_bom,
    inspect_freecad_document,
    probe_freecad,
)
from lightspeed_runtime.result_receipt_browser import list_result_receipts, open_result_receipt
from lightspeed_runtime.simulation_capability_probe import probe_femm, probe_gmat, probe_mpl

CORE_ROOT = Path(os.environ.get("LIGHTSPEED_CORE_ROOT", r"D:\LightSpeed\Core"))
SHELL_ROOT = Path(os.environ.get(
    "LIGHTSPEED_SHELL_ROOT",
    r"D:\LightSpeed\App\Z Axis\Z+2_Neo\data\temp_shells",
))
CONTRACT_PATH = Path(os.environ.get(
    "LIGHTSPEED_WAKEUP_CONTRACT",
    r"D:\LightSpeed\Core\exports\agent_home\local_agent_wakeup_contract.json",
))


class BridgeInputError(ValueError):
    pass


def _obj(value: Any, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise BridgeInputError(f"{name} must be an object")
    return value


def _strings(value: Any, name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise BridgeInputError(f"{name} must be an array of strings")
    return value


def _required_str(args: dict[str, Any], name: str) -> str:
    value = args.get(name)
    if not isinstance(value, str) or not value.strip():
        raise BridgeInputError(f"{name} must be a non-empty string")
    return value.strip()


def dispatch(operation: str, args: dict[str, Any]) -> dict[str, Any]:
    if operation == "capabilities":
        return capability_summary(_required_str(args, "selector"))
    if operation == "resolve_shortcall":
        return resolve_shortcall(
            _required_str(args, "selector"),
            _required_str(args, "shortcall"),
        )

    if operation == "object_context":
        return resolve_object_context(
            _required_str(args, "query"),
            domain=args.get("domain"),
        )

    if operation == "cross_analysis":
        return build_cross_analysis_plan(
            _required_str(args, "selector"),
            _required_str(args, "question"),
            intent_payload=_obj(args.get("intent_payload"), "intent_payload") or None,
            evidence=args.get("evidence") or (),
            domain_override=args.get("domain_override"),
            execution_depth=str(args.get("execution_depth") or "inspect"),
            reasoning_depth=str(args.get("reasoning_depth") or "standard"),
            cascade_class=str(args.get("cascade_class") or "C0"),
            tags=_strings(args.get("tags"), "tags"),
            allow_heavy=False,
        )

    if operation == "preflight":
        return build_consequence_preflight(
            _required_str(args, "domain"),
            _required_str(args, "execution_depth"),
            reasoning_depth=str(args.get("reasoning_depth") or "standard"),
            cascade_class=str(args.get("cascade_class") or "C0"),
            tags=_strings(args.get("tags"), "tags"),
            assurance_assessment=_obj(
                args.get("assurance_assessment"), "assurance_assessment"
            ) or None,
            custodial_assessment=_obj(
                args.get("custodial_assessment"), "custodial_assessment"
            ) or None,
        )

    if operation == "tool_plan":
        return plan_tool_extension(
            _required_str(args, "selector"),
            _required_str(args, "goal"),
            desired_kind=str(args.get("desired_kind") or "auto"),
            requested_shortcall=args.get("requested_shortcall"),
            required_capabilities=_strings(
                args.get("required_capabilities"), "required_capabilities"
            ),
        )

    if operation == "gmat_probe":
        return probe_gmat()
    if operation == "femm_probe":
        return probe_femm()
    if operation == "mpl_probe":
        return probe_mpl()

    if operation == "freecad_probe":
        return probe_freecad()
    if operation == "freecad_inspect":
        return inspect_freecad_document(_required_str(args, "path"))

    if operation == "freecad_bom":
        return extract_freecad_bom(_required_str(args, "path"))

    if operation == "health":
        return build_bridge_health(CORE_ROOT)

    if operation == "receipts_list":
        limit = min(max(int(args.get("limit", 50)), 1), 100)
        return list_result_receipts(SHELL_ROOT, limit=limit)

    if operation == "receipt_open":
        return open_result_receipt(
            SHELL_ROOT,
            result_id=_required_str(args, "result_id"),
        )

    if operation in {"local_plan", "local_run"}:
        confirmed = args.get("confirmed") is True
        if operation == "local_run" and not confirmed:
            raise BridgeInputError("local_run requires confirmed=true")
        return run_supervised_workflow(
            _required_str(args, "instruction"),
            contract_path=CONTRACT_PATH,
            task_id=args.get("task_id"),
            project_id=args.get("project_id"),
            dry_run=(operation == "local_plan"),
            allow_heavy=False,
            receipt_target=str(args.get("receipt_target") or "neo"),
            stop_on_failure=True,
            persist_learning=True,
        )

    raise BridgeInputError(f"unsupported operation: {operation}")


def main() -> int:
    raw = sys.stdin.read()
    request = json.loads(raw or "{}")
    if not isinstance(request, dict):
        raise BridgeInputError("request must be an object")
    operation = _required_str(request, "operation")
    args = _obj(request.get("args"), "args")
    result = dispatch(operation, args)
    sys.stdout.write(json.dumps({"ok": True, "result": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        payload = {
            "ok": False,
            "error": type(exc).__name__,
            "message": str(exc),
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False))
        raise SystemExit(2)
