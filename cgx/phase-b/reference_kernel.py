from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

GENERATED = {"cgx/bootstrap.json", "cgx/manifest.json", "cgx/dbr.json"}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def jdump(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fsha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def extract(cgx: Path) -> Path:
    root = Path(tempfile.mkdtemp(prefix="cgx_"))
    with zipfile.ZipFile(cgx) as z:
        z.extractall(root)
    return root


def repack(root: Path, cgx: Path) -> None:
    tmp = cgx.with_suffix(cgx.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(root.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(root).as_posix())
    tmp.replace(cgx)


def objects(root: Path) -> dict:
    return load(root / "cgx/objects.json", {"objects": {}}).get("objects", {})


def write_objects(root: Path, value: dict) -> None:
    save(root / "cgx/objects.json", {"schema_version": "0.1", "objects": value})


def semantic_root(value: dict) -> str:
    active = {
        oid: {
            "sha256": o.get("sha256"),
            "blob": o.get("blob"),
            "logical_path": o.get("logical_path"),
            "type": o.get("type"),
            "quadrant": o.get("quadrant"),
            "z": o.get("z"),
            "parent": o.get("parent"),
            "epistemic": o.get("epistemic", "sourced"),
        }
        for oid, o in sorted(value.items())
        if o.get("status", "active") == "active"
    }
    return sha(jdump(active))


def package_root(root: Path) -> str:
    rows = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel in GENERATED:
            continue
        rows.append(f"{rel}\0{fsha(p)}")
    return sha(";".join(rows).encode())


def dbr_hash(record: dict) -> str:
    return sha(jdump({k: v for k, v in record.items() if k != "dbr_root"}))


def classify(path: Path, registry: dict) -> dict:
    ext = path.suffix.lower().lstrip(".")
    for p in registry.get("profiles", []):
        if ext in [x.lower() for x in p.get("extensions", [])]:
            return p
    return {"id": "application/octet-stream", "quadrant": "Q2", "z_min": 0, "extensions": [ext]}


def parent_for(profile: dict) -> str:
    name = {
        "Q1": "symbolic-document",
        "Q2": "structured-compute",
        "Q3": "media-spatial",
        "Q4": "active-operational",
    }.get(profile.get("quadrant"), "structured-compute")
    return name + "/" + profile.get("id", "application.octet-stream").replace("/", ".")


def slot(logical_path: str) -> str:
    # Local slot is only chosen after semantic family/domain placement.
    return hashlib.blake2s(logical_path.casefold().encode(), digest_size=4).hexdigest()


def derive(path: Path) -> dict:
    ext = path.suffix.lower()
    out = {"derivation": "deterministic-v0.1"}
    if ext in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8")
        out.update(characters=len(text), lines=len(text.splitlines()))
    elif ext == ".json":
        v = json.loads(path.read_text(encoding="utf-8"))
        out.update(json_kind=type(v).__name__, top_level_count=len(v) if hasattr(v, "__len__") else None)
    elif ext == ".csv":
        with path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        out.update(rows=len(rows), columns_max=max((len(r) for r in rows), default=0), header=rows[0] if rows else [])
    return out


def aggregate(active: dict, overlay_count=0) -> dict:
    a = {"object_count": 0, "bytes": 0, "type_counts": {}, "quadrant_counts": {}, "z_counts": {}, "epistemic_counts": {}, "overlay_count": overlay_count}
    for o in active.values():
        if o.get("status", "active") != "active":
            continue
        a["object_count"] += 1
        a["bytes"] += int(o.get("size_bytes", 0))
        for field, bucket in (("type", "type_counts"), ("quadrant", "quadrant_counts"), ("epistemic", "epistemic_counts")):
            v = str(o.get(field, "unknown"))
            a[bucket][v] = a[bucket].get(v, 0) + 1
        z = "Z" + str(o.get("z", 0))
        a["z_counts"][z] = a["z_counts"].get(z, 0) + 1
    return a


def add_event(root: Path, action: str, detail: dict) -> dict:
    path = root / "cgx/events/events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    seq = sum(1 for _ in path.open("r", encoding="utf-8")) if path.exists() else 0
    e = {"seq": seq + 1, "timestamp": now_iso(), "action": action, **detail}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, sort_keys=True) + "\n")
    return e


def finalise(root: Path, action: str, detail: dict) -> dict:
    objs = objects(root)
    overlays = load(root / "cgx/overlays.json", {"overlays": {}}).get("overlays", {})
    sr = semantic_root(objs)
    state = load(root / "cgx/state.json", {"sequence": -1})
    seq = int(state.get("sequence", -1)) + 1
    sid = f"S{seq}"
    ev = add_event(root, action, {"state_id": sid, "state_root": sr, **detail})
    save(root / "cgx/state.json", {"schema_version": "0.1", "state_id": sid, "sequence": seq, "state_root": sr, "updated": ev["timestamp"]})
    save(root / f"cgx/states/{sid}.json", {"state_id": sid, "state_root": sr, "objects": objs})
    save(root / "cgx/aggregates.json", {"schema_version": "0.1", **aggregate(objs, len(overlays))})

    pr = package_root(root)
    boot = load(root / "cgx/bootstrap.json", {})
    boot.update(carrier_version="0.2", state_id=sid, state_root=sr, content_root=pr, status="living-phase-b-kernel")
    prev = load(root / "cgx/dbr.json", {}).get("dbr_root")
    dbr = {
        "schema_version": "0.2",
        "object_id": boot.get("object_id"),
        "state_id": sid,
        "state_root": sr,
        "content_root": pr,
        "parent_dbr_root": prev,
        "event": action,
        "timestamp": ev["timestamp"],
        "signature_state": "unsigned-prototype",
    }
    dbr["dbr_root"] = dbr_hash(dbr)
    boot["dbr_root"] = dbr["dbr_root"]
    save(root / "cgx/bootstrap.json", boot)
    save(root / "cgx/dbr.json", dbr)

    tracked = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.relative_to(root).as_posix() not in GENERATED:
            tracked.append({"path": p.relative_to(root).as_posix(), "size_bytes": p.stat().st_size, "sha256": fsha(p)})
    save(root / "cgx/manifest.json", {"schema_version": "0.2", "object_id": boot.get("object_id"), "state_id": sid, "state_root": sr, "content_root": pr, "dbr_root": dbr["dbr_root"], "tracked_files": tracked})
    return {"state_id": sid, "state_root": sr, "content_root": pr, "dbr_root": dbr["dbr_root"]}


def import_payload(root: Path, source: Path, logical_path: str, overlay=False) -> dict:
    reg = load(root / "cgx/type_registry.json", {"profiles": []})
    profile = classify(source, reg)
    raw = source.read_bytes()
    digest = sha(raw)
    blob_rel = f"payload/blobs/{digest[:2]}/{digest}"
    blob = root / blob_rel
    blob.parent.mkdir(parents=True, exist_ok=True)
    if not blob.exists():
        blob.write_bytes(raw)
    oid = "obj:" + digest[:24]
    parent = parent_for(profile)
    rec = {
        "object_id": oid,
        "logical_path": logical_path,
        "blob": blob_rel,
        "sha256": digest,
        "size_bytes": len(raw),
        "type": profile.get("id"),
        "quadrant": profile.get("quadrant"),
        "z": max(1, int(profile.get("z_min", 0))),
        "parent": parent,
        "topology_path": f"{profile.get('quadrant')}/{parent}/{slot(logical_path)}",
        "epistemic": "sourced",
        "status": "overlay" if overlay else "active",
        "semantics": derive(source),
    }
    if overlay:
        ov = load(root / "cgx/overlays.json", {"schema_version": "0.1", "overlays": {}})
        overlay_id = "ovl:" + sha((oid + logical_path + now_iso()).encode())[:20]
        rec["overlay_id"] = overlay_id
        ov["overlays"][overlay_id] = rec
        save(root / "cgx/overlays.json", ov)
        return rec
    all_objects = objects(root)
    all_objects[oid] = rec
    write_objects(root, all_objects)
    return rec


def verify(root: Path) -> dict:
    manifest = load(root / "cgx/manifest.json", {})
    boot = load(root / "cgx/bootstrap.json", {})
    dbr = load(root / "cgx/dbr.json", {})
    errors = []
    for row in manifest.get("tracked_files", manifest.get("files", [])):
        p = root / row["path"]
        if not p.exists(): errors.append("missing:" + row["path"])
        elif fsha(p) != row["sha256"]: errors.append("hash:" + row["path"])
    pr = package_root(root)
    if manifest.get("content_root") and manifest["content_root"] != pr: errors.append("content_root")
    if boot.get("content_root") and boot["content_root"] != pr: errors.append("bootstrap.content_root")
    if dbr.get("content_root") and dbr["content_root"] != pr: errors.append("dbr.content_root")
    if dbr.get("dbr_root") and dbr_hash(dbr) != dbr["dbr_root"]: errors.append("dbr_root")
    sr = semantic_root(objects(root))
    if boot.get("state_root") and boot["state_root"] != sr: errors.append("state_root")
    return {"ok": not errors, "errors": errors, "content_root": pr, "state_root": sr, "dbr_root": dbr.get("dbr_root")}


def main():
    p = argparse.ArgumentParser(prog="cgx-ref")
    sub = p.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("verify"); x.add_argument("cgx")
    x = sub.add_parser("inspect"); x.add_argument("cgx")
    a = p.parse_args()
    root = extract(Path(a.cgx))
    try:
        if a.cmd == "verify": print(json.dumps(verify(root), indent=2))
        else:
            print(json.dumps({
                "bootstrap": load(root / "cgx/bootstrap.json", {}),
                "state": load(root / "cgx/state.json", {}),
                "aggregates": load(root / "cgx/aggregates.json", {}),
                "frontier": load(root / "cgx/frontier.json", {}),
            }, indent=2))
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
