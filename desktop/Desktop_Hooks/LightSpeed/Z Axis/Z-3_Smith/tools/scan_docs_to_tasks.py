#!/usr/bin/env python3
# CODEX NOTE (2026-01-30):
# - This tool is part of the systematic Z-3 (Smith) execution layer: it turns doc markers into DB rows
#   and stages a Z Direct summary (and optionally staged task objects) for Trinity review.
# - Keep it safe for broad scans: the Z Direct per-task staging is capped to avoid huge JSONL writes.
"""
Scan Markdown/TXT documentation for actionable markers and store them in DB.

Targets:
- TODO / FIXME / TBD / COMING SOON / undefined / no attribute / not implemented
- Writes to Merovingian-owned tables: doc_task_markers (+ optional tasks rows)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def _find_lightspeed_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "config" / "unified_config.json").exists() and (parent / "Z Axis").exists():
            return parent
        if (parent / "LightSpeed" / "config" / "unified_config.json").exists() and (parent / "LightSpeed" / "Z Axis").exists():
            return parent / "LightSpeed"
    return start.resolve()


def _load_unified_config(ls_root: Path) -> Dict[str, Any]:
    p = ls_root / "config" / "unified_config.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _default_db_path(ls_root: Path) -> Path:
    cfg = _load_unified_config(ls_root)
    rel = (cfg.get("database") or {}).get("path")
    if rel:
        return (ls_root / rel).resolve()
    return (ls_root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").resolve()


DEFAULT_MARKERS: Sequence[Tuple[str, re.Pattern[str]]] = (
    ("TODO", re.compile(r"\bTODO\b", re.IGNORECASE)),
    ("FIXME", re.compile(r"\bFIXME\b", re.IGNORECASE)),
    ("TBD", re.compile(r"\bTBD\b", re.IGNORECASE)),
    ("COMING_SOON", re.compile(r"\bcoming soon\b", re.IGNORECASE)),
    ("NOT_IMPLEMENTED", re.compile(r"\bnot implemented\b", re.IGNORECASE)),
    ("UNDEFINED", re.compile(r"\bundefined\b", re.IGNORECASE)),
    ("NO_ATTRIBUTE", re.compile(r"\bno attribute\b", re.IGNORECASE)),
    ("PASS_STUB", re.compile(r"^\s*pass\s*(#.*)?$", re.IGNORECASE)),
)

DEFAULT_EXCLUDE_DIRS: Sequence[str] = (
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "ai_logs",
    "logs",
    "legacy",
    "archive",
    "conversations",
    "_crystallization_backup_20251214_224940",
    "z+4_firstrun",
    "z-1_dataflow",
    "z-2_intelligence",
    "z-3_interface",
)


@dataclass
class ScanResult:
    files_scanned: int = 0
    markers_found: int = 0
    markers_inserted: int = 0
    tasks_created: int = 0
    # Staged task payloads (capped) for Z Direct observability; DB remains the source of truth.
    created_task_payloads: List[Dict[str, Any]] = field(default_factory=list)


def _emit_z_direct_summary(ls_root: Path, *, scan_root: Path, res: ScanResult) -> None:
    """
    Best-effort: publish a summary event to Smith's Z Direct events stream.

    This keeps Z Direct observable even when the caller isn't running the full UI.
    """
    if not res or (res.markers_found == 0 and res.tasks_created == 0 and res.markers_inserted == 0):
        return

    try:
        sys.path.insert(0, str(ls_root))
        sys.path.insert(0, str(ls_root / "Z Axis"))
        sys.path.insert(0, str(ls_root / "Z Axis" / "Z-4_Merovingian"))

        from core.services import get_z_direct  # type: ignore

        zd = get_z_direct()
        env = zd.make_envelope(
            kind="event",
            channel="Z-3",
            z_context="Z-3_Smith",
            source="scan_docs_to_tasks",
            tags=["doc-marker", "smith"],
            payload={
                "scan_root": str(scan_root),
                "files_scanned": res.files_scanned,
                "markers_found": res.markers_found,
                "markers_inserted": res.markers_inserted,
                "tasks_created": res.tasks_created,
                "staged_task_payloads": len(res.created_task_payloads or []),
            },
        )
        zd.append_event("Z-3", env)

        # Optional: stage created tasks as Z Direct objects for Trinity review (capped).
        for task_obj in (res.created_task_payloads or []):
            try:
                obj_env = zd.make_envelope(
                    kind="object",
                    channel="Z-3",
                    z_context="Z-3_Smith",
                    source="scan_docs_to_tasks",
                    tags=["task", "doc-marker", "smith"],
                    payload=task_obj,
                )
                zd.append_object("Z-3", obj_env)
                # Push into Trinity's directed inbox for review/approval flows (best-effort).
                try:
                    zd.append_channel_outbox(from_channel="Z-3", to_channel="Z+3", payload=obj_env)
                except Exception:
                    pass
                try:
                    zd.append_channel_inbox(to_channel="Z+3", from_channel="Z-3", payload=obj_env)
                except Exception:
                    pass
            except Exception:
                continue
    except Exception:
        return


def _iter_doc_files(root: Path, include_exts: Sequence[str], exclude_dirs: Sequence[str]) -> Iterable[Path]:
    # Allow targeting a single file (used by Trinity context menus and quick scans).
    try:
        if root.is_file():
            if root.suffix.lower() in {e.lower() for e in include_exts}:
                yield root
            return
    except Exception:
        pass

    exclude = {d.lower() for d in exclude_dirs}
    include = {e.lower() for e in include_exts}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            parts = [p.lower() for p in path.parts]
            if any(p in exclude for p in parts):
                continue
        except Exception:
            pass
        if path.suffix.lower() in include:
            yield path


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


def scan_docs_to_db(
    *,
    db_path: Path,
    scan_root: Path,
    include_exts: Sequence[str] = (".md", ".txt"),
    exclude_dirs: Sequence[str] = (
        *DEFAULT_EXCLUDE_DIRS,
    ),
    markers: Sequence[Tuple[str, re.Pattern[str]]] = DEFAULT_MARKERS,
    create_tasks: bool = True,
    backfill_company_ids: bool = False,
) -> ScanResult:
    db_path = db_path.resolve()
    scan_root = scan_root.resolve()
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if not scan_root.exists():
        raise FileNotFoundError(f"Scan root not found: {scan_root}")

    res = ScanResult()
    now = datetime.datetime.now().isoformat()

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass

    try:
        cur = conn.cursor()
        # Discover optional columns (keeps tool compatible with older DBs)
        try:
            cur.execute("PRAGMA table_info(tasks)")
            task_cols = {str(r[1]) for r in (cur.fetchall() or []) if r and r[1]}
        except Exception:
            task_cols = set()

        company_ids: Dict[str, int] = {}
        if "company_id" in task_cols:
            try:
                cur.execute("SELECT id, name FROM companies")
                for rid, name in (cur.fetchall() or []):
                    if name:
                        company_ids[str(name).strip().lower()] = int(rid)
            except Exception:
                pass

        # Optional backfill: set tasks.company_id for existing tasks if null.
        if backfill_company_ids and "company_id" in task_cols and company_ids:
            try:
                cur.execute("SELECT id, metadata_json FROM tasks WHERE company_id IS NULL")
                rows = cur.fetchall() or []
                for tid, meta_json in rows:
                    try:
                        meta = json.loads(meta_json) if meta_json else {}
                    except Exception:
                        meta = {}
                    doc = str(meta.get("doc_marker_file") or "").lower()
                    detected = str(meta.get("company_detected") or "").strip().lower()
                    cid = None
                    if detected == "emassc" or "emassc" in doc:
                        cid = company_ids.get("emassc")
                    elif detected in {"romer industries", "römer industries"} or "romer" in doc or "römer" in doc:
                        cid = company_ids.get("romer industries") or company_ids.get("römer industries")
                    if cid:
                        cur.execute("UPDATE tasks SET company_id=?, updated_at=? WHERE id=?", (cid, now, int(tid)))
            except Exception:
                pass

        for file_path in _iter_doc_files(scan_root, include_exts, exclude_dirs):
            res.files_scanned += 1
            try:
                # Skip extremely large docs; scan only the head portion (prevents multi-GB reads).
                if file_path.stat().st_size > 20 * 1024 * 1024:
                    text = file_path.read_text(encoding="utf-8", errors="replace")[:2_000_000]
                else:
                    text = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            rel = str(file_path)
            inserted_for_file = 0
            hashes_for_file: List[str] = []

            for line_no, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                for marker_name, pat in markers:
                    if not pat.search(line):
                        continue
                    res.markers_found += 1
                    content = line.strip()
                    h = _sha256(f"{rel}:{line_no}:{marker_name}:{content}")
                    try:
                        cur.execute(
                            """
                            INSERT OR IGNORE INTO doc_task_markers (file_path, line_no, marker, content, hash_sha256, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (rel, int(line_no), marker_name, content[:2000], h, now),
                        )
                        if cur.rowcount:
                            res.markers_inserted += 1
                            inserted_for_file += 1
                            hashes_for_file.append(h)
                    except Exception:
                        continue

            if create_tasks and inserted_for_file:
                # One task per file when new markers were discovered (idempotent via metadata_json LIKE).
                meta = {
                    "source": "scan_docs_to_tasks",
                    "doc_marker_file": rel,
                    "doc_marker_hashes": hashes_for_file[:200],
                    "doc_marker_count": inserted_for_file,
                    "scanned_at": now,
                }
                try:
                    rel_like = rel.replace("\\", "\\\\")
                    cur.execute(
                        "SELECT id FROM tasks WHERE metadata_json LIKE ? LIMIT 1",
                        (f'%"doc_marker_file": "{rel_like}"%',),
                    )
                    if cur.fetchone() is None:
                        # Best-effort company classification from path/name.
                        company_id = None
                        low = rel.lower()
                        if "emassc" in low:
                            company_id = company_ids.get("emassc")
                            meta["company_detected"] = "EMASSC"
                        elif "romer" in low or "römer" in low:
                            company_id = company_ids.get("romer industries") or company_ids.get("römer industries")
                            meta["company_detected"] = "Romer Industries"

                        title = f"Resolve doc markers: {Path(rel).name}"
                        desc = f"Found {inserted_for_file} new marker(s) in {rel}"
                        if "company_id" in task_cols:
                            cur.execute(
                                """
                                INSERT INTO tasks (title, description, company_id, status, priority, created_at, updated_at, metadata_json)
                                VALUES (?, ?, ?, 'pending', 'normal', ?, ?, ?)
                                """,
                                (title, desc, company_id, now, now, json.dumps(meta, ensure_ascii=False)),
                            )
                        else:
                            cur.execute(
                                """
                                INSERT INTO tasks (title, description, status, priority, created_at, updated_at, metadata_json)
                                VALUES (?, ?, 'pending', 'normal', ?, ?, ?)
                                """,
                                (title, desc, now, now, json.dumps(meta, ensure_ascii=False)),
                            )
                        res.tasks_created += 1
                        # Stage a lightweight task object to Z Direct (capped) for Trinity review.
                        try:
                            task_id = int(cur.lastrowid or 0)
                        except Exception:
                            task_id = 0
                        if task_id and len(res.created_task_payloads) < 50:
                            res.created_task_payloads.append(
                                {
                                    "kind": "task",
                                    "id": str(task_id),
                                    "title": title,
                                    "status": "pending",
                                    "priority": "normal",
                                    "source": "scan_docs_to_tasks",
                                    "doc_marker_file": rel,
                                    "doc_marker_count": inserted_for_file,
                                    "created_at": now,
                                }
                            )
                except Exception:
                    pass

        conn.commit()
        return res
    finally:
        conn.close()


def main(argv: Optional[Iterable[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    here = Path(__file__).resolve()
    ls_root = _find_lightspeed_root(here)

    ap = argparse.ArgumentParser(description="Scan docs for TODO/FIXME/TBD markers and store in DB")
    ap.add_argument("--db", type=str, default=str(_default_db_path(ls_root)), help="Path to lightspeed_unified.db")
    ap.add_argument("--root", type=str, default=str(ls_root / "Z Axis"), help="Root directory to scan")
    ap.add_argument(
        "--oracle-inbox",
        action="store_true",
        help="Shortcut: scan Oracle inbox at `Z Axis/Z-2_Oracle/archive/inbox` (also implies --include-archive).",
    )
    ap.add_argument(
        "--include-archive",
        action="store_true",
        help="Include directories named 'archive' in the scan (excluded by default).",
    )
    ap.add_argument(
        "--include-conversations",
        action="store_true",
        help="Include directories named 'conversations' in the scan (excluded by default).",
    )
    ap.add_argument(
        "--include-ai-logs",
        action="store_true",
        help="Include directories named 'ai_logs' when scanning (excluded by default).",
    )
    ap.add_argument(
        "--ext",
        action="append",
        default=[],
        help="File extension to include (repeatable). Default: .md and .txt",
    )
    ap.add_argument("--no-tasks", action="store_true", help="Only store markers; do not create tasks rows")
    ap.add_argument("--backfill-company", action="store_true", help="Backfill tasks.company_id for existing tasks when possible")
    args = ap.parse_args(argv)

    scan_root = Path(args.root)
    if bool(args.oracle_inbox):
        scan_root = (ls_root / "Z Axis" / "Z-2_Oracle" / "archive" / "inbox").resolve()
        args.include_archive = True

    include_exts = (".md", ".txt")
    if args.ext:
        include_exts = tuple(
            (e if str(e).startswith(".") else f".{e}").lower().strip() for e in args.ext if str(e).strip()
        ) or include_exts

    exclude_dirs = list(DEFAULT_EXCLUDE_DIRS)
    if bool(args.include_archive):
        exclude_dirs = [d for d in exclude_dirs if d.lower() != "archive"]
    if bool(args.include_conversations):
        exclude_dirs = [d for d in exclude_dirs if d.lower() != "conversations"]
    if bool(args.include_ai_logs):
        exclude_dirs = [d for d in exclude_dirs if d.lower() != "ai_logs"]
    else:
        # If the scan root is already inside `ai_logs`, do not exclude it; the user
        # explicitly targeted that subtree.
        try:
            _ai_logs = (ls_root / "ai_logs").resolve()
            scan_root.resolve().relative_to(_ai_logs)
        except Exception:
            pass
        else:
            exclude_dirs = [d for d in exclude_dirs if d.lower() != "ai_logs"]

    res = scan_docs_to_db(
        db_path=Path(args.db),
        scan_root=scan_root,
        include_exts=include_exts,
        exclude_dirs=exclude_dirs,
        create_tasks=not args.no_tasks,
        backfill_company_ids=bool(args.backfill_company),
    )
    summary = {
        "files_scanned": res.files_scanned,
        "markers_found": res.markers_found,
        "markers_inserted": res.markers_inserted,
        "tasks_created": res.tasks_created,
    }
    print(json.dumps(summary, indent=2))
    _emit_z_direct_summary(ls_root, scan_root=scan_root, res=res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
