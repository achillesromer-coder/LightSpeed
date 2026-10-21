"""CGX existing method bridge: dimensional consistency and false-equivalence holds."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from cgx.portable_node.cross_domain_method_lens import (
    validate_crosswalk, preview_method_reuse,
)

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"cgx"/"domain_templates"/"cross_domain_bridge_registry.json"

def registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))

class CrossDomainMethodLensTests(unittest.TestCase):
    def test_all_four_laws_dimensional_only_never_physical_proof(self):
        result=validate_crosswalk(registry())
        self.assertEqual(len(result["validated_examples"]),4)
        self.assertEqual(result["status"],"DIMENSIONAL_CONSISTENCY_TESTED_ONLY")
        self.assertFalse(result["physical_model_validated"])
        self.assertFalse(result["canonical_promotion"])
        self.assertFalse(result["native_dbr_verified"])

    def test_viscosity_can_appear_in_two_domains_without_law_equivalence(self):
        r=registry()
        dims=[1,-1,-1,0,0,0,0]
        for domain in ("romer","eco","cgx_printspace"):
            p=preview_method_reuse(r,domain=domain,
                   law_id="NEWTONIAN_VISCOUS_SHEAR",
                   quantity_name="mu_dynamic_viscosity",si_dimension=dims)
            self.assertEqual(p["status"],"PROPOSED_METHOD_REUSE_ONLY")
            self.assertIn("non-newtonian", " ".join(p["non_equivalence"]).lower())
            self.assertFalse(p["physical_model_validated"])
            self.assertFalse(p["canonical_promotion"])
            self.assertIsNone(p["object_id"])

    def test_heat_and_species_have_same_operator_not_same_quantity(self):
        r=registry()
        thermal=preview_method_reuse(r,domain="cgx_printspace",
                  law_id="FOURIER_CONDUCTION",quantity_name="heat_flux",
                  si_dimension=[1,0,-3,0,0,0,0])
        species=preview_method_reuse(r,domain="eco",
                  law_id="FICK_DIFFUSION",quantity_name="species_flux",
                  si_dimension=[0,-2,-1,0,0,1,0])
        self.assertEqual(thermal["operator_family"],"GRADIENT_FLUX")
        self.assertEqual(species["operator_family"],"GRADIENT_FLUX")
        self.assertNotEqual(thermal["quantity_name"],species["quantity_name"])
        self.assertFalse(thermal["solver_executed"])

    def test_wrong_dimensions_and_bad_rheology_hold(self):
        r=registry()
        x=preview_method_reuse(r,domain="cgx_printspace",
              law_id="NEWTONIAN_VISCOUS_SHEAR",
              quantity_name="mu_dynamic_viscosity",
              si_dimension=[0,2,-1,0,0,0,0])
        self.assertEqual(x["status"],"FRONTIER")
        self.assertEqual(x["reason"],"MISMATCHED_OR_UNKNOWN_PHYSICAL_QUANTITY")
        unknown=preview_method_reuse(r,domain="romer",
              law_id="NON_NEWTONIAN_RESIN_GENERIC",
              quantity_name="mu_dynamic_viscosity",
              si_dimension=[1,-1,-1,0,0,0,0])
        self.assertEqual(unknown["status"],"FRONTIER")
        self.assertEqual(unknown["reason"],"MISSING_APPLICABILITY_OR_METHOD_EVIDENCE")

    def test_unverified_sai_network_and_nonphysical_domain_not_inferred(self):
        r=registry()
        for domain in ("sai","natural_network","unknown"):
            p=preview_method_reuse(r,domain=domain,
                 law_id="NEWTONIAN_VISCOUS_SHEAR",
                 quantity_name="mu_dynamic_viscosity",
                 si_dimension=[1,-1,-1,0,0,0,0])
            self.assertEqual(p["status"],"FRONTIER")
            self.assertFalse(p["right_to_publish"])

    def test_dimension_mutation_and_accepted_relation_fail_closed(self):
        r=registry()
        r["operator_family_crosswalk"]["constitutive_examples"][0]["quantities"][-1]["si_dimension"]=[0,0,0,0,0,0,0]
        with self.assertRaisesRegex(ValueError,"physical dimension mismatch"):
            validate_crosswalk(r)
        r=registry()
        r["operator_family_crosswalk"]["cross_domain_application_candidates"][0]["status"]="accepted"
        with self.assertRaisesRegex(ValueError,"unqualified cross-domain"):
            validate_crosswalk(r)
        r=registry()
        r["operator_family_crosswalk"]["operators"][0]["derived_physics_claim"]=True
        with self.assertRaisesRegex(ValueError,"physical authority"):
            validate_crosswalk(r)

    def test_invalid_units_or_duplicate_family_refused(self):
        r=registry()
        with self.assertRaisesRegex(ValueError,"seven integer"):
            preview_method_reuse(r,domain="eco",law_id="FICK_DIFFUSION",
                               quantity_name="species_flux",si_dimension=[0,1])
        r=registry()
        r["operator_family_crosswalk"]["operators"].append(copy.deepcopy(r["operator_family_crosswalk"]["operators"][0]))
        with self.assertRaisesRegex(ValueError,"duplicated"):
            validate_crosswalk(r)

if __name__=="__main__":
    unittest.main()
