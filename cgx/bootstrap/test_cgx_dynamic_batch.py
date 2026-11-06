"""Negative scope tests for deterministic one-call CGX batch review."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).with_name("cgx_dynamic_batch.py")
SPEC = importlib.util.spec_from_file_location("cgx_dynamic_batch", PATH)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class DynamicBatchTests(unittest.TestCase):
    def test_three_source_lanes_are_selected_without_escalation(self):
        got=mod.choose_lanes([
            "cgx/review/unispaceR3Projection.mjs",
            "apps/lightspeed-go/src/cgxFacetProjection.mjs",
            "desktop/LightSpeed_Runtime/lightspeed_runtime/host_owned_receipts.py"
        ])
        for expected in ("git-index","source-manifest","load-registry",
                         "core-node","facet-node","host-evidence",
                         "public-guard","app-check","app-vitest","load-python"):
            self.assertIn(expected,got)
        self.assertEqual(len(got),len(set(got)))
    def test_unknown_deletion_and_source_escape_hold(self):
        for invalid in (["../private/token"],["C:/owner/file"],["/api/owner"],
                        ["apps/lightspeed-go/dist/index.html"],
                        ["apps/lightspeed-go/node_modules/a.js"],
                        ["cgx//bad"],["cgx/../../a"],["data/private.json"],
                        ["cgx/foo","cgx/foo"],[],["cgx/foo"]*301):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                mod.choose_lanes(invalid)
    def test_documentation_change_still_checks_release_guards(self):
        got=mod.choose_lanes(["docs/ls-go-launch/a.md"])
        self.assertIn("public-guard",got)
        self.assertIn("facet-node",got)
    def test_only_allowlisted_tools_and_no_shell_dispatch(self):
        lanes=mod.choose_lanes(["cgx/review/unispaceR3Projection.mjs"])
        jobs=mod.test_commands(lanes)
        self.assertTrue(jobs)
        for ident, argv, cwd in jobs:
            self.assertIsInstance(argv,list)
            self.assertNotIn("powershell",str(argv).lower())
            self.assertNotIn("cmd /c",str(argv).lower())
            self.assertTrue(str(cwd).startswith(str(mod.ROOT)))
            self.assertNotIn("push",argv)
            self.assertNotIn("merge",argv)
            self.assertNotIn("mint",argv)
            self.assertNotIn("deploy",argv)
    def test_git_sha_validation_fails_closed(self):
        for val in ("HEAD;echo hello","origin/main","", "../a", "1"*41):
            with self.subTest(val=val),self.assertRaises(ValueError):
                mod.delta_from_base(val)

if __name__=="__main__":
    unittest.main()
