"""
Open Dialogue Board (Codex <-> Claude <-> User)

This is a lightweight, local-only message board that writes to:
  LightSpeed/ai_logs/open_dialogue/live_conversation.jsonl

Design:
  - Append-only JSONL event log (type=msg, type=review, type=meta)
  - Refresh loop (default: 60s)
  - Checkpoint autosave (default: 300s) to keep the UI state consistent
  - Minimal UI: inbox, message detail, compose, and quick review (Y/N/Reply)

This is intentionally simple and file-based so it works offline and does not
require any external services.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, messagebox


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return start.parent


LIGHTSPEED_ROOT = _find_lightspeed_root(Path(__file__))
OPEN_DIALOGUE_DIR = (LIGHTSPEED_ROOT / "ai_logs" / "open_dialogue").resolve()
LIVE_LOG = OPEN_DIALOGUE_DIR / "live_conversation.jsonl"


def _ensure_files() -> None:
    OPEN_DIALOGUE_DIR.mkdir(parents=True, exist_ok=True)
    if not LIVE_LOG.exists():
        LIVE_LOG.write_text(
            json.dumps(
                {
                    "type": "meta",
                    "schema_version": "1.0",
                    "created_at": _now_iso(),
                    "channels": ["codex", "claude", "user"],
                    "notes": "Append-only JSONL. Events include type=msg and type=review.",
                }
            )
            + "\n",
            encoding="utf-8",
        )


def _append_event(evt: Dict[str, Any]) -> None:
    _ensure_files()
    with LIVE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")


def _read_events(max_bytes: int = 5_000_000) -> List[Dict[str, Any]]:
    _ensure_files()
    try:
        if LIVE_LOG.stat().st_size > max_bytes:
            # Soft safety: only read the tail if the file grows very large.
            with LIVE_LOG.open("rb") as bf:
                bf.seek(-max_bytes, os.SEEK_END)
                data = bf.read().decode("utf-8", errors="replace")
        else:
            data = LIVE_LOG.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    for line in data.splitlines():
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


@dataclass(frozen=True)
class MessageState:
    msg_id: str
    ts: str
    sender: str
    recipient: str
    text: str
    reviewed_by: Tuple[str, ...]
    decisions: Dict[str, str]
    replies: Dict[str, str]


def _build_state(events: Iterable[Dict[str, Any]]) -> List[MessageState]:
    msgs: Dict[str, Dict[str, Any]] = {}
    reviews: Dict[str, List[Dict[str, Any]]] = {}

    for e in events:
        et = e.get("type")
        if et == "msg":
            mid = str(e.get("id") or "")
            if not mid:
                continue
            msgs[mid] = e
        elif et == "review":
            mid = str(e.get("msg_id") or "")
            if not mid:
                continue
            reviews.setdefault(mid, []).append(e)

    states: List[MessageState] = []
    for mid, m in msgs.items():
        rv = reviews.get(mid, [])
        reviewed_by = []
        decisions: Dict[str, str] = {}
        replies: Dict[str, str] = {}
        for r in rv:
            by = str(r.get("by") or "").strip().lower()
            if not by:
                continue
            if by not in reviewed_by:
                reviewed_by.append(by)
            dec = r.get("decision")
            if isinstance(dec, str) and dec:
                decisions[by] = dec
            rep = r.get("reply")
            if isinstance(rep, str) and rep:
                replies[by] = rep

        states.append(
            MessageState(
                msg_id=mid,
                ts=str(m.get("ts") or ""),
                sender=str(m.get("from") or ""),
                recipient=str(m.get("to") or ""),
                text=str(m.get("text") or ""),
                reviewed_by=tuple(reviewed_by),
                decisions=decisions,
                replies=replies,
            )
        )

    # Newest first
    def sort_key(s: MessageState):
        return s.ts

    states.sort(key=sort_key, reverse=True)
    return states


class OpenDialogueBoard(tk.Toplevel):
    def __init__(
        self,
        parent: Optional[tk.Misc] = None,
        *,
        refresh_seconds: int = 60,
        checkpoint_seconds: int = 300,
    ):
        super().__init__(parent)
        self.title("Open Dialogue Board (Codex / Claude / User)")
        self.geometry("980x720")
        self.minsize(860, 640)

        self.refresh_seconds = int(refresh_seconds)
        self.checkpoint_seconds = int(checkpoint_seconds)

        self.persona = tk.StringVar(value="user")
        self.filter_to_me = tk.BooleanVar(value=True)
        self._states: List[MessageState] = []
        self._selected: Optional[MessageState] = None
        self._last_refresh = 0.0

        self._build_ui()
        self._refresh()
        self._schedule_refresh()
        self._schedule_checkpoint()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Persona").pack(side=tk.LEFT)
        persona = ttk.Combobox(
            top,
            textvariable=self.persona,
            values=["user", "codex", "claude"],
            state="readonly",
            width=10,
        )
        persona.pack(side=tk.LEFT, padx=(6, 14))
        persona.bind("<<ComboboxSelected>>", lambda _e: self._refresh())

        ttk.Checkbutton(top, text="Only messages to me", variable=self.filter_to_me, command=self._refresh).pack(
            side=tk.LEFT
        )

        ttk.Button(top, text="Refresh", command=self._refresh).pack(side=tk.RIGHT)
        ttk.Button(top, text="Open Folder", command=self._open_folder).pack(side=tk.RIGHT, padx=(0, 8))

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=2)
        body.add(right, weight=3)

        self.tree = ttk.Treeview(left, columns=("when", "from", "to", "status"), show="headings", selectmode="browse")
        self.tree.heading("when", text="When")
        self.tree.heading("from", text="From")
        self.tree.heading("to", text="To")
        self.tree.heading("status", text="Status")
        self.tree.column("when", width=160, anchor="w")
        self.tree.column("from", width=90, anchor="w")
        self.tree.column("to", width=90, anchor="w")
        self.tree.column("status", width=100, anchor="w")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._on_select())

        sb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        detail = ttk.LabelFrame(right, text="Message", padding=10)
        detail.pack(fill=tk.BOTH, expand=True)
        self.detail = tk.Text(detail, wrap="word", height=18)
        self.detail.pack(fill=tk.BOTH, expand=True)
        self.detail.configure(state="disabled")

        actions = ttk.Frame(right)
        actions.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(actions, text="Y (Approve)", command=lambda: self._review("Y")).pack(side=tk.LEFT)
        ttk.Button(actions, text="N (Reject)", command=lambda: self._review("N")).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(actions, text="Reply…", command=self._reply).pack(side=tk.LEFT, padx=(6, 0))

        compose = ttk.LabelFrame(right, text="Compose", padding=10)
        compose.pack(fill=tk.BOTH, expand=False, pady=(10, 0))

        row1 = ttk.Frame(compose)
        row1.pack(fill=tk.X)
        ttk.Label(row1, text="To").pack(side=tk.LEFT)
        self.to_var = tk.StringVar(value="codex")
        to_box = ttk.Combobox(row1, textvariable=self.to_var, values=["codex", "claude", "user"], state="readonly")
        to_box.pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(row1, text="Refresh (s)").pack(side=tk.LEFT)
        self.refresh_var = tk.IntVar(value=self.refresh_seconds)
        ttk.Spinbox(row1, from_=10, to=600, increment=10, textvariable=self.refresh_var, width=6).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(row1, text="Apply", command=self._apply_intervals).pack(side=tk.LEFT, padx=(6, 0))

        self.compose = tk.Text(compose, wrap="word", height=6)
        self.compose.pack(fill=tk.BOTH, expand=True, pady=(8, 8))

        ttk.Button(compose, text="Send", command=self._send).pack(anchor="e")

        footer = ttk.Frame(self, padding=(10, 0, 10, 10))
        footer.pack(fill=tk.X)
        self.status = ttk.Label(footer, text="")
        self.status.pack(side=tk.LEFT)
        self._set_status(f"Log: {LIVE_LOG}")

    def _set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def _open_folder(self) -> None:
        try:
            os.startfile(str(OPEN_DIALOGUE_DIR))  # type: ignore[attr-defined]
        except Exception as e:
            messagebox.showerror("Open Folder", f"Failed:\n{e}", parent=self)

    def _apply_intervals(self) -> None:
        try:
            self.refresh_seconds = int(self.refresh_var.get() or 60)
        except Exception:
            self.refresh_seconds = 60
        self._set_status(f"Refresh every {self.refresh_seconds}s | Log: {LIVE_LOG}")

    def _refresh(self) -> None:
        events = _read_events()
        self._states = _build_state(events)

        me = (self.persona.get() or "user").strip().lower()
        filtered = self._states
        if self.filter_to_me.get():
            filtered = [s for s in filtered if (s.recipient or "").strip().lower() == me]

        # Preserve selection
        sel_id = self._selected.msg_id if self._selected else None

        for iid in self.tree.get_children():
            self.tree.delete(iid)

        for s in filtered:
            reviewed = me in s.reviewed_by
            status = "NEW" if not reviewed else (s.decisions.get(me) or "SEEN")
            self.tree.insert("", "end", iid=s.msg_id, values=(s.ts, s.sender, s.recipient, status))

        if sel_id and self.tree.exists(sel_id):
            self.tree.selection_set(sel_id)
            self.tree.see(sel_id)
        else:
            self._selected = None
            self._set_detail("")

        self._last_refresh = time.time()

    def _schedule_refresh(self) -> None:
        self.after(self.refresh_seconds * 1000, self._tick_refresh)

    def _tick_refresh(self) -> None:
        try:
            self._refresh()
        finally:
            self._schedule_refresh()

    def _schedule_checkpoint(self) -> None:
        self.after(self.checkpoint_seconds * 1000, self._checkpoint)

    def _checkpoint(self) -> None:
        # Autosave/checkpoint: emit a small heartbeat so other boards can show activity.
        try:
            _append_event(
                {
                    "type": "review",
                    "ts": _now_iso(),
                    "msg_id": "__checkpoint__",
                    "by": (self.persona.get() or "user").strip().lower(),
                    "decision": "CHECKPOINT",
                    "reply": "",
                }
            )
        except Exception:
            pass
        finally:
            self._schedule_checkpoint()

    def _on_select(self) -> None:
        sel = self.tree.selection()
        if not sel:
            self._selected = None
            self._set_detail("")
            return
        mid = sel[0]
        match = None
        for s in self._states:
            if s.msg_id == mid:
                match = s
                break
        self._selected = match
        if match is None:
            self._set_detail("")
            return

        payload = {
            "id": match.msg_id,
            "ts": match.ts,
            "from": match.sender,
            "to": match.recipient,
            "text": match.text,
            "reviewed_by": list(match.reviewed_by),
            "decisions": match.decisions,
            "replies": match.replies,
        }
        self._set_detail(json.dumps(payload, indent=2, ensure_ascii=False))

    def _set_detail(self, text: str) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", tk.END)
        self.detail.insert(tk.END, text or "")
        self.detail.configure(state="disabled")

    def _send(self) -> None:
        sender = (self.persona.get() or "user").strip().lower()
        to = (self.to_var.get() or "codex").strip().lower()
        text = self.compose.get("1.0", tk.END).strip()
        if not text:
            return
        if to not in {"codex", "claude", "user"}:
            return
        mid = str(uuid.uuid4())
        _append_event({"type": "msg", "id": mid, "ts": _now_iso(), "from": sender, "to": to, "text": text})
        self.compose.delete("1.0", tk.END)
        self._refresh()

    def _review(self, decision: str) -> None:
        if self._selected is None:
            return
        me = (self.persona.get() or "user").strip().lower()
        _append_event({"type": "review", "ts": _now_iso(), "msg_id": self._selected.msg_id, "by": me, "decision": decision})
        self._refresh()

    def _reply(self) -> None:
        if self._selected is None:
            return
        me = (self.persona.get() or "user").strip().lower()
        to = self._selected.sender.strip().lower() or "user"
        if to not in {"codex", "claude", "user"}:
            to = "user"
        prompt = tk.Toplevel(self)
        prompt.title("Reply")
        prompt.geometry("520x240")
        prompt.minsize(480, 200)
        ttk.Label(prompt, text=f"Reply to {to}").pack(anchor="w", padx=10, pady=(10, 4))
        txt = tk.Text(prompt, wrap="word", height=6)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        def send_reply():
            rep = txt.get("1.0", tk.END).strip()
            if not rep:
                return
            _append_event(
                {
                    "type": "review",
                    "ts": _now_iso(),
                    "msg_id": self._selected.msg_id,
                    "by": me,
                    "decision": "REPLY",
                    "reply": rep,
                }
            )
            _append_event(
                {
                    "type": "msg",
                    "id": str(uuid.uuid4()),
                    "ts": _now_iso(),
                    "from": me,
                    "to": to,
                    "text": rep,
                    "in_reply_to": self._selected.msg_id,
                }
            )
            try:
                prompt.destroy()
            except Exception:
                pass
            self._refresh()

        ttk.Button(prompt, text="Send", command=send_reply).pack(anchor="e", padx=10, pady=(0, 10))


def launch_dialogue_board(parent: Optional[tk.Misc] = None) -> OpenDialogueBoard:
    _ensure_files()
    return OpenDialogueBoard(parent)


def main() -> int:
    _ensure_files()
    root = tk.Tk()
    root.withdraw()
    OpenDialogueBoard(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
