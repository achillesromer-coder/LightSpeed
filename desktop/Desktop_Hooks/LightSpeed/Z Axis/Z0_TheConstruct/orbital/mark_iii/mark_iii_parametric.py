#!/usr/bin/env python3
"""Generate the Mark III v0.3.3 original-layout print-and-plating reference.

This is a deterministic geometry, serviceability and manufacturing-reference
artifact. It is not validated hardware, a hazardous-process instruction set,
a mission article, a safety certification or a performance model.
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
    "resonator_mount": [95, 85, 116, 255],
    "resonator_guide": [167, 118, 190, 55],
    "coil_reference": [151, 92, 65, 255],
    "plating_feature": [184, 137, 63, 255],
    "plating_allowance": [215, 164, 76, 45],
    "layout_guide": [57, 154, 178, 35],
    "energy_tray": [105, 100, 75, 255],
    "arm_solenoid_reference": [145, 86, 68, 255],
    "arm_gas_joint": [99, 126, 146, 255],
    "collector_pad": [66, 102, 125, 255],
    "probe_mast": [109, 121, 135, 255],
    "print_fixture": [118, 126, 133, 255],
    "propulsion_interface": [91, 122, 154, 255],
    "reservoir_placeholder": [122, 108, 138, 255],
    "propulsion_service_port": [108, 126, 142, 255],
    "fluid_route_reservation": [82, 145, 163, 55],
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


def annulus_between(a: Iterable[float], b: Iterable[float], r_min: float, r_max: float,
                    sections: int = 24) -> trimesh.Trimesh:
    """Create a closed annular sleeve between two points."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    vector = b - a
    length = float(np.linalg.norm(vector))
    mesh = trimesh.creation.annulus(r_min=r_min, r_max=r_max, height=length, sections=sections)
    transform = rotation_z_to_vector(vector)
    transform[:3, 3] = (a + b) / 2.0
    mesh.apply_transform(transform)
    return mesh


def polyline_tube(points: Iterable[Iterable[float]], radius: float, sections: int = 12) -> trimesh.Trimesh:
    pts = [np.asarray(p, dtype=float) for p in points]
    meshes = [cylinder_between(a, b, radius, sections) for a, b in zip(pts, pts[1:])]
    return trimesh.util.concatenate(meshes)


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
               removal_path: str = "", panel_access: str = "", array_configuration: str = "",
               configuration: str = "", component_role: str = "", manufacturing_state: str = "",
               print_part: str = "") -> dict[str, Any]:
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
        "configuration": configuration,
        "component_role": component_role,
        "manufacturing_state": manufacturing_state,
        "print_part": print_part,
    }


def add_node(scene: trimesh.Scene, records: list[dict[str, Any]], mesh: trimesh.Trimesh, name: str,
             family: str, subsystem: str, evidence_state: str, review_gate: str, source_basis: str,
             physical: bool = True, maintainable: bool = False, cable_required: bool = False,
             attachment_parent: str = "PRIMARY_STRUCTURE", cable_route: str = "",
             service_clearance: str = "", removal_path: str = "", panel_access: str = "",
             array_configuration: str = "", configuration: str = "", component_role: str = "",
             manufacturing_state: str = "", print_part: str = "") -> None:
    if name in scene.geometry:
        raise ValueError(f"Duplicate node: {name}")
    apply_color(mesh, family)
    scene.add_geometry(mesh, node_name=name, geom_name=name)
    record = record_for(name, family, subsystem, evidence_state, review_gate, source_basis, physical,
                        maintainable, cable_required, attachment_parent, cable_route,
                        service_clearance, removal_path, panel_access, array_configuration,
                        configuration, component_role, manufacturing_state, print_part)
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
                 source_basis: str, array_configuration: str = "", configuration: str = "",
                 component_role: str = "") -> None:
    add_node(scene, records, mesh, name, family, subsystem, evidence, review_gate, source_basis,
             physical=False, maintainable=False, attachment_parent=parent,
             array_configuration=array_configuration, configuration=configuration,
             component_role=component_role)


def build_shell(scene: trimesh.Scene, records: list[dict[str, Any]], p: dict[str, Any]) -> None:
    d = p["derived_configuration"]
    sector_count = p["source_parameters"]["shell_sector_count"]["value"]
    axial_count = d["axial_panel_count"]
    body_len = d["main_body_length_m"]
    gap_a = math.radians(2.0)
    zone_len = body_len / axial_count
    for axial in range(axial_count):
        x0 = -body_len / 2 + axial * zone_len + 0.004
        x1 = -body_len / 2 + (axial + 1) * zone_len - 0.004
        for sector in range(sector_count):
            center_a = 2 * math.pi * sector / sector_count
            a0 = center_a - math.pi / sector_count + gap_a
            a1 = center_a + math.pi / sector_count - gap_a
            mid_a = (a0 + a1) / 2
            panel = f"M3_SHELL_PANEL_A{axial+1:02d}_S{sector+1:02d}"
            clearance = f"M3_SERVICE_CLEARANCE_PANEL_A{axial+1:02d}_S{sector+1:02d}"
            removal = f"M3_REMOVAL_PATH_PANEL_A{axial+1:02d}_S{sector+1:02d}"
            add_node(
                scene, records,
                annular_sector_x(x0, x1, d["structural_panel_inner_radius_m"],
                                 d["print_substrate_outer_radius_m"], a0, a1),
                panel, "shell_panel", "structure", "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
                "Substrate, raster, wall, insert, sanding, coating, tolerance and load-path qualification",
                "Six-sector faceted original body with three axial print/service zones",
                maintainable=True, attachment_parent=f"M3_LONGITUDINAL_RAIL_{sector+1:02d}",
                service_clearance=clearance, removal_path=removal, panel_access=panel,
                manufacturing_state="PRE_PLATE_PRINT_SUBSTRATE",
                print_part=f"SHELL_PANEL_A{axial+1:02d}_S{sector+1:02d}"
            )
            add_envelope(
                scene, records,
                annular_sector_x(x0, x1, d["print_substrate_outer_radius_m"],
                                 d["electroplate_nominal_outer_radius_m"], a0, a1),
                f"M3_PLATING_ALLOWANCE_A{axial+1:02d}_S{sector+1:02d}",
                "plating_allowance", "manufacturing", panel,
                "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
                "Qualify thickness, uniformity, stress, adhesion and environmental compatibility",
                "Nominal configurable metal-build envelope; not a released coating thickness",
                configuration="ELECTROPLATE_BUILD_ENVELOPE"
            )
            radial = d["electroplate_nominal_outer_radius_m"] + 0.045
            add_envelope(
                scene, records,
                box([x1-x0, 0.07, 0.025],
                    [(x0+x1)/2, radial*math.cos(mid_a), radial*math.sin(mid_a)],
                    rotation_x=mid_a),
                clearance, "service_clearance", "serviceability", panel,
                "DERIVED_MAINTENANCE_ENVELOPE",
                "Confirm technician/tool access and adjacent interference",
                "Derived panel access volume"
            )
            p0 = np.array([(x0+x1)/2,
                           (d["electroplate_nominal_outer_radius_m"]+0.006)*math.cos(mid_a),
                           (d["electroplate_nominal_outer_radius_m"]+0.006)*math.sin(mid_a)])
            p1 = np.array([(x0+x1)/2,
                           (d["electroplate_nominal_outer_radius_m"]+0.105)*math.cos(mid_a),
                           (d["electroplate_nominal_outer_radius_m"]+0.105)*math.sin(mid_a)])
            add_envelope(scene, records, cylinder_between(p0, p1, 0.012, 12), removal,
                         "removal_path", "serviceability", panel,
                         "DERIVED_MAINTENANCE_ENVELOPE",
                         "Confirm panel removal direction, support and plated-edge protection",
                         "Derived panel removal vector")
            # Captive insert bosses, mask lands, datum pads, contact tabs and a true drain sleeve.
            for fidx, x in enumerate((x0+0.018, x1-0.018), start=1):
                r0 = d["structural_panel_inner_radius_m"] - 0.004
                r1 = d["print_substrate_outer_radius_m"] + 0.001
                add_node(
                    scene, records,
                    annulus_between(
                        [x, r0*math.cos(mid_a), r0*math.sin(mid_a)],
                        [x, r1*math.cos(mid_a), r1*math.sin(mid_a)],
                        0.0016, 0.0045, 18),
                    f"M3_PANEL_INSERT_BOSS_A{axial+1:02d}_S{sector+1:02d}_F{fidx:02d}",
                    "fastener", "structure", "PROVISIONAL_INTERFACE_REFERENCE",
                    "Select insert, boss wall, thread engagement, preload and galvanic isolation",
                    "Through-boss reference replaces a solid cosmetic fastener",
                    maintainable=True, attachment_parent=panel, panel_access=panel,
                    manufacturing_state="INSERT_BOSS_REFERENCE"
                )
            for edge_idx, x in enumerate((x0+0.006, x1-0.006), start=1):
                add_node(
                    scene, records,
                    annular_sector_x(x-0.003, x+0.003,
                                     d["print_substrate_outer_radius_m"]-0.001,
                                     d["print_substrate_outer_radius_m"], a0+0.012, a1-0.012),
                    f"M3_PLATING_MASK_LAND_A{axial+1:02d}_S{sector+1:02d}_E{edge_idx:02d}",
                    "plating_feature", "manufacturing",
                    "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
                    "Protect seams, datums and electrical isolation during metallization",
                    "Raised/controlled mask land reference",
                    maintainable=True, attachment_parent=panel, panel_access=panel,
                    manufacturing_state="MASK_LAND_REFERENCE"
                )
            drain_r = d["plating_drain_bore_radius_m"]
            drain_x = x0 + 0.025
            drain_a = a0 + 0.12*(a1-a0)
            add_node(
                scene, records,
                annulus_between(
                    [drain_x, (d["structural_panel_inner_radius_m"]-0.004)*math.cos(drain_a),
                     (d["structural_panel_inner_radius_m"]-0.004)*math.sin(drain_a)],
                    [drain_x, (d["electroplate_nominal_outer_radius_m"]+0.002)*math.cos(drain_a),
                     (d["electroplate_nominal_outer_radius_m"]+0.002)*math.sin(drain_a)],
                    drain_r, drain_r+0.0022, 18),
                f"M3_PLATING_DRAIN_SLEEVE_A{axial+1:02d}_S{sector+1:02d}",
                "plating_feature", "manufacturing",
                "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
                "Confirm bath drainage, rinsing, venting, masking and minimum wall",
                "Explicit through-sleeve prevents sealed plating pockets in this reference",
                maintainable=True, attachment_parent=panel, panel_access=panel,
                manufacturing_state="DRAIN_VENT_REFERENCE"
            )
            datum_r = d["structural_panel_inner_radius_m"] - 0.003
            add_node(
                scene, records,
                box([0.020, 0.012, 0.004],
                    [(x0+x1)/2, datum_r*math.cos(mid_a), datum_r*math.sin(mid_a)],
                    rotation_x=mid_a),
                f"M3_ASSEMBLY_DATUM_PAD_A{axial+1:02d}_S{sector+1:02d}",
                "plating_feature", "manufacturing",
                "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
                "Inspect before/after sanding and mask during coating as required",
                "Internal datum and thickness measurement pad",
                maintainable=True, attachment_parent=panel, panel_access=panel,
                manufacturing_state="INSPECTION_DATUM"
            )

    # Six continuous functional-skin envelopes.
    for sector in range(sector_count):
        center_a = 2 * math.pi * sector / sector_count
        a0 = center_a - math.pi / sector_count + gap_a
        a1 = center_a + math.pi / sector_count - gap_a
        name = f"M3_SOLAR_HULL_SKIN_S{sector+1:02d}"
        add_node(
            scene, records,
            annular_sector_x(-body_len/2+0.002, body_len/2-0.002,
                             d["solar_skin_inner_radius_m"], d["solar_skin_outer_radius_m"], a0, a1),
            name, "solar_hull_skin", "solar_hull_interface",
            "PROVISIONAL_INTERFACE_REFERENCE",
            "Coupon, adhesion, thermal-cycle, electrical, contamination and environmental review",
            "Solar Hull silica/copper/bismuth/conductive-layer concept retained as an interface envelope only",
            maintainable=True, attachment_parent=f"M3_SHELL_PANEL_A02_S{sector+1:02d}",
            panel_access=f"M3_SHELL_PANEL_A02_S{sector+1:02d}",
            manufacturing_state="FUNCTIONAL_SKIN_ENVELOPE_NOT_RELEASED"
        )

    for sector in range(sector_count):
        a = 2 * math.pi * sector / sector_count
        name = f"M3_LONGITUDINAL_RAIL_{sector+1:02d}"
        add_node(
            scene, records,
            box([body_len-0.015, 0.012, 0.018],
                [0, 0.143*math.cos(a), 0.143*math.sin(a)], rotation_x=a),
            name, "primary_structure", "structure", "DERIVED_SPATIAL_REFERENCE",
            "Structural sizing, joining, plating-current isolation, load path and tolerance review",
            "Derived rail attaches panels, internal mounts and conductive bonding references",
            maintainable=True, attachment_parent="PRIMARY_STRUCTURE"
        )
    for idx, x in enumerate((-0.30, -0.10, 0.10, 0.30), start=1):
        add_node(
            scene, records, annulus_x(0.118, 0.150, 0.012, [x,0,0], 48),
            f"M3_BULKHEAD_RING_{idx:02d}", "primary_structure", "structure",
            "DERIVED_SPATIAL_REFERENCE",
            "Structural, vibration, cable-passage and access-opening review",
            "Derived internal ring for panel, rail and bay support",
            maintainable=True, attachment_parent="PRIMARY_STRUCTURE"
        )


def build_original_layout_structure(scene: trimesh.Scene, records: list[dict[str, Any]],
                                    p: dict[str, Any]) -> None:
    """Restore the original schematic's upper-control, energy and lower-field zoning."""
    d = p["derived_configuration"]
    zones = [
        ("UPPER_CONTROL", [0.52, 0.19, 0.010], [0.00, 0.00, d["internal_decks_z_m"][0]], "controller"),
        ("MID_ENERGY", [0.54, 0.20, 0.010], [0.00, 0.00, d["internal_decks_z_m"][1]], "energy"),
        ("LOWER_FIELD", [0.56, 0.20, 0.010], [0.00, 0.00, d["internal_decks_z_m"][2]], "solenoid"),
    ]
    for label, ext, center, role in zones:
        add_node(
            scene, records, box(ext, center, 0),
            f"M3_INTERNAL_DECK_{label}", "primary_structure", "structure",
            "DERIVED_SPATIAL_REFERENCE",
            "Deck stiffness, cable penetrations, thermal path, access and plated-polymer bonding review",
            "Physical deck restores the original top-control / middle-energy / lower-field zoning",
            maintainable=True, attachment_parent="M3_BULKHEAD_RING_02",
            component_role=role, manufacturing_state="PRINTED_INTERNAL_FRAME_REFERENCE"
        )
        add_envelope(
            scene, records, box([ext[0], ext[1], 0.045], center, 0),
            f"M3_LAYOUT_GUIDE_{label}", "layout_guide", "original_layout",
            f"M3_INTERNAL_DECK_{label}", "ILLUSTRATIVE_ONLY_NOT_PHYSICAL_PERFORMANCE",
            "Compare v0.3.3 packaging against the owner-supplied original schematic",
            "Original schematic zoning guide", configuration="ORIGINAL_SCHEMATIC"
        )
    for sector in range(6):
        a = sector * math.pi / 3
        c = [0, 0.112*math.cos(a), 0.112*math.sin(a)]
        add_node(
            scene, records,
            box([0.58, 0.010, 0.014], c, rotation_x=a),
            f"M3_SOLENOID_RAIL_S{sector+1:02d}", "primary_structure", "solenoid_array",
            "DERIVED_SPATIAL_REFERENCE",
            "Rail load, thermal path, electrical isolation and service access review",
            "Six source body segments each support three compact solenoid cassettes",
            maintainable=True, attachment_parent=f"M3_LONGITUDINAL_RAIL_{sector+1:02d}",
            manufacturing_state="PRINTED_OR_METAL_INSERT_RAIL_REFERENCE"
        )
    # Interior bonding buses and plating contact tabs.
    for sector in range(6):
        a = sector * math.pi / 3
        r = 0.139
        add_node(
            scene, records,
            box([0.55, 0.006, 0.006], [0, r*math.cos(a), r*math.sin(a)], rotation_x=a),
            f"M3_BONDING_BUS_S{sector+1:02d}", "plating_feature", "manufacturing",
            "PROVISIONAL_INTERFACE_REFERENCE",
            "Electrical bonding, current return, isolation, corrosion and fault-current review",
            "Dedicated internal bonding-bus geometry; rating unassigned",
            maintainable=True, cable_required=True,
            attachment_parent=f"M3_LONGITUDINAL_RAIL_{sector+1:02d}",
            cable_route=f"M3_HARNESS_TRUNK_{sector+1:02d}",
            manufacturing_state="BONDING_BUS_INTERFACE"
        )
        add_node(
            scene, records,
            box([0.025, 0.010, 0.010],
                [-0.29, 0.137*math.cos(a), 0.137*math.sin(a)], rotation_x=a),
            f"M3_PLATING_CONTACT_TAB_S{sector+1:02d}", "plating_feature", "manufacturing",
            "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
            "Define temporary cathode contact, removal, mask and continuity inspection with plater",
            "Sacrificial plating contact-tab reference inside the nominal envelope",
            maintainable=True, attachment_parent=f"M3_BONDING_BUS_S{sector+1:02d}",
            panel_access=f"M3_SHELL_PANEL_A01_S{sector+1:02d}",
            manufacturing_state="SACRIFICIAL_PLATING_CONTACT"
        )


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



def build_internal_systems(scene: trimesh.Scene, records: list[dict[str, Any]],
                           p: dict[str, Any]) -> None:
    d = p["derived_configuration"]
    add_node(
        scene, records,
        annulus_x(d["process_tunnel_inner_radius_m"], d["process_tunnel_outer_radius_m"],
                  0.62, [0,0,0], 48),
        "M3_PROCESS_TUNNEL", "process_tunnel", "process_module",
        "SOURCE_ALIGNED_TOPOLOGY",
        "Sample containment, vacuum/pressure, cleaning and material compatibility review",
        "Central process-path topology from Mark III and RFS/EMFF lineage",
        maintainable=True, attachment_parent="M3_BULKHEAD_RING_02"
    )
    cart = "M3_SAMPLE_CHAMBER_CARTRIDGE"
    add_node(
        scene, records,
        cylinder_x(d["sample_cartridge_radius_m"], d["sample_cartridge_length_m"], [0,0,0], 36),
        cart, "sample_cartridge", "process_module", "PROVISIONAL_INTERFACE_REFERENCE",
        "Sample compatibility, assay, containment, cleaning and blank-control review",
        "Removable central chamber reference; no extraction claim",
        maintainable=True, cable_required=True, attachment_parent="M3_PROCESS_TUNNEL",
        cable_route="M3_HARNESS_TRUNK_01", service_clearance="M3_SERVICE_CLEARANCE_SAMPLE",
        removal_path="M3_REMOVAL_PATH_SAMPLE", panel_access="M3_COUPLER_RING_FRONT"
    )
    add_envelope(scene, records, cylinder_x(0.043, 0.24, [0,0,0], 28),
                 "M3_SERVICE_CLEARANCE_SAMPLE", "service_clearance", "serviceability", cart,
                 "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm cartridge handling, isolation and sensor access",
                 "Derived chamber clearance")
    add_envelope(scene, records, cylinder_x(0.033, 0.36, [-0.25,0,0], 24),
                 "M3_REMOVAL_PATH_SAMPLE", "removal_path", "serviceability", cart,
                 "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm axial extraction through front coupler",
                 "Derived cartridge removal path")

    # Eighteen compact body solenoids: six sectors, three axial positions per sector.
    axial_positions = d["solenoid_axial_positions_m"]
    for sector in range(6):
        a = sector * math.pi / 3
        r = d["solenoid_radial_position_m"]
        y, z = r*math.cos(a), r*math.sin(a)
        route = f"M3_HARNESS_TRUNK_{sector+1:02d}"
        panel = f"M3_SHELL_PANEL_A02_S{sector+1:02d}"
        for zone, x in enumerate(axial_positions, start=1):
            idx = sector*3 + zone
            base = f"M3_SOLENOID_S{sector+1:02d}_Z{zone:02d}"
            clearance = f"M3_SERVICE_CLEARANCE_SOLENOID_{idx:02d}"
            removal = f"M3_REMOVAL_PATH_SOLENOID_{idx:02d}"
            add_node(
                scene, records,
                annulus_x(d["solenoid_inner_radius_m"], d["solenoid_outer_radius_m"],
                          d["solenoid_axial_length_m"], [x,y,z], 36),
                base, "solenoid", "solenoid_array", "SOURCE_RECONCILED_TOPOLOGY",
                "Measured conductor, turns, insulation, switching, thermal and field-map review",
                "Original schematic three-per-segment topology implemented as six sectors x three axial cartridges",
                maintainable=True, cable_required=True,
                attachment_parent=f"M3_SOLENOID_RAIL_S{sector+1:02d}", cable_route=route,
                service_clearance=clearance, removal_path=removal, panel_access=panel,
                configuration="SIX_SECTOR_THREE_AXIAL",
                component_role=f"SECTOR_{sector+1:02d}_ZONE_{zone:02d}"
            )
            add_node(
                scene, records,
                annulus_x(d["solenoid_inner_radius_m"]+0.001,
                          d["solenoid_outer_radius_m"]-0.002,
                          d["solenoid_axial_length_m"]-0.006, [x,y,z], 32),
                f"{base}_COIL_REFERENCE", "coil_reference", "solenoid_array",
                "QUARANTINED_UNVERIFIED_NOT_USED_FOR_CAPABILITY",
                "Replace with measured winding, insulation and thermal geometry",
                "Illustrative coil envelope only; no turn/current/field or carbon-fill claim",
                maintainable=True, cable_required=True, attachment_parent=base,
                cable_route=route, panel_access=panel
            )
            mount_center = [x, (r+0.031)*math.cos(a), (r+0.031)*math.sin(a)]
            add_node(
                scene, records, box([0.050,0.018,0.016], mount_center, rotation_x=a),
                f"{base}_MOUNT_BRACKET", "primary_structure", "solenoid_array",
                "DERIVED_SPATIAL_REFERENCE",
                "Bracket load, thermal conduction, insert and isolation review",
                "Derived cassette-to-sector rail mount",
                maintainable=True, attachment_parent=f"M3_SOLENOID_RAIL_S{sector+1:02d}",
                panel_access=panel
            )
            conn_center = [x, (r+0.035)*math.cos(a+0.12), (r+0.035)*math.sin(a+0.12)]
            add_node(
                scene, records, box([0.018,0.014,0.014], conn_center, rotation_x=a),
                f"{base}_CONNECTOR", "coupler_bridge", "solenoid_array",
                "PROVISIONAL_INTERFACE_REFERENCE",
                "Connector rating, shielding, keying, thermal and strain-relief review",
                "Derived connector interface",
                maintainable=True, cable_required=True, attachment_parent=base,
                cable_route=route, service_clearance=f"M3_CONNECTOR_ACCESS_SOLENOID_{idx:02d}",
                panel_access=panel
            )
            add_envelope(
                scene, records, cylinder_x(0.033, 0.065, [x,y,z], 24), clearance,
                "service_clearance", "serviceability", base,
                "DERIVED_MAINTENANCE_ENVELOPE",
                "Confirm cassette tool, insulation and thermal-clearance envelope",
                "Derived solenoid service volume"
            )
            outward = np.array([0,y,z], dtype=float); outward /= np.linalg.norm(outward)
            add_envelope(
                scene, records,
                cylinder_between(np.array([x,y,z]), np.array([x,y,z])+outward*0.105, 0.018, 12),
                removal, "removal_path", "serviceability", base,
                "DERIVED_MAINTENANCE_ENVELOPE",
                "Confirm radial cassette removal path through its sector panel",
                "Derived removal corridor"
            )
            add_envelope(
                scene, records, box([0.040,0.040,0.040],
                                    np.asarray(conn_center)+outward*0.018, rotation_x=a),
                f"M3_CONNECTOR_ACCESS_SOLENOID_{idx:02d}",
                "connector_access", "serviceability", f"{base}_CONNECTOR",
                "DERIVED_MAINTENANCE_ENVELOPE",
                "Confirm connector access and cable bend relief",
                "Derived connector access volume"
            )

    # Resonator tray: 25 replaceable sockets with two interleaved spirals and source role bands.
    tray_x = d["resonator_tray_x_m"]
    tray = "M3_RESONATOR_TRAY"
    add_node(
        scene, records,
        annulus_x(d["resonator_tray_inner_radius_m"], d["resonator_tray_outer_radius_m"],
                  d["resonator_tray_thickness_m"], [tray_x,0,0], 64),
        tray, "primary_structure", "rfs_module",
        "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
        "Tray stiffness, socket tolerances, isolation, damping, cable routing and removal review",
        "Original Flower-of-Life role set packaged as a replaceable dual-spiral tray",
        maintainable=True, attachment_parent="M3_BULKHEAD_RING_02",
        service_clearance="M3_SERVICE_CLEARANCE_RESONATOR_TRAY",
        removal_path="M3_REMOVAL_PATH_RESONATOR_TRAY",
        panel_access="M3_SHELL_PANEL_A02_S02",
        manufacturing_state="PRINTABLE_RESONATOR_TRAY_REFERENCE",
        print_part="RESONATOR_TRAY"
    )
    add_envelope(scene, records, cylinder_x(0.139,0.045,[tray_x,0,0],40),
                 "M3_SERVICE_CLEARANCE_RESONATOR_TRAY",
                 "service_clearance","serviceability",tray,
                 "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm tray isolation, connector and tool access",
                 "Derived resonator-tray service envelope")
    add_envelope(scene, records, cylinder_x(0.132,0.18,[tray_x-0.10,0,0],40),
                 "M3_REMOVAL_PATH_RESONATOR_TRAY",
                 "removal_path","serviceability",tray,
                 "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm complete tray removal through front service path",
                 "Derived resonator-tray removal corridor")

    # Central annular resonator around the process tunnel.
    central = "M3_RESONATOR_CENTRAL"
    add_node(
        scene, records,
        annulus_x(d["process_tunnel_outer_radius_m"]+0.002,
                  d["process_tunnel_outer_radius_m"]+0.014,
                  d["resonator_socket_length_m"], [tray_x,0,0], 36),
        central, "resonator", "rfs_module",
        "QUARANTINED_UNVERIFIED_NOT_USED_FOR_CAPABILITY",
        "Select and calibrate insert/actuator against blank-controlled material-response tests",
        "Source central Pt-Pd-Rh label retained only as a replaceable insert concept",
        maintainable=True, cable_required=True, attachment_parent=tray,
        cable_route="M3_RESONATOR_BUS_A",
        service_clearance="M3_SERVICE_CLEARANCE_RESONATOR_CENTRAL",
        removal_path="M3_REMOVAL_PATH_RESONATOR_CENTRAL",
        panel_access="M3_COUPLER_RING_FRONT",
        configuration="SHARED_CENTRAL",
        component_role="CENTRAL_BROAD_RANGE_SOURCE_ROLE"
    )
    add_envelope(scene, records, cylinder_x(0.055,0.050,[tray_x,0,0],24),
                 "M3_SERVICE_CLEARANCE_RESONATOR_CENTRAL",
                 "service_clearance","serviceability",central,
                 "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm central insert isolation and tool access",
                 "Derived central clearance")
    add_envelope(scene, records, cylinder_x(0.048,0.18,[tray_x-0.10,0,0],24),
                 "M3_REMOVAL_PATH_RESONATOR_CENTRAL",
                 "removal_path","serviceability",central,
                 "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm central insert removal through process service path",
                 "Derived central removal path")

    start_r = d["resonator_spiral_start_radius_m"]
    end_r = d["resonator_spiral_end_radius_m"]
    step_angle = math.radians(d["resonator_spiral_step_angle_deg"])
    phase_offset = math.radians(d["resonator_spiral_phase_offset_deg"])
    spiral_points = {"A": [], "B": []}
    ordinal = 0
    for spiral_name, phase in (("A",0.0),("B",phase_offset)):
        for i in range(12):
            ordinal += 1
            frac = i/11
            radius = start_r + frac*(end_r-start_r)
            angle = phase + i*step_angle
            y, z = radius*math.cos(angle), radius*math.sin(angle)
            x = tray_x + (0.006 if i % 2 == 0 else -0.006)
            spiral_points[spiral_name].append([x,y,z])
            if ordinal <= 6:
                role = "SURROUNDING_TARGET_SPECIFIC_ROLE"
                source_label = "Pt-Pd / Pt-Rh alternating insert concept"
            elif ordinal <= 18:
                role = "PERIPHERAL_HIGH_MID_FREQUENCY_ROLE"
                source_label = "Au-Ir / Ni-Co alternating insert concept"
            else:
                role = "UNDOPED_SUPPORT_ROLE"
                source_label = "Pure quartz supporting insert concept"
            name = f"M3_RESONATOR_{spiral_name}_{i+1:02d}"
            bus = f"M3_RESONATOR_BUS_{spiral_name}"
            panel_sector = int(((angle % (2*math.pi)) / (2*math.pi/6))) + 1
            panel = f"M3_SHELL_PANEL_A02_S{panel_sector:02d}"
            add_node(
                scene, records,
                cylinder_x(d["resonator_socket_radius_m"],
                           d["resonator_socket_length_m"], [x,y,z], 24),
                name, "resonator", "rfs_module",
                "QUARANTINED_UNVERIFIED_NOT_USED_FOR_CAPABILITY",
                "Calibrate frequency, Q, acceleration, coupling, thermal response and assay against blanks",
                f"{source_label}; physical role is a replaceable keyed socket, not validated doping",
                maintainable=True, cable_required=True, attachment_parent=tray,
                cable_route=bus,
                service_clearance=f"M3_SERVICE_CLEARANCE_RESONATOR_{spiral_name}_{i+1:02d}",
                removal_path=f"M3_REMOVAL_PATH_RESONATOR_{spiral_name}_{i+1:02d}",
                panel_access=panel,
                configuration=f"DUAL_SPIRAL_{spiral_name}",
                component_role=role
            )
            add_node(
                scene, records,
                annulus_x(d["resonator_socket_radius_m"]+0.001,
                          d["resonator_socket_radius_m"]+0.004,
                          d["resonator_tray_thickness_m"]+0.006,
                          [tray_x,y,z], 24),
                f"{name}_SOCKET_COLLAR", "resonator_mount", "rfs_module",
                "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
                "Socket tolerance, keying, isolation, wear and insert retention review",
                "Printable keyed-collar reference",
                maintainable=True, attachment_parent=tray, panel_access=panel,
                configuration=f"DUAL_SPIRAL_{spiral_name}",
                component_role=role, manufacturing_state="PRINTABLE_SOCKET_COLLAR"
            )
            add_envelope(
                scene, records, sphere(0.018,[x,y,z],1),
                f"M3_SERVICE_CLEARANCE_RESONATOR_{spiral_name}_{i+1:02d}",
                "service_clearance","serviceability",name,
                "DERIVED_MAINTENANCE_ENVELOPE",
                "Confirm insert isolation and service clearance",
                "Derived resonator socket clearance",
                configuration=f"DUAL_SPIRAL_{spiral_name}", component_role=role
            )
            outward = np.array([0,y,z],dtype=float); outward /= np.linalg.norm(outward)
            add_envelope(
                scene, records,
                cylinder_between(np.array([x,y,z]), np.array([x,y,z])+outward*0.075, 0.009, 12),
                f"M3_REMOVAL_PATH_RESONATOR_{spiral_name}_{i+1:02d}",
                "removal_path","serviceability",name,
                "DERIVED_MAINTENANCE_ENVELOPE",
                "Confirm keyed insert replacement through the nearest service panel",
                "Derived resonator removal path",
                configuration=f"DUAL_SPIRAL_{spiral_name}", component_role=role
            )

    # Energy: isolated CPU power, two paired capacitor assemblies/four cells and controller.
    add_node(
        scene, records, box([0.13,0.085,0.038],[-0.19,0,0.105],0),
        "M3_BATTERY_BMS", "energy", "free_flow_energy_bus",
        "SOURCE_RECONCILED_TOPOLOGY",
        "Measured capacity, DCIR, BMS, containment, thermal and fault-response review",
        "Isolated primary CPU/control power source at original top location",
        maintainable=True, cable_required=True, attachment_parent="M3_INTERNAL_DECK_UPPER_CONTROL",
        cable_route="M3_HARNESS_TRUNK_02",
        service_clearance="M3_SERVICE_CLEARANCE_BATTERY_BMS",
        removal_path="M3_REMOVAL_PATH_BATTERY_BMS",
        panel_access="M3_SHELL_PANEL_A01_S02",
        component_role="ISOLATED_CONTROL_POWER"
    )
    add_envelope(scene,records,box([0.17,0.12,0.075],[-0.19,0,0.105],0),
                 "M3_SERVICE_CLEARANCE_BATTERY_BMS","service_clearance","serviceability",
                 "M3_BATTERY_BMS","DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm fault containment, cooling and access","Derived battery service volume")
    add_envelope(scene,records,box([0.17,0.13,0.07],[-0.19,0,0.20],0),
                 "M3_REMOVAL_PATH_BATTERY_BMS","removal_path","serviceability",
                 "M3_BATTERY_BMS","DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm isolated battery replacement through top panel","Derived battery removal volume")

    cap_x = (-0.21,-0.07,0.07,0.21)
    for assembly in range(2):
        tray_name=f"M3_CAPACITOR_ASSEMBLY_{assembly+1:02d}_TRAY"
        tray_center=[sum(cap_x[assembly*2:assembly*2+2])/2,-0.055,0.035]
        add_node(scene,records,box([0.18,0.09,0.012],tray_center,0),tray_name,
                 "energy_tray","free_flow_energy_bus",
                 "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
                 "Tray isolation, containment, thermal path and insert review",
                 "Two source capacitor assemblies, each carrying two replaceable cells",
                 maintainable=True,attachment_parent="M3_INTERNAL_DECK_MID_ENERGY",
                 panel_access=f"M3_SHELL_PANEL_A{1 if assembly==0 else 3:02d}_S05",
                 manufacturing_state="PRINTABLE_ENERGY_TRAY_REFERENCE")
        for local in range(2):
            idx=assembly*2+local
            name=f"M3_CAPACITOR_CELL_{idx+1:02d}"
            center=[cap_x[idx],-0.055,0.035]
            add_node(scene,records,box([0.075,0.050,0.050],center,0),name,
                     "energy","free_flow_energy_bus",
                     "SOURCE_RECONCILED_TOPOLOGY",
                     "Measured capacitance, ESR, voltage, pulse, containment and thermal review",
                     "Four-cell visual bank reconciled as two paired assemblies",
                     maintainable=True,cable_required=True,attachment_parent=tray_name,
                     cable_route="M3_HARNESS_TRUNK_05",
                     service_clearance=f"M3_SERVICE_CLEARANCE_CAP_CELL_{idx+1:02d}",
                     removal_path=f"M3_REMOVAL_PATH_CAP_CELL_{idx+1:02d}",
                     panel_access=f"M3_SHELL_PANEL_A{1 if idx<2 else 3:02d}_S05",
                     component_role=f"CAPACITOR_ASSEMBLY_{assembly+1:02d}_CELL_{local+1:02d}")
            add_envelope(scene,records,box([0.095,0.075,0.075],center,0),
                         f"M3_SERVICE_CLEARANCE_CAP_CELL_{idx+1:02d}",
                         "service_clearance","serviceability",name,
                         "DERIVED_MAINTENANCE_ENVELOPE",
                         "Confirm cell cooling, isolation and tool access",
                         "Derived capacitor-cell service volume")
            add_envelope(scene,records,box([0.095,0.09,0.07],
                                           [center[0],center[1]-0.085,center[2]],0),
                         f"M3_REMOVAL_PATH_CAP_CELL_{idx+1:02d}",
                         "removal_path","serviceability",name,
                         "DERIVED_MAINTENANCE_ENVELOPE",
                         "Confirm cell replacement path through energy panel",
                         "Derived capacitor-cell removal volume")

    ctrl="M3_CONTROLLER_DSP"
    add_node(scene,records,box([0.14,0.075,0.035],[0.06,0,0.108],0),ctrl,
             "controller","controls","SOURCE_ALIGNED_TOPOLOGY",
             "Controller hardware, firmware, EMC, fail-safe and evidence-chain review",
             "Central controller/DSP restored to original upper-control zone",
             maintainable=True,cable_required=True,attachment_parent="M3_INTERNAL_DECK_UPPER_CONTROL",
             cable_route="M3_HARNESS_TRUNK_02",
             service_clearance="M3_SERVICE_CLEARANCE_CONTROLLER",
             removal_path="M3_REMOVAL_PATH_CONTROLLER",
             panel_access="M3_SHELL_PANEL_A02_S02")
    add_node(scene,records,box([0.055,0.045,0.025],[0.19,0,0.108],0),
             "M3_CPU_ISOLATION_POWER_CONDITIONER","controller","controls",
             "PROVISIONAL_INTERFACE_REFERENCE",
             "Isolation, filtering, grounding, power integrity and thermal review",
             "Original isolated CPU/control-power function represented separately from the battery",
             maintainable=True,cable_required=True,attachment_parent=ctrl,
             cable_route="M3_HARNESS_TRUNK_02",panel_access="M3_SHELL_PANEL_A03_S02")
    add_envelope(scene,records,box([0.18,0.11,0.075],[0.06,0,0.108],0),
                 "M3_SERVICE_CLEARANCE_CONTROLLER","service_clearance","serviceability",ctrl,
                 "DERIVED_MAINTENANCE_ENVELOPE","Confirm controller cooling and access",
                 "Derived controller service volume")
    add_envelope(scene,records,box([0.18,0.12,0.075],[0.06,0,0.20],0),
                 "M3_REMOVAL_PATH_CONTROLLER","removal_path","serviceability",ctrl,
                 "DERIVED_MAINTENANCE_ENVELOPE","Confirm controller removal through top panel",
                 "Derived controller removal path")

    # Four side damping/isolation chambers.
    damp_centres=[(-0.20,0.115,0.0),(-0.20,-0.115,0.0),(0.20,0.115,0.0),(0.20,-0.115,0.0)]
    for idx,c in enumerate(damp_centres,start=1):
        name=f"M3_DAMPING_PLACEHOLDER_{idx:02d}"
        add_node(scene,records,cylinder_x(0.018,0.065,c,20),name,"damping","damping_isolation",
                 "PROVISIONAL_INTERFACE_REFERENCE",
                 "Specialist medium, pressure, containment, venting, EMI and hazard review",
                 "Original post-launch gas-chamber claim reduced to an unpressurised envelope",
                 maintainable=True,cable_required=True,attachment_parent="M3_BULKHEAD_RING_02",
                 cable_route=f"M3_HARNESS_TRUNK_{1 if c[1]>0 else 4:02d}",
                 service_clearance=f"M3_SERVICE_CLEARANCE_DAMPING_{idx:02d}",
                 removal_path=f"M3_REMOVAL_PATH_DAMPING_{idx:02d}",
                 panel_access=f"M3_SHELL_PANEL_A{1 if c[0]<0 else 3:02d}_S{1 if c[1]>0 else 4:02d}")
        add_envelope(scene,records,sphere(0.038,c,1),
                     f"M3_SERVICE_CLEARANCE_DAMPING_{idx:02d}",
                     "service_clearance","serviceability",name,
                     "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm containment and isolation access","Derived damping clearance")
        outward=np.array([0,c[1],c[2]],float);outward/=np.linalg.norm(outward)
        add_envelope(scene,records,cylinder_between(np.array(c),np.array(c)+outward*0.08,0.015,12),
                     f"M3_REMOVAL_PATH_DAMPING_{idx:02d}",
                     "removal_path","serviceability",name,
                     "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm side-chamber replacement path","Derived damping removal corridor")

    # Sensors and multiple antenna interfaces.
    for idx in range(8):
        a=idx*math.pi/4; x=-0.25+idx*(0.5/7)
        c=[x,0.126*math.cos(a),0.126*math.sin(a)]
        name=f"M3_SENSOR_NODE_{idx+1:02d}"
        sector=int(((a%(2*math.pi))/(2*math.pi/6)))+1
        panel=f"M3_SHELL_PANEL_A{1 if x<-.11 else 3 if x>.11 else 2:02d}_S{sector:02d}"
        add_node(scene,records,box([0.018,0.014,0.014],c,a),name,"sensor","sensor_comms",
                 "SOURCE_ALIGNED_TOPOLOGY",
                 "Calibration, placement, synchronization, bandwidth and EMI review",
                 "Eight source sensor nodes; locations reconciled with original perimeter layout",
                 maintainable=True,cable_required=True,attachment_parent=panel,
                 cable_route=f"M3_HARNESS_TRUNK_{sector:02d}",
                 service_clearance=f"M3_CONNECTOR_ACCESS_SENSOR_{idx+1:02d}",
                 panel_access=panel)
        add_envelope(scene,records,box([0.045,0.035,0.035],c,a),
                     f"M3_CONNECTOR_ACCESS_SENSOR_{idx+1:02d}",
                     "connector_access","serviceability",name,
                     "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm calibration and connector access","Derived sensor access volume")
    antenna_specs=[(-0.22,-0.025),(-0.07,0.015),(0.08,-0.015),(0.23,0.025)]
    for idx,(x,y) in enumerate(antenna_specs,start=1):
        base=[x,y,0.155];tip=[x,y,0.245+0.015*(idx%2)]
        name=f"M3_COMMS_ANTENNA_{idx:02d}"
        add_node(scene,records,cylinder_between(base,tip,0.0045,14),name,"comms","sensor_comms",
                 "SOURCE_RECONCILED_TOPOLOGY",
                 "RF allocation, EMC, deployment, grounding and environmental review",
                 "Multiple specialized survey/communication antenna interfaces from original schematic",
                 maintainable=True,cable_required=True,attachment_parent="M3_SHELL_PANEL_A02_S02",
                 cable_route="M3_HARNESS_TRUNK_02",
                 service_clearance=f"M3_SERVICE_CLEARANCE_COMMS_{idx:02d}",
                 removal_path=f"M3_REMOVAL_PATH_COMMS_{idx:02d}",
                 panel_access="M3_SHELL_PANEL_A02_S02")
        add_envelope(scene,records,cylinder_between([x,y,0.14],[x,y,0.28],0.018,12),
                     f"M3_SERVICE_CLEARANCE_COMMS_{idx:02d}",
                     "service_clearance","serviceability",name,
                     "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm articulation and keep-out","Derived antenna clearance")
        add_envelope(scene,records,cylinder_between([x,y,0.18],[x,y,0.34],0.012,12),
                     f"M3_REMOVAL_PATH_COMMS_{idx:02d}",
                     "removal_path","serviceability",name,
                     "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm antenna replacement path","Derived antenna removal corridor")


def build_propulsion_reference(scene: trimesh.Scene, records: list[dict[str, Any]],
                               p: dict[str, Any]) -> None:
    """Restore the original drawing's propulsion/reservoir callout as inert interface volumes.

    No propellant, pressure, nozzle, thrust or operational propulsion parameter is
    assigned. Fluid-route geometry is a nonphysical volume reservation only.
    """
    d = p["derived_configuration"]
    radius = p["source_parameters"]["outer_radius_m"]["value"]
    interface_radius = d["propulsion_thruster_interface_radius_m"]
    interface_length = d["propulsion_thruster_interface_length_m"]
    angles = [math.radians(value) for value in d["propulsion_thruster_interface_angles_deg"]]

    reservoir = "M3_PROPULSION_RESERVOIR_ALLOCATION"
    reservoir_center = np.asarray(d["propulsion_reservoir_reference_center_m"], dtype=float)
    reservoir_extents = d["propulsion_reservoir_reference_extents_m"]
    add_node(
        scene, records,
        box(reservoir_extents, reservoir_center, 0),
        reservoir, "reservoir_placeholder", "propulsion_reference",
        "PROVISIONAL_INTERFACE_REFERENCE",
        "Select working fluid/propellant, vessel construction, pressure, isolation, venting, thermal, contamination and hazard controls before any physical reservoir design",
        "Original refillable-fuel-reservoir callout restored only as an unpressurised packaging allocation",
        maintainable=True, attachment_parent="M3_INTERNAL_DECK_LOWER_FIELD",
        service_clearance="M3_SERVICE_CLEARANCE_PROPULSION_RESERVOIR",
        removal_path="M3_REMOVAL_PATH_PROPULSION_RESERVOIR",
        panel_access="M3_SHELL_PANEL_A03_S05",
        component_role="UNPRESSURISED_RESERVOIR_ALLOCATION_ONLY"
    )
    add_envelope(
        scene, records,
        box([reservoir_extents[0] + 0.04, reservoir_extents[1] + 0.04, reservoir_extents[2] + 0.04],
            reservoir_center, 0),
        "M3_SERVICE_CLEARANCE_PROPULSION_RESERVOIR",
        "service_clearance", "serviceability", reservoir,
        "DERIVED_MAINTENANCE_ENVELOPE",
        "Confirm reservoir, valve and restraint access after hardware selection",
        "Derived maintenance allocation around unpressurised reservoir placeholder"
    )
    add_envelope(
        scene, records,
        box([0.13, 0.075, 0.06], [0.31, 0.0, -0.118], 0),
        "M3_REMOVAL_PATH_PROPULSION_RESERVOIR",
        "removal_path", "serviceability", reservoir,
        "DERIVED_MAINTENANCE_ENVELOPE",
        "Confirm reservoir removal through rear/lower service opening after structure and vessel selection",
        "Derived removal corridor; not a pressure-system design"
    )

    # Refill/service port at the lower exterior. This is an interface allocation,
    # not a selected fill connector or pressure fitting.
    service_a = -math.pi / 2
    service_base = np.array([0.24, radius * math.cos(service_a), radius * math.sin(service_a)])
    service_tip = np.array([
        0.24,
        (radius + d["propulsion_service_port_length_m"]) * math.cos(service_a),
        (radius + d["propulsion_service_port_length_m"]) * math.sin(service_a),
    ])
    service_port = "M3_PROPULSION_REFILL_SERVICE_PORT"
    add_node(
        scene, records,
        cylinder_between(service_base, service_tip, d["propulsion_service_port_radius_m"], 18),
        service_port, "propulsion_service_port", "propulsion_reference",
        "PROVISIONAL_INTERFACE_REFERENCE",
        "Select qualified fill/service connector, isolation, caps, venting, contamination controls and access after propulsion architecture is chosen",
        "Original refillable-reservoir concept requires an external service interface; geometry is allocation-only",
        maintainable=True, attachment_parent="M3_SHELL_PANEL_A03_S05",
        service_clearance="M3_SERVICE_CLEARANCE_PROPULSION_REFILL_PORT",
        panel_access="M3_SHELL_PANEL_A03_S05",
        component_role="REFILL_SERVICE_INTERFACE_ALLOCATION_ONLY"
    )
    add_envelope(
        scene, records,
        cylinder_between(
            service_base - np.array([0.0, 0.0, 0.025]),
            service_tip - np.array([0.0, 0.0, 0.040]),
            0.022, 16
        ),
        "M3_SERVICE_CLEARANCE_PROPULSION_REFILL_PORT",
        "service_clearance", "serviceability", service_port,
        "DERIVED_MAINTENANCE_ENVELOPE",
        "Confirm external hand/tool access, cap removal and contamination-control envelope",
        "Derived refill/service keep-out"
    )
    add_envelope(
        scene, records,
        polyline_tube(
            [reservoir_center, [0.24, 0.0, -0.145], service_base.tolist()],
            d["propulsion_route_reservation_radius_m"], 10
        ),
        "M3_PROPULSION_FILL_ROUTE_RESERVATION",
        "fluid_route_reservation", "propulsion_reference", reservoir,
        "DERIVED_SPATIAL_REFERENCE",
        "Reserve routing volume only; line material, diameter, fittings, pressure and medium remain unselected",
        "Nonphysical reservoir-to-service-port corridor",
        configuration="ROUTE_RESERVATION_ONLY"
    )

    # Four source-visible corner thruster/attitude-control interfaces.
    # Their geometry is intentionally generic and excludes nozzle/thrust parameters.
    for idx, angle in enumerate(angles, start=1):
        inward_r = radius - 0.012
        outward_r = radius + interface_length
        base = np.array([0.0, inward_r * math.cos(angle), inward_r * math.sin(angle)])
        tip = np.array([0.0, outward_r * math.cos(angle), outward_r * math.sin(angle)])
        sector = int(((angle % (2 * math.pi)) / (2 * math.pi / 6))) + 1
        panel = f"M3_SHELL_PANEL_A02_S{sector:02d}"
        route = f"M3_HARNESS_TRUNK_{sector:02d}"
        name = f"M3_PROPULSION_INTERFACE_{idx:02d}"
        clearance = f"M3_SERVICE_CLEARANCE_PROPULSION_INTERFACE_{idx:02d}"
        removal = f"M3_REMOVAL_PATH_PROPULSION_INTERFACE_{idx:02d}"
        add_node(
            scene, records,
            cylinder_between(base, tip, interface_radius, 20),
            name, "propulsion_interface", "propulsion_reference",
            "SOURCE_RECONCILED_TOPOLOGY",
            "Select propulsion/attitude-control hardware, loads, thermal isolation, contamination control, electrical interface and safe operating envelope",
            "Four source-visible thruster locations restored as generic hardware interface envelopes only",
            maintainable=True, cable_required=True,
            attachment_parent=panel, cable_route=route,
            service_clearance=clearance, removal_path=removal, panel_access=panel,
            component_role="PROPULSION_OR_ATTITUDE_CONTROL_INTERFACE_ONLY"
        )
        radial = np.array([0.0, math.cos(angle), math.sin(angle)])
        add_envelope(
            scene, records,
            cylinder_between(base - radial * 0.020, tip + radial * 0.045, 0.026, 16),
            clearance, "service_clearance", "serviceability", name,
            "DERIVED_MAINTENANCE_ENVELOPE",
            "Confirm hardware installation, connector access, thermal clearance and external keep-out",
            "Derived generic propulsion-interface clearance"
        )
        add_envelope(
            scene, records,
            cylinder_between(tip, tip + radial * 0.090, 0.020, 16),
            removal, "removal_path", "serviceability", name,
            "DERIVED_MAINTENANCE_ENVELOPE",
            "Confirm outward replacement/removal corridor after hardware selection",
            "Derived generic propulsion-interface removal path"
        )
        # Reserve volume from the reservoir allocation to each interface. This is
        # deliberately not a pipe, pressure line or selected plumbing geometry.
        waypoint = np.array([0.16 if idx <= 2 else 0.05, 0.0, -0.105])
        inner = np.array([0.0, (radius - 0.035) * math.cos(angle), (radius - 0.035) * math.sin(angle)])
        add_envelope(
            scene, records,
            polyline_tube(
                [reservoir_center, waypoint, inner],
                d["propulsion_route_reservation_radius_m"], 10
            ),
            f"M3_PROPULSION_ROUTE_RESERVATION_{idx:02d}",
            "fluid_route_reservation", "propulsion_reference", reservoir,
            "DERIVED_SPATIAL_REFERENCE",
            "Reserve service-routing volume only; no pipe diameter, medium, pressure, valve or fitting is defined",
            "Nonphysical reservoir-to-interface routing corridor",
            configuration="ROUTE_RESERVATION_ONLY"
        )


def build_harnesses(scene: trimesh.Scene, records: list[dict[str, Any]],
                    p: dict[str, Any]) -> None:
    d=p["derived_configuration"];tray_radius=d["cable_tray_radius_m"]
    for idx in range(6):
        a=idx*math.pi/3
        c=[0,tray_radius*math.cos(a),tray_radius*math.sin(a)]
        tray=f"M3_CABLE_TRAY_{idx+1:02d}";trunk=f"M3_HARNESS_TRUNK_{idx+1:02d}"
        bend=f"M3_CABLE_BEND_SPACE_{idx+1:02d}"
        add_node(scene,records,
                 box([0.59,d["cable_tray_section_m"][0],d["cable_tray_section_m"][1]],c,a),
                 tray,"cable_tray","electrical_data","DERIVED_SPATIAL_REFERENCE",
                 "Cable fill, support spacing, bonding, thermal and EMI separation review",
                 "Six longitudinal trays align with shell/solenoid sectors",
                 maintainable=True,attachment_parent=f"M3_LONGITUDINAL_RAIL_{idx+1:02d}",
                 panel_access=f"M3_SHELL_PANEL_A02_S{idx+1:02d}")
        add_node(scene,records,
                 cylinder_between([-0.285,c[1],c[2]],[0.285,c[1],c[2]],0.0040,14),
                 trunk,"harness","electrical_data","DERIVED_SPATIAL_REFERENCE",
                 "Select conductor gauges, shielding, grounding, isolation and connector families",
                 "Derived common trunk; no current/data rating",
                 maintainable=True,attachment_parent=tray,
                 panel_access=f"M3_SHELL_PANEL_A02_S{idx+1:02d}")
        add_envelope(scene,records,
                     cylinder_x(d["cable_minimum_bend_radius_m"],0.06,[0.30,c[1],c[2]],18),
                     bend,"cable_bend_space","serviceability",trunk,
                     "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm selected cable minimum bend radius",
                     "Derived cable bend reservation")
    # Two ring cross-links connect all six trunks.
    for ring_idx,x in enumerate((-0.12,0.12),start=1):
        pts=[]
        for seg in range(7):
            a=(seg%6)*math.pi/3
            pts.append([x,tray_radius*math.cos(a),tray_radius*math.sin(a)])
        for seg,(p0,p1) in enumerate(zip(pts,pts[1:]),start=1):
            add_node(scene,records,cylinder_between(p0,p1,0.0032,12),
                     f"M3_HARNESS_CROSSLINK_R{ring_idx:02d}_S{seg:02d}",
                     "harness","electrical_data","DERIVED_SPATIAL_REFERENCE",
                     "Cable routing, bend, separation and support review",
                     "Derived six-sector harness cross-link",
                     maintainable=True,attachment_parent=f"M3_BULKHEAD_RING_{ring_idx+1:02d}",
                     panel_access=f"M3_SHELL_PANEL_A02_S{seg:02d}")
    # Interleaved resonator A/B buses.
    pconf=p["derived_configuration"];tx=pconf["resonator_tray_x_m"]
    start_r=pconf["resonator_spiral_start_radius_m"];end_r=pconf["resonator_spiral_end_radius_m"]
    step=math.radians(pconf["resonator_spiral_step_angle_deg"])
    phase=math.radians(pconf["resonator_spiral_phase_offset_deg"])
    for label,offset in (("A",0.0),("B",phase)):
        points=[]
        for i in range(12):
            frac=i/11;r=start_r+frac*(end_r-start_r);a=offset+i*step
            points.append([tx+(0.006 if i%2==0 else -0.006),r*math.cos(a),r*math.sin(a)])
        add_node(scene,records,polyline_tube(points,0.0025,10),
                 f"M3_RESONATOR_BUS_{label}","harness","rfs_module",
                 "DERIVED_SPATIAL_REFERENCE",
                 "Drive topology, grounding, channel isolation and sensor synchronization review",
                 f"Independent bus for spiral {label}; supports alternating, paired and swept modes",
                 maintainable=True,attachment_parent="M3_RESONATOR_TRAY",
                 panel_access="M3_SHELL_PANEL_A02_S02",
                 configuration=f"DUAL_SPIRAL_{label}")
    # Dedicated energy and control trunks.
    add_node(scene,records,cylinder_between([-0.28,-0.105,0.035],[0.28,-0.105,0.035],0.0045,14),
             "M3_ENERGY_BUS","harness","free_flow_energy_bus",
             "DERIVED_SPATIAL_REFERENCE",
             "Busbar/conductor sizing, insulation, fault current, grounding and thermal review",
             "Derived low-level energy-distribution route; rating unassigned",
             maintainable=True,attachment_parent="M3_INTERNAL_DECK_MID_ENERGY",
             panel_access="M3_SHELL_PANEL_A02_S05")


def build_arm(scene: trimesh.Scene, records: list[dict[str, Any]],
              p: dict[str, Any], arm_idx: int, side: float) -> None:
    a=p["derived_configuration"]["arm"];prefix=f"M3_ARM_{arm_idx:02d}"
    panel=f"M3_SHELL_PANEL_A02_S{1 if side>0 else 4:02d}"
    base=np.array([0.0,0.157*side,-0.025])
    route=f"{prefix}_CABLE_CHAIN"
    add_node(scene,records,cylinder_between(base-np.array([0,0.018*side,0]),base+np.array([0,0.020*side,0]),
                                            a["base_radius_m"],28),
             f"{prefix}_BASE_INTERFACE","arm","arm_system",
             "SOURCE_RECONCILED_TOPOLOGY",
             "Base load, latch, sealing, alignment, collision and conductive bonding review",
             "Bilateral original arm mount restored on the body sides",
             maintainable=True,cable_required=True,attachment_parent=panel,cable_route=route,
             service_clearance=f"{prefix}_BASE_CLEARANCE",
             removal_path=f"{prefix}_REMOVAL_PATH",panel_access=panel,
             manufacturing_state="PRINTED_BASE_WITH_METAL_INSERTS_PENDING_TEST")
    add_node(scene,records,cylinder_between(base-np.array([0.030,0,0]),base+np.array([0.030,0,0]),0.030,24),
             f"{prefix}_BASE_MOTOR_SPOOL","arm_actuator","arm_system",
             "PROVISIONAL_INTERFACE_REFERENCE",
             "Motor, spool, Kevlar/tendon, lock, brake, torque, fatigue and thermal review",
             "Original motor/Kevlar spool function retained as an interface envelope",
             maintainable=True,cable_required=True,attachment_parent=f"{prefix}_BASE_INTERFACE",
             cable_route=route,panel_access=panel)
    add_node(scene,records,box([0.028,0.018,0.018],base+np.array([0.035,0,0]),0),
             f"{prefix}_SPOOL_LOCK","arm_actuator","arm_system",
             "PROVISIONAL_INTERFACE_REFERENCE",
             "Fail-safe lock, release, wear, jam and load-hold review",
             "Energy-saving spool-lock reference",
             maintainable=True,attachment_parent=f"{prefix}_BASE_MOTOR_SPOOL",panel_access=panel)

    n=a["link_segment_count"];points=[base]
    for i in range(1,n+1):
        t=i/n
        y=side*(0.165+0.115*math.sin(math.pi*t))
        z=-0.025-0.070*i
        x=0.030*math.sin(2*math.pi*t + (0 if arm_idx==1 else math.pi))
        points.append(np.array([x,y,z]))
    # Joints and modular octagonal segments.
    previous_parent=f"{prefix}_BASE_INTERFACE"
    for i in range(1,len(points)):
        p0,p1=points[i-1],points[i]
        joint_name=f"{prefix}_JOINT_{i:02d}"
        link_name=f"{prefix}_SEGMENT_{i:02d}"
        add_node(scene,records,sphere(a["joint_radius_m"],p0,2),joint_name,
                 "arm_joint","arm_system","DERIVED_SPATIAL_REFERENCE",
                 "Joint type, range, load, hard stop, sealing, friction and life review",
                 "Segmented joint restores the original chain-arm silhouette",
                 maintainable=True,cable_required=True,attachment_parent=previous_parent,
                 cable_route=route,service_clearance=f"{joint_name}_CLEARANCE",panel_access=panel)
        add_node(scene,records,cylinder_between(p0,p1,a["link_radius_m"],8),link_name,
                 "arm","arm_system","MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
                 "Segment material, inserts, plating, buckling, fatigue and impact review",
                 "Octagonal modular link based on the original arm segments",
                 maintainable=True,cable_required=True,attachment_parent=joint_name,
                 cable_route=route,panel_access=panel,
                 manufacturing_state="PRINTABLE_ARM_LINK_REFERENCE",
                 print_part=f"ARM_LINK_{i:02d}")
        unit=(p1-p0)/np.linalg.norm(p1-p0)
        for coil in range(a["segment_solenoid_reference_count"]):
            q=p0+(coil+1)/(a["segment_solenoid_reference_count"]+1)*(p1-p0)
            add_node(scene,records,cylinder_between(q-unit*0.006,q+unit*0.006,0.0065,14),
                     f"{link_name}_COIL_{coil+1:02d}","arm_solenoid_reference","arm_system",
                     "QUARANTINED_UNVERIFIED_NOT_USED_FOR_CAPABILITY",
                     "Determine whether segment coils are sensing, actuation or field elements; measure all electrical/thermal limits",
                     "Original three-solenoids-per-segment visual/function retained only as internal envelopes",
                     maintainable=True,cable_required=True,attachment_parent=link_name,
                     cable_route=route,panel_access=panel)
        add_node(scene,records,sphere(a["joint_radius_m"]*0.58,p0,1),
                 f"{joint_name}_GAS_CHAMBER_PLACEHOLDER","arm_gas_joint","arm_system",
                 "PROVISIONAL_INTERFACE_REFERENCE",
                 "No pressurization until medium, vessel, seal, vent and failure containment are qualified",
                 "Original gas-compressed joint concept represented as an unpressurised placeholder",
                 maintainable=True,attachment_parent=joint_name,panel_access=panel)
        add_envelope(scene,records,sphere(a["service_clearance_radius_m"],p0,1),
                     f"{joint_name}_CLEARANCE","service_clearance","serviceability",joint_name,
                     "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm articulation, tool access and collision keep-out",
                     "Derived joint clearance")
        previous_parent=link_name
    tip=points[-1];prev=points[-2];direction=(tip-prev)/np.linalg.norm(tip-prev)
    pad_end=tip+direction*a["collector_pad_thickness_m"]
    add_node(scene,records,cylinder_between(tip,pad_end,a["collector_pad_radius_m"],8),
             f"{prefix}_COLLECTOR_PAD","collector_pad","arm_system",
             "PROVISIONAL_INTERFACE_REFERENCE",
             "Collector/end-effector purpose, loads, sensor content, contact hazards and environmental review",
             "Octagonal end pad reflects the original paired Mark III visual; no capture/extraction claim",
             maintainable=True,cable_required=True,attachment_parent=previous_parent,
             cable_route=route,service_clearance=f"{prefix}_END_CLEARANCE",panel_access=panel)
    add_node(scene,records,annulus_between(tip+direction*0.002,pad_end-direction*0.002,0.018,0.028,24),
             f"{prefix}_END_COUPLER","coupler","arm_system",
             "PROVISIONAL_INTERFACE_REFERENCE",
             "Select tool/sample interface, latch, alignment and release system",
             "Replaceable end-effector coupling reference",
             maintainable=True,attachment_parent=f"{prefix}_COLLECTOR_PAD",panel_access=panel)
    add_node(scene,records,polyline_tube(points, a["cable_chain_radius_m"],12),
             route,"harness","arm_system","DERIVED_SPATIAL_REFERENCE",
             "Cable/tendon bend, torsion, abrasion, strain relief and segment replacement review",
             "Continuous routed arm harness through all modular joints",
             maintainable=True,attachment_parent=f"{prefix}_BASE_INTERFACE",panel_access=panel)
    add_envelope(scene,records,sphere(a["service_clearance_radius_m"]*1.2,pad_end,1),
                 f"{prefix}_END_CLEARANCE","service_clearance","serviceability",
                 f"{prefix}_COLLECTOR_PAD","DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm end-effector articulation and keep-out","Derived end clearance")
    add_envelope(scene,records,cylinder_between(base,pad_end,0.075,16),
                 f"{prefix}_REMOVAL_PATH","removal_path","serviceability",
                 f"{prefix}_BASE_INTERFACE","DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm complete arm removal, handling support and plated-surface protection",
                 "Derived complete arm removal corridor")


def build_central_probe(scene: trimesh.Scene, records: list[dict[str, Any]],
                        p: dict[str, Any]) -> None:
    c=p["derived_configuration"]["central_probe"];prefix="M3_CENTRAL_PROBE"
    panel="M3_SHELL_PANEL_A02_S05";route=f"{prefix}_HARNESS"
    points=[np.array([0.0,0.0,-0.155])]
    for i in range(1,c["segment_count"]+1):
        points.append(np.array([0.012*math.sin(i*math.pi/3),0.0,
                                -0.155-i*c["segment_length_m"]]))
    add_node(scene,records,cylinder_between(points[0]-np.array([0,0,0.018]),points[0],
                                            c["joint_radius_m"],24),
             f"{prefix}_BASE_INTERFACE","probe_mast","probe_system",
             "SOURCE_RECONCILED_TOPOLOGY",
             "Probe/mast base load, sealing, deployment, collision and instrumentation review",
             "Central segmented appendage restored from original schematic",
             maintainable=True,cable_required=True,attachment_parent=panel,cable_route=route,
             service_clearance=f"{prefix}_BASE_CLEARANCE",
             removal_path=f"{prefix}_REMOVAL_PATH",panel_access=panel)
    parent=f"{prefix}_BASE_INTERFACE"
    for i,(p0,p1) in enumerate(zip(points,points[1:]),start=1):
        joint=f"{prefix}_JOINT_{i:02d}";seg=f"{prefix}_SEGMENT_{i:02d}"
        add_node(scene,records,sphere(c["joint_radius_m"],p0,1),joint,
                 "arm_joint","probe_system","DERIVED_SPATIAL_REFERENCE",
                 "Joint range, stiffness, sealing, hard-stop and life review",
                 "Central mast joint reference",maintainable=True,cable_required=True,
                 attachment_parent=parent,cable_route=route,
                 service_clearance=f"{joint}_CLEARANCE",panel_access=panel)
        add_node(scene,records,cylinder_between(p0,p1,c["link_radius_m"],8),seg,
                 "probe_mast","probe_system",
                 "MANUFACTURING_REFERENCE_PENDING_PROCESS_QUALIFICATION",
                 "Segment material, insert, plating, stiffness and fatigue review",
                 "Printable central mast segment reference",maintainable=True,cable_required=True,
                 attachment_parent=joint,cable_route=route,panel_access=panel,
                 manufacturing_state="PRINTABLE_PROBE_SEGMENT_REFERENCE",
                 print_part=f"PROBE_SEGMENT_{i:02d}")
        add_envelope(scene,records,sphere(0.042,p0,1),f"{joint}_CLEARANCE",
                     "service_clearance","serviceability",joint,
                     "DERIVED_MAINTENANCE_ENVELOPE",
                     "Confirm articulation and body/arm collision keep-out",
                     "Derived probe joint clearance")
        parent=seg
    tip=points[-1]
    add_node(scene,records,sphere(c["instrument_head_radius_m"],tip,2),
             f"{prefix}_INSTRUMENT_HEAD","sensor","probe_system",
             "PROVISIONAL_INTERFACE_REFERENCE",
             "Define survey, assay, imaging and telemetry payload and calibration",
             "Original central appendage terminated as a replaceable instrument head",
             maintainable=True,cable_required=True,attachment_parent=parent,cable_route=route,
             service_clearance=f"{prefix}_HEAD_CLEARANCE",panel_access=panel)
    add_node(scene,records,polyline_tube(points,0.0055,12),route,
             "harness","probe_system","DERIVED_SPATIAL_REFERENCE",
             "Harness bend, deployment, strain relief and sensor isolation review",
             "Central probe routed harness",maintainable=True,
             attachment_parent=f"{prefix}_BASE_INTERFACE",panel_access=panel)
    add_envelope(scene,records,sphere(0.055,tip,1),f"{prefix}_HEAD_CLEARANCE",
                 "service_clearance","serviceability",f"{prefix}_INSTRUMENT_HEAD",
                 "DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm instrument head keep-out and replacement access",
                 "Derived head clearance")
    add_envelope(scene,records,cylinder_between(points[0],tip,0.050,16),
                 f"{prefix}_REMOVAL_PATH","removal_path","serviceability",
                 f"{prefix}_BASE_INTERFACE","DERIVED_MAINTENANCE_ENVELOPE",
                 "Confirm mast removal and handling path","Derived mast removal corridor")

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



def build_field_guides(scene: trimesh.Scene, records: list[dict[str, Any]],
                       p: dict[str, Any]) -> None:
    for idx,r in enumerate((0.055,0.085,0.115),start=1):
        add_envelope(scene,records,annulus_x(r-0.002,r+0.002,0.50,[0,0,0],48),
                     f"M3_FIELD_GUIDE_{idx:02d}","field_guide","emff_module",
                     "ILLUSTRATIVE_REFERENCE_ROOT","ILLUSTRATIVE_ONLY_NOT_PHYSICAL_PERFORMANCE",
                     "Replace with measured synchronized field maps",
                     "Illustrative spatial guide only; no field-strength evidence")
    d=p["derived_configuration"];tx=d["resonator_tray_x_m"]
    start_r=d["resonator_spiral_start_radius_m"];end_r=d["resonator_spiral_end_radius_m"]
    step=math.radians(d["resonator_spiral_step_angle_deg"])
    phase=math.radians(d["resonator_spiral_phase_offset_deg"])
    for label,offset in (("A",0.0),("B",phase)):
        pts=[]
        for i in range(12):
            frac=i/11;r=start_r+frac*(end_r-start_r);a=offset+i*step
            pts.append([tx+(0.010 if label=="A" else -0.010),r*math.cos(a),r*math.sin(a)])
        add_envelope(scene,records,polyline_tube(pts,0.0018,10),
                     f"M3_RESONATOR_GUIDE_SPIRAL_{label}",
                     "resonator_guide","rfs_module","ILLUSTRATIVE_REFERENCE_ROOT",
                     "ILLUSTRATIVE_ONLY_NOT_PHYSICAL_PERFORMANCE",
                     "Review dual-spiral ordering, role assignment and independent A/B drive modes",
                     f"Interleaved spiral {label} guide",configuration=f"SPIRAL_{label}")
    for idx,r in enumerate((0.050,0.082,0.112),start=1):
        add_envelope(scene,records,annulus_x(r-0.0015,r+0.0015,0.004,[tx,0,0],48),
                     f"M3_RESONATOR_GUIDE_FLOWER_BAND_{idx:02d}",
                     "resonator_guide","rfs_module","ILLUSTRATIVE_REFERENCE_ROOT",
                     "ILLUSTRATIVE_ONLY_NOT_PHYSICAL_PERFORMANCE",
                     "Compare spiral sockets against central/surrounding/peripheral/support role bands",
                     "Flower-of-Life role-band guide",configuration="FLOWER_OF_LIFE_ROLE_BANDS")


def build_reference(parameters: dict[str, Any]) -> tuple[trimesh.Scene, list[dict[str, Any]]]:
    scene=trimesh.Scene();records:list[dict[str,Any]]=[]
    build_shell(scene,records,parameters)
    build_original_layout_structure(scene,records,parameters)
    build_couplers(scene,records,parameters)
    build_internal_systems(scene,records,parameters)
    build_propulsion_reference(scene,records,parameters)
    build_harnesses(scene,records,parameters)
    build_arm(scene,records,parameters,1,-1.0)
    build_arm(scene,records,parameters,2,1.0)
    build_central_probe(scene,records,parameters)
    build_array_guides(scene,records,parameters)
    build_field_guides(scene,records,parameters)
    if len(scene.geometry)!=len(records):
        raise RuntimeError("Scene/record count mismatch")
    return scene,records



def build_print_references(parameters: dict[str, Any], scene: trimesh.Scene,
                           records: list[dict[str, Any]]) -> dict[str,trimesh.Trimesh]:
    d=parameters["derived_configuration"]
    length=parameters["source_parameters"]["module_length_m"]["value"]
    radius=parameters["source_parameters"]["outer_radius_m"]["value"]
    refs:dict[str,trimesh.Trimesh]={}

    # Compact full-system display article; 1:8 is the largest complete body scale
    # that fits the 40 mm reference Z dimension.
    full=cylinder_x(radius,length,[0,0,0],64);full.apply_scale(1000/8)
    refs["mark_iii_full_module_display_1to8.stl"]=full

    def concatenate(names:list[str],scale:float=1000.0)->trimesh.Trimesh:
        meshes=[scene.geometry[n].copy() for n in names if n in scene.geometry]
        if not meshes: raise KeyError(names)
        mesh=trimesh.util.concatenate(meshes);mesh.apply_scale(scale)
        if mesh.volume<0:mesh.invert()
        return mesh

    # A common local panel geometry avoids orientation-dependent bounding boxes.
    zone_len=d["main_body_length_m"]/d["axial_panel_count"]
    x0=-zone_len/2+0.004;x1=zone_len/2-0.004
    a0=-math.pi/6+math.radians(2.0);a1=math.pi/6-math.radians(2.0);mid=0.0
    panel_meshes=[annular_sector_x(
        x0,x1,d["structural_panel_inner_radius_m"],
        d["print_substrate_outer_radius_m"],a0,a1)]
    for x in (x0+0.018,x1-0.018):
        panel_meshes.append(annulus_between(
            [x,d["structural_panel_inner_radius_m"]-0.004,0],
            [x,d["print_substrate_outer_radius_m"]+0.001,0],
            0.0016,0.0045,18))
    for x in (x0+0.006,x1-0.006):
        panel_meshes.append(annular_sector_x(
            x-0.003,x+0.003,d["print_substrate_outer_radius_m"]-0.001,
            d["print_substrate_outer_radius_m"],a0+0.012,a1-0.012))
    panel_meshes.append(annulus_between(
        [x0+0.025,d["structural_panel_inner_radius_m"]-0.004,0],
        [x0+0.025,d["electroplate_nominal_outer_radius_m"]+0.002,0],
        d["plating_drain_bore_radius_m"],
        d["plating_drain_bore_radius_m"]+0.0022,18))
    panel_meshes.append(box([0.020,0.012,0.004],
                            [(x0+x1)/2,d["structural_panel_inner_radius_m"]-0.003,0],0))
    panel=trimesh.util.concatenate(panel_meshes);panel.apply_scale(1000)
    refs["mark_iii_standard_shell_panel_1to1.stl"]=panel

    hatch_frame=[
        box([zone_len-0.035,0.006,0.006],[0,d["structural_panel_inner_radius_m"]-0.006,0.045],0),
        box([zone_len-0.035,0.006,0.006],[0,d["structural_panel_inner_radius_m"]-0.006,-0.045],0),
        box([0.006,0.006,0.084],[-zone_len/2+0.020,d["structural_panel_inner_radius_m"]-0.006,0],0),
        box([0.006,0.006,0.084],[zone_len/2-0.020,d["structural_panel_inner_radius_m"]-0.006,0],0),
    ]
    service=trimesh.util.concatenate(panel_meshes+hatch_frame);service.apply_scale(1000)
    refs["mark_iii_standard_service_panel_1to1.stl"]=service

    tray_names=["M3_RESONATOR_TRAY"]+[r["node_name"] for r in records if r["family"]=="resonator_mount"]
    refs["mark_iii_resonator_tray_25_socket_1to1.stl"]=concatenate(tray_names)

    # Split sector rail with keyed overlap.
    rail_a=box([0.270,0.010,0.014],[-0.135,0,0],0)
    rail_b=box([0.270,0.010,0.014],[0.135,0,0],0)
    key_a=box([0.018,0.018,0.008],[-0.004,0,0.008],0)
    key_b=box([0.018,0.018,0.008],[0.004,0,-0.008],0)
    refs["mark_iii_solenoid_sector_rail_half_A_1to1.stl"]=trimesh.util.concatenate([rail_a,key_a])
    refs["mark_iii_solenoid_sector_rail_half_A_1to1.stl"].apply_scale(1000)
    refs["mark_iii_solenoid_sector_rail_half_B_1to1.stl"]=trimesh.util.concatenate([rail_b,key_b])
    refs["mark_iii_solenoid_sector_rail_half_B_1to1.stl"].apply_scale(1000)

    # Solenoid shell is split longitudinally; print two halves per cartridge.
    sol_half=annular_sector_x(
        -d["solenoid_axial_length_m"]/2,d["solenoid_axial_length_m"]/2,
        d["solenoid_inner_radius_m"],d["solenoid_outer_radius_m"],0,math.pi)
    sol_half.apply_scale(1000)
    refs["mark_iii_solenoid_cartridge_half_shell_1to1.stl"]=sol_half
    mount=box([0.050,0.018,0.016],[0,0,0],0);mount.apply_scale(1000)
    refs["mark_iii_solenoid_mount_bracket_1to1.stl"]=mount

    refs["mark_iii_coupler_quadrant_1to1.stl"] = annular_sector_x(
        -d["coupler_length_m"]/2,d["coupler_length_m"]/2,0.11,0.16,0,math.pi/2)
    refs["mark_iii_coupler_quadrant_1to1.stl"].apply_scale(1000)

    cap_tray=box([0.18,0.09,0.012],[0,0,0],0);cap_tray.apply_scale(1000)
    refs["mark_iii_capacitor_pair_tray_1to1.stl"]=cap_tray
    refs["mark_iii_controller_bay_reference_1to1.stl"]=concatenate(
        ["M3_CONTROLLER_DSP","M3_CPU_ISOLATION_POWER_CONDITIONER"])

    # Straight printable half-shell is the production reference for each curved arm link.
    link_half=annular_sector_x(
        -d["arm"]["link_segment_length_m"]/2,d["arm"]["link_segment_length_m"]/2,
        d["arm"]["link_radius_m"]-0.005,d["arm"]["link_radius_m"],0,math.pi)
    link_half.apply_scale(1000)
    refs["mark_iii_arm_link_half_shell_1to1.stl"]=link_half
    joint_ring=annulus_x(0.014,d["arm"]["joint_radius_m"],0.025,[0,0,0],32)
    joint_ring.apply_scale(1000)
    refs["mark_iii_arm_joint_ring_1to1.stl"]=joint_ring
    probe=cylinder_x(d["central_probe"]["link_radius_m"],
                     d["central_probe"]["segment_length_m"],[0,0,0],8)
    probe.apply_scale(1000)
    refs["mark_iii_probe_segment_1to1.stl"]=probe
    collector=cylinder_x(d["arm"]["collector_pad_radius_m"],
                         d["arm"]["collector_pad_thickness_m"],[0,0,0],8)
    collector_coupler=annulus_x(0.018,0.028,
                                d["arm"]["collector_pad_thickness_m"]-0.002,[0,0,0],24)
    collector=trimesh.util.concatenate([collector,collector_coupler]);collector.apply_scale(1000)
    refs["mark_iii_collector_pad_1to1.stl"]=collector

    coupon=d["plating_witness_coupon_m"]
    coupon_meshes=[
        box(coupon,[0,0,0],0),
        annulus_between([-coupon[0]/2+0.012,0,0],[coupon[0]/2-0.012,0,0],
                        0.0025,0.0055,18),
        box([0.018,0.012,0.002],[0.020,0,0.003],0),
        box([0.018,0.012,0.002],[-0.020,0,0.003],0),
    ]
    coupon_tree=trimesh.util.concatenate(coupon_meshes);coupon_tree.apply_scale(1000)
    refs["mark_iii_plating_witness_coupon_tree_1to1.stl"]=coupon_tree

    # Flat shop fixture; all posts extend in Z and remain below 40 mm.
    jig_meshes=[box([0.250,0.200,0.012],[0,0,0],0)]
    for a in [0,math.pi/3,2*math.pi/3,math.pi,4*math.pi/3,5*math.pi/3]:
        x=0.080*math.cos(a);y=0.080*math.sin(a)
        jig_meshes.append(cylinder_between([x,y,0.006],[x,y,0.025],0.004,16))
    jig=trimesh.util.concatenate(jig_meshes);jig.apply_scale(1000)
    refs["mark_iii_alignment_and_plating_jig_1to1.stl"]=jig

    # Generic interface mount only; not a nozzle or thrust device.
    prop_mount = trimesh.util.concatenate([
        annulus_x(0.008, 0.020, 0.012, [0,0,0], 24),
        box([0.050,0.038,0.006], [-0.009,0,0], 0),
    ])
    prop_mount.apply_scale(1000)
    refs["mark_iii_propulsion_interface_mount_1to1.stl"] = prop_mount

    # Reservoir cradle reference only. The pressure/working-fluid vessel itself
    # is explicitly not a printed part in this package.
    cradle = trimesh.util.concatenate([
        box([0.115,0.012,0.010], [0,-0.032,0], 0),
        box([0.115,0.012,0.010], [0,0.032,0], 0),
        box([0.012,0.076,0.025], [-0.050,0,0.008], 0),
        box([0.012,0.076,0.025], [0.050,0,0.008], 0),
    ])
    cradle.apply_scale(1000)
    refs["mark_iii_reservoir_cradle_reference_1to1.stl"] = cradle

    arm_names=[r["node_name"] for r in records
               if r["node_name"].startswith("M3_ARM_01") and r["physical"]
               and r["family"] not in {"harness"}]
    refs["mark_iii_arm_assembly_display_1to5.stl"]=concatenate(arm_names,1000/5)
    for mesh in refs.values():
        if mesh.volume<0:mesh.invert()
    return refs

def print_kit_manifest(parameters:dict[str,Any],
                       refs:dict[str,trimesh.Trimesh])->dict[str,Any]:
    bed=parameters["derived_configuration"]["print_bed_mm"]
    orientations={
      "mark_iii_full_module_display_1to8.stl":"Display model; orient for minimum support.",
      "mark_iii_standard_shell_panel_1to1.stl":"Place inner datum face down; protect mask lands and drain sleeve.",
      "mark_iii_standard_service_panel_1to1.stl":"Place inner datum face down; verify insert bosses and seam edges.",
      "mark_iii_resonator_tray_25_socket_1to1.stl":"Tray plane on bed; inspect every keyed collar.",
      "mark_iii_solenoid_sector_rail_half_A_1to1.stl":"Flat rail face on bed; inspect keyed split and datum continuity.",
      "mark_iii_solenoid_sector_rail_half_B_1to1.stl":"Flat rail face on bed; inspect keyed split and datum continuity.",
      "mark_iii_solenoid_cartridge_half_shell_1to1.stl":"Print two mirrored halves per cartridge; winding and insulation remain separate qualified components.",
      "mark_iii_solenoid_mount_bracket_1to1.stl":"Mount face down; validate insert pull-out and thermal path with coupons.",
      "mark_iii_coupler_quadrant_1to1.stl":"Flat split face down; inspect alignment and plated seam allowance.",
      "mark_iii_capacitor_pair_tray_1to1.stl":"Tray face down; cells remain non-energised packaging references.",
      "mark_iii_controller_bay_reference_1to1.stl":"Reference packaging only; no electronics installation release.",
      "mark_iii_arm_link_half_shell_1to1.stl":"Link axis parallel to bed when possible; validate anisotropy with coupons.",
      "mark_iii_arm_joint_ring_1to1.stl":"Split/fixture strategy to be selected after bearing and seal design.",
      "mark_iii_probe_segment_1to1.stl":"Link axis parallel to bed; inspect straightness.",
      "mark_iii_collector_pad_1to1.stl":"Pad face down; mask end-coupler and sensor interfaces.",
      "mark_iii_plating_witness_coupon_tree_1to1.stl":"Print with every production build and process through identical sanding/sealing/plating steps.",
      "mark_iii_alignment_and_plating_jig_1to1.stl":"Non-flight shop fixture; do not plate datum pins unless specified.",
      "mark_iii_propulsion_interface_mount_1to1.stl":"Generic mount/interface only; no nozzle, pressure line or propulsion hardware is defined.",
      "mark_iii_reservoir_cradle_reference_1to1.stl":"Cradle only; do not interpret as a printable pressure or propellant vessel.",
      "mark_iii_arm_assembly_display_1to5.stl":"Display/kinematic review only."
    }
    rows=[]
    for name,mesh in sorted(refs.items()):
        dims=sorted(float(v) for v in mesh.extents)
        bed_sorted=sorted(float(v) for v in bed)
        fits=all(a<=b+1e-6 for a,b in zip(dims,bed_sorted))
        rows.append({
          "file":name,
          "extents_mm":[round(float(v),6) for v in mesh.extents],
          "fits_reference_bed_by_orientation":fits,
          "watertight":bool(mesh.is_watertight),
          "winding_consistent":bool(mesh.is_winding_consistent),
          "quantity_reference":1,
          "orientation_and_process_note":orientations.get(name,"Engineering review required."),
          "release_state":"MANUFACTURING_REFERENCE_ONLY"
        })
    return {
      "schema_version":"mark-iii-print-kit-manifest-v0.3.3",
      "print_bed_mm":bed,
      "plating_allowance_per_surface_mm":parameters["derived_configuration"]["plating_allowance_per_surface_m"]*1000,
      "mandatory_witnesses":parameters["manufacturing_reference"]["mandatory_witnesses"],
      "mandatory_inspections":parameters["manufacturing_reference"]["mandatory_inspections"],
      "parts":rows,
      "claim_gate":"No production, pressure, electrical, structural, flight or deployment release."
    }


def build_verification(parameters: dict[str, Any], scene: trimesh.Scene,
                       records: list[dict[str, Any]],
                       print_refs: dict[str,trimesh.Trimesh]) -> dict[str,Any]:
    families={}
    for record in records:families[record["family"]]=families.get(record["family"],0)+1
    checks={name:{"watertight":bool(mesh.is_watertight),
                  "winding_consistent":bool(mesh.is_winding_consistent),
                  "vertices":int(len(mesh.vertices)),"faces":int(len(mesh.faces))}
            for name,mesh in scene.geometry.items()}
    bed=parameters["derived_configuration"]["print_bed_mm"]
    bed_sorted=sorted(bed)
    return {
      "schema_version":"mark-iii-verification-v0.3.3",
      "status":"PASS_ORIGINAL_LAYOUT_PRINT_REFERENCE_GEOMETRY"
               if all(v["watertight"] and v["winding_consistent"] for v in checks.values())
               else "FAIL_GEOMETRY",
      "scene":{"geometry_nodes":len(scene.geometry),
               "physical_nodes":sum(1 for r in records if r["physical"]),
               "illustrative_nodes":sum(1 for r in records if not r["physical"])},
      "family_counts":families,
      "geometry_checks":checks,
      "semantic_geometry_sha256":semantic_geometry_fingerprint(scene),
      "semantic_quantization_m":QUANTIZATION_METRES,
      "print_references":{
        name:{
          "watertight":bool(mesh.is_watertight),
          "winding_consistent":bool(mesh.is_winding_consistent),
          "extents_mm":np.round(mesh.extents,6).tolist(),
          "fits_280x280x40_by_orientation":all(
              a<=b+1e-6 for a,b in zip(sorted(float(v) for v in mesh.extents),bed_sorted))
        } for name,mesh in print_refs.items()},
      "resonator_configuration":parameters["resonator_configuration"],
      "manufacturing_reference_state":"PROCESS_QUALIFICATION_REQUIRED",
      "claim_gate_state":"STRENGTHENED"
    }


def export_reference(parameters_path: Path, out_dir: Path) -> dict[str,Any]:
    out_dir.mkdir(parents=True,exist_ok=True)
    parameters=load_parameters(parameters_path)
    scene,records=build_reference(parameters)
    print_refs=build_print_references(parameters,scene,records)
    glb_path=out_dir/"mark_iii_assembly.glb"
    glb_path.write_bytes(scene.export(file_type="glb"))
    for name,mesh in print_refs.items():
        (out_dir/name).write_bytes(mesh.export(file_type="stl"))
    manifest={"schema_version":"mark-iii-component-manifest-v0.3.3",
              "node_count":len(records),"components":records}
    manifest["canonical_manifest_sha256"]=canonical_manifest_sha256(manifest)
    (out_dir/"mark_iii_component_manifest.json").write_text(
        json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    kit=print_kit_manifest(parameters,print_refs)
    (out_dir/"mark_iii_print_kit_manifest.json").write_text(
        json.dumps(kit,indent=2)+"\n",encoding="utf-8")
    import csv
    with (out_dir/"mark_iii_print_kit_manifest.csv").open("w",newline="",encoding="utf-8") as stream:
        rows=kit["parts"];w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader()
        for row in rows:
            r=dict(row);r["extents_mm"]=json.dumps(r["extents_mm"]);w.writerow(r)
    verification=build_verification(parameters,scene,records,print_refs)
    verification["canonical_manifest_sha256"]=manifest["canonical_manifest_sha256"]
    verification["observed_artifacts"]={"assembly_glb_sha256":sha256_file(glb_path)}
    (out_dir/"mark_iii_verification.json").write_text(
        json.dumps(verification,indent=2)+"\n",encoding="utf-8")
    return {
      "status":verification["status"],
      "geometry_nodes":len(records),
      "physical_nodes":verification["scene"]["physical_nodes"],
      "resonator_nodes":verification["family_counts"].get("resonator",0),
      "solenoid_nodes":verification["family_counts"].get("solenoid",0),
      "semantic_geometry_sha256":verification["semantic_geometry_sha256"],
      "print_references":len(print_refs)
    }

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--parameters",type=Path,required=True);ap.add_argument("--out-dir",type=Path,required=True)
    args=ap.parse_args();summary=export_reference(args.parameters,args.out_dir);print(json.dumps(summary,indent=2));return 0 if summary["status"].startswith("PASS") else 1

if __name__=="__main__": raise SystemExit(main())
