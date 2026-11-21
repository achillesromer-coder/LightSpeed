"""CGX modular deployment candidate — tests only, no construction authority."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"cgx"/"manufacturing"/"modular_facility_packing.py"
FIXTURE=ROOT/"cgx"/"manufacturing"/"fixtures"/"five_unit_relief_synthetic_v0_1.json"
spec=importlib.util.spec_from_file_location("cgx_modular_facility_packing",FILE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def build():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

class ModularFacilityTests(unittest.TestCase):
    def test_five_unit_fixture_is_synthetic_and_all_publication_held(self):
        p=mod.compile_facility(build())
        self.assertEqual(p["unit_count"],5)
        self.assertFalse(p["issues"],p["issues"])
        self.assertFalse(p["shipment_authorised"])
        self.assertFalse(p["construction_authorised"])
        self.assertFalse(p["commissioning_authorised"])
        self.assertTrue(all(u["geometry_evidence"]=="SYNTHETIC_TEST_ONLY" for u in p["units"]))
    def test_shared_catalogue_instances_not_duplicated(self):
        p=mod.compile_facility(build())
        self.assertEqual(p["component_type_count"],7)
        self.assertEqual(p["component_instance_count"],10)
        self.assertEqual(p["shared_component_types"]["sensor-board"],3)
        self.assertEqual(p["shared_component_types"]["data-gateway"],2)
    def test_volumes_reserved_and_remain_unallocated(self):
        p=mod.compile_facility(build())
        for u in p["units"]:
            self.assertAlmostEqual(u["internal_m3"],36.0)
            self.assertAlmostEqual(u["embedded_asset_m3"],1.6)
            self.assertGreater(u["reserved_m3"],0)
            self.assertGreater(u["remaining_unallocated_m3"],0)
            self.assertAlmostEqual(u["remaining_unallocated_m3"]+u["reserved_m3"]+u["embedded_asset_m3"],u["internal_m3"])
    def test_links_match_world_coordinates_but_unqualified(self):
        p=mod.compile_facility(build())
        self.assertEqual(len(p["linked_services"]),4)
        self.assertTrue(all(x["port_distance_m"]==0 for x in p["linked_services"]))
        self.assertTrue(all(not x["physical_mating_qualified"] for x in p["linked_services"]))
        self.assertIn("LINK-0:HOLD_ACTUAL_PIPE_CABLE_HOSE_ROUTING_AND_COMMISSIONING",p["holds"])
    def test_unset_mass_cannot_be_transport_ready(self):
        p=mod.compile_facility(build())
        self.assertTrue(all(u["known_gross_kg"] is None for u in p["units"]))
        self.assertTrue(any("HOLD_TRANSPORT_GROSS_LIMIT" in x for x in p["holds"]))
    def test_outside_envelope_detected(self):
        d=build();d["units"][0]["placements"][0]["box_m"]=[5.8,.1,.1,1,.5,.7]
        p=mod.compile_facility(d)
        self.assertTrue(any("OUTSIDE_INTERNAL_ENVELOPE" in x for x in p["issues"]))
    def test_reserve_collision_detected(self):
        d=build();d["units"][0]["reserves"][0]["box_m"]=[.5,.3,.4,.6,.6,.6]
        p=mod.compile_facility(d)
        self.assertTrue(any("INTERSECTION" in x for x in p["issues"]))
    def test_overweight_unit_detected(self):
        d=build()
        u=d["units"][0];u["tare_kg"]=100;u["max_gross_kg"]=250
        for part in u["placements"]:part["mass_kg"]=150
        p=mod.compile_facility(d)
        self.assertTrue(any("EXCEEDS_GROSS_MASS_LIMIT" in x for x in p["issues"]))
    def test_unregistered_component_type_rejected(self):
        d=build();d["units"][0]["placements"][0]["type_id"]="invention"
        with self.assertRaises(ValueError):mod.compile_facility(d)
    def test_unregistered_and_incompatible_ports(self):
        d=build();d["connections"][0]["b"]="unit-2/absent"
        p=mod.compile_facility(d)
        self.assertTrue(any("UNREGISTERED_PORT" in x for x in p["issues"]))
        d=build();d["units"][1]["ports"][0]["medium"]="water"
        p=mod.compile_facility(d)
        self.assertTrue(any("SERVICE_FAMILY_MISMATCH" in x for x in p["issues"]))
    def test_incompatible_mating_standard(self):
        d=build();d["units"][1]["ports"][0]["standard_ref"]="DIFFERENT"
        p=mod.compile_facility(d)
        self.assertTrue(any("CONNECTOR_STANDARD_MISMATCH" in x for x in p["issues"]))
    def test_bad_port_face_detected(self):
        d=build();d["units"][0]["ports"][0]["local_xyz_m"]=[5.9,1.2,1.2]
        p=mod.compile_facility(d)
        self.assertTrue(any("PORT_NOT_ON_DECLARED_FACE" in x for x in p["issues"]))
    def test_dependency_missing_and_cycles_fail_closed(self):
        d=build();a=d["units"][0]["placements"][0];b=d["units"][0]["placements"][1]
        a["depends_on"]=[b["id"]];b["depends_on"]=[a["id"]]
        p=mod.compile_facility(d)
        self.assertTrue(any("DEPENDENCY_CYCLE" in x for x in p["issues"]))
        d=build();d["units"][0]["placements"][0]["depends_on"]=["missing"]
        p=mod.compile_facility(d)
        self.assertTrue(any("MISSING_ASSEMBLY_DEPENDENCY" in x for x in p["issues"]))
    def test_unknown_envelope_never_filled_by_intersol_proxy(self):
        d=build();d["units"][0]["internal_envelope_m"]=None;d["units"][0]["geometry_evidence"]="UNKNOWN"
        p=mod.compile_facility(d)
        self.assertIsNone(p["units"][0]["remaining_unallocated_m3"])
        self.assertIn("unit-1:HOLD_GEOMETRY_UNVERIFIED",p["holds"])
    def test_no_release_even_with_full_synthetic_volumes(self):
        d=build();p=mod.compile_facility(d)
        self.assertEqual(p["state"],"HOLD")
        self.assertIn("HOLD_DOMAIN_QUALIFICATION:STRUCTURAL",p["holds"])
    def test_schema_and_implied_release_rejected(self):
        d=build();d["release_intent"]="BUILD_NOW"
        with self.assertRaises(ValueError):mod.compile_facility(d)
        d=build();d["schema"]="CGX-COMPLETE-MANUFACTURING-AUTHORITY"
        with self.assertRaises(ValueError):mod.compile_facility(d)

if __name__=="__main__":
    unittest.main()
