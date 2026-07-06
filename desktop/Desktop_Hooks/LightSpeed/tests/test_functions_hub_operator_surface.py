from pathlib import Path


N_PY = Path(__file__).resolve().parents[1] / "N.py"


def test_functions_hub_exposes_operator_home_contract() -> None:
    source = N_PY.read_text(encoding="utf-8")

    required_surface_text = [
        "Functions Hub Home",
        "Operator Surface",
        "Active floor:",
        "Ollama:",
        "Buildout:",
        "Stage:",
        "Open Backend Workspace",
        "Open Wake Packet",
        "Open Buildout Handoff",
        "Open Agent Queue",
        "Open Web/GO Bridge",
        "Open Neo Receipt / Smith Queue",
        "WEB/GO:",
        "web_drive_bridge",
        "web_drive_bridge.json",
        "agentic_launch_queue",
        "buildout_phase_queue.json",
        "smart_floor_artifacts",
        "*receipt*.json",
    ]

    for text in required_surface_text:
        assert text in source


def test_functions_hub_keeps_backend_workspace_lazy() -> None:
    source = N_PY.read_text(encoding="utf-8")

    assert "Backend workspace is not mounted unless explicitly opened." not in source
    assert "command=lambda: _mount_floor(selected_floor[\"name\"])" in source
    assert "_workspace_placeholder(selected_floor[\"name\"])" in source
