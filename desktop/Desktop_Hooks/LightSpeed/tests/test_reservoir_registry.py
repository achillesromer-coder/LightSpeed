from __future__ import annotations

from pathlib import Path

from lightspeed_runtime.contracts import ReservoirManifest
from lightspeed_runtime.reservoirs.registry import ReservoirRegistry


def test_bounded_reservoir_index_stops_source_iteration(monkeypatch, tmp_path: Path) -> None:
    source_paths = []
    for index in range(3):
        path = tmp_path / f"asset-{index}.md"
        path.write_text(f"asset {index}\n", encoding="utf-8")
        source_paths.append(path)

    def guarded_rglob(_root: Path, _pattern: str):
        yield source_paths[0]
        yield source_paths[1]
        raise AssertionError("bounded indexing consumed more files than requested")

    monkeypatch.setattr(Path, "rglob", guarded_rglob)
    registry = ReservoirRegistry()
    registry.register_source(
        ReservoirManifest(
            source_id="bounded",
            root_path=str(tmp_path),
            source_type="test",
            classification="reference",
        )
    )

    assets = registry.build_index("bounded", max_files=2)

    assert [asset.relative_path for asset in assets] == [
        "asset-0.md",
        "asset-1.md",
    ]
