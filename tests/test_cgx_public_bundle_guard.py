"""UniSpace synthetic-only static bundle and private operator disclosure gates."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import subprocess
import os

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"apps/lightspeed-go/scripts/cgx_public_bundle_guard.py"
SPEC=importlib.util.spec_from_file_location("cgx_public_bundle_guard",FILE)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class PublicBundleTests(unittest.TestCase):
    def test_exact_pr174_source_blobs_are_preserved(self):
        receipt=json.loads((ROOT/"cgx/review/unispace_public_source_fold_20261020.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["source_pr"],174)
        self.assertEqual(len(receipt["carried_source_files"]),18)
        self.assertEqual(receipt["review_delta_schema"],"CGX-UNISPACE-PR188-ORBIT-DELTA/0.1")
        deltas={x["path"]:x for x in receipt["review_deltas"]}
        self.assertEqual(len(deltas),5)
        self.assertEqual(set(deltas),{
            ".github/workflows/unispace-public-viewer.yml",
            "apps/lightspeed-go/public/cgx/assets/core.js",
            "apps/lightspeed-go/public/cgx/assets/viewer.css",
            "apps/lightspeed-go/public/cgx/assets/viewer.js",
            "apps/lightspeed-go/tests/unispace-public.test.mjs",
        })
        for item in receipt["carried_source_files"]:
            raw=(ROOT/item["path"]).read_bytes()
            # Git owns canonical provenance bytes; Windows checkout CRLF is not a new source revision.
            canonical=subprocess.check_output(["git","show",":"+item["path"]],cwd=ROOT)
            self.assertEqual(raw.replace(b"\r\n",b"\n"),canonical,item["path"])
            blob=hashlib.sha1(b"blob "+str(len(canonical)).encode()+bytes([0])+canonical).hexdigest()
            if item["path"] in deltas:
                delta=deltas[item["path"]]
                # This preserves PR174 source lineage without claiming that
                # intentionally modified PR188 review files are byte-identical.
                self.assertEqual(delta["original_pr174_blob_sha1"],item["git_blob_sha1"])
                self.assertEqual(delta["disposition"],"SOURCE_REVIEW_ONLY_NOT_PUBLIC_RELEASE")
                self.assertEqual(blob,delta["review_branch_blob_sha1"],item["path"])
            else:
                self.assertEqual(blob,item["git_blob_sha1"],item["path"])

    def test_existing_cgx_tree_exact_allowlist(self):
        report=mod.inspect_public_bundle()
        self.assertEqual(report["file_count"],12)
        self.assertEqual({x["path"] for x in report["assets"]},{"cgx/"+s for s in mod.APPROVED})
        self.assertFalse(report["operator_source_included"])
        self.assertFalse(report["external_host_live_verified"])
        self.assertFalse(report["source_licences_independently_cleared"])

    def test_fresh_package_contains_only_cgx_and_policy(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"release"
            review=mod.make_public_bundle(out)
            files={p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
            self.assertEqual(files,{"cgx/"+p for p in mod.APPROVED}|{"vercel.json","cgx-package-review.json"})
            self.assertFalse((out/"data").exists())
            self.assertFalse((out/"review").exists())
            self.assertFalse((out/"src").exists())
            self.assertFalse((out/"cgx/deployment").exists())
            for x in review["assets"]:
                raw=(out/x["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),x["sha256"])
            self.assertFalse(json.loads((out/"cgx-package-review.json").read_text())["external_host_live_verified"])

    def test_unreviewed_asset_is_not_automatically_packaged(self):
        with tempfile.TemporaryDirectory() as d:
            copy=Path(d)/"cgx"
            shutil.copytree(mod.SOURCE,copy)
            (copy/"internal_dump.json").write_text('{"private":true}',encoding="utf-8")
            with self.assertRaisesRegex(mod.BundleHold,"unexpected public payload"):
                mod.inspect_public_bundle(copy)

    def test_private_catalogue_or_native_api_reference_rejected(self):
        for attack in [
          'fetch("/data/cgx_object_review_catalogue.json")',
          'fetch("/api/v1/cgx/intake")',
          'import {x} from "../../../desktopBridge"',
          'const pwd = "sk-proj-DO_NOT_USE_TEST"',
        ]:
            with self.subTest(attack=attack),tempfile.TemporaryDirectory() as d:
                c=Path(d)/"cgx"
                shutil.copytree(mod.SOURCE,c)
                with (c/"assets/core.js").open("a",encoding="utf-8") as f:
                    f.write("\n"+attack)
                with self.assertRaises(mod.BundleHold):
                    mod.inspect_public_bundle(c)

    def test_scripted_navigation_escapes_fail_closed(self):
        # #158: connect-src 'none' is not a navigation/redirect ACL.
        # Only the reviewed read-only location.pathname usage is permitted.
        attacks = [
            'window.location = "https://example.invalid/collect"',
            'location.href = "/owner-private/receipt.json"',
            'location.assign("/owner-private/receipt.json")',
            'document.location.replace("https://example.invalid/collect")',
            'top.location = "/owner-private/receipt.json"',
            'window.open("https://example.invalid/collect", "_self")',
            'globalThis["open"]("https://example.invalid/collect")',
            'window["location"]["href"] = "/owner-private/receipt.json"',
            'location["href"] = "/owner-private/receipt.json"',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "scripted navigation escape"):
                    mod.inspect_public_bundle(c)

    def test_read_only_location_pathname_remains_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "cgx"
            shutil.copytree(mod.SOURCE, c)
            with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                handle.write("\nconst currentRoute = location.pathname;")
            self.assertEqual(mod.inspect_public_bundle(c)["file_count"], 12)

    def test_scripted_passive_resource_sinks_fail_closed(self):
        # #158: CSP connect-src 'none' does not deny same-origin img/worker GET.
        attacks = [
            'const i = new Image(); i.src="/owner-private/receipt.json";',
            'const a = new Audio("/owner-private/voice.mp3");',
            'const f = document.createElement("iframe");',
            'img.setAttribute("src","/owner-private/receipt.json");',
            'img["src"]="/owner-private/receipt.json";',
            'const w = new Worker("/owner-private/worker.js");',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "scripted passive resource loads"):
                    mod.inspect_public_bundle(c)

    def test_dom_and_cssom_string_injection_sinks_fail_closed(self):
        # #158: passive private GET can be created via HTML/CSS parsing without
        # fetch(), src=, createElement() or window navigation.
        attacks = [
            'document.write("<img src=/owner-private/receipt.json>")',
            'document.writeln("<iframe src=/owner-private/status>")',
            'surface.insertAdjacentHTML("beforeend", "<img src=/owner-private/x>")',
            'panel.outerHTML = "<img src=/owner-private/x>"',
            'range.createContextualFragment("<img src=/owner-private/x>")',
            'sheet.insertRule("body{background:url(/owner-private/x)}")',
            'sheet.replaceSync("body{background:url(/owner-private/x)}")',
            'new DOMParser().parseFromString("<img src=/owner-private/x>", "text/html")',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                    handle.write(chr(10) + attack)
                with self.assertRaisesRegex(mod.BundleHold, "unreviewed DOM or stylesheet injection"):
                    mod.inspect_public_bundle(c)

    def test_text_only_dom_projection_remains_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "cgx"
            shutil.copytree(mod.SOURCE, c)
            with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                handle.write(chr(10) + 'node.textContent = "PUBLIC_SAFE_SYNTHETIC";')
            self.assertEqual(mod.inspect_public_bundle(c)["file_count"], 12)

    def test_dynamic_network_and_code_paths_hold_even_when_private_name_is_split(self):
        attacks = [
            'fetch("/da" + "ta/cgx_object_review_" + "catalogue.json")',
            'const x = new XMLHttpRequest();',
            'const x = new WebSocket("wss://example.invalid/socket");',
            'const x = new EventSource("/events");',
            'navigator.sendBeacon("/collect", "synthetic");',
            'import("./" + "unreviewed.js")',
            'navigator.serviceWorker.register("/sw.js")',
            'eval("globalThis.privateData")',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "active network or dynamic code API"):
                    mod.inspect_public_bundle(c)

    def test_computed_network_api_access_is_denied(self):
        # #158: a public asset must not call browser transport APIs through
        # computed properties even if no literal fetch( or sendBeacon( appears.
        attacks = [
            'globalThis["fetch"]("/owner-private/receipt.json")',
            'navigator["sendBeacon"]("/collect", "data")',
            'window["WebSocket"]("wss://example.invalid")',
            'navigator["serviceWorker"]["register"]("/sw.js")',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "computed network API access"):
                    mod.inspect_public_bundle(c)

    def test_split_computed_network_property_names_fail_closed(self):
        # #158: bracket-string concatenation bypasses literal fetch() and
        # bracket-single-string scans; deny this bounded known form.
        attacks = [
            'globalThis["fe" + "tch"]("/owner-private/receipt.json")',
            "navigator['send'+'Beacon']('/collect', 'data')",
            'window["Web" + "Socket"]("wss://example.invalid")',
            'navigator["service" + "Worker"]["register"]("/sw.js")',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "computed split network API access"):
                    mod.inspect_public_bundle(c)

    def test_split_computed_navigation_properties_fail_closed(self):
        # #158: connect-src does not stop navigation via computed JS properties.
        # These evade literal location.assign/window.open scanners.
        attacks = [
            'window["loc" + "ation"].assign("/owner-private/receipt.json")',
            'globalThis["op" + "en"]("https://example.invalid/collect")',
            'location["as" + "sign"]("/owner-private/receipt.json")',
            'location["re" + "place"]("https://example.invalid/collect")',
            'window.location["hr" + "ef"] = "/owner-private/receipt.json"',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "computed split navigation property access"):
                    mod.inspect_public_bundle(c)

    def test_escaped_js_computed_transport_and_navigation_hold(self):
        # #158: JS string escapes bypass literal bracket-property regexes.
        # These are synthetic negatives, not proof of a deployed ACL.
        attacks = [
            r'globalThis["\x66etch"]("/owner-private/receipt.json")',
            r'window["\u006cocation"].assign("/owner-private/receipt.json")',
            r'window["\u{6f}pen"]("https://example.invalid/collect")',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "unreviewed JavaScript hex/unicode escape"):
                    mod.inspect_public_bundle(c)

    def test_js_template_literal_transport_fail_closed(self):
        # #158: computed template literals can hide network API names from
        # ordinary fetch() and bracket-quoted-property checks. The reviewed
        # synthetic JS source uses no backticks, so fail closed on all of them.
        attacks = [
            'globalThis[`fetch`]("/owner-private/receipt.json")',
            'globalThis[`fe\u0024{"t"}ch`]("/owner-private/receipt.json")',
            'window[`WebSocket`]("wss://example.invalid/socket")',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/core.js").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "unreviewed JavaScript template literal"):
                    mod.inspect_public_bundle(c)

    def test_inline_or_empty_source_script_fails_closed(self):
        # #158: offline/static preview must not gain an unreviewed executable
        # surface merely because the intended hosted CSP forbids inline JS.
        attacks = [
            '<script>document.body.innerHTML = "<img src=/owner-private/receipt.json>"</script>',
            '<script type="module">globalThis.owner = true</script>',
            '<script src=""></script>',
            '<script type="module" src></script>',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "index.html").open("a", encoding="utf-8") as handle:
                    handle.write("\\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "inline or empty-source script"):
                    mod.inspect_public_bundle(c)

    def test_passive_html_css_network_resources_fail_closed(self):
        # Network-capable passive resource attributes and CSS url() must be
        # rejected even if CSP is intended to deny their runtime requests.
        attacks = [
            ("assets/viewer.css", '\n.tile{background-image:url("https://example.invalid/pixel.png")}'),
            ("index.html", '<img src="https://example.invalid/pixel.png" alt="unreviewed">'),
            ("index.html", '<img srcset="https://example.invalid/pixel.png 1x" alt="unreviewed">'),
        ]
        for relative, attack in attacks:
            with self.subTest(relative=relative, attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / relative).open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaises(mod.BundleHold):
                    mod.inspect_public_bundle(c)

    def test_html_navigation_and_form_surfaces_fail_closed(self):
        # #158: meta refresh, base URL rewriting and forms bypass fetch() scans.
        attacks = [
            '<meta http-equiv="refresh" content="0;url=https://example.invalid/leak">',
            '<META content="0;url=/data/private" HTTP-EQUIV="REFRESH">',
            '<base href="https://example.invalid/">',
            '<form action="https://example.invalid/collect" method="post"></form>',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "index.html").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaises(mod.BundleHold):
                    mod.inspect_public_bundle(c)

    def test_public_anchor_navigation_does_not_escape_allowlist(self):
        # #158: anchors and image-map areas are navigational disclosure
        # surfaces even without fetch(), form submission or inline scripts.
        attacks = [
            '<a href="/owner-private/achilles-status.json">private</a>',
            '<a href="javascript:alert(1)">script URL</a>',
            '<a href="data:text/html,private">data URL</a>',
            '<a href="https://example.invalid/collect">remote</a>',
            '<area href="//example.invalid/collect" alt="remote">',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "index.html").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaises(mod.BundleHold):
                    mod.inspect_public_bundle(c)

    def test_duplicate_html_resource_attributes_fail_closed(self):
        # HTMLParser preserves duplicate attrs, but dict() silently keeps only
        # the last one. Browser-first semantics can load an unapproved URL.
        attacks = [
            '<img src="/owner-private/receipt.json" src="/cgx/assets/viewer.css">',
            '<img src="/cgx/assets/viewer.css" src="/owner-private/receipt.json">',
            '<a HREF="https://example.invalid/collect" href="#overview">demo</a>',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "index.html").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaisesRegex(mod.BundleHold, "duplicate HTML attributes"):
                    mod.inspect_public_bundle(c)

    def test_reviewed_local_anchor_routes_and_fragments_remain_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "cgx"
            shutil.copytree(mod.SOURCE, c)
            with (c / "index.html").open("a", encoding="utf-8") as handle:
                handle.write("\n" + '<a href="/cgx/">home</a><a href="/cgx/eco/">eco</a><a href="#overview">local</a>')
            report = mod.inspect_public_bundle(c)
            self.assertEqual(report["file_count"], 12)

    def test_unquoted_html_and_embedded_private_resource_negatives(self):
        # #158: HTMLParser must inspect unquoted and entity-decoded URLs;
        # regex scans of only quoted src/href silently miss browser loads.
        attacks = [
            '<img src=/owner-private/achilles-packet.json>',
            '<object data=/owner-private/cognigrex-sandbox.sqlite></object>',
            '<img src=&#47;owner-private&#47;packet.json>',
            '<iframe srcdoc="&lt;img src=/owner-private/packet.json&gt;"></iframe>',
            '<img srcset=/owner-private/packet.png>',
            '<a href="#public" ping="/owner-private/beacon">demo</a>',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "index.html").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaises(mod.BundleHold):
                    mod.inspect_public_bundle(c)

    def test_embedded_markup_and_inline_event_resource_surfaces_hold(self):
        # Reviewed HTML shells contain no inline SVG, MathML, styles or handlers.
        attacks = [
            '<svg><image href="https://example.invalid/pixel.svg"/></svg>',
            '<math><annotation-xml encoding="text/html">unreviewed</annotation-xml></math>',
            '<style>.x{background:image-set("https://example.invalid/pixel.png" 1x)}</style>',
            '<div style="background-image:url(https://example.invalid/pixel.png)"></div>',
            '<img src="./assets/viewer.css" onerror="alert(1)">',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "index.html").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaises(mod.BundleHold):
                    mod.inspect_public_bundle(c)

    def test_css_non_url_resource_and_obfuscation_negatives(self):
        attacks = [
            '.x{background:image-set("https://example.invalid/pixel.png" 1x)}',
            '.x{background:-webkit-image-set("https://example.invalid/pixel.png" 1x)}',
            '.x{background:url(/*masked*/https://example.invalid/pixel.png)}',
            '.x{background:u\\72l(https://example.invalid/pixel.png)}',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "assets/viewer.css").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaises(mod.BundleHold):
                    mod.inspect_public_bundle(c)

    def test_legacy_html_resource_loads_fail_closed(self):
        # #158: input[type=image] and legacy background attributes can request
        # resources even when ordinary src/href element scans pass.
        attacks = [
            '<input type="image" src="/owner-private/achilles-packet.json">',
            '<body background="/owner-private/owner-background.png">',
            '<table background="/owner-private/owner-background.png"></table>',
        ]
        for attack in attacks:
            with self.subTest(attack=attack), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                with (c / "index.html").open("a", encoding="utf-8") as handle:
                    handle.write("\n" + attack)
                with self.assertRaises(mod.BundleHold):
                    mod.inspect_public_bundle(c)

    def test_non_resource_input_remains_usable_in_public_shell(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "cgx"
            shutil.copytree(mod.SOURCE, c)
            with (c / "index.html").open("a", encoding="utf-8") as handle:
                handle.write('\n<input type="search" aria-label="Local demo filter">')
            self.assertEqual(mod.inspect_public_bundle(c)["file_count"], 12)

    def test_no_symlink_intake(self):
        with tempfile.TemporaryDirectory() as d:
            c=Path(d)/"cgx"
            shutil.copytree(mod.SOURCE,c)
            try:
                (c/"internal_link").symlink_to(c/"assets/core.js")
            except OSError as exc:
                if os.name=="nt" and getattr(exc,"winerror",None)==1314:
                    self.skipTest("Windows symbolic-link creation privilege unavailable; CI Linux tests this negative")
                raise
            with self.assertRaises(mod.BundleHold):
                mod.inspect_public_bundle(c)

    def test_public_bundle_never_overwrites_existing_folder(self):
        with tempfile.TemporaryDirectory() as d:
            existing=Path(d)/"release"
            existing.mkdir()
            (existing/"keep.txt").write_text("owner bytes",encoding="utf-8")
            with self.assertRaisesRegex(mod.BundleHold,"overwrite"):
                mod.make_public_bundle(existing)
            self.assertEqual((existing/"keep.txt").read_text(),"owner bytes")

    def test_missing_release_headers_holds_and_removes_incomplete_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            c=Path(d)/"cgx"
            shutil.copytree(mod.SOURCE,c)
            p=c/"deployment/vercel.json"
            x=json.loads(p.read_text(encoding="utf-8"))
            x["headers"][0]["headers"]=[h for h in x["headers"][0]["headers"] if h["key"]!="Content-Security-Policy"]
            p.write_text(json.dumps(x),encoding="utf-8")
            output=Path(d)/"bundle"
            with self.assertRaisesRegex(mod.BundleHold,"content security policy"):
                mod.make_public_bundle(output,c)
            self.assertFalse(output.exists())

    def test_host_policy_drift_cannot_override_reviewed_public_boundary(self):
        # #158: a valid CSP entry must not mask an added rewrite, alternate
        # header rule, or external redirect in the deployable policy sidecar.
        for change in ("private_rewrite", "external_redirect", "extra_header_rule", "relaxed_csp"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as d:
                c = Path(d) / "cgx"
                shutil.copytree(mod.SOURCE, c)
                p = c / "deployment/vercel.json"
                policy = json.loads(p.read_text(encoding="utf-8"))
                if change == "private_rewrite":
                    policy["rewrites"] = [{"source": "/cgx/private", "destination": "/api/v1/owner"}]
                elif change == "external_redirect":
                    policy["redirects"].append({"source": "/cgx/escape", "destination": "https://example.invalid/collect"})
                elif change == "extra_header_rule":
                    policy["headers"].append({"source": "/cgx/(.*)", "headers": [{"key": "Content-Security-Policy", "value": "default-src *"}]})
                else:
                    policy["headers"][0]["headers"][-1]["value"] += "; report-uri https://example.invalid/collect"
                p.write_text(json.dumps(policy), encoding="utf-8")
                output = Path(d) / "candidate"
                with self.assertRaisesRegex(mod.BundleHold, "unreviewed public hosting policy drift"):
                    mod.make_public_bundle(output, c)
                self.assertFalse(output.exists())

    def test_host_policy_json_formatting_does_not_change_accepted_semantics(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "cgx"
            shutil.copytree(mod.SOURCE, c)
            p = c / "deployment/vercel.json"
            policy = json.loads(p.read_text(encoding="utf-8"))
            p.write_text(json.dumps(policy, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            output = Path(d) / "candidate"
            report = mod.make_public_bundle(output, c)
            self.assertEqual(report["file_count"], 12)
            self.assertTrue((output / "vercel.json").is_file())

    def test_does_not_write_under_operator_public(self):
        with self.assertRaises(mod.BundleHold):
            mod.make_public_bundle(ROOT/"apps/lightspeed-go/public/new_release_subtree")

    def test_operator_build_destinations_fail_closed_before_copy(self):
        # #158: do not contaminate LS GO dist/build/Vite cache with a
        # separately reviewed public-only CGX candidate.
        for relative in ("dist", "build", ".vite", "public"):
            dest=ROOT/"apps/lightspeed-go"/relative/"__cgx_public_guard_negative_20261101__"
            with self.subTest(relative=relative):
                with self.assertRaisesRegex(mod.BundleHold,"operator application/build/static tree"):
                    mod.make_public_bundle(dest)
                self.assertFalse(dest.exists())

    def test_full_operator_public_root_cannot_be_used_as_cgx_release_root(self):
        # Vite copies LS GO public/data and public/review into its ordinary build.
        # The reviewed CGX public release MUST come from the separately allowlisted
        # 12-file bundle, not a general Vite operator build (issue #158).
        with self.assertRaisesRegex(mod.BundleHold,"unexpected public payload"):
            mod.inspect_public_bundle(ROOT/"apps/lightspeed-go/public")

if __name__=="__main__":unittest.main()
