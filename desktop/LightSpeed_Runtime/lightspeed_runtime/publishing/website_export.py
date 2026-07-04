from __future__ import annotations

import json
from pathlib import Path

from lightspeed_runtime.publishing.romer_profile import build_romer_publish_manifest
from lightspeed_runtime.runtime import LightSpeedRuntime


def export_romer_dataspace(
    runtime: LightSpeedRuntime,
    output_dir: Path,
    *,
    overview: str,
    artifact_refs: list[dict] | None = None,
    dataset_refs: list[str] | None = None,
    visibility: str = "internal",
) -> Path:
    manifest = build_romer_publish_manifest(
        runtime,
        overview=overview,
        artifact_refs=artifact_refs,
        dataset_refs=dataset_refs,
        visibility=visibility,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "romer_manifest.json"
    output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return output_path
