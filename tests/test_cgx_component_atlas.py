from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cgx" / "component_atlas"

def load(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))

ATLAS = load("component_geometry_atlas_v0_1.json")
MRI = load("mri4d_field_slice_model_v0_1.json")
RGS = load("raphael_component_geometry_search_v0_1.json")
CIM = load("component_interaction_map_v0_1.json")

def by_id(doc: dict) -> dict[str, dict]:
    return {row["ID"]: row for row in doc["records"]}

def test_cardinality_and_unique_ids() -> None:
    assert ATLAS["record_count"] == 266
    assert MRI["record_count"] == 54
    assert RGS["record_count"] == 49
    assert CIM["record_count"] == 60
    for doc in (ATLAS, MRI, RGS, CIM):
        ids = [row["ID"] for row in doc["records"]]
        assert len(ids) == len(set(ids))

def test_atlas_covers_requested_current_component_classes() -> None:
    names = {row["Component Archetype"] for row in ATLAS["records"]}
    required = {
        "Parallel-plate capacitor",
        "Air-core solenoid inductor",
        "Quartz crystal resonator",
        "Visible LED die",
        "Electrical conduit / raceway",
        "RFID/NFC loop antenna",
        "Ambient RF energy harvester",
    }
    assert required <= names

def test_4d_model_is_xyz_plus_time_with_frequency_as_view() -> None:
    rows = by_id(MRI)
    root = rows["MRI4D-000"]
    assert "x,y,z,t" in root["Coordinates / State"]
    assert "frequency is transform/view of t" in root["Field / Property"]
    assert "analogy only" in root["Notes"]
    exposure = rows["MRI4D-058"]
    assert "no biological" in exposure["Safety / Hard Gate"]

def test_raphael_is_comparative_not_substitute_physics() -> None:
    rows = by_id(RGS)
    assert "no physical-law substitution" in rows["RGS-000"]["Raphael Role"]
    assert "standard physics solver" in rows["RGS-000"]["Evaluation Sequence"]
    assert "no free-energy assumptions" in rows["RGS-047"]["Hard Constraints"]

def test_interaction_map_requires_residual_before_higher_order() -> None:
    rows = by_id(CIM)
    closure = rows["CIM-060"]
    assert "pair/higher-order" in closure["Mechanism"]
    raphael = rows["CIM-052"]
    assert "standard physics" in raphael["Mechanism"]
    assert "novelty bias" in raphael["Primary Conflict / Parasitic"]

def test_advanced_components_are_not_falsely_marked_printable() -> None:
    rows = {row["Component Archetype"]: row for row in ATLAS["records"]}
    assert "INSERT-SEED" in rows["Visible LED die"]["Current CGX Build Class"]
    assert "INSERT-SEED" in rows["Quartz crystal resonator"]["Current CGX Build Class"]
    assert "INSERT-SEED" in rows["MEMS accelerometer"]["Current CGX Build Class"]
