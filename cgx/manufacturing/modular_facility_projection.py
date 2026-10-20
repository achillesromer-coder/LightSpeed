"""Non-authoritative deterministic 2D viewer for modular CGX facility candidates.

Shows container outlines, component/reserved XY footprints and logical links.
Projected footprints can overlap in XY while disjoint in Z. Do NOT use as native
CAD, transport plan, clearance or service route drawing.
"""
from __future__ import annotations
import json
import math
from html import escape

def _e(x) -> str:
    return escape(str(x), quote=True)

def render_svg(plan: dict, *, scale: float=56.0) -> str:
    if not math.isfinite(scale) or not (8.0 <= scale <= 200.0):
        raise ValueError("scale must be finite 8..200")
    if plan.get("schema") != "CGX-MODULAR-FACILITY-PACKING-CANDIDATE/0.1":
        raise ValueError("wrong source schema")
    units=plan.get("units")
    if not isinstance(units,list) or not units:
        raise ValueError("units required")
    coords=[]
    for u in units:
        dim=u.get("internal_envelope_m")
        org=u.get("origin_m",[0,0,0])
        if not (isinstance(dim,list) and len(dim)==3 and isinstance(org,list) and len(org)==3):
            raise ValueError("missing geometry; refuse misleading representation")
        if any(isinstance(z,bool) or not isinstance(z,(int,float)) or not math.isfinite(z) for z in dim+org):
            raise ValueError("nonfinite geometry")
        if dim[0]<=0 or dim[1]<=0:
            raise ValueError("positive XY envelope required")
        coords.append((u,float(org[0]),float(org[1]),float(dim[0]),float(dim[1])))
    minx=min(x for _,x,_,_,_ in coords)
    miny=min(y for _,_,y,_,_ in coords)
    maxx=max(x+w for _,x,_,w,_ in coords)
    maxy=max(y+h for _,_,y,_,h in coords)
    pad=55.0
    width=(maxx-minx)*scale+2*pad
    height=(maxy-miny)*scale+2*pad+80
    if width>50000 or height>50000:
        raise ValueError("drawing bounds unreasonably large")
    out=[
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="{height:.1f}" viewBox="0 0 {width:.1f} {height:.1f}" role="img" aria-label="Non-authoritative CGX five-unit review plan">',
        '<title>CGX modular facility · source-linked review projection · NOT FOR CONSTRUCTION</title>',
        '<desc>XY footprints of synthetic/candidate containers, equipment and protected voids. Each shape preserves source identifier and Z extents. Utility links are conceptual, not measured routes.</desc>',
        '<rect width="100%" height="100%" fill="#f9fbff"/>',
        '<g id="L00-SHEET"><text x="22" y="30" font-size="15">CGX / UNI SPACE · REVIEW-ONLY SOURCE PROJECTION</text></g>',
        '<g id="L91-UNKNOWNS"><text x="22" y="48" font-size="11" fill="#9b2635">Geometry, masses, service routes and approvals not certified. XY footprints do not prove 3D fit.</text></g>',
        '<g id="L20-AUTH-GEOMETRY"></g>'
    ]
    px=lambda x:pad+(x-minx)*scale
    py=lambda y:pad+(y-miny)*scale
    for u,x,y,w,h in coords:
        state=u.get("geometry_evidence")
        if state not in {"SOURCE_VERIFIED","BOUNDED_ASSUMPTION","SYNTHETIC_TEST_ONLY","UNKNOWN"}:
            raise ValueError("unclassified geometry provenance")
        X,Y,W,H=px(x),py(y),w*scale,h*scale
        out.append(f'<g id="{_e(u["id"])}" data-cgx-unit="{_e(u["id"])}" data-evidence="{_e(state)}">')
        out.append(f'<rect x="{X:.2f}" y="{Y:.2f}" width="{W:.2f}" height="{H:.2f}" stroke="#25485d" stroke-width="2" fill="#e9f2f6"/>')
        for key,name,color in (("reserves","reserved","#f7dba2"),("placements","asset","#a6cce8")):
            for obj in u.get(key,[]):
                a=obj.get("box_m")
                if not isinstance(a,list) or len(a)!=6 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in a):
                    continue
                xx,yy,zz,dx,dy,dz=a
                objid=obj.get("id","?")
                out.append(f'<g data-cgx-role="{name}" data-cgx-object="{_e(objid)}" data-local-z-m="{zz:.5g}" data-depth-m="{dz:.5g}">')
                out.append(f'<rect x="{X+xx*scale:.2f}" y="{Y+yy*scale:.2f}" width="{dx*scale:.2f}" height="{dy*scale:.2f}" fill="{color}" stroke="#57717f" stroke-width="0.7" opacity="0.80"/>')
                out.append(f'<title>{_e(objid)}: {name}, z={zz:.3g}m depth={dz:.3g}m</title></g>')
        out.append(f'<text x="{X+5:.2f}" y="{Y+H-6:.2f}" font-size="10">{_e(u["id"])} — {_e(u.get("function","unassigned"))}</text></g>')
    out.append('<g id="L70-INTERFACES" fill="none" stroke="#bc563a" stroke-dasharray="5 4" stroke-width="1.8">')
    portmap={}
    for u,x,y,w,h in coords:
        for p in u.get("ports",[]):
            v=p.get("local_xyz_m")
            if isinstance(v,list) and len(v)==3 and all(isinstance(k,(int,float)) for k in v):
                portmap[f'{u["id"]}/{p["id"]}']=(px(x+v[0]),py(y+v[1]))
    for i,e in enumerate(plan.get("connections",[])):
        a=portmap.get(e.get("a"))
        b=portmap.get(e.get("b"))
        if a and b:
            out.append(f'<path data-cgx-link="{i}" d="M{a[0]:.2f},{a[1]:.2f} L{b[0]:.2f},{b[1]:.2f}"/>')
    out.append('</g>')
    out.append(f'<g id="L99-CLAIM-GATE"><text x="22" y="{height-17:.1f}" font-size="10" fill="#992536">R0 SOURCE REFERENCES / CANDIDATE VIEW. NATIVE CAD + SI MEASUREMENTS + QUALIFICATION REQUIRED.</text></g></svg>')
    return "\n".join(out)

if __name__=="__main__":
    import sys
    print(render_svg(json.load(sys.stdin)))
