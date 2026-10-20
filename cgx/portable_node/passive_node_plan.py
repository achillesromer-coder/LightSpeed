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


SURFACE_KINDS = {"SQUARESPACE_PUBLIC", "UNISPACE_APP", "CGX_OWNER"}
TRANSPORT_PREFERENCES = {"CURRENT_HTTPS", "OFFLINE", "NATURAL_CANDIDATE"}
INTELLIGENCE_CONTEXTS = {"CGX", "SAI"}


def plan_unispace_surface(
    surface: str = "SQUARESPACE_PUBLIC", *,
    transport: str = "CURRENT_HTTPS",
    intelligence: str = "CGX",
    jurisdiction: str = "UNVERIFIED",
    jurisdiction_attested: bool = False,
    sai_opt_in: bool = False,
    server_session_attested: bool = False,
    natural_transport_attested: bool = False,
    origin: str = "",
) -> dict:
    """Review-only view and transport selection over Cognigrex/CCC.

    Inputs describing attestations are caller assertions and NEVER create an
    authenticated session, network transport, regional authority or node lease.
    The true server-side resolver must independently verify the actual proofs.
    """
    if surface not in SURFACE_KINDS:
        raise ValueError("unknown existing user surface")
    if transport not in TRANSPORT_PREFERENCES:
        raise ValueError("unknown transport preference")
    if intelligence not in INTELLIGENCE_CONTEXTS:
        raise ValueError("unknown intelligence context")
    if jurisdiction not in ("AU", "OTHER", "UNVERIFIED"):
        raise ValueError("unknown declared jurisdiction")
    for name, flag in (("jurisdiction_attested", jurisdiction_attested),
                       ("sai_opt_in", sai_opt_in),
                       ("server_session_attested", server_session_attested),
                       ("natural_transport_attested", natural_transport_attested)):
        if type(flag) is not bool:
            raise ValueError(name + " must be boolean")
    chosen_origin = https_origin(origin)
    if surface == "SQUARESPACE_PUBLIC" and intelligence == "SAI":
        context_state = "HOLD_AUTHENTICATED_APP_REQUIRED"
    elif intelligence == "SAI" and not sai_opt_in:
        context_state = "HOLD_EXPLICIT_SAI_OPT_IN"
    elif intelligence == "SAI" and jurisdiction != "AU":
        context_state = "HOLD_AU_JURISDICTION_NOT_ESTABLISHED"
    elif intelligence == "SAI" and not jurisdiction_attested:
        context_state = "HOLD_TRUSTED_AU_ELIGIBILITY_PROOF"
    elif intelligence == "SAI":
        context_state = "SAI_REVIEW_BY_AUTHENTICATED_SERVER"
    else:
        context_state = "CGX_BASELINE_REVIEW"

    if transport == "OFFLINE":
        network_state = "LOCAL_OFFLINE_ONLY"
        profile = "WEB_OFFLINE"
        selected_origin = None
    elif transport == "NATURAL_CANDIDATE":
        # No physical/protocol endpoint or independently signed peer proof is
        # established by the planner, even when a caller asserts an attestation.
        network_state = ("HOLD_NATURAL_PEER_READBACK"
                         if natural_transport_attested
                         else "HOLD_NATURAL_TRANSPORT_PROTOCOL_AND_EVIDENCE")
        profile = "WEB_CONNECTED" if chosen_origin else "WEB_OFFLINE"
        selected_origin = chosen_origin or None
    else:
        network_state = ("HOLD_SERVER_AUTH_AND_ACL"
                         if chosen_origin else "HOLD_EXPLICIT_HTTPS_ORIGIN")
        profile = "WEB_CONNECTED" if chosen_origin else "WEB_OFFLINE"
        selected_origin = chosen_origin or None
    if surface == "SQUARESPACE_PUBLIC":
        network_state = ("PUBLIC_EMBED_READ_ONLY" if transport == "CURRENT_HTTPS"
                         else network_state)
        profile = "WEB_OFFLINE"
        selected_origin = None  # static iframe never discovers a private host
    return {
        "schema": "CGX-UNISPACE-SURFACE-ACCESS-PLAN/0.1",
        "status": "CANDIDATE_NOT_EXECUTED",
        "parent_root": "Cognigrex.cgx",
        "shared_capability_root": "Cognigrex.cgx:/ccc",
        "surface": surface,
        "requested_intelligence": intelligence,
        "intelligence_eligibility": context_state,
        "jurisdiction_declared": jurisdiction,
        "jurisdiction_verified_by_planner": False,
        "transport_preference": transport,
        "transport_state": network_state,
        "fallback_transport": "LOCAL_OFFLINE_OR_EXPLICIT_HTTPS",
        "device_profile": profile,
        "selected_https_origin": selected_origin,
        "connection_established": False,
        "natural_transport_established": False,
        "sai_activated": False,
        "authenticated": False,
        "contains_credentials": False,
        "source_bytes_embedded": False,
        "node_id": None,
        "lease_ref": None,
        "canonical_promotion": False,
        "public_publish_authorized": False,
        "owner_gates": ["ISSUE_158_PUBLIC_PRIVATE_BOUNDARY",
                        "ISSUE_161_NATIVE_TWO_NODE_READBACK",
                        "SIGNED_SESSION_ACL_AND_JURISDICTION",
                        "INDEPENDENT_NATURAL_TRANSPORT_QUALIFICATION"],
        "next_action": ("Use existing authenticated LS GO/UniSpace session and CGX "
                        "node-exchange after owner-approved server-side attestation. "
                        "Squarespace remains a static shell; no ambient region or "
                        "network signal grants authority."),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="WEB_OFFLINE")
    parser.add_argument("--budget", type=int, default=4096)
    parser.add_argument("--origin", default="")
    args = parser.parse_args()
    print(json.dumps(plan_passive_node(args.profile, budget_bytes=args.budget, origin=args.origin), indent=2))
