from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mark_iii_glb_roundtrip_audit import audit
from mark_iii_parametric import export_reference

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / "mark_iii_parameters.json").read_text())


class MarkIIIGLBRoundtripTests(unittest.TestCase):
    def test_exported_glb_matches_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            export_reference(ROOT / "mark_iii_parameters.json", out)
            result = audit(P, out / "mark_iii_assembly.glb")
            self.assertEqual(result["status"], "PASS_GLB_ROUNDTRIP_REFERENCE")
            self.assertEqual(result["schema_version"], "mark-iii-glb-roundtrip-v0.3.3")
            self.assertEqual(result["matched_nodes"], 786)
            self.assertFalse(result["missing_nodes"])
            self.assertFalse(result["unexpected_nodes"])
            self.assertFalse(result["failures"])


if __name__ == "__main__":
    unittest.main()
