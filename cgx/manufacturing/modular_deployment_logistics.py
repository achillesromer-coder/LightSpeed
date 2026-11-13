"""CGX modular facility logistics compiler — one review-only source graph.

Builds reused CCC-type BOM, instance pick lists, installation order, shipping
holds, site/commissioning gates and Type1 drawing requirements. No purchasing,
manufacturing, actual freight quote or regulatory/safety certification.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from .modular_facility_packing import compile_facility

REQUIRED_DRAWINGS = (
    "T1-00_general_arrangement","T1-01_geometry_sections",
    "T1-02_assembly_exploded","T1-03_interfaces_services",
    "T1-04_materials_layers","T1-05_operating_envelope",
    "T1-06_instrumentation_state","T1-07_evidence_unknowns"
)

def build_deployment_review(plan: dict) -> dict:
    g = compile_facility(plan)
    types = {x["id"]:x for x in plan["component_types"]}
    instances={}
    deps={}
    perunit=defaultdict(list)
    for u in plan["units"]:
        for p in u.get("placements",[]):
            instances[p["id"]]=p
            deps[p["id"]]=set(p.get("depends_on",[]))
            perunit[u["id"]].append(p["id"])
    # The geometric solver separately rejects cycles and dangling deps.
    pending={k:set(v) for k,v in deps.items()}
    order=[]
    while pending:
        ready=sorted(k for k,values in pending.items() if not values)
        if not ready:
            break
        for k in ready:
            order.append(k)
            del pending[k]
        for values in pending.values():
            values.difference_update(ready)
    by_type=Counter(p["type_id"] for p in instances.values())
    bom=[]
    procurement_holds=[]
    for type_id,qty in sorted(by_type.items()):
        t=types[type_id]
        if t.get("qualification") != "SOURCE_VERIFIED":
            procurement_holds.append(f"{type_id}:HOLD_UNQUALIFIED_COMPONENT_TYPE")
        # Never treat archetype/source graph as an actual ordered vendor SKU.
        procurement_holds.append(f"{type_id}:HOLD_SUPPLIER_SKU_PURCHASE_TERMS")
        bom.append({
            "component_type_id":type_id,"source_ref":t["source_ref"],
            "distinct_instance_count":qty,
            "allocated_unit_ids":sorted(set(
                unit["id"] for unit in plan["units"] for p in unit["placements"]
                if p["type_id"]==type_id
            )),
            "requested_procurement_qty":None,
            "stock_on_hand":None,"approved_vendor_sku":None,
            "certified_material_trace":None,"unit_price_aud":None,
            "supplier_lead_time_days":None,"export_controls": "REVIEW_REQUIRED",
            "rights_and_license":"REVIEW_REQUIRED",
            "purchasing_authorised":False
        })
    shipping=[]
    for gunit in g["units"]:
        shipping.append({
            "unit_id":gunit["id"],
            "interior_m3":gunit["internal_m3"],
            "shipping_envelope_m":gunit["shipping_envelope_m"],
            "gross_kg":gunit["known_gross_kg"],
            "route_vehicle_and_clearance":None,
            "handling_lift_points_and_wll":None,
            "centre_of_gravity_and_load_distribution":None,
            "lash_resistance":None,
            "dangerous_goods_and_battery_declaration":None,
            "packing_weather_vibration_protection":None,
            "freight_invoice_and_customs":None,
            "offloading_site_foundation":None,
            "transport_ready":False
        })
    units=[]
    for unit in plan["units"]:
        units.append({
            "unit_id":unit["id"],
            "functional_role":unit["function"],
            "equipment_pick_list":list(perunit[unit["id"]]),
            "installation_order": [x for x in order if x in perunit[unit["id"]]],
            "reserved_volume_purpose":sorted({v["kind"] for v in unit.get("reserves",[])}),
            "utilities_mated":False,"site_commissioned":False,"handover_complete":False
        })
    return {
        "schema":"CGX-MODULAR-DEPLOYMENT-LOGISTICS-REVIEW/0.1",
        "state":"HOLD",
        "source_project":plan.get("project_id"),
        "semantic_root":"Cognigrex.cgx",
        "packing_result":g,
        "bill_of_materials":bom,
        "module_pick_lists":units,
        "installation_order_candidate":order,
        "unresolved_dependency_graph":sorted(pending),
        "shipping_units":shipping,
        "drawing_views_required":list(REQUIRED_DRAWINGS),
        "installation_phases":[
            "R0_IDENTIFY_AND_ACQUIRE_WITH_RIGHTS",
            "INSPECT_MEASURED_PARTS_AND_KITS",
            "SIMULATE_SPATIAL_SERVICE_AND_SAFETY_HOLDS",
            "DRY_FIT_ASSEMBLY_AND_INTERLOCK",
            "QUALIFY_UTILITIES_AND_ACCESS",
            "RECEIPTED_PACK_AND_LASH",
            "APPROVED_TRANSPORT_ROUTE_AND_DISPATCH",
            "SITE_SURVEY_FOUNDATION_AND_SAFE_UNLOAD",
            "INSTALL_INTERCONNECTS_AND_SAFETY_TEST",
            "COMMISSION_AND_INDEPENDENT_READBACK",
            "TRAIN_HANDOVER_AND_MAINTENANCE_BASELINE"
        ],
        "supply_chain_holds":sorted(set(procurement_holds)),
        "site_fields_required":["legal_occupancy","weather/flood/fire/geology",
            "foundation/bearing","grid/generation/battery","potable-water/sanitation",
            "local_access/transport","environment/biodiversity","accessibility",
            "operator_training","fire/clinical/public-safety/permits"],
        "qualified_operational_delivery":False,
        "public_publish_authorised":False,
        "source_claim_note":"Römer InterSol facility methodology and component atlas are referenced, not imported as physical container authority.",
        "runtime_note":"All tool execution requires approved LightSpeed capability and signed receipts; this result is pure planning."
    }
