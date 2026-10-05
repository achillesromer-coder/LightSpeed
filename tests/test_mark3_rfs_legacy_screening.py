from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK3 = ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed" / "Z Axis" / "Z-4_Merovingian" / "core" / "simulations" / "mark3.py"
RECEIPT = ROOT / "cgx" / "domain_templates" / "mark3_rfs_legacy_screening_2026-10-05.json"


def test_legacy_mark3_rfs_frequency_is_not_presented_as_operational():
    text = MARK3.read_text(encoding="utf-8")
    assert "'status': 'simulated_unvalidated'" in text
    assert "LEGACY_SIMULATION_CONSTANT_UNVALIDATED" in text
    assert "not measured RFS resonance" in text


def test_screening_receipt_preserves_claim_boundary():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert receipt["status"] == "DERIVED_SCREENING_EXECUTED / PHYSICAL_VALIDATION_HELD"
    assert receipt["source_value"]["legacy_frequency_hz"] == 2.4e9
    mid = receipt["sensitivity_band"]["rows"][1]
    assert abs(mid["wavelength_vacuum_m"] - 0.12491352416666666) < 1e-15
    assert receipt["authority_transfer"] is False
    assert receipt["public_publish_authorized"] is False
    joined = " ".join(receipt["conclusions"]).lower()
    assert "do not validate" in joined
    assert "no extraction rate" in joined
