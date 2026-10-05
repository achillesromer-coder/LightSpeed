from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "cgx" / "domain_templates" / "free_flow_battery_model_consistency_2026-10-05.json"

def test_free_flow_battery_consistency_receipt():
    a=json.loads(AUDIT.read_text(encoding="utf-8"))
    d=a["derived_identities"]
    assert abs(d["gross_pack_energy_wh"] - 76.8) < 1e-12
    assert abs(d["usable_energy_wh"] - 55.296) < 1e-12
    assert abs(d["total_resistance_ohm"] - 0.058) < 1e-15
    assert abs(d["loss_fraction_of_nominal_power"] - 0.02265625) < 1e-15
    assert abs(d["round_trip_efficiency_fraction"] - 0.97734375) < 1e-15
    assert abs(d["steady_thermal_delta_c"] - 4.35) < 1e-12
    assert a["authority_transfer"] is False
    assert a["public_publish_authorized"] is False
