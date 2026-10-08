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
    assert ATLAS["record_count"] == 411
    assert MRI["record_count"] == 64
    assert RGS["record_count"] == 61
    assert CIM["record_count"] == 75
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
        "Receiver front-end module",
        "Transmitter front-end module",
        "RFID/NFC transponder/tag assembly",
        "Three-phase inverter bridge",
        "Rigid PCB stack",
        "Thermopile infrared sensor",
        "Linear motor",
        "Porous filter element",
        "Photonic crystal / metasurface",
        "Lead screw / nut",
        "Helmholtz resonator",
        "Electrolyzer cell",
        "Microprocessor / CPU",
        "System-on-chip (SoC)",
        "Gate-driver IC",
        "CAN / LIN transceiver IC",
        "Electromechanical contactor",
        "Thermal fuse / thermal cutoff",
        "BLDC / PMSM motor-drive power stage",
        "Machine frame / datum network",
        "Printed dielectric / insulation layer",
        "Visible semiconductor LED / RGB emitter package",
        "Service bay / removable access interface",
    }
    assert required <= names

def test_4d_model_is_xyz_plus_time_with_frequency_as_view() -> None:
    rows = by_id(MRI)
    root = rows["MRI4D-000"]
    assert "x,y,z,t" in root["Coordinates / State"]
    assert "frequency is transform/view of t" in root["Coordinates / State"]
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
    assert "pairwise/higher-order" in closure["Mechanism"]
    raphael = rows["CIM-052"]
    assert "standard physics" in raphael["Mechanism"]
    assert "novelty bias" in raphael["Primary Conflict / Parasitic"]

def test_advanced_components_are_not_falsely_marked_printable() -> None:
    rows = {row["Component Archetype"]: row for row in ATLAS["records"]}
    assert "INSERT-SEED" in rows["Microprocessor / CPU"]["Current CGX Build Class"]
    assert "INSERT-SEED" in rows["System-on-chip (SoC)"]["Current CGX Build Class"]
    assert "INSERT-SEED" in rows["Electromechanical contactor"]["Current CGX Build Class"]
    assert "INSERT-SEED" in rows["Visible LED die"]["Current CGX Build Class"]
    assert "INSERT-SEED" in rows["Quartz crystal resonator"]["Current CGX Build Class"]
    assert "INSERT-SEED" in rows["MEMS accelerometer"]["Current CGX Build Class"]


def test_every_archetype_has_geometry_material_physics_and_test_fields() -> None:
    required = {
        "Baseline Geometry",
        "Geometric Parameters",
        "Typical Material Stack",
        "Primary Physics",
        "Baseline Model / Equation",
        "Ports / Interfaces",
        "Current Manufacturing Route",
        "Current CGX Build Class",
        "Raphael Search Variables",
        "Acceptance Tests",
        "Failure Modes",
        "Evidence State",
    }
    for row in ATLAS["records"]:
        for key in required:
            assert key in row
            assert str(row[key]).strip(), (row["ID"], key)


def test_gap_closure_adds_energy_process_emc_and_lineage_hard_gates() -> None:
    rows = by_id(MRI)
    assert "no output may exceed" in rows["MRI4D-063"]["Safety / Hard Gate"]
    assert "later operation" in rows["MRI4D-067"]["Safety / Hard Gate"]
    assert "simulation cannot substitute" in rows["MRI4D-066"]["Safety / Hard Gate"]
    assert "no evidence or authority uplift" in rows["MRI4D-069"]["Safety / Hard Gate"]


def test_gap_closure_raphael_keeps_conventional_physics_authoritative() -> None:
    rows = by_id(RGS)
    for key in ("RGS-049", "RGS-050", "RGS-060"):
        assert "conventional physics" in rows[key]["Raphael Role"]
        assert "standard physics solver" in rows[key]["Evaluation Sequence"]


def test_gap_closure_tracks_directional_process_and_delegated_compute_safety() -> None:
    rows = by_id(CIM)
    assert "directional" in rows["CIM-074"]["Interaction Type"]
    assert "later" in rows["CIM-074"]["Mechanism"]
    assert "local C0 safe state" in rows["CIM-075"]["Mitigation / Control"]


def test_atlas_owner_range_and_cardinality_are_exact() -> None:
    assert ATLAS["authority"]["drive_range"] == "A1:V412"
    assert ATLAS["record_count"] == len(ATLAS["records"])
    assert ATLAS["status"].endswith("GAP-CLOSURE-0.4")
