from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mark_iii_dimensional_audit import build_audit, write_audit
from mark_iii_glb_roundtrip_audit import audit
from mark_iii_interactive import build_html
from mark_iii_manufacturing_audit import build_audit as build_manufacturing, write as write_manufacturing
from mark_iii_parametric import export_reference
from mark_iii_serviceability_audit import build_audit as build_serviceability, write as write_serviceability

ROOT = Path(__file__).resolve().parent
P = json.loads((ROOT / "mark_iii_parameters.json").read_text())


class MarkIIIInteractiveTests(unittest.TestCase):
    def test_interactive_surface_contains_original_layout_controls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            export_reference(ROOT / "mark_iii_parameters.json", out)
            rows, summary = build_audit(P)
            write_audit(rows, summary, out)
            service = build_serviceability(P)
            write_serviceability(service, out)
            manufacturing = build_manufacturing(P)
            write_manufacturing(manufacturing, out)
            roundtrip = audit(P, out / "mark_iii_assembly.glb")
            (out / "mark_iii_glb_roundtrip_audit.json").write_text(json.dumps(roundtrip))
            html = build_html(
                out / "mark_iii_assembly.glb",
                out / "mark_iii_component_manifest.json",
                ROOT / "mark_iii_parameters.json",
                out / "mark_iii_verification.json",
                out / "mark_iii_serviceability_audit.json",
                out / "mark_iii_glb_roundtrip_audit.json",
                out / "mark_iii_manufacturing_audit.json",
            )
            self.assertGreater(len(html), 1_200_000)
            self.assertIn("Mark III v0.3", html)
            self.assertIn("Resonator mode", html)
            self.assertIn("Dual interleaved A+B", html)
            self.assertIn("Manufacturing view", html)
            self.assertIn("Manufacturing gates", html)
            self.assertIn("764 named nodes", html)
            self.assertIn("deployment blocked", html.lower())


if __name__ == "__main__":
    unittest.main()
