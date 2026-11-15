#!/usr/bin/env python3
"""Mutually pinned Ed25519 genesis attestation between LOCAL review processes.

No transaction, Object_ID, issuer, RootAuthority, consensus, independent-node
DBR or external network access is created or authorised by this test protocol.
Only source-hash/review challenge proofs are exchanged.
"""
from __future__ import annotations
import argparse
import base64
import binascii
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import time
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

from cgxEmptyGenesisDevnet import CHAIN_ID, canonical, read_state

SCHEMA = "CGX-TWO-PROCESS-GENESIS-PROOF/0.1"
REQUEST = "CGX-LOCAL-GENESIS-CHALLENGE/0.1"
RESPONSE = "CGX-LOCAL-GENESIS-ATTESTATION/0.1"
SCOPE = "genesis.readonly"
MAX_BODY = 2_048
TTL = 20


def _deny(message: str):
    raise ValueError(message)


def public_hex(private: Ed25519PrivateKey) -> str:
    return private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    ).hex()


def load_private(file: Path) -> Ed25519PrivateKey:
    file = Path(file)
    if not file.is_file() or file.is_symlink() or file.stat().st_size != 65:
        return _deny("IDENTITY_KEY_FILE_INVALID")
    try:
        data = file.read_text("ascii").strip()
        if len(data) != 64 or any(c not in "0123456789abcdef" for c in data):
            return _deny("IDENTITY_KEY_FORMAT_INVALID")
        return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(data))
    except (UnicodeError, ValueError) as err:
        raise ValueError("IDENTITY_KEY_FORMAT_INVALID") from err


def create_identity(folder: Path, name: str) -> dict:
    if name not in ("review_node_a", "review_node_b"):
        return _deny("REVIEW_IDENTITY_NAME_HOLD")
    folder = Path(folder)
    if folder.is_symlink():
        return _deny("IDENTITY_FOLDER_SYMLINK_HOLD")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (name + ".private.hex")
    if target.exists() or target.is_symlink():
        return _deny("IDENTITY_EXISTS_NO_OVERWRITE")
    key = Ed25519PrivateKey.generate()
    raw = key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    ).hex()
    descriptor = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as f:
            f.write(raw + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(target, 0o600)
    except BaseException:
        # Never report successful identity provisioning on an incomplete write.
        raise
    return {"schema": SCHEMA, "name": name, "public_key_hex": public_hex(key),
            "private_key_file": str(target),
            "authority": "EPHEMERAL_LOCAL_REVIEW_ONLY",
            "may_mint": False, "may_sign_root_authority": False}


def _parse_pin(value: str) -> Ed25519PublicKey:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        return _deny("PEER_PUBLIC_KEY_PIN_INVALID")
    return Ed25519PublicKey.from_public_bytes(bytes.fromhex(value))


def _sign(payload: dict, key: Ed25519PrivateKey) -> str:
    return base64.b64encode(key.sign(canonical(payload))).decode("ascii")


def _verify(payload: dict, signature: str, key: Ed25519PublicKey):
    if not isinstance(signature, str) or len(signature) > 120:
        return _deny("SIGNATURE_FORMAT_HOLD")
    try:
        signature_bytes = base64.b64decode(signature, validate=True)
        key.verify(signature_bytes, canonical(payload))
    except (ValueError, InvalidSignature, binascii.Error) as exc:
        raise ValueError("INVALID_PEER_SIGNATURE") from exc


def request_proof(genesis_hash: str, key: Ed25519PrivateKey, now: int | None = None) -> dict:
    t = int(time.time()) if now is None else now
    request = {
        "schema": REQUEST, "chain_id": CHAIN_ID,
        "genesis_sha256": genesis_hash,
        "scope": SCOPE,
        "nonce": secrets.token_hex(32),
        "issued_at": t, "expires_at": t + TTL,
        "subject_public_key": public_hex(key)
    }
    request["signature"] = _sign(request, key)
    return request


def _checked_request(doc: object, trusted_client_hex: str, genesis_hash: str, now: int):
    if not isinstance(doc, dict) or set(doc) != {
        "schema", "chain_id", "genesis_sha256", "scope", "nonce",
        "issued_at", "expires_at", "subject_public_key", "signature"
    }:
        return _deny("REQUEST_SHAPE_HOLD")
    if doc["schema"] != REQUEST or doc["chain_id"] != CHAIN_ID or doc["scope"] != SCOPE:
        return _deny("REQUEST_CHAIN_OR_SCOPE_HOLD")
    if doc["genesis_sha256"] != genesis_hash:
        return _deny("GENESIS_PIN_MISMATCH")
    if doc["subject_public_key"] != trusted_client_hex:
        return _deny("UNTRUSTED_CLIENT_IDENTITY")
    if not isinstance(doc["nonce"], str) or len(doc["nonce"]) != 64 or any(c not in "0123456789abcdef" for c in doc["nonce"]):
        return _deny("NONCE_INVALID")
    if (type(doc["issued_at"]) is not int or type(doc["expires_at"]) is not int or
            doc["expires_at"] - doc["issued_at"] != TTL or
            abs(now - doc["issued_at"]) > 5 or not now < doc["expires_at"]):
        return _deny("CHALLENGE_EXPIRED_OR_CLOCK_SKEW")
    sig = doc["signature"]
    unsigned = {k: v for k, v in doc.items() if k != "signature"}
    _verify(unsigned, sig, _parse_pin(trusted_client_hex))


def build_reply(doc: object, key: Ed25519PrivateKey, trusted_client_hex: str,
                genesis_hash: str, now: int, seen: set[str], lock: Lock) -> dict:
    _checked_request(doc, trusted_client_hex, genesis_hash, now)
    with lock:
        # Bounded replay cache; when full refuse instead of silently accepting old nonces.
        if doc["nonce"] in seen:
            return _deny("NONCE_REPLAY_HOLD")
        if len(seen) >= 2_048:
            return _deny("NONCE_CACHE_FULL_HOLD")
        seen.add(doc["nonce"])
    body = {
        "schema": RESPONSE, "chain_id": CHAIN_ID, "genesis_sha256": genesis_hash,
        "scope": SCOPE, "nonce": doc["nonce"],
        "issued_at": now, "expires_at": min(now + TTL, doc["expires_at"]),
        "server_public_key": public_hex(key),
        "subject_public_key": trusted_client_hex,
        "native_dbr_verified": False,
        "signed_root_authority": False,
        "mint_authorized": False,
        "consensus_verified": False,
        "network_scope": "127.0.0.1_only",
    }
    return {**body, "signature": _sign(body, key)}


def verify_reply(reply: object, request: dict, trusted_server_hex: str, now: int) -> dict:
    if not isinstance(reply, dict):
        return _deny("RESPONSE_SHAPE_HOLD")
    allowed = {
        "schema", "chain_id", "genesis_sha256", "scope", "nonce", "issued_at",
        "expires_at", "server_public_key", "subject_public_key", "native_dbr_verified",
        "signed_root_authority", "mint_authorized", "consensus_verified",
        "network_scope", "signature"
    }
    if set(reply) != allowed:
        return _deny("RESPONSE_SHAPE_HOLD")
    if (reply["schema"] != RESPONSE or reply["chain_id"] != request["chain_id"] or
        reply["genesis_sha256"] != request["genesis_sha256"] or
        reply["nonce"] != request["nonce"] or reply["scope"] != SCOPE or
        reply["subject_public_key"] != request["subject_public_key"] or
        reply["server_public_key"] != trusted_server_hex):
        return _deny("RESPONSE_NOT_BOUND_TO_REQUEST")
    if (type(reply["issued_at"]) is not int or type(reply["expires_at"]) is not int or
        not reply["issued_at"] <= now <= reply["expires_at"] or
        reply["expires_at"] > request["expires_at"] or
        reply["expires_at"] - reply["issued_at"] > TTL):
        return _deny("RESPONSE_EXPIRED_OR_CLOCK_SKEW")
    for field in ("native_dbr_verified", "signed_root_authority", "mint_authorized", "consensus_verified"):
        if reply[field] is not False:
            return _deny("REVIEW_AUTHORITY_ESCALATION_HOLD")
    if reply["network_scope"] != "127.0.0.1_only":
        return _deny("NONLOCAL_SCOPE_HOLD")
    unsigned = {k: v for k, v in reply.items() if k != "signature"}
    _verify(unsigned, reply["signature"], _parse_pin(trusted_server_hex))
    return {
        "schema": SCHEMA,
        "state": "LOCAL_MUTUAL_PINNED_GENESIS_PROOF_ONLY",
        "chain_id": CHAIN_ID,
        "genesis_sha256": reply["genesis_sha256"],
        "client_key_fingerprint_sha256": hashlib.sha256(bytes.fromhex(request["subject_public_key"])).hexdigest(),
        "server_key_fingerprint_sha256": hashlib.sha256(bytes.fromhex(trusted_server_hex)).hexdigest(),
        "challenge_nonce_sha256": hashlib.sha256(bytes.fromhex(request["nonce"])).hexdigest(),
        "expires_at": reply["expires_at"],
        "verified_ed25519": True,
        "independent_dbr": False,
        "issuer_verified": False,
        "mint_authorized": False,
        "native_admission": False,
        "public_network": False,
    }


def make_handler(genesis_file: Path, private: Ed25519PrivateKey, trusted_client_hex: str):
    peer = _parse_pin(trusted_client_hex)
    del peer
    seen: set[str] = set()
    lock = Lock()
    class Handler(BaseHTTPRequestHandler):
        server_version = "CGXPeerReview/0.1"
        sys_version = ""

        def reply(self, status: int, body: dict):
            payload = canonical(body)
            self.send_response(status)
            for k, v in (
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(payload))),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ):
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path != "/health":
                return self.reply(404, {"state": "HOLD", "reason": "PATH_NOT_ALLOWED"})
            try:
                genesis = read_state(genesis_file)
                return self.reply(200, {"state": "LOCAL_PEER_REVIEW_ONLY",
                                        "genesis_sha256": genesis["genesis_sha256"],
                                        "native_dbr": False})
            except (ValueError, OSError):
                return self.reply(503, {"state": "HOLD", "reason": "GENESIS_INTEGRITY_FAILED"})

        def do_POST(self):
            if self.path != "/attest":
                return self.reply(405, {"state": "HOLD", "reason": "TRANSACTIONS_DISABLED"})
            size = self.headers.get("Content-Length")
            if size is None or len(size) > 5 or not size.isascii() or not size.isdecimal() or not 1 <= int(size) <= MAX_BODY:
                return self.reply(413, {"state": "HOLD", "reason": "REQUEST_TOO_LARGE_OR_MISSING"})
            try:
                doc = json.loads(self.rfile.read(int(size)))
                genesis = read_state(genesis_file)
                response = build_reply(doc, private, trusted_client_hex,
                                       genesis["genesis_sha256"], int(time.time()),
                                       seen, lock)
            except (ValueError, OSError, json.JSONDecodeError) as exc:
                # Never reveal private keys, file paths, or full exception payloads.
                return self.reply(403, {"state": "HOLD", "reason": type(exc).__name__})
            return self.reply(200, response)

        def do_PUT(self):
            return self.reply(405, {"state": "HOLD", "reason": "TRANSACTIONS_DISABLED"})
        do_PATCH = do_PUT
        do_DELETE = do_PUT

        def log_message(self, *_):
            pass

    return Handler


def probe(state_file: Path, client_key_file: Path, server_key_hex: str, port: int) -> dict:
    if not isinstance(port, int) or not 18000 <= port <= 65535:
        return _deny("INVALID_LOOPBACK_PORT")
    _parse_pin(server_key_hex)
    record = read_state(state_file)
    client = load_private(client_key_file)
    req = request_proof(record["genesis_sha256"], client)
    data = canonical(req)
    with urlopen(Request(f"http://127.0.0.1:{port}/attest", data=data,
                         headers={"Content-Type": "application/json"},
                         method="POST"), timeout=5) as response:
        if response.status != 200:
            return _deny("PEER_ATTESTATION_NOT_ACCEPTED")
        encoded = response.read(MAX_BODY + 1)
    if len(encoded) > MAX_BODY:
        return _deny("PEER_RESPONSE_TOO_LARGE")
    result = verify_reply(json.loads(encoded), req, server_key_hex, int(time.time()))
    # Detect source genesis changes between local proof preparation and verification.
    if read_state(state_file)["genesis_sha256"] != result["genesis_sha256"]:
        return _deny("CLIENT_GENESIS_CHANGED_DURING_PROBE")
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("keygen", "serve", "probe"))
    p.add_argument("--state", type=Path)
    p.add_argument("--private-key", type=Path)
    p.add_argument("--key-dir", type=Path)
    p.add_argument("--name")
    p.add_argument("--trusted-peer-key")
    p.add_argument("--port", type=int, default=18842)
    args = p.parse_args()
    try:
        if args.action == "keygen":
            if args.key_dir is None:
                return _deny("KEY_DIRECTORY_REQUIRED")
            result = create_identity(args.key_dir, args.name)
        elif args.action == "serve":
            if args.state is None or args.private_key is None:
                return _deny("STATE_AND_KEY_REQUIRED")
            if not 18000 <= args.port <= 65535:
                return _deny("INVALID_LOOPBACK_PORT")
            _parse_pin(args.trusted_peer_key)
            read_state(args.state)
            key = load_private(args.private_key)
            server = ThreadingHTTPServer(("127.0.0.1", args.port),
                                         make_handler(args.state, key, args.trusted_peer_key))
            server.daemon_threads = True
            try:
                server.serve_forever(poll_interval=0.25)
            finally:
                server.server_close()
            return 0
        else:
            if args.state is None or args.private_key is None:
                return _deny("STATE_AND_KEY_REQUIRED")
            result = probe(args.state, args.private_key, args.trusted_peer_key, args.port)
    except (ValueError, OSError, HTTPError, URLError, json.JSONDecodeError) as exc:
        print(json.dumps({"state": "HOLD", "error_class": type(exc).__name__,
                          "mint_authorized": False, "independent_dbr": False}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
