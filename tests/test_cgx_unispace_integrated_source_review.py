"""Single-root source convergence across engineering gates and public routes."""
from __future__ import annotations
import unittest
from pathlib import Path
from tools.cgx_unispace_integrated_source_review import (
    PUBLIC_GATEWAY, ReviewHold, build, inspect_gateway,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / PUBLIC_GATEWAY).read_text(encoding="utf-8")

class SourceConvergenceTests(unittest.TestCase):
    def test_real_sources_one_root_with_distinct_route_and_gate_namespaces(self):
        item=build(REPO_ROOT)
        n=item["independent_scope_counts"]
        self.assertEqual(item["canonical_root"],"cgx:root:cognigrex")
        self.assertEqual(n["root_count"],1)
        self.assertEqual(n["workspace_facets"],5)
        self.assertEqual(n["shared_contracts"],12)
        self.assertEqual(n["root_shared_services"],7)
        self.assertEqual(n["engineering_gate_groups"],51)
        self.assertEqual(n["public_route_descriptors"],51)
        self.assertEqual(n["public_missing_404_routes"],6)
        self.assertEqual(n["LOAD_actions"],10)
        self.assertEqual(n["PrintSpace_workstreams"],16)

    def test_real_inputs_retain_all_release_holds(self):
        item=build(REPO_ROOT)
        self.assertEqual(item["state"],"INTEGRATED_SOURCE_REVIEW_NOT_DEPLOYED")
        self.assertEqual(len(item["open_conditions"]),9)
        self.assertTrue(item["original_sources_retained"])
        for key in ("native_root_admitted","source_rights_all_accepted",
                    "archive_deletion_authorised","native_dbr_proved","physical_print_qualified",
                    "public_published","model_training_performed","new_scheduler_created",
                    "new_database_created","authority_transferred"):
            self.assertFalse(item[key],key)

    def test_source_identities_reproducible(self):
        self.assertEqual(build(REPO_ROOT)["review_sha256"],build(REPO_ROOT)["review_sha256"])

    def test_gateway_has_unique_routes_and_six_nonexistent_public_links(self):
        item=inspect_gateway(HTML)
        self.assertEqual(item["route_count"],51)
        self.assertEqual(item["missing_404"],[f"/w{i}-data" for i in range(1,7)])
        self.assertFalse(item["network_fetch_performed"])
        self.assertFalse(item["peer_authenticated"])

    def test_missing_one_route_fails_closed(self):
        changed=HTML.replace('    ["/cgx/fs", "FileSpace", "space-gateway", "filespace", "candidate"],\n',"")
        self.assertNotEqual(changed,HTML)
        with self.assertRaises(ReviewHold):inspect_gateway(changed)

    def test_duplicate_path_fails_closed(self):
        changed=HTML.replace(
            '    ["/cgx/fs", "FileSpace", "space-gateway", "filespace", "candidate"],',
            '    ["/cgx/ds", "FileSpace", "space-gateway", "filespace", "candidate"],')
        self.assertNotEqual(changed,HTML)
        with self.assertRaises(ReviewHold):inspect_gateway(changed)

    def test_missing_route_must_remain_missing(self):
        changed=HTML.replace(
            '["/w3-data", "W3 data (unconnected)", "unconnected", "dataspace", "missing-404"]',
            '["/w3-data", "W3 data (unconnected)", "unconnected", "dataspace", "observed"]')
        self.assertNotEqual(changed,HTML)
        with self.assertRaises(ReviewHold):inspect_gateway(changed)

    def test_broken_missing_link_cannot_admit_other_facet(self):
        changed=HTML.replace(
            '["/w3-data", "W3 data (unconnected)", "unconnected", "dataspace", "missing-404"]',
            '["/w3-data", "W3 data (unconnected)", "unconnected", "admin", "missing-404"]')
        self.assertNotEqual(changed,HTML)
        with self.assertRaises(ReviewHold):inspect_gateway(changed)

    def test_new_fetch_denied(self):
        with self.assertRaises(ReviewHold):inspect_gateway(HTML+"\nfetch('/api/private');")

    def test_new_websocket_denied(self):
        with self.assertRaises(ReviewHold):inspect_gateway(HTML+"\nnew WebSocket('wss://example.com');")

    def test_browser_storage_denied(self):
        with self.assertRaises(ReviewHold):inspect_gateway(HTML+"\nlocalStorage.setItem('a','b')")

    def test_iframe_denied(self):
        with self.assertRaises(ReviewHold):inspect_gateway(HTML+"\n<iframe src='https://example.com'>")

    def test_invalid_source_table_denied(self):
        with self.assertRaises(ReviewHold):
            inspect_gateway(HTML.replace("var routes = [","var routes_removed = ["))

    def test_unbounded_source_denied(self):
        with self.assertRaises(ReviewHold):inspect_gateway(HTML+" "*60000)

    def test_gateway_is_not_a_native_handoff(self):
        item=build(REPO_ROOT)
        gw=item["public_gateway"]
        self.assertFalse(gw["published_pages_created"])
        self.assertFalse(gw["execution_authorised"])
        self.assertTrue(gw["route_discovery_only"])
        self.assertGreater(len(item["source_head_mismatches"]),0)

if __name__=="__main__":
    unittest.main()
