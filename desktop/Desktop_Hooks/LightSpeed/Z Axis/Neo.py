#!/usr/bin/env python
"""
Neo (Z+2) - AI Integration Floor
Complete Floor Coordinator with AI Models, Training, and Context Management

Neo is THE primary AI integration layer. It holds:
- AI model management (Achilles, learning engines)
- Training pipelines and fine-tuning
- Context management and memory
- Code assistance and generation
- Romer synchronization (external AI coordination)

Variables Held:
- active_models: Currently loaded AI models
- training_jobs: Running training pipelines
- context_store: Conversation and session context
- model_configs: Model hyperparameters and settings
- code_assistant_state: Active code generation sessions

Renders:
- Lab Assistant UI (AI chat interface)
- Code Assistant (code generation tools)
- Training dashboard (model training)
- Context viewer (memory management)
- Romer Sync panel (external coordination)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Callable, List, Any
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import json
import os
from datetime import datetime, timezone
import re


def _load_symbol(rel_path: str, symbol: str):
    """Load a symbol (class/function) from a file by relative path"""
    root = Path(__file__).resolve().parents[1]
    path = (root / rel_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    mod_name = f"lightspeed_dynamic_{path.stem}_{abs(hash(str(path)))%1_000_000}"
    spec = spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    mod = module_from_spec(spec)
    # Ensure dataclasses/type evaluation can resolve __module__ via sys.modules.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, symbol):
        raise AttributeError(f"{symbol} not found in {path}")
    return getattr(mod, symbol)


# Backwards compatibility
_load_class = _load_symbol


class NeoFloorState:
    """
    State manager for Neo floor

    This class holds all state variables for the AI integration layer
    """

    def __init__(self):
        # AI Model state
        self.active_models: Dict[str, Any] = {}
        self.model_configs: Dict[str, Dict] = {}
        self.default_model = "achilles"

        # Training state
        self.training_jobs: List[Dict[str, Any]] = []
        self.training_history: List[Dict] = []
        self.last_training_metrics: Dict[str, float] = {}

        # Context management
        self.context_store: List[Dict[str, Any]] = []
        self.max_context_length = 8000
        self.active_conversations: Dict[str, List] = {}

        # Code assistant state
        self.code_assistant_active = False
        self.active_code_sessions: List[Dict] = []
        self.code_generation_history: List[Dict] = []

        # Romer sync state
        self.romer_connected = False
        self.romer_last_sync: Optional[str] = None
        self.external_ai_endpoints: Dict[str, str] = {}

        # Learning engine state
        self.learning_enabled = True
        self.learned_patterns: List[Dict] = []
        self.adaptation_rate = 0.1

    def add_to_context(self, role: str, content: str, session_id: str = "default"):
        """Add a message to context store"""
        if session_id not in self.active_conversations:
            self.active_conversations[session_id] = []

        self.active_conversations[session_id].append({
            'role': role,
            'content': content,
            'timestamp': None  # Would use datetime in production
        })

        # Trim if exceeds max length
        while len(str(self.active_conversations[session_id])) > self.max_context_length:
            self.active_conversations[session_id].pop(0)

    def record_training_job(self, job_type: str, config: Dict):
        """Record a training job"""
        self.training_jobs.append({
            'type': job_type,
            'config': config,
            'status': 'running'
        })


class NeoUI(ttk.Frame):
    """
    Primary Neo UI - AI Integration Floor

    Neo owns all AI model management, training, context, and code assistance.
    It coordinates with external AI systems and manages learning pipelines.
    """

    def __init__(self, parent: tk.Misc, app: Optional[object] = None, *, compact: bool = False, **_ignored):
        super().__init__(parent)
        self.app = app
        self.compact = bool(compact)
        self.state = NeoFloorState()
        self.neo_bridge = getattr(app, "neo_achilles_bridge", None)

        # Services (prefer shared app instances)
        try:
            from core.services import get_db, get_event_bus, get_storage
            self.db = getattr(app, "db", None) or get_db()
            self.event_bus = getattr(app, "event_bus", None) or get_event_bus()
            self.storage = getattr(app, "storage", None) or get_storage()
        except Exception:
            self.db = None
            self.event_bus = None
            self.storage = None

        # Register Bento widgets
        self._register_bento_widgets()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._tabs: Dict[str, ttk.Frame] = {}
        self._builders: Dict[str, Callable[[ttk.Frame], None]] = {}
        self._tab_group: Dict[str, str] = {}
        self._tab_container: Dict[str, Any] = {}
        self._group_frames: Dict[str, ttk.Frame] = {}

        if self.compact:
            self._build_compact_shell()
        else:
            self._build_full_shell()

    def _build_full_shell(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self._register_tab("Workbench", self._build_workbench)
        self._register_tab("Lab Assistant", self._build_lab_assistant)
        self._register_tab("Code Assistant", self._build_code_assistant)
        self._register_tab("Training", self._build_training)
        self._register_tab("Context", self._build_context)
        self._register_tab("Romer Sync", self._build_romer_sync)
        self._register_tab("Model Config", self._build_model_config)
        # Neo-owned: plan/propose flows (stage-only; Trinity remains the commit gate).
        self._register_tab("Planner", self._build_planner)
        self._register_tab("API Manager", self._build_api_manager)
        self._register_tab("Z Direct Registry", self._build_z_direct_registry)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._ensure_built("Workbench")

    def _build_compact_shell(self) -> None:
        """
        Compact embedding for IT Portal:
        - Workbench (single primary orchestration surface)
        - Assistant (lab assistant + context)
        - Tools (code/training/sync/model/api)
        - Governance (planner + Z Direct)
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        workbench_group = ttk.Frame(self.notebook)
        assistant_group = ttk.Frame(self.notebook)
        tools_group = ttk.Frame(self.notebook)
        gov_group = ttk.Frame(self.notebook)

        self.notebook.add(workbench_group, text="Workbench")
        self.notebook.add(assistant_group, text="Assistant")
        self.notebook.add(tools_group, text="Tools")
        self.notebook.add(gov_group, text="Governance")

        self._group_frames = {
            "Workbench": workbench_group,
            "Assistant": assistant_group,
            "Tools": tools_group,
            "Governance": gov_group,
        }

        self._tabs["Workbench"] = workbench_group
        self._builders["Workbench"] = self._build_workbench
        self._tab_group["Workbench"] = "Workbench"
        self._tab_container["Workbench"] = None

        asst_nb = ttk.Notebook(assistant_group)
        asst_nb.pack(fill="both", expand=True)
        self._register_tab("Lab Assistant", self._build_lab_assistant, notebook=asst_nb, group="Assistant")
        self._register_tab("Context", self._build_context, notebook=asst_nb, group="Assistant")

        tools_nb = ttk.Notebook(tools_group)
        tools_nb.pack(fill="both", expand=True)
        self._register_tab("Code Assistant", self._build_code_assistant, notebook=tools_nb, group="Tools")
        self._register_tab("Training", self._build_training, notebook=tools_nb, group="Tools")
        self._register_tab("Romer Sync", self._build_romer_sync, notebook=tools_nb, group="Tools")
        self._register_tab("Model Config", self._build_model_config, notebook=tools_nb, group="Tools")
        self._register_tab("API Manager", self._build_api_manager, notebook=tools_nb, group="Tools")

        gov_nb = ttk.Notebook(gov_group)
        gov_nb.pack(fill="both", expand=True)
        self._register_tab("Planner", self._build_planner, notebook=gov_nb, group="Governance")
        self._register_tab("Z Direct Registry", self._build_z_direct_registry, notebook=gov_nb, group="Governance")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_group_tab_changed)
        asst_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        tools_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        gov_nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._ensure_built("Workbench")

    def _register_tab(
        self,
        title: str,
        builder: Callable[[ttk.Frame], None],
        *,
        notebook: Optional[ttk.Notebook] = None,
        group: str = "Assistant",
    ) -> None:
        nb = notebook or self.notebook
        frame = ttk.Frame(nb)
        nb.add(frame, text=title)
        self._tabs[title] = frame
        self._builders[title] = builder
        self._tab_group[title] = group
        self._tab_container[title] = nb

    def _on_tab_changed(self, _evt=None) -> None:
        try:
            nb = _evt.widget if _evt is not None and hasattr(_evt, "widget") else self.notebook
            idx = nb.index("current")
            title = nb.tab(idx, "text")
            self._ensure_built(str(title))
        except Exception:
            return

    def _on_group_tab_changed(self, _evt=None) -> None:
        """When switching compact groups, ensure the visible leaf is built."""
        try:
            group = self.notebook.tab(self.notebook.select(), "text")
        except Exception:
            return
        if group == "Workbench":
            self._ensure_built("Workbench")
            return
        # Each group tab contains a nested notebook. Build the currently-selected leaf.
        try:
            grp_frame = self._group_frames.get(group)
            if grp_frame is None:
                return
            children = [w for w in grp_frame.winfo_children() if isinstance(w, ttk.Notebook)]
            if not children:
                return
            nb = children[0]
            leaf = nb.tab(nb.select(), "text")
            self._ensure_built(str(leaf))
        except Exception:
            return

    def _ensure_built(self, title: str) -> None:
        frame = self._tabs.get(title)
        builder = self._builders.get(title)
        if frame is None or builder is None:
            return
        if getattr(frame, "_built", False):
            return
        builder(frame)
        setattr(frame, "_built", True)

    def select_tab(self, title: str) -> None:
        """Select a leaf tab by title, regardless of compact/full shell."""
        if title not in self._tabs:
            return
        if not self.compact:
            try:
                self.notebook.select(self._tabs[title])
            except Exception:
                pass
            self._ensure_built(title)
            return

        group = self._tab_group.get(title) or "Assistant"
        try:
            self.notebook.select(self._group_frames[group])
        except Exception:
            pass
        if group == "Workbench":
            self._ensure_built("Workbench")
            return
        nb = self._tab_container.get(title)
        if nb is not None:
            try:
                nb.select(self._tabs[title])
            except Exception:
                pass
        self._ensure_built(title)

    def _build_workbench(self, parent: ttk.Frame) -> None:
        try:
            from core.ui.base_portal_glass import mount_smart_ops_strip  # type: ignore

            mount_smart_ops_strip(parent, app=self.app, floor_channel="Z+2", it_portal=self.compact, title="Neo Ops")
        except Exception:
            pass
        try:
            from lightspeed_runtime.desktop_adapters import build_neo_orchestration_panel

            panel = build_neo_orchestration_panel(parent, self.app)
            if panel is not None:
                panel.pack(fill="x", padx=12, pady=(0, 10))
        except Exception:
            pass

        actions = ttk.Frame(parent)
        actions.pack(fill="x", padx=12, pady=(0, 10))
        ttk.Label(
            actions,
            text="Primary Neo workbench: orchestrate here first, then open a deeper model or governance surface on demand.",
            justify="left",
        ).pack(side="left", padx=(0, 12))
        ttk.Button(actions, text="Lab Assistant", command=lambda: self.select_tab("Lab Assistant")).pack(side="left")
        ttk.Button(actions, text="Code Assistant", command=lambda: self.select_tab("Code Assistant")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Planner", command=lambda: self.select_tab("Planner")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Model Config", command=lambda: self.select_tab("Model Config")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Z Direct", command=lambda: self.select_tab("Z Direct Registry")).pack(side="left", padx=(8, 0))

        control = ttk.LabelFrame(parent, text="Realisation Control")
        control.pack(fill="x", padx=12, pady=(0, 10))
        status = tk.Text(control, height=10, wrap="word", font=("Consolas", 9))
        status.pack(fill="x", padx=10, pady=(8, 8))

        def _set_status(message: str) -> None:
            try:
                status.delete("1.0", "end")
            except Exception:
                return
            status.insert("1.0", message)

        def _load_realisation() -> tuple[dict[str, Any], dict[str, Any]]:
            bridge = getattr(self.app, "agent_home_bridge", None)
            if bridge is None:
                return {}, {}
            try:
                summary = bridge.summary()
            except Exception as exc:
                return {}, {"error": str(exc)}
            return summary, (summary.get("neo_realisation_runtime") or {})

        def _render_realisation(note: str | None = None) -> None:
            summary, payload = _load_realisation()
            if not payload or payload.get("error"):
                if isinstance(payload, dict) and payload.get("error"):
                    _set_status(str(payload.get("error")))
                    return
                if isinstance(summary, dict) and summary.get("error"):
                    _set_status(str(summary.get("error")))
                    return
                _set_status(note or "Neo realisation runtime unavailable.")
                return
            current_wave = payload.get("current_wave") or {}
            lines = [
                f"Runtime: {payload.get('runtime_id', 'unknown')} | state={payload.get('state', 'unknown')}",
                (
                    f"Current wave: {payload.get('current_wave_label', 'unknown')} | "
                    f"state={payload.get('current_wave_state', 'unknown')} | "
                    f"tasks={payload.get('current_wave_task_count', 0)} | "
                    f"training_loops={payload.get('current_wave_training_loop_count', 0)}"
                ),
            ]
            if current_wave.get("goal"):
                lines.append(f"Goal: {current_wave.get('goal')}")
            local_runtime = summary.get("neo_local_runtime") or {}
            if local_runtime:
                lines.append(
                    "Local runtime: "
                    f"{local_runtime.get('state', 'unknown')} | "
                    f"profile={local_runtime.get('active_profile', 'unknown')} | "
                    f"models={local_runtime.get('available_model_count', 0)} | "
                    f"temp_shells={local_runtime.get('temp_shell_count', 0)}"
                )
            task_refs = current_wave.get("task_refs") or []
            if task_refs:
                lines.append("Tasks: " + ", ".join(str(item) for item in task_refs[:6]))
            training_loop_ids = current_wave.get("training_loop_ids") or []
            if training_loop_ids:
                lines.append("Training: " + ", ".join(str(item) for item in training_loop_ids[:4]))
            if note:
                lines.append("")
                lines.append(note)
            _set_status("\n".join(lines))

        def _stage_current_wave() -> None:
            summary, payload = _load_realisation()
            if not payload:
                _render_realisation("Cannot stage: Neo realisation runtime is unavailable.")
                return
            current_wave = payload.get("current_wave") or {}
            wave_id = str(current_wave.get("wave_id") or "").strip()
            if not wave_id:
                _render_realisation("Cannot stage: no current wave is defined.")
                return

            try:
                from core.services import get_z_direct  # type: ignore

                z_direct = get_z_direct()
            except Exception as exc:
                _render_realisation(f"Cannot stage wave: Z Direct unavailable ({exc}).")
                return

            task_payload = {}
            bridge = getattr(self.app, "agent_home_bridge", None)
            if bridge is not None:
                try:
                    task_payload = bridge.gated_build_tasks()
                except Exception:
                    task_payload = {}

            tasks_by_id = {
                str(item.get("task_id")): item
                for item in (task_payload.get("tasks") or [])
                if isinstance(item, dict) and item.get("task_id")
            }
            steps: List[Dict[str, Any]] = []
            for task_id in current_wave.get("task_refs") or []:
                task = tasks_by_id.get(str(task_id), {})
                steps.append(
                    {
                        "title": task.get("task_id") or str(task_id),
                        "owner": task.get("owner_floor") or "Neo",
                        "channel": task.get("owner_floor") or "Neo",
                        "what": task.get("goal") or f"Execute gated build task {task_id}.",
                        "artifacts": task.get("done_when") or [],
                    }
                )

            staged_at = datetime.now(timezone.utc).isoformat()
            workflow = {
                "id": f"neo_realisation_{wave_id}",
                "kind": "workflow_def",
                "title": f"Neo Realisation Wave - {current_wave.get('label') or wave_id}",
                "description": current_wave.get("goal") or "Supervised Neo realisation wave.",
                "steps": steps,
                "metadata": {
                    "wave_id": wave_id,
                    "staged_at": staged_at,
                    "owner": "Neo",
                    "training_loop_ids": current_wave.get("training_loop_ids") or [],
                    "handoff_artifacts": current_wave.get("handoff_artifacts") or [],
                    "approval_mode": payload.get("approval_mode"),
                },
                "tags": ["neo_realisation", "cognigrex", "buildout", "staged"],
            }

            try:
                envelope = z_direct.make_envelope(
                    kind="object",
                    channel="Z+3",
                    z_context="Z+2_Neo",
                    source="neo.workbench.stage_current_wave",
                    tags=["neo_realisation", "cognigrex", "buildout", "staged"],
                    payload=workflow,
                )
                z_direct.append_object("Z+3", envelope)
            except Exception as exc:
                _render_realisation(f"Failed to stage current wave: {exc}")
                return

            self.state.record_training_job(
                "supervised_realisation_wave",
                {
                    "wave_id": wave_id,
                    "task_count": len(steps),
                    "training_loop_ids": current_wave.get("training_loop_ids") or [],
                    "staged_at": staged_at,
                },
            )
            self.state.training_history.append(
                {
                    "wave_id": wave_id,
                    "training_loop_ids": current_wave.get("training_loop_ids") or [],
                    "task_refs": current_wave.get("task_refs") or [],
                    "staged_at": staged_at,
                    "mode": "supervised_buildout",
                }
            )
            self.state.last_training_metrics = {
                "task_count": float(len(steps)),
                "training_loop_count": float(len(current_wave.get("training_loop_ids") or [])),
            }
            self.state.add_to_context(
                "system",
                f"Staged Neo realisation wave {wave_id} with {len(steps)} tasks and "
                f"{len(current_wave.get('training_loop_ids') or [])} training loops.",
                session_id="neo_realisation",
            )

            try:
                host = self.app
                fn = getattr(host, "open_it_portal_z_direct", None)
                if callable(fn):
                    fn(channel="Z+3", peer="All", kind="workflow_def", tags="neo_realisation", search=wave_id)
            except Exception:
                pass

            _render_realisation(
                f"Staged {wave_id} to Trinity review with {len(steps)} gated tasks and "
                f"{len(current_wave.get('training_loop_ids') or [])} training loops."
            )

        controls = ttk.Frame(control)
        controls.pack(anchor="w", padx=10, pady=(0, 10))
        ttk.Button(controls, text="Refresh Realisation", command=_render_realisation).pack(side="left")
        ttk.Button(controls, text="Stage Current Wave", command=_stage_current_wave).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="Open Planner", command=lambda: self.select_tab("Planner")).pack(side="left", padx=(8, 0))
        _render_realisation()

        try:
            from lightspeed_runtime.desktop_adapters import mount_neo_achilles_console

            mount_neo_achilles_console(parent, self.app)
        except Exception:
            pass

    def _build_lab_assistant(self, parent: ttk.Frame) -> None:
        try:
            from core.ui.base_portal_glass import mount_smart_ops_strip  # type: ignore

            mount_smart_ops_strip(parent, app=self.app, floor_channel="Z+2", it_portal=self.compact, title="Neo Ops")
        except Exception:
            pass
        try:
            # Prefer an embeddable panel; fall back to opening a separate window.
            try:
                cls = _load_class("Z Axis/Z+2_Neo/components/neo_lab_assistant_glass.py", "NEOLabAssistantPanel")
                ui = cls(parent, app=self.app)
                ui.pack(fill="both", expand=True)
                return
            except Exception:
                cls = _load_class("Z Axis/Z+2_Neo/components/neo_lab_assistant_glass.py", "NEOLabAssistant")
                ui = cls(self.winfo_toplevel())
                try:
                    ttk.Label(parent, text="Opened NEO Lab Assistant in a separate window.", justify="left").pack(
                        fill="x", padx=12, pady=12
                    )
                except Exception:
                    pass
        except Exception as e:
            ttk.Label(parent, text=f"Neo Lab Assistant unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_code_assistant(self, parent: ttk.Frame) -> None:
        try:
            cls = _load_class("Z Axis/Z+2_Neo/components/ai_code_assistant.py", "AICodeAssistantGUI")
            ui = cls(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"AI Code Assistant unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_training(self, parent: ttk.Frame) -> None:
        try:
            cls = _load_class("Z Axis/Z+2_Neo/components/ai_training.py", "AITrainingGUI")
            ui = cls(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"AI Training unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_context(self, parent: ttk.Frame) -> None:
        try:
            cls = _load_class("Z Axis/Z+2_Neo/components/ai_context.py", "AIContextGUI")
            ui = cls(parent)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"AI Context unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_romer_sync(self, parent: ttk.Frame) -> None:
        try:
            cls = _load_class("Z Axis/Z+2_Neo/components/romer_sync_panel.py", "RomerSyncPanel")
            ui = cls(parent, app=self.app)
            ui.pack(fill="both", expand=True)
        except Exception as e:
            ttk.Label(parent, text=f"Romer Sync unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )

    def _build_model_config(self, parent: ttk.Frame) -> None:
        """Build model configuration tab"""
        ttk.Label(parent, text="AI Model Configuration", font=("Consolas", 14, "bold")).pack(pady=10)

        # Model status
        status_frame = ttk.LabelFrame(parent, text="Active Models")
        status_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ttk.Label(status_frame, text=f"Default Model: {self.state.default_model}").pack(anchor="w", padx=10, pady=5)
        ttk.Label(status_frame, text=f"Loaded Models: {len(self.state.active_models)}").pack(anchor="w", padx=10, pady=5)
        ttk.Label(status_frame, text=f"Training Jobs: {len(self.state.training_jobs)}").pack(anchor="w", padx=10, pady=5)
        ttk.Label(status_frame, text=f"Learning Enabled: {self.state.learning_enabled}").pack(anchor="w", padx=10, pady=5)

    def _build_planner(self, parent: ttk.Frame) -> None:
        """
        Cognigrex Planner (Neo-owned).

        Stages `workflow_def` plans into Trinity's Z Direct staging stream for operator review/commit.
        """
        try:
            from lightspeed_runtime.desktop_adapters import mount_neo_achilles_console

            if mount_neo_achilles_console(parent, self.app):
                return
        except Exception:
            pass

        try:
            from core.services import get_z_direct  # type: ignore

            z_direct = get_z_direct()
        except Exception as e:
            ttk.Label(parent, text=f"Z Direct unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        header = ttk.Frame(parent)
        header.pack(fill="x", padx=12, pady=(12, 8))
        ttk.Label(header, text="Cognigrex Planner (Stage-Only)", font=("Consolas", 14, "bold")).pack(side="left")

        body = ttk.Frame(parent)
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(2, weight=1)

        ttk.Label(
            body,
            text=(
                "Output: staged workflow_def objects in Trinity Z Direct (Z+3/objects.jsonl).\n"
                "Governance: stage-only; durable commits happen in Trinity IT Portal (Z Direct)."
            ),
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        focus_row = ttk.Frame(body)
        focus_row.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        focus_row.columnconfigure(1, weight=1)
        ttk.Label(focus_row, text="Focus:", width=10).grid(row=0, column=0, sticky="w")
        focus_var = tk.StringVar(value="V1R Bootstrap")
        ttk.Entry(focus_row, textvariable=focus_var, width=60).grid(row=0, column=1, sticky="ew", padx=(8, 8))

        out = tk.Text(body, wrap="word", font=("Consolas", 10))
        out.grid(row=2, column=0, sticky="nsew")
        out.insert(
            "1.0",
            "Use 'Stage Plan A/B/C' to propose plans into Trinity's review queue.\n\n"
            "Tip: In IT Portal -> Z Direct, filter Kind=workflow_def and Tags=plan.\n",
        )
        out.configure(state="disabled")

        def _slug(s: str) -> str:
            s = re.sub(r"[^a-zA-Z0-9]+", "_", (s or "").strip().lower()).strip("_")
            return s[:64] if s else "plan"

        def _make_plans(focus: str) -> List[Dict[str, Any]]:
            focus = (focus or "").strip() or "V1R Bootstrap"
            sid = _slug(focus)
            now = datetime.now(timezone.utc).isoformat()

            def step(title: str, *, owner: str, channel: str, what: str, artifacts: Optional[List[str]] = None) -> Dict[str, Any]:
                return {
                    "title": title,
                    "owner": owner,
                    "channel": channel,
                    "what": what,
                    "artifacts": artifacts or [],
                }

            common = {
                "kind": "workflow_def",
                "metadata": {"focus": focus, "staged_at": now, "owner": "Neo"},
                "tags": ["plan", "cognigrex"],
            }

            return [
                {
                    **common,
                    "id": f"cognigrex_plan_a_{sid}",
                    "title": f"Cognigrex Plan A - {focus}",
                    "description": "Primary plan (default path)",
                    "steps": [
                        step(
                            "Seed schemas",
                            owner="Trinity",
                            channel="Z+3",
                            what="Seed builtin schemas and tag v1r/bootstrap.",
                            artifacts=["IT Portal: Seed Schemas"],
                        ),
                        step(
                            "Stage V1R defs",
                            owner="Trinity",
                            channel="Z+3",
                            what="Stage baseline defs (append-only) and commit.",
                            artifacts=["N.py:stage_v1r_definitions"],
                        ),
                        step(
                            "Verify",
                            owner="Smith",
                            channel="Z-3",
                            what="Run verification suite and ensure governance loop stays green.",
                            artifacts=["verify_integration.py", "run_all_tests.py"],
                        ),
                    ],
                },
                {
                    **common,
                    "id": f"cognigrex_plan_b_{sid}",
                    "title": f"Cognigrex Plan B - {focus}",
                    "description": "Fallback plan (safe minimal lift)",
                    "steps": [
                        step(
                            "Stage minimal objects",
                            owner="Trinity",
                            channel="Z+3",
                            what="Stage only the minimum required defs; commit in small batches.",
                        ),
                        step(
                            "Verify",
                            owner="Smith",
                            channel="Z-3",
                            what="Verify after each batch to isolate regressions.",
                        ),
                    ],
                },
                {
                    **common,
                    "id": f"cognigrex_plan_c_{sid}",
                    "title": f"Cognigrex Plan C - {focus}",
                    "description": "Containment plan (staging-only exploration)",
                    "steps": [
                        step(
                            "Stage-only exploration",
                            owner="Neo",
                            channel="Z+2",
                            what="Generate proposals and keep them staged; no commits until stable.",
                        ),
                        step(
                            "Operator review",
                            owner="Trinity",
                            channel="Z+3",
                            what="Review staged items in Peer=All queue; reject/commit explicitly.",
                        ),
                    ],
                },
            ]

        def _set_out(text: str) -> None:
            try:
                out.configure(state="normal")
                out.delete("1.0", "end")
                out.insert("1.0", text or "")
                out.configure(state="disabled")
            except Exception:
                return

        def stage_plans() -> None:
            focus = focus_var.get()
            payloads = _make_plans(focus)
            staged = 0
            for payload in payloads:
                env = z_direct.make_envelope(
                    kind="object",
                    channel="Z+3",
                    z_context="Z+2_Neo",
                    source="neo.planner.stage_plans",
                    tags=["plan", "cognigrex", "staged"],
                    payload=payload,
                )
                z_direct.append_object("Z+3", env)
                staged += 1

            _set_out(
                "Staged workflow_def plans into Trinity review queue:\n"
                + "- " + "\n- ".join([p.get("id", "") for p in payloads])
                + "\n\nNext: IT Portal -> Z Direct -> Kind=workflow_def, Tags=plan -> Commit Selection (Batch).\n"
            )

            # Best-effort: open IT Portal review view when hosted under N.py.
            try:
                host = self.app
                fn = getattr(host, "open_it_portal_z_direct", None)
                if callable(fn):
                    fn(channel="Z+3", peer="All", kind="workflow_def", tags="plan", search="cognigrex_plan")
            except Exception:
                pass

        def preview_plans() -> None:
            focus = focus_var.get()
            payloads = _make_plans(focus)
            _set_out(json.dumps(payloads, indent=2, ensure_ascii=False))

        buttons = ttk.Frame(parent)
        buttons.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Button(buttons, text="Preview JSON", command=preview_plans).pack(side="left")
        ttk.Button(buttons, text="Stage Plan A/B/C", command=stage_plans).pack(side="left", padx=(8, 0))

    def _build_api_manager(self, parent: ttk.Frame) -> None:
        """API keys + connectors (Neo-owned; writes config, not durable registries)."""
        ttk.Label(parent, text="API Manager", font=("Consolas", 14, "bold")).pack(pady=(12, 8))
        ttk.Label(
            parent,
            text="Configure API keys/connectors (Ollama/OpenAI/etc). This does not commit to Z Direct registries.",
            justify="left",
        ).pack(padx=12, pady=(0, 10), anchor="w")

        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=12, pady=(0, 10))

        def _open_api_mgr():
            try:
                from core.api.api_manager import APIManager  # type: ignore

                mgr = APIManager()
                mgr.create_wizard_window(self.winfo_toplevel())
            except Exception as e:
                try:
                    messagebox.showerror("API Manager", f"Could not open API Manager:\n{e}", parent=self.winfo_toplevel())
                except Exception:
                    pass

        ttk.Button(btns, text="Open API Manager", command=_open_api_mgr).pack(side="left")

        # Show the current config path for operator context.
        info = tk.Text(parent, wrap="word", font=("Consolas", 10), height=8)
        info.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        try:
            cfg = (Path(__file__).resolve().parents[1] / "config" / "unified_config.json").resolve()
            info.insert("1.0", json.dumps({"config": str(cfg)}, indent=2))
        except Exception:
            info.insert("1.0", json.dumps({"config": "config/unified_config.json"}, indent=2))
        info.configure(state="disabled")

    def _build_z_direct_registry(self, parent: ttk.Frame) -> None:
        """
        Z Direct Registry (Neo): browse committed objects for interactability.

        Trinity is the approval gate for commits; this view reads the durable registry:
        `Z Axis/Z+2_Neo/Z Direct/objects.json`.
        """
        ttk.Label(parent, text="Z Direct Registry (Committed Objects)", font=("Consolas", 14, "bold")).pack(pady=10)

        try:
            from core.services import get_z_direct  # type: ignore
            z_direct = get_z_direct()
        except Exception as e:
            ttk.Label(parent, text=f"Z Direct unavailable:\n{e}", justify="left").pack(
                fill="both", expand=True, padx=16, pady=16
            )
            return

        outer = ttk.Frame(parent)
        outer.pack(fill="both", expand=True, padx=10, pady=10)
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=2)
        outer.rowconfigure(0, weight=1)

        left = ttk.Frame(outer)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right = ttk.Frame(outer)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        listbox = tk.Listbox(left, height=20, font=("Consolas", 10))
        listbox.pack(fill="both", expand=True)

        details = tk.Text(right, wrap="word", font=("Consolas", 10))
        details.pack(fill="both", expand=True)

        btns = ttk.Frame(parent)
        btns.pack(fill="x", padx=10, pady=(0, 10))

        state: Dict[str, Any] = {"items": []}

        def _render_details(item: Any) -> None:
            try:
                details.delete("1.0", "end")
            except Exception:
                pass
            try:
                details.insert("1.0", json.dumps(item, indent=2, ensure_ascii=True))
            except Exception:
                details.insert("1.0", str(item))

        def _load() -> None:
            try:
                items = z_direct.read_registry("Z+2", name="objects")
            except Exception:
                items = []
            state["items"] = items or []
            listbox.delete(0, "end")
            for it in state["items"]:
                if not isinstance(it, dict):
                    listbox.insert("end", str(it))
                    continue
                kind = it.get("kind") or "object"
                oid = it.get("id") or ""
                title = it.get("title") or it.get("name") or ""
                listbox.insert("end", f"{kind} {oid} {title}".strip())
            _render_details({"count": len(state["items"]), "channel": "Z+2"})

        def _open_selected() -> None:
            try:
                sel = listbox.curselection()
                if not sel:
                    messagebox.showwarning("Registry", "Select an item first.", parent=self.winfo_toplevel())
                    return
                it = state["items"][int(sel[0])]
                if not isinstance(it, dict):
                    messagebox.showwarning("Registry", "Invalid item selection.", parent=self.winfo_toplevel())
                    return
                p = it.get("path") or it.get("source_path")
                if not isinstance(p, str) or not p.strip():
                    messagebox.showwarning("Registry", "No file path on this object.", parent=self.winfo_toplevel())
                    return
                fp = Path(p)
                if not fp.exists():
                    messagebox.showwarning("Registry", f"File not found:\n{fp}", parent=self.winfo_toplevel())
                    return
                os.startfile(str(fp))  # type: ignore[attr-defined]
            except Exception as e:
                messagebox.showerror("Registry", f"Open failed:\n{e}", parent=self.winfo_toplevel())

        def _on_select(_evt=None) -> None:
            try:
                sel = listbox.curselection()
                if not sel:
                    return
                it = state["items"][int(sel[0])]
                _render_details(it)
            except Exception:
                return

        ttk.Button(btns, text="Refresh", command=_load).pack(side="left")
        ttk.Button(btns, text="Open File", command=_open_selected).pack(side="left", padx=(8, 0))

        listbox.bind("<<ListboxSelect>>", _on_select)
        _load()

    def _register_bento_widgets(self):
        """Register Neo widgets with Bento system"""
        try:
            import sys
            trinity_path = Path(__file__).parent / "Z+3_Trinity"
            if str(trinity_path) not in sys.path:
                sys.path.insert(0, str(trinity_path))

            from ui.universal_bento_system import register_floor_widgets, BentoWidget, BentoWidgetType

            widgets = [
                BentoWidget(
                    id="neo_lab_assistant",
                    title="Lab Assistant",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z+2_Neo",
                    callback=lambda w: self._open_lab_assistant(),
                    config={"icon": "AI", "description": "AI chat interface"}
                ),
                BentoWidget(
                    id="neo_code_assistant",
                    title="Code Assistant",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z+2_Neo",
                    callback=lambda w: self._open_code_assistant(),
                    config={"icon": "CODE", "description": "AI code generation"}
                ),
                BentoWidget(
                    id="neo_training",
                    title="Training",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z+2_Neo",
                    callback=lambda w: self._open_training(),
                    config={"icon": "TRAIN", "description": "Model training"}
                ),
                BentoWidget(
                    id="neo_model_selector",
                    title="Model Selector",
                    widget_type=BentoWidgetType.BUTTON,
                    floor="Z+2_Neo",
                    callback=lambda w: self._open_model_config(),
                    config={"icon": "MODEL", "description": "Switch AI models"}
                )
            ]

            register_floor_widgets("Z+2_Neo", widgets)
            print("[Neo] Registered Neo Bento widgets")
        except Exception as e:
            print(f"[Neo] Could not register Bento widgets: {e}")

    def _open_lab_assistant(self):
        """Open lab assistant tab"""
        print("[Neo] Opening Lab Assistant...")
        self.select_tab("Lab Assistant")

    def _open_code_assistant(self):
        """Open code assistant tab"""
        print("[Neo] Opening Code Assistant...")
        self.state.code_assistant_active = True
        self.select_tab("Code Assistant")

    def _open_training(self):
        """Open training tab"""
        print("[Neo] Opening Training...")
        self.select_tab("Training")

    def _open_model_config(self):
        """Open model configuration tab"""
        print("[Neo] Opening Model Config...")
        self.select_tab("Model Config")


def create_gui(*args, **kwargs):
    """
    N.py / IT Portal integration entry point.

    Supported call shapes:
    - create_gui(parent, colors)
    - create_gui(app, parent, colors)
    """
    app = None
    parent = None
    if args and isinstance(args[0], tk.Misc):
        parent = args[0]
    elif len(args) >= 2 and isinstance(args[1], tk.Misc):
        app = args[0]
        parent = args[1]
    if parent is None:
        return None
    compact = bool(kwargs.get("compact") or kwargs.get("it_portal"))
    return NeoUI(parent, app=app, compact=compact)


def build(*args, **kwargs):
    """Alias for legacy floor loaders."""
    return create_gui(*args, **kwargs)


# ---------------------------------------------------------------------------
# Floor boot hook (used by FloorLoader)
# ---------------------------------------------------------------------------

_NEO_INITIALIZED = False
NEO_RUNTIME: Dict[str, Any] = {}


def initialize(*, components: Optional[Dict[str, Any]] = None, dependencies: Optional[Dict[str, Any]] = None, **_kwargs) -> bool:
    """
    Initialize Neo floor runtime services.

    This runs during floor bootstrap (no UI) and ensures Neo's AI
    backend connections and integrations are active.

    Args:
        components: Pre-loaded component classes/instances
        dependencies: Shared services (db, event_bus, storage, logger)
        **_kwargs: Additional platform parameters

    Returns:
        bool: True if initialization succeeded, False otherwise
    """
    global _NEO_INITIALIZED, NEO_RUNTIME
    if _NEO_INITIALIZED:
        return True
    _NEO_INITIALIZED = True

    try:
        # Core services are provided by the Merovingian floor (`Z Axis/Z-4_Merovingian/core`).
        # The platform adds floor roots to `sys.path` during bootstrap, so `core.services` is
        # the stable import path (avoid invalid module names like `Z-4_Merovingian`).
        from core.services import get_db, get_event_bus, get_storage, get_logger  # type: ignore

        db = get_db()
        event_bus = get_event_bus()
        storage = get_storage()
        logger = get_logger()
    except Exception as e:
        print(f"[Neo] Failed to load core services: {e}")
        db = None
        event_bus = None
        storage = None
        logger = None

    NEO_RUNTIME["db"] = db
    NEO_RUNTIME["event_bus"] = event_bus
    NEO_RUNTIME["storage"] = storage
    NEO_RUNTIME["logger"] = logger

    # Initialize AI backend connection
    try:
        # Attempt to connect to Ollama or other AI backends
        AIOrchestratorComponent = _load_symbol(
            "Z Axis/Z+2_Neo/components/ai_orchestrator.py",
            "AIOrchestratorComponent",
        )
        orchestrator = AIOrchestratorComponent()
        NEO_RUNTIME["orchestrator"] = orchestrator

        if logger:
            logger.info("[Neo] AI orchestrator initialized")
    except Exception as e:
        NEO_RUNTIME["orchestrator_error"] = str(e)
        if logger:
            logger.warning(f"[Neo] AI orchestrator unavailable: {e}")

    # Initialize Cognigrex engine
    try:
        cognigrex_cls = None
        if isinstance(components, dict):
            cognigrex_cls = components.get("cognigrex_foundation")
        if cognigrex_cls is None:
            cognigrex_cls = _load_symbol(
                "Z Axis/Z+2_Neo/components/cognigrex_foundation.py",
                "CognigrexFoundation",
            )

        cognigrex = cognigrex_cls(db=db, event_bus=event_bus, logger=logger)
        NEO_RUNTIME["cognigrex"] = cognigrex

        if logger:
            logger.info("[Neo] Cognigrex engine initialized")
    except Exception as e:
        NEO_RUNTIME["cognigrex_error"] = str(e)
        if logger:
            logger.warning(f"[Neo] Cognigrex unavailable: {e}")

    # Subscribe to relevant events
    if event_bus:
        try:
            event_bus.subscribe("*.task.created", _on_task_created)
            event_bus.subscribe("trinity.ai.request", _on_ai_request)
            event_bus.subscribe("system.health.check", _on_health_check)
        except Exception as e:
            if logger:
                logger.warning(f"[Neo] Event subscription failed: {e}")

    # Publish floor ready event
    if event_bus:
        try:
            event_bus.publish("neo.floor.ready", {
                "floor": "Neo",
                "z_level": 2,
                "capabilities": ["ai_inference", "code_generation", "training", "context_management"],
                "ai_backend": "available" if "orchestrator" in NEO_RUNTIME else "unavailable"
            })
        except Exception as e:
            if logger:
                logger.warning(f"[Neo] Failed to publish ready event: {e}")

    if logger:
        logger.info("[Neo] Floor initialized successfully")

    return True


def _on_task_created(event):
    """Handle task created events"""
    logger = NEO_RUNTIME.get("logger")
    if logger:
        logger.debug(f"[Neo] Task created: {event.data.get('task_id')}")


def _on_ai_request(event):
    """Handle AI request events from other floors"""
    logger = NEO_RUNTIME.get("logger")
    orchestrator = NEO_RUNTIME.get("orchestrator")

    if logger:
        logger.info(f"[Neo] AI request received: {event.data.get('request_type')}")

    if orchestrator:
        # Process AI request
        try:
            response = orchestrator.process_request(event.data)
            event_bus = NEO_RUNTIME.get("event_bus")
            if event_bus:
                event_bus.publish("neo.ai.response", response)
        except Exception as e:
            if logger:
                logger.error(f"[Neo] AI request failed: {e}")


def _on_health_check(event):
    """Respond to health check events"""
    event_bus = NEO_RUNTIME.get("event_bus")
    if event_bus:
        try:
            event_bus.publish("neo.health.status", {
                "floor": "Neo",
                "status": "operational",
                "ai_backend": "connected" if NEO_RUNTIME.get("orchestrator") else "disconnected",
                "cognigrex": "active" if NEO_RUNTIME.get("cognigrex") else "inactive"
            })
        except Exception:
            pass


def main() -> int:
    root = tk.Tk()
    root.title("Neo (Z+2) - AI Integration")
    root.geometry("1200x800")
    NeoUI(root).pack(fill="both", expand=True)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
