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
        "Open Selected Floor",
        "Ask Achilles",
        "Open GO Review",
        "Open Agent Queue",
        "GO: local review surface http://127.0.0.1:4173",
        "external Web deferred",
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


def test_functions_hub_routes_home_to_the_compact_operator_surface() -> None:
    source = N_PY.read_text(encoding="utf-8")

    assert "self.show_floors_hub()" in source
    assert "self.bind('<Control-h>', lambda e: self.show_home()" in source
