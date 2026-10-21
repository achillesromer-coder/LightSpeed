"""Synthetic cross-scale operator tests; NO empirical/mission qualification."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "cgx/review/alexandria_cross_scale_interaction_projection.py"
spec = importlib.util.spec_from_file_location("_cgx_cross_scale", FILE)
cross = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cross)

class CrossScaleOperatorTests(unittest.TestCase):
    def test_existing_raphael_printspace_assurance_source_roots(self):
        result = cross.load_and_validate_overlay()
        self.assertEqual(result["source_roots_verified"], 3)
        self.assertEqual(result["operator_families"], 7)
        self.assertEqual(result["candidate_scenarios"], 7)
        self.assertFalse(result["AU_SAI_network_activated"])
        self.assertFalse(result["physical_model_accepted"])
        self.assertEqual(result["public_release"], "HOLD")
        self.assertEqual(result["native_two_node"], "HOLD")

    def test_mass_transport_closes_without_declaring_mitigation(self):
        x = cross.mass_inventory_kg(source_in_kg=100, recovered_kg=50,
                                    safely_stored_kg=30, emitted_kg=10, unresolved_kg=10)
        self.assertTrue(x["balance_closed"])
        self.assertFalse(x["environmentally_safe"])
        self.assertFalse(x["mitigation_verified"])

    def test_missing_emissions_inventory_is_not_silently_created(self):
        with self.assertRaisesRegex(cross.CrossScaleHold, "CONSERVATION"):
            cross.mass_inventory_kg(source_in_kg=100, recovered_kg=70,
                                    safely_stored_kg=20, emitted_kg=0, unresolved_kg=0)

    def test_mass_negative_and_nonfinite_rejected(self):
        for mass in (-1, float("nan"), float("inf")):
            with self.assertRaises(cross.CrossScaleHold):
                cross.mass_inventory_kg(source_in_kg=mass, recovered_kg=0,
                                        safely_stored_kg=0, emitted_kg=0, unresolved_kg=0)

    def test_newtonian_reynolds_in_SI_and_not_global_solver(self):
        x = cross.reynolds_candidate(density_kg_m3=1000, velocity_m_s=2,
                                     length_m=0.1, dynamic_viscosity_pa_s=0.001,
                                     constitutive_regime="newtonian_continuum")
        self.assertAlmostEqual(x["Re"], 200000)
        self.assertTrue(x["dimensionless"])
        self.assertFalse(x["flow_solution"])
        self.assertFalse(x["turbulence_or_equivalent_behaviour_proved"])

    def test_viscosity_regime_not_identical_to_nonnewtonian_resin(self):
        for regime in ("non_newtonian", "rarefied_gas", "unknown", ""):
            with self.assertRaisesRegex(cross.CrossScaleHold,"CONSTITUTIVE"):
                cross.reynolds_candidate(density_kg_m3=1000,velocity_m_s=1,length_m=0.1,
                                         dynamic_viscosity_pa_s=1,constitutive_regime=regime)

    def test_zero_viscosity_and_negative_density_rejected(self):
        for rho, mu in ((1, 0),(-1,1)):
            with self.assertRaises(cross.CrossScaleHold):
                cross.reynolds_candidate(density_kg_m3=rho,velocity_m_s=1,length_m=1,
                                         dynamic_viscosity_pa_s=mu,constitutive_regime="newtonian_continuum")

    def test_passive_rf_budget_requires_every_power_flow(self):
        s = cross.passive_rf_budget_w(incident_w=10,local_supplied_w=0,released_storage_w=0,
                                      harvested_w=2,outgoing_w=6,dissipated_w=2,stored_increase_w=0)
        self.assertEqual(s["usable_output_w"],2)
        self.assertFalse(s["net_energy_generated"])
        self.assertFalse(s["solar_or_rf_harvesting_measured"])

    def test_passive_backscatter_cannot_exceed_input_without_supply(self):
        with self.assertRaisesRegex(cross.CrossScaleHold,"CONSERVATION"):
            cross.passive_rf_budget_w(incident_w=1,local_supplied_w=0,released_storage_w=0,
                                      harvested_w=2,outgoing_w=0,dissipated_w=0,stored_increase_w=0)

    def test_active_rf_budget_declares_local_supply_and_loss(self):
        x = cross.passive_rf_budget_w(incident_w=1,local_supplied_w=3,released_storage_w=0,
                                      harvested_w=1,outgoing_w=2,dissipated_w=1,stored_increase_w=0)
        self.assertTrue(x["power_conservation_closed"])
        self.assertFalse(x["net_energy_generated"])

    def test_negative_specific_energy_not_claimed_captured_body(self):
        x = cross.two_body_orbital_energy_candidate(speed_m_s=0,radius_m=7e6,
                                                     gravitational_parameter_m3_s2=3.986004418e14)
        self.assertLess(x["specific_mechanical_energy_m2_s2"],0)
        self.assertTrue(x["negative_two_body_energy"])
        self.assertFalse(x["stable_rendezvous_or_capture_proved"])
        self.assertFalse(x["ice_deposition_qualifies_orbital_absorption"])

    def test_hyperbolic_energy_not_stable_capture(self):
        x = cross.two_body_orbital_energy_candidate(speed_m_s=17000,radius_m=7e6,
                                                     gravitational_parameter_m3_s2=3.986004418e14)
        self.assertFalse(x["negative_two_body_energy"])
        self.assertFalse(x["stable_rendezvous_or_capture_proved"])

    def test_forged_owner_or_SAI_capability_cannot_pass(self):
        data=json.loads((ROOT/"cgx/review/alexandria_cross_scale_interaction_overlay_20261021.json").read_text())
        for field,value in (("SAI_AU_network_enabled_by_this_overlay",True),
                            ("native_peer_issue_161","PASS"),
                            ("public_release_issue_158","PASS")):
            changed=copy.deepcopy(data)
            changed["status"][field]=value
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                for src in changed["source_roots"]:
                    p=root/src["path"]
                    p.parent.mkdir(parents=True,exist_ok=True)
                    p.write_bytes((ROOT/src["path"]).read_bytes())
                p=root/"cgx/review/alexandria_cross_scale_interaction_overlay_20261021.json"
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text(json.dumps(changed))
                with self.assertRaises(cross.CrossScaleHold):
                    cross.load_and_validate_overlay(root)

    def test_existing_blob_tamper_rejects_source_hydration(self):
        source=json.loads((ROOT/"cgx/review/alexandria_cross_scale_interaction_overlay_20261021.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for src in source["source_roots"]:
                p=root/src["path"]
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes((ROOT/src["path"]).read_bytes())
            f=root/source["source_roots"][0]["path"]
            f.write_bytes(f.read_bytes()+b" tampered")
            p=root/"cgx/review/alexandria_cross_scale_interaction_overlay_20261021.json"
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps(source))
            with self.assertRaisesRegex(cross.CrossScaleHold,"SOURCE_BLOB_MISMATCH"):
                cross.load_and_validate_overlay(root)

if __name__ == "__main__":
    unittest.main()
