"""Private CGX review library: strict file and static-path protection tests."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import pytest

from lightspeed_runtime.private_review_assets import (
    LIMIT_BYTES, PrivateReviewAssetError, private_review_root, read_private_review_asset
)

def source(tmp_path: Path):
    root=tmp_path/"cgx_private_object_review"
    (root/"data").mkdir(parents=True)
    (root/"review"/"renders").mkdir(parents=True)
    (root/"review"/"mesh").mkdir(parents=True)
    (root/"data"/"cgx_object_review_catalogue.json").write_bytes(b'{"status":"INTERNAL_REVIEW"}')
    (root/"data"/"component_geometry_atlas_public_review.json").write_bytes(b'{"record_count":411}')
    (root/"review"/"renders"/"diode.svg").write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
    (root/"review"/"mesh"/"diode.json").write_bytes(b'{"vertices":[]}')
    return root

def test_config_requires_explicit_absolute_non_public_root(tmp_path):
    root=source(tmp_path)
    assert private_review_root({"CGX_PRIVATE_REVIEW_ROOT":str(root)})==root.resolve()
    for value in ("", ".", "../relative", str(root/"missing")):
        with pytest.raises(PrivateReviewAssetError):
            private_review_root({"CGX_PRIVATE_REVIEW_ROOT":value})
    p=tmp_path/"public"
    p.mkdir()
    with pytest.raises(PrivateReviewAssetError,match="STATIC_PATH_FORBIDDEN"):
        private_review_root({"CGX_PRIVATE_REVIEW_ROOT":str(p)})

def test_exact_content_and_receipt_after_owner_verification(tmp_path):
    root=source(tmp_path)
    for kind,name in [
        ("catalogue","cgx_object_review_catalogue.json"),
        ("atlas","component_geometry_atlas_public_review.json"),
        ("renders","diode.svg"),
        ("mesh","diode.json")
    ]:
        packet=read_private_review_asset(root,kind,name)
        assert packet["sha256"]==hashlib.sha256(packet["content"]).hexdigest()
        assert packet["size_bytes"]==len(packet["content"])
        assert packet["media_type"]==("image/svg+xml" if kind=="renders" else "application/json")

@pytest.mark.parametrize("kind,name",[
    ("catalogue","fake.json"),("atlas","fake.json"),("renders","diode.json"),
    ("mesh","diode.svg"),("public","diode.svg"),("mesh",".."),
    ("mesh","../other.json"),("mesh","%2E%2E.json"),("mesh",".env"),
    ("renders","abc.svg/../../private.txt"),("renders","bad:asset.svg"),
])
def test_arbitrary_filename_and_category_denied(tmp_path,kind,name):
    root=source(tmp_path)
    with pytest.raises(PrivateReviewAssetError):
        read_private_review_asset(root,kind,name)

def test_symlink_rejected_even_if_target_is_inside_root(tmp_path):
    root=source(tmp_path)
    target=root/"review"/"renders"/"diode.svg"
    link=root/"review"/"renders"/"shortcut.svg"
    try:link.symlink_to(target)
    except (OSError,NotImplementedError):pytest.skip("symlinks unsupported")
    with pytest.raises(PrivateReviewAssetError,match="SYMLINK"):
        read_private_review_asset(root,"renders","shortcut.svg")

def test_zero_oroversize_restricted_and_no_unbounded_archive(tmp_path):
    root=source(tmp_path)
    giant=root/"review"/"mesh"/"large.json"
    with giant.open("wb") as h:
        h.truncate(LIMIT_BYTES+1)
    with pytest.raises(PrivateReviewAssetError,match="SIZE"):
        read_private_review_asset(root,"mesh","large.json")
    # No directory listing or wildcard path is available through this reader.
    with pytest.raises(PrivateReviewAssetError):
        read_private_review_asset(root,"mesh","*")
