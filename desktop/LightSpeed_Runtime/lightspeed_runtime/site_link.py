"""One-shot outbound status exchange through the existing private LS GO Site.

No daemon, scheduler, command dispatch, credential persistence or authority grant.
The caller obtains current supported Sites service access and retains it in memory.
"""
from datetime import datetime, timezone
import hashlib
import json
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

MAX_RESPONSE_BYTES = 65536

class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the Sites service credential to a redirected target.
        raise ValueError("Site exchange redirects are not allowed")

def _request(url, token="", payload=None):
    headers={"Accept":"application/json"}
    if token: headers["OAI-Sites-Authorization"]="Bearer "+token
    if payload is not None: headers["Content-Type"]="application/json"
    data=None if payload is None else json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode()
    with build_opener(_NoRedirects()).open(Request(url,data=data,headers=headers),timeout=15) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError("Site exchange response exceeds the bound")
        result = json.loads(body)
        if not isinstance(result, dict):
            raise ValueError("Site exchange response must be an object")
        return result

def exchange_status(site_origin, service_token, *, local_status=None, transport=_request):
    target=urlsplit(site_origin)
    if target.scheme!="https" or not target.hostname or not target.hostname.endswith(".chatgpt.site") or target.port not in (None,443) or target.username or target.password or target.query or target.fragment or target.path not in ("","/"):
        raise ValueError("Use the exact existing HTTPS LS GO Site origin")
    if not service_token or len(service_token)>4096:
        raise ValueError("Current supported Sites service access required")
    raw=local_status if local_status is not None else _request("http://127.0.0.1:8765/api/v1/status")
    if not isinstance(raw.get("ok"),bool):
        raise ValueError("Local bridge status unavailable")
    now=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")
    services=raw.get("services") or {}
    health=(raw.get("merovingian") or {}).get("status")
    report={"schema":"cgx-site-host-report/1","host_node":"bouwerbase","generated_at":now,
        "status":{"ok":raw["ok"],"services":{k:services.get(k) is True for k in ("db","storage","merovingian")},
            "merovingian":{"status":health if health in ("pass","degraded","review_required") else "unknown"},
            "auth":{"configured":(raw.get("auth") or {}).get("configured") is True}},
        "execution_authorized":False,"evidence":"HOST_REPORTED; NOT_DEVICE_ENROLLMENT_OR_EXECUTION"}
    sha=hashlib.sha256(json.dumps(report,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    url=site_origin.rstrip("/")+"/api/v1/site-link/host"
    ack=transport(url,service_token,report)
    readback=transport(url,service_token)
    if not ack.get("stored") or ack.get("sha256")!=sha or readback.get("sha256")!=sha or readback.get("report")!=report:
        raise ValueError("Independent Sites report readback did not match")
    return {"schema":"cgx-site-status-exchange-receipt/1","host_node":"bouwerbase","site_origin":site_origin.rstrip("/"),
        "sha256":sha,"generated_at":now,"status_exchange_verified":True,"execution_authorized":False,
        "device_enrollment_verified":False,"credential_persisted":False}
