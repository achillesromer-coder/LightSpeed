"""Build a strictly allowlisted UniSpace /cgx static site.

The LS GO Vite public/ tree is NOT an authorised CGX public distribution.
This produces a separate deployable site containing only named public assets,
seven explicit routes, and a hardened Vercel policy. It neither publishes nor
reads any owner-only source, credentials or private catalogue.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PUBLIC_FILES = (
    "index.html",
    "fs/index.html", "ds/index.html", "ps/index.html",
    "doom/index.html", "romer/index.html", "eco/index.html",
    "assets/core.js", "assets/domain-overviews.js",
    "assets/domain-viewer.js", "assets/viewer.css", "assets/viewer.js",
)
DENIED_SNIPPETS = (
    b"cgx_internal_review_projection",
    b"component_geometry_atlas_public_review",
    b"localhost:8765",
    b"X-LightSpeed-Session",
    b"/api/v1/",
    b"desktopBridge",
    b"ownerAuth",
    b"Bearer ",
)
MANIFEST_NAME = "cgx-public-integrity.json"


def _resolved_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def assemble_cgx_public(source: Path, output: Path) -> dict:
    source = Path(source).absolute()
    output = Path(output).absolute()
    if not source.is_dir() or source.is_symlink():
        raise ValueError("CGX public source directory unavailable or linked")
    if _resolved_within(output, source) or _resolved_within(source, output):
        raise ValueError("Release output must be separate from the source tree")
    if output.exists() or output.is_symlink():
        raise ValueError("Refusing to replace an existing release directory")
    required = [Path(name) for name in PUBLIC_FILES]
    policy_relative = Path("deployment/vercel.json")
    contents = {}
    for relative in (*required, policy_relative):
        candidate = source / relative
        if not candidate.is_file() or candidate.is_symlink() or not _resolved_within(candidate.resolve(), source.resolve()):
            raise ValueError("Missing, linked or untrusted public source file: " + str(relative))
        raw = candidate.read_bytes()
        if not raw or len(raw) > 256_000:
            raise ValueError("Invalid bounded public asset size: " + str(relative))
        if relative != policy_relative:
            for unsafe in DENIED_SNIPPETS:
                if unsafe.lower() in raw.lower():
                    raise ValueError("Private or operational reference in CGX asset: " + str(relative))
        contents[str(relative)] = raw
    policy = json.loads(contents[str(policy_relative)].decode("utf-8"))
    headers = policy.get("headers", [])
    policies = [
        h.get("value", "") for item in headers
        for h in item.get("headers", [])
        if h.get("key", "").lower() == "content-security-policy"
    ]
    if not policies or not all(
        "connect-src 'none'" in value
        and "object-src 'none'" in value
        and "frame-ancestors https://romer.industries https://www.romer.industries" in value
        for value in policies
    ):
        raise ValueError("Public release requires isolated CSP and framing policy")
    output.mkdir(parents=True)
    records = []
    for relative in PUBLIC_FILES:
        raw = contents[relative]
        destination = output / "cgx" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        if destination.read_bytes() != raw:
            raise ValueError("Public source copy readback mismatch")
        records.append({"path": "cgx/" + relative, "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest()})
    (output / "vercel.json").write_bytes(contents[str(policy_relative)])
    manifest = {
        "schema": "CGX-PUBLIC-ISOLATED-STATIC-PACKAGE/0.1",
        "status": "UNPUBLISHED_REVIEW_ARTIFACT",
        "distribution_root": "/cgx",
        "source_subset": "apps/lightspeed-go/public/cgx",
        "allowed_file_count": len(PUBLIC_FILES),
        "assets": records,
        "contains_private_lsgo_application": False,
        "contains_internal_review_files": False,
        "contains_owner_credentials": False,
        "network_execution_enabled": False,
        "source_integrity_covered": True,
        "native_cgx_authentication": False,
        "live_deployment_verified": False,
        "rights_release_authorized": False,
        "gates": ["ISSUE_158_PUBLIC_PRIVATE", "ISSUE_161_NATIVE_TWO_NODE",
                  "OWNER_APPROVED_RELEASE", "BROWSER_SITE_READBACK"],
    }
    (output / MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    observed = {
        p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()
    }
    expected = {"cgx/" + p for p in PUBLIC_FILES} | {"vercel.json", MANIFEST_NAME}
    if observed != expected:
        raise ValueError("Unexpected output file in public release artifact")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="apps/lightspeed-go/public/cgx")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(assemble_cgx_public(Path(args.source), Path(args.output)),
                     indent=2, sort_keys=True))
