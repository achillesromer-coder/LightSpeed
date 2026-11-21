"""Source-only, deterministic UniSpace passive-device enrollment planner.

Does not connect, authenticate, enumerate hardware, read health data, or grant authority.
"""
from __future__ import annotations
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

REGISTRY = Path(__file__).resolve().parents[1] / "domain_templates" / "passive_edge_profile_registry.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")

def registry() -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("schema") != "CGX-PASSIVE-EDGE-PROFILES/0.1":
        raise ValueError("unsupported passive edge profile registry")
    return data

def https_origin(value: str) -> str:
    """Syntactic preflight only. Server must validate DNS/redirects, TLS, ACL and session."""
    value = value.strip()
    if not value:
        return ""
    p = urlsplit(value)
    if p.scheme != "https" or not p.hostname or p.username or p.password:
        raise ValueError("an explicit credential-free HTTPS origin is required")
    if p.path not in ("", "/") or p.query or p.fragment:
        raise ValueError("only an HTTPS origin, not an arbitrary path, is accepted")
    host = p.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("loopback/local origins are unavailable for hosted client bootstrap")
    try:
        addr = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        if "." not in host or any(not item for item in host.split(".")):
            raise ValueError("host must have an explicit qualified DNS name")
    else:
        if not addr.is_global:
            raise ValueError("non-public IP literals are blocked")
    if p.port not in (None, 443):
        raise ValueError("only standard HTTPS port accepted in bootstrap proposal")
    return "https://" + (f"[{host}]" if ":" in host else host)

def plan_passive_node(
    profile_id: str, *, budget_bytes: int = 4096, origin: str = "",
    source_sha256: str | None = None, source_size: int | None = None,
    user_consent: bool = False, registered_node_proof: bool = False,
) -> dict:
    """Return a NON-AUTHORITATIVE candidate, never a connected status."""
    r = registry()
    profiles = {p["id"]: p for p in r["profiles"]}
    if profile_id not in profiles:
        raise ValueError("unregistered device profile")
    if isinstance(budget_bytes, bool) or not isinstance(budget_bytes, int) or budget_bytes <= 0:
        raise ValueError("budget_bytes must be positive integer")
    if source_sha256 is not None and not SHA256.fullmatch(source_sha256):
        raise ValueError("source digest must be full lowercase SHA-256")
    if source_size is not None and (type(source_size) is not int or source_size < 0):
        raise ValueError("source_size must be nonnegative integer")
    if (source_sha256 is None) != (source_size is None):
        raise ValueError("source hash and size must be supplied together")

    profile = profiles[profile_id]
    tiers = r["bandwidth_tiers"]
    available = [t for t in tiers if t["max_transfer_bytes"] <= budget_bytes]
    tier = available[-1] if available else tiers[0]
    chosen_origin = https_origin(origin)
    reason = "LOCAL_CANDIDATE"
    if profile_id == "WEARABLE_VIA_PHONE":
        reason = "HOLD_CONSENT" if not user_consent else "HOLD_VERIFIED_PROVIDER_ADAPTER"
    elif profile["may_be_node"]:
        reason = "HOLD_DEVICE_AND_SERVER_PROOF" if not registered_node_proof else "HOLD_SIGNED_PEER_RECEIPT"
    elif profile_id == "WEB_CONNECTED":
        reason = "HOLD_EXPLICIT_HTTPS_ORIGIN" if not chosen_origin else "HOLD_SERVER_AUTH_SESSION"
    if source_size is not None and source_size > budget_bytes:
        source_state = "NOT_CACHED"
    else:
        source_state = "SOURCE_REFERENCE_ONLY" if source_sha256 else "UNKNOWN"
    return {
        "schema": "CGX-PASSIVE-NODE-PLAN/0.1",
        "semantic_root": r["semantic_root"],
        "source_contract": r["schema"],
        "profile_id": profile_id,
        "device_class": profile["device_class"],
        "node_id": None,
        "connected": False,
        "peer_authenticated": False,
        "authority_transfer": False,
        "canonical_promotion": False,
        "eligibility": reason,
        "source_state": source_state,
        "source_sha256": source_sha256,
        "source_size": source_size,
        "selected_bandwidth_tier": tier["id"],
        "chunk_bytes": min(tier["chunk_bytes"], budget_bytes),
        "max_in_flight": tier["max_in_flight"],
        "selected_https_origin": chosen_origin or None,
        "capabilities_requested": profile["capabilities"],
        "requirements": profile["requirements"],
        "unsatisfied": profile["missing"],
        "lease_ref": None,
        "receipt_ref": None,
        "contains_credentials": False,
        "server_note": "Trusted endpoint must independently verify DNS/redirects, TLS, identity, consent, ACL, leases, source roots and signed receipts."
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="WEB_OFFLINE")
    parser.add_argument("--budget", type=int, default=4096)
    parser.add_argument("--origin", default="")
    args = parser.parse_args()
    print(json.dumps(plan_passive_node(args.profile, budget_bytes=args.budget, origin=args.origin), indent=2))
