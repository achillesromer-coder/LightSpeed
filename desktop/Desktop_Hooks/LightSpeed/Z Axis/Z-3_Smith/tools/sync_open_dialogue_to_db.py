#!/usr/bin/env python3
"""
Sync Open Dialogue JSONL stream into the LightSpeed unified database.

Why:
- Open Dialogue is a lightweight, local-only JSONL log:
  `LightSpeed/ai_logs/open_dialogue/live_conversation.jsonl`
- Trinity already has a DB-backed chat browser (chat_conversations/chat_messages).
- This tool makes Open Dialogue searchable/exportable via that browser by writing
  Open Dialogue events into the DB tables in an idempotent way.

Schema targets (owned by Merovingian):
- chat_conversations(source, conversation_uid, ...)
- chat_messages(conversation_id, message_uid, ...)

Design:
- Idempotent inserts using UNIQUE constraints.
- Supports both `type=msg` and `type=review` events.
  - msg -> chat_messages(role=from, content_text=text)
  - review -> chat_messages(role="review", author_name=by, parent_uid=msg_id, content_text="DECISION: ...")
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _find_lightspeed_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in (cur, *cur.parents):
        try:
            if (parent / "N.py").exists() and (parent / "Z Axis").exists():
                return parent
        except Exception:
            continue
        # common shape: <repo>/LightSpeed/...
        try:
            if (parent / "LightSpeed" / "N.py").exists() and (parent / "LightSpeed" / "Z Axis").exists():
                return (parent / "LightSpeed").resolve()
        except Exception:
            continue
    return start.resolve()


def _load_unified_config(ls_root: Path) -> Dict[str, Any]:
    cfg_path = ls_root / "config" / "unified_config.json"
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _default_db_path(ls_root: Path) -> Path:
    cfg = _load_unified_config(ls_root)
    rel = (cfg.get("database") or {}).get("path")
    if rel:
        return (ls_root / rel).resolve()
    return (ls_root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").resolve()


def _default_open_dialogue_log(ls_root: Path) -> Path:
    return (ls_root / "ai_logs" / "open_dialogue" / "live_conversation.jsonl").resolve()


def _connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn


def _utc_now_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _jobs_table_exists(conn: sqlite3.Connection) -> bool:
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='jobs' LIMIT 1"
        ).fetchone()
        return bool(row)
    except Exception:
        return False


def _job_mark_running(conn: sqlite3.Connection, job_id: int) -> None:
    if not _jobs_table_exists(conn):
        return
    now = _utc_now_iso()
    try:
        conn.execute(
            "UPDATE jobs SET status=?, started_at=COALESCE(started_at, ?), updated_at=? WHERE id=?",
            ("running", now, now, int(job_id)),
        )
    except Exception:
        return


def _job_mark_done(conn: sqlite3.Connection, job_id: int, result: Dict[str, Any]) -> None:
    if not _jobs_table_exists(conn):
        return
    now = _utc_now_iso()
    try:
        conn.execute(
            "UPDATE jobs SET status=?, completed_at=COALESCE(completed_at, ?), result_json=?, error=NULL, updated_at=? WHERE id=?",
            ("completed", now, json.dumps(result, ensure_ascii=False), now, int(job_id)),
        )
    except Exception:
        return


def _job_mark_failed(conn: sqlite3.Connection, job_id: int, error: str) -> None:
    if not _jobs_table_exists(conn):
        return
    now = _utc_now_iso()
    try:
        conn.execute(
            "UPDATE jobs SET status=?, completed_at=COALESCE(completed_at, ?), error=?, updated_at=? WHERE id=?",
            ("failed", now, (error or "")[:4000], now, int(job_id)),
        )
    except Exception:
        return


def _iso_to_epoch(ts: str) -> Optional[float]:
    ts = (ts or "").strip()
    if not ts:
        return None
    try:
        # Accept "YYYY-MM-DDTHH:MM:SS" or with microseconds.
        dt = _dt.datetime.fromisoformat(ts)
        return dt.timestamp()
    except Exception:
        return None


def _read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def _upsert_conversation(
    conn: sqlite3.Connection,
    *,
    company_id: Optional[int],
    source: str,
    conversation_uid: str,
    title: str,
    create_time_ts: Optional[float],
    update_time_ts: Optional[float],
    metadata: Dict[str, Any],
) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO chat_conversations (
            company_id, source, conversation_uid, title, create_time_ts, update_time_ts, message_count, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, 0, ?)
        ON CONFLICT(source, conversation_uid) DO UPDATE SET
            company_id=COALESCE(excluded.company_id, chat_conversations.company_id),
            title=COALESCE(excluded.title, chat_conversations.title),
            create_time_ts=COALESCE(chat_conversations.create_time_ts, excluded.create_time_ts),
            update_time_ts=COALESCE(excluded.update_time_ts, chat_conversations.update_time_ts),
            metadata_json=COALESCE(excluded.metadata_json, chat_conversations.metadata_json)
        """,
        (
            company_id,
            source,
            conversation_uid,
            title,
            create_time_ts,
            update_time_ts,
            json.dumps(metadata, ensure_ascii=False),
        ),
    )
    cur.execute(
        "SELECT id FROM chat_conversations WHERE source=? AND conversation_uid=?",
        (source, conversation_uid),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError("Failed to resolve chat_conversations row after upsert.")
    return int(row[0])


def _insert_message(
    conn: sqlite3.Connection,
    *,
    conversation_id: int,
    message_uid: str,
    parent_uid: Optional[str],
    role: Optional[str],
    author_name: Optional[str],
    create_time_ts: Optional[float],
    content_text: Optional[str],
    content_json: Optional[Dict[str, Any]],
    metadata_json: Optional[Dict[str, Any]],
) -> bool:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO chat_messages (
                conversation_id, message_uid, parent_uid, role, author_name, create_time_ts, content_text, content_json, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                message_uid,
                parent_uid,
                role,
                author_name,
                create_time_ts,
                content_text,
                json.dumps(content_json, ensure_ascii=False) if content_json is not None else None,
                json.dumps(metadata_json, ensure_ascii=False) if metadata_json is not None else None,
            ),
        )
        return True
    except sqlite3.IntegrityError:
        return False


def _update_conversation_rollups(conn: sqlite3.Connection, conversation_id: int) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            COUNT(*),
            MIN(create_time_ts),
            MAX(create_time_ts)
        FROM chat_messages
        WHERE conversation_id=?
        """,
        (conversation_id,),
    )
    row = cur.fetchone() or (0, None, None)
    count, min_ts, max_ts = int(row[0] or 0), row[1], row[2]
    cur.execute(
        """
        UPDATE chat_conversations
        SET message_count=?,
            create_time_ts=COALESCE(create_time_ts, ?),
            update_time_ts=COALESCE(?, update_time_ts)
        WHERE id=?
        """,
        (count, min_ts, max_ts, conversation_id),
    )


def sync_open_dialogue_to_db(
    *,
    db_path: Path,
    log_path: Path,
    company_id: Optional[int] = None,
    source: str = "open_dialogue",
    conversation_uid: str = "live_conversation",
    title: str = "Open Dialogue (live)",
    include_reviews: bool = True,
    job_id: Optional[int] = None,
) -> Dict[str, Any]:
    events = list(_read_jsonl(log_path))
    msg_events = [e for e in events if e.get("type") == "msg"]
    review_events = [e for e in events if include_reviews and e.get("type") == "review"]

    # Estimate conversation timestamps from message events.
    times = [t for t in (_iso_to_epoch(str(e.get("ts") or "")) for e in msg_events) if t is not None]
    create_ts = min(times) if times else None
    update_ts = max(times) if times else None

    meta = {"log_path": str(log_path), "include_reviews": bool(include_reviews)}

    inserted_msgs = 0
    inserted_reviews = 0

    result: Dict[str, Any]
    try:
        with _connect_db(db_path) as conn:
            if job_id is not None:
                _job_mark_running(conn, int(job_id))

            conv_id = _upsert_conversation(
                conn,
                company_id=company_id,
                source=source,
                conversation_uid=conversation_uid,
                title=title,
                create_time_ts=create_ts,
                update_time_ts=update_ts,
                metadata=meta,
            )

            for e in msg_events:
                mid = str(e.get("id") or "").strip()
                if not mid:
                    continue
                ts = _iso_to_epoch(str(e.get("ts") or ""))
                sender = str(e.get("from") or "").strip()
                recipient = str(e.get("to") or "").strip()
                text = str(e.get("text") or "")
                meta_obj = e.get("meta") if isinstance(e.get("meta"), dict) else {}
                parent_uid = None
                if isinstance(meta_obj, dict):
                    parent_uid = str(meta_obj.get("in_reply_to") or "").strip() or None
                ok = _insert_message(
                    conn,
                    conversation_id=conv_id,
                    message_uid=mid,
                    parent_uid=parent_uid,
                    role=sender or None,
                    author_name=sender or None,
                    create_time_ts=ts,
                    content_text=text,
                    content_json=None,
                    metadata_json={"to": recipient, "meta": meta_obj} if (recipient or meta_obj) else None,
                )
                if ok:
                    inserted_msgs += 1

            for e in review_events:
                rid = str(e.get("id") or "").strip()
                if not rid:
                    continue
                ts = _iso_to_epoch(str(e.get("ts") or ""))
                by = str(e.get("by") or "").strip()
                msg_id = str(e.get("msg_id") or "").strip() or None
                decision = str(e.get("decision") or "").strip()
                reply = str(e.get("reply") or "").strip()
                text = f"REVIEW: {decision}"
                if reply:
                    text += f"\n\n{reply}"
                ok = _insert_message(
                    conn,
                    conversation_id=conv_id,
                    message_uid=rid,
                    parent_uid=msg_id,
                    role="review",
                    author_name=by or None,
                    create_time_ts=ts,
                    content_text=text,
                    content_json=None,
                    metadata_json={"decision": decision, "reply": reply, "msg_id": msg_id} if (decision or reply or msg_id) else None,
                )
                if ok:
                    inserted_reviews += 1

            _update_conversation_rollups(conn, conv_id)
            conn.commit()

        result = {
            "db_path": str(db_path),
            "log_path": str(log_path),
            "conversation_uid": conversation_uid,
            "inserted_messages": inserted_msgs,
            "inserted_reviews": inserted_reviews,
            "events_seen": len(events),
        }
    except Exception as exc:
        # Best-effort failure update.
        try:
            with _connect_db(db_path) as conn2:
                if job_id is not None:
                    _job_mark_failed(conn2, int(job_id), str(exc))
                    conn2.commit()
        except Exception:
            pass
        raise

    # Best-effort job row update for UI dashboards (Smith).
    try:
        with _connect_db(db_path) as conn2:
            if job_id is not None:
                _job_mark_done(conn2, int(job_id), result)
                conn2.commit()
    except Exception:
        pass

    return result


def main(argv: Optional[List[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Sync Open Dialogue JSONL into LightSpeed DB")
    parser.add_argument("--db", type=str, default="", help="Path to lightspeed_unified.db")
    parser.add_argument("--log", type=str, default="", help="Path to Open Dialogue live_conversation.jsonl")
    parser.add_argument("--company-id", type=int, default=0, help="Optional company_id for chat_conversations")
    parser.add_argument("--no-reviews", action="store_true", help="Do not import review events")
    parser.add_argument("--job-id", type=int, default=0, help="Optional jobs.id to update status/result_json")
    args = parser.parse_args(argv)

    ls_root = _find_lightspeed_root(Path.cwd())
    db = Path(args.db).resolve() if args.db else _default_db_path(ls_root)
    log = Path(args.log).resolve() if args.log else _default_open_dialogue_log(ls_root)
    company_id = args.company_id or None
    job_id = args.job_id or None

    res = sync_open_dialogue_to_db(
        db_path=db,
        log_path=log,
        company_id=company_id,
        include_reviews=(not bool(args.no_reviews)),
        job_id=job_id,
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
