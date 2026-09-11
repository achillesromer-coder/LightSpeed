"""Generate review-only OBJ viewer meshes for the ACHILLES Digital Twin Atrium.

IMPORTANT: SOURCE_DERIVED geometry is reconstructed from traceable source dimensions.
INTERACTION_PROXY geometry exists only for interactive visualization and MUST NOT be
used as manufacturing, structural, safety, performance, approval or deployment evidence.
Requires: numpy, trimesh.
"""
from pathlib import Path
import math, json
import numpy as np
import trimesh

OUT = Path("generated/digital-twin/atrium/models")
OUT.mkdir(parents=True, exist_ok=True)

def box(ext, c=(0,0,0)):
    m=trimesh.creation.box(extents=ext); m.apply_translation(c); return m

def cyl(r,h,c=(0,0,0),axis="z",sections=24):
    m=trimesh.creation.cylinder(radius=r,height=h,sections=sections)
    if axis=="x": m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[0,1,0]))
    if axis=="y": m.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
    m.apply_translation(c); return m

def torus(R,r,c=(0,0,0)):
    m=trimesh.creation.torus(major_radius=R,minor_radius=r,major_sections=36,minor_sections=12); m.apply_translation(c); return m

def cone(r,h,c=(0,0,0)):
    m=trimesh.creation.cone(radius=r,height=h,sections=32); m.apply_translation(c); return m

def cat(*parts): return trimesh.util.concatenate(parts)

M={}
# INTERACTION_PROXY family
M["solar_hull"]=cat(*[box((5*s,3*s,.1),(0,0,z)) for z,s in [(-.30,1),(-.18,.96),(-.06,.92),(.06,.88),(.18,.84),(.30,.80)]])
M["free_flow_batteries"]=cat(box((5.2,3.6,2.2)),*[cyl(.45,1.7,(x,y,0)) for x in (-1.6,0,1.6) for y in (-1,0,1)])
M["free_flow_capacitors"]=cat(box((5.5,3.2,.3),(0,0,-1)),*[cyl(.5,2,(x,0,0)) for x in (-1.8,-.6,.6,1.8)])
M["free_flow_solenoid_stack"]=cat(*[torus(1.8,.18,(0,0,z)) for z in (-1.4,-.7,0,.7,1.4)],cyl(.35,4))
M["rfs_emff"]=cat(cyl(.28,5),torus(1.6,.18,(0,0,-1)),torus(1.6,.18,(0,0,1)),box((4.5,4.5,.25),(0,0,-2.3)))
M["mark_1p"]=cat(box((5,3,2)),box((4.2,2.2,.2),(0,0,1.1)),*[cyl(.45,1.4,(x,0,1.5)) for x in (-1.4,0,1.4)])
M["mark_i"]=cat(cyl(2,4.5,axis="x"),cyl(.45,1.4,(0,0,2.1)),cyl(.45,1.4,(0,0,-2.1)),box((5.5,3.5,.3),(0,0,-2.2)))
# Mark III viewer proxy deliberately avoids arm-count semantics while that source contradiction remains gated.
M["mark_iii"]=cat(box((4.5,4.5,1),(0,0,-1.2)),box((4,4,1)),box((3.5,3.5,1),(0,0,1.2)),cyl(.5,4))
M["luke_family"]=cat(torus(3,.35),torus(2.2,.22),cyl(.35,2.2))
M["maglev_luke_iv"]=cat(cone(4.2,2.2,(0,0,-.8)),torus(4.5,.25,(0,0,.4)),torus(3.3,.18,(0,0,.8)),box((11,11,.3),(0,0,-2)))
M["embedded_bio_blocks"]=cat(*[box((1.2,1.6,.8),(x,y,0)) for x in (-1.5,0,1.5) for y in (-1,1)])
M["second_cycle"]=cat(cyl(1.5,.7),cyl(.15,3,(0,0,-1.7)),*[cone(.25,1.3,(1.1*math.cos(a),1.1*math.sin(a),.85)) for a in np.linspace(0,2*math.pi,6,endpoint=False)])
# SOURCE_DERIVED_GEOMETRY: WatchTower BREP-extract bounding groups, local CAD origin shifted for viewer.
def wt(x0,y0,z0,x1,y1,z1): return box((x1-x0,y1-y0,z1-z0),((x0+x1)/2-700,(y0+y1)/2-400,(z0+z1)/2))
M["watchtower"]=cat(
    wt(682.368435,388.22801,-4.9,704.695125,410.928449,13.3),
    wt(690.762816,397.709183,13.3,695.055237,402.07346,68.3),
    wt(687.796253,394.358546,68.3,698.461964,405.202802,76.62),
    wt(677.189889,393.771598,0,697.718664,442.644649,9.1),
    wt(681.214722,366.815892,0,728.529076,398.792178,9.1))
# InterSol proxy: program has 48 spaces; this grid is NOT the final room/site layout.
M["intersol"]=cat(*[box((5.2,4.2,2.6),(c*5.8-20.3,r*4.8-12,1.3)) for r in range(6) for c in range(8)])
# SOURCE_DERIVED_GEOMETRY: M1 Stage-0 massing from SEQLD Pilot Builds.FCStd extraction, metres.
M["m1_elevated_bypass"]=cat(
    box((1000,23.5,2),(0,11.75,0)),
    box((1000,23.5,2),(0,38.75,0)),
    box((1000,57,1.5),(0,24.999,-1.25)),
    box((1000,52,4.45),(0,25.25,-.025)))
# SOURCE_DERIVED_PARTIAL: source-bound application-twin facility forms; not a selected-site engineering model.
M["romer_spaceport"]=cat(box((40,75,22),(0,0,11)),box((32,32,6),(85,0,3)),box((18,18,18),(85,0,15)),box((240,4,1),(0,70,.5)))

classes={k:"INTERACTION_PROXY" for k in M}
classes.update({"watchtower":"SOURCE_DERIVED_GEOMETRY","m1_elevated_bypass":"SOURCE_DERIVED_GEOMETRY","romer_spaceport":"SOURCE_DERIVED_PARTIAL"})
manifest=[]
for key,m in M.items():
    p=OUT/f"{key}.obj"
    p.write_text(trimesh.exchange.obj.export_obj(m,include_normals=True,include_texture=False),encoding="utf-8")
    manifest.append({"twin_id":key,"file":str(p),"representation_class":classes[key],"units":"m","vertices":int(len(m.vertices)),"faces":int(len(m.faces)),"watertight":bool(m.is_watertight)})
(OUT.parent/"generated_mesh_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({"generated":len(manifest),"output":str(OUT)},indent=2))
