"""Render deterministic six-view PNG review sheets for Atrium OBJ assets.

These wireframe sheets are visual-review derivatives only. They do not promote
an interaction proxy to engineering, manufacturing, empirical, or release
authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_ROOT = REPO_ROOT / "assets" / "models"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "assets" / "previews"
DEFAULT_MANIFEST = REPO_ROOT / "data" / "digital-twin" / "generated_preview_manifest_v1.json"
VIEWS = {
    "TOP": ([0, 0, 1], [0, 1, 0]),
    "BOTTOM": ([0, 0, -1], [0, 1, 0]),
    "LEFT": ([-1, 0, 0], [0, 0, 1]),
    "RIGHT": ([1, 0, 0], [0, 0, 1]),
    "TOP LEFT": ([-1, -1, 1], [0, 0, 1]),
    "TOP RIGHT": ([1, -1, 1], [0, 0, 1]),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixel_sha256(path):
    with Image.open(path) as image:
        return hashlib.sha256(image.convert("RGB").tobytes()).hexdigest()


def display_path(path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def projection_basis(direction, up_hint):
    direction = np.asarray(direction, dtype=float)
    direction /= np.linalg.norm(direction)
    up_hint = np.asarray(up_hint, dtype=float)
    right = np.cross(up_hint, direction)
    right /= np.linalg.norm(right)
    up = np.cross(direction, right)
    up /= np.linalg.norm(up)
    return right, up


def project(vertices, direction, up_hint):
    right, up = projection_basis(direction, up_hint)
    centred = vertices - vertices.mean(axis=0)
    return np.column_stack((centred @ right, centred @ up))


def draw_view(draw, mesh, bounds, label):
    x0, y0, x1, y1 = bounds
    pad = 28
    direction, up_hint = VIEWS[label]
    points = project(np.asarray(mesh.vertices), direction, up_hint)
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    span = np.maximum(maxs - mins, 1e-9)
    scale = min((x1 - x0 - 2 * pad) / span[0], (y1 - y0 - 2 * pad - 18) / span[1])
    origin = np.array([(x0 + x1) / 2, (y0 + y1 + 18) / 2])
    screen = (points - (mins + maxs) / 2) * np.array([scale, -scale]) + origin
    draw.rectangle(bounds, outline=(47, 79, 90), width=1)
    for start, end in np.asarray(mesh.edges_unique):
        a, b = screen[start], screen[end]
        draw.line((float(a[0]), float(a[1]), float(b[0]), float(b[1])), fill=(118, 219, 210), width=1)
    label_y = y0 + (40 if y0 == 0 else 8)
    draw.text((x0 + 10, label_y), label, fill=(239, 248, 248), font=ImageFont.load_default())


def render_sheet(model_path, output_path, twin_id):
    loaded = trimesh.load_mesh(model_path, process=False)
    mesh = loaded.dump(concatenate=True) if isinstance(loaded, trimesh.Scene) else loaded
    image = Image.new("RGB", (1200, 800), (6, 12, 15))
    draw = ImageDraw.Draw(image)
    labels = list(VIEWS)
    for index, label in enumerate(labels):
        column, row = index % 3, index // 3
        draw_view(draw, mesh, (column * 400, row * 400, (column + 1) * 400 - 1, (row + 1) * 400 - 1), label)
    title = twin_id.replace("_", " ").upper()
    draw.rectangle((0, 0, 1200, 32), fill=(8, 24, 30))
    draw.text((14, 10), f"{title} · REVIEW DERIVATIVE · NOT ENGINEERING AUTHORITY", fill=(154, 226, 170), font=ImageFont.load_default())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=False, compress_level=9)


def generate_previews(model_root, output_root, manifest_output):
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    assets = []
    for model_path in sorted(model_root.glob("*.obj")):
        twin_id = model_path.stem
        output_path = output_root / f"{twin_id}_six_view.png"
        render_sheet(model_path, output_path, twin_id)
        assets.append({
            "twin_id": twin_id,
            "source_obj": display_path(model_path),
            "file": display_path(output_path),
            "format": "PNG",
            "views": list(VIEWS),
            "width": 1200,
            "height": 800,
            "size_bytes": output_path.stat().st_size,
            "sha256": sha256(output_path),
            "pixel_sha256": pixel_sha256(output_path),
            "claim_boundary": "visual review derivative; not engineering or physical validation evidence",
        })
    receipt = {
        "schema": "achilles_six_view_preview_receipt_v1",
        "generator": "tools/digital-twin/render_atrium_views.py",
        "dependencies": {"numpy": np.__version__, "pillow": Image.__version__, "trimesh": trimesh.__version__},
        "assets": assets,
    }
    manifest_output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    return assets


def parse_args(arguments: Iterable[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-root", type=Path, default=DEFAULT_MODEL_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args(arguments)


def main(arguments: Iterable[str] | None = None):
    args = parse_args(arguments)
    assets = generate_previews(args.model_root, args.output_root, args.manifest_output)
    if len(assets) != 16:
        raise SystemExit(f"expected 16 OBJ assets, found {len(assets)}")
    print(json.dumps({"rendered": len(assets), "output_root": display_path(args.output_root), "manifest": display_path(args.manifest_output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
