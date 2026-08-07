from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from mark_iii_geometry_fingerprint import semantic_geometry_fingerprint
from mark_iii_manifest_fingerprint import canonical_manifest_sha256
from mark_iii_parametric import build_print_references, build_reference, export_reference

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / "mark_iii_parameters.json").read_text())
EXPECTED_SEMANTIC = "205912a4f248db9a444f30f5b258d78285dc5799e657b684af82e4fe1474a339"
EXPECTED_MANIFEST = "7e5638ef12b6d5861c7664c623b54aa485749cb4405a11becdd326339f61ca7e"


class MarkIIIParametricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.scene, cls.records = build_reference(P)
        cls.record_map = {record["node_name"]: record for record in cls.records}
        cls.family_counts = Counter(record["family"] for record in cls.records)

    def test_source_envelope_and_original_layout(self) -> None:
        self.assertEqual(P["source_parameters"]["module_length_m"]["value"], 0.75)
        self.assertEqual(P["source_parameters"]["outer_radius_m"]["value"], 0.16)
        self.assertEqual(P["source_parameters"]["shell_sector_count"]["value"], 6)
        self.assertEqual(P["design_authority_update"]["revision"], "v0.3.3")

    def test_reconciled_component_counts(self) -> None:
        expected = {
            "shell_panel": 18,
            "solar_hull_skin": 6,
            "coupler_latch": 8,
            "solenoid": 18,
            "resonator": 25,
            "resonator_mount": 24,
            "sensor": 9,
            "damping": 4,
            "plating_allowance": 18,
            "fastener": 36,
            "propulsion_interface": 4,
            "reservoir_placeholder": 1,
            "propulsion_service_port": 1,
            "fluid_route_reservation": 5,
        }
        for family, count in expected.items():
            self.assertEqual(self.family_counts[family], count, family)

    def test_named_geometry_is_complete_and_manifold(self) -> None:
        self.assertEqual(len(self.scene.geometry), 786)
        self.assertEqual(len(self.records), 786)
        self.assertEqual(sum(record["physical"] for record in self.records), 486)
        self.assertTrue(
            all(
                mesh.is_watertight and mesh.is_winding_consistent
                for mesh in self.scene.geometry.values()
            )
        )

    def test_attachment_and_cable_references_resolve(self) -> None:
        names = set(self.record_map)
        roots = {"PRIMARY_STRUCTURE", "ILLUSTRATIVE_REFERENCE_ROOT"}
        self.assertFalse(
            [
                record["node_name"]
                for record in self.records
                if record["physical"] and record["attachment_parent"] not in names | roots
            ]
        )
        self.assertFalse(
            [
                record["node_name"]
                for record in self.records
                if record["physical"]
                and record["cable_required"]
                and record["cable_route"] not in names
            ]
        )

    def test_original_appendages_are_decomposed(self) -> None:
        self.assertEqual(
            sum(record["node_name"].startswith("M3_ARM_") and record["node_name"].endswith("_BASE_INTERFACE") for record in self.records),
            2,
        )
        self.assertEqual(
            sum(
                record["family"] == "arm" and "_SEGMENT_" in record["node_name"]
                for record in self.records
            ),
            16,
        )
        self.assertEqual(self.family_counts["arm_solenoid_reference"], 48)
        self.assertEqual(
            sum(
                record["family"] == "probe_mast" and "_SEGMENT_" in record["node_name"]
                for record in self.records
            ),
            6,
        )

    def test_resonator_matrix_roles_and_spirals(self) -> None:
        resonators = [record for record in self.records if record["family"] == "resonator"]
        roles = Counter(record["component_role"] for record in resonators)
        configurations = Counter(record["configuration"] for record in resonators)
        self.assertEqual(roles["CENTRAL_BROAD_RANGE_SOURCE_ROLE"], 1)
        self.assertEqual(roles["SURROUNDING_TARGET_SPECIFIC_ROLE"], 6)
        self.assertEqual(roles["PERIPHERAL_HIGH_MID_FREQUENCY_ROLE"], 12)
        self.assertEqual(roles["UNDOPED_SUPPORT_ROLE"], 6)
        self.assertEqual(configurations["DUAL_SPIRAL_A"], 12)
        self.assertEqual(configurations["DUAL_SPIRAL_B"], 12)
        self.assertEqual(configurations["SHARED_CENTRAL"], 1)

    def test_original_propulsion_and_reservoir_interfaces_are_restored(self) -> None:
        self.assertEqual(self.family_counts["propulsion_interface"], 4)
        self.assertEqual(self.family_counts["reservoir_placeholder"], 1)
        self.assertEqual(self.family_counts["propulsion_service_port"], 1)
        self.assertEqual(self.family_counts["fluid_route_reservation"], 5)
        for idx in range(1, 5):
            node = self.record_map[f"M3_PROPULSION_INTERFACE_{idx:02d}"]
            self.assertTrue(node["cable_required"])
            self.assertEqual(node["evidence_state"], "SOURCE_RECONCILED_TOPOLOGY")
            self.assertIn("INTERFACE_ONLY", node["component_role"])
        reservoir = self.record_map["M3_PROPULSION_RESERVOIR_ALLOCATION"]
        self.assertIn("UNPRESSURISED", reservoir["component_role"])
        self.assertTrue(any("propellant" in gate.lower() for gate in P["claim_gates"]))

    def test_array_guides_are_exact(self) -> None:
        for count in P["derived_configuration"]["array_configurations"]:
            self.assertEqual(
                sum(
                    record["family"] == "array_guide"
                    and record["array_configuration"] == str(count)
                    for record in self.records
                ),
                count,
            )

    def test_print_references_are_complete_manifold_and_fit(self) -> None:
        references = build_print_references(P, self.scene, self.records)
        self.assertEqual(len(references), 20)
        bed = sorted(P["derived_configuration"]["print_bed_mm"])
        self.assertTrue(
            all(
                mesh.is_watertight
                and mesh.is_winding_consistent
                and all(
                    extent <= limit + 1e-6
                    for extent, limit in zip(sorted(mesh.extents), bed)
                )
                for mesh in references.values()
            )
        )

    def test_manufacturing_features_are_explicit(self) -> None:
        self.assertEqual(self.family_counts["plating_allowance"], 18)
        self.assertGreaterEqual(self.family_counts["plating_feature"], 72)
        self.assertTrue(
            all(
                record["print_part"] and record["manufacturing_state"]
                for record in self.records
                if record["family"] == "shell_panel"
            )
        )

    def test_quarantined_claim_values_not_active(self) -> None:
        joined = json.dumps(P).lower()
        self.assertIn("quarantined", joined)
        self.assertIn("deployment release", joined)
        self.assertGreaterEqual(len(P["claim_gates"]), 6)

    def test_semantic_fingerprint_is_stable(self) -> None:
        self.assertEqual(semantic_geometry_fingerprint(self.scene), EXPECTED_SEMANTIC)

    def test_manifest_canonical_meaning_is_stable(self) -> None:
        manifest = {
            "schema_version": "mark-iii-component-manifest-v0.3.3",
            "node_count": len(self.records),
            "components": self.records,
        }
        self.assertEqual(canonical_manifest_sha256(manifest), EXPECTED_MANIFEST)

    def test_generation_is_deterministic_for_portable_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            export_reference(ROOT / "mark_iii_parameters.json", Path(first))
            export_reference(ROOT / "mark_iii_parameters.json", Path(second))
            names = [
                "mark_iii_component_manifest.json",
                "mark_iii_print_kit_manifest.json",
                "mark_iii_print_kit_manifest.csv",
            ] + [path.name for path in Path(first).glob("*.stl")]
            self.assertEqual(len([name for name in names if name.endswith(".stl")]), 20)
            for name in names:
                self.assertEqual(
                    (Path(first) / name).read_bytes(),
                    (Path(second) / name).read_bytes(),
                    name,
                )


if __name__ == "__main__":
    unittest.main()
