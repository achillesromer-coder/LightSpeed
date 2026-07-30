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


def test_shell_export_includes_web_go_bridge_without_external_write(tmp_path: Path) -> None:
    shell_root = tmp_path / "LightSpeed"
    shell_root.mkdir()
    payload = {
        "generated_at": "2026-07-07T00:00:00+00:00",
        "environment": {
            "paths": {
                "desktop_shell_root": {
                    "path": str(shell_root),
                }
            }
        },
        "launch_control": {},
        "web_drive_bridge": {
            "squarespace_embed_source": {
                "id": "1wLNW2cC-vQ1ZTzNmgGQiSFE0wGp_dvupCW1ZGBtT_yw",
                "copy_cell": "01_One_Cell_Embed!A10",
            },
            "squarespace_routes": [{"route": "/ls-go"}],
            "squarespace_implementation_log": [{"route": "/ls-go", "page_exists": "UNCONFIRMED"}],
        },
    }

    outputs = _write_shell_artifacts(payload)
    bridge_path = Path(outputs["web_drive_bridge"])

    assert bridge_path == shell_root / "config" / "web_drive_bridge.json"
    assert bridge_path.exists()
    assert "1wLNW2cC" in bridge_path.read_text(encoding="utf-8")


def test_unstated_corunner_state_can_receive_local_handoff(tmp_path: Path) -> None:
    shell_root = tmp_path / "LightSpeed"
    shell_root.mkdir()
    handoff_path = tmp_path / "DeSporte" / "lightspeed_launch_handoff.json"
    payload = {
        "generated_at": "2026-07-23T00:00:00+00:00",
        "environment": {
            "paths": {
                "desktop_shell_root": {
                    "path": str(shell_root),
                }
            }
        },
        "launch_control": {
            "co_runner": {
                "handoff_path": str(handoff_path),
            }
        },
    }

    outputs = _write_shell_artifacts(payload)

    assert Path(outputs["co_runner_handoff"]) == handoff_path
    assert handoff_path.is_file()
