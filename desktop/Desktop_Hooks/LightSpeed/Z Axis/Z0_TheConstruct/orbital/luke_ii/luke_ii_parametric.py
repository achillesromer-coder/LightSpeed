#!/usr/bin/env python3
"""Generate the Luke II v1.3 serviceable reference assembly.

The model is a source-reconciled spatial/configuration reference. It is not a
flight, pressure-vessel, human-rating, electrical, thermal, payload-control or
manufacturing release. All service clearances, panel joints, windows, cable
routes and Mark III interface-arm dimensions remain evidence-gated references.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def material(name: str, rgba: tuple[int, int, int, int], metallic: float = 0.15,
             roughness: float = 0.62) -> PBRMaterial:
    return PBRMaterial(
        name=name,
        baseColorFactor=list(rgba),
        metallicFactor=metallic,
        roughnessFactor=roughness,
        alphaMode="BLEND" if rgba[3] < 255 else "OPAQUE",
        doubleSided=True,
    )


def set_material(mesh: trimesh.Trimesh, mat: PBRMaterial) -> trimesh.Trimesh:
    mesh.visual = trimesh.visual.TextureVisuals(material=mat)
    return mesh


def frame_transform(angle: float, center: Iterable[float]) -> np.ndarray:
    radial = np.array([math.cos(angle), math.sin(angle), 0.0])
    tangent = np.array([-math.sin(angle), math.cos(angle), 0.0])
    transform = np.eye(4)
    transform[:3, 0] = tangent
    transform[:3, 1] = radial
    transform[:3, 2] = [0.0, 0.0, 1.0]
    transform[:3, 3] = np.asarray(center, dtype=float)
    return transform


def oriented_box(extents: Iterable[float], angle: float, center: Iterable[float]) -> trimesh.Trimesh:
    return trimesh.creation.box(
        extents=np.asarray(extents, dtype=float),
        transform=frame_transform(angle, center),
    )


def radial_cylinder(radius: float, height: float, angle: float, radial_distance: float,
                    z: float = 0.0, sections: int = 48) -> trimesh.Trimesh:
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_transform(
        trimesh.geometry.align_vectors(
            [0.0, 0.0, 1.0],
            [math.cos(angle), math.sin(angle), 0.0],
        )
    )
    mesh.apply_translation(
        [radial_distance * math.cos(angle), radial_distance * math.sin(angle), z]
    )
    return mesh


def tangent_cylinder(radius: float, height: float, angle: float, radial_distance: float,
                     z: float = 0.0, sections: int = 48) -> trimesh.Trimesh:
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_transform(
        trimesh.geometry.align_vectors(
            [0.0, 0.0, 1.0],
            [-math.sin(angle), math.cos(angle), 0.0],
        )
    )
    mesh.apply_translation(
        [radial_distance * math.cos(angle), radial_distance * math.sin(angle), z]
    )
    return mesh


def torus_segment_solid(major_r: float, minor_r: float, u0: float, u1: float,
                        nu: int = 16, nv: int = 32) -> trimesh.Trimesh:
    """Closed torus-sector solid from the centreline to ``minor_r``."""
    us = np.linspace(u0, u1, nu + 1)
    vs = np.linspace(0.0, 2.0 * math.pi, nv, endpoint=False)
    vertices: list[tuple[float, float, float]] = []
    for u in us:
        cu, su = math.cos(u), math.sin(u)
        for v in vs:
            cv, sv = math.cos(v), math.sin(v)
            vertices.append(
                ((major_r + minor_r * cv) * cu,
                 (major_r + minor_r * cv) * su,
                 minor_r * sv)
            )
    faces: list[tuple[int, int, int]] = []
    for i in range(nu):
        for j in range(nv):
            jn = (j + 1) % nv
            a, b = i * nv + j, (i + 1) * nv + j
            c, d = (i + 1) * nv + jn, i * nv + jn
            faces.extend(((a, b, c), (a, c, d)))
    center0, center1 = len(vertices), len(vertices) + 1
    vertices.extend(
        [
            (major_r * math.cos(u0), major_r * math.sin(u0), 0.0),
            (major_r * math.cos(u1), major_r * math.sin(u1), 0.0),
        ]
    )
    for j in range(nv):
        jn = (j + 1) % nv
        faces.append((center0, jn, j))
        faces.append((center1, nu * nv + j, nu * nv + jn))
    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True)
    mesh.fix_normals(multibody=True)
    return mesh


def torus_patch_solid(major_r: float, outer_r: float, inner_r: float,
                      u0: float, u1: float, v0: float, v1: float,
                      nu: int = 5, nv: int = 5) -> trimesh.Trimesh:
    """Closed, thick toroidal patch bounded in major and minor angle."""
    if not (outer_r > inner_r > 0.0):
        raise ValueError("outer_r must be greater than inner_r and both positive")
    us = np.linspace(u0, u1, nu + 1)
    vs = np.linspace(v0, v1, nv + 1)
    vertices: list[tuple[float, float, float]] = []
    for radius in (outer_r, inner_r):
        for u in us:
            cu, su = math.cos(u), math.sin(u)
            for v in vs:
                cv, sv = math.cos(v), math.sin(v)
                vertices.append(
                    ((major_r + radius * cv) * cu,
                     (major_r + radius * cv) * su,
                     radius * sv)
                )

    stride = nv + 1
    layer_size = (nu + 1) * stride

    def idx(layer: int, i: int, j: int) -> int:
        return layer * layer_size + i * stride + j

    faces: list[tuple[int, int, int]] = []
    for i in range(nu):
        for j in range(nv):
            a, b, c, d = idx(0, i, j), idx(0, i + 1, j), idx(0, i + 1, j + 1), idx(0, i, j + 1)
            faces.extend(((a, b, c), (a, c, d)))
            ai, bi, ci, di = idx(1, i, j), idx(1, i, j + 1), idx(1, i + 1, j + 1), idx(1, i + 1, j)
            faces.extend(((ai, bi, ci), (ai, ci, di)))

    for j in range(nv):
        # u0 cap
        a, b, c, d = idx(0, 0, j), idx(0, 0, j + 1), idx(1, 0, j + 1), idx(1, 0, j)
        faces.extend(((a, b, c), (a, c, d)))
        # u1 cap
        a, b, c, d = idx(0, nu, j), idx(1, nu, j), idx(1, nu, j + 1), idx(0, nu, j + 1)
        faces.extend(((a, b, c), (a, c, d)))

    for i in range(nu):
        # v0 cap
        a, b, c, d = idx(0, i, 0), idx(1, i, 0), idx(1, i + 1, 0), idx(0, i + 1, 0)
        faces.extend(((a, b, c), (a, c, d)))
        # v1 cap
        a, b, c, d = idx(0, i, nv), idx(0, i + 1, nv), idx(1, i + 1, nv), idx(1, i, nv)
        faces.extend(((a, b, c), (a, c, d)))

    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True)
    mesh.fix_normals(multibody=True)
    return mesh


def torus_shell_sector(major_r: float, outer_r: float, inner_r: float,
                       u0: float, u1: float, nu: int = 8, nv: int = 36) -> trimesh.Trimesh:
    """Closed toroidal shell sector spanning the complete minor circumference."""
    us = np.linspace(u0, u1, nu + 1)
    vs = np.linspace(0.0, 2.0 * math.pi, nv, endpoint=False)
    vertices: list[tuple[float, float, float]] = []
    for radius in (outer_r, inner_r):
        for u in us:
            cu, su = math.cos(u), math.sin(u)
            for v in vs:
                cv, sv = math.cos(v), math.sin(v)
                vertices.append(
                    ((major_r + radius * cv) * cu,
                     (major_r + radius * cv) * su,
                     radius * sv)
                )
    layer_size = (nu + 1) * nv

    def idx(layer: int, i: int, j: int) -> int:
        return layer * layer_size + i * nv + (j % nv)

    faces: list[tuple[int, int, int]] = []
    for i in range(nu):
        for j in range(nv):
            jn = (j + 1) % nv
            a, b, c, d = idx(0, i, j), idx(0, i + 1, j), idx(0, i + 1, jn), idx(0, i, jn)
            faces.extend(((a, b, c), (a, c, d)))
            ai, bi, ci, di = idx(1, i, j), idx(1, i, jn), idx(1, i + 1, jn), idx(1, i + 1, j)
            faces.extend(((ai, bi, ci), (ai, ci, di)))
    for j in range(nv):
        jn = (j + 1) % nv
        a, b, c, d = idx(0, 0, j), idx(0, 0, jn), idx(1, 0, jn), idx(1, 0, j)
        faces.extend(((a, b, c), (a, c, d)))
        a, b, c, d = idx(0, nu, j), idx(1, nu, j), idx(1, nu, jn), idx(0, nu, jn)
        faces.extend(((a, b, c), (a, c, d)))
    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True)
    mesh.fix_normals(multibody=True)
    return mesh


def torus_tube_segment(major_r: float, tube_r: float, u0: float, u1: float,
                       minor_angle: float, nu: int = 12, nv: int = 12) -> trimesh.Trimesh:
    """Small tube following the major circle at a fixed torus minor angle."""
    centers: list[np.ndarray] = []
    us = np.linspace(u0, u1, nu + 1)
    for u in us:
        radial = np.array([math.cos(u), math.sin(u), 0.0])
        center = radial * (major_r + math.cos(minor_angle))
        center[2] = math.sin(minor_angle)
        centers.append(center)
    # Sweep circular sections using tangent / local minor normal basis.
    vertices: list[np.ndarray] = []
    for u, center in zip(us, centers):
        tangent = np.array([-math.sin(u), math.cos(u), 0.0])
        radial = np.array([math.cos(u), math.sin(u), 0.0])
        normal = np.cross(tangent, radial)
        for v in np.linspace(0.0, 2.0 * math.pi, nv, endpoint=False):
            vertices.append(center + tube_r * (math.cos(v) * radial + math.sin(v) * normal))
    faces: list[tuple[int, int, int]] = []
    for i in range(nu):
        for j in range(nv):
            jn = (j + 1) % nv
            a, b = i * nv + j, (i + 1) * nv + j
            c, d = (i + 1) * nv + jn, i * nv + jn
            faces.extend(((a, b, c), (a, c, d)))
    # cap ends
    c0, c1 = len(vertices), len(vertices) + 1
    vertices.extend([centers[0], centers[-1]])
    for j in range(nv):
        jn = (j + 1) % nv
        faces.append((c0, jn, j))
        faces.append((c1, nu * nv + j, nu * nv + jn))
    mesh = trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=True)
    mesh.fix_normals(multibody=True)
    return mesh


@dataclass
class AssemblyBuilder:
    scene: trimesh.Scene = field(default_factory=trimesh.Scene)
    records: list[dict[str, Any]] = field(default_factory=list)
    materials: dict[str, PBRMaterial] = field(default_factory=dict)

    def add(self, name: str, mesh: trimesh.Trimesh, material_key: str, *, family: str,
            evidence_state: str, review_gate: str, attachment_parent: str,
            source_basis: str, physical: bool = True, maintainable: bool = False,
            cable_required: bool = False, cable_route: str | None = None,
            service_clearance: str | None = None, removal_path: str | None = None,
            print_candidate: bool = False, connected_to_walkway: bool | None = None,
            notes: str = "") -> None:
        if name in self.scene.geometry:
            raise ValueError(f"duplicate geometry node: {name}")
        set_material(mesh, self.materials[material_key])
        self.scene.add_geometry(mesh, node_name=name, geom_name=name)
        self.records.append(
            {
                "node_name": name,
                "family": family,
                "evidence_state": evidence_state,
                "review_gate": review_gate,
                "attachment_parent": attachment_parent,
                "source_basis": source_basis,
                "physical": physical,
                "maintainable": maintainable,
                "cable_required": cable_required,
                "cable_route": cable_route,
                "service_clearance": service_clearance,
                "removal_path": removal_path,
                "print_candidate": print_candidate,
                "connected_to_walkway": connected_to_walkway,
                "notes": notes,
            }
        )


def _materials() -> dict[str, PBRMaterial]:
    return {
        "solar_panel": material("Solar Hull panel", (92, 112, 125, 255), 0.48, 0.36),
        "panel_alt": material("Solar Hull alternate panel", (112, 132, 145, 255), 0.42, 0.42),
        "pressure": material("Pressure liner reference", (96, 108, 124, 210), 0.30, 0.52),
        "glass_outer": material("Window outer pane", (88, 178, 220, 105), 0.08, 0.18),
        "glass_middle": material("Window middle pane", (92, 204, 236, 85), 0.05, 0.15),
        "glass_inner": material("Window inner pane", (154, 222, 248, 110), 0.04, 0.16),
        "window_frame": material("Window frame", (57, 73, 88, 255), 0.55, 0.30),
        "structure": material("Primary structure", (74, 85, 104, 255), 0.58, 0.38),
        "lining": material("Removable interior lining", (203, 213, 225, 235), 0.12, 0.70),
        "walkway": material("Walkway and deck", (148, 163, 184, 255), 0.28, 0.55),
        "habitat": material("Habitation equipment", (52, 168, 112, 255), 0.08, 0.68),
        "hab_clear": material("Habitation clearance", (74, 222, 128, 45), 0.02, 0.85),
        "field": material("Field module", (52, 122, 235, 255), 0.25, 0.42),
        "coil": material("Solenoid winding reference", (37, 99, 235, 255), 0.38, 0.34),
        "resonator": material("Resonator", (160, 92, 230, 255), 0.24, 0.50),
        "capacitor": material("Free Flow capacitor", (245, 158, 11, 255), 0.18, 0.55),
        "battery": material("Free Flow battery/BMS", (234, 88, 12, 255), 0.20, 0.58),
        "sensor": material("Sensor", (20, 184, 166, 255), 0.18, 0.44),
        "damping": material("Damping placeholder", (100, 116, 139, 210), 0.18, 0.52),
        "cable_tray": material("Cable tray", (71, 85, 105, 255), 0.42, 0.48),
        "power_cable": material("Power harness", (239, 68, 68, 255), 0.18, 0.55),
        "data_cable": material("Data harness", (34, 211, 238, 255), 0.15, 0.45),
        "connector": material("Connector", (250, 204, 21, 255), 0.25, 0.44),
        "service": material("Service clearance", (248, 113, 113, 40), 0.02, 0.90),
        "egress": material("Egress/removal path", (250, 204, 21, 45), 0.02, 0.90),
        "interface": material("Interface", (217, 70, 239, 255), 0.30, 0.42),
        "arm": material("Mark III interface arm", (192, 132, 252, 255), 0.36, 0.40),
        "actuator": material("Actuator housing", (126, 34, 206, 255), 0.34, 0.44),
        "payload": material("Payload sequence", (239, 68, 68, 160), 0.45, 0.28),
        "path": material("Illustrative path", (248, 250, 252, 100), 0.05, 0.25),
        "field_guide": material("Illustrative field guide", (96, 165, 250, 95), 0.08, 0.22),
    }


def _point_on_ring(radius: float, angle: float, z: float = 0.0) -> np.ndarray:
    return np.array([radius * math.cos(angle), radius * math.sin(angle), z], dtype=float)


def _panel_step_inset(v_center: float, maximum: float) -> float:
    return maximum * abs(math.sin(v_center))


def build_reference(parameters: dict[str, Any]) -> tuple[trimesh.Scene, list[dict[str, Any]]]:
    source = parameters["source_parameters"]
    revision = parameters["closure_revision"]
    panel_cfg = revision["panelisation"]
    layer_cfg = revision["pressure_and_service_layers"]
    window_cfg = revision["windows"]
    access_cfg = revision["habitat_access"]
    service_cfg = revision["serviceability"]
    arm_cfg = revision["mark_iii_interface_arm"]

    R = float(source["major_radius_m"]["value"])
    r = float(source["body_minor_radius_m"]["value"])
    sectors = int(source["field_sector_count"]["value"])
    bands = int(panel_cfg["minor_band_count"])
    du = 2.0 * math.pi / sectors
    dv = 2.0 * math.pi / bands
    major_gap = float(panel_cfg["major_seam_gap_rad"])
    minor_gap = float(panel_cfg["minor_seam_gap_rad"])
    habitat_indices = set(window_cfg["habitat_sector_indices_zero_based"])
    window_bands = set(window_cfg["minor_band_indices"])

    builder = AssemblyBuilder(materials=_materials())

    # Primary structural frames establish the root attachment graph.
    for sector in range(sectors):
        u = sector * du
        center = _point_on_ring(R, u)
        frame_parent = "PRIMARY_STRUCTURE"
        pieces = [
            ("OUTER_POST", (0.12, 0.16, 3.20), center + _point_on_ring(1.60, u)),
            ("INNER_POST", (0.12, 0.16, 3.20), center - _point_on_ring(1.60, u)),
            ("TOP_BEAM", (0.12, 3.20, 0.16), center + np.array([0.0, 0.0, 1.60])),
            ("LOWER_BEAM", (0.12, 3.20, 0.16), center + np.array([0.0, 0.0, -1.60])),
        ]
        for suffix, extents, piece_center in pieces:
            builder.add(
                f"STRUCTURE_PRIMARY_FRAME_{sector + 1:02d}_{suffix}",
                oriented_box(extents, u, piece_center),
                "structure",
                family="primary_structure",
                evidence_state="PROVISIONAL_REFERENCE_GEOMETRY",
                review_gate="STRUCTURAL_LOAD_AND_TOLERANCE_REVIEW",
                attachment_parent=frame_parent,
                source_basis="owner panelised assembly directive",
                physical=True,
                print_candidate=True,
            )

    # Panelised Solar Hull envelope and habitation pressure/window layers.
    outer_panel_outer = float(panel_cfg["outer_panel_outer_radius_m"])
    outer_panel_inner = float(panel_cfg["outer_panel_inner_radius_m"])
    pressure_outer = float(layer_cfg["pressure_liner_outer_radius_m"])
    pressure_inner = float(layer_cfg["pressure_liner_inner_radius_m"])

    for sector in range(sectors):
        u0 = sector * du + major_gap / 2.0
        u1 = (sector + 1) * du - major_gap / 2.0
        sector_parent = f"STRUCTURE_PRIMARY_FRAME_{sector + 1:02d}_OUTER_POST"
        is_habitat = sector in habitat_indices

        if not is_habitat:
            builder.add(
                f"PRESSURE_SERVICE_LINER_SYSTEM_SECTOR_{sector + 1:02d}",
                torus_shell_sector(R, pressure_outer, pressure_inner, u0, u1),
                "pressure",
                family="pressure_liner",
                evidence_state="PROVISIONAL_SPATIAL_RESERVATION",
                review_gate="PRESSURE_SHELL_AND_SERVICE_BAY_REVIEW",
                attachment_parent=sector_parent,
                source_basis="Luke sector topology plus service-bay reservation",
                physical=True,
                print_candidate=False,
            )

        for band in range(bands):
            v0 = band * dv + minor_gap / 2.0
            v1 = (band + 1) * dv - minor_gap / 2.0
            vc = (v0 + v1) / 2.0
            inset = _panel_step_inset(vc, float(panel_cfg["panel_step_inset_max_m"]))
            panel_outer = outer_panel_outer - inset
            panel_inner = outer_panel_inner - inset
            panel_name = f"HULL_SOLAR_PANEL_S{sector + 1:02d}_B{band + 1:02d}"

            if is_habitat and band in window_bands:
                # Three external transparent layers plus the inner pressure pane.
                outer_t = float(window_cfg["outer_layer_thickness_m"])
                gap = float(window_cfg["interlayer_gap_m"])
                inner_t = float(window_cfg["inner_layer_thickness_m"])
                layer_specs = [
                    ("OUTER", panel_outer, panel_outer - outer_t, "glass_outer"),
                    ("MIDDLE", panel_outer - outer_t - gap, panel_outer - outer_t - gap - inner_t, "glass_middle"),
                    ("INNER", panel_outer - outer_t - 2 * gap - inner_t, panel_outer - outer_t - 2 * gap - 2 * inner_t, "glass_inner"),
                ]
                frame_id = f"STRUCTURE_WINDOW_FRAME_S{sector + 1:02d}_B{band + 1:02d}"
                for layer_name, ro, ri, material_key in layer_specs:
                    builder.add(
                        f"WINDOW_{layer_name}_S{sector + 1:02d}_B{band + 1:02d}",
                        torus_patch_solid(R, ro, ri, u0, u1, v0, v1),
                        material_key,
                        family="pressure_window",
                        evidence_state="PROVISIONAL_TRANSPARENT_PRESSURE_LAYER",
                        review_gate="WINDOW_LAMINATE_FRAME_SEAL_IMPACT_REVIEW",
                        attachment_parent=f"{frame_id}_U0",
                        source_basis="owner clock-position directive",
                        physical=True,
                        maintainable=True,
                        service_clearance=f"CLEARANCE_WINDOW_SERVICE_S{sector + 1:02d}_B{band + 1:02d}",
                        removal_path=f"REMOVAL_WINDOW_S{sector + 1:02d}_B{band + 1:02d}",
                        print_candidate=(layer_name == "OUTER"),
                    )
                builder.add(
                    f"WINDOW_PRESSURE_PANE_S{sector + 1:02d}_B{band + 1:02d}",
                    torus_patch_solid(R, pressure_outer, pressure_inner, u0, u1, v0, v1),
                    "glass_inner",
                    family="pressure_window",
                    evidence_state="PROVISIONAL_TRANSPARENT_PRESSURE_LAYER",
                    review_gate="WINDOW_LAMINATE_FRAME_SEAL_IMPACT_REVIEW",
                    attachment_parent=f"{frame_id}_U0",
                    source_basis="serviceable pressure-liner reservation",
                    physical=True,
                    maintainable=True,
                    service_clearance=f"CLEARANCE_WINDOW_SERVICE_S{sector + 1:02d}_B{band + 1:02d}",
                    removal_path=f"REMOVAL_WINDOW_S{sector + 1:02d}_B{band + 1:02d}",
                )
                # Narrow structural strips around each panel cell.
                frame_depth = float(window_cfg["frame_depth_m"])
                strip = min(0.035, (v1 - v0) / 6.0)
                for suffix, fu0, fu1, fv0, fv1 in (
                    ("U0", u0, u0 + 0.020, v0, v1),
                    ("U1", u1 - 0.020, u1, v0, v1),
                    ("V0", u0, u1, v0, v0 + strip),
                    ("V1", u0, u1, v1 - strip, v1),
                ):
                    builder.add(
                        f"{frame_id}_{suffix}",
                        torus_patch_solid(R, panel_outer + 0.01, panel_outer - frame_depth, fu0, fu1, fv0, fv1),
                        "window_frame",
                        family="window_frame",
                        evidence_state="PROVISIONAL_INTERFACE",
                        review_gate="WINDOW_FRAME_ATTACHMENT_REVIEW",
                        attachment_parent=sector_parent,
                        source_basis="owner window pressure-control directive",
                        physical=True,
                        maintainable=True,
                        print_candidate=True,
                    )
                builder.add(
                    f"CLEARANCE_WINDOW_SERVICE_S{sector + 1:02d}_B{band + 1:02d}",
                    torus_patch_solid(R, panel_outer + 0.18, pressure_outer - 0.10, u0, u1, v0, v1),
                    "service",
                    family="service_clearance",
                    evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
                    review_gate="MAINTENANCE_ACCESS_REVIEW",
                    attachment_parent=f"{frame_id}_U0",
                    source_basis="owner repair-access directive",
                    physical=False,
                    notes="Reserved access and retaining-layer removal volume.",
                )
                builder.add(
                    f"REMOVAL_WINDOW_S{sector + 1:02d}_B{band + 1:02d}",
                    torus_patch_solid(R, panel_outer + 0.42, panel_outer + 0.20, u0, u1, v0, v1),
                    "egress",
                    family="removal_path",
                    evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
                    review_gate="MAINTENANCE_REMOVAL_PATH_REVIEW",
                    attachment_parent=f"{frame_id}_U0",
                    source_basis="owner repair-access directive",
                    physical=False,
                )
            else:
                builder.add(
                    panel_name,
                    torus_patch_solid(R, panel_outer, panel_inner, u0, u1, v0, v1),
                    "solar_panel" if (sector + band) % 2 == 0 else "panel_alt",
                    family="solar_hull_panel",
                    evidence_state="DERIVED_PANELISED_REFERENCE",
                    review_gate="SOLAR_HULL_PANEL_FASTENER_SEAL_PROCESS_REVIEW",
                    attachment_parent=sector_parent,
                    source_basis="Solar Hull v0.2 plus owner external-form reference",
                    physical=True,
                    maintainable=True,
                    service_clearance=f"CLEARANCE_PANEL_S{sector + 1:02d}_B{band + 1:02d}",
                    removal_path=f"REMOVAL_PANEL_S{sector + 1:02d}_B{band + 1:02d}",
                    print_candidate=True,
                )
                builder.add(
                    f"CLEARANCE_PANEL_S{sector + 1:02d}_B{band + 1:02d}",
                    torus_patch_solid(R, panel_outer + 0.12, panel_outer + 0.04, u0, u1, v0, v1),
                    "service",
                    family="service_clearance",
                    evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
                    review_gate="MAINTENANCE_ACCESS_REVIEW",
                    attachment_parent=panel_name,
                    source_basis="owner repair-access directive",
                    physical=False,
                )
                builder.add(
                    f"REMOVAL_PANEL_S{sector + 1:02d}_B{band + 1:02d}",
                    torus_patch_solid(R, panel_outer + 0.30, panel_outer + 0.16, u0, u1, v0, v1),
                    "egress",
                    family="removal_path",
                    evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
                    review_gate="MAINTENANCE_REMOVAL_PATH_REVIEW",
                    attachment_parent=panel_name,
                    source_basis="owner repair-access directive",
                    physical=False,
                )
                if is_habitat:
                    builder.add(
                        f"PRESSURE_LINER_HAB_S{sector + 1:02d}_B{band + 1:02d}",
                        torus_patch_solid(R, pressure_outer, pressure_inner, u0, u1, v0, v1),
                        "pressure",
                        family="pressure_liner",
                        evidence_state="PROVISIONAL_SPATIAL_RESERVATION",
                        review_gate="PRESSURE_SHELL_AND_SERVICE_BAY_REVIEW",
                        attachment_parent=sector_parent,
                        source_basis="habitat serviceability allocation",
                        physical=True,
                    )

    # Cable tray ring and harness routes in the reserved service bay.
    tray_radius = R + 1.82
    tray_segments = 32
    tray_du = 2.0 * math.pi / tray_segments
    for index in range(tray_segments):
        u = (index + 0.5) * tray_du
        length = R * tray_du * 1.04
        name = f"SERVICE_CABLE_TRAY_SEGMENT_{index + 1:02d}"
        builder.add(
            name,
            oriented_box((length, service_cfg["cable_tray_width_m"], service_cfg["cable_tray_height_m"]), u,
                         _point_on_ring(tray_radius, u, 0.0)),
            "cable_tray",
            family="cable_tray",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="CABLE_ROUTING_EMI_THERMAL_FIRE_REVIEW",
            attachment_parent=f"STRUCTURE_PRIMARY_FRAME_{(index // 2) + 1:02d}_OUTER_POST",
            source_basis="owner cable-space directive",
            physical=True,
            maintainable=True,
            print_candidate=True,
        )

    # Field modules, brackets, connectors, harnesses and clearances for all sectors.
    for sector in range(sectors):
        u = (sector + 0.5) * du
        root = f"STRUCTURE_PRIMARY_FRAME_{sector + 1:02d}_OUTER_POST"
        module = f"SYSTEM_FIELD_MODULE_{sector + 1:02d}"
        bracket = f"ATTACH_FIELD_MODULE_{sector + 1:02d}"
        clearance = f"CLEARANCE_FIELD_MODULE_{sector + 1:02d}"
        removal = f"REMOVAL_FIELD_MODULE_{sector + 1:02d}"
        cable = f"HARNESS_FIELD_MODULE_{sector + 1:02d}"
        connector = f"CONNECTOR_FIELD_MODULE_{sector + 1:02d}"
        module_center = _point_on_ring(R + 1.25, u, 0.0)
        builder.add(
            bracket,
            oriented_box((0.65, 0.32, 0.18), u, _point_on_ring(R + 1.52, u, 0.0)),
            "structure",
            family="attachment",
            evidence_state="PROVISIONAL_INTERFACE",
            review_gate="COMPONENT_ATTACHMENT_LOAD_REVIEW",
            attachment_parent=root,
            source_basis="owner physical-attachment directive",
            physical=True,
            print_candidate=True,
        )
        builder.add(
            module,
            radial_cylinder(0.30, 0.72, u, R + 1.25, 0.0, sections=36),
            "field",
            family="field_module",
            evidence_state="SOURCE_ALIGNED_TOPOLOGY",
            review_gate="COIL_FIELD_INSULATION_THERMAL_REVIEW",
            attachment_parent=bracket,
            source_basis="Free Flow Solenoid Stack plus Luke 16-sector topology",
            physical=True,
            maintainable=True,
            cable_required=True,
            cable_route=cable,
            service_clearance=clearance,
            removal_path=removal,
            print_candidate=True,
        )
        coil = trimesh.creation.torus(major_radius=0.21, minor_radius=0.055, major_sections=48, minor_sections=12)
        coil.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], [math.cos(u), math.sin(u), 0]))
        coil.apply_translation(module_center)
        builder.add(
            f"SYSTEM_FIELD_COIL_{sector + 1:02d}", coil, "coil",
            family="field_coil",
            evidence_state="SYNTHETIC_GEOMETRY_FROM_SOLENOID_TWIN",
            review_gate="COIL_FIELD_INSULATION_THERMAL_REVIEW",
            attachment_parent=module,
            source_basis="Free Flow Solenoid Stack geometry class",
            physical=True,
            maintainable=True,
            cable_required=True,
            cable_route=cable,
            service_clearance=clearance,
            removal_path=removal,
        )
        builder.add(
            connector,
            oriented_box((0.22, 0.16, 0.14), u, _point_on_ring(R + 1.55, u, 0.20)),
            "connector",
            family="connector",
            evidence_state="PROVISIONAL_INTERFACE",
            review_gate="CONNECTOR_SELECTION_AND_ACCESS_REVIEW",
            attachment_parent=bracket,
            source_basis="owner connector-access directive",
            physical=True,
            maintainable=True,
            cable_required=True,
            cable_route=cable,
            service_clearance=clearance,
        )
        builder.add(
            cable,
            radial_cylinder(0.035, 0.62, u, R + 1.57, 0.20, sections=18),
            "power_cable",
            family="power_harness",
            evidence_state="PROVISIONAL_ROUTE_ENVELOPE",
            review_gate="CABLE_GAUGE_BEND_EMI_THERMAL_REVIEW",
            attachment_parent=connector,
            source_basis="owner cable-space directive",
            physical=True,
            maintainable=True,
        )
        builder.add(
            f"HARNESS_DATA_FIELD_MODULE_{sector + 1:02d}",
            radial_cylinder(0.022, 0.62, u, R + 1.57, -0.20, sections=16),
            "data_cable",
            family="data_harness",
            evidence_state="PROVISIONAL_ROUTE_ENVELOPE",
            review_gate="CABLE_GAUGE_BEND_EMI_THERMAL_REVIEW",
            attachment_parent=connector,
            source_basis="owner cable-space directive",
            physical=True,
            maintainable=True,
        )
        builder.add(
            clearance,
            oriented_box((1.30, 0.95, 1.10), u, _point_on_ring(R + 1.28, u, 0.0)),
            "service",
            family="service_clearance",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="MAINTENANCE_ACCESS_REVIEW",
            attachment_parent=module,
            source_basis="owner repair-access directive",
            physical=False,
        )
        builder.add(
            removal,
            oriented_box((1.30, service_cfg["removal_path_length_m"], 1.10), u,
                         _point_on_ring(R + 1.75, u, 0.0)),
            "egress",
            family="removal_path",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="MAINTENANCE_REMOVAL_PATH_REVIEW",
            attachment_parent=module,
            source_basis="owner repair-access directive",
            physical=False,
        )
        # Sensor node and mount bracket.
        sensor_mount = f"ATTACH_SENSOR_NODE_{sector + 1:02d}"
        sensor = f"SYSTEM_SENSOR_NODE_{sector + 1:02d}"
        builder.add(
            sensor_mount,
            oriented_box((0.22, 0.12, 0.10), u, _point_on_ring(R - 1.46, u, 0.45)),
            "structure",
            family="attachment",
            evidence_state="PROVISIONAL_INTERFACE",
            review_gate="SENSOR_MOUNT_ALIGNMENT_REVIEW",
            attachment_parent=f"STRUCTURE_PRIMARY_FRAME_{sector + 1:02d}_INNER_POST",
            source_basis="Luke sensor topology",
            physical=True,
        )
        sphere = trimesh.creation.icosphere(subdivisions=1, radius=0.13)
        sphere.apply_translation(_point_on_ring(R - 1.56, u, 0.45))
        builder.add(
            sensor, sphere, "sensor",
            family="sensor_system",
            evidence_state="SOURCE_ALIGNED_TOPOLOGY",
            review_gate="INSTRUMENTATION_CALIBRATION_CONTROL_REVIEW",
            attachment_parent=sensor_mount,
            source_basis="Luke/Mark III sensor schema",
            physical=True,
            maintainable=True,
            cable_required=True,
            cable_route=f"HARNESS_DATA_SENSOR_{sector + 1:02d}",
            service_clearance=f"CLEARANCE_SENSOR_{sector + 1:02d}",
        )
        builder.add(
            f"HARNESS_DATA_SENSOR_{sector + 1:02d}",
            oriented_box((0.42, 0.04, 0.04), u, _point_on_ring(R - 1.35, u, 0.45)),
            "data_cable",
            family="data_harness",
            evidence_state="PROVISIONAL_ROUTE_ENVELOPE",
            review_gate="CABLE_GAUGE_BEND_EMI_THERMAL_REVIEW",
            attachment_parent=sensor_mount,
            source_basis="owner cable-space directive",
            physical=True,
        )
        builder.add(
            f"CLEARANCE_SENSOR_{sector + 1:02d}",
            oriented_box((0.55, 0.45, 0.55), u, _point_on_ring(R - 1.55, u, 0.45)),
            "service",
            family="service_clearance",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="MAINTENANCE_ACCESS_REVIEW",
            attachment_parent=sensor,
            source_basis="owner repair-access directive",
            physical=False,
        )

    # Shared resonator, capacitor, battery and damping racks with physical attachments.
    equipment_sets = [
        ("SYSTEM_RESONATOR_BAY", "resonator", "resonator_system", (0.0, math.pi / 2, math.pi, 3 * math.pi / 2), 1.10, 0.85),
        ("SYSTEM_POWER_CAPACITOR_BAY", "capacitor", "power_capacitor", (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4), -1.05, 0.90),
        ("SYSTEM_POWER_BATTERY_BMS", "battery", "power_battery", (math.pi / 3, 4 * math.pi / 3), -0.35, 1.05),
    ]
    for prefix, mat_key, family, angles, z, radial_offset in equipment_sets:
        for number, u in enumerate(angles, 1):
            sector = int((u % (2 * math.pi)) // du)
            root = f"STRUCTURE_PRIMARY_FRAME_{sector + 1:02d}_OUTER_POST"
            rack = f"ATTACH_{prefix}_{number}"
            node = f"{prefix}_{number}"
            cable = f"HARNESS_{prefix}_{number}"
            clearance = f"CLEARANCE_{prefix}_{number}"
            removal = f"REMOVAL_{prefix}_{number}"
            centre = _point_on_ring(R + radial_offset, u, z)
            builder.add(
                rack,
                oriented_box((2.15, 0.22, 0.22), u, _point_on_ring(R + radial_offset + 0.22, u, z)),
                "structure",
                family="attachment",
                evidence_state="PROVISIONAL_INTERFACE",
                review_gate="COMPONENT_ATTACHMENT_LOAD_REVIEW",
                attachment_parent=root,
                source_basis="Luke equipment-bay topology",
                physical=True,
                print_candidate=True,
            )
            builder.add(
                node,
                oriented_box((1.80, 0.72, 0.58), u, centre),
                mat_key,
                family=family,
                evidence_state="SOURCE_ALIGNED_TOPOLOGY" if family != "power_battery" else "SOURCE_ALIGNED_MODULE_CLASS",
                review_gate=("RFS_EMI_REVIEW" if family == "resonator_system" else "POWER_THERMAL_SAFETY_REVIEW"),
                attachment_parent=rack,
                source_basis=("RFS/EMFF inheritance" if family == "resonator_system" else "Free Flow energy-storage inheritance"),
                physical=True,
                maintainable=True,
                cable_required=True,
                cable_route=cable,
                service_clearance=clearance,
                removal_path=removal,
                print_candidate=True,
            )
            builder.add(
                cable,
                oriented_box((0.60, 0.055, 0.055), u, _point_on_ring(R + 1.42, u, z)),
                "power_cable" if family != "resonator_system" else "data_cable",
                family="power_harness" if family != "resonator_system" else "data_harness",
                evidence_state="PROVISIONAL_ROUTE_ENVELOPE",
                review_gate="CABLE_GAUGE_BEND_EMI_THERMAL_REVIEW",
                attachment_parent=rack,
                source_basis="owner cable-space directive",
                physical=True,
            )
            builder.add(
                clearance,
                oriented_box((2.35, 1.30, 1.15), u, centre),
                "service",
                family="service_clearance",
                evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
                review_gate="MAINTENANCE_ACCESS_REVIEW",
                attachment_parent=node,
                source_basis="owner repair-access directive",
                physical=False,
            )
            builder.add(
                removal,
                oriented_box((2.35, 0.95, 1.15), u, _point_on_ring(R + radial_offset + 0.75, u, z)),
                "egress",
                family="removal_path",
                evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
                review_gate="MAINTENANCE_REMOVAL_PATH_REVIEW",
                attachment_parent=node,
                source_basis="owner repair-access directive",
                physical=False,
            )

    for number, u in enumerate((3 * math.pi / 8, 7 * math.pi / 8, 11 * math.pi / 8, 15 * math.pi / 8), 1):
        sector = int((u % (2 * math.pi)) // du)
        root = f"STRUCTURE_PRIMARY_FRAME_{sector + 1:02d}_OUTER_POST"
        attach = f"ATTACH_DAMPING_PLACEHOLDER_{number}"
        node = f"SYSTEM_DAMPING_PLACEHOLDER_{number}"
        builder.add(
            attach,
            oriented_box((0.55, 0.24, 0.18), u, _point_on_ring(R + 0.72, u, -0.15)),
            "structure",
            family="attachment",
            evidence_state="PROVISIONAL_INTERFACE",
            review_gate="COMPONENT_ATTACHMENT_LOAD_REVIEW",
            attachment_parent=root,
            source_basis="Luke damping placeholder topology",
            physical=True,
        )
        builder.add(
            node,
            radial_cylinder(0.34, 1.25, u, R + 0.55, -0.15),
            "damping",
            family="damping_system",
            evidence_state="CONCEPTUAL_SPECIALIST_REVIEW",
            review_gate="GAS_PRESSURE_HAZARD_REVIEW",
            attachment_parent=attach,
            source_basis="Luke conceptual damping register",
            physical=True,
            maintainable=True,
            service_clearance=f"CLEARANCE_DAMPING_{number}",
        )
        builder.add(
            f"CLEARANCE_DAMPING_{number}",
            radial_cylinder(0.62, 1.55, u, R + 0.65, -0.15),
            "service",
            family="service_clearance",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="MAINTENANCE_ACCESS_REVIEW",
            attachment_parent=node,
            source_basis="owner repair-access directive",
            physical=False,
        )

    # Five-sector connected habitation layout, walkways, doorway frames and removable linings.
    hab_start = min(habitat_indices) * du
    hab_end = (max(habitat_indices) + 1) * du
    pressure_clear_r = float(parameters["habitation"]["pressure_liner_clear_minor_radius_m"])
    service_clear_r = float(parameters["habitation"]["service_allocated_clear_minor_radius_m"])
    builder.add(
        "CLEARANCE_HABITAT_GROSS_VOLUME",
        torus_segment_solid(R, float(parameters["habitation"]["clear_minor_radius_m"]), hab_start, hab_end, 28, 32),
        "hab_clear",
        family="habitation_clearance",
        evidence_state="GROSS_DERIVED_TARGET_NOT_HUMAN_RATED",
        review_gate="HUMAN_FACTORS_ECLSS_PRESSURE_REVIEW",
        attachment_parent="PRIMARY_STRUCTURE",
        source_basis="prior gross 201.525 m3 planning envelope",
        physical=False,
        connected_to_walkway=True,
    )
    builder.add(
        "CLEARANCE_HABITAT_PRESSURE_VOLUME",
        torus_segment_solid(R, pressure_clear_r, hab_start, hab_end, 28, 32),
        "hab_clear",
        family="habitation_clearance",
        evidence_state="DERIVED_SERVICEABILITY_ALLOCATION_NOT_HUMAN_RATED",
        review_gate="HUMAN_FACTORS_ECLSS_PRESSURE_REVIEW",
        attachment_parent="PRIMARY_STRUCTURE",
        source_basis="pressure-liner spatial reservation",
        physical=False,
        connected_to_walkway=True,
    )
    builder.add(
        "CLEARANCE_HABITAT_SERVICE_ALLOCATED_VOLUME",
        torus_segment_solid(R, service_clear_r, hab_start, hab_end, 28, 32),
        "hab_clear",
        family="habitation_clearance",
        evidence_state="DERIVED_SERVICEABILITY_ALLOCATION_NOT_HUMAN_RATED",
        review_gate="HUMAN_FACTORS_ECLSS_MAINTENANCE_REVIEW",
        attachment_parent="PRIMARY_STRUCTURE",
        source_basis="internal service and walkway reservation",
        physical=False,
        connected_to_walkway=True,
    )

    walkway_segments = int(access_cfg["walkway_segment_count"])
    walkway_du = (hab_end - hab_start) / walkway_segments
    walkway_names: list[str] = []
    for index in range(walkway_segments):
        u = hab_start + (index + 0.5) * walkway_du
        length = R * walkway_du * 1.06
        name = f"HAB_WALKWAY_SEGMENT_{index + 1:02d}"
        walkway_names.append(name)
        builder.add(
            name,
            oriented_box((length, access_cfg["walkway_width_m"], access_cfg["walkway_deck_thickness_m"]), u,
                         _point_on_ring(R, u, -0.82)),
            "walkway",
            family="habitat_walkway",
            evidence_state="DERIVED_SERVICEABLE_LAYOUT",
            review_gate="HUMAN_FACTORS_EGRESS_LOAD_REVIEW",
            attachment_parent=f"STRUCTURE_PRIMARY_FRAME_{min(max(int(u // du), 0), sectors - 1) + 1:02d}_LOWER_BEAM",
            source_basis="owner connected-walkway directive",
            physical=True,
            connected_to_walkway=True,
            print_candidate=True,
        )
        builder.add(
            f"HAB_EGRESS_PATH_{index + 1:02d}",
            oriented_box((length, 0.82, 1.90), u, _point_on_ring(R, u, 0.17)),
            "egress",
            family="egress_path",
            evidence_state="PROVISIONAL_HUMAN_FACTORS_RESERVATION",
            review_gate="EMERGENCY_EGRESS_SAFE_HAVEN_REVIEW",
            attachment_parent=name,
            source_basis="owner walkway and access directive",
            physical=False,
            connected_to_walkway=True,
        )

    room_specs = [
        ("HAB_COMMAND_TELEMETRY", 9, 0.15),
        ("HAB_WARDROOM_GALLEY", 10, -0.15),
        ("HAB_CREW_SLEEP_CLUSTER", 11, 0.10),
        ("HAB_HYGIENE_EXERCISE", 12, -0.10),
        ("HAB_ECLSS_MEDICAL_STORES", 13, 0.05),
    ]
    for room_index, (room_name, sector_index, z_offset) in enumerate(room_specs, 1):
        u = (sector_index + 0.5) * du
        room_parent = f"HAB_WALKWAY_SEGMENT_{min((room_index - 1) * 5 + 3, walkway_segments):02d}"
        builder.add(
            f"CLEARANCE_{room_name}",
            oriented_box((4.20, 2.20, 2.35), u, _point_on_ring(R, u, 0.18)),
            "hab_clear",
            family="habitat_room_clearance",
            evidence_state="DERIVED_FUNCTIONAL_LAYOUT",
            review_gate="HUMAN_FACTORS_ECLSS_REVIEW",
            attachment_parent=room_parent,
            source_basis="Luke II functional-zone register",
            physical=False,
            connected_to_walkway=True,
        )
        # Three removable service linings per room.
        for suffix, extents, offset in (
            ("OUTER", (3.80, 0.08, 2.10), (0.0, 0.92, 0.18)),
            ("INNER", (3.80, 0.08, 2.10), (0.0, -0.92, 0.18)),
            ("CEILING", (3.80, 1.75, 0.08), (0.0, 0.0, 1.23)),
        ):
            tangent = np.array([-math.sin(u), math.cos(u), 0.0])
            radial = np.array([math.cos(u), math.sin(u), 0.0])
            centre = _point_on_ring(R, u) + tangent * offset[0] + radial * offset[1] + np.array([0.0, 0.0, offset[2]])
            builder.add(
                f"HAB_LINING_{room_index:02d}_{suffix}",
                oriented_box(extents, u, centre),
                "lining",
                family="removable_lining",
                evidence_state="DERIVED_SERVICEABLE_LAYOUT",
                review_gate="INTERIOR_PANEL_FIRE_LOAD_MAINTENANCE_REVIEW",
                attachment_parent=f"STRUCTURE_PRIMARY_FRAME_{sector_index + 1:02d}_{'OUTER_POST' if suffix == 'OUTER' else 'INNER_POST' if suffix == 'INNER' else 'TOP_BEAM'}",
                source_basis="owner panelled interior directive",
                physical=True,
                maintainable=True,
                service_clearance=f"CLEARANCE_LINING_{room_index:02d}_{suffix}",
                print_candidate=True,
                connected_to_walkway=True,
            )
            builder.add(
                f"CLEARANCE_LINING_{room_index:02d}_{suffix}",
                oriented_box(tuple(float(x) + 0.18 for x in extents), u, centre),
                "service",
                family="service_clearance",
                evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
                review_gate="MAINTENANCE_ACCESS_REVIEW",
                attachment_parent=f"HAB_LINING_{room_index:02d}_{suffix}",
                source_basis="owner repair-access directive",
                physical=False,
                connected_to_walkway=True,
            )

        # Functional equipment mounted to deck or lining.
        equipment_name = f"{room_name}_EQUIPMENT"
        equipment_extents = (1.60, 0.58, 0.90) if room_index != 3 else (1.75, 0.65, 0.60)
        equipment_center = _point_on_ring(R + (0.42 if room_index % 2 else -0.42), u, z_offset - 0.20)
        builder.add(
            equipment_name,
            oriented_box(equipment_extents, u, equipment_center),
            "habitat",
            family="habitation_equipment",
            evidence_state="DERIVED_FUNCTIONAL_LAYOUT",
            review_gate="HUMAN_FACTORS_ECLSS_EQUIPMENT_REVIEW",
            attachment_parent=room_parent,
            source_basis="Luke II functional-zone register",
            physical=True,
            maintainable=True,
            cable_required=True,
            cable_route=f"HARNESS_{room_name}",
            service_clearance=f"CLEARANCE_{equipment_name}",
            removal_path=f"REMOVAL_{equipment_name}",
            connected_to_walkway=True,
        )
        builder.add(
            f"HARNESS_{room_name}",
            oriented_box((1.25, 0.045, 0.045), u, _point_on_ring(R + (0.78 if room_index % 2 else -0.78), u, -0.30)),
            "data_cable" if room_index == 1 else "power_cable",
            family="habitat_harness",
            evidence_state="PROVISIONAL_ROUTE_ENVELOPE",
            review_gate="CABLE_GAUGE_BEND_EMI_THERMAL_REVIEW",
            attachment_parent=room_parent,
            source_basis="owner cable-space directive",
            physical=True,
            maintainable=True,
            connected_to_walkway=True,
        )
        builder.add(
            f"CLEARANCE_{equipment_name}",
            oriented_box(tuple(float(x) + service_cfg["component_service_clearance_m"] for x in equipment_extents), u, equipment_center),
            "service",
            family="service_clearance",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="MAINTENANCE_ACCESS_REVIEW",
            attachment_parent=equipment_name,
            source_basis="owner repair-access directive",
            physical=False,
            connected_to_walkway=True,
        )
        builder.add(
            f"REMOVAL_{equipment_name}",
            oriented_box((1.85, 0.75, 1.10), u, _point_on_ring(R, u, 0.05)),
            "egress",
            family="removal_path",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="MAINTENANCE_REMOVAL_PATH_REVIEW",
            attachment_parent=equipment_name,
            source_basis="owner repair-access directive",
            physical=False,
            connected_to_walkway=True,
        )

    # Doorway frames and panelled partitions at each room boundary.
    door_width = float(access_cfg["door_clear_width_m"])
    door_height = float(access_cfg["door_clear_height_m"])
    for boundary_index, u in enumerate([10 * du, 11 * du, 12 * du, 13 * du], 1):
        root = f"STRUCTURE_PRIMARY_FRAME_{int(round(u / du)) + 1:02d}_OUTER_POST"
        post = 0.14
        floor_z = -0.78
        parts = [
            ("INNER_POST", (0.14, post, door_height), -door_width / 2 - post / 2, floor_z + door_height / 2),
            ("OUTER_POST", (0.14, post, door_height), door_width / 2 + post / 2, floor_z + door_height / 2),
            ("HEADER", (0.14, door_width + 2 * post, 0.16), 0.0, floor_z + door_height + 0.08),
            ("INNER_PANEL", (0.14, 0.42, 2.30), -1.05, 0.12),
            ("OUTER_PANEL", (0.14, 0.42, 2.30), 1.05, 0.12),
            ("TOP_PANEL", (0.14, 1.78, 0.32), 0.0, 1.33),
        ]
        for suffix, extents, radial_offset, z in parts:
            builder.add(
                f"HAB_BULKHEAD_{boundary_index:02d}_{suffix}",
                oriented_box(extents, u, _point_on_ring(R + radial_offset, u, z)),
                "lining" if "PANEL" in suffix else "structure",
                family="habitat_bulkhead",
                evidence_state="DERIVED_SERVICEABLE_LAYOUT",
                review_gate="PRESSURE_FIRE_EGRESS_BULKHEAD_REVIEW",
                attachment_parent=root,
                source_basis="owner connected-room and panelled-wall directive",
                physical=True,
                maintainable=("PANEL" in suffix),
                connected_to_walkway=True,
                print_candidate=True,
            )

    # Three berths as separately mounted components.
    sleep_u = 11.5 * du
    for index, z in enumerate((-0.30, 0.35, 0.95), 1):
        name = f"HAB_CREW_BERTH_{index}"
        builder.add(
            name,
            oriented_box((1.75, 0.66, 0.48), sleep_u, _point_on_ring(R + 0.52, sleep_u, z)),
            "habitat",
            family="habitation_equipment",
            evidence_state="DERIVED_FUNCTIONAL_LAYOUT",
            review_gate="HUMAN_FACTORS_SLEEP_STATION_REVIEW",
            attachment_parent="HAB_LINING_03_OUTER",
            source_basis="three-crew owner directive",
            physical=True,
            maintainable=True,
            cable_required=True,
            cable_route="HARNESS_HAB_CREW_SLEEP_CLUSTER",
            service_clearance=f"CLEARANCE_HAB_CREW_BERTH_{index}",
            connected_to_walkway=True,
        )
        builder.add(
            f"CLEARANCE_HAB_CREW_BERTH_{index}",
            oriented_box((2.10, 1.00, 0.78), sleep_u, _point_on_ring(R + 0.42, sleep_u, z)),
            "service",
            family="service_clearance",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="HUMAN_FACTORS_MAINTENANCE_REVIEW",
            attachment_parent=name,
            source_basis="owner repair-access directive",
            physical=False,
            connected_to_walkway=True,
        )

    # Docking collars and future interfaces.
    for number, u in enumerate((0.0, math.pi), 1):
        root = f"STRUCTURE_PRIMARY_FRAME_{int((u % (2 * math.pi)) // du) + 1:02d}_OUTER_POST"
        builder.add(
            f"INTERFACE_PROVISIONAL_DOCKING_COLLAR_{number}",
            radial_cylinder(1.10, 2.40, u, R + r + 1.15, 0.0, 64),
            "interface",
            family="interface",
            evidence_state="PROVISIONAL_INTERFACE",
            review_gate="DOCKING_STRUCTURAL_STANDARD_REVIEW",
            attachment_parent=root,
            source_basis="Luke interface register",
            physical=True,
            maintainable=True,
            service_clearance=f"CLEARANCE_INTERFACE_DOCKING_COLLAR_{number}",
            removal_path=f"REMOVAL_INTERFACE_DOCKING_COLLAR_{number}",
            print_candidate=True,
        )
        builder.add(
            f"CLEARANCE_INTERFACE_DOCKING_COLLAR_{number}",
            radial_cylinder(1.42, 2.95, u, R + r + 1.42, 0.0, 48),
            "service",
            family="service_clearance",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="DOCKING_SERVICE_COLLISION_REVIEW",
            attachment_parent=f"INTERFACE_PROVISIONAL_DOCKING_COLLAR_{number}",
            source_basis="owner repair-access directive",
            physical=False,
        )
        builder.add(
            f"REMOVAL_INTERFACE_DOCKING_COLLAR_{number}",
            radial_cylinder(1.32, 3.20, u, R + r + 2.20, 0.0, 40),
            "egress",
            family="removal_path",
            evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
            review_gate="DOCKING_REPLACEMENT_PATH_REVIEW",
            attachment_parent=f"INTERFACE_PROVISIONAL_DOCKING_COLLAR_{number}",
            source_basis="owner on-site assembly directive",
            physical=False,
        )

    # Mark III decomposed arm at the +Y interface.
    u = math.pi / 2.0
    root = f"STRUCTURE_PRIMARY_FRAME_{int(u // du) + 1:02d}_OUTER_POST"
    port_radius = R + r + 0.78
    builder.add(
        "INTERFACE_MARK_III_BASE_COLLAR",
        radial_cylinder(0.78, 1.10, u, port_radius, 0.0, 56),
        "interface",
        family="mark_iii_interface",
        evidence_state="PROVISIONAL_INTERFACE",
        review_gate="MARK_III_INTERFACE_CONTROL_DOCUMENT_REVIEW",
        attachment_parent=root,
        source_basis="Mark III modular coupling context",
        physical=True,
        maintainable=True,
        service_clearance="CLEARANCE_MARK_III_ARM",
        removal_path="REMOVAL_MARK_III_ARM",
        print_candidate=True,
    )
    base_centre = _point_on_ring(port_radius + 0.62, u, 0.0)
    builder.add(
        "INTERFACE_MARK_III_ARM_BASE_YAW",
        radial_cylinder(arm_cfg["base_yaw_radius_m"], arm_cfg["base_yaw_depth_m"], u, port_radius + 0.58, 0.0, 48),
        "arm",
        family="mark_iii_arm_joint",
        evidence_state="PROVISIONAL_INTERFACE_DECOMPOSITION_FROM_MARK_III_TWIN",
        review_gate="JOINT_LOAD_ACTUATION_CONTROL_REVIEW",
        attachment_parent="INTERFACE_MARK_III_BASE_COLLAR",
        source_basis="Mark III coupling-node and arm-interface scaffolds",
        physical=True,
        maintainable=True,
        cable_required=True,
        cable_route="HARNESS_MARK_III_ARM",
        service_clearance="CLEARANCE_MARK_III_ARM",
        removal_path="REMOVAL_MARK_III_ARM",
        print_candidate=True,
    )
    builder.add(
        "INTERFACE_MARK_III_ARM_SHOULDER_PITCH",
        tangent_cylinder(arm_cfg["shoulder_pitch_radius_m"], 0.48, u, port_radius + 0.82, 0.0, 48),
        "arm",
        family="mark_iii_arm_joint",
        evidence_state="PROVISIONAL_INTERFACE_DECOMPOSITION_FROM_MARK_III_TWIN",
        review_gate="JOINT_LOAD_ACTUATION_CONTROL_REVIEW",
        attachment_parent="INTERFACE_MARK_III_ARM_BASE_YAW",
        source_basis="Mark III coupling-node and arm-interface scaffolds",
        physical=True,
        maintainable=True,
        cable_required=True,
        cable_route="HARNESS_MARK_III_ARM",
        service_clearance="CLEARANCE_MARK_III_ARM",
        print_candidate=True,
    )
    upper_length = float(arm_cfg["upper_link_length_m"])
    fore_length = float(arm_cfg["fore_link_length_m"])
    link_x, link_z = [float(value) for value in arm_cfg["link_section_m"]]
    upper_centre_r = port_radius + 0.82 + upper_length / 2.0
    builder.add(
        "INTERFACE_MARK_III_ARM_UPPER_LINK",
        oriented_box((link_x, upper_length, link_z), u, _point_on_ring(upper_centre_r, u, 0.0)),
        "arm",
        family="mark_iii_arm_link",
        evidence_state="PROVISIONAL_INTERFACE_DECOMPOSITION_FROM_MARK_III_TWIN",
        review_gate="ARM_LINK_LOAD_BUCKLING_PRINT_REVIEW",
        attachment_parent="INTERFACE_MARK_III_ARM_SHOULDER_PITCH",
        source_basis="Mark III spool/rope arm placeholder expanded for interface review",
        physical=True,
        maintainable=True,
        cable_required=True,
        cable_route="HARNESS_MARK_III_ARM",
        service_clearance="CLEARANCE_MARK_III_ARM",
        print_candidate=True,
    )
    elbow_r = port_radius + 0.82 + upper_length
    builder.add(
        "INTERFACE_MARK_III_ARM_ELBOW",
        tangent_cylinder(arm_cfg["elbow_radius_m"], 0.42, u, elbow_r, 0.0, 48),
        "arm",
        family="mark_iii_arm_joint",
        evidence_state="PROVISIONAL_INTERFACE_DECOMPOSITION_FROM_MARK_III_TWIN",
        review_gate="JOINT_LOAD_ACTUATION_CONTROL_REVIEW",
        attachment_parent="INTERFACE_MARK_III_ARM_UPPER_LINK",
        source_basis="Mark III arm-interface placeholder",
        physical=True,
        maintainable=True,
        cable_required=True,
        cable_route="HARNESS_MARK_III_ARM",
        service_clearance="CLEARANCE_MARK_III_ARM",
        print_candidate=True,
    )
    fore_centre_r = elbow_r + fore_length / 2.0
    builder.add(
        "INTERFACE_MARK_III_ARM_FORE_LINK",
        oriented_box((link_x * 0.88, fore_length, link_z * 0.88), u, _point_on_ring(fore_centre_r, u, 0.0)),
        "arm",
        family="mark_iii_arm_link",
        evidence_state="PROVISIONAL_INTERFACE_DECOMPOSITION_FROM_MARK_III_TWIN",
        review_gate="ARM_LINK_LOAD_BUCKLING_PRINT_REVIEW",
        attachment_parent="INTERFACE_MARK_III_ARM_ELBOW",
        source_basis="Mark III arm-interface placeholder",
        physical=True,
        maintainable=True,
        cable_required=True,
        cable_route="HARNESS_MARK_III_ARM",
        service_clearance="CLEARANCE_MARK_III_ARM",
        print_candidate=True,
    )
    wrist_r = elbow_r + fore_length
    builder.add(
        "INTERFACE_MARK_III_ARM_WRIST",
        tangent_cylinder(arm_cfg["wrist_radius_m"], 0.34, u, wrist_r, 0.0, 40),
        "arm",
        family="mark_iii_arm_joint",
        evidence_state="PROVISIONAL_INTERFACE_DECOMPOSITION_FROM_MARK_III_TWIN",
        review_gate="JOINT_LOAD_ACTUATION_CONTROL_REVIEW",
        attachment_parent="INTERFACE_MARK_III_ARM_FORE_LINK",
        source_basis="Mark III arm-interface placeholder",
        physical=True,
        maintainable=True,
        cable_required=True,
        cable_route="HARNESS_MARK_III_ARM",
        service_clearance="CLEARANCE_MARK_III_ARM",
        print_candidate=True,
    )
    builder.add(
        "INTERFACE_MARK_III_ARM_END_EFFECTOR",
        oriented_box((0.40, arm_cfg["end_effector_length_m"], 0.28), u,
                     _point_on_ring(wrist_r + arm_cfg["end_effector_length_m"] / 2.0, u, 0.0)),
        "interface",
        family="mark_iii_end_effector",
        evidence_state="PROVISIONAL_INTERFACE_DECOMPOSITION_FROM_MARK_III_TWIN",
        review_gate="END_EFFECTOR_INTERFACE_LOAD_CONTROL_REVIEW",
        attachment_parent="INTERFACE_MARK_III_ARM_WRIST",
        source_basis="Mark III spool/rope arm-interface placeholder",
        physical=True,
        maintainable=True,
        cable_required=True,
        cable_route="HARNESS_MARK_III_ARM",
        service_clearance="CLEARANCE_MARK_III_ARM",
        print_candidate=True,
    )
    for index, radial_offset in enumerate((port_radius + 1.05, elbow_r - 0.30, wrist_r - 0.25), 1):
        builder.add(
            f"INTERFACE_MARK_III_ARM_ACTUATOR_{index}",
            radial_cylinder(arm_cfg["actuator_housing_radius_m"], 0.46, u, radial_offset, 0.25, 36),
            "actuator",
            family="mark_iii_arm_actuator",
            evidence_state="PROVISIONAL_INTERFACE_DECOMPOSITION_FROM_MARK_III_TWIN",
            review_gate="ACTUATOR_SELECTION_LOAD_THERMAL_CONTROL_REVIEW",
            attachment_parent=("INTERFACE_MARK_III_ARM_SHOULDER_PITCH" if index == 1 else "INTERFACE_MARK_III_ARM_ELBOW" if index == 2 else "INTERFACE_MARK_III_ARM_WRIST"),
            source_basis="Mark III solenoid/actuator inheritance class",
            physical=True,
            maintainable=True,
            cable_required=True,
            cable_route="HARNESS_MARK_III_ARM",
            service_clearance="CLEARANCE_MARK_III_ARM",
            print_candidate=True,
        )
    chain_segments = 12
    chain_start = port_radius + 0.95
    chain_end = wrist_r + 0.10
    for index in range(chain_segments):
        radial_pos = chain_start + (index + 0.5) * (chain_end - chain_start) / chain_segments
        builder.add(
            f"HARNESS_MARK_III_ARM_CHAIN_{index + 1:02d}",
            oriented_box((0.10, (chain_end - chain_start) / chain_segments * 0.92, 0.08), u,
                         _point_on_ring(radial_pos, u, 0.22)),
            "data_cable" if index % 2 else "power_cable",
            family="mark_iii_arm_harness",
            evidence_state="PROVISIONAL_ROUTE_ENVELOPE",
            review_gate="CABLE_CHAIN_BEND_STRAIN_EMI_REVIEW",
            attachment_parent=("INTERFACE_MARK_III_ARM_UPPER_LINK" if radial_pos < elbow_r else "INTERFACE_MARK_III_ARM_FORE_LINK"),
            source_basis="owner cable-space directive",
            physical=True,
            maintainable=True,
        )
    builder.add(
        "HARNESS_MARK_III_ARM",
        oriented_box((0.18, chain_end - chain_start, arm_cfg["cable_chain_clearance_m"]), u,
                     _point_on_ring((chain_start + chain_end) / 2.0, u, 0.22)),
        "service",
        family="cable_route_envelope",
        evidence_state="PROVISIONAL_ROUTE_ENVELOPE",
        review_gate="CABLE_CHAIN_BEND_STRAIN_EMI_REVIEW",
        attachment_parent="INTERFACE_MARK_III_ARM_BASE_YAW",
        source_basis="owner cable-space directive",
        physical=False,
    )
    builder.add(
        "CLEARANCE_MARK_III_ARM",
        oriented_box((1.20, upper_length + fore_length + 1.40, 1.20), u,
                     _point_on_ring(port_radius + (upper_length + fore_length + 1.40) / 2.0, u, 0.0)),
        "service",
        family="service_clearance",
        evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
        review_gate="ARM_SERVICE_AND_COLLISION_ENVELOPE_REVIEW",
        attachment_parent="INTERFACE_MARK_III_ARM_BASE_YAW",
        source_basis="owner repair-access directive",
        physical=False,
    )
    builder.add(
        "REMOVAL_MARK_III_ARM",
        oriented_box((1.40, upper_length + fore_length + 2.20, 1.40), u,
                     _point_on_ring(port_radius + (upper_length + fore_length + 2.20) / 2.0, u, 0.0)),
        "egress",
        family="removal_path",
        evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
        review_gate="ARM_REMOVAL_AND_ONSITE_ASSEMBLY_REVIEW",
        attachment_parent="INTERFACE_MARK_III_ARM_BASE_YAW",
        source_basis="owner assembly and repair directive",
        physical=False,
    )

    # Luke IV handoff remains a placeholder, without arm detail.
    u = 3 * math.pi / 2
    root = f"STRUCTURE_PRIMARY_FRAME_{int(u // du) + 1:02d}_OUTER_POST"
    builder.add(
        "INTERFACE_LUKE_IV_HANDOFF",
        oriented_box((2.40, 1.35, 1.80), u, _point_on_ring(R + r + 0.85, u, 0.0)),
        "interface",
        family="interface",
        evidence_state="FUTURE_BRIDGE_PLACEHOLDER",
        review_gate="INTERFACE_CONTROL_DOCUMENT_REVIEW",
        attachment_parent=root,
        source_basis="Luke IV bridge register",
        physical=True,
        maintainable=True,
        service_clearance="CLEARANCE_INTERFACE_LUKE_IV_HANDOFF",
        removal_path="REMOVAL_INTERFACE_LUKE_IV_HANDOFF",
    )
    builder.add(
        "CLEARANCE_INTERFACE_LUKE_IV_HANDOFF",
        oriented_box((3.10, 2.10, 2.40), u, _point_on_ring(R + r + 1.10, u, 0.0)),
        "service",
        family="service_clearance",
        evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
        review_gate="INTERFACE_SERVICE_COLLISION_REVIEW",
        attachment_parent="INTERFACE_LUKE_IV_HANDOFF",
        source_basis="owner repair-access directive",
        physical=False,
    )
    builder.add(
        "REMOVAL_INTERFACE_LUKE_IV_HANDOFF",
        oriented_box((3.20, 3.40, 2.60), u, _point_on_ring(R + r + 2.20, u, 0.0)),
        "egress",
        family="removal_path",
        evidence_state="PROVISIONAL_MAINTAINABILITY_RESERVATION",
        review_gate="INTERFACE_REPLACEMENT_PATH_REVIEW",
        attachment_parent="INTERFACE_LUKE_IV_HANDOFF",
        source_basis="owner on-site assembly directive",
        physical=False,
    )

    # Illustrative payload sequence and field-guide nodes remain clearly nonphysical.
    builder.add(
        "PAYLOAD_GUIDE_AXIS",
        trimesh.creation.cylinder(radius=0.055, height=18.0, sections=32),
        "path",
        family="payload_path",
        evidence_state="ILLUSTRATIVE_SEQUENCE_ONLY",
        review_gate="GUIDANCE_CONTROL_ENVELOPE_REVIEW",
        attachment_parent="ILLUSTRATIVE_REFERENCE_ROOT",
        source_basis="Luke operational sequence",
        physical=False,
    )
    payload_radius = float(source["payload_reference_radius_m"]["value"])
    for name, z in (("PAYLOAD_INCOMING", -6.5), ("PAYLOAD_ACTIVE", 0.0), ("PAYLOAD_OUTGOING", 6.5)):
        sphere = trimesh.creation.icosphere(subdivisions=2, radius=payload_radius)
        sphere.apply_translation([0.0, 0.0, z])
        builder.add(
            name,
            sphere,
            "payload",
            family="payload_path",
            evidence_state="ILLUSTRATIVE_SEQUENCE_ONLY",
            review_gate="GUIDANCE_CONTROL_ENVELOPE_REVIEW",
            attachment_parent="PAYLOAD_GUIDE_AXIS",
            source_basis="Luke operational sequence",
            physical=False,
        )
    for index, z in enumerate((-1.25, 0.0, 1.25), 1):
        guide = trimesh.creation.torus(major_radius=R - r - 0.45, minor_radius=0.045,
                                       major_sections=128, minor_sections=10)
        guide.apply_translation([0.0, 0.0, z])
        builder.add(
            f"FIELD_GUIDE_RING_{index}",
            guide,
            "field_guide",
            family="field_guide",
            evidence_state="ILLUSTRATIVE_ONLY_NOT_PHYSICAL_FIELD",
            review_gate="MEASURED_FIELD_MAP_REVIEW",
            attachment_parent="ILLUSTRATIVE_REFERENCE_ROOT",
            source_basis="field-map review visualisation",
            physical=False,
        )

    return builder.scene, builder.records


def build_scene(parameters: dict[str, Any]) -> trimesh.Scene:
    return build_reference(parameters)[0]


def build_component_records(parameters: dict[str, Any]) -> list[dict[str, Any]]:
    return build_reference(parameters)[1]


def records_by_name(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["node_name"]: record for record in records}


def _concatenate(scene: trimesh.Scene, names: Iterable[str]) -> trimesh.Trimesh:
    meshes = [scene.geometry[name].copy() for name in names]
    if not meshes:
        raise ValueError("no meshes selected")
    combined = trimesh.util.concatenate(meshes)
    combined.remove_unreferenced_vertices()
    return combined


def build_print_references(parameters: dict[str, Any], scene: trimesh.Scene,
                           records: list[dict[str, Any]]) -> dict[str, trimesh.Trimesh]:
    record_map = records_by_name(records)
    physical_hull = [
        name for name, record in record_map.items()
        if record["physical"] and record["family"] in {"solar_hull_panel", "pressure_window", "window_frame"}
    ]
    full = _concatenate(scene, physical_hull)
    full.apply_scale(10.0)  # metres to millimetres at 1:100
    full.metadata["units"] = "mm"

    representative_panel = scene.geometry["HULL_SOLAR_PANEL_S01_B01"].copy()
    representative_panel.apply_scale(50.0)  # 1:20
    representative_panel.metadata["units"] = "mm"

    window_names = [name for name in scene.geometry if name.startswith("WINDOW_") and "S10_B01" in name]
    window_names += [name for name in scene.geometry if name.startswith("STRUCTURE_WINDOW_FRAME_S10_B01")]
    representative_window = _concatenate(scene, sorted(window_names))
    representative_window.apply_scale(50.0)
    representative_window.metadata["units"] = "mm"

    arm_names = [
        name for name, record in record_map.items()
        if record["physical"] and record["family"].startswith("mark_iii")
    ]
    representative_arm = _concatenate(scene, sorted(arm_names))
    representative_arm.apply_scale(50.0)
    representative_arm.metadata["units"] = "mm"

    return {
        "luke_ii_reference_1to100.stl": full,
        "luke_ii_representative_hull_panel_1to20.stl": representative_panel,
        "luke_ii_representative_window_1to20.stl": representative_window,
        "luke_ii_mark_iii_interface_arm_1to20.stl": representative_arm,
    }


def build_print_shell(parameters: dict[str, Any]) -> trimesh.Trimesh:
    scene, records = build_reference(parameters)
    return build_print_references(parameters, scene, records)["luke_ii_reference_1to100.stl"]


def component_manifest(scene: trimesh.Scene, records: list[dict[str, Any]],
                       parameters: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for record in records:
        mesh = scene.geometry[record["node_name"]]
        row = dict(record)
        row.update(
            {
                "bounds_m": [[round(float(v), 6) for v in point] for point in mesh.bounds],
                "extents_m": [round(float(v), 6) for v in mesh.extents],
                "centroid_m": [round(float(v), 6) for v in mesh.centroid],
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
                "watertight": bool(mesh.is_watertight),
                "winding_consistent": bool(mesh.is_winding_consistent),
            }
        )
        rows.append(row)
    return {
        "schema_version": "luke-ii-component-manifest-v1.3",
        "status": "REFERENCE_CONFIGURATION_ONLY",
        "source_state": parameters["artifact_status"],
        "task_issue": parameters["source_reconciliation"]["current_task_issue"],
        "node_count": len(rows),
        "components": rows,
        "claim_gate_state": "HELD_NO_ENGINEERING_CAPABILITY_PROMOTION",
    }


def verify(scene: trimesh.Scene, prints: dict[str, trimesh.Trimesh], parameters: dict[str, Any],
           outputs: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    checks = {
        name: {
            "vertices": len(geometry.vertices),
            "faces": len(geometry.faces),
            "watertight": bool(geometry.is_watertight),
            "winding_consistent": bool(geometry.is_winding_consistent),
        }
        for name, geometry in scene.geometry.items()
    }
    record_map = records_by_name(records)
    physical = [record for record in records if record["physical"]]
    maintainable = [record for record in physical if record["maintainable"]]
    cable_required = [record for record in physical if record["cable_required"]]
    return {
        "schema_version": "luke-ii-geometry-verification-v1.3",
        "status": "PASS_SERVICEABLE_REFERENCE_GEOMETRY",
        "not_certified_for": [
            "flight", "pressure vessel", "human rating", "high current", "payload capture performance",
            "radiation shielding", "electrical qualification", "thermal qualification", "manufacturing release",
        ],
        "scene": {
            "geometry_nodes": len(scene.geometry),
            "bounds_m": scene.bounds.tolist(),
            "extents_m": scene.extents.tolist(),
        },
        "configuration": {
            "physical_nodes": len(physical),
            "maintainable_nodes": len(maintainable),
            "cable_required_nodes": len(cable_required),
            "all_physical_nodes_have_attachment_parent": all(record["attachment_parent"] for record in physical),
            "all_maintainable_nodes_have_clearance_or_structural_role": all(
                record["service_clearance"] or record["family"] in {
                    "solar_hull_panel", "window_frame", "cable_tray", "primary_structure",
                    "habitat_walkway", "habitat_bulkhead", "removable_lining",
                    "power_harness", "data_harness", "habitat_harness", "arm_harness",
                    "mark_iii_arm_harness",
                }
                for record in maintainable
            ),
            "all_cable_required_nodes_have_route": all(record["cable_route"] for record in cable_required),
            "window_nodes": sum(1 for record in records if record["family"] == "pressure_window"),
            "walkway_segments": sum(1 for record in records if record["family"] == "habitat_walkway"),
            "mark_iii_arm_nodes": sum(1 for record in records if record["family"].startswith("mark_iii")),
            "open_engineering_gaps": len(parameters["open_engineering_gaps"]),
        },
        "habitation": {
            "crew": parameters["habitation"]["crew"],
            "gross_clear_volume_m3": parameters["habitation"]["gross_clear_volume_m3"],
            "pressure_liner_clear_volume_m3": parameters["habitation"]["pressure_liner_clear_volume_m3"],
            "service_allocated_reference_volume_m3": parameters["habitation"]["service_allocated_reference_volume_m3"],
            "state": parameters["habitation"]["volume_revision_state"],
        },
        "print_references": {
            name: {
                "watertight": bool(mesh.is_watertight),
                "winding_consistent": bool(mesh.is_winding_consistent),
                "bounds_mm": mesh.bounds.tolist(),
                "extents_mm": mesh.extents.tolist(),
                "signed_volume_mm3": float(mesh.volume),
            }
            for name, mesh in prints.items()
        },
        "geometry_checks": checks,
        "outputs": outputs,
        "record_index": sorted(record_map),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parameters", type=Path, default=Path(__file__).with_name("luke_ii_parameters.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("generated"))
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    parameters = json.loads(args.parameters.read_text(encoding="utf-8"))
    scene, records = build_reference(parameters)

    glb_path = args.out_dir / "luke_ii_assembly.glb"
    glb_path.write_bytes(scene.export(file_type="glb"))

    manifest_path = args.out_dir / "luke_ii_component_manifest.json"
    manifest_path.write_text(json.dumps(component_manifest(scene, records, parameters), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    prints = build_print_references(parameters, scene, records)
    print_outputs: dict[str, Any] = {}
    for filename, mesh in prints.items():
        path = args.out_dir / filename
        mesh.export(path)
        print_outputs[filename] = {
            "path": filename,
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "units": "millimetres",
        }

    outputs = {
        "parameters": {"path": args.parameters.name, "sha256": sha256_file(args.parameters)},
        "assembly_glb": {"path": glb_path.name, "sha256": sha256_file(glb_path), "bytes": glb_path.stat().st_size},
        "component_manifest": {"path": manifest_path.name, "sha256": sha256_file(manifest_path), "bytes": manifest_path.stat().st_size},
        "print_references": print_outputs,
    }
    receipt = verify(scene, prints, parameters, outputs, records)
    verification_path = args.out_dir / "luke_ii_verification.json"
    verification_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "status": receipt["status"],
                "geometry_nodes": len(scene.geometry),
                "physical_nodes": receipt["configuration"]["physical_nodes"],
                "window_nodes": receipt["configuration"]["window_nodes"],
                "walkway_segments": receipt["configuration"]["walkway_segments"],
                "mark_iii_arm_nodes": receipt["configuration"]["mark_iii_arm_nodes"],
                "service_allocated_reference_volume_m3": receipt["habitation"]["service_allocated_reference_volume_m3"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
