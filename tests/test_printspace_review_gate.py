"""Negative-path focused tests; synthetic IDs are not real evidence receipts."""
import copy
import importlib.util
from pathlib import Path
import json
import unittest

spec = importlib.util.spec_from_file_location("printspace_review", Path(__file__).resolve().parents[1] / "cgx" / "manufacturing" / "review_gate.py")
compiler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compiler)


def fixture():
    return {
        "schema": "CGX-PRINTSPACE-REVIEW-INPUT/0.1",
        "article_id": "PC01-TEST-001", "manufacturing_ir_ref": "cgx://manufacturing/build/pc01-synthetic", "source_revision": "SYNTHETIC-TEST-NOT-AUTHORITY",
        "geometry": {"catalogue_position": 1, "source_id": "SYNTHETIC-GEO", "units": "mm", "coordinate_frame": "XYZ", "admission_receipt": "SYNTHETIC-ONLY", "rights_ref": "SYNTHETIC", "sha256": "a" * 64, "minimum_feature_mm": 0.4},
        "rights": {"status": "CLEARED", "licence_ref": "SYNTHETIC-ONLY"},
        "machine": {"physical_state": "NOT_BUILT", "safety_control": "INDEPENDENT_C0", "initial_atmosphere": "AMBIENT", "tool_ids": ["T1", "T2"], "minimum_feature_mm": 0.3},
        "material_lots": {"A": {"passport_ref": "A-SYNTHETIC"}, "B": {"passport_ref": "B-SYNTHETIC"}},
        "interfaces": [{"id": "AB", "predecessor_lot": "A", "successor_lot": "B", "status": "QUALIFIED", "evidence_ref": "FAKE-TEST-RECEIPT", "process_revision": "SYNTHETIC"}],
        "operations": [
            {"id": "p0", "kind": "PREPARE", "depends_on": []},
            {"id": "d1", "kind": "DEPOSIT", "depends_on": ["p0"], "material_lot_id": "A", "tool_id": "T1"},
            {"id": "d2", "kind": "DEPOSIT", "depends_on": ["d1"], "material_lot_id": "B", "on_material_lot_id": "A", "on_operation_id": "d1", "interface_id": "AB", "tool_id": "T2"},
            {"id": "seal", "kind": "ENCAPSULATE", "depends_on": ["d2"], "barrier_ref": "SYNTHETIC-BARRIER", "post_seal_test_id": "test"},
            {"id": "test", "kind": "VERIFY", "depends_on": ["seal"], "test_type": "POST_SEAL", "evidence_ref": "SYNTHETIC-TEST"},
        ]
    }


def codes(doc):
    return {f["code"] for f in compiler.compile_review(doc)["findings"]}


class PrintSpaceReviewTests(unittest.TestCase):
    def test_review_deterministic_and_without_authority(self):
        p = fixture()
        a = compiler.compile_review(p)
        self.assertEqual(a, compiler.compile_review(copy.deepcopy(p)))
        self.assertEqual(a["state"], "REVIEW_ONLY")
        self.assertEqual(a["ordered_operations"], ["p0", "d1", "d2", "seal", "test"])
        for k in ("physical_machine_authorised", "mint_authorised", "commercial_release_authorised"):
            self.assertFalse(a[k])
        self.assertEqual(a["evidence_status"], "DECLARED_NOT_INDEPENDENTLY_VERIFIED")

    def test_catalogue_sentinel_rejected(self):
        p = fixture(); p["geometry"]["catalogue_position"] = 174
        self.assertIn("GEOMETRY_NOT_ADMITTED", codes(p))

    def test_direction_not_reversible(self):
        p = fixture()
        p["operations"][2]["material_lot_id"] = "A"
        p["operations"][2]["on_material_lot_id"] = "B"
        self.assertIn("DIRECTIONAL_INTERFACE", codes(p))

    def test_gradient_with_missing_composition_law(self):
        p = fixture(); p["operations"][2]["gradient"] = {"minimum_feature_mm": 0.4, "coupon_receipt": "TEST"}
        self.assertIn("GRADIENT_UNQUALIFIED", codes(p))

    def test_encapsulation_needs_post_seal(self):
        p = fixture(); p["operations"][3]["post_seal_test_id"] = "none"
        self.assertIn("POST_SEAL_TEST", codes(p))

    def test_field_activation_needs_measurements(self):
        p = fixture(); p["operations"].append({"id": "act", "kind": "ACTIVATE", "depends_on": ["test"], "stimulus": "EM", "field": {"frequency_hz": 2.4e9}})
        self.assertIn("EM_DOSE_UNBOUND", codes(p))

    def test_purge_needs_chamber_rating(self):
        p = fixture(); p["operations"].insert(1, {"id": "gas", "kind": "PURGE", "depends_on": ["p0"], "target_atmosphere": "VACUUM", "sensor_calibration_ref": "SYN", "transition_receipt": "SYN"})
        self.assertIn("UNRATED_CHAMBER", codes(p))

    def test_rights_blocked(self):
        p = fixture(); p["rights"]["status"] = "UNKNOWN"; p["commercial_release_requested"] = True
        self.assertIn("RIGHTS_BLOCK", codes(p))

    def test_cyclic_dependencies_rejected(self):
        p = fixture(); p["operations"][0]["depends_on"] = ["test"]
        a = compiler.compile_review(p)
        self.assertEqual(a["state"], "HOLD")
        self.assertIn("CYCLIC_PROCESS", {f["code"] for f in a["findings"]})

    def test_unqualified_reverse_and_undeclared_lot(self):
        p = fixture(); p["operations"][2]["on_material_lot_id"] = "B"
        self.assertIn("PREDECESSOR_NOT_DEPOSITED", codes(p))
        p["operations"][2]["material_lot_id"] = "NO_LOT"
        self.assertIn("UNBOUND_MATERIAL", codes(p))

    def test_oxygen_budget(self):
        p = fixture(); p["operations"].insert(1, {"id": "gas", "kind": "PURGE", "depends_on": ["p0"], "target_atmosphere": "CONTROLLED_GAS", "measured_o2_ppm": 800, "maximum_o2_ppm": 500, "sensor_calibration_ref": "SYN", "transition_receipt": "SYN"})
        p["operations"][2]["depends_on"] = ["gas"]
        self.assertIn("OXYGEN_BUDGET", codes(p))

    def test_out_of_order_layer_rejected(self):
        p = fixture(); p["operations"][2]["depends_on"] = ["p0"]
        self.assertIn("PREDECESSOR_NOT_DEPOSITED", codes(p))

    def test_resolution_and_tool_constraints(self):
        p = fixture(); p["geometry"]["minimum_feature_mm"] = 0.05
        p["operations"][2]["tool_id"] = "unknown"
        c = codes(p)
        self.assertIn("RESOLUTION_EXCEEDED", c)
        self.assertIn("UNAVAILABLE_TOOL", c)

    def test_unsafe_control_plan(self):
        p = fixture(); p["machine"]["safety_control"] = "DELEGATED_C2"
        self.assertIn("C0_NOT_INDEPENDENT", codes(p))

    def test_positive_synthetic_gradient_and_purge(self):
        p = fixture()
        p["operations"].insert(1, {"id": "gas", "kind": "PURGE", "depends_on": ["p0"], "target_atmosphere": "CONTROLLED_GAS", "sensor_calibration_ref": "SYN", "transition_receipt": "SYN", "measured_o2_ppm": 200, "maximum_o2_ppm": 500})
        p["operations"][2]["depends_on"] = ["gas"]
        p["operations"][2]["required_atmosphere"] = "CONTROLLED_GAS"
        p["operations"][3]["required_atmosphere"] = "CONTROLLED_GAS"
        p["operations"][3]["gradient"] = {"composition_law_ref": "SYN", "spatial_field_ref": "SYN", "coupon_receipt": "SYN", "minimum_feature_mm": 0.4}
        self.assertEqual(compiler.compile_review(p)["state"], "REVIEW_ONLY")

    def test_later_purge_invalidates_earlier_atmosphere(self):
        p = fixture()
        p["operations"].insert(1, {"id": "inert", "kind": "PURGE", "depends_on": ["p0"], "target_atmosphere": "CONTROLLED_GAS", "sensor_calibration_ref": "SYN", "transition_receipt": "SYN", "measured_o2_ppm": 200, "maximum_o2_ppm": 500})
        p["operations"].insert(2, {"id": "reset", "kind": "PURGE", "depends_on": ["inert"], "target_atmosphere": "AMBIENT", "sensor_calibration_ref": "SYN", "transition_receipt": "SYN"})
        p["operations"][3]["depends_on"] = ["reset"]
        p["operations"][3]["required_atmosphere"] = "CONTROLLED_GAS"
        self.assertIn("MISSING_ATMOSPHERE", codes(p))

    def test_parallel_environment_conflict(self):
        p = fixture()
        p["operations"].append({"id": "inert", "kind": "PURGE", "depends_on": ["p0"], "target_atmosphere": "CONTROLLED_GAS", "sensor_calibration_ref": "SYN", "transition_receipt": "SYN", "measured_o2_ppm": 200, "maximum_o2_ppm": 500})
        p["operations"][1]["depends_on"] = ["p0", "inert"]
        self.assertIn("AMBIGUOUS_ATMOSPHERE", codes(p))

    def test_malformed_untrusted_types_fail_closed(self):
        p = fixture()
        p["operations"][2]["material_lot_id"] = {}
        p["operations"][3]["post_seal_test_id"] = []
        p["interfaces"][0]["predecessor_lot"] = {}
        p["operations"][2]["kind"] = {}
        self.assertEqual(compiler.compile_review(p)["state"], "HOLD")

    def test_nonfinite_input_fails_closed(self):
        p = fixture(); p["machine"]["minimum_feature_mm"] = float("inf")
        self.assertIn("NONCANONICAL_INPUT", codes(p))

    def test_canonical_manufacturing_ref_required(self):
        p = fixture(); p.pop("manufacturing_ir_ref")
        self.assertIn("CANONICAL_IR_REFERENCE", codes(p))

    def test_empty_process_fails_closed(self):
        p = fixture(); p["operations"] = []
        self.assertIn("EMPTY_PROCESS", codes(p))

    def test_malformed_dependency_and_unknown_kind(self):
        p = fixture(); p["operations"][1]["depends_on"] = ["MISSING"]
        p["operations"][2]["kind"] = "EXECUTE_NOW"
        c = codes(p)
        self.assertIn("UNKNOWN_DEPENDENCY", c)
        self.assertIn("UNKNOWN_OPERATION", c)




class CanonicalIRBindingTests(unittest.TestCase):
    """Synthetic tests: a declared match does not verify external source evidence."""

    def example(self):
        from cgx.manufacturing import compile_component, find_archetype, load_default_atlas
        from cgx.manufacturing import review_existing_manufacturing_ir
        ir = compile_component(
            find_archetype(load_default_atlas(), "PN rectifier diode"),
            build_id="pc01-synthetic",
        )
        packet = fixture()
        packet["manufacturing_ir_ref"] = ir["cgx_uri"]
        packet["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
        return review_existing_manufacturing_ir, ir, packet

    def test_unbound_canonical_ir_cannot_be_overridden_by_synthetic_receipts(self):
        review, ir, packet = self.example()
        out = review(ir, packet)
        self.assertEqual(out["state"], "HOLD")
        self.assertTrue(out["binding_proof"]["canonical_ir_hash_matched"])
        codes = {f["code"] for f in out["findings"]}
        self.assertIn("EXACT_CGXI_UNBOUND", codes)
        self.assertIn("CANONICAL_IR_BLOCKERS", codes)
        self.assertIn("CANONICAL_INSTANCE_NOT_READY", codes)
        self.assertFalse(out["physical_machine_authorised"])

    def test_wrong_uri_and_hash_block_even_when_geometry_review_is_synthetic_pass(self):
        review, ir, packet = self.example()
        packet["manufacturing_ir_ref"] = "cgx://manufacturing/build/other"
        packet["manufacturing_ir_configuration_hash"] = "0" * 64
        out = review(ir, packet)
        self.assertEqual(out["state"], "HOLD")
        codes = {f["code"] for f in out["findings"]}
        self.assertIn("CANONICAL_IR_URI_MISMATCH", codes)
        self.assertIn("CANONICAL_IR_HASH_MISMATCH", codes)

    def test_mutated_canonical_ir_requires_rehash_and_review(self):
        review, ir, packet = self.example()
        ir["scope_decision"]["included"].pop("material", None)
        out = review(ir, packet)
        self.assertEqual(out["state"], "HOLD")
        self.assertIn("CANONICAL_IR_HASH_MISMATCH", {f["code"] for f in out["findings"]})

    def test_synthetic_ready_instance_still_not_a_machine_licence_or_qualification(self):
        from cgx.manufacturing.compiler import _canonical_hash
        review, ir, packet = self.example()
        ir["instance_ref"] = "CGXI-SYNTHETIC"
        ir["binding_progress"] = "BUILD_READY"
        ir["execution_state"] = "BUILD_READY"
        ir["blockers"] = []
        ir["configuration_hash"] = _canonical_hash({k: v for k, v in ir.items() if k != "configuration_hash"})
        packet["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
        result = review(ir, packet)
        self.assertEqual(result["state"], "REVIEW_ONLY")
        self.assertTrue(result["binding_proof"]["canonical_ir_hash_matched"])
        self.assertFalse(result["binding_proof"]["trusted_external_receipt"])
        for field in ("physical_machine_authorised", "mint_authorised", "commercial_release_authorised"):
            self.assertFalse(result[field])




class CanonicalIRGeometryCompositionTests(unittest.TestCase):
    """Geometry references and process IR are the SAME frozen build, never separate masters."""

    def packet(self):
        from cgx.manufacturing import compile_component, find_archetype, load_default_atlas
        from cgx.manufacturing import review_existing_manufacturing_ir
        ir = compile_component(find_archetype(load_default_atlas(), "PN rectifier diode"),
                               build_id="pc01-three-layer-coupon")
        process = fixture()
        process["manufacturing_ir_ref"] = ir["cgx_uri"]
        process["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
        example = json.loads(
            (Path(__file__).resolve().parents[1] /
             "cgx/manufacturing/printspace_composite_pilot_v0_1.json").read_text()
        )
        example["manufacturing_ir_ref"] = ir["cgx_uri"]
        example["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
        return review_existing_manufacturing_ir, ir, process, example

    def test_composition_links_to_exact_same_ir_but_unbound_instance_holds(self):
        func, ir, process, geometry = self.packet()
        out = func(ir, process, geometry_composition=geometry)
        self.assertEqual(out["state"], "HOLD")
        self.assertEqual(out["geometry_projection"]["state"], "REVIEW_ONLY")
        self.assertEqual(out["geometry_projection"]["load_h0"]["hydration"], "H0_METADATA_ONLY")
        self.assertFalse(out["geometry_projection"]["source_and_material_evidence_verified"])
        self.assertIn("CANONICAL_INSTANCE_NOT_READY", {e["code"] for e in out["findings"]})
        self.assertFalse(out["physical_machine_authorised"])

    def test_mutated_ir_geometry_hash_holds(self):
        func, ir, process, geometry = self.packet()
        geometry["manufacturing_ir_configuration_hash"] = "0" * 64
        out = func(ir, process, geometry_composition=geometry)
        self.assertIn("GEOMETRY_IR_HASH_MISMATCH", {e["code"] for e in out["findings"]})

    def test_cross_build_geometry_uri_holds(self):
        func, ir, process, geometry = self.packet()
        geometry["manufacturing_ir_ref"] = "cgx://manufacturing/build/another-candidate"
        out = func(ir, process, geometry_composition=geometry)
        self.assertIn("GEOMETRY_IR_URI_MISMATCH", {e["code"] for e in out["findings"]})

    def test_unadmitted_raphael_composite_does_not_pass(self):
        func, ir, process, geometry = self.packet()
        geometry["source_shapes"][0]["t173_position"] = 1
        out = func(ir, process, geometry_composition=geometry)
        self.assertEqual(out["state"], "HOLD")
        self.assertIn("GEOMETRY_COMPOSITION_HOLD", {e["code"] for e in out["findings"]})
        self.assertFalse(out["mint_authorised"])

    def test_malformed_geometry_bridge_returns_explicit_hold(self):
        func, ir, process, geometry = self.packet()
        out = func(ir, process, geometry_composition=["bad"])
        codes = {e["code"] for e in out["findings"]}
        self.assertEqual(out["state"], "HOLD")
        self.assertIn("GEOMETRY_COMPOSITION_HOLD", codes)
        self.assertIn("GEOMETRY_IR_URI_MISMATCH", codes)
        self.assertFalse(out["commercial_release_authorised"])

    def test_mock_ready_ir_is_still_review_not_actuation(self):
        from cgx.manufacturing.compiler import _canonical_hash
        func, ir, process, geometry = self.packet()
        ir["instance_ref"] = "CGXI-SYNTHETIC-NOT-REAL"
        ir["binding_progress"] = "BUILD_READY"
        ir["execution_state"] = "BUILD_READY"
        ir["blockers"] = []
        ir["configuration_hash"] = _canonical_hash({k: v for k, v in ir.items()
                                                    if k != "configuration_hash"})
        process["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
        geometry["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
        out = func(ir, process, geometry_composition=geometry)
        self.assertEqual(out["state"], "REVIEW_ONLY")
        self.assertEqual(out["geometry_projection"]["state"], "REVIEW_ONLY")
        self.assertFalse(out["binding_proof"]["trusted_external_receipt"])
        for key in ("physical_machine_authorised", "commercial_release_authorised", "mint_authorised"):
            self.assertFalse(out[key])




class CanonicalIRDirectionalWitnessTests(unittest.TestCase):
    """A valid source-index plan never constitutes physical interface acceptance."""

    def inputs(self):
        from cgx.manufacturing import compile_component, find_archetype, load_default_atlas
        from cgx.manufacturing import review_existing_manufacturing_ir
        from cgx.manufacturing.compiler import _canonical_hash
        root = Path(__file__).resolve().parents[1] / "cgx/manufacturing"
        ir = compile_component(find_archetype(load_default_atlas(), "PN rectifier diode"),
                               build_id="pc01-three-layer-coupon")
        ir["instance_ref"] = "CGXI-SYNTHETIC-UNTRUSTED"
        ir["binding_progress"] = "BUILD_READY"
        ir["execution_state"] = "BUILD_READY"
        ir["blockers"] = []
        ir["configuration_hash"] = _canonical_hash({k: v for k, v in ir.items() if k != "configuration_hash"})
        process = fixture()
        process["manufacturing_ir_ref"] = ir["cgx_uri"]
        process["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
        geometry = json.loads((root / "printspace_composite_pilot_v0_1.json").read_text())
        geometry["manufacturing_ir_ref"] = ir["cgx_uri"]
        geometry["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
        selection = json.loads((root / "pc01_interface_witness_plan_v0_1.json").read_text())
        selection["manufacturing_ir_ref"] = ir["cgx_uri"]
        selection["manufacturing_ir_configuration_hash"] = ir["configuration_hash"]
        return review_existing_manufacturing_ir, ir, process, geometry, selection

    def test_exact_four_directional_witnesses_still_hold_execution(self):
        review, ir, process, geometry, selection = self.inputs()
        output = review(ir, process, geometry_composition=geometry, interface_selections=selection)
        self.assertEqual(output["witness_projection"]["state"], "PLAN_READY_UNQUALIFIED")
        self.assertEqual(output["witness_projection"]["coupon_plans"], 4)
        self.assertTrue(output["binding_proof"]["canonical_ir_hash_matched"])
        self.assertEqual(output["state"], "HOLD")
        self.assertIn("MATERIAL_INTERFACE_EVIDENCE_PENDING", {x["code"] for x in output["findings"]})
        self.assertFalse(output["witness_projection"]["independent_material_evidence_verified"])
        self.assertFalse(output["physical_machine_authorised"])
        self.assertFalse(output["commercial_release_authorised"])

    def test_stale_owner_matrix_row_blocks_selection(self):
        review, ir, process, geometry, selection = self.inputs()
        selection["region_selections"][0]["directional_sha256"] = "0" * 64
        output = review(ir, process, geometry_composition=geometry, interface_selections=selection)
        self.assertEqual(output["witness_projection"]["state"], "HOLD")
        self.assertIn("WITNESS_PLAN_HOLD", {x["code"] for x in output["findings"]})

    def test_ir_configuration_revision_not_inherited_by_witness(self):
        review, ir, process, geometry, selection = self.inputs()
        selection["manufacturing_ir_configuration_hash"] = "0" * 64
        output = review(ir, process, geometry_composition=geometry, interface_selections=selection)
        self.assertIn("WITNESS_IR_MISMATCH", {x["code"] for x in output["findings"]})

    def test_no_or_invalid_geometry_prevents_witness_resolution(self):
        review, ir, process, geometry, selection = self.inputs()
        output = review(ir, process, interface_selections=selection)
        self.assertIn("WITNESS_REQUIRES_GEOMETRY", {x["code"] for x in output["findings"]})
        self.assertEqual(output["witness_projection"]["state"], "HOLD")

    def test_caller_claimed_material_qualification_cannot_promote_ir(self):
        review, ir, process, geometry, selection = self.inputs()
        selection["evidence_state"] = "QUALIFIED"
        output = review(ir, process, geometry_composition=geometry, interface_selections=selection)
        self.assertIn("WITNESS_PLAN_HOLD", {x["code"] for x in output["findings"]})
        self.assertFalse(output["mint_authorised"])


if __name__ == "__main__":
    unittest.main()