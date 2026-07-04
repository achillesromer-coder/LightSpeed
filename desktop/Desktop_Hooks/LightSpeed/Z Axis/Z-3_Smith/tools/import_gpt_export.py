#!/usr/bin/env python3
"""
Import a ChatGPT "GPT Export" conversations.json into LightSpeed DB.

Design goals:
- Streaming JSON parsing (does not load the full ~300MB file into memory)
- Idempotent inserts (safe to re-run)
- DB schema is owned by Merovingian (Z-4) but this tool is executed from Smith (Z-3)
"""

from __future__ import annotations

import argparse
import codecs
import datetime
import json
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, Optional, Tuple


def _find_lightspeed_root(start: Path) -> Path:
    cur = start.resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "config" / "unified_config.json").exists() and (parent / "Z Axis").exists():
            return parent
        # common shape: <repo>/LightSpeed/...
        if (parent / "LightSpeed" / "config" / "unified_config.json").exists() and (parent / "LightSpeed" / "Z Axis").exists():
            return parent / "LightSpeed"
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


def _default_export_path(ls_root: Path) -> Path:
    return (
        ls_root
        / "Z Axis"
        / "Z-2_Oracle"
        / "archive"
        / "conversations"
        / "GPT_Export_2025-11-16"
        / "conversations.json"
    ).resolve()


@dataclass
class StreamProgress:
    bytes_read: int = 0
    file_size: int = 0
    conversations_seen: int = 0
    messages_seen: int = 0
    conversations_upserted: int = 0
    messages_upserted: int = 0
    started_at: float = 0.0

    @property
    def pct(self) -> float:
        if not self.file_size:
            return 0.0
        return min(100.0, (self.bytes_read / self.file_size) * 100.0)


class JsonArrayStream:
    """
    Stream a JSON array from disk using JSONDecoder.raw_decode on a rolling buffer.
    This supports very large arrays without loading everything into memory.
    """

    def __init__(self, path: Path, chunk_bytes: int = 1 << 20):
        self.path = path
        self.chunk_bytes = max(64 * 1024, int(chunk_bytes))
        self._decoder = json.JSONDecoder()
        self._text_buf = ""
        self._pos = 0
        self._started = False
        self._done = False
        self._byte_decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self.progress = StreamProgress(file_size=path.stat().st_size, started_at=time.time())

    def _refill(self, f) -> bool:
        chunk = f.read(self.chunk_bytes)
        if not chunk:
            return False
        self.progress.bytes_read += len(chunk)
        self._text_buf += self._byte_decoder.decode(chunk)
        return True

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        with self.path.open("rb") as f:
            # Initial fill
            self._refill(f)
            if self._text_buf.startswith("\ufeff"):
                self._text_buf = self._text_buf.lstrip("\ufeff")

            # Seek to '['
            while True:
                while self._pos < len(self._text_buf) and self._text_buf[self._pos].isspace():
                    self._pos += 1

                if self._pos >= len(self._text_buf):
                    if not self._refill(f):
                        raise ValueError("Unexpected EOF while looking for '['")
                    continue

                if self._text_buf[self._pos] != "[":
                    raise ValueError("Expected JSON array '[' at start of file")
                self._pos += 1
                self._started = True
                break

            # Decode elements
            while True:
                if self._done:
                    return

                # Skip whitespace + commas
                while True:
                    while self._pos < len(self._text_buf) and self._text_buf[self._pos].isspace():
                        self._pos += 1

                    if self._pos < len(self._text_buf) and self._text_buf[self._pos] == ",":
                        self._pos += 1
                        continue

                    if self._pos >= len(self._text_buf):
                        if not self._refill(f):
                            raise ValueError("Unexpected EOF while decoding array")
                        continue
                    break

                # End of array
                if self._text_buf[self._pos] == "]":
                    self._done = True
                    return

                try:
                    obj, end = self._decoder.raw_decode(self._text_buf, self._pos)
                except json.JSONDecodeError:
                    if not self._refill(f):
                        raise
                    continue

                self._pos = end
                self.progress.conversations_seen += 1
                yield obj

                # Compact buffer occasionally
                if self._pos > 5_000_000:
                    self._text_buf = self._text_buf[self._pos :]
                    self._pos = 0


def _extract_text_from_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        parts = content.get("parts")
        if isinstance(parts, list):
            try:
                return "\n".join([str(p) for p in parts if p is not None]).strip()
            except Exception:
                return ""
        text = content.get("text")
        if isinstance(text, str):
            return text.strip()
        return ""
    if isinstance(content, list):
        try:
            return "\n".join([_extract_text_from_content(x) for x in content]).strip()
        except Exception:
            return ""
    return str(content).strip()


def _company_id(conn: sqlite3.Connection, name: str) -> Optional[int]:
    name = (name or "").strip()
    if not name:
        return None
    cur = conn.cursor()
    cur.execute("SELECT id FROM companies WHERE lower(name)=lower(?) LIMIT 1", (name,))
    row = cur.fetchone()
    if row:
        return int(row[0])
    now = datetime.datetime.now().isoformat()
    cur.execute(
        "INSERT INTO companies (name, industry, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (name, "", now, now),
    )
    return int(cur.lastrowid)


def _upsert_conversation(
    conn: sqlite3.Connection,
    *,
    company_id: Optional[int],
    source: str,
    conversation_uid: str,
    title: str,
    create_time_ts: Optional[float],
    update_time_ts: Optional[float],
    message_count: int,
    metadata: Dict[str, Any],
) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO chat_conversations
            (company_id, source, conversation_uid, title, create_time_ts, update_time_ts, message_count, metadata_json, imported_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source, conversation_uid) DO UPDATE SET
            company_id=COALESCE(excluded.company_id, chat_conversations.company_id),
            title=COALESCE(excluded.title, chat_conversations.title),
            create_time_ts=COALESCE(excluded.create_time_ts, chat_conversations.create_time_ts),
            update_time_ts=COALESCE(excluded.update_time_ts, chat_conversations.update_time_ts),
            message_count=MAX(chat_conversations.message_count, excluded.message_count),
            metadata_json=COALESCE(excluded.metadata_json, chat_conversations.metadata_json)
        """,
        (
            company_id,
            source,
            conversation_uid,
            title,
            create_time_ts,
            update_time_ts,
            message_count,
            json.dumps(metadata, ensure_ascii=False) if metadata else None,
            datetime.datetime.now().isoformat(),
        ),
    )
    cur.execute(
        "SELECT id FROM chat_conversations WHERE source=? AND conversation_uid=? LIMIT 1",
        (source, conversation_uid),
    )
    row = cur.fetchone()
    return int(row[0])


def _upsert_message(
    conn: sqlite3.Connection,
    *,
    conversation_id: int,
    message_uid: str,
    parent_uid: Optional[str],
    role: Optional[str],
    author_name: Optional[str],
    create_time_ts: Optional[float],
    content_text: str,
    content_json: Optional[str],
    metadata_json: Optional[str],
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO chat_messages
            (conversation_id, message_uid, parent_uid, role, author_name, create_time_ts, content_text, content_json, metadata_json, imported_at)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(conversation_id, message_uid) DO UPDATE SET
            parent_uid=COALESCE(excluded.parent_uid, chat_messages.parent_uid),
            role=COALESCE(excluded.role, chat_messages.role),
            author_name=COALESCE(excluded.author_name, chat_messages.author_name),
            create_time_ts=COALESCE(excluded.create_time_ts, chat_messages.create_time_ts),
            content_text=COALESCE(excluded.content_text, chat_messages.content_text),
            content_json=COALESCE(excluded.content_json, chat_messages.content_json),
            metadata_json=COALESCE(excluded.metadata_json, chat_messages.metadata_json)
        """,
        (
            conversation_id,
            message_uid,
            parent_uid,
            role,
            author_name,
            create_time_ts,
            content_text if content_text else None,
            content_json,
            metadata_json,
            datetime.datetime.now().isoformat(),
        ),
    )


def _update_job(
    conn: sqlite3.Connection,
    job_id: int,
    *,
    status: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    cur = conn.cursor()
    sets = []
    params: list[Any] = []
    now = datetime.datetime.now().isoformat()

    if status is not None:
        sets.append("status=?")
        params.append(status)
        if status == "running":
            sets.append("started_at=COALESCE(started_at, ?)")
            params.append(now)
        if status in {"completed", "failed", "error"}:
            sets.append("completed_at=COALESCE(completed_at, ?)")
            params.append(now)

    sets.append("updated_at=?")
    params.append(now)

    if metadata is not None:
        sets.append("metadata_json=?")
        params.append(json.dumps(metadata, ensure_ascii=False))
    if result is not None:
        sets.append("result_json=?")
        params.append(json.dumps(result, ensure_ascii=False))
    if error is not None:
        sets.append("error=?")
        params.append(error)

    params.append(job_id)
    cur.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE id=?", params)


def import_gpt_export(
    *,
    db_path: Path,
    export_path: Path,
    source: str,
    company_name: Optional[str] = None,
    limit: Optional[int] = None,
    commit_every: int = 25,
    job_id: Optional[int] = None,
    progress_cb: Optional[Callable[[StreamProgress], None]] = None,
) -> StreamProgress:
    export_path = export_path.resolve()
    db_path = db_path.resolve()

    if not export_path.exists():
        raise FileNotFoundError(f"Export file not found: {export_path}")
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    stream = JsonArrayStream(export_path)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
    except Exception:
        pass

    try:
        company_mode = (company_name or "").strip().lower()
        auto_company = company_mode in {"auto", "detect", "autodetect"}
        cid = None
        romer_id = None
        emassc_id = None
        if company_name and not auto_company:
            cid = _company_id(conn, company_name or "")
        elif auto_company:
            # Ensure these canonical companies exist for consistent lobbies.
            romer_id = _company_id(conn, "Romer Industries")
            emassc_id = _company_id(conn, "EMASSC")

        def detect_company_id(conv_obj: Dict[str, Any]) -> Optional[int]:
            if not auto_company:
                return cid

            title = str(conv_obj.get("title") or "")
            blob = title.lower()

            # Sample only a small portion of the conversation for classification.
            mapping = conv_obj.get("mapping") if isinstance(conv_obj.get("mapping"), dict) else {}
            sample_texts = []
            count = 0
            for node in (mapping or {}).values():
                if count >= 25:
                    break
                if not isinstance(node, dict):
                    continue
                msg = node.get("message")
                if not isinstance(msg, dict):
                    continue
                content_text = _extract_text_from_content(msg.get("content"))
                if content_text:
                    sample_texts.append(content_text)
                    count += 1
            if sample_texts:
                blob += "\n" + "\n".join(sample_texts).lower()

            if "emassc" in blob or "e-massc" in blob:
                return emassc_id
            if "romer" in blob or "römer" in blob:
                return romer_id

            # Default to Romer lobby when ambiguous.
            return romer_id

        if job_id is not None:
            _update_job(
                conn,
                job_id,
                status="running",
                metadata={
                    "tool": "import_gpt_export",
                    "source": source,
                    "export_path": str(export_path),
                    "company": company_name,
                    "started_at": datetime.datetime.now().isoformat(),
                },
            )
            conn.commit()

        conv_batch = 0
        processed = 0
        for conv in stream:
            if limit is not None and processed >= limit:
                break

            conv_uid = str(conv.get("id") or conv.get("conversation_id") or "").strip()
            if not conv_uid:
                conv_uid = f"conv_{stream.progress.conversations_seen}_{int(time.time())}"

            mapping = conv.get("mapping") if isinstance(conv.get("mapping"), dict) else {}

            # Store non-mapping metadata (keeps DB leaner but preserves key fields)
            meta = {}
            for k, v in conv.items():
                if k == "mapping":
                    continue
                if k in {"title", "create_time", "update_time", "id", "conversation_id"}:
                    continue
                meta[k] = v

            conv_company_id = detect_company_id(conv)
            if auto_company:
                meta["company_detection"] = {
                    "mode": "auto",
                    "assigned_company_id": conv_company_id,
                    "rules": ["emassc keyword", "romer keyword", "default romer"],
                }

            conv_id = _upsert_conversation(
                conn,
                company_id=conv_company_id,
                source=source,
                conversation_uid=conv_uid,
                title=str(conv.get("title") or "").strip() or None,
                create_time_ts=conv.get("create_time"),
                update_time_ts=conv.get("update_time"),
                message_count=len(mapping),
                metadata=meta,
            )
            stream.progress.conversations_upserted += 1
            processed += 1

            # Insert messages from mapping nodes
            for node_id, node in (mapping or {}).items():
                if not isinstance(node, dict):
                    continue
                msg = node.get("message")
                if not isinstance(msg, dict):
                    continue

                msg_uid = str(msg.get("id") or node_id).strip()
                if not msg_uid:
                    continue

                author = msg.get("author") if isinstance(msg.get("author"), dict) else {}
                role = author.get("role") if isinstance(author, dict) else None
                author_name = author.get("name") if isinstance(author, dict) else None

                content = msg.get("content")
                content_text = _extract_text_from_content(content)
                try:
                    content_json = json.dumps(content, ensure_ascii=False) if content is not None else None
                except Exception:
                    content_json = None

                # Metadata without duplicating full content
                msg_meta = {k: v for k, v in msg.items() if k not in {"content"}}
                try:
                    msg_meta_json = json.dumps(msg_meta, ensure_ascii=False) if msg_meta else None
                except Exception:
                    msg_meta_json = None

                _upsert_message(
                    conn,
                    conversation_id=conv_id,
                    message_uid=msg_uid,
                    parent_uid=node.get("parent"),
                    role=role,
                    author_name=author_name,
                    create_time_ts=msg.get("create_time"),
                    content_text=content_text,
                    content_json=content_json,
                    metadata_json=msg_meta_json,
                )
                stream.progress.messages_seen += 1
                stream.progress.messages_upserted += 1

            conv_batch += 1
            if conv_batch >= max(1, int(commit_every)):
                conn.commit()
                conv_batch = 0

                if job_id is not None:
                    _update_job(
                        conn,
                        job_id,
                        status="running",
                        metadata={
                            "tool": "import_gpt_export",
                            "source": source,
                            "export_path": str(export_path),
                            "company": company_name,
                            "bytes_read": stream.progress.bytes_read,
                            "file_size": stream.progress.file_size,
                            "pct": round(stream.progress.pct, 2),
                            "conversations_seen": stream.progress.conversations_seen,
                            "messages_seen": stream.progress.messages_seen,
                            "updated_at": datetime.datetime.now().isoformat(),
                        },
                    )
                    conn.commit()

                if progress_cb is not None:
                    try:
                        progress_cb(stream.progress)
                    except Exception:
                        pass

        conn.commit()

        if job_id is not None:
            _update_job(
                conn,
                job_id,
                status="completed",
                result={
                    "source": source,
                    "export_path": str(export_path),
                    "company": company_name,
                    "bytes_read": stream.progress.bytes_read,
                    "file_size": stream.progress.file_size,
                    "pct": round(stream.progress.pct, 2),
                    "conversations_seen": stream.progress.conversations_seen,
                    "messages_seen": stream.progress.messages_seen,
                    "conversations_upserted": stream.progress.conversations_upserted,
                    "messages_upserted": stream.progress.messages_upserted,
                    "duration_s": round(time.time() - stream.progress.started_at, 2),
                },
            )
            conn.commit()

        if progress_cb is not None:
            try:
                progress_cb(stream.progress)
            except Exception:
                pass

        return stream.progress
    except Exception as e:
        try:
            if job_id is not None:
                _update_job(conn, job_id, status="error", error=str(e))
                conn.commit()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def main(argv: Optional[Iterable[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    here = Path(__file__).resolve()
    ls_root = _find_lightspeed_root(here)

    ap = argparse.ArgumentParser(description="Import GPT export conversations.json into LightSpeed DB")
    ap.add_argument("--db", type=str, default=str(_default_db_path(ls_root)), help="Path to lightspeed_unified.db")
    ap.add_argument("--input", type=str, default=str(_default_export_path(ls_root)), help="Path to conversations.json")
    ap.add_argument("--source", type=str, default="GPT_Export_2025-11-16", help="Source label stored in DB")
    ap.add_argument(
        "--company",
        type=str,
        default="auto",
        help="Company name for imported conversations (use 'auto' to classify Romer vs EMASSC per conversation)",
    )
    ap.add_argument("--limit", type=int, default=0, help="Limit conversations (0 = no limit)")
    ap.add_argument("--commit-every", type=int, default=25, help="Commit every N conversations")
    ap.add_argument("--job-id", type=int, default=0, help="Optional jobs.id to update (0 disables)")
    args = ap.parse_args(argv)

    def _print_prog(p: StreamProgress):
        dur = max(0.001, time.time() - p.started_at)
        rate = p.conversations_seen / dur
        sys.stdout.write(
            f"\r[{p.pct:6.2f}%] conv={p.conversations_seen} msgs={p.messages_seen} rate={rate:.2f} conv/s"
        )
        sys.stdout.flush()

    progress = import_gpt_export(
        db_path=Path(args.db),
        export_path=Path(args.input),
        source=args.source,
        company_name=args.company.strip() if args.company else None,
        limit=args.limit or None,
        commit_every=max(1, int(args.commit_every)),
        job_id=(args.job_id or None),
        progress_cb=_print_prog,
    )
    sys.stdout.write(
        f"\nDone. Conversations={progress.conversations_seen} Messages={progress.messages_seen} Duration={time.time()-progress.started_at:.2f}s\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
