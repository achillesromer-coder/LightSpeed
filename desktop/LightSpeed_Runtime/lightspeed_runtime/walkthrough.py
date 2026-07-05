from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from lightspeed_runtime.bridge_health import build_bridge_health, read_bridge_health
from lightspeed_runtime.operator_os import default_operator_os_contract_path
from lightspeed_runtime.storage_paths import finalization_queue_root
from lightspeed_runtime.ui_experience import default_ui_experience_alignment_path
from lightspeed_runtime.ui_polish import default_ui_polish_contract_path
from lightspeed_runtime.web_integration import default_romer_web_integration_path


DEFAULT_WALKTHROUGH_TIME = "2026-04-12T09:00:00+10:00"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_walkthrough_readiness_path(root: Path) -> Path:
    return finalization_queue_root(root) / "walkthrough_readiness.json"


def _exists(path: Path) -> bool:
    try:
        return path.exists()
    except Exception:
        return False


def _gate(gate_id: str, label: str, status: str, owner: str, note: str) -> dict:
    return {
        "gate_id": gate_id,
        "label": label,
        "status": status,
        "owner_floor": owner,
        "note": note,
    }


def build_walkthrough_readiness(
    root: Path,
    *,
    scheduled_local: str = DEFAULT_WALKTHROUGH_TIME,
) -> dict:
    root = Path(root)
    health = read_bridge_health(root) or build_bridge_health(root)
    public = health.get("public_routes") or {}
    data = health.get("dataspace_routes") or {}
    drive = health.get("drive_sources") or {}
    sheets = health.get("spreadsheet_feeds") or {}

    gates = [
        _gate(
            "WT-01",
            "Smart Bento Project Wall contract",
            "pass" if _exists(default_operator_os_contract_path(root)) else "blocked",
            "Trinity",
            "Bento is the primary interface; Holospace remains opt-in.",
        ),
        _gate(
            "WT-02",
            "Original UI to bento translation",
            "pass" if _exists(default_ui_experience_alignment_path(root)) else "blocked",
            "Trinity",
            "Original PDF flow is represented as bento/modals/actions, not blank page sprawl.",
        ),
        _gate(
            "WT-03",
            "Final UI polish contract",
            "pass" if _exists(default_ui_polish_contract_path(root)) else "blocked",
            "Trinity",
            "Shortcuts, theme controls, loading behavior, and page density rules are captured.",
        ),
        _gate(
            "WT-04",
            "Romer website bridge contract",
            "pass" if _exists(default_romer_web_integration_path(root)) else "blocked",
            "Oracle",
            "Website, Drive, and Sheets endpoints are mapped into local floor ownership.",
        ),
        _gate(
            "WT-05",
            "Public route coverage",
            "pass" if public.get("pass_count") == public.get("required_count") else "blocked",
            "Architect",
            f"{public.get('pass_count', 0)}/{public.get('required_count', 0)} public routes are represented as live.",
        ),
        _gate(
            "WT-06",
            "Dataspace endpoint status",
            "warn" if data.get("pending_count", 0) else "pass",
            "Smith",
            f"{data.get('pending_count', 0)} dataspace endpoints need payloads or explicit maintenance stubs before publish.",
        ),
        _gate(
            "WT-07",
            "Drive connector access",
            "warn" if drive.get("pending") else "pass",
            "Oracle",
            f"Pending Drive ids: {', '.join(drive.get('pending') or []) or 'none'}.",
        ),
        _gate(
            "WT-08",
            "Sheets connector access",
            "warn" if sheets.get("pending") else "pass",
            "Oracle",
            f"Pending Sheet ids: {', '.join(sheets.get('pending') or []) or 'none'}.",
        ),
        _gate(
            "WT-09",
            "D-root publish snapshot",
            "hold",
            "Architect",
            "Do not overwrite the D-root snapshot until after human walkthrough approval.",
        ),
    ]

    blocked = [gate for gate in gates if gate["status"] == "blocked"]
    warnings = [gate for gate in gates if gate["status"] == "warn"]
    hold = [gate for gate in gates if gate["status"] == "hold"]
    overall = "blocked" if blocked else "walkthrough_ready_with_warnings" if warnings or hold else "walkthrough_ready"
    pass_count = sum(1 for gate in gates if gate["status"] == "pass")

    return {
        "generated_at": utc_now_iso(),
        "scheduled_local": scheduled_local,
        "owner_floor": "Architect",
        "support_floors": ["Trinity", "Oracle", "Smith", "Neo", "Morpheus", "TheConstruct", "Merovingian"],
        "readiness_path": str(default_walkthrough_readiness_path(root)),
        "overall_status": overall,
        "walkthrough_ready": not blocked,
        "gate_count": len(gates),
        "pass_count": pass_count,
        "warning_count": len(warnings),
        "hold_count": len(hold),
        "blocked_count": len(blocked),
        "bridge_health_status": health.get("overall_status"),
        "bridge_health_percent": health.get("readiness_percent"),
        "gates": gates,
        "run_of_show": [
            "Launch app and confirm loading/status bars do not freeze the shell.",
            "Show Smart Bento Project Wall and bridge health workspace/card.",
            "Open operations routes and explain W6 as public compatibility facade only.",
            "Create/select a project and enter a component set.",
            "Attach an original file through Oracle and preserve source provenance.",
            "Run or demonstrate ingestion output: definitions, strings, tasks, object fragments, datatable rows.",
            "Review/proof extracted content in Morpheus with source_type, confidence_level, and publish_flag visible.",
            "Route approved items through Smith/Z Direct and confirm queue states.",
            "Open TheConstruct map/simulation context and save an ephemeris-style output artifact.",
            "Show Architect publish gate and confirm D-root snapshot stays held until approval.",
        ],
        "walkthrough_notes": [
            "Warnings are acceptable for the first walkthrough if they are visible and do not crash the app.",
            "Do not claim the second Drive folder or desktop population Sheet are connected until permissions are granted.",
            "Do not package V0.10.0 until smoke, verify, tests, and human approval are complete after the walkthrough.",
        ],
    }


def read_walkthrough_readiness(root: Path, output_path: Path | None = None) -> dict:
    path = output_path or default_walkthrough_readiness_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_walkthrough_readiness(
    root: Path,
    output_path: Path | None = None,
    *,
    scheduled_local: str = DEFAULT_WALKTHROUGH_TIME,
) -> dict:
    destination = output_path or default_walkthrough_readiness_path(root)
    payload = build_walkthrough_readiness(root, scheduled_local=scheduled_local)
    payload["readiness_path"] = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
