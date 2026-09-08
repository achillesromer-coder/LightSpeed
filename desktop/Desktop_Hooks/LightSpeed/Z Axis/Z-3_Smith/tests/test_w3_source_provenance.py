from __future__ import annotations

import ast
import pathlib
import unittest


RUNNER = pathlib.Path(__file__).parents[1] / "tools" / "rfs_emff_runner.py"
EXPECTED_FILE_ID = "1OfpojKyX7gefk7c0-2NL3xm-ZnohhJI5"
EXPECTED_SHA256 = "05b34a9fb912dd9f349479b5f3480048f96c7871daa67798f29cee021aa559e6"
EXPECTED_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
EXPECTED_SIZE = 52351


class W3SourceProvenanceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = RUNNER.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def test_canonical_drive_source_identity_is_declared(self) -> None:
        self.assertIn(EXPECTED_FILE_ID, self.source)
        self.assertIn(EXPECTED_SHA256, self.source)
        self.assertIn(EXPECTED_MIME, self.source)
        self.assertIn(f'"size_bytes": {EXPECTED_SIZE}', self.source)
        self.assertIn('"provider": "google_drive"', self.source)
        self.assertIn('"role": "canonical_w3_digital_twin_source"', self.source)

    def test_job_creation_binds_canonical_source_through_inputs(self) -> None:
        create_job_calls = [
            node
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_job_v1"
        ]
        self.assertEqual(len(create_job_calls), 1)
        call = create_job_calls[0]
        inputs_kw = next((kw for kw in call.keywords if kw.arg == "inputs"), None)
        self.assertIsNotNone(inputs_kw)
        self.assertIsInstance(inputs_kw.value, ast.List)
        self.assertEqual(len(inputs_kw.value.elts), 1)
        input_expr = inputs_kw.value.elts[0]
        self.assertIsInstance(input_expr, ast.Call)
        self.assertIsInstance(input_expr.func, ast.Name)
        self.assertEqual(input_expr.func.id, "dict")
        self.assertEqual(len(input_expr.args), 1)
        self.assertIsInstance(input_expr.args[0], ast.Name)
        self.assertEqual(input_expr.args[0].id, "W3_SOURCE_INPUT")


if __name__ == "__main__":
    unittest.main()
