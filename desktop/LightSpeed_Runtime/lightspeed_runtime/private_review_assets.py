"""Owner-gated CGX Object Review asset loader.

Standalone, bounded read-only file layer for the existing LS GO bridge.
The configured root must be private and outside Vite public/dist. Never
derive this path from a requested URL, browser role or a public catalogue.
No grant, credential or signed delivery receipt is created here.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat

ROOT_ENV = "CGX_PRIVATE_REVIEW_ROOT"
LIMIT_BYTES = 4 * 1024 * 1024
SAFE_FILENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z", re.ASCII)

class PrivateReviewAssetError(ValueError):
    """No access, unavailable root or unsafe privately held asset."""

def private_review_root(environment: dict[str, str] | None = None) -> Path:
    env = environment if environment is not None else os.environ
    raw = env.get(ROOT_ENV, "")
    if not raw or not Path(raw).is_absolute() or ".." in Path(raw).parts:
        raise PrivateReviewAssetError("PRIVATE_REVIEW_ROOT_UNCONFIGURED")
    path = Path(raw)
    if path.is_symlink() or not path.is_dir():
        raise PrivateReviewAssetError("PRIVATE_REVIEW_ROOT_UNAVAILABLE")
    try:
        canonical = path.resolve(strict=True)
    except (OSError, ValueError) as exc:
        raise PrivateReviewAssetError("PRIVATE_REVIEW_ROOT_UNAVAILABLE") from exc
    if any(s.lower() in {"public", "dist"} for s in canonical.parts):
        raise PrivateReviewAssetError("PRIVATE_REVIEW_ROOT_STATIC_PATH_FORBIDDEN")
    return canonical

def _local_asset_path(root: Path, category: str, name: str) -> Path:
    if not isinstance(name, str) or not SAFE_FILENAME.fullmatch(name):
        raise PrivateReviewAssetError("INVALID_ASSET_NAME")
    if category == "catalogue" and name == "cgx_object_review_catalogue.json":
        rel = Path("data", name)
    elif category == "atlas" and name == "component_geometry_atlas_public_review.json":
        rel = Path("data", name)
    elif category == "renders" and name.endswith(".svg"):
        rel = Path("review", "renders", name)
    elif category == "mesh" and name.endswith(".json"):
        rel = Path("review", "mesh", name)
    else:
        raise PrivateReviewAssetError("UNREGISTERED_REVIEW_ASSET")
    value = root / rel
    for parent in (root, *list(value.parents)[:-1]):
        if parent == root.parent:
            break
        if parent.is_symlink():
            raise PrivateReviewAssetError("ASSET_SYMLINK_FORBIDDEN")
    if any(part.is_symlink() for part in [value, value.parent, value.parent.parent]):
        raise PrivateReviewAssetError("ASSET_SYMLINK_FORBIDDEN")
    try:
        candidate = value.resolve(strict=True)
    except (OSError, ValueError) as exc:
        raise PrivateReviewAssetError("ASSET_UNAVAILABLE") from exc
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise PrivateReviewAssetError("ASSET_OUTSIDE_PRIVATE_ROOT")
    return candidate

def read_private_review_asset(root: Path, category: str, name: str) -> dict:
    if any(p.lower() in {"public", "dist"} for p in root.parts):
        raise PrivateReviewAssetError("PRIVATE_REVIEW_ROOT_STATIC_PATH_FORBIDDEN")
    filename = _local_asset_path(root, category, name)
    try:
        before = filename.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > LIMIT_BYTES or before.st_size < 0:
            raise PrivateReviewAssetError("ASSET_TYPE_OR_SIZE_REJECTED")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(filename, flags)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns
            ):
                raise PrivateReviewAssetError("ASSET_CHANGED_DURING_READ")
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                body = stream.read(LIMIT_BYTES + 1)
            if len(body) > LIMIT_BYTES or len(body) != before.st_size:
                raise PrivateReviewAssetError("ASSET_CHANGED_DURING_READ")
        finally:
            os.close(descriptor)
    except PrivateReviewAssetError:
        raise
    except OSError as exc:
        raise PrivateReviewAssetError("ASSET_UNAVAILABLE") from exc
    mime = "image/svg+xml" if category == "renders" else "application/json"
    return {"content": body, "media_type": mime,
            "sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body)}
