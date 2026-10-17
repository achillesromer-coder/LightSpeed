import importlib.util
from pathlib import Path
import hashlib
import json
import pytest
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

module_path=Path(__file__).resolve().parents[1]/"lightspeed_runtime"/"site_link.py"
spec=importlib.util.spec_from_file_location("site_link_tested",module_path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_outbound_status_has_independent_hash_readback_and_no_secret_projection():
    records={}
    def transport(url,token,payload=None):
        assert token=="test-service-access"
        if payload is not None:
            assert "password" not in json.dumps(payload)
            sha=hashlib.sha256(json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
            records.update(stored=True,sha256=sha,report=payload)
        return dict(records)
    result=m.exchange_status("https://lightspeed-go.example.chatgpt.site","test-service-access",
      local_status={"ok":True,"auth":{"configured":True,"password":"do-not-transfer"}},transport=transport)
    assert result["status_exchange_verified"] is True
    assert result["execution_authorized"] is False
    assert result["credential_persisted"] is False

def test_hash_mismatch_fails_without_second_submission():
    calls=[]
    def transport(url,token,payload=None):
        calls.append(payload)
        return {"stored":True,"sha256":"wrong"}
    with pytest.raises(ValueError,match="readback"):
        m.exchange_status("https://lightspeed-go.example.chatgpt.site","token",local_status={"ok":True},transport=transport)
    assert len(calls)==2
    assert calls[1] is None

@pytest.mark.parametrize("origin",["http://example.chatgpt.site","https://example.chatgpt.site@evil.test","https://example.chatgpt.site/path","https://other.example","https://example.chatgpt.site:8443"])
def test_outbound_destination_is_the_existing_sites_origin(origin):
    with pytest.raises(ValueError,match="existing HTTPS"):
        m.exchange_status(origin,"token",local_status={"ok":True})

@pytest.fixture
def http_exchange():
    seen = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers.get("OAI-Sites-Authorization")))
            self.send_response(302 if self.path == "/redirect" else 200)
            if self.path == "/redirect":
                self.send_header("Location", "/credential-target")
            self.end_headers()
            self.wfile.write(b"x" * (m.MAX_RESPONSE_BYTES + 1) if self.path == "/oversized" else b"[]" if self.path == "/array" else b'{"ok":true}')
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", seen
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

def test_redirect_does_not_forward_service_access(http_exchange):
    origin, seen = http_exchange
    with pytest.raises(ValueError, match="redirects"):
        m._request(origin + "/redirect", "synthetic-test-token")
    assert seen == [("/redirect", "Bearer synthetic-test-token")]

@pytest.mark.parametrize("path, error", [("/oversized", "bound"), ("/array", "object")])
def test_http_response_is_bounded_and_typed(http_exchange, path, error):
    origin, _ = http_exchange
    with pytest.raises(ValueError, match=error):
        m._request(origin + path)

def test_direct_http_response_is_accepted(http_exchange):
    origin, _ = http_exchange
    assert m._request(origin + "/valid") == {"ok": True}
