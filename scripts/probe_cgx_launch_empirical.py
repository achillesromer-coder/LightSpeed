#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import UTC, datetime
import hashlib
import ipaddress
import json
from pathlib import Path
import platform
import secrets
import socket
import subprocess
import sys
from typing import Any

SCHEMA = "CGX-LAUNCH-EMPIRICAL-PREFLIGHT/0.1"
CRED_TYPE_GENERIC = 1
CRED_PERSIST_SESSION = 1
ERROR_NOT_FOUND = 1168


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def git_head(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def windows_node_fingerprint() -> dict[str, Any]:
    if platform.system() != "Windows":
        return {
            "supported": False,
            "method": "windows-machine-guid-sha256-v1",
            "node_fingerprint_sha256": None,
            "raw_identifier_persisted": False,
        }
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Cryptography",
    ) as key:
        machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
    digest = sha256_text("CGX-NODE-FP-V1|" + str(machine_guid).strip())
    return {
        "supported": True,
        "method": "windows-machine-guid-sha256-v1",
        "node_fingerprint_sha256": digest,
        "raw_identifier_persisted": False,
    }


def non_loopback_ipv4_count() -> int:
    addresses: set[str] = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = str(item[4][0])
            parsed = ipaddress.ip_address(address)
            if not parsed.is_loopback and not parsed.is_unspecified:
                addresses.add(address)
    except OSError:
        pass
    return len(addresses)


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def windows_credential_manager_probe() -> dict[str, Any]:
    base = {
        "supported": platform.system() == "Windows",
        "provider": "Windows Credential Manager / CRED_TYPE_GENERIC / session persistence",
        "synthetic_only": True,
        "production_credential_touched": False,
        "secret_in_receipt": False,
        "write_readback_pass": False,
        "revocation_delete_pass": False,
        "post_revocation_absent": False,
        "cleanup_verified": False,
        "production_integration_verified": False,
        "recovery_path_verified": False,
    }
    if platform.system() != "Windows":
        return base

    advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    cred_write = advapi32.CredWriteW
    cred_write.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]
    cred_write.restype = wintypes.BOOL
    cred_read = advapi32.CredReadW
    cred_read.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(CREDENTIALW)),
    ]
    cred_read.restype = wintypes.BOOL
    cred_delete = advapi32.CredDeleteW
    cred_delete.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    cred_delete.restype = wintypes.BOOL
    cred_free = advapi32.CredFree
    cred_free.argtypes = [ctypes.c_void_p]
    cred_free.restype = None

    target = "CGX-PREFLIGHT-" + secrets.token_hex(12)
    username = "CGX-Preflight"
    secret = secrets.token_bytes(32)
    secret_buffer = ctypes.create_string_buffer(secret)
    credential = CREDENTIALW()
    credential.Type = CRED_TYPE_GENERIC
    credential.TargetName = target
    credential.UserName = username
    credential.CredentialBlobSize = len(secret)
    credential.CredentialBlob = ctypes.cast(
        secret_buffer, ctypes.POINTER(wintypes.BYTE)
    )
    credential.Persist = CRED_PERSIST_SESSION

    wrote = False
    deleted = False
    try:
        if not cred_write(ctypes.byref(credential), 0):
            raise OSError(ctypes.get_last_error(), "CredWriteW failed")
        wrote = True

        read_ptr = ctypes.POINTER(CREDENTIALW)()
        if not cred_read(target, CRED_TYPE_GENERIC, 0, ctypes.byref(read_ptr)):
            raise OSError(ctypes.get_last_error(), "CredReadW failed")
        try:
            read_blob = ctypes.string_at(
                read_ptr.contents.CredentialBlob,
                read_ptr.contents.CredentialBlobSize,
            )
            base["write_readback_pass"] = secrets.compare_digest(read_blob, secret)
        finally:
            cred_free(read_ptr)

        if not cred_delete(target, CRED_TYPE_GENERIC, 0):
            raise OSError(ctypes.get_last_error(), "CredDeleteW failed")
        deleted = True
        base["revocation_delete_pass"] = True

        after_ptr = ctypes.POINTER(CREDENTIALW)()
        present_after = bool(
            cred_read(target, CRED_TYPE_GENERIC, 0, ctypes.byref(after_ptr))
        )
        if present_after:
            cred_free(after_ptr)
        else:
            base["post_revocation_absent"] = ctypes.get_last_error() == ERROR_NOT_FOUND
    finally:
        if wrote and not deleted:
            deleted = bool(cred_delete(target, CRED_TYPE_GENERIC, 0))
        verify_ptr = ctypes.POINTER(CREDENTIALW)()
        still_present = bool(
            cred_read(target, CRED_TYPE_GENERIC, 0, ctypes.byref(verify_ptr))
        )
        if still_present:
            cred_free(verify_ptr)
            cred_delete(target, CRED_TYPE_GENERIC, 0)
        base["cleanup_verified"] = not still_present
        secret = b""
    return base


def build_receipt(
    *,
    source_head: str | None,
    host_class: str,
    node_identity: dict[str, Any],
    ipv4_count: int,
    credential_probe: dict[str, Any],
) -> dict[str, Any]:
    credential_pass = all(
        credential_probe.get(key) is True
        for key in (
            "write_readback_pass",
            "revocation_delete_pass",
            "post_revocation_absent",
            "cleanup_verified",
        )
    )
    return {
        "schema": SCHEMA,
        "generated_at_utc": utc_now(),
        "source_head": source_head,
        "host_class": host_class,
        "node_identity": node_identity,
        "network": {
            "non_loopback_ipv4_count": int(ipv4_count),
            "raw_network_identifiers_persisted": False,
        },
        "launch_007": {
            "state": "EMPIRICAL_OPEN_PREPARED",
            "physical_devices_observed": 1 if node_identity.get("supported") else 0,
            "distinct_peer_verified": False,
            "non_loopback_network_available": int(ipv4_count) > 0,
            "peer_transport_verified": False,
            "peer_compute_verified": False,
            "peer_revocation_stop_propagation_verified": False,
            "partition_degraded_mode_authority_tested": False,
            "closure_claim": False,
            "next_evidence": [
                "run this preflight on a genuinely distinct second physical host",
                "perform authenticated non-loopback transfer/readback between distinct nodes",
                "read back scoped identity and execution lease on both nodes",
                "exercise stop/revocation propagation and partition/degraded fail-closed behavior",
                "independent Achilles audit of complete peer evidence",
            ],
        },
        "launch_008": {
            "state": "EMPIRICAL_OPEN_PREPARED",
            "credential_boundary": credential_probe,
            "synthetic_host_boundary_pass": credential_pass,
            "production_integration_verified": False,
            "production_revocation_verified": False,
            "recovery_path_verified": False,
            "closure_claim": False,
            "next_evidence": [
                "bind production-relevant LightSpeed/CGX credentials to the approved platform boundary",
                "exercise production-relevant revocation without exposing secret material",
                "exercise approved recovery path and verify recovered capability",
                "repeat for every target host class in launch scope",
                "independent Achilles audit of cleanup and non-secret receipt",
            ],
        },
        "claim_boundary": (
            "This receipt proves only one-host preparation and a synthetic host credential "
            "boundary probe. It does not close CGX-LAUNCH-007 or CGX-LAUNCH-008, does not "
            "prove a second device, production credential integration, disaster recovery, "
            "distributed governance, child promotion, publication, or physical actuation."
        ),
        "authority_transfer": False,
        "canonical_promotion_authorized": False,
        "public_publish_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--contract-only", action="store_true")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    if args.contract_only:
        node = {
            "supported": False,
            "method": "contract-only",
            "node_fingerprint_sha256": None,
            "raw_identifier_persisted": False,
        }
        credential = {
            "supported": False,
            "provider": "contract-only",
            "synthetic_only": True,
            "production_credential_touched": False,
            "secret_in_receipt": False,
            "write_readback_pass": False,
            "revocation_delete_pass": False,
            "post_revocation_absent": False,
            "cleanup_verified": True,
            "production_integration_verified": False,
            "recovery_path_verified": False,
        }
        receipt = build_receipt(
            source_head=git_head(root),
            host_class=platform.system().lower() or "unknown",
            node_identity=node,
            ipv4_count=0,
            credential_probe=credential,
        )
    else:
        node = windows_node_fingerprint()
        credential = windows_credential_manager_probe()
        receipt = build_receipt(
            source_head=git_head(root),
            host_class=platform.system().lower() or "unknown",
            node_identity=node,
            ipv4_count=non_loopback_ipv4_count(),
            credential_probe=credential,
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if args.contract_only:
        return 0
    return 0 if receipt["launch_008"]["synthetic_host_boundary_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
