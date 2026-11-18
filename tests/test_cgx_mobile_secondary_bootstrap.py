from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "apps/lightspeed-go/public/achilles-mobile.cgx.html"


class ScriptParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.in_script = True
    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
    def handle_data(self, data):
        if self.in_script:
            self.scripts.append(data)


def read_page():
    html = PAGE.read_text(encoding="utf-8")
    parser = ScriptParser()
    parser.feed(html)
    assert len(parser.scripts) == 1
    return html, parser.scripts[0]


def test_mobile_node_is_single_offline_handoff_not_second_runtime():
    html, script = read_page()
    assert "cgx://cgx.cgx" in html
    assert "CGX-MOBILE-SECONDARY-HANDOFF/0.1" in html
    assert 'device_identity:"PENDING_PLATFORM_KEYSTORE_AND_SIGNATURE"' in script
    assert 'enrollment_state:"NOT_ENROLLED"' in script
    assert 'native_mint_authorized:false' in script
    assert 'data_space_network_mint_authorized:false' in script
    assert 'owner_session_verified:false' in script
    assert 'peer_authenticated:false' in script
    assert 'model_training_performed:false' in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "indexedDB" not in script
    assert "serviceWorker" not in script


def test_relay_is_opt_in_without_credentials_or_localhost():
    html, script = read_page()
    assert 'id="relay"' in html
    assert "https://your-private-relay.example" in html
    assert 'u.protocol!=="https:"' in script
    assert 'u.username||u.password||u.search||u.hash' in script
    assert 'host.endsWith(".localhost")' in script
    assert 'host==="[::1]"' in script
    assert '/^127\\./.test(host)' in script
    assert "requestCount++" in script
    assert 'credentials:"omit"' in script
    assert 'cache:"no-store"' in script
    assert 'redirect:"error"' in script
    assert "origin+\"/api/v1/status\"" in script
    assert script.count("fetch(") == 1
    assert "XMLHttpRequest" not in script
    assert "WebSocket" not in script
    assert "authorization" not in script.lower()
    assert 'type="password"' not in html.lower()
    assert 'name="token"' not in html.lower()


def test_android_permissions_are_requests_not_grants():
    html, script = read_page()
    assert "Android has granted" in html
    assert 'android_grants_verified:false' in script
    assert "navigator.geolocation" not in script
    assert "getUserMedia" not in script
    assert "requestDevice" not in script
    assert "requestPermission" not in script
    assert "deviceId" not in script
    assert 'permissioned_network_execution:false' in script


def test_html_script_is_valid_javascript(tmp_path):
    _, script = read_page()
    target = tmp_path / "bootstrap.js"
    target.write_text(script, encoding="utf-8")
    result = subprocess.run(
        ["node", "--check", str(target)], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr


def test_no_privileged_write_or_live_enrollment_endpoints():
    html, script = read_page()
    for forbidden in (
        "/api/v1/cgx/persistence/checkpoint",
        "/api/v1/node-exchange/transfer",
        "/api/v1/node-exchange/compute",
        "/api/v1/owner",
        "/api/v1/auth/login",
        "deviceowner",
        "chmod",
        "native_mint_authorized:true",
    ):
        assert forbidden.lower() not in script.lower()


def test_mobile_js_offline_and_relay_negative_runtime_contract():
    harness = r"""
const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
const html=fs.readFileSync(process.argv[1],"utf8");
const source=html.match(/<script>([\s\S]*?)<\/script>/)[1];
let fetchCalls=0;
const elems={};
function element(id){
 if(!elems[id])elems[id]={value:"",textContent:"",disabled:false,hidden:false,events:{},
   addEventListener(k,fn){this.events[k]=fn},
   querySelectorAll(){return []}
 };
 return elems[id];
}
const context={
 document:{getElementById:element,createElement(){return {click(){},remove(){}}},body:{appendChild(){}}},
 URL,Uint8Array,Date,Array,Blob,console,crypto:require("node:crypto").webcrypto,
 setTimeout,clearTimeout,navigator:{clipboard:{writeText:async()=>{}}},
 fetch(){fetchCalls++;throw new Error("unexpected network request")}
};
vm.runInNewContext(source,context,{timeout:2000});
assert.equal(fetchCalls,0,"must not fetch on page load");
element("make").events.click();
let offline=JSON.parse(element("output").textContent);
assert.equal(offline.selected_transport,"offline_handoff");
assert.equal(offline.enrollment_state,"NOT_ENROLLED");
assert.equal(offline.peer_authenticated,false);
assert.equal(offline.native_mint_authorized,false);
assert.match(offline.challenge_nonce,/^[0-9a-f]{32}$/);
assert.equal(fetchCalls,0);
for(const bad of ["http://example.com","https://127.0.0.2",
  "https://[::1]","https://localhost","https://example.com/path",
  "https://guest:secret@example.com","https://example.com/?token=x"]){
 element("relay").value=bad;
 element("relay").events.input();
 element("make").events.click();
 assert.match(element("output").textContent,/^HOLD:/);
}
element("relay").value="https://relay.example";
element("relay").events.input();
element("make").events.click();
let online=JSON.parse(element("output").textContent);
assert.equal(online.selected_transport,"https_relay_candidate");
assert.equal(online.relay_origin_candidate,"https://relay.example");
assert.equal(online.peer_authenticated,false);
assert.equal(online.owner_session_verified,false);
assert.equal(fetchCalls,0,"building handoff must not initiate a network request");
"""
    result = subprocess.run(
        ["node", "-e", harness, str(PAGE)], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
