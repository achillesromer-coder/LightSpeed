"""Private, loopback-only CGX/LOAD pre-mint GUI. Does NOT operate mint/issuer.
Built source lives in an isolated review directory, never a public release.
Authentication here protects the review server only, NOT native CGX authority.
"""
from __future__ import annotations
import argparse
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, unquote
import hmac, secrets, socket, webbrowser

PORT=4174
COOKIE="cgx_premint_local_session"
def gate(method, path, host, cookie, ticket):
    """Pure security gate; no network effects or capability grant."""
    if host not in (f"127.0.0.1:{PORT}","127.0.0.1"):
        return "DENY_HOST"
    if method not in ("GET","HEAD"):
        return "DENY_METHOD"
    parsed=urlsplit(path)
    raw=unquote(parsed.path)
    if raw in ("/start","/start/"):
        value=parse_qs(parsed.query).get("ticket",[])
        if method=="GET" and len(value)==1 and hmac.compare_digest(value[0],ticket):
            return "START_SESSION"
        return "DENY_TICKET"
    if raw.startswith("/api/") or raw in ("/api",):
        return "DENY_API"
    parts=raw.split("/")
    if not raw.startswith("/") or any(
        part in ("..",".git") or part.startswith(".") for part in parts if part
    ) or chr(0) in raw or "\\" in raw:
        return "DENY_PATH"
    prefix=COOKIE+"="
    candidates=[x.strip()[len(prefix):] for x in cookie.split(";")
                if x.strip().startswith(prefix)]
    if len(candidates)!=1 or not hmac.compare_digest(candidates[0],ticket):
        return "DENY_SESSION"
    return "ALLOW_STATIC"

class ExclusiveServer(ThreadingHTTPServer):
    allow_reuse_address=False
    daemon_threads=True
    def server_bind(self):
        if hasattr(socket,"SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        super().server_bind()

class Handler(SimpleHTTPRequestHandler):
    server_version="CGXPrivateReview"
    sys_version=""
    def log_message(self,*args):
        return
    def end_headers(self):
        self.send_header("Cache-Control","no-store, private")
        self.send_header("Referrer-Policy","no-referrer")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("X-Frame-Options","DENY")
        self.send_header("Cross-Origin-Resource-Policy","same-origin")
        self.send_header("Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; connect-src 'self' http://127.0.0.1:8772 "
            "http://127.0.0.1:8765; font-src 'self' data:; frame-src 'none'; "
            "object-src 'none'; base-uri 'self'; form-action 'none'")
        super().end_headers()
    def _serve(self):
        decision=gate(self.command,self.path,self.headers.get("Host",""),
            self.headers.get("Cookie",""),self.server.ticket)
        if decision=="START_SESSION":
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Set-Cookie",
                f"{COOKIE}={self.server.ticket}; HttpOnly; SameSite=Strict; Path=/")
            self.send_header("Location","/#objects")
            self.send_header("Content-Length","0")
            self.end_headers()
            return
        if decision!="ALLOW_STATIC":
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        route=urlsplit(self.path).path
        target=Path(self.translate_path(route))
        root=self.server.review_root
        # Disallow symlinks anywhere between root and target.
        try:
            relative=target.relative_to(root)
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN); return
        cursor=root
        for part in relative.parts:
            cursor=cursor/part
            if cursor.is_symlink():
                self.send_error(HTTPStatus.FORBIDDEN); return
        if not target.is_file():
            if route=="/" or (not Path(route).suffix and not route.startswith("/api/")):
                self.path="/index.html"
            else:
                self.send_error(HTTPStatus.NOT_FOUND);return
        else:
            self.path=route
        if self.command=="HEAD":super().do_HEAD()
        else:super().do_GET()
    def do_GET(self):self._serve()
    def do_HEAD(self):self._serve()
    def do_POST(self):self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
    def do_PUT(self):self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
    def do_DELETE(self):self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
    def list_directory(self,path):
        self.send_error(HTTPStatus.FORBIDDEN);return None

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--directory",type=Path,required=True)
    parser.add_argument("--open-browser",action="store_true")
    args=parser.parse_args()
    root=args.directory.resolve(strict=True)
    if not root.is_dir() or not (root/"index.html").is_file():
        raise SystemExit("CGX_GUI_BUILD_NOT_FOUND")
    ticket=secrets.token_hex(32)
    with ExclusiveServer(("127.0.0.1",PORT),partial(Handler,directory=str(root))) as server:
        server.ticket=ticket
        server.review_root=root
        if args.open_browser:
            webbrowser.open(f"http://127.0.0.1:{PORT}/start?ticket={ticket}")
        server.serve_forever(poll_interval=0.5)
if __name__=="__main__":
    main()
