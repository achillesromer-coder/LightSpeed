"""Alexandria transport/interaction overlay: numerical, source and falsifier checks."""
from __future__ import annotations
import copy
import importlib.util
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT/"cgx/review/alexandria_cross_scale_operator_check.py"
spec = importlib.util.spec_from_file_location("cgx_transport_overlay",P)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SourceOverlayTests(unittest.TestCase):
    def test_exact_source_anchors_and_no_native_or_release_promotion(self):
        r=mod.validate_source_projection()
        self.assertEqual(r["operator_count"],6)
        self.assertTrue(r["original_source_anchors_unchanged"])
        self.assertEqual(r["independent_physical_tests"],0)
        self.assertFalse(r["native_peer_accepted"])
        self.assertFalse(r["public_release_authorised"])
        self.assertFalse(r["owner_staging_executed"])
    def test_tampered_original_registry_has_no_valid_source_binding(self):
        self._copy_and_modify_source(lambda d:d.update({"fake_public_authority":True}),"cgx/component_atlas/type1_volumetric_kernel_v0_1.json","ORIGINAL_SOURCE_BLOB_MISMATCH")
    def _copy_and_modify_source(self,mutation,path,expected):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            projection=json.loads(mod.PROJECTION.read_text())
            for anchor in projection["source_anchors"]:
                target=base/anchor["path"]
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/anchor["path"],target)
            dest=base/mod.PROJECTION.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(json.dumps(projection),encoding="utf-8")
            target=base/path
            j=json.loads(target.read_text())
            mutation(j)
            target.write_text(json.dumps(j))
            with self.assertRaisesRegex(mod.OperatorHold,expected):
                mod.validate_source_projection(base)
    def test_invalid_reused_kernel_or_virtual_owner_promotion_fails(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            j=json.loads(mod.PROJECTION.read_text())
            for item in j["source_anchors"]:
                dest=base/item["path"]
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/item["path"],dest)
            j["operators"][0]["existing"].append("VGK-NONEXISTENT")
            dest=base/mod.PROJECTION.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(json.dumps(j))
            with self.assertRaisesRegex(mod.OperatorHold,"UNPINNED_SOURCE_KERNEL"):
                mod.validate_source_projection(base)
            j["operators"][0]["existing"].pop()
            j["owner_stage"]="APPROVED_PUBLIC_RELEASE"
            dest.write_text(json.dumps(j))
            with self.assertRaisesRegex(mod.OperatorHold,"RELEASE_STATE_CHANGED"):
                mod.validate_source_projection(base)
    def test_fluid_viscosity_is_shared_but_regimes_do_not_promote(self):
        x=mod.laminar_circular_tube(density_kg_m3=1000,viscosity_pa_s=.001,
            mean_speed_m_s=.01,radius_m=.001,length_m=1)
        self.assertAlmostEqual(x["reynolds"],20)
        self.assertAlmostEqual(x["pressure_drop_pa"],80)
        self.assertAlmostEqual(x["kinematic_viscosity_m2_s"],1e-6)
        smaller=mod.laminar_circular_tube(density_kg_m3=1000,viscosity_pa_s=.001,
            mean_speed_m_s=.01,radius_m=.0005,length_m=1)
        self.assertAlmostEqual(smaller["pressure_drop_pa"]/x["pressure_drop_pa"],4)
        self.assertIn("NOT_CALIBRATED",x["status"])
    def test_turbulent_or_unqualified_law_is_refused(self):
        with self.assertRaisesRegex(mod.OperatorHold,"LAMINAR_REGIME"):
            mod.laminar_circular_tube(density_kg_m3=1000,viscosity_pa_s=.001,
               mean_speed_m_s=10,radius_m=.01,length_m=2)
        with self.assertRaisesRegex(mod.OperatorHold,"NON_PHYSICAL"):
            mod.laminar_circular_tube(density_kg_m3=1000,viscosity_pa_s=-.001,
               mean_speed_m_s=.01,radius_m=.001,length_m=1)
    def test_no_nan_infinite_unsafe_or_boolean_quantities(self):
        with self.assertRaises(mod.OperatorHold):
            mod.passive_incident_capture(irradiance_w_m2=float("nan"),aperture_m2=1,
                                         coupling_efficiency=.5,converter_efficiency=.5)
        with self.assertRaises(mod.OperatorHold):
            mod.encounter_relative_energy(moving_mass_kg=True,target_mass_kg=100,relative_speed_m_s=1)
        with self.assertRaises(mod.OperatorHold):
            mod.power_balance(incident_power_w=math.inf,useful_power_w=0,thermal_loss_w=0,stored_power_w=0)
    def test_passive_rf_power_bounded_by_incident_irradiance(self):
        r=mod.passive_incident_capture(irradiance_w_m2=10,aperture_m2=2,
                                      coupling_efficiency=.5,converter_efficiency=.8)
        self.assertEqual(r["incident_power_w"],20)
        self.assertAlmostEqual(r["upper_bound_delivered_power_w"],8)
        self.assertIn("NO_MEASURED",r["status"])
        with self.assertRaisesRegex(mod.OperatorHold,"GREATER_THAN_INCIDENT"):
            mod.passive_incident_capture(irradiance_w_m2=10,aperture_m2=2,
                                         coupling_efficiency=1.01,converter_efficiency=.9)
    def test_encounter_is_not_capture_or_passive_planet_formation(self):
        r=mod.encounter_relative_energy(moving_mass_kg=1,target_mass_kg=1,relative_speed_m_s=10)
        self.assertEqual(r["center_of_mass_relative_energy_j"],25)
        self.assertFalse(r["capture_demonstrated"])
        self.assertFalse(r["environmental_fate_demonstrated"])
        still=mod.encounter_relative_energy(moving_mass_kg=1,target_mass_kg=1,relative_speed_m_s=0)
        self.assertEqual(still["center_of_mass_relative_energy_j"],0)
        self.assertFalse(still["capture_demonstrated"])
    def test_power_energy_budget_flags_unaccounted_loss(self):
        matched=mod.power_balance(incident_power_w=100,useful_power_w=40,
                                   thermal_loss_w=30,stored_power_w=30)
        self.assertTrue(matched["closed_within_declared_tolerance"])
        missing=mod.power_balance(incident_power_w=100,useful_power_w=40,
                                   thermal_loss_w=20,stored_power_w=10)
        self.assertEqual(missing["unallocated_power_residual_w"],30)
        self.assertFalse(missing["closed_within_declared_tolerance"])
        with self.assertRaisesRegex(mod.OperatorHold,"OUTPUTS_EXCEED_INPUTS"):
            mod.power_balance(incident_power_w=20,useful_power_w=25,
                               thermal_loss_w=0,stored_power_w=0)
    def test_scale_graph_analogy_preserves_dimension_and_rights(self):
        j=json.loads(mod.PROJECTION.read_text())
        op=next(x for x in j["operators"] if x["id"]=="TR-05")
        self.assertNotEqual(op["dimensions"]["information"],op["dimensions"]["energy"])
        self.assertIn("not convertible",op["falsifier"])
        self.assertIn("no claim",j["semantic_contract"]["fractal_rule"].lower())
        self.assertEqual(j["protected_issues"],[158,161])
    def test_multiple_observation_modes_not_one_universal_wave_model(self):
        j=json.loads(mod.PROJECTION.read_text())
        op=next(x for x in j["operators"] if x["id"]=="TR-03")
        names=" ".join(d["name"] for d in op["domains"])
        self.assertIn("sonar",names)
        self.assertIn("passive RF",names)
        self.assertIn("Schumann",names)
        self.assertIn("no derived sensing coverage",op["falsifier"])
if __name__=="__main__":
    unittest.main()
