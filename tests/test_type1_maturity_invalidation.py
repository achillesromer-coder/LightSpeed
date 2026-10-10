import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "cgx" / "component_atlas" / "type1_maturity_invalidation_fixture_v0_1.json"
SCRIPT_PATH = ROOT / "scripts" / "evaluate_type1_maturity_invalidation.py"


def load_script():
    spec = importlib.util.spec_from_file_location("maturity_invalidation", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8-sig"))


def test_all_invalidation_fixtures_pass_exact_closure():
    module = load_script()
    result = module.evaluate_fixture(load_fixture())

    assert result["status"] == "PASS"
    assert all(event["expected_stale_match"] for event in result["results"])
    assert all(event["preserved_violations"] == [] for event in result["results"])
    assert result["physical_evidence"] == "UNCHANGED / NO_PHYSICAL_EXECUTION"


def test_geometry_change_only_stales_capacitance_dependency_chain():
    module = load_script()
    fixture = load_fixture()
    event = next(e for e in fixture["events"] if e["id"] == "EV-GEOM-001")
    result = module.evaluate_event(fixture, event)

    assert result["stale"] == [
        "DER-CAP-100MM2",
        "DER-CAP-DENSITY",
        "STACK-P2-C-NUMERIC",
    ]
    assert "DER-R-SQUARES" not in result["stale"]
    assert "DER-MOTOR-TAU" not in result["stale"]
    assert "RAW-P2-C-MEASUREMENT" not in result["stale"]


def test_calibration_expiry_preserves_immutable_raw_observation():
    module = load_script()
    fixture = load_fixture()
    event = next(e for e in fixture["events"] if e["id"] == "EV-CAL-001")
    result = module.evaluate_event(fixture, event)

    assert result["stale"] == ["ACC-P2-C-MEASUREMENT"]
    assert "RAW-P2-C-MEASUREMENT" not in result["stale"]


def test_seed_revision_does_not_erase_independent_structure():
    module = load_script()
    fixture = load_fixture()
    event = next(e for e in fixture["events"] if e["id"] == "EV-SEED-001")
    result = module.evaluate_event(fixture, event)

    assert result["stale"] == ["DER-SEED-TIMING"]
    assert "STRUCTURE-SHELL" not in result["stale"]
