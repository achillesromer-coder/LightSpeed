from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER = Path(__file__).with_name("freecad_inspect_worker.py")
FREECAD_BIN = Path(os.environ.get(
    "FREECAD_BIN",
    r"C:\Users\acc\Desktop\Programs\FreeCAD 1.0\bin",
))
FREECAD_CMD = FREECAD_BIN / "freecadcmd.exe"
FREECAD_PYTHON = FREECAD_BIN / "python.exe"
DEFAULT_ALLOWED_ROOTS = (
    Path(r"D:\LightSpeed"),
    Path(r"C:\Users\acc\Desktop"),
)


class FreeCADAdapterError(RuntimeError):
    pass


def _allowed_roots() -> tuple[Path, ...]:
    raw = os.environ.get("FREECAD_ALLOWED_ROOTS")
    if not raw:
        return DEFAULT_ALLOWED_ROOTS
    return tuple(Path(item).resolve() for item in raw.split(os.pathsep) if item.strip())


def _safe_fcstd_path(value: str | Path) -> Path:
    path = Path(value).expanduser().resolve()
    if path.suffix.lower() != ".fcstd":
        raise FreeCADAdapterError("only .FCStd documents are accepted")
    if not path.exists() or not path.is_file():
        raise FreeCADAdapterError(f"FCStd file not found: {path}")
    allowed = False
    for root in _allowed_roots():
        try:
            path.relative_to(root.resolve())
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        raise FreeCADAdapterError(
            "FCStd path is outside registered project roots; arbitrary path access is disabled"
        )
    return path


def probe_freecad() -> dict[str, Any]:
    exists = FREECAD_CMD.exists() and FREECAD_PYTHON.exists()
    result: dict[str, Any] = {
        "schema": "LIGHTSPEED-FREECAD-PROBE/0.1",
        "available": exists,
        "bin": str(FREECAD_BIN),
        "freecadcmd": str(FREECAD_CMD),
        "python": str(FREECAD_PYTHON),
        "read_only_adapter": exists,
    }
    if not exists:
        result["state"] = "missing"
        return result
    completed = subprocess.run(
        [str(FREECAD_CMD), "--version"],
        cwd=str(FREECAD_BIN),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
        check=False,
    )
    result["returncode"] = completed.returncode
    result["version"] = (completed.stdout or completed.stderr).strip()
    result["state"] = "available" if completed.returncode == 0 else "probe_failed"
    result["write_operations"] = "not_exposed"
    return result


def inspect_freecad_document(path: str | Path) -> dict[str, Any]:
    probe = probe_freecad()
    if not probe["available"] or probe.get("state") != "available":
        raise FreeCADAdapterError("FreeCAD headless runtime is not available")
    target = _safe_fcstd_path(path)
    completed = subprocess.run(
        [str(FREECAD_PYTHON), str(WORKER), str(target)],
        cwd=str(FREECAD_BIN),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise FreeCADAdapterError(
            f"FreeCAD inspection failed ({completed.returncode}): {completed.stderr.strip()}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise FreeCADAdapterError(f"FreeCAD worker returned invalid JSON: {exc}") from exc
    payload["adapter_probe"] = {
        "version": probe.get("version"),
        "freecadcmd": probe.get("freecadcmd"),
    }
    return payload


def extract_freecad_bom(path: str | Path) -> dict[str, Any]:
    inspection = inspect_freecad_document(path)
    rows = []
    for obj in inspection.get("objects", []):
        shape = obj.get("shape") or {}
        props = obj.get("properties") or {}
        if not shape and not any(key in props for key in ("PartNumber", "Material", "Description")):
            continue
        rows.append({
            "name": obj.get("name"),
            "label": obj.get("label"),
            "type_id": obj.get("type_id"),
            "part_number": props.get("PartNumber"),
            "material": props.get("Material"),
            "description": props.get("Description"),
            "solids": shape.get("solids"),
            "volume": shape.get("volume"),
            "area": shape.get("area"),
            "bbox_mm": shape.get("bbox_mm"),
        })
    return {
        "schema": "LIGHTSPEED-FREECAD-BOM/0.1",
        "document": inspection.get("document"),
        "rows": rows,
        "row_count": len(rows),
        "evidence_class": "derived_from_fcstd",
        "read_only": True,
        "authority_limit": (
            "This is a derived object/geometry summary for analysis and reconciliation. "
            "It is not an approved manufacturing, procurement, mass-properties, or release BOM."
        ),
    }


__all__ = [
    "FreeCADAdapterError",
    "probe_freecad",
    "inspect_freecad_document",
    "extract_freecad_bom",
]
