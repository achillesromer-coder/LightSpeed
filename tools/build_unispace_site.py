"""Build the offline S91 starter kit and a relative-path static Römer site."""
import argparse
from collections import Counter
import hashlib
from html import escape
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

from verify_unispace_product import verify

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "UniSpace"
PUBLIC = ROOT / "apps/lightspeed-go/public"
KIT = ("FileSpace.html", "CGX.cgx", "index.html", "unispace.css", "unispace.js", "filespace.js", "product.json")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path, value):
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False)+"\n").encode())

def render_family_pages(site):
    families=json.loads((site/"assets/families.json").read_bytes())
    folder=site/"families"
    folder.mkdir(exist_ok=True)
    links=[]
    for family in families:
        name=family["selector"]
        if not re.fullmatch(r"[a-z0-9-]+",name): raise ValueError("invalid selector slug")
        routes="".join(f"<tr><td><code>@{name} /{escape(call)}</code></td><td>{escape(route)}</td></tr>" for call,route in family["shortcalls"].items())
        page=f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{name} · UniSpace</title><link rel="stylesheet" href="../unispace.css"><header><a class="brand" href="../index.html">UniSpace</a><a href="../library.html">Review library</a></header><main><section><p class="edition">Selector profile</p><h1>{name}</h1><p>Registered toolkits: {escape(", ".join(family["toolkits"]))}.</p><h2>Shortcalls</h2><table><thead><tr><th>Call</th><th>Registered route</th></tr></thead><tbody>{routes}</tbody></table><p>This page describes routes. Execution depends on the installed host, connected tools and current permissions.</p><a href="../FileSpace.html">Open the shared FileSpace tutorial</a></section></main></html>"""
        (folder/(name+".html")).write_bytes(page.encode())
        links.append(f'<li><a href="families/{name}.html">{name}</a></li>')
    page=site/"library.html"
    markup=page.read_text(encoding="utf-8")
    start=markup.index('<ul>',markup.index('<h2>Selector toolkits</h2>'))
    end=markup.index('</ul>',start)+5
    page.write_bytes((markup[:start]+'<ul>'+''.join(links)+'</ul>'+markup[end:]).encode())

def catalogue(site):
    assets = site / "assets"
    assets.mkdir()
    rows = []
    def include(path):
        relative = path.relative_to(PUBLIC)
        target = assets / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        url = target.relative_to(site).as_posix()
        rows.append({"url":url, "source":path.relative_to(ROOT).as_posix(), "sha256":digest(target), "bytes":target.stat().st_size})
        return url

    atlas = PUBLIC / "data/component_geometry_atlas_public_review.json"
    domains = Counter(r["Domain"] for r in json.loads(atlas.read_bytes())["records"])
    atlas_url = include(atlas)
    objects_file = PUBLIC / "data/cgx_object_review_catalogue.json"
    objects_url = include(objects_file)
    type_url = include(PUBLIC / "data/type1_catalogue_projection.json")
    objects = json.loads(objects_file.read_bytes())
    figures = []
    added = set()
    for key in ("micro_review_objects", "macro_review_objects", "bridge_review_objects"):
        for item in objects[key]:
            ref = item.get("render", "")
            if not ref.startswith("/review/renders/") or Path(ref).suffix != ".svg":
                continue
            render = (PUBLIC / ref.lstrip("/")).resolve(strict=True)
            if render.parent != (PUBLIC / "review/renders").resolve():
                raise ValueError("render outside the public catalogue")
            if render in added: continue
            added.add(render)
            url = include(render)
            figures.append(f'<figure><a href="{escape(url)}"><img loading="lazy" width="384" height="216" src="{escape(url)}" alt="{escape(item["label"])}"></a><figcaption>{escape(item["label"])}</figcaption><small>{escape(item["geometry_state"])}</small></figure>')
    selectors = json.loads((ROOT/"plugins/source/selector_shortcalls.json").read_bytes())
    family_rows = [{"selector":name, "toolkits":s["toolkits"], "shortcalls":s["shortcalls"]}
                   for name,s in selectors["selectors"].items()]
    write_json(assets/"families.json", family_rows)
    write_json(assets/"catalogue.json", {"scope":"Supplemental public-source review assets", "source_files":rows,
        "selector_index":{"url":"assets/families.json","sha256":digest(assets/"families.json"),"source":"plugins/source/selector_shortcalls.json"},
        "domains":domains,"physical_acceptance":False})
    family_list = "".join(f'<li><b>{escape(r["selector"])}</b> · {escape(", ".join(r["toolkits"]))}</li>' for r in family_rows)
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Review library · UniSpace</title><link rel="stylesheet" href="unispace.css"><header><a class="brand" href="index.html">UniSpace</a><a href="FileSpace.html">FileSpace tutorial</a></header><main><section><p class="edition">Römer / website library</p><h1>Scientific review sets</h1><p>Explore {sum(domains.values())} component archetypes across {len(domains)} domains. These supplemental datasets and renderings carry their source evidence states.</p><p><a href="{atlas_url}">Component atlas JSON</a> · <a href="{objects_url}">Object catalogue</a> · <a href="{type_url}">Type I catalogue</a> · <a href="assets/catalogue.json">Asset checksums</a></p><div class="gallery">{''.join(figures)}</div></section><section><h2>Selector toolkits</h2><ul>{family_list}</ul><p><a href="assets/families.json">Download the selector and shortcall index</a></p></section></main></html>"""
    (site/"library.html").write_bytes(html.encode())
    return len(figures),len(family_rows)

def build(destination, raphael_source=None):
    receipt=verify(PRODUCT)
    destination=destination.resolve()
    if destination.exists(): raise ValueError("choose a new output directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        site=Path(tmp)/"site"
        site.mkdir()
        for name in KIT: shutil.copyfile(PRODUCT/name,site/name)
        renders,families=catalogue(site)
        # Use the original writer only from the independently pinned release.
        if receipt["sha256"]!="1138da5af4e1c66eb60120dd050e2037fc8d7799a9ccebb01ad48089b234785f":
            raise ValueError("review the new writer before packaging")
        writer=Path(tmp)/"writer"
        writer.mkdir()
        with zipfile.ZipFile(site/"CGX.cgx") as original:
            for module in ("cgx_kernel","cgx_security","cgx_adapters","cgx_encryption"):
                (writer/(module+".py")).write_bytes(original.read("runtime/python/"+module+".py"))
        library=Path(tmp)/"review-library"
        shutil.copytree(site/"assets",library/"assets")
        if raphael_source is not None:
            from raphael_review_set import populate
            populate(library,raphael_source)
        # Preserve the portable tutorial in the supplemental CGX filespace too.
        for name in ("FileSpace.html","filespace.js","unispace.css"):
            shutil.copyfile(site/name,library/name)
        command="""import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import cgx_kernel as kernel
root=Path(sys.argv[2])
kernel.create_empty(root,"UniSpace scientific review library")
result=kernel.verify(root)
if not result['ok']: raise ValueError(result)
kernel.write_carrier(root,Path(sys.argv[3]))
"""
        companion=site/"ReviewLibrary.cgx"
        subprocess.run([sys.executable,"-I","-B","-c",command,str(writer),str(library),str(companion)],check=True,timeout=120)
        with zipfile.ZipFile(companion) as archive:
            manifest=json.loads(archive.read("cgx/manifest.json"))
            for member in manifest["files"]:
                raw=archive.read(member["path"])
                if len(raw)!=member["size_bytes"] or hashlib.sha256(raw).hexdigest()!=member["sha256"]:
                    raise ValueError("companion member verification failed")
        html=(site/"FileSpace.html").read_text(encoding="utf-8")
        html=html.replace('<main>',f'<main data-library-size="{companion.stat().st_size}" data-library-sha="{digest(companion)}">')
        (site/"FileSpace.html").write_bytes(html.encode())
        # The offline landing page only links to included assets.
        with zipfile.ZipFile(site/"UniSpace.zip","w") as kit:
            for name in KIT:
                info=zipfile.ZipInfo(name)
                kit.writestr(info,(site/name).read_bytes(),compress_type=zipfile.ZIP_STORED if name=="CGX.cgx" else zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(site/"UniSpace.zip") as kit:
            if kit.testzip() or hashlib.sha256(kit.read("CGX.cgx")).hexdigest()!=receipt["sha256"]:
                raise ValueError("starter kit failed verification")
        library_page=(site/"library.html").read_text(encoding="utf-8")
        (site/"library.html").write_bytes(library_page.replace('<h1>Scientific review sets</h1>', '<h1>Scientific review sets</h1><p><a href="ReviewLibrary.cgx" download>Download the optional review library (.cgx)</a>. Open it with the FileSpace tutorial supplied in this edition.</p>').encode())
        render_family_pages(site)
        page=(site/"index.html").read_text(encoding="utf-8")
        page=page.replace("<!-- kit-download -->",'<p><a class="button" href="UniSpace.zip" download>Download product + offline tutorial ↓</a></p><p><a href="library.html">Explore the scientific review library →</a></p>')
        (site/"index.html").write_bytes(page.encode())
        write_json(site/"hosting.json",{"intended_origin":"https://romer.industries","proposed_base_path":"/unispace/",
            "published":False,"scope":"private Raphael review" if raphael_source else "hosting candidate",
            "entry":"index.html","starter_kit":"UniSpace.zip","carrier":"CGX.cgx",
            "carrier_sha256":receipt["sha256"],"kit_sha256":digest(site/"UniSpace.zip"),
            "tutorial":"FileSpace.html","library":"library.html","catalogue":"assets/catalogue.json",
            "companion":{"url":"ReviewLibrary.cgx","sha256":digest(companion),"bytes":companion.stat().st_size,"state_id":manifest["state_id"],"object_id":manifest["object_id"],"release":"local review candidate"},
            "renders":renders,"selectors":families,"server_requirements":"Static HTTPS; serve .cgx and .zip as downloadable binary files."})
        site.rename(destination)
    print(destination)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination",type=Path)
    parser.add_argument("--private-raphael-source",type=Path,help="Embed the hash-pinned local research set for private review.")
    args=parser.parse_args()
    build(args.destination,args.private_raphael_source)
