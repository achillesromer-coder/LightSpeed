from __future__ import annotations

import json
import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime import cognigrex_supervisor
from lightspeed_runtime.local_agent_wakeup import DEFAULT_FLOOR_ORDER


def write_contract(tmp_path: Path) -> Path:
    shell_root = tmp_path / "shell"
    floors = []
    for index, floor in enumerate(DEFAULT_FLOOR_ORDER, start=1):
        floors.append(
            {
                "floor": floor,
                "order": index,
                "floor_root": str(shell_root / "Z Axis" / floor),
                "activation": {"mode": "staged"},
                "ollama_connection": {
                    "endpoint": "http://localhost:11434",
                    "model": "test-model",
                },
                "training_context": {
                    "wake_goal": f"Wake {floor}",
                    "assimilation_role": f"Role {floor}",
                },
                "assimilation_draw": {"priority_paths": []},
            }
        )
    contract = {
        "contract_id": "supervisor-test-contract",
        "root": str(tmp_path),
        "shell_root": str(shell_root),
        "policy": {"receipt_prompt_overrides": {"num_predict": 64}},
        "ollama": {"endpoint": "http://localhost:11434"},
        "floors": floors,
    }
    path = tmp_path / "local_agent_wakeup_contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path


def test_plan_keeps_neo_as_head_and_routes_specialists_then_morpheus():
    plan = cognigrex_supervisor.build_workflow_plan(
        "Reconcile source evidence, improve the OS UI, build a CAD mesh and verify provenance.",
        task_id="TASK-TEST",
    )

    assert plan.floor_sequence[0] == "Neo"
    assert "Oracle" in plan.floor_sequence
    assert "Trinity" in plan.floor_sequence
    assert "TheConstruct" in plan.floor_sequence
    assert plan.floor_sequence[-1] == "Morpheus"
    assert plan.canonical_promotion_authorized is False
    assert plan.public_publish_authorized is False


def test_default_unclassified_work_routes_to_architect_under_neo():
    plan = cognigrex_supervisor.build_workflow_plan(
        "Coordinate this bounded new matter"
    )
    assert plan.primary_floors == ("Architect",)
    assert plan.floor_sequence == ("Neo", "Architect", "Morpheus")


def test_supervised_dry_run_keeps_raw_text_out_of_aggregate_and_learning(tmp_path):
    contract_path = write_contract(tmp_path)
    instruction = "Inspect private runtime health and reconcile the UI evidence route."
    seen_contracts: list[dict] = []

    def fake_runner(**kwargs):
        overlay = json.loads(
            Path(kwargs["contract_path"]).read_text(encoding="utf-8")
        )
        seen_contracts.append(overlay)
        floor = kwargs["floor"]
        return {
            "receipt_id": f"receipt-{floor}",
            "receipt_path": str(tmp_path / f"{floor}.json"),
            "status": "dry_run",
            "model": "test-model",
            "resource_preflight": {"execution_state": "pass"},
        }

    receipt = cognigrex_supervisor.run_supervised_workflow(
        instruction,
        contract_path=contract_path,
        task_id="TASK-PRIVATE",
        project_id="PROJECT-1",
        dry_run=True,
        runner=fake_runner,
    )

    assert receipt["operational_head"] == "Neo"
    assert receipt["canonical_release_gate"] == "Achilles"
    assert receipt["raw_instruction_persisted_in_aggregate"] is False
    assert receipt["floor_receipt_prompt_preview_may_include_task_text"] is True
    assert receipt["learning_state_raw_instruction_persisted"] is False
    assert receipt["requested_execution"] is False
    assert receipt["complete_workflow"] is True
    assert receipt["de_sporte_content_ingest_authorized"] is False
    assert receipt["instruction_sha256"] == cognigrex_supervisor.instruction_hash(
        instruction
    )
    assert instruction not in Path(receipt["receipt_path"]).read_text(
        encoding="utf-8"
    )
    assert instruction not in Path(receipt["learning_state_path"]).read_text(
        encoding="utf-8"
    )
    assert seen_contracts
    assert instruction in json.dumps(seen_contracts[0])
    overlay_meta = seen_contracts[0]["cognigrex_supervisor"]
    assert overlay_meta["overlay_ephemeral"] is True
    assert overlay_meta["floor_receipt_prompt_preview_may_include_task_text"] is True

    learning = json.loads(
        Path(receipt["learning_state_path"]).read_text(encoding="utf-8")
    )
    assert learning["dry_run_observations"] == 1
    assert learning["executed_observations"] == 0
    assert learning["policy"]["adaptive_routing_mode"] == "advisory_only"
    assert learning["policy"]["raw_instruction_persisted"] is False


def test_completed_execution_updates_private_advisory_learning(tmp_path):
    contract_path = write_contract(tmp_path)

    def fake_runner(**kwargs):
        floor = kwargs["floor"]
        return {
            "receipt_id": f"receipt-{floor}",
            "receipt_path": str(tmp_path / f"{floor}.json"),
            "status": "completed",
            "model": "test-model",
            "elapsed_ms": 10,
            "resource_preflight": {"execution_state": "pass"},
        }

    receipt = cognigrex_supervisor.run_supervised_workflow(
        "Build and test a bounded code artifact, then verify the result.",
        contract_path=contract_path,
        task_id="TASK-EXEC",
        dry_run=False,
        runner=fake_runner,
    )
    learning = json.loads(
        Path(receipt["learning_state_path"]).read_text(encoding="utf-8")
    )

    assert learning["executed_observations"] == 1
    assert learning["dry_run_observations"] == 0
    assert learning["floors"]["Neo"]["executed_count"] == 1
    assert learning["floors"]["Neo"]["ewma_completion"] == 1.0
    assert learning["floors"]["Smith"]["completed_count"] == 1
    assert learning["floors"]["Morpheus"]["last_status"] == "completed"


def test_missing_required_floor_is_rejected_before_execution(tmp_path):
    contract_path = write_contract(tmp_path)
    payload = json.loads(contract_path.read_text(encoding="utf-8"))
    payload["floors"] = [
        row for row in payload["floors"] if row["floor"] != "Morpheus"
    ]
    contract_path.write_text(json.dumps(payload), encoding="utf-8")

    try:
        cognigrex_supervisor.run_supervised_workflow(
            "Build a code artifact",
            contract_path=contract_path,
            runner=lambda **_: {},
        )
    except Exception as exc:
        assert "missing required floor" in str(exc).lower()
    else:
        raise AssertionError("missing Morpheus proof floor must block the workflow")
