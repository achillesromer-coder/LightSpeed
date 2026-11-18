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



def test_uncertain_cycle_stops_even_when_continue_requested(tmp_path):
    calls=[]
    def runner(**kw):
        calls.append(kw["floor"])
        return {"receipt_id":"fixture","status":"failed","server_outcome_uncertain":True}
    receipt=local_agent_cycle.run_cycle(contract_path=write_contract(tmp_path),dry_run=False,
        stop_on_failure=False,runner=runner)
    assert len(calls)==1 and not receipt["complete_cycle"] and receipt["server_outcome_uncertain"]



def test_cycle_forwards_exact_shared_admission(tmp_path):
    import pytest
    from lightspeed_runtime.local_floor_runner import CommonInferenceSession,LocalFloorRunnerError
    path=write_contract(tmp_path)
    contract=json.loads(path.read_text(encoding="utf-8"))
    contract["policy"]={"require_common_inference_session":True}
    path.write_text(json.dumps(contract),encoding="utf-8")
    gate=CommonInferenceSession(tmp_path/"common.lock",task_id="fixture",scope_revision="r1",
        authorise=lambda *a:True,resources_ready=lambda:True)
    calls=[]
    def runner(**kw):
        assert kw["common_session"] is gate
        with gate:gate.check_before_request()
        calls.append(kw["floor"])
        return {"receipt_id":"id-"+kw["floor"],"status":"completed"}
    def run(task="fixture",session=None):
        return local_agent_cycle.run_cycle(contract_path=path,task_id=task,dry_run=False,runner=runner,common_session=session)
    with pytest.raises(LocalFloorRunnerError):run()
    with pytest.raises(LocalFloorRunnerError):run("other",gate)
    assert calls==[]
    assert run(session=gate)["complete_cycle"] and len(calls)==8
