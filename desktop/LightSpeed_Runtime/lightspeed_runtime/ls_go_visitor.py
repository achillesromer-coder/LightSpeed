"""Permission-scoped LS GO visitor review adapter; shares the existing bridge and database.
No source catalogue, CAD files, machine controls, or canonical CGX roots are exposed.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any, Callable

from fastapi import FastAPI, Header, HTTPException

SCHEMA = "LS-GO-CGX-VISITOR/0.1"
LENSES = {"neo", "athene", "achilles", "alexandria"}
THEMES = {"orbit", "forest", "blueprint", "dawn"}
EVENT_KINDS = {"question", "model_request", "selection", "feedback", "session_start", "linked_url"}
PROJECTION_SET_SCHEMA = "CGX-LS-GO-PUBLIC-PROJECTION-SET/0.1"
PROJECTION_PAYLOAD_KEYS = {"title", "summary", "evidence_stage", "limitations", "citations", "model"}
PROJECTION_RELEASE_KEYS = {
    "release_class", "target_visibility", "release_approval_state",
    "source_release_classes", "contains_restricted_material", "release_receipt_ref",
}
PROJECTION_KEYS = {
    "projection_id", "object_id", "lens", "source_sha256", "source_revision",
    "projection_sha256", "release", "payload",
}
EVIDENCE_STAGES = {
    "CONCEPT", "SOURCE_BACKED", "SIMULATED", "MEASURED",
    "INDEPENDENTLY_ACCEPTED", "PUBLICLY_RELEASED",
}
LOCK = threading.RLock()


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def bound(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


def _canonical_payload_sha(value: dict) -> str:
    packed = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(packed.encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in value)


def _safe_https_url(value: Any) -> bool:
    if not isinstance(value, str) or len(value) > 500:
        return False
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        return (
            parsed.scheme == "https"
            and bool(host) and "." in host
            and host not in {"localhost", "127.0.0.1", "0.0.0.0"}
            and not host.endswith((".local", ".internal", ".localhost"))
            and parsed.port in {None, 443}
            and not parsed.username and not parsed.password
            and not parsed.query and not parsed.fragment
            and not host.replace(".", "").isdigit()
        )
    except ValueError:
        return False


def _projection_payload_is_public(payload: Any) -> bool:
    if not isinstance(payload, dict) or not {"title", "summary", "evidence_stage", "limitations"} <= set(payload):
        return False
    if set(payload) - PROJECTION_PAYLOAD_KEYS:
        return False
    title, summary = payload.get("title"), payload.get("summary")
    if not isinstance(title, str) or not title.strip() or len(title) > 160:
        return False
    if not isinstance(summary, str) or not summary.strip() or len(summary) > 4000:
        return False
    if payload.get("evidence_stage") not in EVIDENCE_STAGES:
        return False
    limitations = payload.get("limitations")
    if not isinstance(limitations, list) or len(limitations) > 20 or any(
        not isinstance(item, str) or not item.strip() or len(item) > 500 for item in limitations
    ):
        return False
    citations = payload.get("citations", [])
    if not isinstance(citations, list) or len(citations) > 20:
        return False
    for citation in citations:
        if not isinstance(citation, dict) or set(citation) != {"label", "url", "source_sha256", "revision"}:
            return False
        if not bound(citation.get("label"), 160) or not bound(citation.get("revision"), 160):
            return False
        if not _safe_https_url(citation.get("url")) or not _is_sha256(citation.get("source_sha256")):
            return False
    model = payload.get("model")
    if model is not None:
        required = {"kind", "url", "sha256", "media_type", "representation_class"}
        if not isinstance(model, dict) or set(model) != required:
            return False
        if model.get("kind") not in {"mesh", "render", "diagram", "model"}:
            return False
        if model.get("media_type") not in {
            "model/gltf-binary", "model/gltf+json", "image/svg+xml", "image/png", "image/webp"
        }:
            return False
        if not _safe_https_url(model.get("url")) or not _is_sha256(model.get("sha256")):
            return False
        if not bound(model.get("representation_class"), 120):
            return False
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden = (
        "Cognigrex.cgx", "LightSpeed_Runtime", "cgx_object_review_catalogue",
        "cgx_internal_review_projection", "review/renders/", "file://",
    )
    if any(marker.lower() in serialized.lower() for marker in forbidden):
        return False
    if any(f"{letter}:\\" in serialized for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"):
        return False
    return True


def _load_public_projection(manifest_path: str, object_id: str, lens: str) -> dict | None:
    if not manifest_path or not object_id or lens not in LENSES:
        return None
    try:
        source = Path(manifest_path)
        if source.suffix.lower() != ".json" or not source.is_file():
            return None
        manifest = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(manifest, dict):
        return None
    if manifest.get("schema") != PROJECTION_SET_SCHEMA or manifest.get("state") != "OWNER_SUPPLIED_PUBLIC_SAFE_PROJECTION_SET":
        return None
    projections = manifest.get("projections")
    if not isinstance(projections, list):
        return None
    matches = [
        item for item in projections
        if isinstance(item, dict) and item.get("object_id") == object_id and item.get("lens") == lens
    ]
    if len(matches) != 1:
        return None
    item = matches[0]
    if set(item) != PROJECTION_KEYS:
        return None
    if not bound(item.get("projection_id"), 160) or not bound(item.get("source_revision"), 160):
        return None
    if not _is_sha256(item.get("source_sha256")) or not _is_sha256(item.get("projection_sha256")):
        return None
    release = item.get("release")
    if not isinstance(release, dict) or set(release) != PROJECTION_RELEASE_KEYS:
        return None
    source_classes = release.get("source_release_classes")
    release_ref = release.get("release_receipt_ref")
    if (
        release.get("release_class") != "Public"
        or release.get("target_visibility") != "public"
        or release.get("release_approval_state") != "APPROVED"
        or not isinstance(source_classes, list) or not source_classes
        or any(value != "Public" for value in source_classes)
        or release.get("contains_restricted_material") is not False
        or not isinstance(release_ref, str) or not release_ref.strip() or len(release_ref) > 240
        or "\\" in release_ref or release_ref.lower().startswith("file:")
        or not (
            release_ref.startswith("public-receipt:")
            or (release_ref.startswith("https://") and _safe_https_url(release_ref))
        )
    ):
        return None
    payload = item.get("payload")
    if not _projection_payload_is_public(payload):
        return None
    if not hmac.compare_digest(_canonical_payload_sha(payload), str(item["projection_sha256"]).lower()):
        return None
    return {
        "projection_id": item["projection_id"],
        "object_id": object_id,
        "lens": lens,
        "source_sha256": str(item["source_sha256"]).lower(),
        "source_revision": item["source_revision"],
        "projection_sha256": str(item["projection_sha256"]).lower(),
        "release_receipt_ref": release_ref,
        "payload": payload,
    }


def register_visitor_routes(
    app: FastAPI, database: Any, owner_guard: Callable[[str | None], str],
) -> None:
    """Install in the existing LS GO bridge, fail closed until the approved schema is present."""
    enabled = os.environ.get("LIGHTSPEED_VISITOR_REVIEW_ENABLED") == "1"
    signing_key = os.environ.get("LIGHTSPEED_VISITOR_RECEIPT_KEY", "")
    projection_manifest_path = os.environ.get("LIGHTSPEED_VISITOR_PUBLIC_PROJECTION_MANIFEST", "").strip()
    privacy_policy_accepted = os.environ.get("LIGHTSPEED_VISITOR_PRIVACY_POLICY_ACCEPTED") == "1"
    privacy_policy_ref = os.environ.get("LIGHTSPEED_VISITOR_PRIVACY_POLICY_REF", "").strip()

    def _privacy_policy_ref_valid() -> bool:
        if not privacy_policy_ref or len(privacy_policy_ref) > 240:
            return False
        if "\\" in privacy_policy_ref or privacy_policy_ref.lower().startswith("file:"):
            return False
        return (
            privacy_policy_ref.startswith("owner-policy:")
            or (privacy_policy_ref.startswith("https://") and _safe_https_url(privacy_policy_ref))
        )

    def ready() -> None:
        if not enabled or database is None or len(signing_key) < 32:
            raise HTTPException(503, "Visitor review is held pending owner-enabled storage and signing")
        try:
            database.execute_query("SELECT reviewer_id FROM ls_go_visitor_profiles LIMIT 0")
            database.execute_query("SELECT invite_id FROM ls_go_visitor_invites LIMIT 0")
            database.execute_query("SELECT event_id FROM ls_go_visitor_events LIMIT 0")
        except Exception as exc:
            raise HTTPException(503, "Visitor schema migration not accepted") from exc

    def admission_ready() -> None:
        ready()
        if not privacy_policy_accepted or not _privacy_policy_ref_valid():
            raise HTTPException(
                503,
                "Visitor admission is held pending explicit owner-accepted privacy policy reference",
            )

    def rows(query: str, params: tuple = ()) -> list[dict]:
        return [dict(r) for r in database.execute_query(query, params)]

    def write(query: str, params: tuple = ()) -> None:
        database.execute_update(query, params)

    def receipt(reviewer_id: str, event: str, data: dict) -> dict:
        # A review-specific append chain, NOT an authoritative CGX/DBR root transition.
        with LOCK:
            previous = rows(
                "SELECT event_hash FROM ls_go_visitor_events WHERE reviewer_id = ? ORDER BY sequence DESC LIMIT 1",
                (reviewer_id,),
            )
            prev = previous[0]["event_hash"] if previous else "GENESIS"
            record = {
                "schema": SCHEMA, "reviewer_id": reviewer_id,
                "event_type": event, "recorded_utc": utc(), "previous_hash": prev,
                "payload": data,
            }
            encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            record_hash = sha(encoded)
            signature = hmac.new(signing_key.encode(), record_hash.encode(), hashlib.sha256).hexdigest()
            event_id = secrets.token_hex(16)
            write(
                "INSERT INTO ls_go_visitor_events(event_id, reviewer_id, event_type, recorded_utc, payload_json, previous_hash, event_hash, event_hmac) VALUES (?,?,?,?,?,?,?,?)",
                (event_id, reviewer_id, event, record["recorded_utc"], json.dumps(data, ensure_ascii=False), prev, record_hash, signature),
            )
            return {"event_id": event_id, "event_hash": record_hash, "previous_hash": prev,
                    "state": "REVIEW_LOCAL_ONLY", "canonical_cgx_ingestion": False}

    def visitor(session: str | None) -> dict:
        ready()
        if not session or len(session) > 256:
            raise HTTPException(401, "Visitor sign-in required")
        found = rows(
            "SELECT s.reviewer_id, s.expires_utc, s.revoked_utc, p.name, p.theme, p.lens, p.handshake_json "
            "FROM ls_go_visitor_sessions s JOIN ls_go_visitor_profiles p ON p.reviewer_id=s.reviewer_id "
            "WHERE s.session_sha256=? LIMIT 1", (sha(session),),
        )
        if not found or found[0]["revoked_utc"] or found[0]["expires_utc"] <= utc():
            raise HTTPException(401, "Visitor session expired or revoked")
        return found[0]

    @app.get("/api/v1/visitor/capabilities")
    async def capabilities():
        # Public orientation only; actual storage/signing readiness is checked.
        try:
            ready()
            available = True
        except HTTPException:
            available = False
        try:
            admission_ready()
            admission_available = True
        except HTTPException:
            admission_available = False
        return {
            "schema": SCHEMA, "enabled": available,
            "admission_enabled": admission_available,
            "privacy_policy_state": (
                "OWNER_ACCEPTED_REFERENCE_PRESENT"
                if privacy_policy_accepted and _privacy_policy_ref_valid()
                else "OWNER_ACCEPTANCE_REQUIRED"
            ),
            "roles": ["visitor"], "lenses": sorted(LENSES), "themes": sorted(THEMES),
            "identity_assurance": "INVITATION_POSSESSION_ONLY",
            "public_cgx_url": "https://romer.industries/cgx",
            "resolver_state": "PREAPPROVED_PUBLIC_PROJECTION_ONLY",
            "projection_manifest_configured": bool(projection_manifest_path),
            "public_model_state": "PREAPPROVED_METADATA_ONLY",
            "source_mutation": False, "machine_execution": False,
            "remote_source_fetch": False, "canonical_cgx_ingestion": False,
        }

    @app.post("/api/v1/visitor/invites")
    async def issue_invite(body: dict, x_lightspeed_session: str | None = Header(None)):
        admission_ready()
        owner_guard(x_lightspeed_session)
        reviewer_id = bound(body.get("reviewer_id"), 90) or "RV-" + secrets.token_hex(7)
        # A finite owner-approved four-place panel; renew an existing seat without minting a fifth.
        with LOCK:
            existing = rows("SELECT reviewer_id FROM ls_go_visitor_invites WHERE reviewer_id=?", (reviewer_id,))
            count = rows("SELECT COUNT(DISTINCT reviewer_id) AS n FROM ls_go_visitor_invites")[0]["n"]
            if not existing and int(count) >= 4:
                raise HTTPException(409, "Four reviewer seats already provisioned")
            write("UPDATE ls_go_visitor_invites SET revoked_utc=? WHERE reviewer_id=? AND redeemed_utc IS NULL AND revoked_utc IS NULL",
                  (utc(), reviewer_id))
            raw = secrets.token_urlsafe(32)
            invite_id = "INV-" + secrets.token_hex(8)
            expiry = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(timespec="seconds")
            write("INSERT INTO ls_go_visitor_invites(invite_id, reviewer_id, token_sha256, expiry_utc, redeemed_utc, revoked_utc) VALUES (?,?,?,?,NULL,NULL)",
                  (invite_id, reviewer_id, sha(raw), expiry))
        return {"invite_id": invite_id, "reviewer_id": reviewer_id, "invite_token": raw,
                "expires_utc": expiry, "one_time": True, "share_privately": True}

    @app.post("/api/v1/visitor/enroll")
    async def enroll(body: dict):
        admission_ready()
        raw = bound(body.get("invite_token"), 200)
        name = bound(body.get("name"), 72)
        theme = body.get("theme")
        lens = body.get("lens", "achilles")
        if len(raw) < 24 or not 2 <= len(name) <= 72 or not all(c.isalnum() or c in " ._'-" for c in name):
            raise HTTPException(400, "Invitation and valid display name required")
        if theme not in THEMES or lens not in LENSES or body.get("consent") is not True:
            raise HTTPException(400, "Theme, lens and explicit recording consent required")
        background = bound(body.get("background"), 500)
        intent = bound(body.get("intent"), 500)
        with LOCK:
            found = rows("SELECT * FROM ls_go_visitor_invites WHERE token_sha256=? LIMIT 1", (sha(raw),))
            if not found or found[0]["redeemed_utc"] or found[0]["revoked_utc"] or found[0]["expiry_utc"] <= utc():
                raise HTTPException(403, "Invite invalid, expired, revoked or previously used")
            reviewer_id = found[0]["reviewer_id"]
            if rows("SELECT reviewer_id FROM ls_go_visitor_profiles WHERE reviewer_id=?", (reviewer_id,)):
                # Existing session/profile can be renewed only through an owner-issued fresh invitation.
                write("UPDATE ls_go_visitor_profiles SET name=?, theme=?, lens=?, handshake_json=? WHERE reviewer_id=?",
                      (name, theme, lens, json.dumps({"background": background, "intent": intent}), reviewer_id))
            else:
                write("INSERT INTO ls_go_visitor_profiles(reviewer_id,name,theme,lens,handshake_json,consent_utc) VALUES (?,?,?,?,?,?)",
                      (reviewer_id, name, theme, lens, json.dumps({"background": background, "intent": intent}), utc()))
            write("UPDATE ls_go_visitor_invites SET redeemed_utc=? WHERE invite_id=? AND redeemed_utc IS NULL",
                  (utc(), found[0]["invite_id"]))
            session = secrets.token_urlsafe(40)
            expiry = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat(timespec="seconds")
            write("INSERT INTO ls_go_visitor_sessions(session_sha256,reviewer_id,expires_utc,revoked_utc) VALUES (?,?,?,NULL)",
                  (sha(session), reviewer_id, expiry))
            event = receipt(reviewer_id, "session_start",
                {"theme": theme, "lens": lens, "consent": True, "identity_assurance": "INVITATION_POSSESSION_ONLY"})
        return {"schema": SCHEMA, "reviewer_id": reviewer_id, "visitor_session": session,
                "expires_utc": expiry, "profile": {"name": name, "theme": theme, "lens": lens,
                "background": background, "intent": intent},
                "receipt": event, "identity_assurance": "INVITATION_POSSESSION_ONLY"}

    @app.get("/api/v1/visitor/me")
    async def whoami(x_lightspeed_visitor_session: str | None = Header(None)):
        p = visitor(x_lightspeed_visitor_session)
        return {"schema": SCHEMA, "reviewer_id": p["reviewer_id"], "name": p["name"],
                "theme": p["theme"], "lens": p["lens"],
                "handshake": json.loads(p["handshake_json"]),
                "identity_assurance": "INVITATION_POSSESSION_ONLY"}

    @app.post("/api/v1/visitor/interaction")
    async def interaction(body: dict, x_lightspeed_visitor_session: str | None = Header(None)):
        p = visitor(x_lightspeed_visitor_session)
        kind, lens = body.get("kind", "question"), body.get("lens", p["lens"])
        content = bound(body.get("text"), 2000)
        object_id = bound(body.get("object_id"), 120)
        if kind not in EVENT_KINDS or lens not in LENSES or (not content and kind != "selection"):
            raise HTTPException(400, "Invalid visitor interaction")
        count = rows("SELECT COUNT(*) AS n FROM ls_go_visitor_events WHERE reviewer_id=? AND event_type IN ('question','model_request','feedback')",
                     (p["reviewer_id"],))
        if int(count[0]["n"]) >= 200:
            raise HTTPException(429, "Review interaction limit reached; owner review required")
        linked = {}
        if kind == "linked_url":
            raw_url = bound(body.get("text"), 500)
            try:
                parsed_url = urlsplit(raw_url)
                host = (parsed_url.hostname or "").lower()
                allowed = (
                    parsed_url.scheme == "https"
                    and bool(host) and "." in host
                    and host not in {"localhost", "127.0.0.1", "0.0.0.0"}
                    and not host.endswith((".local", ".internal", ".localhost"))
                    and parsed_url.port in {None, 443}
                    and not parsed_url.username and not parsed_url.password
                    and not parsed_url.query and not parsed_url.fragment
                    and not host.replace(".", "").isdigit()
                )
            except ValueError:
                allowed = False
            provider = bound(body.get("provider"), 32).lower()
            if not allowed or provider not in {"github", "google", "microsoft", "canva", "linkedin", "other"}:
                raise HTTPException(400, "Only safe HTTPS profile URLs without query, credentials or fragments are accepted")
            linked = {"provider": provider, "verification_state": "LINK_SUBMITTED_UNVERIFIED",
                      "external_login_performed": False, "url_fetch_performed": False}
        # Resolve only exact, already-approved Public derived projections. No private hydration,
        # arbitrary fetch, tool execution, on-demand AI answer or model generation is implied.
        projection = (
            _load_public_projection(projection_manifest_path, object_id, lens)
            if kind in {"question", "model_request"} and object_id else None
        )
        if projection:
            payload = projection["payload"]
            result = {
                "kind": kind, "lens": lens, "text": content, "object_id": object_id,
                "status": "PUBLIC_SAFE_PROJECTION", "evidence_stage": payload["evidence_stage"],
                "public_safe": True, "source_mutation": False, "model_generated": False,
                "projection_id": projection["projection_id"],
                "projection_sha256": projection["projection_sha256"],
                "source_sha256": projection["source_sha256"],
                "source_revision": projection["source_revision"],
                "release_receipt_ref": projection["release_receipt_ref"],
                **linked,
            }
            answer = payload["summary"] if kind == "question" else None
            model = payload.get("model") if kind == "model_request" else None
            limitations = payload["limitations"]
            citations = payload.get("citations", [])
        else:
            result = {"kind": kind, "lens": lens, "text": content,
                      "object_id": object_id, "status": "PENDING_PUBLIC_SAFE_RESOLVER",
                      "evidence_stage": "CONCEPT", "public_safe": False,
                      "source_mutation": False, "model_generated": False, **linked}
            answer, model, limitations, citations = None, None, [], []
        event = receipt(p["reviewer_id"], kind, result)
        if lens != p["lens"] and kind == "selection":
            write("UPDATE ls_go_visitor_profiles SET lens=? WHERE reviewer_id=?", (lens, p["reviewer_id"]))
        return {"schema": SCHEMA, "status": result["status"], "receipt": event,
                "answer": answer, "model": model, "evidence_stage": result["evidence_stage"],
                "public_safe": result["public_safe"], "limitations": limitations, "citations": citations,
                "projection_id": result.get("projection_id"),
                "projection_sha256": result.get("projection_sha256"),
                "source_sha256": result.get("source_sha256"),
                "release_receipt_ref": result.get("release_receipt_ref"),
                "link_verification_state": linked.get("verification_state")}

    @app.post("/api/v1/visitor/surface")
    async def read_surface(body: dict, x_lightspeed_visitor_session: str | None = Header(None)):
        """One public-safe CGX object facet, for reusable visitor windows and web embeds.

        Uses the EXISTING owner-approved projection manifest, not a new object,
        cache, renderer, FileSpace resolver, DBR root, or execution service.
        """
        visitor(x_lightspeed_visitor_session)
        permitted_fields = {"object_id", "lens", "view_id", "requested_valid_at", "requested_recorded_at"}
        if not isinstance(body, dict) or set(body) - permitted_fields:
            raise HTTPException(400, "Unsupported surface selector")
        object_id = body.get("object_id")
        lens = body.get("lens")
        view_id = body.get("view_id", "overview")
        valid_views = {"overview", "evidence", "model", "map", "timeline"}
        if (
            not isinstance(object_id, str)
            or not 1 <= len(object_id) <= 120
            or not all(c.isalnum() or c in "._:-" for c in object_id)
            or lens not in LENSES or view_id not in valid_views
        ):
            raise HTTPException(400, "Invalid exact object, lens or view selection")
        if body.get("requested_valid_at") is not None or body.get("requested_recorded_at") is not None:
            raise HTTPException(409, "Historic snapshot held: no admitted bitemporal public manifest")
        if view_id in {"map", "timeline"}:
            return {
                "schema": SCHEMA, "status": "SURFACE_NOT_RELEASED",
                "view_id": view_id, "public_safe": False, "payload": None,
                "canonical_cgx_ingestion": False, "machine_execution": False,
            }
        projection = _load_public_projection(projection_manifest_path, object_id, lens)
        if projection is None:
            return {
                "schema": SCHEMA, "status": "PENDING_PUBLIC_SAFE_RESOLVER",
                "view_id": view_id, "public_safe": False, "payload": None,
                "canonical_cgx_ingestion": False, "machine_execution": False,
            }
        approved = projection["payload"]
        if view_id == "model" and not approved.get("model"):
            return {
                "schema": SCHEMA, "status": "SURFACE_NOT_RELEASED",
                "view_id": view_id, "public_safe": False, "payload": None,
                "canonical_cgx_ingestion": False, "machine_execution": False,
            }
        visible_fields = {"title", "summary", "evidence_stage", "limitations", "citations"}
        if view_id == "model":
            visible_fields.add("model")
        projection_payload = {key: value for key, value in approved.items() if key in visible_fields}
        return {
            "schema": SCHEMA, "status": "PUBLIC_SAFE_PROJECTION",
            "view_id": view_id, "object_id": object_id, "lens": lens,
            "public_safe": True, "payload": projection_payload,
            "projection_id": projection["projection_id"],
            "projection_sha256": projection["projection_sha256"],
            "source_sha256": projection["source_sha256"],
            "source_revision": projection["source_revision"],
            "release_receipt_ref": projection["release_receipt_ref"],
            "canonical_cgx_ingestion": False, "machine_execution": False,
        }

    @app.post("/api/v1/visitor/privacy-request")
    async def privacy_request(body: dict, x_lightspeed_visitor_session: str | None = Header(None)):
        p = visitor(x_lightspeed_visitor_session)
        action = body.get("action")
        if action not in {"export", "erasure", "withdraw_consent"}:
            raise HTTPException(400, "Privacy request must be export, erasure, or withdraw_consent")
        record = receipt(p["reviewer_id"], "privacy_request",
                         {"action": action, "status": "OWNER_REVIEW_REQUIRED"})
        if action == "withdraw_consent":
            write("UPDATE ls_go_visitor_sessions SET revoked_utc=? WHERE reviewer_id=? AND revoked_utc IS NULL",
                  (utc(), p["reviewer_id"]))
            write("UPDATE ls_go_visitor_invites SET revoked_utc=? WHERE reviewer_id=? AND redeemed_utc IS NULL AND revoked_utc IS NULL",
                  (utc(), p["reviewer_id"]))
        return {"schema": SCHEMA, "request": action, "state": "OWNER_REVIEW_REQUIRED",
                "receipt": record, "automated_deletion_performed": False}
    @app.post("/api/v1/visitor/logout")
    async def logout(x_lightspeed_visitor_session: str | None = Header(None)):
        visitor(x_lightspeed_visitor_session)
        write("UPDATE ls_go_visitor_sessions SET revoked_utc=? WHERE session_sha256=?",
              (utc(), sha(x_lightspeed_visitor_session or "")))
        return {"schema": SCHEMA, "session_active": False}

    @app.post("/api/v1/visitor/revoke")
    async def revoke_reviewer(body: dict, x_lightspeed_session: str | None = Header(None)):
        ready()
        owner_guard(x_lightspeed_session)
        reviewer_id = bound(body.get("reviewer_id"), 90)
        if not reviewer_id:
            raise HTTPException(400, "Reviewer ID required")
        write("UPDATE ls_go_visitor_sessions SET revoked_utc=? WHERE reviewer_id=? AND revoked_utc IS NULL",
              (utc(), reviewer_id))
        write("UPDATE ls_go_visitor_invites SET revoked_utc=? WHERE reviewer_id=? AND redeemed_utc IS NULL AND revoked_utc IS NULL",
              (utc(), reviewer_id))
        return {"schema": SCHEMA, "reviewer_id": reviewer_id, "revoked": True}

    @app.get("/api/v1/visitor/owner-review")
    async def owner_review(x_lightspeed_session: str | None = Header(None)):
        ready()
        owner_guard(x_lightspeed_session)
        profiles = rows("SELECT reviewer_id,name,theme,lens,handshake_json,consent_utc FROM ls_go_visitor_profiles ORDER BY reviewer_id")
        events = rows("SELECT sequence,event_id,reviewer_id,event_type,recorded_utc,payload_json,previous_hash,event_hash,event_hmac FROM ls_go_visitor_events ORDER BY sequence")
        chain_verified = True
        last_hash: dict[str, str] = {}
        for item in events:
            reviewer = item["reviewer_id"]
            previous = last_hash.get(reviewer, "GENESIS")
            try:
                data = json.loads(item["payload_json"])
                value = {
                    "schema": SCHEMA, "reviewer_id": reviewer,
                    "event_type": item["event_type"],
                    "recorded_utc": item["recorded_utc"],
                    "previous_hash": item["previous_hash"],
                    "payload": data,
                }
                packed = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                computed = sha(packed)
                expected_hmac = hmac.new(signing_key.encode(), computed.encode(), hashlib.sha256).hexdigest()
                if (item["previous_hash"] != previous or computed != item["event_hash"] or
                        not hmac.compare_digest(expected_hmac, item["event_hmac"])):
                    chain_verified = False
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                chain_verified = False
            last_hash[reviewer] = item["event_hash"]
        return {"schema": SCHEMA, "profiles": profiles, "events": events,
                "chain_verified": chain_verified,
                "canonical_cgx_ingestion": False, "proof_scope": "LS_GO_VISITOR_RECEIPT_ONLY"}
