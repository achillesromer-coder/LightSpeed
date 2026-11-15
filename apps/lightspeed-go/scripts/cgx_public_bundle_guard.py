"""CGX isolated public release bundle — deny-by-default source packaging.

This is a source-only package planner. It copies only reviewed static /cgx
demonstration files into a fresh separate output directory. It NEVER copies the
operator's other Vite public/ assets, grants rights, deploys, signs or authenticates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
from html.parser import HTMLParser
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "apps/lightspeed-go/public/cgx"

# Exact paths, NOT a wildcard under apps/lightspeed-go/public/.
APPROVED = frozenset({
    "index.html","fs/index.html","ds/index.html","ps/index.html",
    "doom/index.html","romer/index.html","eco/index.html",
    "assets/core.js","assets/viewer.js","assets/viewer.css",
    "assets/domain-overviews.js","assets/domain-viewer.js",
})
REQUIRED_CONTEXT = (
    "PUBLIC_SAFE_SYNTHETIC",
    "unispace-cgx-public-demonstration/1",
)
BLOCKED = {
    "operator bridge": re.compile(r"desktopBridge|ownerAuth|lightspeed_runtime|ls_go_job_consumer",re.I),
    "internal review catalogue": re.compile(
        r"cgx_object_review_catalogue|component_geometry_atlas_public_review|cgx_internal_review_projection",re.I),
    "private assets path": re.compile(r"(?<![a-z])/review/(?:mesh|renders)|/data/(?:cgx|component_geometry)",re.I),
    "native owner APIs": re.compile(r"/api/(?:v1|owner)|https?://(?:127\.0\.0\.1|localhost)(?::\d+)?/",re.I),
    "credential syntax": re.compile(r"(?:sk-proj-|ghp_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)",re.I),
    # #158: a scripted image/iframe/worker can request same-origin private
    # bytes even when fetch(), WebSocket and connect-src are denied.
    # This bounded static sink guard is defence in depth, NOT an ACL test.
    "scripted passive resource loads": re.compile(
        r"""\bnew\s+(?:Image|Audio|Worker|SharedWorker)\s*\("""
        r"""|\b(?:document|window\.document)\s*\.\s*createElement\s*\(\s*['"](?:img|iframe|script|link|audio|video|source|object|embed)['"]"""
        r"""|\.\s*(?:src|srcset|poster)\s*=(?!=)"""
        r"""|\.\s*setAttribute\s*\(\s*['"](?:src|srcset|poster|data)['"]"""
        r"""|\[\s*['"](?:src|srcset|poster|data)['"]\s*\]\s*=(?!=)""", re.I),
    # #158: CSP connect-src does not prevent top-level navigation or window.open.
    # The reviewed public JS reads location.pathname but has no scripted navigation.
    "scripted navigation escape": re.compile(
        r"""\b(?:(?:window|document|self|top|parent|globalThis)\s*\.\s*)?location\s*"""
        r"""(?:\.\s*(?:assign|replace)\s*\(|\.\s*href\s*=(?!=)|=(?!=)|\[)"""
        r"""|\b(?:window|globalThis|self|top|parent)\s*\.\s*open\s*\("""
        r"""|\b(?:window|document|globalThis|self|top|parent)\s*\[\s*['"](?:location|open)['"]\s*\]""", re.I),

    # #158: these DOM/CSSOM APIs can manufacture same-origin passive resource
    # requests from strings without using fetch(), createElement(), or src=.
    # The reviewed demo uses fixed innerHTML layouts, so that sink is NOT
    # covered here; this is a bounded negative, not an authenticated ACL.
    "unreviewed DOM or stylesheet injection": re.compile(
        r"\b(?:document\s*\.\s*(?:write|writeln)\s*\("
        r"|(?:insertAdjacentHTML|createContextualFragment|parseFromString|insertRule|replaceSync|setHTMLUnsafe|parseHTMLUnsafe)\s*\("
        r"|\.\s*outerHTML\s*=(?!=))", re.I),
    # Static demonstration code has no reason to initiate network reads or dynamic code loads.
    # CSP remains mandatory, but is not a substitute for rejecting source-level bypasses.
    # #158: bracket-property API invocation bypasses bare fetch()/sendBeacon() scans.
    # This is a bounded static deny rule, not a replacement for runtime ACL/CSP.
    "computed network API access": re.compile(
        r"""\[\s*[\x27\x22](?:fetch|XMLHttpRequest|WebSocket|EventSource|sendBeacon|serviceWorker|importScripts|eval|Function)[\x27\x22]\s*\]""",re.I),
    "active network or dynamic code API": re.compile(
        r"\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\b|EventSource\b|sendBeacon\s*\(|"
        r"serviceWorker\b|importScripts\s*\(|import\s*\(|eval\s*\(|Function\s*\()",re.I),
}
MAX_FILE_BYTES=250_000
MAX_BYTES=1_000_000

class BundleHold(ValueError):
    pass

def _reject_split_computed_transport(text: str, relative: str) -> None:
    """Deny literal-string assembly of browser transport property names (#158).

    This is a bounded source-level negative, not a JS parser or runtime ACL.
    """
    for match in re.finditer(
        r"""\[\s*(?:['"][^'"\n]{1,40}['"]\s*\+\s*)+['"][^'"\n]{1,40}['"]\s*\]""",
        text,
    ):
        fragments = re.findall(r"""['"]([^'"\n]*)['"]""", match.group(0))
        joined = "".join(fragments).casefold()
        if joined in {
            "fetch", "xmlhttprequest", "websocket", "eventsource",
            "sendbeacon", "serviceworker", "importscripts", "eval", "function",
        }:
            raise BundleHold(f"computed split network API access: {relative}")
        # #158: CSP connect-src cannot stop top-level navigation. Literal
        # window["location"] and window["open"] are rejected above; these
        # split-string spellings must also fail closed before static packaging.
        if joined in {"location", "open", "assign", "replace", "href"}:
            raise BundleHold(f"computed split navigation property access: {relative}")

def _validate_static_reference(relative:str,uri:str) -> None:
    # A parent-relative link is permitted only when the resolved target
    # still names one of the exact CGX public package assets.
    addr=uri.split("#",1)[0].split("?",1)[0]
    if addr.startswith("/cgx/"):
        target=posixpath.normpath(addr.removeprefix("/cgx/"))
    elif addr.startswith("/") or "://" in addr or addr.startswith("//"):
        raise BundleHold(f"reference leaves public site boundary: {relative}")
    else:
        target=posixpath.normpath(posixpath.join(posixpath.dirname(relative),addr))
    # Static directory routes resolve to the already-allowlisted index.html.
    # Never generalise to arbitrary files or external navigation.
    if target == ".":
        target = "index.html"
    elif target + "/index.html" in APPROVED:
        target += "/index.html"
    if target not in APPROVED:
        raise BundleHold(f"reference not in exact CGX public allowlist: {relative} => {target}")

class _PublicHtmlReferences(HTMLParser):
    """Parse HTML attributes rather than rely on quote-sensitive regex scans."""
    RESOURCE_TAGS = frozenset({
        "script", "link", "img", "source", "video", "audio",
        "track", "iframe", "embed", "object", "a", "area", "input",
    })
    RESOURCE_ATTRS = frozenset({"src", "href", "poster", "data"})

    def __init__(self, relative: str):
        super().__init__(convert_charrefs=True)
        self.relative = relative

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # HTMLParser retains duplicate attributes while dict() discards them.
        # Browsers may honour the first occurrence; a later allowlisted src/href
        # must never conceal an earlier private or remote resource (#158).
        keys = [key for key, _ in attrs]
        if len(keys) != len(set(keys)):
            raise BundleHold(f"duplicate HTML attributes: {self.relative}")
        values = dict(attrs)
        # Reviewed shells load only exact allowlisted external JS modules.
        # Inline scripts evade static resource-attribute checks and may execute
        # during offline preview even where the intended host CSP blocks them.
        if tag == "script" and not values.get("src"):
            raise BundleHold(f"inline or empty-source script not reviewed: {self.relative}")
        # These HTML surfaces can initiate passive loads or execute scripts
        # outside the ordinary src/href checks; none belong to reviewed shells.
        if tag in {"svg", "math", "style"}:
            raise BundleHold(f"unreviewed embedded markup/style: {self.relative}")
        if any(key == "style" or key.startswith("on") for key in values):
            raise BundleHold(f"unreviewed inline style or event handler: {self.relative}")
        if tag in {"base", "form"}:
            raise BundleHold(f"unreviewed HTML navigation or form: {self.relative}")
        if tag == "meta" and (values.get("http-equiv") or "").casefold() == "refresh":
            raise BundleHold(f"unreviewed HTML meta refresh: {self.relative}")
        if any(key in values for key in ("srcdoc", "srcset", "ping")):
            raise BundleHold(f"unreviewed embedded, responsive or beacon attribute: {self.relative}")
        # Legacy HTML background attributes can initiate resource loads without src/href.
        if "background" in values:
            raise BundleHold(f"unreviewed legacy HTML background resource: {self.relative}")
        if tag in self.RESOURCE_TAGS:
            for key in self.RESOURCE_ATTRS.intersection(values):
                uri = values[key]
                if uri is None:
                    raise BundleHold(f"empty HTML resource attribute: {self.relative}")
                if tag in {"a", "area"} and key == "href" and uri.startswith("#"):
                    continue  # in-document fragment: no navigation outside the static root
                _validate_static_reference(self.relative, uri)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def _source_files(root:Path) -> dict[str,Path]:
    if not root.is_dir() or root.is_symlink():
        raise BundleHold("expected ordinary public/cgx source directory")
    found={}
    for p in root.rglob("*"):
        if "deployment" in p.relative_to(root).parts:
            continue   # source-only embed, README and hosted deployment contract
        if p.is_symlink():
            raise BundleHold("symlink source not permitted")
        if p.is_file():
            relative=p.relative_to(root).as_posix()
            if relative in found:raise BundleHold("duplicate path")
            found[relative]=p
    if set(found)!=APPROVED:
        extra=sorted(set(found)-APPROVED)
        missing=sorted(APPROVED-set(found))
        raise BundleHold(f"unexpected public payload: extra={extra}, missing={missing}")
    return found

def inspect_public_bundle(source:Path=SOURCE)->dict[str,Any]:
    found=_source_files(Path(source))
    file_index=[]
    total=0
    all_text=[]
    for relative in sorted(found):
        blob=found[relative].read_bytes()
        if len(blob)>MAX_FILE_BYTES:raise BundleHold(f"source file too large: {relative}")
        total+=len(blob)
        if total>MAX_BYTES:raise BundleHold("public package size beyond bounded review")
        try:text=blob.decode("utf-8")
        except UnicodeError as exc:raise BundleHold("non-UTF8 public payload") from exc
        if relative.endswith(".js"):
            # Exact reviewed JS assets contain no template literals. Reject
            # interpolated computed properties rather than pretending a regex
            # scan of fetch()/bracket literals is a complete JS parser (#158).
            if "`" in text:
                raise BundleHold(f"unreviewed JavaScript template literal: {relative}")
            # #158: JS escape sequences can hide computed transport/navigation
            # properties from literal scans. The reviewed public JS needs
            # only ordinary newline escapes and one regex slash escape.
            if re.search(r"\\(?:x[0-9A-Fa-f]{2}|u(?:[0-9A-Fa-f]{4}|\{[0-9A-Fa-f]{1,6}\}))", text):
                raise BundleHold(f"unreviewed JavaScript hex/unicode escape: {relative}")
            _reject_split_computed_transport(text, relative)
        for label,pattern in BLOCKED.items():
            if pattern.search(text):
                raise BundleHold(f"{label}: {relative}")
        # An HTML page or ESM file may reference only local peer assets or preapproved
        # route names. No network fetch of private data permitted in static examples.
        for uri in re.findall(r"""(?:import\s*(?:[^;]*?\s+from\s*)?|from\s*)['"]([^'"]+)['"]""",text):
            _validate_static_reference(relative,uri)
        if relative.endswith(".html"):
            _PublicHtmlReferences(relative).feed(text)
        if relative.endswith(".css") and re.search(r"@import\b",text,re.I):
            raise BundleHold(f"unreviewed CSS import: {relative}")
        if relative.endswith(".css"):
            # No escapes, comments or image-set() occur in the approved CSS.
            # Reject ambiguous syntax instead of claiming regex is a CSS parser.
            if "\\" in text or "/*" in text:
                raise BundleHold(f"unreviewed CSS escape/comment syntax: {relative}")
            if re.search(r"(?<![\w-])(?:-webkit-)?image-set\s*\(",text,re.I):
                raise BundleHold(f"unreviewed CSS image-set resource: {relative}")
        if relative.endswith((".css",".html")):
            # CSS and inline HTML styles may load remote pixels/fonts without JS.
            for uri in re.findall(r"""\burl\(\s*['"]?([^)'"]+)['"]?\s*\)""",text,re.I):
                _validate_static_reference(relative,uri.strip())
        all_text.append(text)
        file_index.append({
            "path":"cgx/"+relative,
            "sha256":hashlib.sha256(blob).hexdigest(),
            "bytes":len(blob)
        })
    full="\n".join(all_text)
    for required in REQUIRED_CONTEXT:
        if required not in full:raise BundleHold("missing demonstrator authority/evidence marking")
    # No unreviewed provider API, private device bridge or read-write transport.
    return {
        "schema":"CGX-PUBLIC-ALLOWLIST-PACKAGE/0.1",
        "status":"SOURCE_CANDIDATE_NOT_PUBLISHED_NOT_OWNER_SIGNED",
        "root_path":"cgx/",
        "file_count":len(file_index),
        "source_bytes":total,
        "assets":file_index,
        "operator_source_included":False,
        "source_licences_independently_cleared":False,
        "external_host_live_verified":False,
        "native_node_authenticated":False,
        "releases_owner_metadata":False,
        "owner_approval_required":True,
        "issue_158":"OPEN_HOLD_FOR_LS_GO_INTERNAL_STATIC_BOUNDARY",
        "issue_161":"OPEN_HOLD_FOR_REAL_NATIVE_TWO_NODE_ACCEPTANCE",
    }

def make_public_bundle(dest:Path,source:Path=SOURCE)->dict[str,Any]:
    src=Path(source).resolve()
    dst=Path(dest).resolve()
    # The isolated public candidate must never be generated anywhere inside
    # the LS GO application, including its compiled dist/build/cache roots.
    # A clean source allowlist alone cannot prevent contamination of operator
    # release artifacts if the output destination overlaps those trees (#158).
    operator_tree=(ROOT/"apps/lightspeed-go").resolve()
    if (dst==src or src in dst.parents or dst==ROOT.resolve() or
        dst==operator_tree or operator_tree in dst.parents):
        raise BundleHold("output cannot overlap source or operator application/build/static tree")
    if dst.exists():
        raise BundleHold("refuse overwrite of prior release candidate")
    result=inspect_public_bundle(src)
    # Static preview uses a separate fresh root, not the Vite operator build.
    dst.mkdir(parents=True,exist_ok=False)
    try:
        for entry in result["assets"]:
            relative=entry["path"]
            target=dst/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            srcfile=src/relative.removeprefix("cgx/")
            blob=srcfile.read_bytes()
            if hashlib.sha256(blob).hexdigest()!=entry["sha256"] or len(blob)!=entry["bytes"]:
                raise BundleHold("TOCTOU source bytes changed during candidate packaging")
            target.write_bytes(blob)
        config=src/"deployment/vercel.json"
        if not config.is_file() or config.is_symlink():
            raise BundleHold("Vercel policy source missing")
        policy=json.loads(config.read_text(encoding="utf-8"))
        if policy.get("version")!=2 or not any(
            x.get("source")=="/cgx/(.*)" and any(
                v.get("key")=="Content-Security-Policy" and "connect-src 'none'" in v.get("value","")
                for v in x.get("headers",[])) for x in policy.get("headers",[])
        ):
            raise BundleHold("public content security policy has drifted")
        # #158: a safe-looking CSP on one route is insufficient when a second
        # header, rewrite, redirect, or route can override/escape it. Pin the
        # entire reviewed hosting contract; JSON formatting/key order is ignored.
        # This is source-level packaging validation, NOT deployed ACL proof.
        expected_policy=json.loads("{\"version\":2,\"trailingSlash\":true,\"headers\":[{\"source\":\"/cgx/(.*)\",\"headers\":[{\"key\":\"X-Content-Type-Options\",\"value\":\"nosniff\"},{\"key\":\"Referrer-Policy\",\"value\":\"strict-origin-when-cross-origin\"},{\"key\":\"Permissions-Policy\",\"value\":\"camera=(), microphone=(), geolocation=()\"},{\"key\":\"Content-Security-Policy\",\"value\":\"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'self'; form-action 'none'; frame-ancestors https://romer.industries https://www.romer.industries\"}]}],\"redirects\":[{\"source\":\"/Cgx\",\"destination\":\"/cgx\",\"permanent\":true},{\"source\":\"/Cgx/:path*\",\"destination\":\"/cgx/:path*\",\"permanent\":true}]}")
        if policy!=expected_policy:
            raise BundleHold("unreviewed public hosting policy drift")
        (dst/"vercel.json").write_text(json.dumps(policy,indent=2)+"\n",encoding="utf-8")
        (dst/"cgx-package-review.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        # Post-copy exact byte check, with an explicit tiny allowlist of sidecars.
        actual={p.relative_to(dst).as_posix() for p in dst.rglob("*") if p.is_file()}
        expected={x["path"] for x in result["assets"]}|{"vercel.json","cgx-package-review.json"}
        if actual!=expected:raise BundleHold("unexpected files after public package construction")
    except Exception:
        shutil.rmtree(dst,ignore_errors=True)
        raise
    return result


def verify_existing_public_candidate(dest:Path,source:Path=SOURCE)->dict[str,Any]:
    """Independently re-read a previously built *isolated* CGX static candidate.

    Fail closed if the output was mutated after packaging or if someone passes
    the ordinary LS GO Vite operator/dist tree as a public deployment source.
    This does not check an actual deployed host or approve publication rights.
    """
    src=Path(source).resolve()
    dst=Path(dest).resolve()
    operator_tree=(ROOT/"apps/lightspeed-go").resolve()
    if (dst==operator_tree or operator_tree in dst.parents or
        dst==src or src in dst.parents or not dst.is_dir() or dst.is_symlink()):
        raise BundleHold("candidate must be an existing isolated directory outside LS GO operator build/static trees")
    expected=inspect_public_bundle(src)  # recheck the canonical allowlisted source
    required={entry["path"] for entry in expected["assets"]}|{"vercel.json","cgx-package-review.json"}
    observed=set()
    for path in dst.rglob("*"):
        if path.is_symlink():
            raise BundleHold("candidate symlink is not permitted")
        if path.is_file():
            rel=path.relative_to(dst).as_posix()
            observed.add(rel)
    if observed!=required:
        raise BundleHold(f"candidate changed file set: missing={len(required-observed)}, extra={len(observed-required)}")
    receipt_file=dst/"cgx-package-review.json"
    try:
        receipt=json.loads(receipt_file.read_text(encoding="utf-8"))
        hosted_policy=json.loads((dst/"vercel.json").read_text(encoding="utf-8"))
        source_policy=json.loads((src/"deployment/vercel.json").read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError) as exc:
        raise BundleHold("candidate metadata or CSP is invalid") from exc
    if receipt!=expected:
        raise BundleHold("candidate receipt does not match qualified source review")
    if hosted_policy!=source_policy:
        raise BundleHold("candidate hosting policy differs from pinned source contract")
    for entry in expected["assets"]:
        blob=(dst/entry["path"]).read_bytes()
        if len(blob)!=entry["bytes"] or hashlib.sha256(blob).hexdigest()!=entry["sha256"]:
            raise BundleHold("candidate leaf bytes no longer match the source receipt")
    return {
        "schema":"CGX-PUBLIC-CANDIDATE-REVERIFY/0.1",
        "state":"SOURCE_ONLY_CANDIDATE_REVERIFIED_NOT_PUBLISHED",
        "verified_file_count":len(expected["assets"]),
        "verified_source_bytes":expected["source_bytes"],
        "operator_dist_accepted":False,
        "rights_cleared":False,
        "live_host_verified":False,
        "native_admitted":False,
        "publication_authorised":False,
        "mint_authorised":False,
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=SOURCE)
    flags=parser.add_mutually_exclusive_group()
    flags.add_argument("--output",type=Path,help="write new, nonexisting candidate directory; NO upload")
    flags.add_argument("--verify-output",type=Path,help="recheck an isolated existing candidate; NO deployment")
    args=parser.parse_args()
    try:
        report=(verify_existing_public_candidate(args.verify_output,args.source) if args.verify_output
                else make_public_bundle(args.output,args.source) if args.output
                else inspect_public_bundle(args.source))
        print(json.dumps(report,sort_keys=True,indent=2))
    except BundleHold as exc:
        parser.exit(2,"CGX_PUBLIC_HOLD: "+str(exc)+"\n")
