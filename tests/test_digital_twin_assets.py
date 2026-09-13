from __future__ import annotations

import hashlib
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = REPO_ROOT / "data" / "digital-twin" / "complete_digital_asset_manifest_2026-09-12.json"
GENERATED_MANIFEST = REPO_ROOT / "data" / "digital-twin" / "generated_mesh_manifest_v1.json"
GENERATOR = REPO_ROOT / "tools" / "digital-twin" / "build_atrium_viewer_meshes.py"
PREVIEW_GENERATOR = REPO_ROOT / "tools" / "digital-twin" / "render_atrium_views.py"
TYPE1_PACKAGE_GENERATOR = REPO_ROOT / "tools" / "digital-twin" / "build_type1_svg_packages.py"


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.start_tags = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.start_tags.append((tag, attributes))
        if tag == "a":
            href = attributes.get("href")
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


def load_type1_package_generator():
    spec = importlib.util.spec_from_file_location("build_type1_svg_packages", TYPE1_PACKAGE_GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixel_sha256(path):
    with Image.open(path) as image:
        return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()


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


def test_type1_surface_is_static_mobile_print_and_privacy_bounded():
    html_path = REPO_ROOT / "docs" / "digital-twin" / "type1-svg" / "index.html"
    html = html_path.read_text(encoding="utf-8")
    parser = AnchorParser()
    parser.feed(html)

    forbidden = {"script", "form", "iframe", "object", "embed"}
    assert forbidden.isdisjoint(tag for tag, _ in parser.start_tags)
    assert "innerHTML" not in html and "eval(" not in html

    metas = [attrs for tag, attrs in parser.start_tags if tag == "meta"]
    assert any(attrs.get("name") == "viewport" and "width=device-width" in attrs.get("content", "") for attrs in metas)
    assert any(attrs.get("name") == "referrer" and attrs.get("content") == "no-referrer" for attrs in metas)
    csp = next(attrs["content"] for attrs in metas if attrs.get("http-equiv") == "Content-Security-Policy")
    for directive in ("default-src 'none'", "style-src 'unsafe-inline'", "base-uri 'none'", "form-action 'none'"):
        assert directive in csp

    assert "@media (max-width: 700px)" in html
    assert "@media print" in html
    assert "break-inside: avoid" in html
    assert ".links a:focus-visible" in html

    allowed_external = ("https://docs.google.com/", "https://github.com/")
    external_links = [href for href in parser.hrefs if "://" in href]
    assert external_links
    assert all(href.startswith(allowed_external) for href in external_links)

    cards = [attrs["data-twin-id"] for tag, attrs in parser.start_tags if tag == "article" and "data-twin-id" in attrs]
    assets = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))["assets"]
    migration = json.loads((REPO_ROOT / "data" / "digital-twin" / "type1_svg_contract_v1.json").read_text(encoding="utf-8"))["migration"]
    expected_order = [item["twin_id"] for item in sorted(migration, key=lambda item: int(item["priority"][1:]))]
    assert cards == expected_order
    assert set(cards) == {item["twin_id"] for item in assets}


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
        assert pixel_sha256(preview) == item["pixel_sha256"]

    generator = load_preview_generator()
    regenerated = generator.generate_previews(REPO_ROOT / "assets" / "models", tmp_path / "previews", tmp_path / "manifest.json")
    assert [item["twin_id"] for item in regenerated] == [item["twin_id"] for item in checked_in]
    for expected, actual in zip(checked_in, regenerated, strict=True):
        assert actual["pixel_sha256"] == expected["pixel_sha256"]


def test_type1_svg_packages_are_addressable_bounded_and_reproducible(tmp_path):
    manifest_path = REPO_ROOT / "data" / "digital-twin" / "generated_type1_svg_manifest_v1.json"
    receipt = json.loads(manifest_path.read_text(encoding="utf-8"))
    contract_path = REPO_ROOT / "data" / "digital-twin" / "type1_svg_contract_v1.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    migration = sorted(contract["migration"], key=lambda item: int(item["priority"][1:]))
    expected_twins = [item["twin_id"] for item in migration]
    expected_sheets = [f"T1-{index:02d}" for index in range(8)]
    source_assets = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))["assets"]
    proxy_ids = {item["twin_id"] for item in source_assets if item["representation_class"] == "INTERACTION_PROXY"}
    mesh_receipts = {
        item["twin_id"]: item
        for item in json.loads(GENERATED_MANIFEST.read_text(encoding="utf-8"))["assets"]
    }

    assert receipt["schema"] == "type1_svg_generated_package_receipt_v2"
    assert receipt["twins"] == expected_twins
    assert receipt["sheets"] == expected_sheets
    assert receipt["package_count"] == 16
    assert receipt["asset_count"] == 128
    assert len(receipt["assets"]) == 128
    assert proxy_ids == set(expected_twins[3:])

    generator_path = REPO_ROOT / receipt["generator"]["file"]
    assert sha256(generator_path) == receipt["generator"]["sha256"]
    assert receipt["dependency_versions"] == {"numpy": "1.26.4", "trimesh": "5.1.0"}
    for input_receipt in receipt["input_receipts"]:
        assert sha256(REPO_ROOT / input_receipt["file"]) == input_receipt["sha256"]
    for environment_receipt in receipt["environment_receipts"]:
        assert sha256(REPO_ROOT / environment_receipt["file"]) == environment_receipt["sha256"]

    source_policy = {
        "watchtower": ("SOURCE_BOUNDED_REVIEW", "B", "COMMITTED_DERIVATION_RECEIPT"),
        "m1_elevated_bypass": ("SOURCE_BOUNDED_REVIEW", "B", "COMMITTED_DERIVATION_RECEIPT"),
        "romer_spaceport": ("PARTIAL_SOURCE_REVIEW", "MIXED_B_C", "PARTIAL_DERIVATION_RECEIPT"),
    }
    for item in receipt["assets"]:
        svg_path = REPO_ROOT / item["file"]
        assert svg_path.is_file()
        assert svg_path.stat().st_size == item["size_bytes"]
        assert sha256(svg_path) == item["sha256"]
        assert item["projection_input_obj_sha256"] == mesh_receipts[item["twin_id"]]["sha256"]
        assert item["type1_complete"] is False
        assert item["release_eligible"] is False

        raw_svg = svg_path.read_text(encoding="utf-8")
        root = ET.fromstring(raw_svg)
        assert root.attrib["width"] == "100%"
        assert root.attrib["height"] == "auto"
        assert root.attrib["viewBox"] == "0 0 1600 1000"
        assert root.attrib["preserveAspectRatio"] == "xMidYMin meet"
        assert root.attrib["role"] == "img"
        assert root.attrib["data-twin-id"] == item["twin_id"]
        assert root.attrib["data-drawing-id"].endswith(item["sheet_id"])
        assert root.attrib["data-representation-class"] == item["representation_class"]
        assert root.attrib["data-package-kind"] == item["package_kind"]
        assert root.attrib["data-evidence-ceiling"] == item["package_evidence_ceiling"]
        assert root.attrib["data-source-binding-state"] == item["source_binding_state"]
        assert root.attrib["data-dimension-authority"] == item["dimension_authority"]
        assert root.attrib["data-type1-complete"] == "false"
        assert root.attrib["data-release-eligible"] == "false"
        assert root.attrib["data-release-state"] == "REVIEW_ONLY_NOT_PUBLICLY_RELEASED"

        title = next(element for element in root if element.tag.endswith("title"))
        description = next(element for element in root if element.tag.endswith("desc"))
        assert root.attrib["aria-labelledby"] == f"{title.attrib['id']} {description.attrib['id']}"
        metadata_element = next(element for element in root if element.tag.endswith("metadata"))
        metadata = json.loads(metadata_element.text)
        assert metadata["projection_input_obj_sha256"] == item["projection_input_obj_sha256"]
        assert metadata["type1_complete"] is False and metadata["release_eligible"] is False

        groups = {child.attrib.get("id"): child for child in root if child.tag.endswith("g")}
        assert set(groups) == set(receipt["required_layers"])
        assert not any(element.tag.endswith("script") for element in root.iter())
        assert not any("href" in element.attrib for element in root.iter())

        if item["twin_id"] in proxy_ids:
            assert item["package_kind"] == "INTERACTION_PROXY_REVIEW_SHELL"
            assert item["package_evidence_ceiling"] == "E"
            assert item["source_binding_state"] == "NONE_PROXY_ONLY"
            assert item["dimension_authority"] == "NONE"
            assert "proxy_model_extents_m" in metadata and "derived_model_extents_m" not in metadata
            assert "INTERACTION PROXY / INCOMPLETE REVIEW SHELL" in raw_svg
            assert "source mesh hash" not in raw_svg.lower()
            assert "bounding dimensions are derived" not in raw_svg.lower()
            assert metadata["feature_addressability"] == "WHOLE_PROXY_ONLY"
            assert "data-feature-id=" not in raw_svg
            assert not any(element.attrib.get("class") == "geometry" for element in groups["L21-DERIVED-GEOMETRY"].iter())
            assert any(element.attrib.get("class") == "geometry" for element in groups["L22-PROVISIONAL-GEOMETRY"].iter())
            if item["sheet_id"] in {"T1-02", "T1-03", "T1-04", "T1-05", "T1-06"}:
                assert metadata["sheet_domain_state"] == "UNBOUND"
                assert "DOMAIN UNBOUND" in raw_svg
        else:
            kind, ceiling, binding = source_policy[item["twin_id"]]
            assert (item["package_kind"], item["package_evidence_ceiling"], item["source_binding_state"]) == (kind, ceiling, binding)
            assert "derived_model_extents_m" in metadata and "proxy_model_extents_m" not in metadata
            assert metadata["feature_addressability"] == "EDGE_LEVEL_DERIVED"

    gallery_path = REPO_ROOT / receipt["gallery"]["file"]
    assert gallery_path.is_file()
    assert gallery_path.stat().st_size == receipt["gallery"]["size_bytes"]
    assert sha256(gallery_path) == receipt["gallery"]["sha256"]
    gallery_parser = AnchorParser()
    gallery_parser.feed(gallery_path.read_text(encoding="utf-8"))
    assert len([href for href in gallery_parser.hrefs if href.endswith(".svg")]) == 128
    assert len([href for href in gallery_parser.hrefs if href.endswith(".obj")]) == 16
    assert len([href for href in gallery_parser.hrefs if href.endswith(".png")]) == 16
    for href in gallery_parser.hrefs:
        assert (gallery_path.parent / href).resolve().is_file(), href

    generator = load_type1_package_generator()
    regenerated = generator.generate_packages(
        REPO_ROOT / "assets" / "models",
        tmp_path / "type1-svg",
        tmp_path / "manifest.json",
    )
    for expected, actual in zip(receipt["assets"], regenerated, strict=True):
        assert actual["twin_id"] == expected["twin_id"]
        assert actual["sheet_id"] == expected["sheet_id"]
        assert actual["sha256"] == expected["sha256"]
        assert actual["size_bytes"] == expected["size_bytes"]


def test_ci_dependencies_and_actions_are_immutable():
    workflow = (REPO_ROOT / ".github" / "workflows" / "digital-twin-type1-validation.yml").read_text(encoding="utf-8")
    lock = (REPO_ROOT / "tools" / "digital-twin" / "requirements-ci-linux-py311.lock").read_text(encoding="utf-8")
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in workflow
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in workflow
    assert 'python-version: "3.11.9"' in workflow
    assert "--require-hashes --only-binary=:all:" in workflow
    assert 'branches: [main, "review/**"]' not in workflow
    assert lock.count("--hash=sha256:") == 8
