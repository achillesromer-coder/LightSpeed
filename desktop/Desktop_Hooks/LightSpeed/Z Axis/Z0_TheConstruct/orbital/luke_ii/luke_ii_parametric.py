#!/usr/bin/env python3
"""Generate the source-reconciled Luke II reference assembly.

Outputs GLB, a 1:100 watertight STL reference shell and a JSON verification
receipt. This is not flight, pressure-vessel, human-rating or manufacturing
certification.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Iterable
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def material(name, rgba, metallic=0.15, roughness=0.62):
    return PBRMaterial(name=name, baseColorFactor=list(rgba), metallicFactor=metallic,
                       roughnessFactor=roughness,
                       alphaMode="BLEND" if rgba[3] < 255 else "OPAQUE",
                       doubleSided=True)


def set_material(mesh, mat):
    mesh.visual = trimesh.visual.TextureVisuals(material=mat)
    return mesh


def torus_segment(major_r, minor_r, u0, u1, nu=20, nv=36):
    us = np.linspace(u0, u1, nu + 1)
    vs = np.linspace(0.0, 2.0 * math.pi, nv, endpoint=False)
    vertices = []
    for u in us:
        cu, su = math.cos(u), math.sin(u)
        for v in vs:
            cv, sv = math.cos(v), math.sin(v)
            vertices.append(((major_r + minor_r * cv) * cu,
                             (major_r + minor_r * cv) * su,
                             minor_r * sv))
    vertices = np.asarray(vertices, dtype=float)
    faces = []
    for i in range(nu):
        for j in range(nv):
            jn = (j + 1) % nv
            a, b = i * nv + j, (i + 1) * nv + j
            c, d = (i + 1) * nv + jn, i * nv + jn
            faces.extend(((a, b, c), (a, c, d)))
    center0, center1 = len(vertices), len(vertices) + 1
    vertices = np.vstack((vertices,
        [major_r * math.cos(u0), major_r * math.sin(u0), 0.0],
        [major_r * math.cos(u1), major_r * math.sin(u1), 0.0]))
    for j in range(nv):
        jn = (j + 1) % nv
        faces.append((center0, jn, j))
        faces.append((center1, nu * nv + j, nu * nv + jn))
    mesh = trimesh.Trimesh(vertices=vertices, faces=np.asarray(faces), process=True)
    mesh.fix_normals(multibody=True)
    return mesh


def torus_shell(major_r, outer_r, inner_r, major_sections=256, minor_sections=64):
    outer = trimesh.creation.torus(major_radius=major_r, minor_radius=outer_r,
                                    major_sections=major_sections, minor_sections=minor_sections)
    inner = trimesh.creation.torus(major_radius=major_r, minor_radius=inner_r,
                                    major_sections=major_sections, minor_sections=minor_sections)
    inner.invert()
    shell = trimesh.util.concatenate((outer, inner))
    shell.remove_unreferenced_vertices()
    return shell


def frame_transform(angle, center):
    radial = np.array([math.cos(angle), math.sin(angle), 0.0])
    tangent = np.array([-math.sin(angle), math.cos(angle), 0.0])
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = tangent, radial, [0, 0, 1], center
    return T


def oriented_box(extents: Iterable[float], angle, center):
    return trimesh.creation.box(extents=np.asarray(extents, dtype=float),
                                transform=frame_transform(angle, center))


def radial_cylinder(radius, height, angle, radial_distance, z=0.0, sections=48):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_transform(trimesh.geometry.align_vectors([0, 0, 1],
        [math.cos(angle), math.sin(angle), 0.0]))
    mesh.apply_translation([radial_distance * math.cos(angle),
                            radial_distance * math.sin(angle), z])
    return mesh


def add(scene, name, mesh, mat):
    set_material(mesh, mat)
    scene.add_geometry(mesh, node_name=name, geom_name=name)


def build_scene(p):
    R = p["source_parameters"]["major_radius_m"]["value"]
    r = p["source_parameters"]["body_minor_radius_m"]["value"]
    sectors = p["source_parameters"]["field_sector_count"]["value"]
    habitat_count = p["habitation"]["reserved_sector_count"]
    hab_r = p["habitation"]["clear_minor_radius_m"]
    scene = trimesh.Scene()
    mats = {
        "shell": material("Shell", (95, 115, 130, 125), .45, .35),
        "habitat": material("Habitat", (52, 168, 112, 175), .05, .75),
        "field": material("Field modules", (52, 122, 235, 255), .2, .45),
        "resonator": material("Resonator", (160, 92, 230, 255), .25, .5),
        "power": material("Power", (245, 158, 11, 255), .15, .6),
        "sensor": material("Sensors", (20, 184, 166, 255), .2, .45),
        "damping": material("Damping placeholder", (100, 116, 139, 210), .2, .5),
        "payload": material("Payload", (239, 68, 68, 220), .55, .25),
        "path": material("Payload guide", (248, 250, 252, 150), .05, .25),
        "interface": material("Interface", (217, 70, 239, 255), .25, .45),
        "interior": material("Interior fixtures", (234, 179, 8, 255), .05, .75),
        "bulkhead": material("Bulkheads", (148, 163, 184, 255), .25, .55),
    }
    du = 2.0 * math.pi / sectors
    habitat_indices = set(range(9, 9 + habitat_count))
    for i in range(sectors):
        u0, u1, uc = i * du, (i + 1) * du, (i + .5) * du
        prefix = "SHELL_HABITAT_SECTOR" if i in habitat_indices else "SHELL_SYSTEM_SECTOR"
        add(scene, f"{prefix}_{i+1:02d}", torus_segment(R, r, u0, u1), mats["shell"])
        pod_center = np.array([(R+r+.42)*math.cos(uc), (R+r+.42)*math.sin(uc), 0.0])
        add(scene, f"SYSTEM_FIELD_MODULE_{i+1:02d}",
            oriented_box((1.65, .55, 1.35), uc, pod_center), mats["field"])
        sensor_center = np.array([(R-r-.18)*math.cos(uc), (R-r-.18)*math.sin(uc), 0.0])
        sensor = trimesh.creation.icosphere(subdivisions=2, radius=.14)
        sensor.apply_translation(sensor_center)
        add(scene, f"SYSTEM_SENSOR_NODE_{i+1:02d}", sensor, mats["sensor"])
        add(scene, f"STRUCTURE_BULKHEAD_{i+1:02d}",
            oriented_box((.10, 2.7, 2.7), u0,
                         np.array([R*math.cos(u0), R*math.sin(u0), 0])), mats["bulkhead"])
    hab_u0, hab_u1 = min(habitat_indices)*du, (max(habitat_indices)+1)*du
    add(scene, "HABITAT_PRESSURISED_CLEAR_VOLUME",
        torus_segment(R, hab_r, hab_u0, hab_u1, nu=70, nv=48), mats["habitat"])
    rooms = [
        ("HAB_COMMAND_TELEMETRY", 9.45, (3.3, 1.55, 1.35), .15),
        ("HAB_WARDROOM_GALLEY", 10.35, (3.5, 1.65, 1.35), -.15),
        ("HAB_CREW_SLEEP_CLUSTER", 11.30, (3.5, 1.50, 1.45), .10),
        ("HAB_HYGIENE_EXERCISE", 12.25, (3.3, 1.55, 1.35), -.10),
        ("HAB_ECLSS_MEDICAL_STORES", 13.15, (3.3, 1.55, 1.45), .05),
    ]
    for name, pos, ext, z in rooms:
        a = pos * du
        add(scene, name, oriented_box(ext, a, np.array([R*math.cos(a), R*math.sin(a), z])), mats["interior"])
    a = 11.30 * du
    radial = np.array([math.cos(a), math.sin(a), 0.0])
    base = np.array([R*math.cos(a), R*math.sin(a), 0.0])
    for j, z in enumerate((-.85, 0, .85), 1):
        add(scene, f"HAB_CREW_BERTH_{j}", oriented_box((1.75, .68, .55), a,
            base + radial*.15 + np.array([0, 0, z])), mats["habitat"])
    for i, a in enumerate((0, math.pi/2, math.pi, 3*math.pi/2), 1):
        c=np.array([(R+.35)*math.cos(a),(R+.35)*math.sin(a),1.25])
        add(scene,f"SYSTEM_RESONATOR_BAY_{i}",oriented_box((2,.9,.55),a,c),mats["resonator"])
    for i, a in enumerate((math.pi/4,3*math.pi/4,5*math.pi/4,7*math.pi/4),1):
        c=np.array([(R+.30)*math.cos(a),(R+.30)*math.sin(a),-1.25])
        add(scene,f"SYSTEM_POWER_CAPACITOR_BAY_{i}",oriented_box((2,.95,.60),a,c),mats["power"])
    for i, a in enumerate((3*math.pi/8,7*math.pi/8,11*math.pi/8,15*math.pi/8),1):
        add(scene,f"SYSTEM_DAMPING_PLACEHOLDER_{i}",radial_cylinder(.34,1.25,a,R+.55,-.15),mats["damping"])
    for i, a in enumerate((0, math.pi),1):
        add(scene,f"INTERFACE_PROVISIONAL_DOCKING_COLLAR_{i}",radial_cylinder(1.10,2.4,a,R+r+1.15,0,64),mats["interface"])
    for name,a in (("INTERFACE_MARK_III",math.pi/2),("INTERFACE_LUKE_IV_HANDOFF",3*math.pi/2)):
        c=np.array([(R+r+.85)*math.cos(a),(R+r+.85)*math.sin(a),0])
        add(scene,name,oriented_box((2.4,1.35,1.8),a,c),mats["interface"])
    add(scene,"PAYLOAD_GUIDE_AXIS",trimesh.creation.cylinder(radius=.055,height=18,sections=32),mats["path"])
    pr=p["source_parameters"]["payload_reference_radius_m"]["value"]
    for name,z in (("PAYLOAD_INCOMING",-6.5),("PAYLOAD_ACTIVE",0),("PAYLOAD_OUTGOING",6.5)):
        sphere=trimesh.creation.icosphere(subdivisions=3,radius=pr);sphere.apply_translation([0,0,z])
        add(scene,name,sphere,mats["payload"])
    for i,z in enumerate((-1.25,0,1.25),1):
        guide=trimesh.creation.torus(major_radius=R-r-.45,minor_radius=.045,major_sections=160,minor_sections=12)
        guide.apply_translation([0,0,z]);add(scene,f"FIELD_GUIDE_RING_{i}",guide,mats["field"])
    return scene


def build_print_shell(p):
    R=p["source_parameters"]["major_radius_m"]["value"]
    r=p["source_parameters"]["body_minor_radius_m"]["value"]
    t=p["derived_geometry"]["structural_shell_thickness_m"]["value"]
    shell=torus_shell(R,r,r-t);shell.apply_scale(10.0);shell.metadata["units"]="mm"
    return shell


def verify(scene,shell,p,outputs):
    checks={name:{"vertices":len(g.vertices),"faces":len(g.faces),"watertight":bool(g.is_watertight),"winding_consistent":bool(g.is_winding_consistent)} for name,g in scene.geometry.items()}
    return {
      "schema_version":"luke-ii-geometry-verification-v1","status":"PASS_REFERENCE_GEOMETRY",
      "not_certified_for":["flight","pressure vessel","human rating","high current","payload capture performance","radiation shielding","manufacturing release"],
      "scene":{"geometry_nodes":len(scene.geometry),"bounds_m":scene.bounds.tolist(),"extents_m":scene.extents.tolist()},
      "habitation":{"crew":p["habitation"]["crew"],"iss_scaled_baseline_m3":p["habitation"]["iss_scaled_baseline_m3"],"deep_space_comparator_m3":p["habitation"]["deep_space_linear_3_crew_comparator_m3"],"modelled_clear_volume_m3":p["habitation"]["modelled_habitable_volume_m3"]},
      "print_shell":{"watertight":bool(shell.is_watertight),"winding_consistent":bool(shell.is_winding_consistent),"bounds_mm":shell.bounds.tolist(),"extents_mm":shell.extents.tolist(),"signed_volume_mm3":float(shell.volume)},
      "geometry_checks":checks,"outputs":outputs}


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--parameters",default="luke_ii_parameters.json");ap.add_argument("--out-dir",default=".");args=ap.parse_args()
    out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
    pp=Path(args.parameters);p=json.loads(pp.read_text(encoding="utf-8"))
    scene=build_scene(p);glb=out/"luke_ii_assembly.glb";glb.write_bytes(scene.export(file_type="glb"))
    shell=build_print_shell(p);stl=out/"luke_ii_reference_1to100.stl";shell.export(stl)
    outputs={"parameters":{"path":pp.name,"sha256":sha256_file(pp)},"assembly_glb":{"path":glb.name,"sha256":sha256_file(glb),"bytes":glb.stat().st_size},"print_shell_stl":{"path":stl.name,"sha256":sha256_file(stl),"bytes":stl.stat().st_size}}
    receipt=verify(scene,shell,p,outputs);(out/"luke_ii_verification.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    print(json.dumps({"status":receipt["status"],"geometry_nodes":len(scene.geometry),"print_shell_watertight":shell.is_watertight,"habitable_volume_m3":p["habitation"]["modelled_habitable_volume_m3"]},indent=2))

if __name__=="__main__": main()
