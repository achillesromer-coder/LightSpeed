"""CGX Drive minimal-key readback candidate. NO API, scheduler, lease or command execution.

Existing authorised local intake exports the Google Doc key as text and supplies
a locally-selected source file. This utility merely classifies exact source bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

KEY_SCHEMA = "cgx.drive.minimal-reference-candidate.v1"
RECEIPT_SCHEMA = "cgx.drive.local-reference-readback-candidate.v1"
MAX_KEY = 16384
MAX_SOURCE = 64 * 1024 * 1024


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical(record: dict) -> bytes:
    return json.dumps(record, ensure_ascii=True, separators=(",", ":"), sort_keys=True).encode("ascii")


def resolve_key(key: dict, *, asset: Path | None = None, previous: dict | None = None) -> tuple[dict, bool]:
    source = key.get("source") if isinstance(key, dict) else None
    if (not isinstance(key, dict) or key.get("schema") != KEY_SCHEMA or
        key.get("action") != "source_root_readback_only" or
        key.get("target") != "BouwerBase" or
        key.get("mode") != "review_only" or key.get("authority_transfer") is not False or
        not isinstance(key.get("handoff"), str) or not key["handoff"] or
        not isinstance(source, dict) or
        not isinstance(source.get("ref"), str) or not source["ref"].startswith("drive:file:") or
        not isinstance(source.get("sha256"), str) or len(source["sha256"]) != 64 or
        any(c not in "0123456789abcdef" for c in source["sha256"]) or
        type(source.get("bytes")) is not int or
        not 0 <= source["bytes"] <= MAX_SOURCE):
        raise ValueError("HOLD_INVALID_INPUT")

    observed = None
    if asset is None or not asset.is_file():
        status = "NOT_CACHED"
    elif asset.stat().st_size > MAX_SOURCE:
        status = "HOLD_BOUNDS"
    else:
        observed = digest(asset.read_bytes())  # Only locally selected path; never key-supplied.
        status = ("RESOLVED_LOCAL_REFERENCE" if
                  (observed == source["sha256"] and asset.stat().st_size == source["bytes"])
                  else "CONTEXT_MISMATCH")
    key_digest = digest(canonical(key))
    receipt = {
        "schema": RECEIPT_SCHEMA, "handoff": key["handoff"], "key_sha256": key_digest,
        "status": status, "source_sha256": source["sha256"],
        "observed_sha256": observed, "evidence": "LOCAL_BYTES_READBACK_ONLY",
        "device_identity_attested": False, "provider_permissions_verified": False,
        "lease_verified": False, "execution_performed": False,
        "canonical_promotion_authorized": False, "authority_transfer": False
    }
    fresh = not (isinstance(previous, dict) and
                 all(previous.get(field) == receipt[field] for field in
                     ("schema", "handoff", "key_sha256", "status", "observed_sha256")))
    return receipt, fresh


def main() -> int:
    p = argparse.ArgumentParser(description="Read-only source-root key classification")
    p.add_argument("key", type=Path)
    p.add_argument("--asset", type=Path)
    p.add_argument("--previous", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        if args.key.stat().st_size > MAX_KEY:
            raise ValueError("HOLD_OVERSIZE_KEY")
        key = json.loads(args.key.read_text(encoding="utf-8"))
        previous = (json.loads(args.previous.read_text(encoding="utf-8"))
                    if args.previous and args.previous.is_file() else None)
        result, fresh = resolve_key(key, asset=args.asset, previous=previous)
        if not fresh:
            print('{"status":"NO_ACTION"}')
            return 0
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=True, sort_keys=True, indent=2)
                stream.write("\n")
        print(canonical(result).decode("ascii"))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "HOLD_INVALID_INPUT", "reason": str(exc),
                          "execution_performed": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
