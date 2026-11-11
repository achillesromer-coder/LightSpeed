#!/usr/bin/env python3
"""Local, genesis-only CGX development chain for non-issuing integration tests.

This process is NOT the Cognigrex parent, native DBR, consensus, mint, issuer,
on-chain deployment, wallet, or an authority-granting service. Read-only and
strictly bound to the host loopback; no RPC to submit transactions exists.
"""
from __future__ import annotations
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re

SCHEMA = "CGX-EMPTY-GENESIS-LOCAL-DEVNET/0.1"
ZERO = "0" * 64
EMPTY_PAYLOAD_ROOT = hashlib.sha256(b"").hexdigest()
CHAIN_ID = "cgx:devnet:local:genesis-only:review-1"


def canonical(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def genesis_record() -> dict:
    block = {
        "schema": SCHEMA,
        "chain_id": CHAIN_ID,
        "chain_type": "CGX_TYPE1_EXPERIMENTAL_REVIEW",
        "chain_height": 0,
        "parent": "cgx:root:cognigrex",
        "previous_block_sha256": ZERO,
        "payload_merkle_root_sha256": EMPTY_PAYLOAD_ROOT,
        "transaction_count": 0,
        "object_count": 0,
        "minted_count": 0,
        "account_count": 0,
        "consensus": "NONE_LOCAL_REVIEW",
        "issuer": "UNCONFIGURED",
        "signed_root_authority": False,
        "independent_dbr": False,
        "source_rights_verified": False,
        "native_admission": False,
        "public_network": False,
        "network_transfers": False,
        "may_mint": False,
        "may_sign": False,
        "may_submit_transactions": False,
    }
    return {"genesis": block, "genesis_sha256": hashlib.sha256(canonical(block)).hexdigest()}


def validate_record(record: object) -> dict:
    expected = genesis_record()
    if not isinstance(record, dict) or set(record) != set(expected):
        raise ValueError("GENESIS_RECORD_SHAPE_HOLD")
    if record != expected:
        raise ValueError("GENESIS_NONEMPTY_OR_AUTHORITY_HOLD")
    if not re.fullmatch("[a-f0-9]{64}", str(record.get("genesis_sha256", ""))):
        raise ValueError("GENESIS_DIGEST_INVALID")
    if hashlib.sha256(canonical(record["genesis"])).hexdigest() != record["genesis_sha256"]:
        raise ValueError("GENESIS_DIGEST_MISMATCH")
    return record


def read_state(path: Path) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 12_000:
        raise ValueError("GENESIS_FILE_MISSING_SYMLINK_OR_OVERSIZE")
    try:
        return validate_record(json.loads(path.read_text("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("GENESIS_JSON_INVALID") from exc


def initialise(path: Path) -> dict:
    path = Path(path)
    if path.is_symlink() or path.exists():
        raise ValueError("GENESIS_ALREADY_EXISTS_NO_OVERWRITE")
    if path.parent.is_symlink():
        raise ValueError("STATE_PARENT_SYMLINK_FORBIDDEN")
    path.parent.mkdir(parents=True, exist_ok=True)
    record = genesis_record()
    # x mode ensures existing owner/agent state can never be replaced.
    with path.open("x", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(record, sort_keys=True, indent=2) + "\n")
    return read_state(path)


def status(path: Path) -> dict:
    record = read_state(path)
    return {
        "schema": "CGX-LOCAL-EMPTY-CHAIN-STATUS/0.1",
        "state": "GENESIS_ONLY_READ_ONLY_LOCAL",
        "chain_id": CHAIN_ID,
        "genesis_sha256": record["genesis_sha256"],
        "height": 0,
        "transaction_count": 0,
        "minted_count": 0,
        "consensus": "NONE",
        "authenticated_two_node_dbr": False,
        "native_mint": False,
        "public_deployment": False,
        "source_rights_qualified": False,
        "note": "Local review/devnet only; no blockchain consensus, DBR, issuer or native operations",
    }


def make_handler(state_path: Path):
    class ReadOnlyHandler(BaseHTTPRequestHandler):
        server_version = "CGXEmptyGenesisReview/0.1"
        sys_version = ""

        def _reply(self, status_code: int, document: dict):
            body = canonical(document)
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path not in ("/health", "/status", "/genesis"):
                return self._reply(404, {"state": "HOLD", "reason": "ENDPOINT_NOT_ALLOWLISTED"})
            try:
                record = read_state(state_path)
            except (ValueError, OSError):
                return self._reply(503, {"state": "HOLD", "reason": "GENESIS_INTEGRITY_FAILED"})
            if self.path == "/genesis":
                return self._reply(200, record)
            s = status(state_path)
            return self._reply(200, s if self.path == "/status" else {
                "schema": s["schema"], "state": s["state"],
                "genesis_sha256": s["genesis_sha256"], "healthy": True})

        def do_POST(self):
            return self._reply(405, {"state": "HOLD", "reason": "TRANSACTIONS_DISABLED"})

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST

        def log_message(self, format_string, *args):
            # Never log user-supplied URL or query values.
            pass

    return ReadOnlyHandler


def serve(path: Path, port: int):
    read_state(path)
    if not isinstance(port, int) or not 18000 <= port <= 65535:
        raise ValueError("INVALID_LOCAL_DEVNET_PORT")
    # There is intentionally NO host parameter or public bind option.
    with ThreadingHTTPServer(("127.0.0.1", port), make_handler(path)) as server:
        server.daemon_threads = True
        server.serve_forever(poll_interval=0.25)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("init", "verify", "serve"))
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--port", type=int, default=18841)
    args = parser.parse_args()
    try:
        if args.action == "init":
            result = initialise(args.state)
        elif args.action == "verify":
            result = status(args.state)
        else:
            serve(args.state, args.port)
            return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"state": "HOLD", "reason": str(exc),
                          "native_mint": False, "public_deployment": False}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
