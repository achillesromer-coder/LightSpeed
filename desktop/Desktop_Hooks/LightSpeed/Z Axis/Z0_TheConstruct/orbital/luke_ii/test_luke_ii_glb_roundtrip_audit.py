from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from luke_ii_glb_roundtrip_audit import audit_glb_roundtrip
from luke_ii_parametric import build_scene

class LukeIIGLBRoundtripAuditTests(unittest.TestCase):
    def test_generated_glb_matches_source_scene_within_container_tolerance(self):
        parameters = json.loads((HERE / "luke_ii_parameters.json").read_text(encoding="utf-8"))
        scene = build_scene(parameters)
        with tempfile.TemporaryDirectory() as directory:
            glb = Path(directory) / "luke_ii_assembly.glb"
            glb.write_bytes(scene.export(file_type="glb"))
            audit = audit_glb_roundtrip(parameters, glb)
        self.assertEqual(audit["status"], "PASS_GLB_ROUNDTRIP_REFERENCE")
        self.assertEqual(audit["matched_nodes"], 1357)
        self.assertFalse(audit["missing_nodes"])
        self.assertFalse(audit["unexpected_nodes"])
        self.assertLessEqual(audit["maximum_observed_errors"]["bounds_m"], audit["linear_tolerance_m"])

if __name__ == "__main__":
    unittest.main()
