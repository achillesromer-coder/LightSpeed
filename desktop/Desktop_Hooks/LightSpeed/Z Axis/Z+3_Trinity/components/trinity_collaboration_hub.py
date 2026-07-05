"""
Trinity Collaboration Hub - Three-Way AI Collaboration System
Trinity Floor (Z+3) - Real-Time Claude/Codex/User Collaboration

Revolutionary three-way collaboration interface implementing M1-2/2-3 methodology
with weighted voting (Claude 24.5%, Codex 24.5%, User 51%) for trustable,
interference-free platform growth.

Features:
- Real-time three-way chat interface
- M1-2/2-3 sign-off system
- Weighted voting and decision making
- File upload and code drop zones
- Z-Axis commit planning
- Glassmorphism aesthetic
- Change tracking and audit trail
- API/library integration review

Floor: Trinity
Z-Level: 3
Author: LightSpeed Team
Version: 0.9.7
Date: 2026-01-12
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import threading
import queue
import hashlib
import sys
import os
import time
import uuid

# Import Premium Theme Engine
try:
    TRINITY_UI_PATH = Path(__file__).parent.parent / "ui"
    import sys
    sys.path.insert(0, str(TRINITY_DIR := Path(__file__).parents[1]))
    from ui.premium_theme_engine import get_theme_engine, ThemeMode
    HAS_PREMIUM_THEME = True
except ImportError as e:
    print(f"[INFO] Premium theme engine not available: {e}")
    HAS_PREMIUM_THEME = False


class ParticipantRole(Enum):
    """Collaboration participant roles"""
    USER = "user"           # 51% voting weight
    CLAUDE = "claude"       # 24.5% voting weight
    CODEX = "codex"         # 24.5% voting weight


class ProposalStatus(Enum):
    """Proposal lifecycle status"""
    DRAFT = "draft"
    PENDING_M1 = "pending_m1"      # Awaiting M1 (initial review)
    PENDING_M2 = "pending_m2"      # Awaiting M2 (cross-check)
    PENDING_M3 = "pending_m3"      # Awaiting M3 (final sign-off)
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class VoteType(Enum):
    """Vote types in M1-2/2-3 system"""
    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"
    REQUEST_CHANGES = "request_changes"


@dataclass
class Vote:
    """Individual vote in M1-2/2-3 process"""
    participant: ParticipantRole
    vote_type: VoteType
    weight: float  # 0.51 for user, 0.245 for Claude/Codex
    comment: str
    timestamp: str
    milestone: str  # M1, M2, or M3


@dataclass
class Proposal:
    """Change proposal with M1-2/2-3 tracking"""
    id: str
    title: str
    description: str
    proposer: ParticipantRole
    status: ProposalStatus
    created_at: str
    z_axis_floors: List[str]
    affected_files: List[str]
    code_changes: Dict[str, str]
    votes: List[Vote] = field(default_factory=list)
    implementation_notes: str = ""

    @property
    def approval_score(self) -> float:
        """Calculate weighted approval score"""
        approve_weight = sum(
            v.weight for v in self.votes
            if v.vote_type == VoteType.APPROVE
        )
        return approve_weight

    @property
    def can_proceed_m1_to_m2(self) -> bool:
        """Check if can proceed from M1 to M2"""
        # Need at least 2 approvals (any combination)
        approvals = len([v for v in self.votes if v.vote_type == VoteType.APPROVE])
        return approvals >= 2

    @property
    def can_proceed_m2_to_m3(self) -> bool:
        """Check if can proceed from M2 to M3"""
        # Need all three to weigh in with majority approval
        participants_voted = {v.participant for v in self.votes}
        if len(participants_voted) < 3:
            return False
        return self.approval_score > 0.5

    @property
    def is_approved(self) -> bool:
        """Check if fully approved (passed M3)"""
        return self.approval_score >= 0.51  # User must approve


@dataclass
class ChatMessage:
    """Chat message in collaboration hub"""
    sender: ParticipantRole
    content: str
    timestamp: str
    message_type: str = "text"  # text, code, file, proposal
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OpenDialogueMessageState:
    msg_id: str
    ts: str
    sender: str
    recipient: str
    text: str
    reviewed_by: tuple[str, ...]
    decisions: Dict[str, str]
    replies: Dict[str, str]


class CollaborationTheme:
    """LightSpeed glassmorphism theme for Trinity"""
    # Colors from Trinity floor (solid colors for tkinter compatibility)
    BG_PRIMARY = '#0A0A0F'           # Deep space black
    BG_SECONDARY = '#151520'         # Dark purple-black
    BG_GLASS = '#1E1E2E'             # Solid glass (no transparency)

    # Accent colors
    CLAUDE_COLOR = '#00DDFF'         # Cyan (Claude)
    CODEX_COLOR = '#00FF88'          # Green (Codex)
    USER_COLOR = '#FF00FF'           # Magenta (User)

    # Status colors
    STATUS_PENDING = '#FFAA00'       # Orange
    STATUS_APPROVED = '#00FF88'      # Green
    STATUS_REJECTED = '#FF4444'      # Red

    # UI colors
    TEXT_PRIMARY = '#FFFFFF'
    TEXT_SECONDARY = '#AAAAAA'
    BORDER_COLOR = '#00DDFF'         # Solid border (no transparency)
    ACCENT = '#00DDFF'

    # Fonts
    FONT_FAMILY = 'Segoe UI'
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_HEADER = 12
    FONT_SIZE_TITLE = 14


class TrinityCollaborationHub:
    """
    Three-Way Collaboration Hub for Claude, Codex, and User

    Implements M1-2/2-3 methodology with weighted voting:
    - User: 51% weight (final authority)
    - Claude: 24.5% weight
    - Codex: 24.5% weight

    Features:
    - Real-time three-way chat
    - File upload and code drop
    - M1-2/2-3 sign-off workflow
    - Z-Axis commit planning
    - Change tracking and audit
    """

    def __init__(self, lightspeed_root: Path, parent: Optional[tk.Misc] = None):
        """Initialize collaboration hub"""
        self.lightspeed_root = Path(lightspeed_root)
        self._parent = parent
        self.standalone = parent is None
        self.trinity_dir = self.lightspeed_root / "Z Axis" / "Z+3_Trinity"
        self.collab_dir = self.trinity_dir / "data" / "collaboration"
        self.collab_dir.mkdir(parents=True, exist_ok=True)

        # Open Dialogue (shared source-of-truth with OpenDialogueBoard)
        self.open_dialogue_dir = self.lightspeed_root / "ai_logs" / "open_dialogue"
        self.open_dialogue_log = self.open_dialogue_dir / "live_conversation.jsonl"
        self._open_dialogue_seen_ids: set[str] = set()
        self._ensure_open_dialogue_log()

        # Theme (premium or fallback)
        if HAS_PREMIUM_THEME:
            self.premium_theme = get_theme_engine(ThemeMode.DARK)
            self.use_premium_theme = True
        else:
            self.premium_theme = None
            self.use_premium_theme = False

        # Fallback classic theme
        self.classic_theme = CollaborationTheme()

        # State
        self.messages: List[ChatMessage] = []
        self.proposals: Dict[str, Proposal] = {}
        self.active_proposal: Optional[Proposal] = None
        self.message_queue = queue.Queue()

        # Voting weights
        self.voting_weights = {
            ParticipantRole.USER: 0.51,
            ParticipantRole.CLAUDE: 0.245,
            ParticipantRole.CODEX: 0.245
        }

        # Load existing data
        self._load_collaboration_data()
        self._bootstrap_open_dialogue_from_local_history()
        self._sync_from_open_dialogue(display=False)

        # Build UI
        self._build_ui()

        # Start message processor
        self._start_message_processor()

    def _participant_from_str(self, s: str) -> ParticipantRole:
        s = (s or "").strip().lower()
        if s == "claude":
            return ParticipantRole.CLAUDE
        if s == "codex":
            return ParticipantRole.CODEX
        return ParticipantRole.USER

    def _serialize_vote(self, v: Vote) -> Dict[str, Any]:
        return {
            "participant": v.participant.value,
            "vote_type": v.vote_type.value,
            "weight": float(v.weight),
            "comment": v.comment,
            "timestamp": v.timestamp,
            "milestone": v.milestone,
        }

    def _serialize_proposal(self, p: Proposal) -> Dict[str, Any]:
        return {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "proposer": p.proposer.value,
            "status": p.status.value,
            "created_at": p.created_at,
            "z_axis_floors": list(p.z_axis_floors),
            "affected_files": list(p.affected_files),
            "code_changes": dict(p.code_changes),
            "votes": [self._serialize_vote(v) for v in p.votes],
            "implementation_notes": p.implementation_notes,
        }

    def _serialize_message(self, m: ChatMessage) -> Dict[str, Any]:
        return {
            "sender": m.sender.value,
            "content": m.content,
            "timestamp": m.timestamp,
            "message_type": m.message_type,
            "metadata": dict(m.metadata or {}),
        }

    def _load_collaboration_data(self):
        """Load existing collaboration data (legacy local history)."""
        # Proposals
        proposals_file = self.collab_dir / "proposals.json"
        if proposals_file.exists():
            try:
                data = json.loads(proposals_file.read_text(encoding="utf-8"))
            except Exception:
                data = []
            if isinstance(data, list):
                for prop_data in data:
                    if not isinstance(prop_data, dict):
                        continue
                    try:
                        votes: List[Vote] = []
                        for vd in prop_data.get("votes") or []:
                            if not isinstance(vd, dict):
                                continue
                            votes.append(
                                Vote(
                                    participant=self._participant_from_str(str(vd.get("participant") or "user")),
                                    vote_type=VoteType(str(vd.get("vote_type") or "approve")),
                                    weight=float(vd.get("weight") or 0.0),
                                    comment=str(vd.get("comment") or ""),
                                    timestamp=str(vd.get("timestamp") or datetime.now().isoformat()),
                                    milestone=str(vd.get("milestone") or ""),
                                )
                            )
                        prop = Proposal(
                            id=str(prop_data.get("id") or ""),
                            title=str(prop_data.get("title") or ""),
                            description=str(prop_data.get("description") or ""),
                            proposer=self._participant_from_str(str(prop_data.get("proposer") or "user")),
                            status=ProposalStatus(str(prop_data.get("status") or "draft")),
                            created_at=str(prop_data.get("created_at") or datetime.now().isoformat()),
                            z_axis_floors=list(prop_data.get("z_axis_floors") or []),
                            affected_files=list(prop_data.get("affected_files") or []),
                            code_changes=dict(prop_data.get("code_changes") or {}),
                            votes=votes,
                            implementation_notes=str(prop_data.get("implementation_notes") or ""),
                        )
                        if prop.id:
                            self.proposals[prop.id] = prop
                    except Exception:
                        continue

        # Messages (local mirror)
        messages_file = self.collab_dir / "chat_history.json"
        if messages_file.exists():
            try:
                data = json.loads(messages_file.read_text(encoding="utf-8"))
            except Exception:
                data = []
            if isinstance(data, list):
                for msg_data in data:
                    if not isinstance(msg_data, dict):
                        continue
                    try:
                        msg = ChatMessage(
                            sender=self._participant_from_str(str(msg_data.get("sender") or "user")),
                            content=str(msg_data.get("content") or ""),
                            timestamp=str(msg_data.get("timestamp") or datetime.now().isoformat()),
                            message_type=str(msg_data.get("message_type") or "text"),
                            metadata=dict(msg_data.get("metadata") or {}),
                        )
                        if msg.content.strip():
                            self.messages.append(msg)
                    except Exception:
                        continue

    def _save_collaboration_data(self):
        """Save collaboration data (proposals + legacy local chat mirror)."""
        try:
            proposals_file = self.collab_dir / "proposals.json"
            proposals_file.write_text(
                json.dumps([self._serialize_proposal(p) for p in self.proposals.values()], indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

        try:
            messages_file = self.collab_dir / "chat_history.json"
            messages_file.write_text(
                json.dumps([self._serialize_message(m) for m in self.messages[-1000:]], indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    # ---------------------------------------------------------------------
    # Open Dialogue integration (shared JSONL)
    # ---------------------------------------------------------------------

    def _ensure_open_dialogue_log(self) -> None:
        try:
            self.open_dialogue_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            return

        if self.open_dialogue_log.exists():
            return

        try:
            meta = {
                "type": "meta",
                "schema_version": "1.0",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "channels": ["codex", "claude", "user"],
                "notes": "Append-only JSONL. Events include type=msg and type=review.",
            }
            self.open_dialogue_log.write_text(json.dumps(meta, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception:
            return

    def _append_open_dialogue_event(
        self,
        sender: ParticipantRole,
        text: str,
        *,
        recipient: str = "all",
        meta: Optional[Dict[str, Any]] = None,
        ts: Optional[str] = None,
    ) -> str:
        evt_id = str(uuid.uuid4())
        evt = {
            "type": "msg",
            "id": evt_id,
            "ts": ts or datetime.now().isoformat(timespec="seconds"),
            "from": sender.value,
            "to": recipient,
            "text": text,
        }
        if meta:
            evt["meta"] = dict(meta)
        try:
            with self.open_dialogue_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(evt, ensure_ascii=False) + "\n")
        except Exception:
            return ""
        return evt_id

    def _read_open_dialogue_events(self, max_bytes: int = 5_000_000) -> List[Dict[str, Any]]:
        try:
            if not self.open_dialogue_log.exists():
                return []
            if self.open_dialogue_log.stat().st_size > max_bytes:
                with self.open_dialogue_log.open("rb") as bf:
                    bf.seek(-max_bytes, os.SEEK_END)
                    data = bf.read().decode("utf-8", errors="replace")
            else:
                data = self.open_dialogue_log.read_text(encoding="utf-8", errors="replace")
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

    def _sync_from_open_dialogue(self, *, display: bool = True) -> None:
        events = self._read_open_dialogue_events()
        new_msgs: List[ChatMessage] = []

        for e in events:
            if e.get("type") != "msg":
                continue
            mid = str(e.get("id") or "").strip()
            if not mid or mid in self._open_dialogue_seen_ids:
                continue
            sender = self._participant_from_str(str(e.get("from") or "user"))
            text = str(e.get("text") or "").strip()
            ts = str(e.get("ts") or datetime.now().isoformat())
            if not text:
                continue
            self._open_dialogue_seen_ids.add(mid)
            meta = e.get("meta") if isinstance(e.get("meta"), dict) else {}
            payload = {"open_dialogue_id": mid, "to": str(e.get("to") or "all"), **(meta or {})}
            new_msgs.append(
                ChatMessage(
                    sender=sender,
                    content=text,
                    timestamp=ts,
                    message_type=str(payload.get("message_type") or "text"),
                    metadata=payload,
                )
            )

        if not new_msgs:
            return

        new_msgs.sort(key=lambda m: m.timestamp)
        for msg in new_msgs:
            self.messages.append(msg)
            if display and hasattr(self, "chat_display"):
                try:
                    self._display_message(msg)
                except Exception:
                    pass

        try:
            self._save_collaboration_data()
        except Exception:
            pass

    def _bootstrap_open_dialogue_from_local_history(self) -> None:
        """
        If Open Dialogue is empty (meta only), migrate local chat history into JSONL once.
        """
        try:
            if not self.open_dialogue_log.exists():
                return
            lines = self.open_dialogue_log.read_text(encoding="utf-8", errors="replace").splitlines()
            has_msg = any('"type"' in ln and '"msg"' in ln for ln in lines)
            if has_msg:
                return
        except Exception:
            return

        for msg in self.messages[-500:]:
            try:
                self._append_open_dialogue_event(
                    msg.sender,
                    msg.content,
                    recipient="all",
                    meta={"source": "trinity_collaboration_hub_migration", "message_type": msg.message_type},
                    ts=msg.timestamp,
                )
            except Exception:
                continue

        # Clear local messages so a sync repopulates with canonical ids.
        try:
            self.messages = []
        except Exception:
            pass

    def _build_ui(self):
        """Build main UI with premium theme"""
        if self._parent is None:
            self.root = tk.Tk()
            self.standalone = True
        else:
            self.root = tk.Toplevel(self._parent)
            self.standalone = False
        self.root.title("Trinity Collaboration Hub - LightSpeed V1.0.0")
        self.root.geometry("1600x1000")

        # Apply premium theme or fallback
        if self.use_premium_theme:
            self.premium_theme.apply_to_root(self.root)
            self.root.configure(bg=self.premium_theme.palette.primary)
            bg_color = self.premium_theme.palette.primary
            self.theme = self.premium_theme  # Use premium theme as main theme
        else:
            self.root.configure(bg=self.classic_theme.BG_PRIMARY)
            bg_color = self.classic_theme.BG_PRIMARY
            self.theme = self.classic_theme  # Use classic theme as main theme

        # Main container (glass frame if premium)
        if self.use_premium_theme:
            main_container = self.premium_theme.create_glass_frame(self.root)
        else:
            main_container = tk.Frame(self.root, bg=bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        self._build_header(main_container)

        # Content (horizontal split)
        if self.use_premium_theme:
            content_frame = self.premium_theme.create_glass_frame(main_container)
        else:
            content_frame = tk.Frame(main_container, bg=self.classic_theme.BG_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left side: Chat + Proposals (70%)
        left_frame = tk.Frame(content_frame, bg=self.theme.BG_PRIMARY)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self._build_chat_area(left_frame)
        self._build_input_area(left_frame)

        # Right side: Proposals + M1-2/2-3 (30%)
        right_frame = tk.Frame(content_frame, bg=self.theme.BG_PRIMARY)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))
        right_frame.configure(width=450)

        self._build_proposals_area(right_frame)
        self._build_voting_area(right_frame)
        self._build_open_dialogue_inbox(right_frame)

        # Status bar
        self._build_status_bar(main_container)

    def _build_header(self, parent):
        """Build header with title and participant indicators"""
        # Use glass frame for header if premium theme available
        if self.use_premium_theme:
            header_frame = self.premium_theme.create_glass_frame(parent)
            header_frame.configure(height=80)
        else:
            header_frame = tk.Frame(parent, bg=self.classic_theme.BG_SECONDARY, height=80)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        # Title with premium styling
        if self.use_premium_theme:
            title = self.premium_theme.create_title_label(
                header_frame,
                text="⚡ Trinity Collaboration Hub"
            )
        else:
            title = tk.Label(
                header_frame,
                text="⚡ Trinity Collaboration Hub",
                font=(self.classic_theme.FONT_FAMILY, 18, 'bold'),
                fg=self.classic_theme.ACCENT,
                bg=self.classic_theme.BG_SECONDARY
            )
        title.pack(side=tk.LEFT, padx=20, pady=20)

        # Subtitle with premium body label
        if self.use_premium_theme:
            subtitle = self.premium_theme.create_body_label(
                header_frame,
                text="M1-2/2-3 Methodology | Real-Time AI Collaboration"
            )
        else:
            subtitle = tk.Label(
                header_frame,
                text="M1-2/2-3 Methodology | Real-Time AI Collaboration",
                font=(self.classic_theme.FONT_FAMILY, 10),
                fg=self.classic_theme.TEXT_SECONDARY,
                bg=self.classic_theme.BG_SECONDARY
            )
        subtitle.pack(side=tk.LEFT, padx=10, pady=20)

        # Participant indicators (right side) with glass frame
        if self.use_premium_theme:
            participants_frame = self.premium_theme.create_glass_frame(header_frame)
        else:
            participants_frame = tk.Frame(header_frame, bg=self.classic_theme.BG_SECONDARY)
        participants_frame.pack(side=tk.RIGHT, padx=20, pady=15)

        # User indicator (51%)
        self._create_participant_indicator(
            participants_frame, "USER", self.theme.USER_COLOR, "51%"
        ).pack(side=tk.LEFT, padx=10)

        # Claude indicator (24.5%)
        self._create_participant_indicator(
            participants_frame, "CLAUDE", self.theme.CLAUDE_COLOR, "24.5%"
        ).pack(side=tk.LEFT, padx=10)

        # Codex indicator (24.5%)
        self._create_participant_indicator(
            participants_frame, "CODEX", self.theme.CODEX_COLOR, "24.5%"
        ).pack(side=tk.LEFT, padx=10)

    def _create_participant_indicator(self, parent, name, color, weight):
        """Create participant status indicator with premium glass card"""
        # Use premium card frame if available
        if self.use_premium_theme:
            frame = self.premium_theme.create_card_frame(parent)
            frame.configure(padx=12, pady=8)
        else:
            frame = tk.Frame(parent, bg=self.classic_theme.BG_GLASS)

        # Status dot
        canvas = tk.Canvas(
            frame, width=12, height=12,
            bg=self.premium_theme.palette.primary if self.use_premium_theme else self.classic_theme.BG_GLASS,
            highlightthickness=0
        )
        canvas.create_oval(2, 2, 10, 10, fill=color, outline=color)
        canvas.pack(side=tk.LEFT, padx=5)

        # Name with premium label if available
        if self.use_premium_theme:
            label = self.premium_theme.create_body_label(frame, text=f"{name} ({weight})")
            label.configure(fg=color)
        else:
            label = tk.Label(
                frame, text=f"{name} ({weight})",
                font=(self.classic_theme.FONT_FAMILY, 9),
                fg=color, bg=self.classic_theme.BG_GLASS
            )
        label.pack(side=tk.LEFT, padx=5)

        return frame

    def _build_chat_area(self, parent):
        """Build main chat area with premium glass styling"""
        # Use glass frame for chat container if premium theme available
        if self.use_premium_theme:
            chat_container = self.premium_theme.create_glass_frame(parent)
        else:
            chat_container = tk.Frame(parent, bg=self.classic_theme.BG_SECONDARY)
        chat_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Chat header with premium label
        if self.use_premium_theme:
            chat_header = self.premium_theme.create_header_label(
                chat_container,
                text="💬 Collaboration Chat"
            )
        else:
            chat_header = tk.Label(
                chat_container,
                text="💬 Collaboration Chat",
                font=(self.classic_theme.FONT_FAMILY, self.classic_theme.FONT_SIZE_HEADER, 'bold'),
                fg=self.classic_theme.TEXT_PRIMARY,
                bg=self.classic_theme.BG_SECONDARY,
                anchor='w'
            )
        chat_header.pack(fill=tk.X, padx=15, pady=10)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            wrap=tk.WORD,
            font=(self.theme.FONT_FAMILY, self.theme.FONT_SIZE_NORMAL),
            bg=self.theme.BG_PRIMARY,
            fg=self.theme.TEXT_PRIMARY,
            insertbackground=self.theme.ACCENT,
            relief=tk.FLAT,
            padx=15,
            pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Configure tags for different participants
        self.chat_display.tag_config('user', foreground=self.theme.USER_COLOR, font=(self.theme.FONT_FAMILY, 10, 'bold'))
        self.chat_display.tag_config('claude', foreground=self.theme.CLAUDE_COLOR, font=(self.theme.FONT_FAMILY, 10, 'bold'))
        self.chat_display.tag_config('codex', foreground=self.theme.CODEX_COLOR, font=(self.theme.FONT_FAMILY, 10, 'bold'))
        self.chat_display.tag_config('timestamp', foreground=self.theme.TEXT_SECONDARY, font=(self.theme.FONT_FAMILY, 8))
        self.chat_display.tag_config('code', background='#1E1E2E', foreground='#00FF88', font=('Consolas', 9))

        # Load existing messages
        self._display_existing_messages()

    def _build_input_area(self, parent):
        """Build message input area with file upload and code drop"""
        # Use glass frame for input container if premium theme available
        if self.use_premium_theme:
            input_container = self.premium_theme.create_glass_frame(parent)
            input_container.configure(height=150)
        else:
            input_container = tk.Frame(parent, bg=self.classic_theme.BG_SECONDARY, height=150)
        input_container.pack(fill=tk.X, pady=(0, 10))
        input_container.pack_propagate(False)

        # Input header with buttons
        if self.use_premium_theme:
            input_header = self.premium_theme.create_glass_frame(input_container)
        else:
            input_header = tk.Frame(input_container, bg=self.classic_theme.BG_SECONDARY)
        input_header.pack(fill=tk.X, padx=15, pady=(10, 5))

        # "Your Message:" label with premium styling
        if self.use_premium_theme:
            self.premium_theme.create_body_label(
                input_header,
                text="Your Message:"
            ).pack(side=tk.LEFT)
        else:
            tk.Label(
                input_header, text="Your Message:",
                font=(self.classic_theme.FONT_FAMILY, self.classic_theme.FONT_SIZE_NORMAL, 'bold'),
                fg=self.classic_theme.TEXT_PRIMARY, bg=self.classic_theme.BG_SECONDARY
            ).pack(side=tk.LEFT)

        # Buttons with premium styling
        if self.use_premium_theme:
            buttons_frame = self.premium_theme.create_glass_frame(input_header)
        else:
            buttons_frame = tk.Frame(input_header, bg=self.classic_theme.BG_SECONDARY)
        buttons_frame.pack(side=tk.RIGHT)

        # Upload File button
        if self.use_premium_theme:
            self.premium_theme.create_premium_button(
                buttons_frame, text="📁 Upload File",
                command=self._handle_file_upload, style="secondary"
            ).pack(side=tk.LEFT, padx=5)
        else:
            self._create_button(
                buttons_frame, "📁 Upload File", self._handle_file_upload
            ).pack(side=tk.LEFT, padx=5)

        # Code Drop button
        if self.use_premium_theme:
            self.premium_theme.create_premium_button(
                buttons_frame, text="💾 Code Drop",
                command=self._handle_code_drop, style="secondary"
            ).pack(side=tk.LEFT, padx=5)
        else:
            self._create_button(
                buttons_frame, "💾 Code Drop", self._handle_code_drop
            ).pack(side=tk.LEFT, padx=5)

        # New Proposal button (gold style - important action)
        if self.use_premium_theme:
            self.premium_theme.create_premium_button(
                buttons_frame, text="📋 New Proposal",
                command=self._create_new_proposal, style="gold"
            ).pack(side=tk.LEFT, padx=5)
        else:
            self._create_button(
                buttons_frame, "📋 New Proposal", self._create_new_proposal
            ).pack(side=tk.LEFT, padx=5)

        # Text input
        self.message_input = scrolledtext.ScrolledText(
            input_container,
            wrap=tk.WORD,
            height=5,
            font=(self.theme.FONT_FAMILY, self.theme.FONT_SIZE_NORMAL),
            bg=self.theme.BG_PRIMARY,
            fg=self.theme.TEXT_PRIMARY,
            insertbackground=self.theme.ACCENT,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.message_input.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # Send button with premium gold styling
        if self.use_premium_theme:
            send_btn = self.premium_theme.create_premium_button(
                input_container,
                text="⚡ Send Message",
                command=self._send_message,
                style="gold"
            )
        else:
            send_btn = tk.Button(
                input_container,
                text="⚡ Send Message",
                command=self._send_message,
                bg=self.classic_theme.ACCENT,
                fg=self.classic_theme.BG_PRIMARY,
                font=(self.classic_theme.FONT_FAMILY, self.classic_theme.FONT_SIZE_NORMAL, 'bold'),
                relief=tk.FLAT,
                padx=20,
                pady=8,
                cursor='hand2'
            )
        send_btn.pack(side=tk.RIGHT, padx=15, pady=(0, 10))

        # Bind Enter to send
        self.message_input.bind('<Control-Return>', lambda e: self._send_message())

    def _build_proposals_area(self, parent):
        """Build proposals list area with premium glass styling"""
        # Use glass frame for proposals container if premium theme available
        if self.use_premium_theme:
            proposals_container = self.premium_theme.create_glass_frame(parent)
        else:
            proposals_container = tk.Frame(parent, bg=self.classic_theme.BG_SECONDARY)
        proposals_container.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Header with premium label
        if self.use_premium_theme:
            header = self.premium_theme.create_header_label(
                proposals_container,
                text="📋 Active Proposals"
            )
        else:
            header = tk.Label(
                proposals_container,
                text="📋 Active Proposals",
                font=(self.classic_theme.FONT_FAMILY, self.classic_theme.FONT_SIZE_HEADER, 'bold'),
                fg=self.classic_theme.TEXT_PRIMARY,
                bg=self.classic_theme.BG_SECONDARY,
                anchor='w'
            )
        header.pack(fill=tk.X, padx=15, pady=10)

        # Proposals list
        list_frame = tk.Frame(proposals_container, bg=self.theme.BG_PRIMARY)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollable list
        canvas = tk.Canvas(list_frame, bg=self.theme.BG_PRIMARY, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.proposals_list_frame = tk.Frame(canvas, bg=self.theme.BG_PRIMARY)

        self.proposals_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.proposals_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Refresh proposals list
        self._refresh_proposals_list()

    def _build_voting_area(self, parent):
        """Build M1-2/2-3 voting area with premium glass styling"""
        # Use glass frame for voting container if premium theme available
        if self.use_premium_theme:
            voting_container = self.premium_theme.create_glass_frame(parent)
            voting_container.configure(height=300)
        else:
            voting_container = tk.Frame(parent, bg=self.classic_theme.BG_SECONDARY, height=300)
        voting_container.pack(fill=tk.X, pady=(0, 10))
        voting_container.pack_propagate(False)

        # Header with premium label
        if self.use_premium_theme:
            header = self.premium_theme.create_header_label(
                voting_container,
                text="🗳️ M1-2/2-3 Sign-Off"
            )
        else:
            header = tk.Label(
                voting_container,
                text="🗳️ M1-2/2-3 Sign-Off",
                font=(self.classic_theme.FONT_FAMILY, self.classic_theme.FONT_SIZE_HEADER, 'bold'),
                fg=self.classic_theme.TEXT_PRIMARY,
                bg=self.classic_theme.BG_SECONDARY,
                anchor='w'
            )
        header.pack(fill=tk.X, padx=15, pady=10)

        # Active proposal info
        self.voting_info_label = tk.Label(
            voting_container,
            text="No active proposal selected",
            font=(self.theme.FONT_FAMILY, 9),
            fg=self.theme.TEXT_SECONDARY,
            bg=self.theme.BG_SECONDARY,
            anchor='w',
            justify=tk.LEFT
        )
        self.voting_info_label.pack(fill=tk.X, padx=15, pady=(0, 10))

        # Voting buttons with premium styling
        if self.use_premium_theme:
            vote_buttons_frame = self.premium_theme.create_glass_frame(voting_container)
        else:
            vote_buttons_frame = tk.Frame(voting_container, bg=self.classic_theme.BG_SECONDARY)
        vote_buttons_frame.pack(fill=tk.X, padx=15, pady=10)

        # Approve button (gold style for user 51% weight)
        if self.use_premium_theme:
            approve_btn = self.premium_theme.create_premium_button(
                vote_buttons_frame,
                text="✅ Approve (51%)",
                command=lambda: self._cast_vote(VoteType.APPROVE),
                style="gold"
            )
        else:
            approve_btn = tk.Button(
                vote_buttons_frame,
                text="✅ Approve (51%)",
                command=lambda: self._cast_vote(VoteType.APPROVE),
                bg=self.classic_theme.STATUS_APPROVED,
                fg=self.classic_theme.BG_PRIMARY,
                font=(self.classic_theme.FONT_FAMILY, 10, 'bold'),
                relief=tk.FLAT,
                padx=15,
                pady=8
            )
        approve_btn.pack(fill=tk.X, pady=5)

        # Request changes button (secondary style)
        if self.use_premium_theme:
            changes_btn = self.premium_theme.create_premium_button(
                vote_buttons_frame,
                text="🔄 Request Changes",
                command=lambda: self._cast_vote(VoteType.REQUEST_CHANGES),
                style="secondary"
            )
        else:
            changes_btn = tk.Button(
                vote_buttons_frame,
                text="🔄 Request Changes",
                command=lambda: self._cast_vote(VoteType.REQUEST_CHANGES),
                bg=self.classic_theme.STATUS_PENDING,
                fg=self.classic_theme.BG_PRIMARY,
                font=(self.classic_theme.FONT_FAMILY, 10),
                relief=tk.FLAT,
                padx=15,
                pady=8
            )
        changes_btn.pack(fill=tk.X, pady=5)

        # Reject button (danger style)
        if self.use_premium_theme:
            reject_btn = self.premium_theme.create_premium_button(
                vote_buttons_frame,
                text="❌ Reject",
                command=lambda: self._cast_vote(VoteType.REJECT),
                style="danger"
            )
        else:
            reject_btn = tk.Button(
                vote_buttons_frame,
                text="❌ Reject",
                command=lambda: self._cast_vote(VoteType.REJECT),
                bg=self.classic_theme.STATUS_REJECTED,
                fg=self.classic_theme.BG_PRIMARY,
                font=(self.classic_theme.FONT_FAMILY, 10),
                relief=tk.FLAT,
                padx=15,
                pady=8
            )
        reject_btn.pack(fill=tk.X, pady=5)

        # Defer button (glass style)
        if self.use_premium_theme:
            defer_btn = self.premium_theme.create_premium_button(
                vote_buttons_frame,
                text="⏸️ Defer",
                command=lambda: self._cast_vote(VoteType.DEFER),
                style="glass"
            )
        else:
            defer_btn = tk.Button(
                vote_buttons_frame,
                text="⏸️ Defer",
                command=lambda: self._cast_vote(VoteType.DEFER),
                bg=self.classic_theme.BG_GLASS,
                fg=self.classic_theme.TEXT_PRIMARY,
                font=(self.classic_theme.FONT_FAMILY, 10),
                relief=tk.FLAT,
                padx=15,
                pady=8
            )
        defer_btn.pack(fill=tk.X, pady=5)

    def _build_status_bar(self, parent):
        """Build status bar at bottom"""
        status_frame = tk.Frame(parent, bg=self.theme.BG_SECONDARY, height=40)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)

        # Status label
        self.status_label = tk.Label(
            status_frame,
            text="● Ready for collaboration",
            font=(self.theme.FONT_FAMILY, 9),
            fg=self.theme.STATUS_APPROVED,
            bg=self.theme.BG_SECONDARY
        )
        self.status_label.pack(side=tk.LEFT, padx=20)

        # Stats
        self.stats_label = tk.Label(
            status_frame,
            text=f"Messages: {len(self.messages)} | Proposals: {len(self.proposals)}",
            font=(self.theme.FONT_FAMILY, 9),
            fg=self.theme.TEXT_SECONDARY,
            bg=self.theme.BG_SECONDARY
        )
        self.stats_label.pack(side=tk.LEFT, padx=20)

        # Version info
        version_label = tk.Label(
            status_frame,
            text="LightSpeed V0.9.7 | Trinity Floor",
            font=(self.theme.FONT_FAMILY, 9),
            fg=self.theme.TEXT_SECONDARY,
            bg=self.theme.BG_SECONDARY
        )
        version_label.pack(side=tk.RIGHT, padx=20)

    def _create_button(self, parent, text, command):
        """Create styled button"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.theme.BG_GLASS,
            fg=self.theme.TEXT_PRIMARY,
            font=(self.theme.FONT_FAMILY, 9),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor='hand2'
        )
        return btn

    def _display_existing_messages(self):
        """Display existing chat messages"""
        for msg in self.messages[-100:]:  # Last 100 messages
            self._display_message(msg)

    def _display_message(self, msg: ChatMessage):
        """Display a single message in chat"""
        # Timestamp
        timestamp = datetime.fromisoformat(msg.timestamp).strftime("%H:%M:%S")
        self.chat_display.insert(tk.END, f"[{timestamp}] ", 'timestamp')

        # Sender name
        sender_tag = msg.sender.value
        self.chat_display.insert(tk.END, f"{msg.sender.value.upper()}: ", sender_tag)

        # Content
        if msg.message_type == "code":
            self.chat_display.insert(tk.END, f"\n{msg.content}\n\n", 'code')
        else:
            self.chat_display.insert(tk.END, f"{msg.content}\n\n")

        self.chat_display.see(tk.END)

    def _send_message(self):
        """Send user message to chat"""
        content = self.message_input.get("1.0", tk.END).strip()
        if not content:
            return

        # Create message
        msg = ChatMessage(
            sender=ParticipantRole.USER,
            content=content,
            timestamp=datetime.now().isoformat(),
            message_type="text"
        )

        # Add to messages
        self.messages.append(msg)
        self._display_message(msg)

        # Clear input
        self.message_input.delete("1.0", tk.END)

        # Append to shared Open Dialogue stream (canonical)
        try:
            oid = self._append_open_dialogue_event(
                msg.sender,
                msg.content,
                recipient="all",
                meta={"source": "collaboration_hub", "message_type": msg.message_type},
            )
            if oid:
                msg.metadata = {**(msg.metadata or {}), "open_dialogue_id": oid}
        except Exception:
            pass

        # Save (local mirror)
        self._save_collaboration_data()

        # Update status
        self._update_status("Message sent", self.theme.STATUS_APPROVED)

    def _handle_file_upload(self):
        """Handle file upload"""
        file_path = filedialog.askopenfilename(
            title="Select File to Upload",
            filetypes=[
                ("All Files", "*.*"),
                ("Python Files", "*.py"),
                ("JSON Files", "*.json"),
                ("Markdown Files", "*.md")
            ]
        )

        if not file_path:
            return

        file_path = Path(file_path)

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Create message
            msg = ChatMessage(
                sender=ParticipantRole.USER,
                content=f"📁 Uploaded file: {file_path.name}\n\nContent preview:\n{content[:500]}...",
                timestamp=datetime.now().isoformat(),
                message_type="file",
                metadata={'file_path': str(file_path), 'file_name': file_path.name}
            )

            self.messages.append(msg)
            self._display_message(msg)

            # Append to shared Open Dialogue stream
            try:
                oid = self._append_open_dialogue_event(
                    msg.sender,
                    msg.content,
                    recipient="all",
                    meta={"source": "collaboration_hub", "message_type": msg.message_type, **(msg.metadata or {})},
                )
                if oid:
                    msg.metadata = {**(msg.metadata or {}), "open_dialogue_id": oid}
            except Exception:
                pass

            self._save_collaboration_data()

            self._update_status(f"File uploaded: {file_path.name}", self.theme.STATUS_APPROVED)

        except Exception as e:
            messagebox.showerror("Upload Error", f"Failed to upload file: {e}")

    def _handle_code_drop(self):
        """Handle code drop"""
        # Open dialog for code paste
        dialog = tk.Toplevel(self.root)
        dialog.title("Code Drop")
        dialog.geometry("800x600")
        dialog.configure(bg=self.theme.BG_PRIMARY)

        tk.Label(
            dialog,
            text="Paste your code below:",
            font=(self.theme.FONT_FAMILY, 12, 'bold'),
            fg=self.theme.TEXT_PRIMARY,
            bg=self.theme.BG_PRIMARY
        ).pack(padx=20, pady=10)

        code_text = scrolledtext.ScrolledText(
            dialog,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg=self.theme.BG_SECONDARY,
            fg=self.theme.STATUS_APPROVED,
            insertbackground=self.theme.ACCENT
        )
        code_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        def submit_code():
            content = code_text.get("1.0", tk.END).strip()
            if content:
                msg = ChatMessage(
                    sender=ParticipantRole.USER,
                    content=content,
                    timestamp=datetime.now().isoformat(),
                    message_type="code"
                )
                self.messages.append(msg)
                self._display_message(msg)
                try:
                    oid = self._append_open_dialogue_event(
                        msg.sender,
                        msg.content,
                        recipient="all",
                        meta={"source": "collaboration_hub", "message_type": msg.message_type},
                    )
                    if oid:
                        msg.metadata = {**(msg.metadata or {}), "open_dialogue_id": oid}
                except Exception:
                    pass
                self._save_collaboration_data()
                dialog.destroy()
                self._update_status("Code dropped successfully", self.theme.STATUS_APPROVED)

        # Submit Code button with premium styling
        if self.use_premium_theme:
            self.premium_theme.create_premium_button(
                dialog,
                text="Submit Code",
                command=submit_code,
                style="gold"
            ).pack(pady=10)
        else:
            tk.Button(
                dialog,
                text="Submit Code",
                command=submit_code,
                bg=self.classic_theme.ACCENT,
                fg=self.classic_theme.BG_PRIMARY,
                font=(self.classic_theme.FONT_FAMILY, 10, 'bold'),
                padx=20,
                pady=8
            ).pack(pady=10)

    def _create_new_proposal(self):
        """Create new M1-2/2-3 proposal"""
        # Open proposal creation dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("New Proposal")
        dialog.geometry("900x700")
        dialog.configure(bg=self.theme.BG_PRIMARY)

        # Title
        tk.Label(
            dialog, text="Proposal Title:",
            font=(self.theme.FONT_FAMILY, 10, 'bold'),
            fg=self.theme.TEXT_PRIMARY,
            bg=self.theme.BG_PRIMARY
        ).pack(padx=20, pady=(20, 5), anchor='w')

        title_entry = tk.Entry(
            dialog,
            font=(self.theme.FONT_FAMILY, 10),
            bg=self.theme.BG_SECONDARY,
            fg=self.theme.TEXT_PRIMARY,
            insertbackground=self.theme.ACCENT
        )
        title_entry.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Description
        tk.Label(
            dialog, text="Description:",
            font=(self.theme.FONT_FAMILY, 10, 'bold'),
            fg=self.theme.TEXT_PRIMARY,
            bg=self.theme.BG_PRIMARY
        ).pack(padx=20, pady=(10, 5), anchor='w')

        desc_text = scrolledtext.ScrolledText(
            dialog,
            height=8,
            wrap=tk.WORD,
            font=(self.theme.FONT_FAMILY, 10),
            bg=self.theme.BG_SECONDARY,
            fg=self.theme.TEXT_PRIMARY,
            insertbackground=self.theme.ACCENT
        )
        desc_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Z-Axis floors
        tk.Label(
            dialog, text="Affected Z-Axis Floors (comma-separated):",
            font=(self.theme.FONT_FAMILY, 10, 'bold'),
            fg=self.theme.TEXT_PRIMARY,
            bg=self.theme.BG_PRIMARY
        ).pack(padx=20, pady=(10, 5), anchor='w')

        floors_entry = tk.Entry(
            dialog,
            font=(self.theme.FONT_FAMILY, 10),
            bg=self.theme.BG_SECONDARY,
            fg=self.theme.TEXT_PRIMARY,
            insertbackground=self.theme.ACCENT
        )
        floors_entry.pack(fill=tk.X, padx=20, pady=(0, 10))
        floors_entry.insert(0, "Merovingian, Neo, Trinity")

        def submit_proposal():
            title = title_entry.get().strip()
            description = desc_text.get("1.0", tk.END).strip()
            floors = [f.strip() for f in floors_entry.get().split(',')]

            if not title or not description:
                messagebox.showwarning("Invalid Proposal", "Please fill in all fields")
                return

            # Create proposal ID
            proposal_id = hashlib.md5(
                f"{title}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:8]

            # Create proposal
            proposal = Proposal(
                id=proposal_id,
                title=title,
                description=description,
                proposer=ParticipantRole.USER,
                status=ProposalStatus.DRAFT,
                created_at=datetime.now().isoformat(),
                z_axis_floors=floors,
                affected_files=[],
                code_changes={}
            )

            self.proposals[proposal_id] = proposal
            self._refresh_proposals_list()
            self._save_collaboration_data()

            dialog.destroy()
            self._update_status(f"Proposal created: {title}", self.theme.STATUS_APPROVED)

            # Add to chat
            msg = ChatMessage(
                sender=ParticipantRole.USER,
                content=f"📋 Created proposal: {title}\n\nFloors: {', '.join(floors)}\n\nDescription: {description}",
                timestamp=datetime.now().isoformat(),
                message_type="proposal",
                metadata={'proposal_id': proposal_id}
            )
            self.messages.append(msg)
            self._display_message(msg)
            try:
                oid = self._append_open_dialogue_event(
                    msg.sender,
                    msg.content,
                    recipient="all",
                    meta={"source": "collaboration_hub", "message_type": msg.message_type, "proposal_id": proposal_id},
                )
                if oid:
                    msg.metadata = {**(msg.metadata or {}), "open_dialogue_id": oid}
            except Exception:
                pass

            self._save_collaboration_data()

        # Create Proposal button with premium gold styling
        if self.use_premium_theme:
            self.premium_theme.create_premium_button(
                dialog,
                text="Create Proposal",
                command=submit_proposal,
                style="gold"
            ).pack(pady=20)
        else:
            tk.Button(
                dialog,
                text="Create Proposal",
                command=submit_proposal,
                bg=self.classic_theme.ACCENT,
                fg=self.classic_theme.BG_PRIMARY,
                font=(self.classic_theme.FONT_FAMILY, 10, 'bold'),
                padx=20,
                pady=8
            ).pack(pady=20)

    def _refresh_proposals_list(self):
        """Refresh proposals list display"""
        # Clear existing
        for widget in self.proposals_list_frame.winfo_children():
            widget.destroy()

        # Add proposals
        for prop in self.proposals.values():
            self._create_proposal_widget(prop)

    def _create_proposal_widget(self, proposal: Proposal):
        """Create widget for single proposal with premium glass card"""
        # Use premium card frame with elevation if available
        if self.use_premium_theme:
            prop_frame = self.premium_theme.create_card_frame(self.proposals_list_frame)
        else:
            prop_frame = tk.Frame(
                self.proposals_list_frame,
                bg=self.classic_theme.BG_GLASS,
                relief=tk.FLAT
            )
        prop_frame.pack(fill=tk.X, padx=5, pady=5)

        # Title with premium header label
        if self.use_premium_theme:
            title_label = self.premium_theme.create_header_label(prop_frame, text=proposal.title)
            title_label.pack(fill=tk.X, padx=10, pady=(10, 5))
        else:
            tk.Label(
                prop_frame,
                text=proposal.title,
                font=(self.classic_theme.FONT_FAMILY, 10, 'bold'),
                fg=self.classic_theme.TEXT_PRIMARY,
                bg=self.classic_theme.BG_GLASS,
                anchor='w'
            ).pack(fill=tk.X, padx=10, pady=(10, 5))

        # Status with color coding
        status_color = {
            ProposalStatus.DRAFT: self.theme.TEXT_SECONDARY if hasattr(self.theme, 'TEXT_SECONDARY') else '#AAAAAA',
            ProposalStatus.PENDING_M1: self.theme.STATUS_PENDING if hasattr(self.theme, 'STATUS_PENDING') else '#FFAA00',
            ProposalStatus.PENDING_M2: self.theme.STATUS_PENDING if hasattr(self.theme, 'STATUS_PENDING') else '#FFAA00',
            ProposalStatus.PENDING_M3: self.theme.STATUS_PENDING if hasattr(self.theme, 'STATUS_PENDING') else '#FFAA00',
            ProposalStatus.APPROVED: self.theme.STATUS_APPROVED if hasattr(self.theme, 'STATUS_APPROVED') else '#00FF88',
            ProposalStatus.REJECTED: self.theme.STATUS_REJECTED if hasattr(self.theme, 'STATUS_REJECTED') else '#FF4444'
        }.get(proposal.status, '#AAAAAA')

        if self.use_premium_theme:
            status_label = self.premium_theme.create_body_label(
                prop_frame,
                text=f"Status: {proposal.status.value.upper()} | Score: {proposal.approval_score:.1%}"
            )
            status_label.configure(fg=status_color)
            status_label.pack(fill=tk.X, padx=10, pady=(0, 5))
        else:
            tk.Label(
                prop_frame,
                text=f"Status: {proposal.status.value.upper()} | Score: {proposal.approval_score:.1%}",
                font=(self.classic_theme.FONT_FAMILY, 8),
                fg=status_color,
                bg=self.classic_theme.BG_GLASS,
                anchor='w'
            ).pack(fill=tk.X, padx=10, pady=(0, 5))

        # Select button with premium gold styling
        if self.use_premium_theme:
            select_btn = self.premium_theme.create_premium_button(
                prop_frame,
                text="Select",
                command=lambda: self._select_proposal(proposal),
                style="gold"
            )
        else:
            select_btn = tk.Button(
                prop_frame,
                text="Select",
                command=lambda: self._select_proposal(proposal),
                bg=self.classic_theme.ACCENT,
                fg=self.classic_theme.BG_PRIMARY,
                font=(self.classic_theme.FONT_FAMILY, 8),
                relief=tk.FLAT,
                padx=10,
                pady=3
            )
        select_btn.pack(side=tk.RIGHT, padx=10, pady=(0, 10))

    def _select_proposal(self, proposal: Proposal):
        """Select proposal for voting"""
        self.active_proposal = proposal

        # Update voting info
        info_text = f"Proposal: {proposal.title}\n"
        info_text += f"Status: {proposal.status.value.upper()}\n"
        info_text += f"Approval Score: {proposal.approval_score:.1%}\n"
        info_text += f"Floors: {', '.join(proposal.z_axis_floors)}"

        self.voting_info_label.config(text=info_text)

        self._update_status(f"Selected proposal: {proposal.title}", self.theme.ACCENT)

    def _cast_vote(self, vote_type: VoteType):
        """Cast vote on active proposal"""
        if not self.active_proposal:
            messagebox.showwarning("No Proposal", "Please select a proposal first")
            return

        # Determine milestone
        milestone = "M1"
        if self.active_proposal.status == ProposalStatus.PENDING_M2:
            milestone = "M2"
        elif self.active_proposal.status == ProposalStatus.PENDING_M3:
            milestone = "M3"

        # Create vote
        vote = Vote(
            participant=ParticipantRole.USER,
            vote_type=vote_type,
            weight=self.voting_weights[ParticipantRole.USER],
            comment="",
            timestamp=datetime.now().isoformat(),
            milestone=milestone
        )

        self.active_proposal.votes.append(vote)

        # Update proposal status based on votes
        self._update_proposal_status(self.active_proposal)

        # Refresh UI
        self._refresh_proposals_list()
        self._save_collaboration_data()

        # Add to chat
        msg = ChatMessage(
            sender=ParticipantRole.USER,
            content=f"🗳️ Cast vote on '{self.active_proposal.title}': {vote_type.value.upper()} ({milestone})",
            timestamp=datetime.now().isoformat(),
            message_type="text"
        )
        self.messages.append(msg)
        self._display_message(msg)
        try:
            oid = self._append_open_dialogue_event(
                msg.sender,
                msg.content,
                recipient="all",
                meta={
                    "source": "collaboration_hub",
                    "message_type": msg.message_type,
                    "proposal_id": getattr(self.active_proposal, "id", ""),
                    "vote_type": vote_type.value,
                    "milestone": milestone,
                },
            )
            if oid:
                msg.metadata = {**(msg.metadata or {}), "open_dialogue_id": oid}
        except Exception:
            pass

        self._save_collaboration_data()

        self._update_status(f"Vote cast: {vote_type.value}", self.theme.STATUS_APPROVED)

    # ---------------------------------------------------------------------
    # Open Dialogue inbox + review (shared with OpenDialogueBoard)
    # ---------------------------------------------------------------------

    def _build_open_dialogue_state(self) -> List[OpenDialogueMessageState]:
        events = self._read_open_dialogue_events()
        msgs: Dict[str, Dict[str, Any]] = {}
        reviews: Dict[str, List[Dict[str, Any]]] = {}

        for e in events:
            et = e.get("type")
            if et == "msg":
                mid = str(e.get("id") or "").strip()
                if not mid:
                    continue
                msgs[mid] = e
            elif et == "review":
                mid = str(e.get("msg_id") or "").strip()
                if not mid:
                    continue
                reviews.setdefault(mid, []).append(e)

        states: List[OpenDialogueMessageState] = []
        for mid, m in msgs.items():
            rv = reviews.get(mid, [])
            reviewed_by: List[str] = []
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
                OpenDialogueMessageState(
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

        states.sort(key=lambda s: s.ts, reverse=True)
        return states

    def _build_open_dialogue_inbox(self, parent):
        if self.use_premium_theme:
            inbox = self.premium_theme.create_glass_frame(parent)
        else:
            inbox = tk.Frame(parent, bg=self.classic_theme.BG_SECONDARY)
        inbox.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        if self.use_premium_theme:
            header = self.premium_theme.create_header_label(inbox, text="🗣️ Open Dialogue Inbox")
        else:
            header = tk.Label(
                inbox,
                text="🗣️ Open Dialogue Inbox",
                font=(self.classic_theme.FONT_FAMILY, self.classic_theme.FONT_SIZE_HEADER, 'bold'),
                fg=self.classic_theme.TEXT_PRIMARY,
                bg=self.classic_theme.BG_SECONDARY,
                anchor='w',
            )
        header.pack(fill=tk.X, padx=15, pady=10)

        self._open_dialogue_states: List[OpenDialogueMessageState] = []
        self._open_dialogue_selected: Optional[OpenDialogueMessageState] = None

        table = ttk.Frame(inbox)
        table.pack(fill=tk.BOTH, expand=True, padx=10)
        table.rowconfigure(1, weight=1)
        table.columnconfigure(0, weight=1)

        cols = ("ts", "from", "to", "status", "preview")
        self.open_dialogue_tree = ttk.Treeview(table, columns=cols, show="headings", height=7)
        for c, w in [("ts", 120), ("from", 70), ("to", 70), ("status", 70), ("preview", 350)]:
            self.open_dialogue_tree.heading(c, text=c)
            self.open_dialogue_tree.column(c, width=w, anchor="w")
        self.open_dialogue_tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(table, orient="vertical", command=self.open_dialogue_tree.yview)
        self.open_dialogue_tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        details = ttk.Frame(inbox)
        details.pack(fill=tk.BOTH, expand=False, padx=10, pady=(8, 10))
        details.columnconfigure(0, weight=1)

        self.open_dialogue_detail = scrolledtext.ScrolledText(details, height=7, wrap="word")
        self.open_dialogue_detail.grid(row=0, column=0, sticky="nsew")

        btns = ttk.Frame(inbox)
        btns.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(btns, text="Refresh", command=self._refresh_open_dialogue_inbox).pack(side=tk.LEFT)
        ttk.Button(btns, text="Y (Approve)", command=lambda: self._review_open_dialogue("Y")).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(btns, text="N (Reject)", command=lambda: self._review_open_dialogue("N")).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(btns, text="Reply…", command=self._reply_open_dialogue).pack(side=tk.LEFT, padx=(8, 0))

        self.open_dialogue_tree.bind("<<TreeviewSelect>>", lambda _e: self._select_open_dialogue_row())
        self._refresh_open_dialogue_inbox()

    def _refresh_open_dialogue_inbox(self):
        if not hasattr(self, "open_dialogue_tree"):
            return
        try:
            for row in self.open_dialogue_tree.get_children():
                self.open_dialogue_tree.delete(row)
        except Exception:
            pass

        self._open_dialogue_states = self._build_open_dialogue_state()

        # Show only messages "to all" or "to user", newest first. Mark if user already reviewed.
        for st in self._open_dialogue_states[:200]:
            to = (st.recipient or "").strip().lower()
            if to not in ("all", "user"):
                continue
            reviewed = "reviewed" if "user" in st.reviewed_by else "new"
            preview = (st.text or "").replace("\n", " ").strip()
            if len(preview) > 120:
                preview = preview[:117] + "..."
            self.open_dialogue_tree.insert("", "end", values=(st.ts, st.sender, st.recipient, reviewed, preview))

        self._select_open_dialogue_row()

    def _select_open_dialogue_row(self):
        self._open_dialogue_selected = None
        widget = getattr(self, "open_dialogue_detail", None)
        if widget is None:
            return

        try:
            sel = self.open_dialogue_tree.selection()
            if not sel:
                widget.delete("1.0", tk.END)
                widget.insert("end", "Select a message to review.\n")
                return

            row_id = sel[0]
            vals = self.open_dialogue_tree.item(row_id).get("values") or []
            ts = str(vals[0]) if len(vals) > 0 else ""
            sender = str(vals[1]) if len(vals) > 1 else ""
            recipient = str(vals[2]) if len(vals) > 2 else ""

            match = None
            for st in self._open_dialogue_states:
                if st.ts == ts and st.sender == sender and st.recipient == recipient:
                    match = st
                    break
            if match is None:
                widget.delete("1.0", tk.END)
                widget.insert("end", "Message not found (refresh).\n")
                return

            self._open_dialogue_selected = match
            widget.delete("1.0", tk.END)
            widget.insert("end", f"ID: {match.msg_id}\nFrom: {match.sender}  To: {match.recipient}\nTS: {match.ts}\n\n{match.text}\n\n")
            if match.decisions or match.replies:
                widget.insert("end", "Reviews:\n")
                for by in sorted(set(list(match.decisions.keys()) + list(match.replies.keys()))):
                    dec = match.decisions.get(by, "")
                    rep = match.replies.get(by, "")
                    line = f"- {by}: {dec}"
                    if rep:
                        line += f" | reply: {rep}"
                    widget.insert("end", line + "\n")
        except Exception:
            return

    def _append_review_event(self, *, msg_id: str, decision: str, reply: Optional[str] = None):
        evt = {
            "type": "review",
            "id": str(uuid.uuid4()),
            "ts": datetime.now().isoformat(timespec="seconds"),
            "by": "user",
            "msg_id": msg_id,
            "decision": decision,
        }
        if reply:
            evt["reply"] = reply

        try:
            with self.open_dialogue_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(evt, ensure_ascii=False) + "\n")
        except Exception:
            return

    def _review_open_dialogue(self, decision: str):
        st = getattr(self, "_open_dialogue_selected", None)
        if st is None:
            return
        self._append_review_event(msg_id=st.msg_id, decision=decision)
        self._refresh_open_dialogue_inbox()

    def _reply_open_dialogue(self):
        st = getattr(self, "_open_dialogue_selected", None)
        if st is None:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Reply")
        dialog.geometry("720x420")
        dialog.configure(bg=self.theme.BG_PRIMARY)

        tk.Label(dialog, text=f"Reply to {st.sender} ({st.msg_id})", bg=self.theme.BG_PRIMARY, fg=self.theme.TEXT_PRIMARY).pack(
            anchor="w", padx=12, pady=(12, 6)
        )
        box = scrolledtext.ScrolledText(dialog, height=10, wrap="word")
        box.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        def submit():
            text = box.get("1.0", tk.END).strip()
            if not text:
                dialog.destroy()
                return
            self._append_review_event(msg_id=st.msg_id, decision="REPLY", reply=text)
            # Also append an actual message for visibility in both UIs
            try:
                self._append_open_dialogue_event(ParticipantRole.USER, text, recipient="all", meta={"source": "collaboration_hub", "in_reply_to": st.msg_id})
            except Exception:
                pass
            dialog.destroy()
            self._refresh_open_dialogue_inbox()

        ttk.Button(dialog, text="Send Reply", command=submit).pack(side=tk.RIGHT, padx=12, pady=12)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=(0, 8), pady=12)

    def _update_proposal_status(self, proposal: Proposal):
        """Update proposal status based on votes"""
        if proposal.is_approved:
            proposal.status = ProposalStatus.APPROVED
        elif proposal.can_proceed_m2_to_m3:
            proposal.status = ProposalStatus.PENDING_M3
        elif proposal.can_proceed_m1_to_m2:
            proposal.status = ProposalStatus.PENDING_M2
        else:
            proposal.status = ProposalStatus.PENDING_M1

    def _update_status(self, message: str, color: str):
        """Update status bar"""
        self.status_label.config(text=f"● {message}", fg=color)
        self.stats_label.config(text=f"Messages: {len(self.messages)} | Proposals: {len(self.proposals)}")

    def _start_message_processor(self):
        """Start background message processor"""
        def process_messages():
            while True:
                try:
                    # Poll the shared Open Dialogue stream so this hub stays in sync with the
                    # lightweight Open Dialogue Board (and future automation).
                    time.sleep(2.0)
                    try:
                        if hasattr(self, "root") and self.root.winfo_exists():
                            self.root.after(0, lambda: self._sync_from_open_dialogue(display=True))
                            self.root.after(0, self._refresh_open_dialogue_inbox)
                    except Exception:
                        continue
                except Exception:
                    break

        thread = threading.Thread(target=process_messages, daemon=True)
        thread.start()

    def run(self):
        """Start the collaboration hub"""
        if self.standalone:
            self.root.mainloop()
        else:
            try:
                self.root.lift()
                self.root.focus_force()
            except Exception:
                pass


# Main entry point
if __name__ == "__main__":
    lightspeed_root = Path(__file__).parents[3]
    hub = TrinityCollaborationHub(lightspeed_root)
    hub.run()
