"""Source-bound synthetic fluidic regime and cross-domain refusal tests."""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

from cgx.review.fluid_transport_regime_adapter import (
    EQUATION_PATH, VOLUME_PATH, INTERACTION_PATH,
    MAX_SCREEN_RE, REQUIRED_MODEL, UNITS, RegimeHold,
    newtonian_shear_stress, poiseuille_channel_candidate,
)

ROOT=Path(__file__).resolve().parents[1]
META=ROOT/"cgx/review/cgx_fluid_constitutive_operator_reuse_20261021.json"

def candidate():
    return {
        "units": {k:v for k,v in UNITS.items() if k!="shear_rate"},
        "assumptions":dict(REQUIRED_MODEL),
        "evidence":{"synthetic_case_id":"synthetic-channel-001"},
        "quantities":{"radius":0.01,"length":2.0,"volumetric_flow":1e-6,
                      "dynamic_viscosity":0.1,"density":1000.0},
    }

class FluidConstitutiveReuseTests(unittest.TestCase):
    def test_original_type1_operator_identity_not_new_solver(self):
        d=json.loads(META.read_text(encoding="utf-8"))
        self.assertEqual(d["canonical_parent"],"Cognigrex.cgx")
        self.assertFalse(d["novel_solver_created"])
        self.assertFalse(d["physical_validation_performed"])
        self.assertEqual(len(d["domain_lenses"]),5)
        self.assertEqual(len(d["counterexamples"]),5)
        self.assertEqual({x["kernel"] for x in d["upstream_kernel_references"]},
                         {"T1K-012","VGK-019","VGK-020","fluid interactions"})
        self.assertTrue(any("158" in s for s in d["holds"]))
        self.assertTrue(any("161" in s for s in d["holds"]))

    def test_synthetic_laminar_channel_screen_units_and_source_receipts(self):
        out=poiseuille_channel_candidate(candidate(),ROOT)
        self.assertEqual(out["existing_operator_ids"],["T1K-012","VGK-019"])
        self.assertEqual(out["screen_state"],"MODEL_CANDIDATE_NOT_PHYSICALLY_VALIDATED")
        self.assertFalse(out["physical_operation_approved"])
        self.assertFalse(out["native_peer_approved"])
        self.assertFalse(out["public_release_approved"])
        self.assertAlmostEqual(out["pressure_drop_pa"],8*.1*2*1e-6/(math.pi*.01**4))
        self.assertAlmostEqual(out["reynolds_screen"],2*1000*1e-6/(math.pi*.1*.01))
        self.assertEqual(set(out["source_sha256"]),{EQUATION_PATH,VOLUME_PATH,INTERACTION_PATH})
        self.assertTrue(all(len(x)==64 for x in out["source_sha256"].values()))
        self.assertEqual(out["model_units"]["hydraulic_resistance"],"Pa*s/m^3")

    def test_inverse_fourth_power_and_density_screen(self):
        x=candidate()
        a=poiseuille_channel_candidate(x,ROOT)
        x["quantities"]["radius"]*=2
        b=poiseuille_channel_candidate(x,ROOT)
        self.assertAlmostEqual(a["pressure_drop_pa"]/b["pressure_drop_pa"],16)
        self.assertAlmostEqual(a["reynolds_screen"]/b["reynolds_screen"],2)
        self.assertAlmostEqual(a["wall_shear_pa"]/b["wall_shear_pa"],8)

    def test_viscosity_is_constitutive_stress_not_new_aerodynamics_engine(self):
        out=newtonian_shear_stress(0.25,-12)
        self.assertEqual(out["shear_stress_pa"],-3)
        self.assertEqual(out["units"]["stress"],"Pa")
        self.assertFalse(out["validated_material"])
        with self.assertRaisesRegex(RegimeHold,"INVALID_DYNAMIC_VISCOSITY"):
            newtonian_shear_stress(-0.1,1)

    def test_non_newtonian_multiphase_compressible_or_external_lens_held(self):
        tests=[
            ("constitutive_law","SHEAR_THINNING","REGIME_HOLD_CONSTITUTIVE_LAW"),
            ("continuity","AIR_WATER_MIST","REGIME_HOLD_CONTINUITY"),
            ("compressibility","COMPRESSIBLE","REGIME_HOLD_COMPRESSIBILITY"),
            ("geometry","EXTERNAL_AERODYNAMICS","REGIME_HOLD_GEOMETRY"),
            ("inlet_state","UNDEVELOPED","REGIME_HOLD_INLET_STATE"),
            ("wall","COMPLIANT_SLIP","REGIME_HOLD_WALL"),
            ("provenance_grade","UNVERIFIED","REGIME_HOLD_PROVENANCE_GRADE"),
        ]
        for field,value,reason in tests:
            with self.subTest(field=field):
                p=candidate();p["assumptions"][field]=value
                with self.assertRaisesRegex(RegimeHold,reason):
                    poiseuille_channel_candidate(p,ROOT)

    def test_high_reynolds_and_non_slender_channel_rejected(self):
        p=candidate();p["quantities"]["volumetric_flow"]=1.0
        with self.assertRaisesRegex(RegimeHold,"REYNOLDS_REGIME_HOLD"):
            poiseuille_channel_candidate(p,ROOT)
        p=candidate();p["quantities"]["length"]=0.10
        with self.assertRaisesRegex(RegimeHold,"SLENDER_CHANNEL_ASSUMPTION_HOLD"):
            poiseuille_channel_candidate(p,ROOT)
        self.assertEqual(MAX_SCREEN_RE,2000.0)

    def test_reject_implicit_unit_conversion_missing_provenance_and_extra_quantities(self):
        p=candidate();p["units"]["radius"]="mm"
        with self.assertRaisesRegex(RegimeHold,"MISSING_OR_MISMATCHED_SI_UNITS"):
            poiseuille_channel_candidate(p,ROOT)
        p=candidate();p["evidence"]={}
        with self.assertRaisesRegex(RegimeHold,"SYNTHETIC_PROVENANCE_REQUIRED"):
            poiseuille_channel_candidate(p,ROOT)
        p=candidate();p["quantities"]["viscosity"]="duplicate"
        with self.assertRaisesRegex(RegimeHold,"MISSING_OR_EXTRA_QUANTITIES"):
            poiseuille_channel_candidate(p,ROOT)
        p=candidate();p["assumptions"]["extra_unreviewed"]="true"
        with self.assertRaisesRegex(RegimeHold,"UNREVIEWED_EXTRA_MODEL_ASSUMPTIONS"):
            poiseuille_channel_candidate(p,ROOT)

    def test_reject_nonfinite_negative_bool_and_zero_values(self):
        for value in (float("nan"),float("inf"),-1.0,0.0,True):
            with self.subTest(value=str(value)):
                p=candidate();p["quantities"]["dynamic_viscosity"]=value
                with self.assertRaises(RegimeHold):
                    poiseuille_channel_candidate(p,ROOT)

    def test_original_kernel_source_drift_halts_instead_of_minting_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for path in (EQUATION_PATH,VOLUME_PATH,INTERACTION_PATH):
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/path).read_bytes())
            kernel=root/EQUATION_PATH
            d=json.loads(kernel.read_text())
            for row in d["kernels"]:
                if row.get("kernel_id")=="T1K-012":
                    row["kernel_id"]="UNVERIFIED-REPLACEMENT"
            kernel.write_text(json.dumps(d))
            with self.assertRaisesRegex(RegimeHold,"FLUID_EQUATION_OWNER_DRIFT"):
                poiseuille_channel_candidate(candidate(),root)

    def test_cross_domain_review_is_source_only_not_verified_cfd(self):
        d=json.loads(META.read_text())
        lenses={x["id"]:x for x in d["domain_lenses"]}
        self.assertIn("PRINTSPACE-RESIN",lenses)
        self.assertIn("M1-MISTING",lenses)
        self.assertIn("SPACE-PROP",lenses)
        self.assertIn("ECOSYSTEM-DARCY",lenses)
        self.assertIn("AERODYNAMICS",lenses)
        self.assertIn("VGK-020",lenses["ECOSYSTEM-DARCY"]["candidate_if"])
        self.assertEqual(d["constitutive_core"]["evidence_grade"],
                         "SOURCE_QUALIFIED_MATH_AND_SYNTHETIC_FIXTURE_ONLY")

if __name__=="__main__":
    unittest.main()
