from __future__ import annotations
import argparse, csv, hashlib, json, mimetypes, os, shutil, tempfile, zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTROL_EXCLUDED = {"cgx/bootstrap.json", "cgx/manifest.json", "cgx/dbr.json"}
CANON_EXCLUDED_PREFIXES = ("overlays/", "cache/", "session/", "events/")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def dbr_hash(payload: dict[str, Any]) -> str:
    p = dict(payload)
    p.pop("dbr_root", None)
    return sha256_bytes(stable_json(p))


@dataclass
class Workspace:
    root: Path
    temp: tempfile.TemporaryDirectory | None = None

    def close(self) -> None:
        if self.temp:
            self.temp.cleanup()


def open_workspace(path: Path) -> Workspace:
    if path.is_dir():
        return Workspace(path)
    if path.suffix.lower() != ".cgx":
        raise ValueError("Expected a CGX directory or .cgx carrier")
    td = tempfile.TemporaryDirectory(prefix="cgx_")
    root = Path(td.name)
    with zipfile.ZipFile(path, "r") as z:
        z.extractall(root)
    return Workspace(root, td)


def write_carrier(root: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob("*")):
            if p.is_file():
                rel = p.relative_to(root).as_posix()
                if "/__pycache__/" in f"/{rel}" or rel.endswith(".pyc"):
                    continue
                z.write(p, rel)
    tmp.replace(output)


def load_json(root: Path, rel: str, default=None):
    p = root / rel
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(root: Path, rel: str, obj: Any) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if "/__pycache__/" in f"/{rel}" or rel.endswith(".pyc"):
            continue
        if rel in CONTROL_EXCLUDED:
            continue
        if rel.startswith(CANON_EXCLUDED_PREFIXES):
            continue
        yield rel, p


def compute_content_root(root: Path) -> tuple[str, list[dict[str, Any]]]:
    entries = []
    buf = bytearray()
    for rel, p in canonical_files(root):
        h = sha256_file(p)
        size = p.stat().st_size
        entries.append({"path": rel, "size_bytes": size, "sha256": h})
        buf.extend(rel.encode())
        buf.extend(b"\0")
        buf.extend(h.encode())
        buf.extend(b";")
    return sha256_bytes(bytes(buf)), entries


def type_profile(root: Path, path: Path) -> dict[str, Any]:
    reg = load_json(root, "cgx/type_registry.json", {"profiles": []})
    ext = path.suffix.lower().lstrip(".")
    for profile in reg.get("profiles", []):
        if ext in profile.get("extensions", []):
            return profile
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {"id": mime, "quadrant": "Q2", "z_min": 0, "extensions": [ext] if ext else []}


def parse_semantics(path: Path, profile: dict[str, Any]) -> dict[str, Any]:
    mime = profile.get("id")
    data: dict[str, Any] = {"media_type": mime, "source_name": path.name, "sha256": sha256_file(path)}
    if mime in ("text/plain", "text/markdown"):
        text = path.read_text(encoding="utf-8")
        data.update({"kind": "text", "char_count": len(text), "line_count": text.count("\n") + (1 if text else 0)})
    elif mime == "application/json":
        obj = json.loads(path.read_text(encoding="utf-8"))
        data.update({"kind": "tree", "json_type": type(obj).__name__, "semantic_hash": sha256_bytes(stable_json(obj))})
    elif mime == "text/csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        data.update({"kind": "table", "row_count": len(rows), "column_count": max((len(r) for r in rows), default=0)})
    else:
        data.update({"kind": "opaque"})
    return data


def topology_aggregate(root: Path) -> dict[str, Any]:
    topo = load_json(root, "cgx/topology.json", {})
    type_counts: dict[str, int] = {}
    quadrant_counts = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    bytes_total = 0
    object_count = 0
    for rel, p in canonical_files(root):
        object_count += 1
        bytes_total += p.stat().st_size
        ext = p.suffix.lower().lstrip(".") or "noext"
        type_counts[ext] = type_counts.get(ext, 0) + 1
        if rel.startswith(("README", "docs/", "spec/")):
            quadrant_counts["Q1"] += 1
        elif rel.startswith(("runtime/", "events/")):
            quadrant_counts["Q4"] += 1
        else:
            quadrant_counts["Q2"] += 1
    frontier = load_json(root, "cgx/frontier.json", {"frontier": []}).get("frontier", [])
    frontier_counts: dict[str, int] = {}
    for item in frontier:
        state = item.get("state", "unknown")
        frontier_counts[state] = frontier_counts.get(state, 0) + 1
    return {
        "object_count": object_count,
        "bytes_total": bytes_total,
        "type_counts": dict(sorted(type_counts.items())),
        "quadrant_counts": quadrant_counts,
        "frontier_counts": frontier_counts,
        "z_occupancy": topo.get("z_occupancy", {}),
    }


def refresh(root: Path, event: str | None = None, note: str | None = None) -> dict[str, Any]:
    manifest = load_json(root, "cgx/manifest.json", {})
    bootstrap = load_json(root, "cgx/bootstrap.json", {})
    previous_dbr = load_json(root, "cgx/dbr.json", {})
    content_root, entries = compute_content_root(root)
    if event:
        prev_state = int(str(bootstrap.get("state_id", "S0")).lstrip("S") or 0)
        state_id = f"S{prev_state + 1}"
    else:
        state_id = bootstrap.get("state_id", manifest.get("state_id", "S0"))
    manifest.update({
        "schema_version": "0.2",
        "state_id": state_id,
        "content_root_algorithm": "sha256(sorted path\\0hash; excludes bootstrap/manifest/dbr and overlay/cache/session)",
        "content_root": content_root,
        "file_count": len(entries),
        "files": entries,
        "aggregate": topology_aggregate(root),
    })
    bootstrap.update({"carrier_version": "0.2", "state_id": state_id, "content_root": content_root, "status": "living-phase-b-kernel"})
    dbr = dict(previous_dbr)
    if event:
        dbr = {
            "schema_version": "0.2",
            "object_id": bootstrap.get("object_id"),
            "state_id": state_id,
            "event": event,
            "content_root": content_root,
            "parent_dbr_root": previous_dbr.get("dbr_root"),
            "timestamp": now_iso(),
            "authority_state": "owner-project-reference",
            "note": note or event,
        }
        dbr["dbr_root"] = dbr_hash(dbr)
        event_path = root / "events" / f"{state_id}.json"
        save_json(root, event_path.relative_to(root).as_posix(), dbr)
    manifest["dbr_root"] = dbr.get("dbr_root")
    bootstrap["dbr_root"] = dbr.get("dbr_root")
    save_json(root, "cgx/manifest.json", manifest)
    save_json(root, "cgx/bootstrap.json", bootstrap)
    save_json(root, "cgx/dbr.json", dbr)
    return {"state_id": state_id, "content_root": content_root, "dbr_root": dbr.get("dbr_root"), "file_count": len(entries)}


def verify(root: Path) -> dict[str, Any]:
    manifest = load_json(root, "cgx/manifest.json", {})
    bootstrap = load_json(root, "cgx/bootstrap.json", {})
    dbr = load_json(root, "cgx/dbr.json", {})
    expected_root, entries = compute_content_root(root)
    errors = []
    manifest_map = {e["path"]: e for e in manifest.get("files", [])}
    current_paths = {e["path"] for e in entries}
    for e in entries:
        m = manifest_map.get(e["path"])
        if not m:
            errors.append(f"untracked:{e['path']}")
        elif m.get("sha256") != e["sha256"]:
            errors.append(f"hash:{e['path']}")
    for path in manifest_map:
        if path not in current_paths:
            errors.append(f"missing:{path}")
    if manifest.get("content_root") != expected_root: errors.append("manifest.content_root")
    if bootstrap.get("content_root") != expected_root: errors.append("bootstrap.content_root")
    if dbr.get("content_root") != expected_root: errors.append("dbr.content_root")
    if dbr.get("dbr_root") != dbr_hash(dbr): errors.append("dbr.root")
    return {"ok": not errors, "errors": errors, "computed_content_root": expected_root, "state_id": bootstrap.get("state_id"), "tracked": len(entries)}


def do_import(root: Path, source: Path, dest_name: str | None = None) -> dict[str, Any]:
    profile = type_profile(root, source)
    quadrant = profile.get("quadrant", "Q2")
    dest_name = dest_name or source.name
    dest = root / "payload" / quadrant / dest_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    sem = parse_semantics(dest, profile)
    sem.update({"quadrant": quadrant, "z": {"raw": 0, "typed": 1, "semantic": 2}, "epistemic_state": "sourced"})
    sidecar = root / "semantic" / quadrant / (dest_name + ".json")
    save_json(root, sidecar.relative_to(root).as_posix(), sem)
    return refresh(root, "import", f"Imported {source.name} into {quadrant}") | {"destination": dest.relative_to(root).as_posix(), "profile": profile.get("id")}


def do_export(root: Path, target: str, output: Path) -> dict[str, Any]:
    src = root / target
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(target)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, output)
    return {"source": target, "output": str(output), "sha256": sha256_file(output)}


def overlay_create(root: Path, overlay_id: str, source: Path | None = None, frontier_id: str | None = None) -> dict[str, Any]:
    od = root / "overlays" / overlay_id
    od.mkdir(parents=True, exist_ok=True)
    meta = {"overlay_id": overlay_id, "created": now_iso(), "frontier_id": frontier_id, "canonical_state_at_creation": load_json(root, "cgx/bootstrap.json", {}).get("state_id"), "status": "ephemeral"}
    if source:
        shutil.copy2(source, od / source.name)
        meta["source"] = source.name
        meta["source_sha256"] = sha256_file(source)
    save_json(root, f"overlays/{overlay_id}/overlay.json", meta)
    return meta


def resolve_overlay(root: Path, overlay_id: str, destination: str) -> dict[str, Any]:
    od = root / "overlays" / overlay_id
    if not od.exists():
        raise FileNotFoundError(overlay_id)
    candidates = [p for p in od.iterdir() if p.is_file() and p.name != "overlay.json"]
    if not candidates:
        raise ValueError("Overlay contains no resolvable payload")
    src = candidates[0]
    dest = root / destination
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    meta = load_json(root, f"overlays/{overlay_id}/overlay.json", {})
    meta.update({"status": "resolved", "resolved_at": now_iso(), "resolved_to": destination})
    save_json(root, f"overlays/{overlay_id}/overlay.json", meta)
    result = refresh(root, "resolve", f"Resolved overlay {overlay_id} to {destination}")
    return result | {"resolved_to": destination}


def frontier_list(root: Path) -> list[dict[str, Any]]:
    return load_json(root, "cgx/frontier.json", {"frontier": []}).get("frontier", [])


def inspect(root: Path) -> dict[str, Any]:
    b = load_json(root, "cgx/bootstrap.json", {})
    return {"object_id": b.get("object_id"), "display_name": b.get("display_name"), "namespace": b.get("namespace"), "state_id": b.get("state_id"), "content_root": b.get("content_root"), "dbr_root": b.get("dbr_root"), "aggregate": topology_aggregate(root), "frontier": frontier_list(root)}


def create_empty(path: Path, display_name: str = "Untitled CGX Filespace") -> None:
    path.mkdir(parents=True, exist_ok=True)
    oid = "cgx:local:" + sha256_bytes((display_name + now_iso()).encode())[:24]
    save_json(path, "cgx/type_registry.json", {"schema_version": "0.2", "profiles": []})
    save_json(path, "cgx/frontier.json", {"schema_version": "0.2", "frontier": [{"id": "extension.*", "state": "E3_extension_open"}]})
    save_json(path, "cgx/topology.json", {"schema_version": "0.2", "basis": "CGX-XY-Z-T-v0.1", "quadrants": {q: {"objects": []} for q in ("Q1","Q2","Q3","Q4")}, "z_occupancy": {f"Z{i}": False for i in range(8)}, "t": 0})
    save_json(path, "cgx/bootstrap.json", {"magic": "CGX-PROTOTYPE", "carrier_version": "0.2", "object_id": oid, "display_name": display_name, "namespace": "local", "state_id": "S0", "created": now_iso()})
    save_json(path, "cgx/dbr.json", {"schema_version": "0.2", "object_id": oid, "state_id": "S0", "event": "genesis", "content_root": "", "parent_dbr_root": None, "timestamp": now_iso(), "authority_state": "local"})
    d = load_json(path, "cgx/dbr.json")
    d["dbr_root"] = dbr_hash(d)
    save_json(path, "cgx/dbr.json", d)
    save_json(path, "cgx/manifest.json", {"schema_version": "0.2", "object_id": oid, "state_id": "S0", "files": []})
    refresh(path)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cgx", description="CGX Phase-B reference kernel")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("path"); c.add_argument("--name", default="Untitled CGX Filespace")
    for name in ("inspect", "verify", "frontier"):
        p = sub.add_parser(name); p.add_argument("path")
    p = sub.add_parser("import"); p.add_argument("path"); p.add_argument("source"); p.add_argument("--name")
    p = sub.add_parser("export"); p.add_argument("path"); p.add_argument("target"); p.add_argument("output")
    p = sub.add_parser("overlay"); p.add_argument("path"); p.add_argument("overlay_id"); p.add_argument("--source"); p.add_argument("--frontier")
    p = sub.add_parser("resolve"); p.add_argument("path"); p.add_argument("overlay_id"); p.add_argument("destination")
    p = sub.add_parser("pack"); p.add_argument("directory"); p.add_argument("output")
    a = ap.parse_args(argv)
    if a.cmd == "create":
        create_empty(Path(a.path), a.name); print(json.dumps({"ok": True, "path": a.path}, indent=2)); return
    if a.cmd == "pack":
        write_carrier(Path(a.directory), Path(a.output)); print(json.dumps({"ok": True, "output": a.output}, indent=2)); return
    ws = open_workspace(Path(a.path))
    try:
        root = ws.root
        if a.cmd == "inspect": result = inspect(root)
        elif a.cmd == "verify": result = verify(root)
        elif a.cmd == "frontier": result = frontier_list(root)
        elif a.cmd == "import": result = do_import(root, Path(a.source), a.name)
        elif a.cmd == "export": result = do_export(root, a.target, Path(a.output))
        elif a.cmd == "overlay": result = overlay_create(root, a.overlay_id, Path(a.source) if a.source else None, a.frontier)
        elif a.cmd == "resolve": result = resolve_overlay(root, a.overlay_id, a.destination)
        else: raise RuntimeError(a.cmd)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if ws.temp and a.cmd in {"import", "overlay", "resolve"}:
            write_carrier(root, Path(a.path))
    finally:
        ws.close()

if __name__ == "__main__":
    main()
