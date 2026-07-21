import math
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from rfs_emff_validation import ValidationError, evaluate


class RFSEMFFValidationTests(unittest.TestCase):
    def test_qualitative_observation_is_retained_without_promotion(self):
        result = evaluate({
            "observation": {
                "description": "Metal particles followed the desired traced path through the medium.",
                "source": "owner recollection",
                "instrumented": False,
                "parameters_recorded": False,
            }
        })
        self.assertIn("OBSERVED_QUALITATIVE", result["epistemic_status"])
        self.assertFalse(result["gates"]["promotion_gate_to_controlled_canon"])
        self.assertFalse(result["claim_controls"]["purity_allowed"])

    def test_rfs_first_order_calculation(self):
        result = evaluate({
            "rfs": {
                "frequency_hz": 10.0,
                "displacement_amplitude_m": 0.001,
                "particle_diameter_m": 0.001,
                "particle_density_kg_m3": 7800.0,
            },
            "reasoning_evidence": {
                "boundary_conditions_defined": True,
                "alternative_causes_controlled": True,
                "model_applicability_reviewed": True,
                "independent_reviewer": True,
            },
        })
        expected_acc = (2 * math.pi * 10.0) ** 2 * 0.001
        self.assertAlmostEqual(result["calculations"]["rfs"]["acceleration_peak_m_s2"], expected_acc)
        self.assertTrue(result["gates"]["math_pass"])
        self.assertTrue(result["gates"]["promotion_gate_to_controlled_canon"])
        self.assertFalse(result["gates"]["physical_capability_claim_allowed"])

    def test_zero_amplitude_yields_zero_inertial_force(self):
        result = evaluate({
            "rfs": {
                "frequency_hz": 20.0,
                "displacement_amplitude_m": 0.0,
                "particle_diameter_m": 0.001,
                "particle_density_kg_m3": 7800.0,
            }
        })
        self.assertEqual(result["calculations"]["rfs"]["inertial_force_peak_n"], 0.0)

    def test_zero_gradient_yields_zero_magnetic_force(self):
        result = evaluate({
            "emff": {
                "coil_turns": 100,
                "coil_length_m": 0.2,
                "coil_diameter_m": 0.05,
                "current_a": 1.0,
                "relative_permeability": 1.0,
                "particle_susceptibility": 0.001,
                "particle_diameter_m": 0.001,
                "particle_density_kg_m3": 7800.0,
                "field_gradient_t_per_m": 0.0,
            }
        })
        self.assertEqual(result["calculations"]["emff"]["magnetic_force_linear_susceptibility_n"], 0.0)

    def test_negative_input_rejected(self):
        with self.assertRaises(ValidationError):
            evaluate({
                "rfs": {
                    "frequency_hz": -1.0,
                    "displacement_amplitude_m": 0.001,
                    "particle_diameter_m": 0.001,
                    "particle_density_kg_m3": 7800.0,
                }
            })

    def test_short_coil_fails_reasoning_gate(self):
        result = evaluate({
            "emff": {
                "coil_turns": 100,
                "coil_length_m": 0.05,
                "coil_diameter_m": 0.05,
                "current_a": 1.0,
                "relative_permeability": 1.0,
                "particle_susceptibility": 0.001,
                "particle_diameter_m": 0.001,
                "particle_density_kg_m3": 7800.0,
                "field_gradient_t_per_m": 0.1,
            },
            "reasoning_evidence": {
                "boundary_conditions_defined": True,
                "alternative_causes_controlled": True,
                "model_applicability_reviewed": True,
                "independent_reviewer": True,
            },
        })
        self.assertFalse(result["applicability"]["long_solenoid_screening_pass"])
        self.assertFalse(result["gates"]["independent_reasoning_pass"])

    def test_empirical_gate_requires_replicates_controls_instrumentation_and_logs(self):
        result = evaluate({
            "rfs": {
                "frequency_hz": 10.0,
                "displacement_amplitude_m": 0.001,
                "particle_diameter_m": 0.001,
                "particle_density_kg_m3": 7800.0,
            },
            "empirical_evidence": {
                "repeat_count": 2,
                "controls_passed": True,
                "instrumented": True,
                "raw_logs_attached": True,
            },
        })
        self.assertTrue(result["gates"]["empirical_verified"])
        self.assertTrue(result["gates"]["physical_capability_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
