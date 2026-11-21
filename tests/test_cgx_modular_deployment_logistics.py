"""Supply-chain and field-readiness proof gates for CGX five-unit synthetic example."""
import json
from pathlib import Path
import unittest
from cgx.manufacturing.modular_deployment_logistics import build_deployment_review

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/"cgx"/"manufacturing"/"fixtures"/"five_unit_relief_synthetic_v0_1.json"
def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

class ModularLogisticsTests(unittest.TestCase):
    def test_separate_catalogue_from_part_instances(self):
        o=build_deployment_review(fixture())
        self.assertEqual(len(o["bill_of_materials"]),7)
        self.assertEqual(sum(x["distinct_instance_count"] for x in o["bill_of_materials"]),10)
        self.assertEqual(len(o["shipping_units"]),5)
        self.assertTrue(any(x["component_type_id"]=="sensor-board" and x["distinct_instance_count"]==3 for x in o["bill_of_materials"]))
    def test_required_type1_drawing_series(self):
        o=build_deployment_review(fixture())
        self.assertEqual(len(o["drawing_views_required"]),8)
        self.assertTrue(o["drawing_views_required"][0].startswith("T1-00"))
        self.assertTrue(o["drawing_views_required"][-1].startswith("T1-07"))
    def test_no_physical_shipment_without_verified_data(self):
        o=build_deployment_review(fixture())
        self.assertFalse(o["qualified_operational_delivery"])
        self.assertFalse(o["public_publish_authorised"])
        self.assertTrue(all(not item["transport_ready"] for item in o["shipping_units"]))
        self.assertTrue(all(item["gross_kg"] is None for item in o["shipping_units"]))
        self.assertTrue(all(item["approved_vendor_sku"] is None for item in o["bill_of_materials"]))
    def test_assembly_dependencies_topologically_ordered(self):
        s=fixture()
        a=s["units"][0]["placements"][0]["id"]
        b=s["units"][1]["placements"][0]
        b["depends_on"].append(a)
        o=build_deployment_review(s)
        self.assertLess(o["installation_order_candidate"].index(a),o["installation_order_candidate"].index(b["id"]))
        self.assertEqual(o["unresolved_dependency_graph"],[])
    def test_cycle_remains_unresolved(self):
        s=fixture()
        a=s["units"][0]["placements"][0]
        b=s["units"][1]["placements"][0]
        a["depends_on"]=[b["id"]]
        b["depends_on"]=[a["id"]]
        o=build_deployment_review(s)
        self.assertGreater(len(o["unresolved_dependency_graph"]),0)
        self.assertTrue(any("CYCLE" in issue for issue in o["packing_result"]["issues"]))
    def test_no_false_supplier_or_procurement_from_generic_archetype(self):
        o=build_deployment_review(fixture())
        self.assertTrue(any("SUPPLIER_SKU_PURCHASE_TERMS" in h for h in o["supply_chain_holds"]))
        self.assertTrue(all(not p["purchasing_authorised"] for p in o["bill_of_materials"]))
    def test_reserved_expansion_is_retained_for_installers(self):
        o=build_deployment_review(fixture())
        self.assertTrue(all("expansion" in m["reserved_volume_purpose"] for m in o["module_pick_lists"]))
        self.assertTrue(all("circulation" in m["reserved_volume_purpose"] for m in o["module_pick_lists"]))
        self.assertTrue(all("service_access" in m["reserved_volume_purpose"] for m in o["module_pick_lists"]))
if __name__=="__main__":
    unittest.main()
