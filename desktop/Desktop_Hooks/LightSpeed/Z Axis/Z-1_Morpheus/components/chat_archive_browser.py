#!/usr/bin/env python3
"""
Chat Archive Browser (Morpheus)

Interactive viewer for imported chat archives (GPT Export and future sources).
Reads from Merovingian DB tables:
- chat_conversations
- chat_messages
"""

from __future__ import annotations

import json
import sqlite3
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        try:
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        except Exception:
            continue
        try:
            if (candidate / "LightSpeed" / "N.py").exists() and (candidate / "LightSpeed" / "Z Axis").exists():
                return (candidate / "LightSpeed").resolve()
        except Exception:
            continue
    return start


def _db_path(ls_root: Path) -> Path:
    cfg = ls_root / "config" / "unified_config.json"
    try:
        d = json.loads(cfg.read_text(encoding="utf-8"))
        rel = (d.get("database") or {}).get("path")
        if rel:
            return (ls_root / rel).resolve()
    except Exception:
        pass
    return (ls_root / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db").resolve()


class ChatArchiveBrowser(tk.Frame):
    def __init__(self, parent, *, lightspeed_root: Optional[Path] = None, db_path: Optional[Path] = None):
        super().__init__(parent)
        self.lightspeed_root = lightspeed_root or _find_lightspeed_root(Path(__file__))
        self.db_path = (db_path or _db_path(self.lightspeed_root)).resolve()

        self._companies: List[Tuple[Optional[int], str]] = [(None, "All Companies")]
        self._conversation_rows: List[Dict[str, Any]] = []

        self._build_ui()
        self._load_companies()
        self._refresh_conversations()

    # ---- UI ----

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        top.columnconfigure(3, weight=1)

        ttk.Label(top, text="Company").grid(row=0, column=0, sticky="w")
        self.company_var = tk.StringVar(value="All Companies")
        self.company_combo = ttk.Combobox(top, textvariable=self.company_var, state="readonly", width=22)
        self.company_combo.grid(row=0, column=1, sticky="w", padx=(6, 12))
        self.company_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_conversations())

        ttk.Label(top, text="Search").grid(row=0, column=2, sticky="w")
        self.search_var = tk.StringVar(value="")
        self.search_entry = ttk.Entry(top, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=3, sticky="ew", padx=(6, 6))
        self.search_entry.bind("<Return>", lambda _e: self._refresh_conversations())

        ttk.Button(top, text="Refresh", command=self._refresh_conversations).grid(row=0, column=4, sticky="e", padx=(6, 0))

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        left = ttk.Frame(body)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        hdr = ttk.Frame(left)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        hdr.columnconfigure(0, weight=1)
        ttk.Label(hdr, text="Conversations").grid(row=0, column=0, sticky="w")
        self.count_label = ttk.Label(hdr, text="")
        self.count_label.grid(row=0, column=1, sticky="e")

        self.conv_list = tk.Listbox(left, activestyle="dotbox")
        self.conv_list.grid(row=1, column=0, sticky="nsew")
        self.conv_list.bind("<<ListboxSelect>>", lambda _e: self._on_select_conversation())

        left_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.conv_list.yview)
        self.conv_list.configure(yscrollcommand=left_scroll.set)
        left_scroll.grid(row=1, column=1, sticky="ns")

        right = ttk.Frame(body)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self.meta_label = ttk.Label(right, text="Select a conversation", anchor="w")
        self.meta_label.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        self.msg_text = tk.Text(right, wrap="word")
        self.msg_text.grid(row=1, column=0, sticky="nsew")
        self.msg_text.configure(state="disabled")
        msg_scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.msg_text.yview)
        self.msg_text.configure(yscrollcommand=msg_scroll.set)
        msg_scroll.grid(row=1, column=1, sticky="ns")

        body.add(left, weight=1)
        body.add(right, weight=3)

        self.status = ttk.Label(self, text=str(self.db_path), anchor="w")
        self.status.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 6))

    # ---- DB helpers ----

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        return conn

    def _load_companies(self) -> None:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM companies ORDER BY name")
                rows = cur.fetchall() or []
                self._companies = [(None, "All Companies")] + [(int(r[0]), str(r[1])) for r in rows if r and r[0] is not None]
        except Exception:
            self._companies = [(None, "All Companies")]

        self.company_combo["values"] = [name for _id, name in self._companies]
        if self.company_var.get() not in self.company_combo["values"]:
            self.company_var.set("All Companies")

    def _selected_company_id(self) -> Optional[int]:
        selected = self.company_var.get()
        for cid, name in self._companies:
            if name == selected:
                return cid
        return None

    def _refresh_conversations(self) -> None:
        self.conv_list.delete(0, tk.END)
        self._conversation_rows = []

        cid = self._selected_company_id()
        q = (self.search_var.get() or "").strip()

        where = []
        params: List[Any] = []
        if cid is not None:
            where.append("company_id=?")
            params.append(cid)
        if q:
            where.append(
                "(title LIKE ? OR conversation_uid LIKE ? OR EXISTS (SELECT 1 FROM chat_messages m WHERE m.conversation_id=chat_conversations.id AND m.content_text LIKE ?))"
            )
            pat = f"%{q}%"
            params.extend([pat, pat, pat])

        sql = "SELECT id, title, source, update_time_ts, message_count, conversation_uid FROM chat_conversations"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY COALESCE(update_time_ts, 0) DESC, id DESC LIMIT 500"

        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(sql, params)
                rows = cur.fetchall() or []
        except Exception as e:
            self.count_label.config(text="DB error")
            self._set_messages(f"Database error: {e}")
            return

        for r in rows:
            conv_id = int(r[0])
            title = str(r[1] or "").strip() or "(untitled)"
            source = str(r[2] or "").strip()
            msg_count = int(r[4] or 0)
            uid = str(r[5] or "")
            label = f"{title}  —  {msg_count} msgs"
            if source:
                label += f"  [{source}]"
            self.conv_list.insert(tk.END, label)
            self._conversation_rows.append(
                {"id": conv_id, "title": title, "source": source, "message_count": msg_count, "uid": uid}
            )

        self.count_label.config(text=f"{len(self._conversation_rows)}")
        self._set_messages("")
        self.meta_label.config(text="Select a conversation")

    def _on_select_conversation(self) -> None:
        sel = self.conv_list.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self._conversation_rows):
            return
        row = self._conversation_rows[idx]
        conv_id = row["id"]

        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT role, author_name, create_time_ts, content_text
                    FROM chat_messages
                    WHERE conversation_id=?
                    ORDER BY COALESCE(create_time_ts, 0) ASC, id ASC
                    """,
                    (conv_id,),
                )
                msgs = cur.fetchall() or []
        except Exception as e:
            self._set_messages(f"Database error loading messages: {e}")
            return

        self.meta_label.config(text=f"{row.get('title')}  •  {row.get('message_count')} messages")

        parts: List[str] = []
        for role, author_name, create_time_ts, content_text in msgs:
            r = str(role or author_name or "unknown")
            txt = str(content_text or "").strip()
            if not txt:
                continue
            parts.append(f"[{r}]\n{txt}\n")

        self._set_messages("\n".join(parts).strip())

    def _set_messages(self, text: str) -> None:
        self.msg_text.configure(state="normal")
        self.msg_text.delete("1.0", tk.END)
        if text:
            self.msg_text.insert(tk.END, text)
        self.msg_text.configure(state="disabled")
