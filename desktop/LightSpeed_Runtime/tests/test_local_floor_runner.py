from __future__ import annotations

import json
from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.local_floor_runner import (
    _canonical_loopback_endpoint,
    LocalFloorRunnerError,
    build_ollama_request,
    build_resource_preflight,
    run_floor,
    select_floor,
)


def _contract(tmp_path: Path) -> Path:
    root = tmp_path / "LightSpeed_Runtime"
    shell_root = tmp_path / "Desktop_Hooks" / "LightSpeed"
    contract = {
        "contract_id": "test_contract",
        "root": str(root),
        "shell_root": str(shell_root),
        "source_root": str(tmp_path / "To be assimilated"),
        "policy": {
            "max_concurrent_ollama_sessions": 1,
            "load_models_concurrently": False,
            "heavy_models_manual_only": True,
            "receipt_prompt_overrides": {"stream": False, "think": False, "num_predict": 512},
        },
        "ollama": {"endpoint": "http://localhost:11434"},
        "floors": [
            _floor(shell_root, "Neo", 3, "resident", "qwen3:8b", "resident_or_short_hot_path"),
            _floor(shell_root, "Oracle", 5, "staged", "deepseek-r1:8b", "on_demand_short"),
            _floor(shell_root, "TheConstruct", 8, "manual_heavy", "gemma3:27b", "manual_heavy_short"),
        ],
    }
    path = root / "exports" / "agent_home" / "local_agent_wakeup_contract.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path


def _floor(shell_root: Path, name: str, order: int, mode: str, model: str, load_policy: str) -> dict[str, object]:
    floor_root = shell_root / "Z Axis" / f"Z-{order}_{name}"
    return {
        "floor": name,
        "order": order,
        "floor_root": str(floor_root),
        "packet_path": str(floor_root / "data" / "wakeup" / "floor_wakeup_packet.json"),
        "activation": {"mode": mode},
        "ollama_connection": {
            "endpoint": "http://localhost:11434",
            "model": model,
            "enabled": True,
            "load_policy": load_policy,
            "api_overrides": {"stream": True, "think": True, "num_predict": 4096},
        },
        "training_context": {
            "wake_goal": f"Wake {name}",
            "assimilation_role": f"Route {name}",
            "learning_sequence": ["read packet", "return receipt"],
            "do_not_do": ["do not recurse"],
        },
        "assimilation_draw": {"priority_paths": [{"relative_path": f"{name}.md"}]},
    }


def test_select_floor_requires_one_selector(tmp_path: Path) -> None:
    contract_path = _contract(tmp_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert select_floor(contract, floor="neo").floor["floor"] == "Neo"
    assert select_floor(contract, order=5).floor["floor"] == "Oracle"

    try:
        select_floor(contract)
    except LocalFloorRunnerError as exc:
        assert "select exactly one floor" in str(exc)
    else:
        raise AssertionError("missing selector should fail")


def test_dry_run_writes_neo_receipt_without_http(tmp_path: Path) -> None:
    contract_path = _contract(tmp_path)

    def fail_http(_url: str, _payload: dict[str, object], _timeout: float) -> dict[str, object]:
        raise AssertionError("dry-run must not call Ollama")

    receipt = run_floor(contract_path=contract_path, floor="Neo", http_post=fail_http)

    receipt_path = Path(receipt["receipt_path"])
    assert receipt["status"] == "dry_run"
    assert receipt["dry_run"] is True
    assert receipt["request_overrides"] == {"stream": False, "think": False, "num_predict": 512}
    assert "Z+2_Neo" in str(receipt_path)
    assert receipt_path.exists()


def test_request_overrides_force_safe_values_and_bound_num_predict(tmp_path: Path) -> None:
    contract_path = _contract(tmp_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    floor = select_floor(contract, floor="Neo").floor

    request = build_ollama_request(contract, floor, num_predict=10_000)

    assert request["stream"] is False
    assert request["think"] is False
    assert request["options"]["num_predict"] == 1024


def test_manual_heavy_floor_is_blocked_without_allow_flag(tmp_path: Path) -> None:
    contract_path = _contract(tmp_path)

    def fail_http(_url: str, _payload: dict[str, object], _timeout: float) -> dict[str, object]:
        raise AssertionError("blocked heavy run must not call Ollama")

    receipt = run_floor(contract_path=contract_path, floor="TheConstruct", dry_run=False, http_post=fail_http)

    assert receipt["status"] == "blocked"
    assert "manual/heavy" in receipt["blocked_reason"]
    assert Path(receipt["receipt_path"]).exists()


def test_execute_uses_mocked_http_and_writes_floor_receipt(tmp_path: Path) -> None:
    contract_path = _contract(tmp_path)
    calls: list[tuple[str, dict[str, object], float]] = []

    def fake_http(url: str, payload: dict[str, object], timeout: float) -> dict[str, object]:
        calls.append((url, payload, timeout))
        return {"response": "{\"floor_summary\":\"ok\"}", "done": True}

    receipt = run_floor(
        contract_path=contract_path,
        floor="TheConstruct",
        dry_run=False,
        allow_heavy=True,
        receipt_target="floor",
        http_post=fake_http,
        ollama_status_probe=lambda _endpoint, _timeout: {
            "state": "available",
            "loaded_model_count": 1,
            "loaded_models": [{"name": "gemma3:27b"}],
        },
        memory_snapshot=lambda: (32 * 1024**3, 16 * 1024**3),
        lock=False,
    )

    assert receipt["status"] == "completed"
    assert len(calls) == 1
    assert calls[0][0] == "http://127.0.0.1:11434/api/generate"
    assert calls[0][1]["model"] == "gemma3:27b"
    assert calls[0][1]["stream"] is False
    assert calls[0][1]["think"] is False
    assert Path(receipt["receipt_path"]).exists()
    assert "TheConstruct" in str(receipt["receipt_path"])
    assert receipt["resource_preflight"]["execution_state"] == "ready"
    assert receipt["resource_preflight"]["ollama"]["loaded_model_count"] == 1


def test_resource_preflight_is_bounded_and_reports_last_receipt(tmp_path: Path) -> None:
    contract_path = _contract(tmp_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    ledger = Path(contract["root"]) / "logs" / "receipts" / "local_floor_runner_2026_W33.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(
        json.dumps(
            {
                "receipt_id": "prior-receipt",
                "created_at": "2026-08-15T01:00:00+00:00",
                "floor": "Neo",
                "status": "completed",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    status = build_resource_preflight(
        contract,
        endpoint="http://localhost:11434",
        probe_ollama=True,
        memory_snapshot=lambda: (32 * 1024**3, 8 * 1024**3),
        ollama_status_probe=lambda endpoint, timeout: {
            "state": "available",
            "loaded_model_count": 1,
            "loaded_models": [{"name": "qwen3:8b"}],
            "endpoint": endpoint,
            "timeout": timeout,
        },
    )

    assert status["execution_state"] == "ready"
    assert status["memory"]["free_percent"] == 25.0
    assert status["thresholds"]["minimum_free_memory_bytes"] == 4 * 1024**3
    assert status["ollama"]["loaded_models"][0]["name"] == "qwen3:8b"
    assert status["last_receipt"]["receipt_id"] == "prior-receipt"


def test_execute_stops_before_ollama_when_memory_is_critical(tmp_path: Path) -> None:
    contract_path = _contract(tmp_path)

    def fail_http(_url: str, _payload: dict[str, object], _timeout: float) -> dict[str, object]:
        raise AssertionError("resource-held run must not call Ollama generate")

    def fail_probe(_endpoint: str, _timeout: float) -> dict[str, object]:
        raise AssertionError("resource-held run must not probe Ollama")

    receipt = run_floor(
        contract_path=contract_path,
        floor="Neo",
        dry_run=False,
        http_post=fail_http,
        ollama_status_probe=fail_probe,
        memory_snapshot=lambda: (32 * 1024**3, 3 * 1024**3),
        lock=False,
    )

    assert receipt["status"] == "blocked"
    assert "resource stop threshold reached" in receipt["blocked_reason"]
    assert "below 4294967296 bytes" in receipt["blocked_reason"]
    assert receipt["resource_preflight"]["execution_state"] == "stop"
    assert receipt["resource_preflight"]["memory"]["state"] == "stop"
    assert receipt["resource_preflight"]["ollama"]["reason"] == "resource_stop"


def test_dry_run_records_memory_without_probing_ollama(tmp_path: Path) -> None:
    contract_path = _contract(tmp_path)

    def fail_probe(_endpoint: str, _timeout: float) -> dict[str, object]:
        raise AssertionError("dry-run must not probe Ollama")

    receipt = run_floor(
        contract_path=contract_path,
        floor="Neo",
        ollama_status_probe=fail_probe,
        memory_snapshot=lambda: (32 * 1024**3, 16 * 1024**3),
    )

    assert receipt["status"] == "dry_run"
    assert receipt["resource_preflight"]["memory"]["free_percent"] == 50.0
    assert receipt["resource_preflight"]["ollama"]["state"] == "not_probed"


def test_stale_exported_shell_route_is_overridden_by_agent_home_authority(tmp_path: Path) -> None:
    contract_path = _contract(tmp_path)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    root = tmp_path / "LightSpeed" / "Core"
    stale_shell = tmp_path / "LightSpeed" / "Desktop_Hooks" / "LightSpeed"
    canonical_app = tmp_path / "LightSpeed" / "App"
    contract["root"] = str(root)
    contract["shell_root"] = str(stale_shell)
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    agent_home_path = root / "config" / "agent_home.json"
    agent_home_path.parent.mkdir(parents=True)
    agent_home_path.write_text(
        json.dumps({"environment": {"desktop_shell_root": str(canonical_app)}}),
        encoding="utf-8",
    )

    receipt = run_floor(
        contract_path=contract_path,
        floor="Neo",
        memory_snapshot=lambda: (32 * 1024**3, 16 * 1024**3),
    )

    receipt_path = Path(receipt["receipt_path"])
    assert receipt_path.is_relative_to(canonical_app)
    assert receipt_path.exists()
    assert not (stale_shell / "Z Axis" / "Z+2_Neo" / "data" / "temp_shells" / "outputs" / receipt_path.name).exists()


def test_canonical_loopback_endpoint_preserves_remote_hosts() -> None:
    assert (
        _canonical_loopback_endpoint("http://localhost:11434")
        == "http://127.0.0.1:11434"
    )
    assert (
        _canonical_loopback_endpoint("https://models.example:11434")
        == "https://models.example:11434"
    )
