from __future__ import annotations

from itertools import islice
from pathlib import Path
import hashlib

from lightspeed_runtime.contracts import AssetRecord, ReservoirManifest, utc_now_iso


TEXT_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".csv", ".html", ".py", ".jsx", ".yaml", ".yml"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".xlsx"}


class ReservoirRegistry:
    def __init__(self) -> None:
        self._manifests: dict[str, ReservoirManifest] = {}
        self._assets_by_source: dict[str, list[AssetRecord]] = {}

    def register_source(self, manifest: ReservoirManifest) -> None:
        self._manifests[manifest.source_id] = manifest
        self._assets_by_source.setdefault(manifest.source_id, [])

    def build_index(self, source_id: str, max_files: int | None = None) -> list[AssetRecord]:
        manifest = self._manifests[source_id]
        root = Path(manifest.root_path)
        assets: list[AssetRecord] = []
        if not root.exists():
            manifest.index_status = "missing"
            manifest.last_scan_at = utc_now_iso()
            self._assets_by_source[source_id] = []
            return []

        candidates = (path for path in root.rglob("*") if path.is_file())
        if max_files is None:
            files = list(candidates)
        else:
            files = list(islice(candidates, max(0, max_files)))
        files.sort(key=lambda item: str(item).lower())

        for path in files:
            relative_path = path.relative_to(root).as_posix()
            title = path.stem.replace("_", " ").replace("-", " ")
            canonical_rank = self._rank_asset(manifest, relative_path)
            preview_ref = relative_path if self._media_type(path) in {"text", "image", "document"} else None
            asset = AssetRecord(
                asset_id=self._asset_id(source_id, relative_path),
                source_id=source_id,
                relative_path=relative_path,
                media_type=self._media_type(path),
                title=title,
                summary=f"{manifest.source_type} asset from {relative_path}",
                canonical_rank=canonical_rank,
                provenance={
                    "source_root": manifest.root_path,
                    "indexed_at": utc_now_iso(),
                    "classification": manifest.classification,
                },
                related_projects=list(manifest.project_tags),
                related_workspaces=list(manifest.workspace_tags),
                preview_ref=preview_ref,
            )
            assets.append(asset)

        manifest.index_status = "indexed"
        manifest.last_scan_at = utc_now_iso()
        self._assets_by_source[source_id] = assets
        return assets

    def get_assets(self, source_id: str) -> list[AssetRecord]:
        return list(self._assets_by_source.get(source_id, []))

    def manifests(self) -> list[ReservoirManifest]:
        return list(self._manifests.values())

    def preview_asset(self, source_id: str, asset_id: str, *, max_chars: int = 2000) -> dict:
        manifest = self._manifests[source_id]
        asset = next((item for item in self.get_assets(source_id) if item.asset_id == asset_id), None)
        if asset is None:
            raise KeyError(f"Unknown asset id: {asset_id}")

        absolute_path = Path(manifest.root_path) / Path(asset.relative_path)
        payload = {
            "asset": asset.to_dict(),
            "absolute_path": str(absolute_path),
            "preview_kind": asset.media_type,
        }

        if not absolute_path.exists():
            payload["preview"] = "Asset file is missing on disk."
            return payload

        if asset.media_type == "text":
            try:
                payload["preview"] = absolute_path.read_text(encoding="utf-8", errors="replace")[:max_chars]
            except Exception as exc:
                payload["preview"] = f"Preview unavailable: {exc}"
            return payload

        if asset.media_type == "document":
            payload["preview"] = f"Document preview not extracted yet. Source file: {absolute_path.name}"
            return payload

        if asset.media_type == "image":
            payload["preview"] = f"Image asset available at {absolute_path}"
            return payload

        payload["preview"] = f"Binary asset available at {absolute_path}"
        return payload

    def _media_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in TEXT_EXTENSIONS:
            return "text"
        if suffix in IMAGE_EXTENSIONS:
            return "image"
        if suffix in DOCUMENT_EXTENSIONS:
            return "document"
        return "binary"

    def _rank_asset(self, manifest: ReservoirManifest, relative_path: str) -> str:
        lowered = relative_path.lower()
        trusted = [entry.lower() for entry in manifest.trusted_documents]
        if any(item in lowered for item in trusted):
            return "canonical"
        if any(marker in lowered for marker in ("archive", "legacy", "old")):
            return "archive"
        if manifest.classification == "canonical":
            return "canonical"
        if manifest.classification == "archive":
            return "archive"
        return "reference"

    def _asset_id(self, source_id: str, relative_path: str) -> str:
        digest = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:12]
        return f"{source_id}_{digest}"
