from __future__ import annotations

import hashlib
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = REPO_ROOT / "data" / "digital-twin" / "complete_digital_asset_manifest_2026-09-12.json"
GENERATED_MANIFEST = REPO_ROOT / "data" / "digital-twin" / "generated_mesh_manifest_v1.json"
GENERATOR = REPO_ROOT / "tools" / "digital-twin" / "build_atrium_viewer_meshes.py"
PREVIEW_GENERATOR = REPO_ROOT / "tools" / "digital-twin" / "render_atrium_views.py"


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def load_generator():
    spec = importlib.util.spec_from_file_location("build_atrium_viewer_meshes", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_preview_generator():
    spec = importlib.util.spec_from_file_location("render_atrium_views", PREVIEW_GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_checked_in_assets_match_manifests():
    source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    receipt = json.loads(GENERATED_MANIFEST.read_text(encoding="utf-8"))["assets"]
    expected = {item["twin_id"]: item for item in source["assets"]}
    actual = {item["twin_id"]: item for item in receipt}
    assert len(expected) == 16
    assert actual.keys() == expected.keys()
    for twin_id, item in actual.items():
        asset = REPO_ROOT / item["file"]
        contract = expected[twin_id]
        assert asset.is_file()
        assert asset.resolve().is_relative_to((REPO_ROOT / "assets" / "models").resolve())
        assert asset.stat().st_size == item["size_bytes"]
        assert sha256(asset) == item["sha256"]
        assert item["format"] == contract["format"] == "OBJ"
        assert item["representation_class"] == contract["representation_class"]
        assert item["units"] == contract["units"] == "m"
        assert item["vertices"] == contract["vertices"]
        assert item["faces"] == contract["faces"]
        assert item["watertight"] is contract["watertight"] is True


def test_assets_reproduce_byte_for_byte(tmp_path):
    generator = load_generator()
    regenerated = generator.generate_assets(tmp_path / "models", tmp_path / "manifest.json")
    checked_in = json.loads(GENERATED_MANIFEST.read_text(encoding="utf-8"))["assets"]
    assert [item["twin_id"] for item in regenerated] == [item["twin_id"] for item in checked_in]
    for expected, actual in zip(checked_in, regenerated, strict=True):
        assert actual["sha256"] == expected["sha256"]
        assert actual["size_bytes"] == expected["size_bytes"]
        assert actual["vertices"] == expected["vertices"]
        assert actual["faces"] == expected["faces"]
        assert actual["watertight"] == expected["watertight"]


def test_type1_surface_exposes_evidence_boundaries():
    html = (REPO_ROOT / "docs" / "digital-twin" / "type1-svg" / "index.html").read_text(encoding="utf-8")
    standard = (REPO_ROOT / "docs" / "digital-twin" / "type1-svg" / "T1_SVG_STANDARD.md").read_text(encoding="utf-8")
    for required in ("WatchTower", "M1 Elevated Bypass", "Römer Spaceport", "Mark III"):
        assert required in html
    for required in ("SOURCE_AUTHORITY", "INTERACTION_PROXY", "TYPE1 COMPLETE", "Claim boundary"):
        assert required in standard


def test_portfolio_identity_is_consistent():
    asset_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    showcase = json.loads((REPO_ROOT / "data" / "digital-twin" / "twin_showcase_manifest_2026-09-11.json").read_text(encoding="utf-8"))
    type1 = json.loads((REPO_ROOT / "data" / "digital-twin" / "type1_svg_contract_v1.json").read_text(encoding="utf-8"))
    asset_ids = [item["twin_id"] for item in asset_manifest["assets"]]
    showcase_ids = [item["id"] for item in showcase["twins"]]
    type1_ids = [item["twin_id"] for item in type1["migration"]]
    assert len(set(asset_ids)) == len(asset_ids) == 16
    assert set(asset_ids) == set(showcase_ids) == set(type1_ids)
    assert {item["priority"] for item in type1["migration"]} == {f"P{i}" for i in range(16)}
    assert showcase["counts"] == {"formal_suite": 12, "current_living_or_application": 4, "showcased": 16}
    reference = asset_manifest["reference_meshes"][0]
    assert reference["representation_class"] == "SOURCE_LINK_ONLY"
    assert "file" not in reference


def test_type1_local_links_resolve_inside_repository():
    html_path = REPO_ROOT / "docs" / "digital-twin" / "type1-svg" / "index.html"
    parser = AnchorParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    local_links = [href for href in parser.hrefs if "://" not in href and not href.startswith("#")]
    assert local_links
    for href in local_links:
        target = (html_path.parent / href).resolve()
        assert target.is_relative_to(REPO_ROOT.resolve())
        assert target.is_file(), f"broken local link: {href}"


def test_six_view_previews_match_receipt(tmp_path):
    receipt_path = REPO_ROOT / "data" / "digital-twin" / "generated_preview_manifest_v1.json"
    checked_in = json.loads(receipt_path.read_text(encoding="utf-8"))["assets"]
    assert len(checked_in) == 16
    expected_views = ["TOP", "BOTTOM", "LEFT", "RIGHT", "TOP LEFT", "TOP RIGHT"]
    for item in checked_in:
        preview = REPO_ROOT / item["file"]
        assert preview.is_file()
        assert item["views"] == expected_views
        assert item["width"] == 1200 and item["height"] == 800
        assert preview.stat().st_size == item["size_bytes"]
        assert sha256(preview) == item["sha256"]

    generator = load_preview_generator()
    regenerated = generator.generate_previews(REPO_ROOT / "assets" / "models", tmp_path / "previews", tmp_path / "manifest.json")
    assert [item["twin_id"] for item in regenerated] == [item["twin_id"] for item in checked_in]
    for expected, actual in zip(checked_in, regenerated, strict=True):
        assert actual["sha256"] == expected["sha256"]
        assert actual["size_bytes"] == expected["size_bytes"]
