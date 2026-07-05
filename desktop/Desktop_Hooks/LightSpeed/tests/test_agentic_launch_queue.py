from __future__ import annotations

from lightspeed_runtime.agentic_launch_queue import apply_active_floor_limit


def test_active_floor_limit_keeps_two_ready_and_queues_the_remainder() -> None:
    tasks = [
        {"task_id": "neo-1", "owner_floor": "Neo", "state": "ready_no_risk_seed"},
        {"task_id": "neo-2", "owner_floor": "Neo", "state": "ready_no_risk_seed"},
        {"task_id": "neo-3", "owner_floor": "Neo", "state": "ready_no_risk_seed"},
        {"task_id": "smith-1", "owner_floor": "Smith", "state": "ready_no_risk_seed"},
    ]

    limited = apply_active_floor_limit(tasks, limit=2)

    assert [item["state"] for item in limited[:3]] == [
        "ready_no_risk_seed",
        "ready_no_risk_seed",
        "backlog_queued",
    ]
    assert limited[2]["prior_state"] == "ready_no_risk_seed"
    assert limited[2]["floor_queue_position"] == 3
    assert limited[3]["state"] == "ready_no_risk_seed"
