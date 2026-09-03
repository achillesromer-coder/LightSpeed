from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Callable

from lightspeed_runtime.local_agent_wakeup import DEFAULT_FLOOR_ORDER
from lightspeed_runtime.local_floor_runner import (
    DEFAULT_CONTRACT_PATH,
    LocalFloorRunnerError,
    load_contract,
    resolve_contract_shell_root,
    run_floor,
)

RUN_RATE_PERCENT = 100.0 / len(DEFAULT_FLOOR_ORDER)
CycleRunner = Callable[..., dict[str, Any]]


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def cycle_receipt_path(contract: dict[str, Any]) -> Path:
    return (
        resolve_contract_shell_root(contract)
        / "Z Axis"
        / "Z+2_Neo"
        / "data"
        / "temp_shells"
        / "outputs"
        / "local_agent_cycle_receipt_latest.json"
    )


def run_cycle(
    *,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    dry_run: bool = True,
    allow_heavy: bool = False,
    receipt_target: str = "neo",
    stop_on_failure: bool = False,
    runner: CycleRunner = run_floor,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    available = {
        str(item.get("floor"))
        for item in contract.get("floors") or []
        if isinstance(item, dict) and item.get("floor")
    }
    missing = [floor for floor in DEFAULT_FLOOR_ORDER if floor not in available]
    if missing:
        raise LocalFloorRunnerError(
            "cycle contract is missing required floors: " + ", ".join(missing)
        )

    rows: list[dict[str, Any]] = []
    for sequence, floor in enumerate(DEFAULT_FLOOR_ORDER, start=1):
        receipt = runner(
            contract_path=contract_path,
            floor=floor,
            dry_run=dry_run,
            allow_heavy=allow_heavy,
            receipt_target=receipt_target,
        )
        row = {
            "sequence": sequence,
            "floor": floor,
            "run_rate_percent": RUN_RATE_PERCENT,
            "status": receipt.get("status"),
            "receipt_id": receipt.get("receipt_id"),
            "receipt_path": receipt.get("receipt_path"),
            "model": receipt.get("model"),
            "resource_state": (receipt.get("resource_preflight") or {}).get("execution_state"),
        }
        rows.append(row)
        if stop_on_failure and receipt.get("status") == "failed":
            break

    counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1

    cycle = {
        "schema_version": "lightspeed-local-agent-cycle-v1",
        "receipt_id": f"local_agent_cycle_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        "created_at": _utc_now_iso(),
        "contract_id": contract.get("contract_id"),
        "contract_path": str(contract_path),
        "scheduler_mode": "sequential_equal_share",
        "max_concurrent_sessions": 1,
        "floor_count": len(DEFAULT_FLOOR_ORDER),
        "run_rate_percent_per_floor": RUN_RATE_PERCENT,
        "requested_execution": not dry_run,
        "allow_heavy": allow_heavy,
        "stop_on_failure": stop_on_failure,
        "counts": counts,
        "floors": rows,
        "complete_cycle": len(rows) == len(DEFAULT_FLOOR_ORDER),
        "public_publish_authorized": False,
    }
    path = cycle_receipt_path(contract)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cycle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cycle["receipt_path"] = str(path)
    return cycle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one bounded LightSpeed eight-floor cycle with an equal 12.5% scheduler share per floor."
    )
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--execute", action="store_true", help="Call the configured local model instead of dry-run receipts.")
    parser.add_argument("--allow-heavy", action="store_true", help="Allow explicit heavy/manual floor models for this cycle.")
    parser.add_argument("--receipt-target", choices=["neo", "floor"], default="neo")
    parser.add_argument("--stop-on-failure", action="store_true")
    args = parser.parse_args()

    receipt = run_cycle(
        contract_path=args.contract,
        dry_run=not args.execute,
        allow_heavy=args.allow_heavy,
        receipt_target=args.receipt_target,
        stop_on_failure=args.stop_on_failure,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt.get("complete_cycle") else 1


if __name__ == "__main__":
    raise SystemExit(main())
