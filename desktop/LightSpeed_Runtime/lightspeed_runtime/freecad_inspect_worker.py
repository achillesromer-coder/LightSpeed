from __future__ import annotations

import json
from pathlib import Path
import sys

import FreeCAD


def _quantity(value):
    try:
        return {"value": float(value.Value), "unit": str(value.Unit)}
    except Exception:
        return None


def _property_value(obj, name: str):
    try:
        type_id = obj.getTypeIdOfProperty(name)
        value = getattr(obj, name)
    except Exception:
        return None
    if type_id in {"App::PropertyString", "App::PropertyStringList"}:
        return value
    if type_id in {"App::PropertyBool", "App::PropertyInteger", "App::PropertyFloat"}:
        return value
    if type_id in {"App::PropertyLength", "App::PropertyDistance", "App::PropertyAngle"}:
        return _quantity(value)
    if type_id == "App::PropertyEnumeration":
        return str(value)
    return None


def inspect(path: Path) -> dict:
    doc = FreeCAD.openDocument(str(path))
    try:
        objects = []
        for obj in doc.Objects:
            record = {
                "name": obj.Name,
                "label": obj.Label,
                "type_id": obj.TypeId,
                "properties": {},
            }
            for prop in obj.PropertiesList:
                value = _property_value(obj, prop)
                if value is not None:
                    record["properties"][prop] = value
            if hasattr(obj, "Shape") and obj.Shape and not obj.Shape.isNull():
                box = obj.Shape.BoundBox
                record["shape"] = {
                    "solids": len(obj.Shape.Solids),
                    "faces": len(obj.Shape.Faces),
                    "edges": len(obj.Shape.Edges),
                    "volume": float(obj.Shape.Volume),
                    "area": float(obj.Shape.Area),
                    "bbox_mm": {
                        "x": float(box.XLength),
                        "y": float(box.YLength),
                        "z": float(box.ZLength),
                    },
                }
            if hasattr(obj, "Placement"):
                base = obj.Placement.Base
                record["placement_mm"] = {
                    "x": float(base.x),
                    "y": float(base.y),
                    "z": float(base.z),
                }
            objects.append(record)
        return {
            "schema": "LIGHTSPEED-FREECAD-INSPECTION/0.1",
            "document": {
                "name": doc.Name,
                "label": doc.Label,
                "file": str(path),
                "object_count": len(objects),
            },
            "objects": objects,
            "evidence_class": "derived_from_fcstd",
            "read_only": True,
            "authority_limit": (
                "Object metadata and geometry are derived from the FCStd file. "
                "This is not manufacturing certification or a released BOM."
            ),
        }
    finally:
        FreeCAD.closeDocument(doc.Name)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: freecad_inspect_worker.py <file.FCStd>")
    result = inspect(Path(sys.argv[1]).resolve())
    sys.stdout.write(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
