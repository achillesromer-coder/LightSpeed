from __future__ import annotations

import json
import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import local_agent_cycle
from lightspeed_runtime.local_agent_wakeup import DEFAULT_FLOOR_ORDER


def write_contract(tmp_path: Path) -> Path:
    shell_root = tmp_path / "shell"
    contract = {
        "contract_id": "cycle-test-contract",
        "root": str(tmp_path),
        "shell_root": str(shell_root),
        "floors": [{"floor": floor} for floor in DEFAULT_FLOOR_ORDER],
    }
    path = tmp_path / "local_agent_wakeup_contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path


def test_cycle_runs_all_eight_floors_once_with_equal_share(tmp_path):
    contract_path = write_contract(tmp_path)
    calls: list[str] = []

    def fake_runner(**kwargs):
        floor = kwargs["floor"]
        calls.append(floor)
        return {
            "receipt_id": f"receipt-{floor}",
            "receipt_path": str(tmp_path / f"{floor}.json"),
            "status": "completed",
            "model": "test-model",
            "resource_preflight": {"execution_state": "pass"},
        }

    receipt = local_agent_cycle.run_cycle(
        contract_path=contract_path,
        dry_run=False,
        runner=fake_runner,
    )

    assert calls == DEFAULT_FLOOR_ORDER
    assert receipt["floor_count"] == 8
    assert receipt["complete_cycle"] is True
    assert receipt["run_rate_percent_per_floor"] == 12.5
    assert sum(row["run_rate_percent"] for row in receipt["floors"]) == 100.0
    assert receipt["counts"] == {"completed": 8}
    assert receipt["max_concurrent_sessions"] == 1
    assert Path(receipt["receipt_path"]).exists()


def test_cycle_rejects_contract_missing_required_floor(tmp_path):
    contract_path = write_contract(tmp_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["floors"] = contract["floors"][:-1]
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    try:
        local_agent_cycle.run_cycle(contract_path=contract_path, runner=lambda **_: {})
    except Exception as exc:
        assert "missing required floors" in str(exc)
    else:
        raise AssertionError("missing floor contract must be rejected")
