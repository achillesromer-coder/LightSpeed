import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktop/LightSpeed_Runtime"))
from lightspeed_runtime.agent_home_bridge import AgentHomeBridge
from lightspeed_runtime.desktop_adapters import format_host_runtime_policy_focus


@pytest.mark.parametrize("deferred", [False, True])
def test_deferred_budget_is_unallocated_not_measured_usage(tmp_path, deferred):
    mode = "deferred_until_dedicated_device" if deferred else "low_sleep_persistent_companion"
    policy = {"co_running_apps": {"de_sporte": {
        "mode": mode, "lightspeed_logged_in_percent": 48,
        "remaining_window_percent": 52,
        "idle_persistence_percent_of_remaining_window": 80,
        "active_interaction_percent_of_remaining_window": 20,
    }}}
    path = tmp_path / "host_runtime_policy.json"
    path.write_text(json.dumps(policy), encoding="utf-8")
    before = path.read_bytes()
    summary = AgentHomeBridge(tmp_path).host_runtime_policy_summary()
    closure = summary["resource_closure"]
    shares = closure["runtime_shares"]
    assert shares["lightspeed_resident"] == 0.48
    assert shares["de_sporte_idle_persistence"] == (0.0 if deferred else 0.416)
    assert shares["de_sporte_active_interaction"] == (0.0 if deferred else 0.104)
    assert shares["unallocated_while_deferred"] == (0.52 if deferred else 0.0)
    assert closure["runtime_total"] == 1.0
    assert closure["evidence_class"] == "configured_scheduling_weights_not_observed_utilisation"
    assert path.read_bytes() == before
    text = format_host_runtime_policy_focus({"host_runtime_policy": summary})
    assert mode in text
    assert "not measured activity" in text


def test_source_policy_retains_owner_hold_and_historical_weights():
    policy = json.loads((ROOT / "desktop/Desktop_Hooks/LightSpeed/config/host_runtime_policy.json").read_text())
    ds = policy["co_running_apps"]["de_sporte"]
    assert ds["mode"] == "deferred_until_dedicated_device"
    assert ds["prior_mode"] == "low_sleep_persistent_companion"
    assert ds["allocation_status"] == "historical_weights_retained_while_deferred"
    assert ds["active_interaction_percent_of_remaining_window"] == 20
