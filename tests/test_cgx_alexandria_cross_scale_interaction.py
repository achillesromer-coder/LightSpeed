"""Negative-first tests for Alexandria shared-operator review (not a physics solver)."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import tempfile
import shutil
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"cgx/review/alexandria_cross_scale_interaction_validation.py"
spec=importlib.util.spec_from_file_location("_cgx_cross_scale",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CrossScaleOperatorTests(unittest.TestCase):
    def test_source_bound_existing_atlas_and_zero_public_promotion(self):
        p=mod.qualified_projection(ROOT)
        self.assertEqual(p["operator_families"],5)
        self.assertEqual(p["unqualified_frontiers"],6)
        self.assertEqual(p["existing_kernel_refs"],["VGK-019","VGK-020","VGK-021","VGK-037","VGK-039"])
        self.assertEqual(p["state"],mod.HOLD)
        for key in ("public_release_authorised","native_signed_peer_verified",
                    "host_receipt_verified","model_execution_performed"):
            self.assertIs(p[key],False)
        self.assertEqual(len(p["source_sha256"]),2)
        self.assertTrue(all(len(v)==64 for v in p["source_sha256"].values()))

    def test_fluid_and_rf_use_current_kernels_not_new_engines(self):
        x=json.loads((ROOT/mod.REVIEW).read_text())
        f=next(v for v in x["families"] if v["family"]=="FLUID_TRANSPORT")
        e=next(v for v in x["families"] if v["family"]=="FIELD_SCATTERING_AND_OBSERVATION")
        self.assertIn("VGK-039",f["existing_kernels"])
        self.assertIn("VGK-019",f["existing_kernels"])
        self.assertIn("VGK-037",e["existing_kernels"])
        self.assertIn("rheology",str(f["domain_specific"]))
        self.assertIn("SNR",str(e["domain_specific"]))
        self.assertFalse(x["authority_gates"]["australian_network_enabled"])
        self.assertFalse(x["authority_gates"]["other_countries_enabled"])

    def test_mass_and_energy_ledgers_are_only_reported_algebra(self):
        m=mod.check_conservation_ledger(source={"intake":10},disposition={"captured":3,"loss":7},unit="kg")
        e=mod.check_conservation_ledger(source={"sun":20,"battery":10},disposition={"work":2,"heat":22,"emitted":6},unit="J")
        self.assertEqual(m["reported_disposition"],10)
        self.assertEqual(e["reported_input"],30)
        self.assertFalse(e["useful_energy_proven"])
        self.assertFalse(e["independent_measurement"])

    def test_no_output_or_infinite_energy_from_unmetered_ambient(self):
        for sources,sinks in [
            ({"ambient":1.0},{"harvested":2.0}),
            ({"ambient":-1.0},{"harvested":0.0}),
            ({"ambient":float("nan")},{"harvested":0.0}),
            ({"ambient":float("inf")},{"harvested":0.0}),
        ]:
            with self.assertRaises(mod.FrontierHold):
                mod.check_conservation_ledger(source=sources,disposition=sinks,unit="J")
        with self.assertRaisesRegex(mod.FrontierHold,"MISSING_SOURCE_SINK_OR_UNIT"):
            mod.check_conservation_ledger(source={"x":1},disposition={"y":1},unit="Hz")
        with self.assertRaisesRegex(mod.FrontierHold,"UNSAFE_RESIDUAL_TOLERANCE"):
            mod.check_conservation_ledger(source={"x":1},disposition={"y":1},unit="J",relative_tolerance=.1)

    def test_passive_observation_requires_two_measured_paths(self):
        for ref,surv in [(False,True),(True,False),(False,False)]:
            with self.assertRaisesRegex(mod.FrontierHold,"MISSING_DIRECT_AND_REFLECTED_REFERENCE"):
                mod.passive_sensing_input_state(reference_measured=ref,surveillance_measured=surv,
                  bandwidth_hz=10_000,baseline_m=100,snr_db=2)
        self.assertEqual(mod.passive_sensing_input_state(reference_measured=True,surveillance_measured=True,
          bandwidth_hz=10_000,baseline_m=100,snr_db=-5),
          "INPUT_DECLARED_TRACKING_AND_FALSE_ALARM_TEST_NOT_RUN")
        with self.assertRaisesRegex(mod.FrontierHold,"BISTATIC_GEOMETRY"):
            mod.passive_sensing_input_state(reference_measured=True,surveillance_measured=True,
                bandwidth_hz=0,baseline_m=100,snr_db=4)

    def test_ice_preceding_orbit_does_not_create_capture(self):
        with self.assertRaisesRegex(mod.FrontierHold,"NEARBY_MATERIAL_IS_NOT_CAPTURE_PROOF"):
            mod.orbital_deposition_state(epoch_and_frame="2026-10-21T00:00:00/ICRF",
              relative_velocity_m_s=.01,capture_model_verified=False,measured_dissipation=False)
        with self.assertRaisesRegex(mod.FrontierHold,"ORBIT_TIME_FRAME_MISSING"):
            mod.orbital_deposition_state(epoch_and_frame="ICRF",relative_velocity_m_s=.01,
              capture_model_verified=True,measured_dissipation=True)
        self.assertEqual(mod.orbital_deposition_state(epoch_and_frame="2026-10-21T00:00:00/ICRF",
              relative_velocity_m_s=.01,capture_model_verified=True,measured_dissipation=True),
            "MODEL_INPUT_COMPLETE_ONLY_TRAJECTORY_AND_RISK_STILL_UNQUALIFIED")

    def test_stale_or_fabricated_new_kernel_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for relative in [mod.REVIEW,mod.ATLAS]:
                target=root/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/relative,target)
            data=json.loads((root/mod.REVIEW).read_text())
            data["families"][0]["existing_kernels"].append("VGK-999")
            (root/mod.REVIEW).write_text(json.dumps(data))
            with self.assertRaisesRegex(mod.FrontierHold,"UNVERIFIED_NEW_SOLVER"):
                mod.qualified_projection(root)

    def test_no_network_or_release_promotion_from_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for relative in [mod.REVIEW,mod.ATLAS]:
                target=root/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/relative,target)
            data=json.loads((root/mod.REVIEW).read_text())
            data["authority_gates"]["australian_network_enabled"]=True
            (root/mod.REVIEW).write_text(json.dumps(data))
            with self.assertRaisesRegex(mod.FrontierHold,"UNVERIFIED_NETWORK_ENABLED"):
                mod.qualified_projection(root)
            data["authority_gates"]["australian_network_enabled"]=False
            data["authority_gates"]["public_release_authorised"]=True
            (root/mod.REVIEW).write_text(json.dumps(data))
            with self.assertRaisesRegex(mod.FrontierHold,"PUBLIC_OR_CANONICAL_PROMOTION_DENIED"):
                mod.qualified_projection(root)

    def test_evidence_qualification_is_distinct_from_frame_analogy(self):
        data=json.loads((ROOT/mod.REVIEW).read_text())
        v={x["id"]:x for x in data["frontier_records"]}
        self.assertEqual(v["FT-X05"]["grade"],"GEOMETRIC_ANALOGY_ONLY")
        self.assertIn("NO_ORBITAL_RELEASE",v["FT-X06"]["hold"])
        self.assertTrue(all(x["requires"] for x in v.values()))
        self.assertFalse(data["authority_gates"]["canonical_promotion"])

if __name__ == "__main__":
    unittest.main()
