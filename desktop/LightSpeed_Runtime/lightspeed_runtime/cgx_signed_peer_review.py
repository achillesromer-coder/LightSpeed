"""CGX signed peer-review receipt seam over the EXISTING OperationalStore.

Ed25519 authenticates *test-key* review messages; it does not create
production identities, consensus, network transport, source rights, native DBR,
mint or autonomous authority. No secondary agent runtime or storage service.
"""
from __future__ import annotations
import hashlib
import json
import re
from contextlib import closing
from datetime import UTC, datetime, timedelta
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from lightspeed_runtime.operational_store import OperationalStore, OperationalConflict

SCHEMA = "cgx.signed_peer_review/0.1"
KIND = "cgx_signed_peer_review_v01"
GENESIS = "0" * 64
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_SHA = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED = frozenset(("schema", "origin", "recipient", "sequence", "predecessor_sha256",
    "subject_sha256", "source_rights", "created_utc", "expires_utc",
    "native_admitted", "signed_dbr", "source_bytes_included", "execution_authorised"))
_REVIEW = "OWNER_PRIVATE_REVIEW_ONLY"


class PeerReviewError(ValueError):
    pass


def canonical(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("ascii")


def digest(value: dict) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _identity(value):
    if type(value) is not str or not _ID.fullmatch(value):
        raise PeerReviewError("invalid peer identity")
    return value


def _datetime(value):
    if type(value) is not str:
        raise PeerReviewError("timestamp must be a string")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PeerReviewError("invalid timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
        raise PeerReviewError("timestamp must be UTC")
    return dt


def _scope(body, now):
    if type(body) is not dict or set(body) != _ALLOWED or body["schema"] != SCHEMA:
        raise PeerReviewError("unknown or incomplete signed review schema")
    source = _identity(body["origin"])
    target = _identity(body["recipient"])
    if source == target:
        raise PeerReviewError("same-node exchange is not a peer")
    if type(body["sequence"]) is not int or not 1 <= body["sequence"] <= 1000000:
        raise PeerReviewError("invalid sequence")
    if any(type(body[k]) is not str or not _SHA.fullmatch(body[k])
           for k in ("predecessor_sha256", "subject_sha256")):
        raise PeerReviewError("invalid hash identifier")
    if body["source_rights"] != _REVIEW:
        raise PeerReviewError("unqualified remote rights")
    if any(body[k] is not False for k in (
        "native_admitted", "signed_dbr", "source_bytes_included", "execution_authorised")):
        raise PeerReviewError("signed review cannot grant operational authority")
    created = _datetime(body["created_utc"])
    expires = _datetime(body["expires_utc"])
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise PeerReviewError("UTC verification clock required")
    if expires <= created or expires - created > timedelta(minutes=10):
        raise PeerReviewError("invalid review validity window")
    if now < created - timedelta(seconds=10) or now >= expires:
        raise PeerReviewError("expired or future-dated peer review")
    return source, target


def export_public_key(key: Ed25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)


def sign_review(key: Ed25519PrivateKey, *, origin: str, recipient: str,
                sequence: int, predecessor_sha256: str, subject_sha256: str,
                now: datetime) -> dict:
    if not isinstance(key, Ed25519PrivateKey):
        raise PeerReviewError("Ed25519 private key required for test signature")
    body = {
        "schema": SCHEMA, "origin": origin, "recipient": recipient,
        "sequence": sequence, "predecessor_sha256": predecessor_sha256,
        "subject_sha256": subject_sha256,
        "source_rights": _REVIEW,
        "created_utc": now.isoformat(),
        "expires_utc": (now + timedelta(minutes=3)).isoformat(),
        "native_admitted": False, "signed_dbr": False,
        "source_bytes_included": False, "execution_authorised": False,
    }
    _scope(body, now)
    packet = {"body": body, "signature_ed25519": key.sign(canonical(body)).hex()}
    return packet


def _event_id(origin: str, recipient: str, sequence: int) -> str:
    return "cgx-peer-review:" + hashlib.sha256(
        canonical({"origin": origin, "recipient": recipient, "sequence": sequence})
    ).hexdigest()


def _load(store: OperationalStore, event_id: str):
    # Existing canonical operational database and indexed event IDs only.
    with closing(store._connect()) as db:
        row = db.execute("SELECT payload_json,payload_sha256,kind "
                         "FROM operational_events WHERE event_id=?", (event_id,)).fetchone()
    if not row:
        return None
    raw, expected, kind = row
    if hashlib.sha256(raw.encode("utf-8")).hexdigest() != expected or kind != KIND:
        raise PeerReviewError("persisted event hash/kind mismatch")
    event = json.loads(raw)
    if event.get("event_id") != event_id or event.get("kind") != KIND:
        raise PeerReviewError("persisted event identity mismatch")
    return event


def accept_review(store: OperationalStore, packet: dict, *,
                  recipient: str, trust: Mapping[str, bytes],
                  now: datetime) -> dict:
    if type(packet) is not dict or set(packet) != {"body", "signature_ed25519"}:
        raise PeerReviewError("unknown packet fields")
    body = packet["body"]
    origin, target = _scope(body, now)
    if target != _identity(recipient):
        raise PeerReviewError("incorrect recipient")
    raw_key = trust.get(origin)
    if type(raw_key) is not bytes or len(raw_key) != 32:
        raise PeerReviewError("peer is not explicitly trusted")
    sig = packet["signature_ed25519"]
    if type(sig) is not str or not re.fullmatch(r"[0-9a-f]{128}", sig):
        raise PeerReviewError("signature encoding mismatch")
    try:
        Ed25519PublicKey.from_public_bytes(raw_key).verify(bytes.fromhex(sig), canonical(body))
    except (ValueError, InvalidSignature) as exc:
        raise PeerReviewError("invalid peer signature") from exc
    sequence = body["sequence"]
    event_id = _event_id(origin, target, sequence)
    if _load(store, event_id):
        raise PeerReviewError("duplicate/replayed review")
    if sequence == 1:
        if body["predecessor_sha256"] != GENESIS:
            raise PeerReviewError("noncanonical genesis")
    else:
        prev_id = _event_id(origin, target, sequence - 1)
        prev = _load(store, prev_id)
        if prev is None or body["predecessor_sha256"] != digest(prev["packet"]):
            raise PeerReviewError("missing or conflicting previous receipt")
    event = {
        "event_id": event_id, "kind": KIND,
        "source": origin, "target": target,
        "priority": "normal", "risk": "low",
        "status": "REVIEW_ONLY", "packet": packet,
        "execution_enabled": False, "source_lease_verified": False,
        "signed_dbr": False, "native_mint_authorized": False,
        "network_identity_issued": False,
    }
    try:
        outcome = store.record_event(event)
    except OperationalConflict as exc:
        raise PeerReviewError("conflicting persistent event") from exc
    if outcome.get("inserted") is not True:
        raise PeerReviewError("duplicate canonical operational event")
    recovered = _load(store, event_id)
    if recovered is None or recovered.get("packet") != packet:
        raise PeerReviewError("persistent packet readback mismatch")
    return {
        "schema": SCHEMA,
        "origin": origin, "recipient": target, "sequence": sequence,
        "packet_sha256": digest(packet), "event_id": event_id,
        "persisted_in_existing_operational_store": True,
        "signed_test_key_authenticated": True,
        "rights":"REVIEW_ONLY_NO_SOURCE_TRANSFER",
        "live_network_transport_verified": False,
        "independent_machine_operators_verified": False,
        "native_dbr_signed": False,
        "native_admitted": False,
        "production_identity_issued": False,
    }
