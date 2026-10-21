"""Cross-lane numerical consistency, never physical/source-authority equivalence.

Checks one pinned NIST published check state against the existing UTP-137
synthetic pipe law. The stricter lane's additional regime flags must NOT
be relaxed to make both interfaces appear interchangeable.
"""
from __future__ import annotations

import math
import unittest

from cgx.review.fluid_operator_regime_projection import ASSUMPTIONS, screen_pipe_baseline
from cgx.review.water_reference_fluid_kernel_fixture import (
    DomainHold, FluidState, read_reference_state, screen,
)


def shared_parameters():
    state = read_reference_state()
    common = {
        "radius_m": 0.001,
        "length_m": 0.1,
        "flow_m3_s": 1e-7,
    }
    first = {
        "steady": True,
        "newtonian": True,
        "incompressible": True,
        "single_phase": True,
        "circular": True,
        "fully_developed": True,
        **common,
    }
    second = {
        "dynamic_viscosity_Pa_s": state.mu_pa_s,
        "density_kg_m3": state.rho_kg_m3,
        "volume_flow_m3_s": common["flow_m3_s"],
        "radius_m": common["radius_m"],
        "length_m": common["length_m"],
        "conditions": {name: True for name in ASSUMPTIONS},
    }
    return state, first, second


class CrossLaneWaterReview(unittest.TestCase):
    def test_exact_published_state_is_shared_without_new_source(self):
        state, _, p = shared_parameters()
        self.assertEqual(state.source_id, "nist-liquid-water-0p1mpa-table8-298p15k")
        self.assertEqual(state.temperature_kelvin, 298.15)
        self.assertEqual(state.pressure_pa, 100000.0)
        self.assertAlmostEqual(state.mu_pa_s, 0.000889996774, places=15)
        self.assertAlmostEqual(state.rho_kg_m3, 997.047013, places=6)
        self.assertEqual(p["dynamic_viscosity_Pa_s"], state.mu_pa_s)
        self.assertEqual(p["density_kg_m3"], state.rho_kg_m3)

    def test_same_synthetic_pipe_matches_two_original_existing_interfaces(self):
        state, a, b = shared_parameters()
        left = screen("laminar_tube", a, state)
        right = screen_pipe_baseline(b)
        self.assertEqual(left["existing_kernel_links"], ["T1K-012", "VGK-019"])
        self.assertEqual(right["kernel_id"], "VGK-019")
        self.assertEqual(right["screen_state"], "SYNTHETIC_BASELINE_CONDITIONAL")
        self.assertEqual(right["holds"], [])
        self.assertTrue(math.isclose(
            left["output"]["pressure_drop_pa"], right["pressure_drop_Pa"],
            rel_tol=1e-12, abs_tol=1e-13))
        self.assertTrue(math.isclose(
            left["details"]["reynolds"], right["reynolds_dimensionless"],
            rel_tol=1e-12, abs_tol=1e-13))
        self.assertTrue(math.isclose(
            right["viscosity_nu_m2_s"], state.mu_pa_s/state.rho_kg_m3,
            rel_tol=1e-12, abs_tol=1e-15))
        self.assertFalse(left["physical_qualification"])
        self.assertFalse(right["physical_validation"])
        self.assertFalse(right["owner_dbr_promoted"])
        self.assertIsNone(right["pressure_rating"])

    def test_stricter_wall_attestation_must_not_be_ignored(self):
        state, first, second = shared_parameters()
        # The R0 reference demonstrator does not explicitly attest no-slip:
        # its conditional number cannot override the stricter owner screen.
        self.assertGreater(screen("laminar_tube", first, state)["output"]["pressure_drop_pa"], 0)
        second["conditions"]["no_slip"] = False
        held = screen_pipe_baseline(second)
        self.assertEqual(held["screen_state"], "HOLD_REGIME_OR_CONDITION")
        self.assertIn("NO_SLIP_NOT_ATTESTED", held["holds"])
        self.assertIsNone(held["pressure_drop_Pa"])

    def test_owner_numeric_screen_does_not_inherit_nist_source_authority(self):
        state, first, second = shared_parameters()
        fake = FluidState(
            state.mu_pa_s * 1.03, state.rho_kg_m3,
            state.temperature_kelvin, state.pressure_pa, state.source_id
        )
        with self.assertRaisesRegex(DomainHold, "STATE_NOT_PINNED"):
            screen("laminar_tube", first, fake)
        second["dynamic_viscosity_Pa_s"] = fake.mu_pa_s
        other = screen_pipe_baseline(second)
        self.assertEqual(other["source_and_condition_quality"],
                         "USER_ASSERTED_SYNTHETIC_ONLY_NO_MEASURED_INPUTS")
        self.assertIsNone(other["pressure_rating"])
        self.assertFalse(other["physical_validation"])

    def test_source_comparison_never_grants_rights_or_native_acceptance(self):
        state, first, second = shared_parameters()
        a = screen("laminar_tube", first, state)
        b = screen_pipe_baseline(second)
        self.assertFalse(a["native_dbr_admitted"])
        self.assertFalse(a["public_release_authorised"])
        self.assertFalse(b["owner_dbr_promoted"])
        self.assertFalse(b["public_release_authorised"])
        self.assertEqual(a["output"]["unit"], "Pa")
        self.assertIsNone(b["pressure_rating"])


if __name__ == "__main__":
    unittest.main()
