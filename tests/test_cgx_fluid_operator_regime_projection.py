"""Independent dimension and regime falsifiers for existing VGK fluid kernels."""
from __future__ import annotations

import copy
import math
from pathlib import Path
import tempfile
import unittest

from cgx.review.fluid_operator_regime_projection import (
    ASSUMPTIONS, DIMENSIONS, KERNEL_IDS, SOURCE, SOURCE_GIT_BLOB,
    project_fluid_reuse, screen_pipe_baseline
)
ROOT=Path(__file__).resolve().parents[1]

def vector(*xs:tuple[int,int,int]) -> tuple[int,int,int]:
    return tuple(sum(v[i] for v in xs) for i in range(3))

def inverse(v:tuple[int,int,int]) -> tuple[int,int,int]:
    return tuple(-n for n in v)

def sample():
    return {
        "dynamic_viscosity_Pa_s":.001,
        "density_kg_m3":998.0,
        "volume_flow_m3_s":1e-7,
        "radius_m":.005,
        "length_m":1.0,
        "conditions":{k:True for k in ASSUMPTIONS},
    }

class CgxFluidSharedOperatorTests(unittest.TestCase):
    def test_source_bound_four_original_owner_kernels_not_new_engine(self):
        d=project_fluid_reuse()
        self.assertEqual(d["existing_source"]["git_blob_sha1"], SOURCE_GIT_BLOB)
        self.assertEqual(d["existing_source"]["path"],SOURCE)
        self.assertEqual(d["parent"],"Cognigrex.cgx")
        self.assertEqual([r["id"] for r in d["referenced_original_kernels"]],list(KERNEL_IDS))
        self.assertEqual([r["compiler_token"] for r in d["referenced_original_kernels"]],[
            "VOL_FLUID_CIRCULAR", "VOL_FLUID_POROUS",
            "VOL_COUPLED_STATE_ASSEMBLY","VOL_FLUID_GENERAL_3D"
        ])
        self.assertFalse(d["new_solver_installed"])
        self.assertFalse(d["owner_dbr_promoted"])
        self.assertFalse(d["public_release_authorised"])
        self.assertFalse(d["native_two_node_accepted"])
        self.assertEqual(d["issues_held"],[158,161])

    def test_dimensions_conserve_SI_and_Re_is_dimensionless(self):
        D=DIMENSIONS
        self.assertEqual(vector(D["dynamic_viscosity_Pa_s"],inverse(D["density_kg_m3"])),D["kinematic_viscosity_m2_s"])
        self.assertEqual(vector(D["density_kg_m3"],D["velocity_m_s"],D["length_m"],
                                inverse(D["dynamic_viscosity_Pa_s"])), D["dimensionless"])
        self.assertEqual(vector(D["dynamic_viscosity_Pa_s"],D["length_m"],
                                D["flow_m3_s"],*[inverse(D["length_m"])]*4),D["pressure_Pa"])

    def test_distinct_domain_regimes_share_mu_but_not_auto_qualify(self):
        bindings=project_fluid_reuse()["domain_bindings"]
        self.assertEqual(len(bindings),6)
        self.assertIn("VGK-039",bindings["external_aerodynamics"]["kernels"])
        self.assertIn("VGK-020",bindings["porous_or_wicking_flow"]["kernels"])
        self.assertIn("VGK-036",bindings["printspace_resin_or_inert_gas"]["kernels"])
        self.assertIn("VGK-039",bindings["orbital_propellant_and_microgravity"]["kernels"])
        for data in bindings.values():
            self.assertTrue(data["domain_dependencies"])
            self.assertNotIn(data["numeric_state"],("QUALIFIED","PHYSICAL_RUN","RELEASE"))
        # Print resin constitutive rheology and microgravity capillary regime
        # cannot be inferred by knowing room-temperature water viscosity.
        self.assertTrue(any("shear" in x for x in bindings["printspace_resin_or_inert_gas"]["domain_dependencies"]))
        self.assertTrue(any("surface tension" in x for x in bindings["orbital_propellant_and_microgravity"]["domain_dependencies"]))

    def test_laminar_synthetic_baseline_matches_independent_formula(self):
        s=sample()
        actual=screen_pipe_baseline(s)
        q=s["volume_flow_m3_s"];r=s["radius_m"];L=s["length_m"]
        mu=s["dynamic_viscosity_Pa_s"];rho=s["density_kg_m3"]
        expected_p=8*mu*L*q/(math.pi*r**4)
        expected_Re=2*r*(q/(math.pi*r**2))*rho/mu
        self.assertEqual(actual["screen_state"],"SYNTHETIC_BASELINE_CONDITIONAL")
        self.assertAlmostEqual(actual["pressure_drop_Pa"],expected_p,places=10)
        self.assertAlmostEqual(actual["reynolds_dimensionless"],expected_Re,places=10)
        self.assertAlmostEqual(actual["viscosity_nu_m2_s"],mu/rho,places=12)
        self.assertEqual(actual["holds"],[])
        self.assertIsNone(actual["pressure_rating"])
        self.assertFalse(actual["physical_validation"])
        self.assertFalse(actual["owner_dbr_promoted"])

    def test_laminar_viscosity_and_radius_sensitivity_do_not_change_physics(self):
        base=screen_pipe_baseline(sample())
        twice_mu=sample();twice_mu["dynamic_viscosity_Pa_s"]*=2
        visc=screen_pipe_baseline(twice_mu)
        self.assertAlmostEqual(visc["pressure_drop_Pa"],2*base["pressure_drop_Pa"],places=9)
        self.assertAlmostEqual(visc["reynolds_dimensionless"],.5*base["reynolds_dimensionless"],places=9)
        twice_r=sample();twice_r["radius_m"]*=2
        wide=screen_pipe_baseline(twice_r)
        self.assertAlmostEqual(wide["pressure_drop_Pa"],base["pressure_drop_Pa"]/16,places=9)
        self.assertAlmostEqual(wide["reynolds_dimensionless"],base["reynolds_dimensionless"]/2,places=9)

    def test_high_Re_falsifies_laminar_pressure_baseline_without_new_solver(self):
        s=sample();s["volume_flow_m3_s"]=1e-3
        r=screen_pipe_baseline(s)
        self.assertEqual(r["screen_state"],"HOLD_REGIME_OR_CONDITION")
        self.assertIsNone(r["pressure_drop_Pa"])
        self.assertIn("REYNOLDS_ABOVE_CONSERVATIVE_LAMINAR_SCREEN",r["holds"])

    def test_short_pipe_rejects_unproven_fully_developed_entrance(self):
        s=sample();s["length_m"]=1e-3
        r=screen_pipe_baseline(s)
        self.assertEqual(r["screen_state"],"HOLD_REGIME_OR_CONDITION")
        self.assertIn("ENTRANCE_LENGTH_SCREEN_NOT_MET",r["holds"])
        self.assertIsNone(r["pressure_drop_Pa"])

    def test_non_newtonian_or_multiphase_cannot_inherit_channel_law(self):
        for field in ("newtonian","single_phase","incompressible","no_slip",
                      "rigid_circular_wall","steady","isothermal","fully_developed"):
            s=sample();s["conditions"][field]=False
            r=screen_pipe_baseline(s)
            self.assertEqual(r["screen_state"],"HOLD_REGIME_OR_CONDITION",field)
            self.assertIsNone(r["pressure_drop_Pa"])

    def test_malformed_or_unapproved_attributes_fail_closed(self):
        for key,value in [
            ("dynamic_viscosity_Pa_s",0.0),
            ("density_kg_m3",float("nan")),
            ("radius_m",1e-20),
            ("length_m",float("inf")),
            ("volume_flow_m3_s",-1),
            ("dynamic_viscosity_Pa_s",True),
        ]:
            s=sample();s[key]=value
            with self.assertRaises(ValueError, msg=key):
                screen_pipe_baseline(s)
        s=sample();s["conditions"]["newtonian"]="true"
        with self.assertRaisesRegex(ValueError,"BOOLEAN"):
            screen_pipe_baseline(s)
        s=sample();s["source_grant"]="public"
        with self.assertRaisesRegex(ValueError,"EXACT_PIPE_INPUT"):
            screen_pipe_baseline(s)
        s=sample();s["conditions"].pop("isothermal")
        with self.assertRaisesRegex(ValueError,"CONDITION_FLAGS"):
            screen_pipe_baseline(s)

    def test_source_drift_and_disappearing_owner_atlas_cannot_be_silently_accepted(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);path=root/SOURCE;path.parent.mkdir(parents=True)
            original=(ROOT/SOURCE).read_bytes()
            path.write_bytes(original)
            self.assertEqual(project_fluid_reuse(root)["existing_source"]["git_blob_sha1"],SOURCE_GIT_BLOB)
            path.write_bytes(original+b"\n")
            with self.assertRaisesRegex(ValueError,"SOURCE_CHANGED"):
                project_fluid_reuse(root)
            path.unlink()
            with self.assertRaisesRegex(ValueError,"SOURCE_MISSING"):
                project_fluid_reuse(root)

if __name__=="__main__":
    unittest.main()
