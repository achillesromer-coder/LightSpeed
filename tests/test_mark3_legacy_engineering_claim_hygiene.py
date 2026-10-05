from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK3 = ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed" / "Z Axis" / "Z-4_Merovingian" / "core" / "simulations" / "mark3.py"
AUDIT = ROOT / "cgx" / "domain_templates" / "mark3_legacy_engineering_model_audit_2026-10-05.json"


def test_mark3_legacy_engineering_outputs_are_explicitly_unvalidated():
    text = MARK3.read_text(encoding="utf-8")
    assert "LEGACY_EVIDENCE_CLASS = 'legacy_synthetic_screening'" in text
    assert text.count("'status': 'simulated_unvalidated'") >= 8
    assert "simulated_screening_low" in text
    assert "LEGACY_HEURISTIC_UNVALIDATED" in text
    assert "'physical_validation': False" in text
    assert "success_evidence_state" in text


def test_mark3_legacy_audit_enumerates_heuristics_and_nonclaims():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert audit["status"].startswith("EXECUTED")
    assert audit["evidence_class"] == "legacy_synthetic_screening"
    assert audit["semantic_corrections"]["physical_validation"] is False
    names = {item["name"] for item in audit["known_heuristics"]}
    assert {"required_power_kw", "optimal_extraction_rate", "xray_safety_factors", "temperature_rise"} <= names
    assert audit["authority_transfer"] is False
    assert audit["public_publish_authorized"] is False
