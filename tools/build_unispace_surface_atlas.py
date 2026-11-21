"""Build a private surface review atlas from a verified carrier and Git review meshes."""
import argparse
import base64
from collections import defaultdict
import hashlib
from html import escape
import io
import json
from pathlib import Path
import zipfile

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
PIN = "d4c17e1d95d18834ab10be2b9ab7904605ef4b3b0223b1405763980bcaeeaf32"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def records(carrier):
    if sha(carrier.read_bytes()) != PIN:
        raise ValueError("Review carrier revision changed")
    with zipfile.ZipFile(carrier) as z:
        roles = defaultdict(list)
        for row in json.loads(z.read("raphael/index.json"))["roles"]:
            roles[row["mesh"]].append(row)
        for member, slots in roles.items():
            raw = z.read(member)
            mesh = json.loads(raw)
            yield member, slots[0]["name"], raw, mesh["v"], mesh["f"], {
                "roles": [r["id"] for r in slots], "addresses": [r["address"] for r in slots],
                "rights": mesh["rights"], "source": mesh["source"]}
    for path in sorted((ROOT / "apps/lightspeed-go/public/review/mesh").glob("*.json")):
        raw = path.read_bytes()
        mesh = json.loads(raw)
        original = (ROOT / mesh["source"]).resolve()
        if not original.is_relative_to(ROOT) or sha(original.read_bytes()) != mesh["source_sha256"]:
            raise ValueError(f"Original OBJ source mismatch for {path.name}")
        yield path.relative_to(ROOT).as_posix(), mesh["id"], raw, mesh["vertices"], mesh["faces"], {
            "source": mesh["source"], "source_sha256": mesh["source_sha256"], "rights": mesh["state"]}


def inspect(vertices, faces):
    v = np.asarray(vertices, dtype=float)
    if v.ndim != 2 or v.shape[1] != 3 or not np.isfinite(v).all():
        raise ValueError("Invalid vertices")
    edges = defaultdict(list)
    neighbors = [set() for _ in v]
    degenerate = 0
    for face in faces:
        if len(face) < 3 or any(type(i) is not int or not 0 <= i < len(v) for i in face):
            raise ValueError("Invalid face index")
        polygon = v[face] - v[face[0]]
        area = np.cross(polygon, np.roll(polygon, -1, axis=0)).sum(axis=0)
        degenerate += int(len(set(face)) != len(face) or np.linalg.norm(area) <= 1e-12 * np.ptp(v, axis=0).max()**2)
        for a,b in zip(face, face[1:]+face[:1]):
            edges[min(a,b), max(a,b)].append(a < b)
            neighbors[a].add(b)
            neighbors[b].add(a)
    pending = set(range(len(v)))
    components = 0
    while pending:
        stack = [pending.pop()]
        components += 1
        while stack:
            new = neighbors[stack.pop()] & pending
            pending.difference_update(new)
            stack.extend(new)
    return dict(vertices=len(v), faces=len(faces), edges=len(edges), components=components,
                boundary=sum(len(s)==1 for s in edges.values()), overfull=sum(len(s)>2 for s in edges.values()),
                winding=sum(len(s)==2 and s[0]==s[1] for s in edges.values()),
                degenerate_or_cancelling=degenerate, euler=len(v)-len(edges)+len(faces))


def render(vertices, faces, direction):
    v = np.asarray(vertices, dtype=float)
    front = np.asarray(direction, dtype=float)
    front /= np.linalg.norm(front)
    right = np.cross([0,0,1], front)
    right /= np.linalg.norm(right)
    up = np.cross(front,right)
    xyz = v @ np.stack([right,-up,front],axis=1)
    xy = xyz[:,:2]
    xy = (xy-(xy.max(axis=0)+xy.min(axis=0))/2)*96/max(1e-12,np.ptp(xy,axis=0).max()) + [60,58]
    im = Image.new("RGB",(120,116),"#f4f7f8")
    draw = ImageDraw.Draw(im)
    for face in sorted(faces,key=lambda f:xyz[f,2].mean()):
        poly = xyz[face]
        normal = np.cross(poly[1]-poly[0],poly[2]-poly[0])
        shade = int(85*abs(normal[2])/max(np.linalg.norm(normal),1e-15))
        draw.polygon([tuple(x) for x in xy[face]],fill=(66+shade,104+shade,116+shade),outline="#223741")
    return im


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("carrier",type=Path)
    ap.add_argument("atlas",type=Path)
    ap.add_argument("--contact-sheets",type=Path)
    args = ap.parse_args()
    rows, cards = [], []
    for member,name,raw,v,f,meta in records(args.carrier):
        report = inspect(v,f)
        geom = sha(json.dumps([v,f],separators=(",",":")).encode())
        row = dict(name=name,member=member,member_sha256=sha(raw),geometry_sha256=geom,**meta,**report)
        rows.append(row)
        card = Image.new("RGB",(240,142),"white")
        card.paste(render(v,f,(1,2,1)),(0,20))
        card.paste(render(v,f,(-2,1,-1)),(120,20))
        ImageDraw.Draw(card).text((4,3),f"{len(rows):03}  {name}"[:38],fill="black")
        cards.append(card)
    sections=[]
    for start in range(0,len(rows),20):
        subset=cards[start:start+20]
        sheet=Image.new("RGB",(960,142*((len(subset)+3)//4)),"white")
        for i,card in enumerate(subset):
            sheet.paste(card,((i%4)*240,(i//4)*142))
        if args.contact_sheets:
            args.contact_sheets.mkdir(exist_ok=True,parents=True)
            sheet.save(args.contact_sheets/f"{start:03}.png")
        buf=io.BytesIO()
        sheet.save(buf,format="PNG")
        img=base64.b64encode(buf.getvalue()).decode()
        lines=[]
        for i,r in enumerate(rows[start:start+20],start+1):
            desc=", ".join(f"{k} {r[k]}" for k in ("vertices","edges","faces","components","boundary","overfull","winding","degenerate_or_cancelling","euler"))
            lines.append(f"<details><summary>{i:03} {escape(r['name'])} · {desc}</summary><pre>{escape(json.dumps(r,indent=2,ensure_ascii=False))}</pre></details>")
        sections.append(f'<img alt="Two orthographic surface views per mesh, records {start+1} through {start+len(subset)}" src="data:image/png;base64,{img}">'+"".join(lines))
    html="""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>UniSpace surface atlas</title><style>body{max-width:1000px;margin:2rem auto;padding:0 1rem;font:16px/1.5 system-ui;color:#18343b}img{width:100%;margin-top:2rem}details{border-bottom:1px solid #ddd;padding:.4rem}summary{cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>UniSpace surface atlas</h1><p>Private pre-mint review. Each mesh has two depth-sorted polygon projections. Expand its record for source identity, rights statement and topology. Counts use the supplied face loops and vertex indices. Boundary counts edges used once, overfull counts edges used more than twice, and winding counts paired edges traversed in the same direction. Self-intersections, material thickness and physical validity require separate checks.</p>"""
    flagged = [f"{i:03} {escape(r['name'])}" for i,r in enumerate(rows,1) if r["winding"]]
    holds = "<details><summary>Review inconsistent face traversal (" + str(len(flagged)) + ")</summary><ul>" + "".join("<li>"+name+"</li>" for name in flagged) + "</ul></details>"
    args.atlas.write_text(html+holds+"".join(sections),encoding="utf-8")
    print("records",len(rows),"distinct geometry streams",len({r["geometry_sha256"] for r in rows}))
    for k in ("boundary","overfull","winding","degenerate_or_cancelling"):
        print(k,sum(r[k]>0 for r in rows))
    print("multiple components",sum(r["components"]>1 for r in rows))
    print("all four edge/area checks clear",sum(not any(r[k] for k in ("boundary","overfull","winding","degenerate_or_cancelling")) for r in rows))


if __name__=="__main__":
    main()
