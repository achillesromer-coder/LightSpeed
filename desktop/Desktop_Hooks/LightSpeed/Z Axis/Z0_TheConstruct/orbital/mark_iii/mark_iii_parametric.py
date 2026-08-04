#!/usr/bin/env python3
"""Generate the Mark III v0.2 serviceable modular reference assembly.

This is a spatial/configuration reference. It is not validated hardware, a build
manual, a safety certification or a performance model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import trimesh

from mark_iii_geometry_fingerprint import QUANTIZATION_METRES, semantic_geometry_fingerprint
from mark_iii_manifest_fingerprint import canonical_manifest_sha256

ROOTS = {"PRIMARY_STRUCTURE", "ILLUSTRATIVE_REFERENCE_ROOT"}

FAMILY_COLORS = {
    "primary_structure": [136, 145, 156, 255],
    "shell_panel": [155, 163, 172, 255],
    "solar_hull_skin": [78, 111, 126, 255],
    "fastener": [92, 99, 109, 255],
    "coupler": [101, 115, 133, 255],
    "coupler_latch": [132, 115, 89, 255],
    "coupler_bridge": [84, 130, 128, 255],
    "process_tunnel": [111, 118, 128, 255],
    "sample_cartridge": [148, 126, 105, 255],
    "solenoid": [132, 93, 74, 255],
    "resonator": [113, 94, 140, 255],
    "energy": [122, 111, 70, 255],
    "controller": [78, 105, 139, 255],
    "sensor": [82, 139, 119, 255],
    "damping": [112, 122, 137, 255],
    "comms": [78, 125, 150, 255],
    "cable_tray": [72, 83, 96, 255],
    "harness": [106, 114, 123, 255],
    "arm": [115, 126, 139, 255],
    "arm_joint": [131, 119, 106, 255],
    "arm_actuator": [128, 90, 79, 255],
    "service_clearance": [79, 129, 171, 50],
    "removal_path": [188, 151, 73, 55],
    "connector_access": [118, 161, 120, 55],
    "cable_bend_space": [149, 106, 167, 55],
    "array_guide": [92, 143, 158, 45],
    "field_guide": [151, 105, 174, 45],
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_parameters(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rotation_z_to_vector(vector: Iterable[float]) -> np.ndarray:
    vector = np.asarray(vector, dtype=float)
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-12:
        return np.eye(4)
    return trimesh.geometry.align_vectors([0.0, 0.0, 1.0], vector / norm)


def cylinder_x(radius: float, length: float, center: Iterable[float], sections: int = 32) -> trimesh.Trimesh:
    mesh = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    transform = rotation_z_to_vector([1.0, 0.0, 0.0])
    transform[:3, 3] = np.asarray(center, dtype=float)
    mesh.apply_transform(transform)
    return mesh


def annulus_x(r_min: float, r_max: float, length: float, center: Iterable[float], sections: int = 48) -> trimesh.Trimesh:
    mesh = trimesh.creation.annulus(r_min=r_min, r_max=r_max, height=length, sections=sections)
    transform = rotation_z_to_vector([1.0, 0.0, 0.0])
    transform[:3, 3] = np.asarray(center, dtype=float)
    mesh.apply_transform(transform)
    return mesh


def sphere(radius: float, center: Iterable[float], subdivisions: int = 2) -> trimesh.Trimesh:
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    mesh.apply_translation(np.asarray(center, dtype=float))
    return mesh


def box(extents: Iterable[float], center: Iterable[float], rotation_x: float = 0.0) -> trimesh.Trimesh:
    mesh = trimesh.creation.box(extents=np.asarray(extents, dtype=float))
    if rotation_x:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(rotation_x, [1.0, 0.0, 0.0]))
    mesh.apply_translation(np.asarray(center, dtype=float))
    return mesh


def cylinder_between(a: Iterable[float], b: Iterable[float], radius: float, sections: int = 20) -> trimesh.Trimesh:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    vector = b - a
    length = float(np.linalg.norm(vector))
    mesh = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    transform = rotation_z_to_vector(vector)
    transform[:3, 3] = (a + b) / 2.0
    mesh.apply_transform(transform)
    return mesh


def annular_sector_x(x0: float, x1: float, r0: float, r1: float, a0: float, a1: float) -> trimesh.Trimesh:
    """Closed eight-vertex annular-sector prism aligned to the x-axis."""
    points = []
    for x in (x0, x1):
        for r, a in ((r0, a0), (r1, a0), (r1, a1), (r0, a1)):
            points.append([x, r * math.cos(a), r * math.sin(a)])
    faces = [
        [0, 3, 2], [0, 2, 1],
        [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4],
        [1, 2, 6], [1, 6, 5],
        [2, 3, 7], [2, 7, 6],
        [3, 0, 4], [3, 4, 7],
    ]
    mesh = trimesh.Trimesh(vertices=np.asarray(points), faces=np.asarray(faces), process=True)
    if mesh.volume < 0:
        mesh.invert()
    return mesh


def apply_color(mesh: trimesh.Trimesh, family: str) -> None:
    color = FAMILY_COLORS.get(family, [125, 133, 143, 255])
    mesh.visual.face_colors = np.tile(np.asarray(color, dtype=np.uint8), (len(mesh.faces), 1))


def record_for(name: str, family: str, subsystem: str, evidence_state: str, review_gate: str,
               source_basis: str, physical: bool, maintainable: bool, cable_required: bool,
               attachment_parent: str, cable_route: str = "", service_clearance: str = "",
               removal_path: str = "", panel_access: str = "", array_configuration: str = "") -> dict[str, Any]:
    return {
        "node_name": name,
        "family": family,
        "subsystem": subsystem,
        "evidence_state": evidence_state,
        "review_gate": review_gate,
        "source_basis": source_basis,
        "physical": physical,
        "maintainable": maintainable,
        "cable_required": cable_required,
        "attachment_parent": attachment_parent,
        "cable_route": cable_route,
        "service_clearance": service_clearance,
        "removal_path": removal_path,
        "panel_access": panel_access,
        "array_configuration": array_configuration,
    }


def add_node(scene: trimesh.Scene, records: list[dict[str, Any]], mesh: trimesh.Trimesh, name: str,
             family: str, subsystem: str, evidence_state: str, review_gate: str, source_basis: str,
             physical: bool = True, maintainable: bool = False, cable_required: bool = False,
             attachment_parent: str = "PRIMARY_STRUCTURE", cable_route: str = "",
             service_clearance: str = "", removal_path: str = "", panel_access: str = "",
             array_configuration: str = "") -> None:
    if name in scene.geometry:
        raise ValueError(f"Duplicate node: {name}")
    apply_color(mesh, family)
    scene.add_geometry(mesh, node_name=name, geom_name=name)
    record = record_for(name, family, subsystem, evidence_state, review_gate, source_basis, physical,
                        maintainable, cable_required, attachment_parent, cable_route,
                        service_clearance, removal_path, panel_access, array_configuration)
    record.update({
        "bounds_m": np.round(mesh.bounds, 9).tolist(),
        "extents_m": np.round(mesh.extents, 9).tolist(),
        "centroid_m": np.round(mesh.centroid, 9).tolist(),
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "volume_m3": round(abs(float(mesh.volume)), 12),
    })
    records.append(record)


def add_envelope(scene: trimesh.Scene, records: list[dict[str, Any]], mesh: trimesh.Trimesh, name: str,
                 family: str, subsystem: str, parent: str, evidence: str, review_gate: str,
                 source_basis: str, array_configuration: str = "") -> None:
    add_node(scene, records, mesh, name, family, subsystem, evidence, review_gate, source_basis,
             physical=False, maintainable=False, attachment_parent=parent,
             array_configuration=array_configuration)


def build_shell(scene: trimesh.Scene, records: list[dict[str, Any]], p: dict[str, Any]) -> None:
    d = p["derived_configuration"]
    sector_count = p["source_parameters"]["shell_sector_count"]["value"]
    axial_count = d["axial_panel_count"]
    body_len = d["main_body_length_m"]
    gap_a = math.radians(2.0)
    for axial in range(axial_count):
        x0 = -body_len / 2 + axial * body_len / axial_count + 0.004
        x1 = -body_len / 2 + (axial + 1) * body_len / axial_count - 0.004
        for sector in range(sector_count):
            center_a = 2 * math.pi * sector / sector_count
            a0 = center_a - math.pi / sector_count + gap_a
            a1 = center_a + math.pi / sector_count - gap_a
            panel = f"M3_SHELL_PANEL_A{axial+1:02d}_S{sector+1:02d}"
            clearance = f"M3_SERVICE_CLEARANCE_PANEL_A{axial+1:02d}_S{sector+1:02d}"
            removal = f"M3_REMOVAL_PATH_PANEL_A{axial+1:02d}_S{sector+1:02d}"
            mesh = annular_sector_x(x0, x1, d["structural_panel_inner_radius_m"], d["structural_panel_outer_radius_m"], a0, a1)
            add_node(scene, records, mesh, panel, "shell_panel", "structure", "DERIVED_SPATIAL_REFERENCE",
                     "Panel material, tolerance, seam, fastener and load review", "Mark III six-segment shell topology; three axial service zones derived",
                     maintainable=True, attachment_parent="M3_LONGITUDINAL_RAIL_%02d" % (sector+1),
                     service_clearance=clearance, removal_path=removal, panel_access=panel)
            mid_a = (a0 + a1) / 2
            radial = d["structural_panel_outer_radius_m"] + 0.045
            add_envelope(scene, records,
                         box([x1-x0, 0.07, 0.025], [(x0+x1)/2, radial*math.cos(mid_a), radial*math.sin(mid_a)], rotation_x=mid_a),
                         clearance, "service_clearance", "serviceability", panel, "DERIVED_MAINTENANCE_ENVELOPE",
                         "Confirm technician/tool access and adjacent interference", "Derived panel access volume")
            p0 = np.array([(x0+x1)/2, (d["structural_panel_outer_radius_m"]+0.01)*math.cos(mid_a), (d["structural_panel_outer_radius_m"]+0.01)*math.sin(mid_a)])
            p1 = np.array([(x0+x1)/2, (d["structural_panel_outer_radius_m"]+0.11)*math.cos(mid_a), (d["structural_panel_outer_radius_m"]+0.11)*math.sin(mid_a)])
            add_envelope(scene, records, cylinder_between(p0, p1, 0.012, 12), removal, "removal_path", "serviceability", panel,
                         "DERIVED_MAINTENANCE_ENVELOPE", "Confirm removal direction and handling fixture", "Derived panel removal vector")
            for fidx, x in enumerate((x0+0.018, x1-0.018), start=1):
                r = d["structural_panel_outer_radius_m"] - 0.004
                add_node(scene, records, cylinder_between([x, (r-0.003)*math.cos(mid_a), (r-0.003)*math.sin(mid_a)],
                                                          [x, (r+0.003)*math.cos(mid_a), (r+0.003)*math.sin(mid_a)], 0.0015, 12),
                         f"M3_PANEL_FASTENER_A{axial+1:02d}_S{sector+1:02d}_F{fidx:02d}", "fastener", "structure",
                         "PROVISIONAL_INTERFACE_REFERENCE", "Select qualified captive fastener and insert system",
                         "Explicit fastener reference; dimensions provisional", maintainable=True, attachment_parent=panel, panel_access=panel)
    # Six continuous solar-hull outer skins.
    for sector in range(sector_count):
        center_a = 2 * math.pi * sector / sector_count
        a0 = center_a - math.pi / sector_count + gap_a
        a1 = center_a + math.pi / sector_count - gap_a
        name = f"M3_SOLAR_HULL_SKIN_S{sector+1:02d}"
        add_node(scene, records,
                 annular_sector_x(-body_len/2+0.002, body_len/2-0.002, d["solar_skin_inner_radius_m"], d["solar_skin_outer_radius_m"], a0, a1),
                 name, "solar_hull_skin", "solar_hull_interface", "SOURCE_ALIGNED_TOPOLOGY",
                 "Coupon, panel, adhesion, thermal-cycle, EMI and electrical review",
                 "Solar Hull v0.2 functional-skin interface; efficiency claims excluded", maintainable=True,
                 attachment_parent=f"M3_SHELL_PANEL_A02_S{sector+1:02d}", panel_access=f"M3_SHELL_PANEL_A02_S{sector+1:02d}")
    # Rails and bulkhead rings.
    for sector in range(sector_count):
        a = 2 * math.pi * sector / sector_count
        name = f"M3_LONGITUDINAL_RAIL_{sector+1:02d}"
        add_node(scene, records, box([body_len-0.015, 0.012, 0.018], [0, 0.145*math.cos(a), 0.145*math.sin(a)], rotation_x=a),
                 name, "primary_structure", "structure", "DERIVED_SPATIAL_REFERENCE",
                 "Structural sizing, joining, load path and tolerance review", "Derived rail required to attach panels and internal mounts",
                 maintainable=True, attachment_parent="PRIMARY_STRUCTURE")
    for idx, x in enumerate((-0.30, -0.10, 0.10, 0.30), start=1):
        add_node(scene, records, annulus_x(0.118, 0.151, 0.012, [x,0,0], 48), f"M3_BULKHEAD_RING_{idx:02d}",
                 "primary_structure", "structure", "DERIVED_SPATIAL_REFERENCE",
                 "Structural, vibration and access-opening review", "Derived internal ring for panel, rail and bay support",
                 maintainable=True, attachment_parent="PRIMARY_STRUCTURE")


def build_couplers(scene: trimesh.Scene, records: list[dict[str, Any]], p: dict[str, Any]) -> None:
    d = p["derived_configuration"]
    for end, sign in (("FRONT", -1), ("REAR", 1)):
        x = sign * (p["source_parameters"]["module_length_m"]["value"]/2 - d["coupler_length_m"]/2)
        ring = f"M3_COUPLER_RING_{end}"
        clearance = f"M3_SERVICE_CLEARANCE_COUPLER_{end}"
        removal = f"M3_REMOVAL_PATH_COUPLER_{end}"
        add_node(scene, records, annulus_x(0.11, 0.16, d["coupler_length_m"], [x,0,0], 64), ring,
                 "coupler", "coupling", "SOURCE_ALIGNED_TOPOLOGY", "Coupler loads, sealing, alignment and cycle-life review",
                 "Mark III source envelope and linkable coupling topology", maintainable=True, attachment_parent="PRIMARY_STRUCTURE",
                 service_clearance=clearance, removal_path=removal)
        add_envelope(scene, records, cylinder_x(0.20, 0.08, [x + sign*0.045,0,0], 40), clearance,
                     "service_clearance", "serviceability", ring, "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm coupling tool and adjacent-module clearance", "Derived coupling service envelope")
        add_envelope(scene, records, cylinder_x(0.13, 0.16, [x + sign*0.10,0,0], 32), removal,
                     "removal_path", "serviceability", ring, "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm ring removal and support tooling", "Derived axial removal path")
        # Four latches per end = eight source coupling nodes total.
        for idx in range(4):
            a = idx * math.pi / 2
            c = [x, 0.145*math.cos(a), 0.145*math.sin(a)]
            latch = f"M3_COUPLER_LATCH_{end}_{idx+1:02d}"
            add_node(scene, records, box([0.025,0.018,0.035], c, rotation_x=a), latch, "coupler_latch", "coupling",
                     "SOURCE_ALIGNED_TOPOLOGY", "Latch strength, preload, lock indication and release review",
                     "Eight interlocking coupling nodes distributed four per end", maintainable=True, attachment_parent=ring,
                     panel_access=ring)
        for idx, a in enumerate((math.pi/4, 5*math.pi/4), start=1):
            add_node(scene, records, box([0.03,0.012,0.025], [x,0.13*math.cos(a),0.13*math.sin(a)], rotation_x=a),
                     f"M3_ALIGNMENT_KEY_{end}_{idx:02d}", "coupler", "coupling", "PROVISIONAL_INTERFACE_REFERENCE",
                     "Alignment key tolerance, damage and blind-mate review", "Derived keying feature for repeatable orientation",
                     maintainable=True, attachment_parent=ring)
        for idx, a in enumerate((3*math.pi/4, 7*math.pi/4), start=1):
            bridge = f"M3_COUPLER_BRIDGE_{end}_{idx:02d}"
            route = f"M3_HARNESS_TRUNK_{idx:02d}"
            access = f"M3_CONNECTOR_ACCESS_COUPLER_{end}_{idx:02d}"
            add_node(scene, records, box([0.03,0.018,0.025], [x,0.128*math.cos(a),0.128*math.sin(a)], rotation_x=a),
                     bridge, "coupler_bridge", "coupling", "PROVISIONAL_INTERFACE_REFERENCE",
                     "Blind-mate connector, isolation, grounding, sealing and current review", "Derived power/data bridge interface",
                     maintainable=True, cable_required=True, attachment_parent=ring, cable_route=route,
                     service_clearance=access, panel_access=ring)
            add_envelope(scene, records, box([0.06,0.04,0.05], [x+sign*0.04,0.128*math.cos(a),0.128*math.sin(a)], rotation_x=a),
                         access, "connector_access", "serviceability", bridge, "DERIVED_MAINTENANCE_ENVELOPE",
                         "Confirm connector hand/tool access and bend relief", "Derived connector access volume")


def build_internal_systems(scene: trimesh.Scene, records: list[dict[str, Any]], p: dict[str, Any]) -> None:
    d = p["derived_configuration"]
    # Process tunnel and cartridge.
    add_node(scene, records, annulus_x(d["process_tunnel_inner_radius_m"], d["process_tunnel_outer_radius_m"], 0.62, [0,0,0], 48),
             "M3_PROCESS_TUNNEL", "process_tunnel", "process_module", "SOURCE_ALIGNED_TOPOLOGY",
             "Sample containment, pressure/vacuum, material and cleaning review", "Mark III central processing path topology",
             maintainable=True, attachment_parent="M3_BULKHEAD_RING_02")
    cart = "M3_SAMPLE_CHAMBER_CARTRIDGE"
    add_node(scene, records, cylinder_x(d["sample_cartridge_radius_m"], d["sample_cartridge_length_m"], [0,0,0], 36),
             cart, "sample_cartridge", "process_module", "PROVISIONAL_INTERFACE_REFERENCE",
             "Sample compatibility, assay protocol, containment and cleaning review", "Mark 1P removable sample-chamber lineage",
             maintainable=True, cable_required=True, attachment_parent="M3_PROCESS_TUNNEL", cable_route="M3_HARNESS_TRUNK_01",
             service_clearance="M3_SERVICE_CLEARANCE_SAMPLE", removal_path="M3_REMOVAL_PATH_SAMPLE", panel_access="M3_COUPLER_RING_FRONT")
    add_envelope(scene, records, cylinder_x(0.045, 0.24, [0,0,0], 28), "M3_SERVICE_CLEARANCE_SAMPLE",
                 "service_clearance", "serviceability", cart, "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm cartridge handling and isolation clearance", "Derived chamber clearance")
    add_envelope(scene, records, cylinder_x(0.035, 0.36, [-0.25,0,0], 24), "M3_REMOVAL_PATH_SAMPLE",
                 "removal_path", "serviceability", cart, "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm axial extraction through front coupler", "Derived cartridge removal path")
    add_node(scene, records, box([0.035,0.018,0.015], [0.075,0.032,0], 0), "M3_SAMPLE_CONNECTOR",
             "coupler_bridge", "process_module", "PROVISIONAL_INTERFACE_REFERENCE",
             "Select qualified sample sensors and connector", "Derived sensor/data interface",
             maintainable=True, cable_required=True, attachment_parent=cart, cable_route="M3_HARNESS_TRUNK_01",
             service_clearance="M3_CONNECTOR_ACCESS_SAMPLE", panel_access="M3_SHELL_PANEL_A02_S01")
    add_envelope(scene, records, box([0.06,0.05,0.04], [0.09,0.06,0], 0), "M3_CONNECTOR_ACCESS_SAMPLE",
                 "connector_access", "serviceability", "M3_SAMPLE_CONNECTOR", "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm connector access and sample isolation", "Derived access reservation")

    # Six compact solenoid cartridges.
    positions = [(-2.5+i)*d["solenoid_axial_pitch_m"] for i in range(6)]
    for idx, x in enumerate(positions, start=1):
        base = f"M3_SOLENOID_{idx:02d}"
        panel = f"M3_SHELL_PANEL_A{1 if x < -0.11 else 3 if x > 0.11 else 2:02d}_S01"
        route = "M3_HARNESS_TRUNK_01"
        clearance = f"M3_SERVICE_CLEARANCE_SOLENOID_{idx:02d}"
        removal = f"M3_REMOVAL_PATH_SOLENOID_{idx:02d}"
        add_node(scene, records, annulus_x(d["solenoid_inner_radius_m"], d["solenoid_outer_radius_m"], d["solenoid_axial_length_m"], [x,0,0], 40),
                 base, "solenoid", "solenoid_array", "DERIVED_SPATIAL_REFERENCE",
                 "Measured conductor/BOM, current, insulation, thermal and field-map review",
                 "Six source positions; compact axial cartridge resolves envelope conflict M3-CONFLICT-001",
                 maintainable=True, cable_required=True, attachment_parent="M3_PROCESS_TUNNEL", cable_route=route,
                 service_clearance=clearance, removal_path=removal, panel_access=panel)
        add_node(scene, records, annulus_x(0.042,0.055,d["solenoid_axial_length_m"]-0.006,[x,0,0],32),
                 f"{base}_COIL_REFERENCE", "solenoid", "solenoid_array", "QUARANTINED_UNVERIFIED_NOT_USED_FOR_CAPABILITY",
                 "Replace with measured winding and insulation geometry", "Illustrative coil body; no turn/current/field claim",
                 maintainable=True, cable_required=True, attachment_parent=base, cable_route=route, panel_access=panel)
        add_node(scene, records, box([0.025,0.018,0.018],[x,0.067,0],0), f"{base}_MOUNT_BRACKET", "primary_structure",
                 "solenoid_array", "DERIVED_SPATIAL_REFERENCE", "Bracket load, thermal conduction and fastener review",
                 "Derived rail attachment", maintainable=True, attachment_parent="M3_BULKHEAD_RING_02", panel_access=panel)
        add_node(scene, records, box([0.018,0.014,0.014],[x,0.072,0.018],0), f"{base}_CONNECTOR", "coupler_bridge",
                 "solenoid_array", "PROVISIONAL_INTERFACE_REFERENCE", "Connector current, temperature, shielding and strain-relief review",
                 "Derived connector interface", maintainable=True, cable_required=True, attachment_parent=base, cable_route=route,
                 service_clearance=f"M3_CONNECTOR_ACCESS_SOLENOID_{idx:02d}", panel_access=panel)
        add_envelope(scene, records, cylinder_x(0.075,0.085,[x,0,0],28), clearance, "service_clearance", "serviceability", base,
                     "DERIVED_MAINTENANCE_ENVELOPE", "Confirm cartridge tool and thermal-clearance envelope", "Derived solenoid service volume")
        add_envelope(scene, records, cylinder_x(0.065,0.13,[x,0.10,0],24), removal, "removal_path", "serviceability", base,
                     "DERIVED_MAINTENANCE_ENVELOPE", "Confirm radial cartridge removal path", "Derived removal corridor")
        add_envelope(scene, records, box([0.04,0.04,0.04],[x,0.09,0.02],0), f"M3_CONNECTOR_ACCESS_SOLENOID_{idx:02d}",
                     "connector_access", "serviceability", f"{base}_CONNECTOR", "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm connector access and bend relief", "Derived connector access volume")

    # Resonators, energy modules, controller, damping, sensors, comms.
    for idx in range(4):
        a = math.pi/4 + idx*math.pi/2
        x = -0.15 if idx < 2 else 0.15
        c = [x,0.092*math.cos(a),0.092*math.sin(a)]
        name=f"M3_RESONATOR_{idx+1:02d}"; panel=f"M3_SHELL_PANEL_A{1 if x<0 else 3:02d}_S{idx+1:02d}"
        add_node(scene, records, cylinder_between([x-0.035,c[1],c[2]],[x+0.035,c[1],c[2]],0.021,24), name,
                 "resonator", "rfs_module", "SOURCE_ALIGNED_TOPOLOGY", "Measured frequency/acceleration/coupling and assay review",
                 "Four source resonator positions; geometry derived", maintainable=True, cable_required=True,
                 attachment_parent="M3_BULKHEAD_RING_%02d" % (1 if x<0 else 4), cable_route=f"M3_HARNESS_TRUNK_{idx+1:02d}",
                 service_clearance=f"M3_SERVICE_CLEARANCE_RESONATOR_{idx+1:02d}", removal_path=f"M3_REMOVAL_PATH_RESONATOR_{idx+1:02d}", panel_access=panel)
        add_envelope(scene, records, sphere(0.045,c,1), f"M3_SERVICE_CLEARANCE_RESONATOR_{idx+1:02d}", "service_clearance", "serviceability", name,
                     "DERIVED_MAINTENANCE_ENVELOPE", "Confirm resonator isolation and service clearance", "Derived clearance sphere")
        outward=np.array([0,c[1],c[2]]); outward=outward/np.linalg.norm(outward)
        add_envelope(scene, records, cylinder_between(np.array(c),np.array(c)+outward*0.11,0.018,12), f"M3_REMOVAL_PATH_RESONATOR_{idx+1:02d}",
                     "removal_path", "serviceability", name, "DERIVED_MAINTENANCE_ENVELOPE", "Confirm radial replacement path", "Derived removal corridor")

    energy_specs=[("BATTERY_BMS",-0.20,math.pi),("CAPACITOR_01",0.02,math.pi),("CAPACITOR_02",0.20,math.pi)]
    for label,x,a in energy_specs:
        name=f"M3_{label}"; is_batt=label=="BATTERY_BMS"; family="energy"
        ext=[0.12 if is_batt else 0.09,0.055,0.045]
        c=[x,0.105*math.cos(a),0.105*math.sin(a)]
        panel=f"M3_SHELL_PANEL_A{1 if x<-0.11 else 3 if x>0.11 else 2:02d}_S04"
        clearance=f"M3_SERVICE_CLEARANCE_{label}"; removal=f"M3_REMOVAL_PATH_{label}"
        add_node(scene, records, box(ext,c,a), name,family,"free_flow_energy_bus","SOURCE_ALIGNED_TOPOLOGY",
                 "Pulse logs, ESR/DCIR, fault containment, thermal and BMS review",
                 "Source component count; packaging dimensions derived", maintainable=True,cable_required=True,
                 attachment_parent="M3_LONGITUDINAL_RAIL_04",cable_route="M3_HARNESS_TRUNK_03",service_clearance=clearance,
                 removal_path=removal,panel_access=panel)
        add_node(scene, records, box([ext[0]+0.012,0.012,0.018],[x,0.133*math.cos(a),0.133*math.sin(a)],a),f"{name}_MOUNT_RAIL","primary_structure",
                 "free_flow_energy_bus","DERIVED_SPATIAL_REFERENCE","Mount, isolation and thermal-path review","Derived module rail",
                 maintainable=True,attachment_parent="M3_LONGITUDINAL_RAIL_04",panel_access=panel)
        add_node(scene, records, box([0.018,0.015,0.015],[x+ext[0]/2-0.012,0.072*math.cos(a),0.072*math.sin(a)],a),f"{name}_CONNECTOR","coupler_bridge",
                 "free_flow_energy_bus","PROVISIONAL_INTERFACE_REFERENCE","Connector rating, keying, isolation and grounding review","Derived electrical interface",
                 maintainable=True,cable_required=True,attachment_parent=name,cable_route="M3_HARNESS_TRUNK_03",panel_access=panel)
        add_envelope(scene, records, box([ext[0]+0.04,0.09,0.08],c,a),clearance,"service_clearance","serviceability",name,
                     "DERIVED_MAINTENANCE_ENVELOPE","Confirm fault-containment and service access","Derived energy-bay clearance")
        outward=np.array([0,c[1],c[2]])/np.linalg.norm([c[1],c[2]])
        add_envelope(scene, records, box([ext[0]+0.02,0.15,0.07],np.array(c)+outward*0.08,a),removal,"removal_path","serviceability",name,
                     "DERIVED_MAINTENANCE_ENVELOPE","Confirm safe isolated replacement path","Derived energy-module removal volume")

    ctrl="M3_CONTROLLER_DSP"; c=[0.08,0,0.105]
    add_node(scene,records,box([0.11,0.06,0.04],c,0),ctrl,"controller","controls","SOURCE_ALIGNED_TOPOLOGY",
             "Controller hardware, software, EMC, fail-safe and evidence-chain review","One source controller/DSP; packaging derived",
             maintainable=True,cable_required=True,attachment_parent="M3_LONGITUDINAL_RAIL_02",cable_route="M3_HARNESS_TRUNK_02",
             service_clearance="M3_SERVICE_CLEARANCE_CONTROLLER",removal_path="M3_REMOVAL_PATH_CONTROLLER",panel_access="M3_SHELL_PANEL_A02_S02")
    add_envelope(scene,records,box([0.16,0.10,0.08],c,0),"M3_SERVICE_CLEARANCE_CONTROLLER","service_clearance","serviceability",ctrl,
                 "DERIVED_MAINTENANCE_ENVELOPE","Confirm controller cooling and access","Derived controller service volume")
    add_envelope(scene,records,box([0.16,0.12,0.08],[0.08,0,0.19],0),"M3_REMOVAL_PATH_CONTROLLER","removal_path","serviceability",ctrl,
                 "DERIVED_MAINTENANCE_ENVELOPE","Confirm controller removal through shell panel","Derived controller removal path")

    for idx in range(4):
        a=idx*math.pi/2; x=(-0.23,-0.08,0.08,0.23)[idx]
        c=[x,0.105*math.cos(a),0.105*math.sin(a)]; name=f"M3_DAMPING_PLACEHOLDER_{idx+1:02d}"
        add_node(scene,records,cylinder_between([x-0.025,c[1],c[2]],[x+0.025,c[1],c[2]],0.018,20),name,"damping","damping_isolation",
                 "PROVISIONAL_INTERFACE_REFERENCE","Specialist medium, pressure, containment, venting and hazard review","Four source damping placeholders; no medium/pressure claim",
                 maintainable=True,cable_required=True,attachment_parent="M3_BULKHEAD_RING_%02d" % (idx+1),cable_route=f"M3_HARNESS_TRUNK_{idx+1:02d}",
                 service_clearance=f"M3_SERVICE_CLEARANCE_DAMPING_{idx+1:02d}",panel_access=f"M3_SHELL_PANEL_A{1 if x<-.11 else 3 if x>.11 else 2:02d}_S{idx+1:02d}")
        add_envelope(scene,records,sphere(0.04,c,1),f"M3_SERVICE_CLEARANCE_DAMPING_{idx+1:02d}","service_clearance","serviceability",name,
                     "DERIVED_MAINTENANCE_ENVELOPE","Confirm containment and service isolation","Derived damping clearance")

    for idx in range(8):
        a=idx*math.pi/4; x=-0.25+idx*(0.5/7)
        c=[x,0.125*math.cos(a),0.125*math.sin(a)]; name=f"M3_SENSOR_NODE_{idx+1:02d}"
        panel=f"M3_SHELL_PANEL_A{1 if x<-.11 else 3 if x>.11 else 2:02d}_S{(idx%6)+1:02d}"
        add_node(scene,records,box([0.018,0.014,0.014],c,a),name,"sensor","sensor_comms","SOURCE_ALIGNED_TOPOLOGY",
                 "Calibration, placement, synchronization, bandwidth and EMI review","Eight source sensor nodes; locations derived",
                 maintainable=True,cable_required=True,attachment_parent=panel,cable_route=f"M3_HARNESS_TRUNK_{(idx%4)+1:02d}",
                 service_clearance=f"M3_CONNECTOR_ACCESS_SENSOR_{idx+1:02d}",panel_access=panel)
        add_envelope(scene,records,box([0.045,0.035,0.035],c,a),f"M3_CONNECTOR_ACCESS_SENSOR_{idx+1:02d}","connector_access","serviceability",name,
                     "DERIVED_MAINTENANCE_ENVELOPE","Confirm calibration and connector access","Derived sensor access volume")
    add_node(scene,records,cylinder_between([0.18,0,0.15],[0.18,0,0.26],0.006,16),"M3_COMMS_ANTENNA","comms","sensor_comms","SOURCE_ALIGNED_TOPOLOGY",
             "RF, EMC, deployment, grounding and environmental review","One source comms interface; antenna geometry provisional",
             maintainable=True,cable_required=True,attachment_parent="M3_SHELL_PANEL_A03_S02",cable_route="M3_HARNESS_TRUNK_02",
             service_clearance="M3_SERVICE_CLEARANCE_COMMS",removal_path="M3_REMOVAL_PATH_COMMS",panel_access="M3_SHELL_PANEL_A03_S02")
    add_envelope(scene,records,cylinder_between([0.18,0,0.13],[0.18,0,0.30],0.025,16),"M3_SERVICE_CLEARANCE_COMMS","service_clearance","serviceability","M3_COMMS_ANTENNA",
                 "DERIVED_MAINTENANCE_ENVELOPE","Confirm antenna articulation and keep-out","Derived RF/mechanical clearance")
    add_envelope(scene,records,cylinder_between([0.18,0,0.18],[0.18,0,0.35],0.015,12),"M3_REMOVAL_PATH_COMMS","removal_path","serviceability","M3_COMMS_ANTENNA",
                 "DERIVED_MAINTENANCE_ENVELOPE","Confirm antenna replacement path","Derived antenna removal corridor")


def build_harnesses(scene: trimesh.Scene, records: list[dict[str, Any]], p: dict[str, Any]) -> None:
    d=p["derived_configuration"]
    tray_radius=d["cable_tray_radius_m"]
    for idx,a in enumerate((0,math.pi/2,math.pi,3*math.pi/2),start=1):
        c=[0,tray_radius*math.cos(a),tray_radius*math.sin(a)]
        tray=f"M3_CABLE_TRAY_{idx:02d}"; trunk=f"M3_HARNESS_TRUNK_{idx:02d}"; bend=f"M3_CABLE_BEND_SPACE_{idx:02d}"
        add_node(scene,records,box([0.59,d["cable_tray_section_m"][0],d["cable_tray_section_m"][1]],c,a),tray,"cable_tray","electrical_data",
                 "DERIVED_SPATIAL_REFERENCE","Cable fill, support spacing, grounding, thermal and EMI separation review","Derived longitudinal tray inside source envelope",
                 maintainable=True,attachment_parent=f"M3_LONGITUDINAL_RAIL_{idx:02d}",panel_access=f"M3_SHELL_PANEL_A02_S{idx:02d}")
        add_node(scene,records,cylinder_between([-0.285,c[1],c[2]],[0.285,c[1],c[2]],0.0045,14),trunk,"harness","electrical_data",
                 "DERIVED_SPATIAL_REFERENCE","Select cable gauges, shielding, grounding and connector families","Derived common trunk; no electrical rating",
                 maintainable=True,attachment_parent=tray,panel_access=f"M3_SHELL_PANEL_A02_S{idx:02d}")
        add_envelope(scene,records,cylinder_x(d["cable_minimum_bend_radius_m"],0.06,[0.30,c[1],c[2]],18),bend,"cable_bend_space","serviceability",trunk,
                     "DERIVED_MAINTENANCE_ENVELOPE","Confirm minimum bend radius by selected cable specification","Derived cable bend reservation")
    # Cross-links around two rings.
    for ring_idx,x in enumerate((-0.12,0.12),start=1):
        for seg in range(4):
            a0=seg*math.pi/2; a1=(seg+1)*math.pi/2
            p0=[x,tray_radius*math.cos(a0),tray_radius*math.sin(a0)]
            p1=[x,tray_radius*math.cos(a1),tray_radius*math.sin(a1)]
            add_node(scene,records,cylinder_between(p0,p1,0.0035,12),f"M3_HARNESS_CROSSLINK_R{ring_idx:02d}_S{seg+1:02d}","harness","electrical_data",
                     "DERIVED_SPATIAL_REFERENCE","Cable routing, bend, separation and support review","Derived harness cross-link",
                     maintainable=True,attachment_parent=f"M3_BULKHEAD_RING_{ring_idx+1:02d}",panel_access=f"M3_SHELL_PANEL_A02_S{seg+1:02d}")


def build_arm(scene: trimesh.Scene, records: list[dict[str, Any]], p: dict[str, Any], arm_idx: int, side: float) -> None:
    a=p["derived_configuration"]["arm"]
    prefix=f"M3_ARM_{arm_idx:02d}"
    base=np.array([0.16*side,0.0,0.0])
    # Arms mount on front/rear axial face and fold outward/upward in y-z.
    shoulder=base+np.array([0.035*side,0.055,0.0])
    elbow=shoulder+np.array([0.08*side,0.16,0.08*(1 if arm_idx==1 else -1)])
    wrist=elbow+np.array([0.06*side,0.13,0.05*(1 if arm_idx==1 else -1)])
    tip=wrist+np.array([0.035*side,0.06,0.0])
    route=f"{prefix}_CABLE_CHAIN"
    panel="M3_COUPLER_RING_REAR" if side>0 else "M3_COUPLER_RING_FRONT"
    add_node(scene,records,cylinder_between(base,shoulder,a["base_radius_m"],28),f"{prefix}_BASE_INTERFACE","arm","arm_system","PROVISIONAL_INTERFACE_REFERENCE",
             "Base load, latch, seal, alignment and collision review","Two source arm/spool interfaces; detailed geometry derived",
             maintainable=True,cable_required=True,attachment_parent=panel,cable_route=route,service_clearance=f"{prefix}_BASE_CLEARANCE",removal_path=f"{prefix}_REMOVAL_PATH",panel_access=panel)
    add_node(scene,records,sphere(a["joint_radius_m"],shoulder,2),f"{prefix}_YAW_SHOULDER_JOINT","arm_joint","arm_system","DERIVED_SPATIAL_REFERENCE",
             "Joint type, bearing, range, torque, hard-stop and lubrication review","Derived articulated joint; no load/torque claim",
             maintainable=True,cable_required=True,attachment_parent=f"{prefix}_BASE_INTERFACE",cable_route=route,service_clearance=f"{prefix}_SHOULDER_CLEARANCE",panel_access=panel)
    add_node(scene,records,cylinder_between(shoulder,elbow,a["link_radius_m"],24),f"{prefix}_UPPER_LINK","arm","arm_system","DERIVED_SPATIAL_REFERENCE",
             "Link material, buckling, fatigue and collision review","Derived Mark III-scale upper link",
             maintainable=True,cable_required=True,attachment_parent=f"{prefix}_YAW_SHOULDER_JOINT",cable_route=route,panel_access=panel)
    add_node(scene,records,sphere(a["joint_radius_m"]*0.9,elbow,2),f"{prefix}_ELBOW_JOINT","arm_joint","arm_system","DERIVED_SPATIAL_REFERENCE",
             "Elbow joint type, range, torque and hard-stop review","Derived elbow joint",
             maintainable=True,cable_required=True,attachment_parent=f"{prefix}_UPPER_LINK",cable_route=route,service_clearance=f"{prefix}_ELBOW_CLEARANCE",panel_access=panel)
    add_node(scene,records,cylinder_between(elbow,wrist,a["link_radius_m"]*0.9,24),f"{prefix}_FORE_LINK","arm","arm_system","DERIVED_SPATIAL_REFERENCE",
             "Link material, buckling, fatigue and collision review","Derived Mark III-scale fore link",
             maintainable=True,cable_required=True,attachment_parent=f"{prefix}_ELBOW_JOINT",cable_route=route,panel_access=panel)
    add_node(scene,records,sphere(a["wrist_radius_m"],wrist,2),f"{prefix}_WRIST_JOINT","arm_joint","arm_system","DERIVED_SPATIAL_REFERENCE",
             "Wrist degrees of freedom, torque, stop and cable-twist review","Derived wrist reference",
             maintainable=True,cable_required=True,attachment_parent=f"{prefix}_FORE_LINK",cable_route=route,service_clearance=f"{prefix}_WRIST_CLEARANCE",panel_access=panel)
    add_node(scene,records,cylinder_between(wrist,tip,a["link_radius_m"],20),f"{prefix}_END_EFFECTOR_BODY","arm","arm_system","DERIVED_SPATIAL_REFERENCE",
             "End-effector function, interface, force and safety review","Derived service/deployment end-effector body",
             maintainable=True,cable_required=True,attachment_parent=f"{prefix}_WRIST_JOINT",cable_route=route,service_clearance=f"{prefix}_END_CLEARANCE",panel_access=panel)
    # Two jaws, actuator housings and spool references.
    jaw_vec=np.array([0,0.025,0.018])
    for j,sign in enumerate((-1,1),start=1):
        add_node(scene,records,box([0.04,0.012,0.012],tip+sign*jaw_vec,0),f"{prefix}_JAW_{j:02d}","arm","arm_system","PROVISIONAL_INTERFACE_REFERENCE",
                 "End-effector geometry, contact force, material and hazard review","Derived jaws; no capture claim",
                 maintainable=True,cable_required=False,attachment_parent=f"{prefix}_END_EFFECTOR_BODY",panel_access=panel)
    for label,center,parent in (("SHOULDER",(base+shoulder)/2,f"{prefix}_YAW_SHOULDER_JOINT"),("ELBOW",elbow,f"{prefix}_ELBOW_JOINT"),("WRIST",wrist,f"{prefix}_WRIST_JOINT")):
        add_node(scene,records,cylinder_between(center-np.array([0.018,0,0]),center+np.array([0.018,0,0]),0.022,20),f"{prefix}_{label}_ACTUATOR_HOUSING","arm_actuator","arm_system",
                 "PROVISIONAL_INTERFACE_REFERENCE","Select actuator/solenoid, transmission, brake, sensing and thermal design","Derived actuator envelope; no torque/current claim",
                 maintainable=True,cable_required=True,attachment_parent=parent,cable_route=route,panel_access=panel)
        add_node(scene,records,cylinder_between(center-np.array([0,0.018,0]),center+np.array([0,0.018,0]),0.012,16),f"{prefix}_{label}_SPOOL_TENDON_INTERFACE","arm_actuator","arm_system",
                 "PROVISIONAL_INTERFACE_REFERENCE","Spool/tendon selection, fatigue, routing and redundancy review","Derived spool/tendon reference",
                 maintainable=True,cable_required=True,attachment_parent=f"{prefix}_{label}_ACTUATOR_HOUSING",cable_route=route,panel_access=panel)
    # Cable chain through joint centres.
    chain_points=[base,shoulder,elbow,wrist,tip]
    chain_meshes=[cylinder_between(a0,a1,a["cable_chain_radius_m"],14) for a0,a1 in zip(chain_points,chain_points[1:])]
    add_node(scene,records,trimesh.util.concatenate(chain_meshes),route,"harness","arm_system","DERIVED_SPATIAL_REFERENCE",
             "Cable-chain type, bend radius, torsion, strain relief and abrasion review","Derived routed arm harness",
             maintainable=True,attachment_parent=f"{prefix}_BASE_INTERFACE",panel_access=panel)
    add_node(scene,records,box([0.025,0.02,0.02],base+np.array([0,0.04,0]),0),f"{prefix}_STRAIN_RELIEF","harness","arm_system","DERIVED_SPATIAL_REFERENCE",
             "Strain-relief selection and fatigue review","Derived strain relief",
             maintainable=True,attachment_parent=f"{prefix}_BASE_INTERFACE",panel_access=panel)
    for label,center,radius in (("BASE",base,a["service_clearance_radius_m"]),("SHOULDER",shoulder,a["service_clearance_radius_m"]),("ELBOW",elbow,a["service_clearance_radius_m"]),("WRIST",wrist,a["service_clearance_radius_m"]*0.8),("END",tip,a["service_clearance_radius_m"]*0.8)):
        add_envelope(scene,records,sphere(radius,center,1),f"{prefix}_{label}_CLEARANCE","service_clearance","serviceability",f"{prefix}_BASE_INTERFACE",
                     "DERIVED_MAINTENANCE_ENVELOPE","Confirm articulation, tool access and collision keep-out","Derived joint/service envelope")
    add_envelope(scene,records,cylinder_between(base,tip,0.065,16),f"{prefix}_REMOVAL_PATH","removal_path","serviceability",f"{prefix}_BASE_INTERFACE",
                 "DERIVED_MAINTENANCE_ENVELOPE","Confirm complete arm removal, handling and support path","Derived arm replacement corridor")


def build_array_guides(scene: trimesh.Scene, records: list[dict[str, Any]], p: dict[str, Any]) -> None:
    spacing=p["derived_configuration"]["array_spacing_m"]
    length=p["source_parameters"]["module_length_m"]["value"]
    radius=p["source_parameters"]["outer_radius_m"]["value"]
    configs=p["derived_configuration"]["array_configurations"]
    for count in configs:
        if count==1:
            positions=[(0,0)]
        elif count==2:
            positions=[(-0.5,0),(0.5,0)]
        elif count==4:
            positions=[(-0.5,-0.5),(-0.5,0.5),(0.5,-0.5),(0.5,0.5)]
        elif count==8:
            positions=[(i-1.5,j-0.5) for i in range(4) for j in range(2)]
        else:
            positions=[(i-2.5,j-1) for i in range(6) for j in range(3)]
        for idx,(iy,iz) in enumerate(positions,start=1):
            c=[1.2+0.9*configs.index(count),iy*spacing,iz*spacing]
            mesh=box([length,2*radius,2*radius],c,0)
            add_envelope(scene,records,mesh,f"M3_ARRAY_{count:02d}_MODULE_GUIDE_{idx:02d}","array_guide","array_configuration",
                         "ILLUSTRATIVE_REFERENCE_ROOT","ILLUSTRATIVE_ONLY_NOT_PHYSICAL_PERFORMANCE",
                         "Array coupler, bus, thermal, synchronization and field-interaction review",
                         f"Illustrative {count}-module configuration; no array performance claim",array_configuration=str(count))


def build_field_guides(scene: trimesh.Scene, records: list[dict[str, Any]]) -> None:
    for idx,r in enumerate((0.07,0.10,0.13),start=1):
        add_envelope(scene,records,annulus_x(r-0.002,r+0.002,0.50,[0,0,0],48),f"M3_FIELD_GUIDE_{idx:02d}","field_guide","emff_module",
                     "ILLUSTRATIVE_REFERENCE_ROOT","ILLUSTRATIVE_ONLY_NOT_PHYSICAL_PERFORMANCE",
                     "Replace with measured synchronized field maps","Illustrative spatial guide only; no field-strength evidence")


def build_reference(parameters: dict[str, Any]) -> tuple[trimesh.Scene, list[dict[str, Any]]]:
    scene=trimesh.Scene(); records:list[dict[str,Any]]=[]
    build_shell(scene,records,parameters)
    build_couplers(scene,records,parameters)
    build_internal_systems(scene,records,parameters)
    build_harnesses(scene,records,parameters)
    build_arm(scene,records,parameters,1,-1.0)
    build_arm(scene,records,parameters,2,1.0)
    build_array_guides(scene,records,parameters)
    build_field_guides(scene,records)
    if len(scene.geometry)!=len(records):
        raise RuntimeError("Scene/record count mismatch")
    return scene,records


def build_print_references(parameters: dict[str, Any], scene: trimesh.Scene, records: list[dict[str, Any]]) -> dict[str,trimesh.Trimesh]:
    length=parameters["source_parameters"]["module_length_m"]["value"]
    radius=parameters["source_parameters"]["outer_radius_m"]["value"]
    d=parameters["derived_configuration"]
    full=cylinder_x(radius,length,[0,0,0],64); full.apply_scale(1000/5)
    panel=annular_sector_x(-0.11,0.11,d["structural_panel_inner_radius_m"],d["solar_skin_outer_radius_m"],-math.pi/6+0.03,math.pi/6-0.03); panel.apply_scale(1000/3)
    coupler=annulus_x(0.11,0.16,d["coupler_length_m"],[0,0,0],64); coupler.apply_scale(1000/2)
    solenoid=annulus_x(d["solenoid_inner_radius_m"],d["solenoid_outer_radius_m"],d["solenoid_axial_length_m"],[0,0,0],48); solenoid.apply_scale(1000)
    arm_meshes=[]
    for record in records:
        if record["node_name"].startswith("M3_ARM_01") and record["physical"] and record["family"] not in {"harness"}:
            arm_meshes.append(scene.geometry[record["node_name"]].copy())
    arm=trimesh.util.concatenate(arm_meshes); arm.apply_scale(1000/2)
    for mesh in (full,panel,coupler,solenoid,arm):
        if mesh.volume<0: mesh.invert()
    return {
        "mark_iii_full_module_1to5.stl": full,
        "mark_iii_representative_panel_1to3.stl": panel,
        "mark_iii_coupler_1to2.stl": coupler,
        "mark_iii_solenoid_cartridge_1to1.stl": solenoid,
        "mark_iii_arm_assembly_1to2.stl": arm,
    }


def build_verification(parameters: dict[str, Any], scene: trimesh.Scene, records: list[dict[str, Any]], print_refs: dict[str,trimesh.Trimesh]) -> dict[str,Any]:
    families={}
    for record in records: families[record["family"]]=families.get(record["family"],0)+1
    checks={name:{"watertight":bool(mesh.is_watertight),"winding_consistent":bool(mesh.is_winding_consistent),"vertices":int(len(mesh.vertices)),"faces":int(len(mesh.faces))} for name,mesh in scene.geometry.items()}
    return {
        "schema_version":"mark-iii-verification-v0.2",
        "status":"PASS_SERVICEABLE_REFERENCE_GEOMETRY" if all(v["watertight"] and v["winding_consistent"] for v in checks.values()) else "FAIL_GEOMETRY",
        "scene":{"geometry_nodes":len(scene.geometry),"physical_nodes":sum(1 for r in records if r["physical"]),"illustrative_nodes":sum(1 for r in records if not r["physical"])},
        "family_counts":families,
        "geometry_checks":checks,
        "semantic_geometry_sha256":semantic_geometry_fingerprint(scene),
        "semantic_quantization_m":QUANTIZATION_METRES,
        "print_references":{name:{"watertight":bool(mesh.is_watertight),"winding_consistent":bool(mesh.is_winding_consistent),"extents_mm":np.round(mesh.extents,6).tolist(),"fits_280mm":bool(max(mesh.extents)<=280.0+1e-6)} for name,mesh in print_refs.items()},
        "claim_gate_state":"UNCHANGED",
    }


def export_reference(parameters_path: Path, out_dir: Path) -> dict[str,Any]:
    out_dir.mkdir(parents=True,exist_ok=True)
    parameters=load_parameters(parameters_path)
    scene,records=build_reference(parameters)
    print_refs=build_print_references(parameters,scene,records)
    glb_path=out_dir/"mark_iii_assembly.glb"; glb_path.write_bytes(scene.export(file_type="glb"))
    for name,mesh in print_refs.items(): (out_dir/name).write_bytes(mesh.export(file_type="stl"))
    manifest={"schema_version":"mark-iii-component-manifest-v0.2","node_count":len(records),"components":records}
    manifest["canonical_manifest_sha256"]=canonical_manifest_sha256(manifest)
    (out_dir/"mark_iii_component_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    verification=build_verification(parameters,scene,records,print_refs)
    verification["canonical_manifest_sha256"]=manifest["canonical_manifest_sha256"]
    verification["observed_artifacts"]={"assembly_glb_sha256":sha256_file(glb_path)}
    (out_dir/"mark_iii_verification.json").write_text(json.dumps(verification,indent=2)+"\n",encoding="utf-8")
    summary={"status":verification["status"],"geometry_nodes":len(records),"physical_nodes":verification["scene"]["physical_nodes"],"semantic_geometry_sha256":verification["semantic_geometry_sha256"],"print_references":len(print_refs)}
    return summary


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--parameters",type=Path,required=True);ap.add_argument("--out-dir",type=Path,required=True)
    args=ap.parse_args();summary=export_reference(args.parameters,args.out_dir);print(json.dumps(summary,indent=2));return 0 if summary["status"].startswith("PASS") else 1

if __name__=="__main__": raise SystemExit(main())
