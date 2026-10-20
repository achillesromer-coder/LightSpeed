"""Noncanonical, private-first R0 video source preflight for existing CGX FileSpace.

Requires caller-controlled original bytes and provenance. Never decodes a frame,
transcodes, writes to a CGX root, registers an adapter, or changes release scope.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping

SCHEMA = "CGX-VIDEO-R0-PREFLIGHT/0.1"
SUPPORTED_REFERENCE_SUFFIXES = {".mp4", ".mov", ".mkv", ".avi", ".y4m", ".mxf"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class SourceHeld(ValueError):
    """Input cannot pass a source-preserving local preflight."""


def verify_owner_local_source(
    source: str | os.PathLike[str], approved_root: str | os.PathLike[str],
    expected_sha256: str, expected_size: int, *, max_bytes: int = 512 * (1024**3),
) -> dict[str, Any]:
    """Stream-check exact local bytes under an independently approved local root.

    This establishes *only* local byte equality to caller's prior digest; it
    does not attest original provider, copyright, actor, lease, ACL or DBR.
    """
    if not isinstance(expected_sha256, str) or SHA256.fullmatch(expected_sha256) is None:
        raise SourceHeld("expected_sha256 must be canonical lower-case hex")
    if type(expected_size) is not int or not 0 < expected_size <= max_bytes:
        raise SourceHeld("declared size outside bounded intake")
    root = Path(approved_root)
    f = Path(source)
    if root.is_symlink() or f.is_symlink() or not root.is_dir() or not f.is_file():
        raise SourceHeld("unapproved root, symlink or missing regular source")
    try:
        resolved = f.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise SourceHeld("source must be inside approved owner root") from exc
    if f.suffix.lower() not in SUPPORTED_REFERENCE_SUFFIXES:
        raise SourceHeld("unknown video container for this proposal")
    before = f.stat()
    if before.st_size != expected_size:
        raise SourceHeld("source size mismatch before readback")
    digest = hashlib.sha256()
    seen = 0
    with f.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            seen += len(chunk)
            if seen > max_bytes or seen > expected_size:
                raise SourceHeld("source grew beyond allowed size")
            digest.update(chunk)
    after = f.stat()
    if (seen != expected_size or after.st_size != before.st_size or
            after.st_mtime_ns != before.st_mtime_ns or digest.hexdigest() != expected_sha256):
        raise SourceHeld("source changed or content SHA-256 mismatch")
    return {"sha256": digest.hexdigest(), "byte_length": seen,
            "state": "LOCAL_R0_BYTES_MATCH_EXPECTED_DIGEST_ONLY"}


def bounded_ffprobe(source: str | os.PathLike[str], *, approved_root: str | os.PathLike[str],
                    expected_sha256: str, expected_size: int,
                    timeout_seconds: int = 25) -> dict[str, Any]:
    """Require exact local source bytes; fixed read-only FFprobe, no shell."""
    verify_owner_local_source(source, approved_root, expected_sha256, expected_size)
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 60:
        raise SourceHeld("invalid inspect timeout")
    cmd = ["ffprobe", "-v", "error", "-show_entries",
           "format=duration,format_name,size:stream=index,codec_type,codec_name,width,height,pix_fmt,bits_per_raw_sample,r_frame_rate,avg_frame_rate,nb_frames,color_transfer,side_data_list:stream_tags=stereo_mode",
           "-of", "json", "--", str(source)]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=timeout_seconds, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SourceHeld("ffprobe unavailable or timed out") from exc
    if proc.returncode != 0 or len(proc.stdout) > 128 * 1024:
        raise SourceHeld("ffprobe failure or oversized output")
    try:
        data = json.loads(proc.stdout)
    except (ValueError, UnicodeError) as exc:
        raise SourceHeld("invalid ffprobe JSON") from exc
    if not isinstance(data, dict):
        raise SourceHeld("invalid ffprobe envelope")
    return data


def prepare_video_candidate(r0: Mapping[str, Any], probe: Mapping[str, Any],
                            *, claimed_layout: str = "UNKNOWN") -> dict[str, Any]:
    """Assess metadata only; output never grants native/video/physical authority."""
    if not isinstance(r0, Mapping) or not isinstance(probe, Mapping):
        raise SourceHeld("mapping expected")
    sha, n = r0.get("sha256"), r0.get("byte_length")
    if not isinstance(sha, str) or SHA256.fullmatch(sha) is None or type(n) is not int or n <= 0:
        raise SourceHeld("exact-source digest and byte size required")
    if r0.get("state") != "LOCAL_R0_BYTES_MATCH_EXPECTED_DIGEST_ONLY":
        raise SourceHeld("no independently rechecked local R0 source")
    streams = probe.get("streams")
    if not isinstance(streams, list) or len(streams) > 32:
        raise SourceHeld("missing or oversized track manifest")
    video = [s for s in streams if isinstance(s, dict) and s.get("codec_type") == "video"]
    if not video or len(video) > 8:
        raise SourceHeld("missing video or >8 video streams")
    tracks = []
    for s in video:
        width, height = s.get("width"), s.get("height")
        if any(type(v) is not int or not 0 < v <= 16384 for v in (width, height)):
            raise SourceHeld("invalid or unknown video geometry")
        tracks.append({"index": s.get("index"), "width": width, "height": height,
                       "codec": s.get("codec_name") if isinstance(s.get("codec_name"), str) else None,
                       "pixel_format": s.get("pix_fmt") if isinstance(s.get("pix_fmt"), str) else None,
                       "declared_frame_count": s.get("nb_frames"),
                       "frame_rate": s.get("avg_frame_rate"),
                       "stereo_metadata": s.get("tags", {}).get("stereo_mode") if isinstance(s.get("tags"), dict) else None})
    if claimed_layout not in {"UNKNOWN", "SIDE_BY_SIDE", "TOP_BOTTOM", "MULTI_TRACK", "MONO", "VOLUMETRIC"}:
        raise SourceHeld("unsupported declared layout")
    stereo_state = "UNVERIFIED_OWNER_DECLARATION" if claimed_layout != "UNKNOWN" else "UNKNOWN"
    flags = ["MEDIA_ADAPTER_NOT_REGISTERED", "SOURCE_OWNER_REVISION_RIGHTS_ACL_NOT_ATTESTED",
             "NO_CODED_FRAME_OR_PIXEL_ROUND_TRIP", "NO_COMPRESSION_MEASURED", "NO_CANONICAL_DBR",
             "NOT_PUBLIC", "STEREO_LAYOUT_UNVERIFIED", "PHYSICAL_3D_GEOMETRY_NOT_INFERRED"]
    if len(video) > 1: flags.append("MULTI_TRACK_REQUIRES_PER_TRACK_PROCESSING")
    if any((t["pixel_format"] or "").startswith(("yuv420p10", "yuv422p10", "yuv444p10", "p010", "gbrp10")) for t in tracks):
        flags.append("HIGH_BIT_DEPTH_REQUIRES_QUALIFIED_PROFILE")
    return {"schema": SCHEMA, "status": "PRIVATE_R0_MEDIA_PROJECTION_ONLY",
            "root_reference_only": "Cognigrex.cgx", "source_sha256": sha,
            "source_size_bytes": n, "tracks": tracks,
            "claimed_layout": claimed_layout, "layout_state": stereo_state,
            "holds": flags, "native_r1_admitted": False,
            "lossless_reconstruction_verified": False,
            "pixel_exact_reconstruction_verified": False,
            "compression_ratio_measured": False,
            "source_rights_verified": False,
            "signed_peer_verified": False,
            "canonical_promotion_authorized": False,
            "public_publish_authorized": False}


def measured_ratio(original_bytes: int, encoded_bytes: int, *,
                   original_sha256: str | None = None,
                   reconstructed_sha256: str | None = None) -> dict[str, Any]:
    if any(type(n) is not int or n <= 0 for n in (original_bytes, encoded_bytes)):
        raise SourceHeld("positive exact byte counts required")
    exact_original_match = bool(original_sha256 and reconstructed_sha256 and
        SHA256.fullmatch(original_sha256) and SHA256.fullmatch(reconstructed_sha256) and
        original_sha256 == reconstructed_sha256)
    return {"ratio": round(original_bytes / encoded_bytes, 9),
            "encoded_bytes": encoded_bytes,
            "reported_source_and_reconstruction_hashes_match": exact_original_match,
            "exact_original_byte_reconstruction_verified": False,
            "evidence_state": "CALCULATED_FROM_CALLER_SUPPLIED_COUNTS_NOT_NATIVE_READBACK",
            "pixel_exact_reconstruction_verified": False,
            "release_authorized": False}