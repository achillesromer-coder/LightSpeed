"""CGX modular facility spatial/package compiler — review-only deterministic core.

Consumes explicit SI bounds, assets, reserves, dependencies, ports and links.
Uses axis-aligned boxes only (no rotation, load-bearing, transport or life-safety proof).
No source mutation, actuator command, publication or automatic procurement.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

SCHEMA = "CGX-MODULAR-FACILITY-PACKING-CANDIDATE/0.1"
GEOMETRY_STATES = {"SOURCE_VERIFIED", "BOUNDED_ASSUMPTION", "SYNTHETIC_TEST_ONLY", "UNKNOWN"}
FACES = {"x-": (0, 0), "x+": (0, 1), "y-": (1, 0), "y+": (1, 1), "z-": (2, 0), "z+": (2, 1)}
DIRECTIONS = {"IN", "OUT", "BIDIR"}
REQUIRED_ROLES = {"power-comms", "water-sanitation", "shelter-logistics", "first-response", "fabrication-learning"}

def _lengths(value, count=3, *, positive=False):
    if not isinstance(value, (list, tuple)) or len(value) != count or any(
        isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
        or (x <= 0 if positive else x < 0) for x in value
    ):
        raise ValueError("required finite SI dimensions are missing/invalid")
    return tuple(float(x) for x in value)

def _box(data):
    if not isinstance(data, (list, tuple)) or len(data) != 6:
        raise ValueError("AABB must be [x,y,z,dx,dy,dz] in metres")
    pos = _lengths(data[:3])
    size = _lengths(data[3:], positive=True)
    return pos + size

def _inside(box, extent, eps=1e-9):
    return all(box[a] + box[a+3] <= extent[a] + eps for a in range(3))

def _overlap(a, b, eps=1e-9):
    return all(
        min(a[i] + a[i+3], b[i] + b[i+3]) -
        max(a[i], b[i]) > eps for i in range(3)
    )

def _volume(box):
    return box[3] * box[4] * box[5]

def _unique_ids(records, name):
    ids = []
    for r in records:
        k = r.get("id") if isinstance(r, dict) else None
        if not isinstance(k, str) or not k or len(k) > 128:
            raise ValueError(f"{name}: invalid stable id")
        ids.append(k)
    if len(ids) != len(set(ids)):
        raise ValueError(f"{name}: duplicate id")
    return ids

def _finite_mass(x):
    if x is None:
        return None
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0:
        raise ValueError("invalid declared kg mass")
    return float(x)

def compile_facility(source: dict[str, Any]) -> dict[str, Any]:
    """Return a reproducible *candidate* inspection; blockers always prevent release."""
    if not isinstance(source, dict) or source.get("schema") != SCHEMA:
        raise ValueError("unsupported facility source schema")
    if source.get("release_intent") != "REVIEW_ONLY":
        raise ValueError("facility compiler never authorises shipping or construction")
    units = source.get("units")
    catalogue = source.get("component_types")
    connections = source.get("connections", [])
    if not isinstance(units, list) or not (1 <= len(units) <= 64):
        raise ValueError("need 1–64 facility units")
    if not isinstance(catalogue, list) or not (1 <= len(catalogue) <= 2048):
        raise ValueError("need bounded, typed shared component catalogue")
    if not isinstance(connections, list) or len(connections) > 1024:
        raise ValueError("too many proposed connections")
    _unique_ids(units, "units")
    _unique_ids(catalogue, "component types")
    types = {c["id"]: c for c in catalogue}
    issues, holds = [], []
    packs, ports, instmap, dependency_map = [], {}, {}, {}
    raw_instances = []
    for c in catalogue:
        if not isinstance(c.get("source_ref"), str) or not c["source_ref"]:
            raise ValueError("component requires source reference")
        if c.get("qualification") not in GEOMETRY_STATES:
            raise ValueError("component requires explicit evidence class")
    for unit in units:
        uid = unit["id"]
        state = unit.get("geometry_evidence")
        if state not in GEOMETRY_STATES:
            raise ValueError("unit geometry evidence class required")
        origin = _lengths(unit.get("origin_m", [0, 0, 0]))
        envelope = unit.get("internal_envelope_m")
        bounds = _lengths(envelope, positive=True) if envelope is not None else None
        placements = unit.get("placements", [])
        reserves = unit.get("reserves", [])
        pts = unit.get("ports", [])
        if any(not isinstance(x, list) for x in (placements, reserves, pts)):
            raise ValueError("placements, reserves and ports must be arrays")
        _unique_ids(placements, f"{uid}.placements")
        _unique_ids(reserves, f"{uid}.reserves")
        _unique_ids(pts, f"{uid}.ports")
        if not bounds or state == "UNKNOWN":
            holds.append(f"{uid}:HOLD_GEOMETRY_UNVERIFIED")
        solids = []
        total_known_mass = 0.0
        all_masses = True
        for p in placements:
            pid = p["id"]
            if pid in instmap:
                raise ValueError("duplicate instance across facility")
            ctype = p.get("type_id")
            if ctype not in types:
                raise ValueError(f"{pid}: missing catalogue type")
            aabb = _box(p["box_m"]) if p.get("box_m") is not None else None
            if aabb is None:
                holds.append(f"{uid}/{pid}:HOLD_PLACEMENT_GEOMETRY")
            elif bounds:
                if not _inside(aabb, bounds):
                    issues.append(f"{uid}/{pid}:OUTSIDE_INTERNAL_ENVELOPE")
                solids.append(("asset",pid,aabb))
            m = _finite_mass(p.get("mass_kg"))
            if m is None:
                all_masses = False
                holds.append(f"{uid}/{pid}:HOLD_COMPONENT_MASS")
            else:
                total_known_mass += m
            deps = p.get("depends_on", [])
            if not isinstance(deps,list) or any(not isinstance(d,str) for d in deps):
                raise ValueError("dependency must be a list of instance ids")
            dependency_map[pid] = deps
            instmap[pid] = {"unit_id":uid,"type_id":ctype}
            raw_instances.append({"id":pid,"unit_id":uid,"type_id":ctype,"depends_on":deps})
        reserve_sum=0.0
        for reserve in reserves:
            b = _box(reserve["box_m"]) if reserve.get("box_m") is not None else None
            if b is None:
                holds.append(f"{uid}/{reserve['id']}:HOLD_RESERVED_GEOMETRY")
                continue
            if bounds and not _inside(b,bounds):
                issues.append(f"{uid}/{reserve['id']}:RESERVE_OUTSIDE_ENVELOPE")
            solids.append(("reserved",reserve["id"],b))
            reserve_sum += _volume(b)
            if reserve.get("kind") not in {"expansion","circulation","service_access","safety_buffer","connection_bay"}:
                raise ValueError("unclassified reserved volume")
        for i,a in enumerate(solids):
            for b in solids[i+1:]:
                if _overlap(a[2],b[2]):
                    issues.append(f"{uid}:INTERSECTION:{a[0]}:{a[1]}:{b[0]}:{b[1]}")
        occupied = sum(_volume(box) for k,_,box in solids if k=="asset")
        if bounds:
            volume=math.prod(bounds)
            remainder=volume-occupied-reserve_sum
            if remainder < -1e-8:
                issues.append(f"{uid}:NEGATIVE_FREE_VOLUME")
        else:
            volume=None
            remainder=None
        tare = _finite_mass(unit.get("tare_kg"))
        maxgross = _finite_mass(unit.get("max_gross_kg"))
        total = tare + total_known_mass if tare is not None and all_masses else None
        if total is None:
            holds.append(f"{uid}:HOLD_GROSS_MASS")
        elif maxgross is not None and total > maxgross:
            issues.append(f"{uid}:EXCEEDS_GROSS_MASS_LIMIT")
        if maxgross is None:
            holds.append(f"{uid}:HOLD_TRANSPORT_GROSS_LIMIT")
        if not unit.get("shipping_envelope_m"):
            holds.append(f"{uid}:HOLD_SHIPPING_ENVELOPE")
            shipping=None
        else:
            shipping = _lengths(unit["shipping_envelope_m"],positive=True)
        if bounds and shipping and any(shipping[i] < bounds[i] for i in range(3)):
            issues.append(f"{uid}:SHIPPING_ENVELOPE_SMALLER_THAN_INTERIOR")
        for port in pts:
            port_id=port["id"]
            point=_lengths(port.get("local_xyz_m"))
            face=port.get("face")
            if face not in FACES or not bounds:
                holds.append(f"{uid}/{port_id}:HOLD_PORT_FACE_OR_GEOMETRY")
            else:
                ax,end=FACES[face]
                expected=0.0 if end==0 else bounds[ax]
                if abs(point[ax]-expected)>1e-8 or any(point[j]>bounds[j]+1e-8 for j in range(3)):
                    issues.append(f"{uid}/{port_id}:PORT_NOT_ON_DECLARED_FACE")
            if not isinstance(port.get("medium"),str) or not port["medium"]:
                raise ValueError("port medium required")
            if not isinstance(port.get("standard_ref"),str) or not port["standard_ref"]:
                holds.append(f"{uid}/{port_id}:HOLD_CONNECTOR_STANDARD")
            direction=port.get("direction")
            if direction not in DIRECTIONS:
                raise ValueError("port direction unknown")
            ports[f"{uid}/{port_id}"] = {
                "medium":port["medium"], "direction":direction, "family":port.get("family"),
                "xyz_world_m": tuple(point[k]+origin[k] for k in range(3)),
                "standard_ref":port.get("standard_ref")}
        packs.append({
            "id":uid, "function":unit.get("function"), "geometry_evidence":state,
            "internal_m3":volume, "embedded_asset_m3":occupied if bounds else None,
            "reserved_m3":reserve_sum if bounds else None, "remaining_unallocated_m3":remainder,
            "known_gross_kg":total, "shipping_envelope_m":shipping,
            "candidate_instances":[p["id"] for p in placements],
            "port_ids":[p["id"] for p in pts]
        })
    for pid,deps in dependency_map.items():
        for dep in deps:
            if dep not in instmap:
                issues.append(f"{pid}:MISSING_ASSEMBLY_DEPENDENCY:{dep}")
            elif dep==pid:
                issues.append(f"{pid}:SELF_DEPENDENCY")
    # cycle detection without an independent package manager
    temp,done=set(),set()
    def visit(n):
        if n in done:return
        if n in temp:
            issues.append(f"ASSEMBLY_DEPENDENCY_CYCLE:{n}")
            return
        temp.add(n)
        for x in dependency_map[n]:
            if x in dependency_map:visit(x)
        temp.remove(n)
        done.add(n)
    for n in dependency_map:visit(n)
    edge_summaries=[]
    for idx,e in enumerate(connections):
        if not isinstance(e,dict):
            raise ValueError("connection must be object")
        a,b=e.get("a"),e.get("b")
        if not isinstance(a,str) or not isinstance(b,str) or a==b:
            raise ValueError("connections need distinct stable endpoints")
        if a not in ports or b not in ports:
            issues.append(f"LINK-{idx}:UNREGISTERED_PORT")
            continue
        aa,bb=ports[a],ports[b]
        if aa["medium"]!=bb["medium"] or aa["family"]!=bb["family"]:
            issues.append(f"LINK-{idx}:SERVICE_FAMILY_MISMATCH")
        if aa["direction"]==bb["direction"] and aa["direction"]!="BIDIR":
            issues.append(f"LINK-{idx}:DIRECTION_CONFLICT")
        if not aa["standard_ref"] or not bb["standard_ref"]:
            holds.append(f"LINK-{idx}:HOLD_PORT_STANDARD")
        elif aa["standard_ref"]!=bb["standard_ref"]:
            issues.append(f"LINK-{idx}:CONNECTOR_STANDARD_MISMATCH")
        distance=math.dist(aa["xyz_world_m"],bb["xyz_world_m"])
        tol=e.get("alignment_tolerance_m")
        if tol is None:
            holds.append(f"LINK-{idx}:HOLD_ALIGNMENT_TOLERANCE")
        else:
            t=_lengths([tol],count=1)[0]
            if distance>t+1e-9:
                issues.append(f"LINK-{idx}:UNALIGNED_PORTS")
        holds.append(f"LINK-{idx}:HOLD_ACTUAL_PIPE_CABLE_HOSE_ROUTING_AND_COMMISSIONING")
        edge_summaries.append({"a":a,"b":b,"medium":aa["medium"],"port_distance_m":distance,
                               "alignment_tolerance_m":tol,"physical_mating_qualified":False})
    if source.get("site") is None:
        holds.append("HOLD_SITE_TOPOGRAPHY_ENVIRONMENT_RIGHTS")
    for domain in ("structural","lifting","fire","potable_water","electrical","sanitation","clinical",
                   "transport","accessibility","weather","commissioning"):
        holds.append("HOLD_DOMAIN_QUALIFICATION:"+domain.upper())
    all_required_roles=REQUIRED_ROLES.issubset({p["function"] for p in packs})
    if not all_required_roles:
        holds.append("HOLD_PROPOSED_FIVE_FUNCTION_COVERAGE")
    return {
        "schema":"CGX-MODULAR-FACILITY-REVIEW-RESULT/0.1",
        "state":"HOLD" if issues or holds else "SOURCE_CANDIDATE_ONLY",
        "construction_authorised":False,"shipment_authorised":False,"commissioning_authorised":False,
        "source_unchanged":True,"unit_count":len(packs),"component_type_count":len(types),
        "component_instance_count":len(raw_instances),"units":packs,
        "shared_component_types":{k:sum(p["type_id"]==k for p in raw_instances) for k in sorted(types)},
        "linked_services":edge_summaries,"issues":sorted(set(issues)),"holds":sorted(set(holds)),
        "domain_owner_refs":source.get("domain_owner_refs",[]),
        "next_required_proofs":["native CAD geometry and datums","mass, CoG and lashing plan",
        "structural and service installation constraints","actual transport dimensions/route limits",
        "rated connector and commissioning evidence","site safety and regulatory approvals"],
        "notes":["AABB fit and nominal empty volume are not proof of usable access, structural support or payload safety.",
         "All dimensions are SI and are never inferred from InterSol proxy mesh units.",
         "Packed state versus deployed state require separately grounded configuration and measurements.",
         "Existing CCC type reused across instances; no source part/catalogue cloning."]
    }
