#!/usr/bin/env python3
"""Fail-closed HTTPS acceptance probe for a deployed LS GO CGX reviewer ingress.

This does not deploy, mutate CGX, issue invitations, or store session secrets.
Optional valid/revoked visitor sessions are supplied only through environment variables.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import ipaddress
import json
import os
import socket
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA = "LS-GO-CGX-VISITOR-HTTPS-ACCEPTANCE/0.1"
VISITOR_SCHEMA = "LS-GO-CGX-VISITOR/0.1"
SESSION_HEADER = "X-LightSpeed-Visitor-Session"
VALID_SESSION_ENV = "LIGHTSPEED_VISITOR_PROBE_VALID_SESSION"
REVOKED_SESSION_ENV = "LIGHTSPEED_VISITOR_PROBE_REVOKED_SESSION"
NEGATIVE_PATHS = (
    "/api/v1/visitor/invites",
    "/api/v1/visitor/revoke",
    "/api/v1/visitor/owner-review",
    "/api/v1/command",
    "/api/v1/projects",
    "/api/v1/results",
    "/api/v1/node",
    "/api/v1/representation",
    "/data/cgx_object_review_catalogue.json",
    "/data/component_geometry_atlas_public_review.json",
    "/review/renders/",
    "/review/renders/mark_iii_review.svg",
    "/review/renders/rfs_emff_review.svg",
    "/review/mesh/",
    "/review/mesh/mark_iii.json",
    "/review/mesh/intersol.json",
)
FORBIDDEN_MARKERS = (
    "cgx_object_review_catalogue",
    "component_geometry_atlas_public_review",
    "Cognigrex.cgx",
    "LightSpeed_Runtime",
    "review/renders/",
    "file://",
)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_origin(value: str) -> tuple[str, int]:
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or parsed.port not in (None, 443)
    ):
        raise ValueError("origin must be an HTTPS host root with no path, credentials, query or fragment")
    host = parsed.hostname.lower()
    if host in {"localhost", "0.0.0.0"} or host.endswith((".local", ".internal", ".localhost")):
        raise ValueError("local/internal origins are prohibited")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        if "." not in host:
            raise ValueError("origin hostname must be fully qualified") from None
    else:
        if not ip.is_global:
            raise ValueError("non-global IP origins are prohibited")
    return host, parsed.port or 443


def resolve_public(host: str, port: int) -> list[str]:
    addresses: list[str] = []
    for family, _, _, _, sockaddr in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        raw = sockaddr[0]
        ip = ipaddress.ip_address(raw)
        if not ip.is_global:
            raise ValueError(f"origin resolved to non-global address: {raw}")
        if raw not in addresses:
            addresses.append(raw)
    if not addresses:
        raise ValueError("origin did not resolve")
    return addresses


def request(host: str, port: int, path: str, headers: dict[str, str] | None = None) -> dict:
    conn = http.client.HTTPSConnection(host, port, timeout=15, context=ssl.create_default_context())
    try:
        conn.request("GET", path, headers=headers or {})
        response = conn.getresponse()
        body = response.read(1_000_000)
        return {
            "path": path,
            "status": response.status,
            "headers": {k.lower(): v for k, v in response.getheaders()},
            "body_sha256": sha256(body),
            "body_bytes": len(body),
            "_body": body,
        }
    finally:
        conn.close()


def has_security_headers(result: dict) -> bool:
    headers = result["headers"]
    return (
        "no-store" in headers.get("cache-control", "").lower()
        and headers.get("referrer-policy", "").lower() == "no-referrer"
        and bool(headers.get("content-security-policy", "").strip())
    )


def public_checks(host: str, port: int) -> tuple[list[dict], list[str]]:
    failures: list[str] = []
    checks: list[dict] = []

    review = request(host, port, "/review.html")
    body_text = review.pop("_body").decode("utf-8", errors="replace")
    review["check"] = "review_html"
    review["security_headers_ok"] = has_security_headers(review)
    review["forbidden_marker_found"] = any(m.lower() in body_text.lower() for m in FORBIDDEN_MARKERS)
    if review["status"] != 200:
        failures.append(f"review.html status={review['status']}")
    if not review["security_headers_ok"]:
        failures.append("review.html security headers incomplete")
    if review["forbidden_marker_found"]:
        failures.append("review.html contains forbidden internal marker")
    checks.append(review)

    capabilities = request(host, port, "/api/v1/visitor/capabilities")
    cap_body = capabilities.pop("_body")
    capabilities["check"] = "visitor_capabilities"
    capabilities["no_store"] = "no-store" in capabilities["headers"].get("cache-control", "").lower()
    try:
        payload = json.loads(cap_body.decode("utf-8"))
    except Exception:
        payload = None
    capabilities["schema_ok"] = isinstance(payload, dict) and payload.get("schema") == VISITOR_SCHEMA
    capabilities["authority_flags_ok"] = isinstance(payload, dict) and all(
        payload.get(key) is False
        for key in ("source_mutation", "machine_execution", "remote_source_fetch", "canonical_cgx_ingestion")
    )
    capabilities["identity_assurance_ok"] = (
        isinstance(payload, dict) and payload.get("identity_assurance") == "INVITATION_POSSESSION_ONLY"
    )
    if capabilities["status"] != 200:
        failures.append(f"capabilities status={capabilities['status']}")
    if not capabilities["no_store"]:
        failures.append("capabilities missing Cache-Control: no-store")
    if not capabilities["schema_ok"]:
        failures.append("capabilities schema mismatch")
    if not capabilities["authority_flags_ok"]:
        failures.append("capabilities authority flags unsafe")
    if not capabilities["identity_assurance_ok"]:
        failures.append("capabilities identity assurance mismatch")
    checks.append(capabilities)

    for path in NEGATIVE_PATHS:
        result = request(host, port, path)
        result.pop("_body")
        result["check"] = "private_route_non_disclosure"
        result["non_disclosed"] = result["status"] in (403, 404)
        if not result["non_disclosed"]:
            failures.append(f"private path disclosed {path} status={result['status']}")
        checks.append(result)

    return checks, failures


def session_checks(host: str, port: int) -> tuple[list[dict], list[str], list[str]]:
    checks: list[dict] = []
    failures: list[str] = []
    missing: list[str] = []
    cases = (
        ("valid_session", VALID_SESSION_ENV, 200),
        ("revoked_session", REVOKED_SESSION_ENV, 401),
    )
    for name, env_name, expected in cases:
        token = os.environ.get(env_name, "").strip()
        if not token:
            missing.append(env_name)
            continue
        result = request(host, port, "/api/v1/visitor/me", {SESSION_HEADER: token})
        result.pop("_body")
        result["check"] = name
        result["expected_status"] = expected
        result["pass"] = result["status"] == expected
        if not result["pass"]:
            failures.append(f"{name} status={result['status']} expected={expected}")
        checks.append(result)
    return checks, failures, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--expected-review-sha256")
    args = parser.parse_args()

    host, port = parse_origin(args.origin)
    resolved = resolve_public(host, port)
    checks, failures = public_checks(host, port)
    session_results, session_failures, missing_sessions = session_checks(host, port)
    checks.extend(session_results)
    failures.extend(session_failures)

    review = next(item for item in checks if item["check"] == "review_html")
    expected_hash = (args.expected_review_sha256 or "").lower().strip()
    hash_bound = bool(expected_hash)
    if hash_bound and (len(expected_hash) != 64 or any(c not in "0123456789abcdef" for c in expected_hash)):
        raise ValueError("--expected-review-sha256 must be a lowercase/uppercase SHA-256 hex value")
    if hash_bound and review["body_sha256"].lower() != expected_hash:
        failures.append("deployed review.html hash does not match expected release hash")

    if failures:
        classification = "FAIL"
    elif missing_sessions or not hash_bound:
        classification = "PARTIAL / LIVE_INGRESS_BOUNDARY_PASS / SESSION_OR_HASH_BINDING_OPEN"
    else:
        classification = "PASS"

    receipt = {
        "schema": SCHEMA,
        "recorded_utc": utc(),
        "origin": f"https://{host}",
        "resolved_public_addresses": resolved,
        "classification": classification,
        "mutations_performed": False,
        "credentials_persisted": False,
        "expected_review_sha256": expected_hash or None,
        "missing_optional_session_proofs": missing_sessions,
        "failures": failures,
        "checks": checks,
    }
    packed = json.dumps(receipt, indent=2, sort_keys=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(packed + "\n", encoding="utf-8")
    print(packed)
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
