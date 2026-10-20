"""Generate a fully offline Alexandria *reference index preview* from existing registries.

No network requests, mirrors, third-party binaries, personal data, private CGX
catalogues, paid APIs or runtime engine activation. Not a released public kit.
"""
from __future__ import annotations
import argparse
import hashlib
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import ipaddress
import json

ROOT=Path(__file__).resolve().parents[2]

def _source(name):
    p=ROOT/"cgx"/"review"/name
    raw=p.read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def safe_external_reference(url):
    """A source URL must not introduce an embedded secret, local address or JS URI."""
    if not isinstance(url,str) or len(url)>2048:return None
    try:u=urlsplit(url)
    except ValueError:return None
    if u.scheme!="https" or not u.hostname or u.username or u.password or u.port or u.query or u.fragment:
        return None
    host=u.hostname.lower()
    if host=="localhost" or host.endswith((".localhost",".local",".internal")):
        return None
    try:
        ip=ipaddress.ip_address(host)
        if not ip.is_global:return None
    except ValueError:
        if "." not in host or host.startswith("."):return None
    return url

def _e(text):
    return escape(str(text),quote=True)

def build_offline_reference_html() -> str:
    curated,curated_hash=_source("alexandria_curated_upstream_tools_20261020.json")
    legacy,legacy_hash=_source("alexandria_external_reference_intake_20261020.json")
    official,official_hash=_source("alexandria_official_reference_roots_20261020.json")
    learning,learning_hash=_source("alexandria_foundation_learning_modules_v0_1.json")
    if any(r.get("redistribution_authorised") is not False for r in curated["repositories"]):
        raise ValueError("curated source unexpectedly authorised for redistribution")
    rows=[]
    for repo in curated["repositories"]:
        url=safe_external_reference(repo["url"])
        links=('<a target="_blank" rel="noopener noreferrer" href="'+_e(url)+'">Source ↗</a>') if url else "Unavailable"
        name=_e(repo["repository"])
        cat=_e(repo["domain"])
        license_value=_e(repo["github_licence_metadata"])
        name_cells=f'<td><strong>{name}</strong><small>{_e(repo["capability_candidate"])}</small></td><td>{cat}</td><td>{license_value} <small>Metadata only; review required</small></td><td>{links}</td>'
        rows.append(f'<tr data-entry="curated" data-search="{_e((repo["repository"]+" "+repo["domain"]+" "+repo["capability_candidate"]).lower())}">{name_cells}</tr>')
    for group in legacy["groups"]:
        category=group["origin"]["name"]
        for item in group["records"]:
            links=[]
            for url in item.get("sources",[])[:4]:
                safe=safe_external_reference(url)
                if safe:links.append('<a target="_blank" rel="noopener noreferrer" href="'+_e(safe)+'">Source ↗</a>')
            title=_e(item.get("title") or "Untitled source")
            row=f'<td><strong>{title}</strong><small>Line {_e(item.get("line","?"))} · {_e(category)}</small></td><td>{_e(item.get("category") or category)}</td><td>Unverified upstream rights</td><td>{" ".join(links) if links else "Review source"}</td>'
            rows.append(f'<tr data-entry="{_e(category)}" data-search="{_e((str(item.get("title",""))+" "+str(item.get("category",""))+" "+category).lower())}">{row}</tr>')
    for ref in official["official_references"]:
        if ref.get("public_kit_inclusion")!="REFERENCE_ONLY_HOLD":
            raise ValueError("official source unexpectedly promoted into offline asset")
        url=safe_external_reference(ref["url"])
        links=('<a target="_blank" rel="noopener noreferrer" href="'+_e(url)+'">Documentation ↗</a>') if url else "Review official URL"
        row='<td><strong>'+_e(ref["name"])+'</strong><small>'+_e(ref["kind"])+'</small></td><td>'+_e(ref["domain"])+'</td><td>Rights review required<small>'+_e(ref["limitations"])+'</small></td><td>'+links+'</td>'
        rows.append('<tr data-entry="official" data-search="'+_e((ref["name"]+" "+ref["domain"]+" "+ref["kind"]).lower())+'">'+row+'</tr>')
    tracks=[]
    for tr in curated["learning_tracks"]:
        exercises=[m for m in learning["modules"] if m.get("track")==tr["id"]]
        if len(exercises)!=3 or any(m.get("module_state")!="UNEXECUTED_SOURCE_LINKED_EDUCATION" for m in exercises):
            raise ValueError("each training track requires three unexecuted source-linked exercises")
        detail=[]
        for lesson in exercises:
            detail.append('<li><strong>'+_e(lesson["title"])+'</strong> — '+
                          _e(lesson["instruction"])+
                          '<small>Expected: '+_e(lesson["expected_artifact"])+
                          ' · Hold: '+_e(lesson["qualification_hold"])+
                          ' · Sources: '+_e(", ".join(lesson["repository_sources"]))+'</small></li>')
        tracks.append('<li><strong>'+_e(tr["id"].replace("-"," ").title())+'</strong> — '+
                      _e("; ".join(tr["outputs"]))+
                      '<small>Qualification: '+_e(tr["hold"])+'</small><ol>'+"".join(detail)+'</ol></li>')
    entries=len(curated["repositories"])+sum(len(g["records"]) for g in legacy["groups"])+len(official["official_references"])
    if entries!=len(rows):raise ValueError("entry mismatch")
    css="""
:root{color-scheme:light dark;font:15px system-ui,-apple-system,Segoe UI,sans-serif}
body{margin:0;background:#0a1827;color:#e8f1f9;line-height:1.5}
main{margin:0 auto;max-width:1180px;padding:24px 18px 80px}
h1{font-size:clamp(1.7rem,4vw,2.8rem);margin:0 0 6px}h2{font-size:1.15rem;margin-top:25px}
p{color:#c8d6e2;max-width:900px}.eyebrow{color:#89c3da;letter-spacing:.09em}
.panel{background:#10263b;border:1px solid #31506b;border-radius:14px;padding:16px;margin:14px 0}
label{display:inline-flex;flex-direction:column;gap:5px;min-width:min(100%,300px)}
input,select{font:inherit;color:#fff;background:#0e263a;border:1px solid #63849d;border-radius:8px;padding:11px}
.controls{display:flex;gap:12px;flex-wrap:wrap}
table{width:100%;border-collapse:collapse;font-size:0.91rem}th{text-align:left;position:sticky;top:0;background:#17334a;z-index:1}
td,th{padding:10px;border-bottom:1px solid #36516b;vertical-align:top}
td small,li small{display:block;color:#abbecf;font-size:.79rem;margin-top:4px}
a{color:#9cdaff;margin-right:8px}caption{text-align:left;padding:10px}
.scroller{max-height:640px;overflow:auto;border:1px solid #36516b;border-radius:9px}
.tag{border:1px solid #7b94a5;padding:3px 9px;border-radius:99px;display:inline-block;color:#b4ccda}
code{overflow-wrap:anywhere;color:#b0dcff}
@media(max-width:720px){main{padding:15px 8px 40px}td,th{padding:7px 4px;font-size:0.78rem}}
@media print{body{background:white;color:black}th{position:static}a{color:black}.panel{border:1px solid black}}
"""
    js="""
const q=document.getElementById('search'),filter=document.getElementById('kind'),counter=document.getElementById('counter');
const rows=[...document.querySelectorAll('#records tr[data-entry]')];
function refresh(){
 const term=q.value.trim().toLowerCase();let found=0;
 for(const row of rows){
  const ok=(filter.value==='all'||row.dataset.entry===filter.value)&&row.dataset.search.includes(term);
  row.hidden=!ok;if(ok)found++;
 }
 counter.textContent=found+' of '+rows.length+' references shown';
}
q.addEventListener('input',refresh);filter.addEventListener('change',refresh);refresh();
"""
    csp="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'"
    return (
        '<!doctype html><html lang="en-AU"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="'+_e(csp)+'">'
        '<title>Alexandria — Offline reference library preview</title>'
        '<style>'+css+'</style></head><body><main>'
        '<p class="eyebrow">UNISPACE / ALEXANDRIA · PUBLIC REFERENCE CANDIDATE</p>'
        '<h1>Open knowledge, source by source</h1>'
        '<p>Offline searchable list of external projects and learning routes. Names and links only: no binaries, models, game assets, account access, private files or remote queries are bundled. A source link is not redistribution permission.</p>'
        '<div class="panel"><span class="tag">Review-only</span> <strong>'+str(entries)+' source references</strong>'
        '<p>Curated source SHA-256: <code>'+curated_hash+'</code></p>'
        '<p>Original games/engines source SHA-256: <code>'+legacy_hash+'</code></p>'
        '<p>Official references SHA-256: <code>'+official_hash+'</code></p>'
        '<p>Learning modules SHA-256: <code>'+learning_hash+'</code></p>'
        '<p>No internet is needed to browse this file; opening any external source link does require a connection.</p></div>'
        '<h2>Learning pathways</h2><div class="panel"><ol>'+"".join(tracks)+'</ol></div>'
        '<h2>Library index</h2><div class="controls panel">'
        '<label>Search references<input id="search" type="search" placeholder="engine, CAD, NASA, ecology…"></label>'
        '<label>Source<select id="kind"><option value="all">All sources</option>'
        '<option value="curated">Cross-domain curated tools</option>'
        '<option value="official">Official science and standards</option>'
        '<option value="bobeff/open-source-games">Game index</option>'
        '<option value="bobeff/open-source-engines">Engine index</option></select></label>'
        '<span id="counter" role="status" aria-live="polite">'+str(entries)+' references shown</span></div>'
        '<div class="scroller"><table id="records"><thead><tr>'
        '<th scope="col">Project</th><th scope="col">Category</th>'
        '<th scope="col">Rights / status</th><th scope="col">Upstream reference</th>'
        '</tr></thead><tbody>'+"".join(rows)+'</tbody></table></div>'
        '<p>No licence file was independently reviewed in this package. The linked projects, model weights, fonts, game data, scientific records and archives have independent reuse rules. Internal engineering review assets are excluded. This page is not an authorised public release of UniSpace.</p>'
        '<script>'+js+'</script></main></body></html>'
    )
if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--output",help="output HTML path; if omitted, write to stdout")
    opt=a.parse_args()
    value=build_offline_reference_html()
    if opt.output:
        Path(opt.output).write_text(value,encoding="utf-8")
        print("Offline candidate written to",opt.output)
    else:
        print(value)
