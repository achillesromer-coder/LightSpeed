from __future__ import annotations

from pathlib import Path

from lightspeed_runtime.operator_home import _write_shell_artifacts


def test_held_corunner_does_not_receive_a_handoff(tmp_path: Path) -> None:
    shell_root = tmp_path / "LightSpeed"
    shell_root.mkdir()
    handoff_path = tmp_path / "DeSporte" / "lightspeed_launch_handoff.json"
    payload = {
        "generated_at": "2026-07-06T00:00:00+00:00",
        "environment": {
            "paths": {
                "desktop_shell_root": {
                    "path": str(shell_root),
                }
            }
        },
        "launch_control": {
            "co_runner": {
                "state": "held_until_lightspeed_stable",
                "handoff_path": str(handoff_path),
            }
        },
    }

    outputs = _write_shell_artifacts(payload)

    assert not handoff_path.exists()
    assert "co_runner_handoff" not in outputs
