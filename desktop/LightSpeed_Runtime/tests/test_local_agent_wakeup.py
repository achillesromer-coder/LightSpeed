from __future__ import annotations

import json
from pathlib import Path
import sys

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.local_agent_wakeup import (
    build_assimilation_source_inventory,
    build_local_agent_wakeup_contract,
    default_shell_root,
    write_local_agent_wakeup_outputs,
)


def test_local_agent_wakeup_contract_routes_source_files_to_floor_packets(tmp_path: Path) -> None:
    source_root = tmp_path / "To be assimilated"
    source_root.mkdir()
    (source_root / "LightSpeed UI.pdf").write_bytes(b"%PDF-1.4")
    (source_root / "SYSTEM_ARCHITECTURE_FLOWCHART.md").write_text("# Architecture", encoding="utf-8")
    (source_root / "Ollama Responder.py").write_text("print('ok')", encoding="utf-8")

    shell_root = tmp_path / "Desktop_Hooks" / "LightSpeed"
    (shell_root / "config").mkdir(parents=True)

    contract = build_local_agent_wakeup_contract(
        tmp_path / "LightSpeed_Runtime",
        source_root=source_root,
        shell_root=shell_root,
        neo_local_runtime={
            "endpoint_policy": {"base_url": "http://localhost:11434"},
            "available_models": ["qwen3:8b", "deepseek-r1:8b", "gemma3:27b"],
        },
        realization_contract={"floors": []},
        probe_ollama=False,
    )

    assert contract["summary"]["floor_count"] == 8
    assert contract["summary"]["ollama_enabled_floor_count"] == 8
    assert contract["summary"]["source_file_sample_count"] == 3
    assert contract["summary"]["chat_ready_floor_count"] == 8
    assert contract["buildout_phase"]["state"] == "active_packet_first_local_llm_gated"
    assert contract["buildout_phase"]["stages"][0]["stage_id"] == "traditional_context_training"
    by_floor = {item["floor"]: item for item in contract["floors"]}
    assert any("LightSpeed UI.pdf" in item["relative_path"] for item in by_floor["Trinity"]["assimilation_draw"]["priority_paths"])
    assert any("Ollama Responder.py" in item["relative_path"] for item in by_floor["Neo"]["assimilation_draw"]["priority_paths"])
    assert by_floor["Neo"]["ai_chat_enablement"]["entry_surface"].startswith("Functions Hub")
    assert contract["ui_simplification"]["entry_surface"] == "N.py -> Functions Hub"


def test_write_local_agent_wakeup_outputs_creates_contract_and_packets(tmp_path: Path) -> None:
    source_root = tmp_path / "To be assimilated"
    source_root.mkdir()
    (source_root / "COMPLETE_IMPLEMENTATION_GUIDE.md").write_text("# Guide", encoding="utf-8")

    root = tmp_path / "LightSpeed_Runtime"
    shell_root = tmp_path / "Desktop_Hooks" / "LightSpeed"
    (shell_root / "config").mkdir(parents=True)

    result = write_local_agent_wakeup_outputs(
        root,
        source_root=source_root,
        shell_root=shell_root,
        max_scan_entries=50,
    )

    assert Path(result["export_path"]).exists()
    assert Path(result["shell_mirror_path"]).exists()
    assert Path(result["neo_active_task_path"]).exists()
    assert Path(result["oracle_intake_manifest_path"]).exists()
    assert Path(result["operator_report_path"]).exists()
    assert Path(result["buildout_handoff_paths"]["trinity_shell"]).exists()
    assert Path(result["buildout_handoff_paths"]["neo_handoff"]).exists()
    assert Path(result["buildout_handoff_paths"]["smith_queue"]).exists()
    assert Path(result["packet_paths"]["Architect"]).exists()


def test_assimilation_source_inventory_is_bounded(tmp_path: Path) -> None:
    source_root = tmp_path / "To be assimilated"
    source_root.mkdir()
    for index in range(10):
        (source_root / f"file_{index}.md").write_text("x", encoding="utf-8")

    inventory = build_assimilation_source_inventory(source_root, max_entries=5)

    assert inventory["exists"] is True
    assert inventory["scan_truncated"] is True
    assert inventory["sampled_file_count"] <= 5


def test_default_shell_root_uses_agent_home_operator_authority(tmp_path: Path) -> None:
    root = tmp_path / "LightSpeed" / "Core"
    canonical_app = tmp_path / "LightSpeed" / "App"
    config_path = root / "config" / "agent_home.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps({"environment": {"desktop_shell_root": str(canonical_app)}}),
        encoding="utf-8",
    )

    assert default_shell_root(root) == canonical_app

    contract = build_local_agent_wakeup_contract(
        root,
        source_root=tmp_path / "missing-source",
        realization_contract={"floors": []},
        neo_local_runtime={"available_models": ["qwen3:8b"]},
        probe_ollama=False,
    )

    assert Path(contract["shell_root"]) == canonical_app
    assert all(Path(item["floor_root"]).is_relative_to(canonical_app) for item in contract["floors"])
