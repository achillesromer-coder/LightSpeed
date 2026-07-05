from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable


UI_ROOT = Path(__file__).resolve().parent
LIGHTSPEED_ROOT = UI_ROOT.parents[2]
if str(UI_ROOT) not in sys.path:
    sys.path.insert(0, str(UI_ROOT))

from achilles_dock import AchillesDock
from floor_selector import FloorSelector
from shell_routes import (
    FLOOR_CHANNELS,
    SHELL_MODES,
    ShellRouter,
    ShellState,
    normalize_floor,
)


FLOOR_CAPABILITIES = {
    "Trinity": (
        "Interface contracts",
        "Operator interaction",
        "Human review gates",
    ),
    "Neo": (
        "Cross-floor orchestration",
        "Queue priority",
        "Local model assignment",
    ),
    "Architect": (
        "Projects and work breakdown",
        "Dependencies",
        "Publish planning",
    ),
    "The Construct": (
        "Desktop-bound simulation",
        "Digital twin visualization",
        "Scenario testing",
    ),
    "Morpheus": (
        "Knowledge comparison",
        "Provenance",
        "Contradiction review",
    ),
    "Oracle": (
        "Ingestion and knowns",
        "Evidence classification",
        "Dataset compaction",
    ),
    "Smith": (
        "Bounded automation",
        "Task execution",
        "Receipts and retries",
    ),
    "Merovingian": (
        "Diagnostics",
        "Telemetry",
        "Persistence maintenance",
    ),
}


class ITShell(tk.Frame):
    """Single embedded founder surface for LightSpeed Desktop."""

    def __init__(
        self,
        parent,
        *,
        host=None,
        user: dict | None = None,
        colors: dict | None = None,
        z_floors_available: dict | None = None,
        mode: str = "workspace",
        active_floor: str = "Trinity",
        workspace_context: str = "",
    ) -> None:
        self.host = host or parent
        self.user = user or {}
        self.colors = colors or {}
        self.z_floors_available = z_floors_available or {}
        self._bg = self.colors.get("bg_dark", "#031A2D")
        self._panel = self.colors.get("bg_panel", "#082B4B")
        self._panel_alt = self.colors.get("bg_blue", "#0D3D63")
        self._text = self.colors.get("text_white", "#F7F3E8")
        self._muted = self.colors.get("text_green", "#9AC8B8")
        self._accent = self.colors.get("accent_cyan", "#30D5C8")
        self._gold = "#C9A24A"
        self._danger = self.colors.get("error_red", "#D66A6A")
        super().__init__(parent, bg=self._bg)

        clearance = self._clearance()
        self.router = ShellRouter(clearance=clearance)
        initial = self.router.resolve(
            mode,
            active_floor=active_floor,
            workspace_context=workspace_context,
        )
        self.state = ShellState(**initial.snapshot())
        self.state.subscribe(self._state_changed)
        self.services: dict[str, Any] = {}
        self.company_context: dict[str, Any] = {}
        self.project_manager = None
        self._mode_buttons: dict[str, tk.Button] = {}

        self._build()
        self._state_changed(self.state.snapshot())

    def _clearance(self) -> int:
        for key in ("clearance", "clearance_level", "level"):
            value = self.user.get(key)
            try:
                if value is not None:
                    return int(value)
            except (TypeError, ValueError):
                continue
        mode = getattr(self.host, "user_mode", "")
        return 5 if mode == "it_founder" else 0

    def _build(self) -> None:
        header = tk.Frame(self, bg=self._panel, height=76)
        header.pack(fill="x")
        header.pack_propagate(False)
        home = tk.Button(
            header,
            text="LIGHTSPEED\nCOGNIGREX",
            command=lambda: self.navigate("workspace"),
            justify="left",
            bg=self._panel,
            fg=self._accent,
            activebackground=self._panel_alt,
            activeforeground=self._text,
            relief="flat",
            bd=0,
            font=("Garamond", 14, "bold"),
            cursor="hand2",
        )
        home.pack(side="left", padx=(18, 24), pady=8)

        modes = tk.Frame(header, bg=self._panel)
        modes.pack(side="left", fill="y")
        for mode in SHELL_MODES:
            button = tk.Button(
                modes,
                text=mode.upper(),
                command=lambda value=mode: self.navigate(value),
                bg=self._panel,
                fg=self._text,
                activebackground=self._accent,
                activeforeground=self._bg,
                relief="flat",
                bd=0,
                font=("Garamond", 9, "bold"),
                padx=10,
                cursor="hand2",
            )
            button.pack(side="left", fill="y", padx=1)
            self._mode_buttons[mode] = button

        self.context_title = tk.Label(
            header,
            text="",
            anchor="e",
            justify="right",
            bg=self._panel,
            fg=self._gold,
            font=("Garamond", 10, "bold"),
        )
        self.context_title.pack(side="right", padx=18)

        context_bar = tk.Frame(self, bg=self._panel_alt, height=42)
        context_bar.pack(fill="x")
        context_bar.pack_propagate(False)
        self.floor_selector = FloorSelector(
            context_bar,
            active_floor=self.state.active_floor,
            on_change=self._floor_changed,
            colors=self.colors,
        )
        self.floor_selector.pack(side="left", padx=18, pady=7)
        self.route_label = tk.Label(
            context_bar,
            text="",
            bg=self._panel_alt,
            fg=self._muted,
            font=("Garamond", 10),
        )
        self.route_label.pack(side="right", padx=18)

        panes = tk.PanedWindow(
            self,
            orient="horizontal",
            bg=self._panel,
            sashwidth=5,
            sashrelief="flat",
            showhandle=False,
        )
        panes.pack(fill="both", expand=True)
        self.content_host = tk.Frame(panes, bg=self._bg)
        self.achilles = AchillesDock(
            panes,
            colors=self.colors,
            context_provider=self.state.snapshot,
        )
        panes.add(self.content_host, minsize=640, stretch="always")
        panes.add(self.achilles, minsize=290, width=340, stretch="never")

        self.status = tk.Label(
            self,
            text="Local-first / governed / one active workspace",
            anchor="w",
            bg=self._panel,
            fg=self._muted,
            font=("Garamond", 9),
            padx=14,
        )
        self.status.pack(fill="x", ipady=4)

    def _state_changed(self, snapshot: dict[str, str]) -> None:
        mode = snapshot["mode"]
        floor = snapshot["active_floor"]
        workspace = snapshot["workspace_context"] or "general"
        self.floor_selector.set_floor(floor)
        self.context_title.configure(
            text=f"{floor.upper()}\n{workspace}"
        )
        self.route_label.configure(text=f"{mode} / {floor}")
        for name, button in self._mode_buttons.items():
            active = name == mode
            button.configure(
                bg=self._accent if active else self._panel,
                fg=self._bg if active else self._text,
            )
        self.achilles.update_context(snapshot)
        self._render_mode()

    def navigate(
        self,
        mode: str,
        *,
        active_floor: str | None = None,
        workspace_context: str | None = None,
    ) -> bool:
        try:
            route = self.router.resolve(
                mode,
                active_floor=active_floor or self.state.active_floor,
                workspace_context=(
                    self.state.workspace_context
                    if workspace_context is None
                    else workspace_context
                ),
            )
        except (PermissionError, ValueError) as exc:
            messagebox.showwarning("Route unavailable", str(exc), parent=self)
            return False
        self.state.transition(**route.snapshot())
        return True

    def _floor_changed(self, floor: str) -> None:
        mode = self.state.mode
        if mode == "workspace":
            mode = "operator"
        self.navigate(mode, active_floor=floor)

    def _clear_content(self) -> None:
        for child in self.content_host.winfo_children():
            child.destroy()

    def _title(self, title: str, subtitle: str) -> tk.Frame:
        frame = tk.Frame(self.content_host, bg=self._bg)
        frame.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(
            frame,
            text=title,
            anchor="w",
            bg=self._bg,
            fg=self._accent,
            font=("Garamond", 22, "bold"),
        ).pack(fill="x")
        tk.Label(
            frame,
            text=subtitle,
            anchor="w",
            justify="left",
            bg=self._bg,
            fg=self._text,
            font=("Garamond", 11),
            wraplength=880,
        ).pack(fill="x", pady=(4, 0))
        return frame

    def _card(
        self,
        parent,
        *,
        title: str,
        value: str,
        detail: str,
        command: Callable[[], None] | None = None,
    ) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=self._panel,
            highlightthickness=1,
            highlightbackground=self._panel_alt,
        )
        tk.Label(
            card,
            text=title.upper(),
            anchor="w",
            bg=self._panel,
            fg=self._gold,
            font=("Garamond", 10, "bold"),
        ).pack(fill="x", padx=14, pady=(12, 2))
        tk.Label(
            card,
            text=value,
            anchor="w",
            bg=self._panel,
            fg=self._accent,
            font=("Garamond", 18, "bold"),
        ).pack(fill="x", padx=14)
        tk.Label(
            card,
            text=detail,
            anchor="nw",
            justify="left",
            bg=self._panel,
            fg=self._text,
            font=("Garamond", 10),
            wraplength=360,
        ).pack(fill="both", expand=True, padx=14, pady=(4, 10))
        if command is not None:
            tk.Button(
                card,
                text="OPEN",
                command=command,
                bg=self._panel_alt,
                fg=self._text,
                activebackground=self._accent,
                activeforeground=self._bg,
                relief="flat",
                font=("Garamond", 9, "bold"),
            ).pack(anchor="e", padx=12, pady=(0, 12))
        return card

    def _render_mode(self) -> None:
        self._clear_content()
        renderer = getattr(self, f"_render_{self.state.mode}")
        renderer()

    def _workspace_name(self) -> str:
        current = getattr(self.host, "current_project", None)
        if isinstance(current, dict):
            return str(current.get("name") or current.get("id") or "General")
        return self.state.workspace_context or "General"

    def _runtime_counts(self) -> tuple[str, str]:
        runtime = getattr(self.host, "canonical_runtime", None)
        if runtime is None:
            return "not connected", "Canonical runtime is not available."
        try:
            telemetry = runtime.telemetry_summary()
            count = int(telemetry.get("span_count") or 0)
            return f"{count} signals", "SQLite-backed local operational telemetry."
        except Exception:
            return "connected", "Runtime connected; summary is awaiting refresh."

    def _render_workspace(self) -> None:
        workspace = self._workspace_name()
        self._title(
            "Workspace",
            "The default LightSpeed surface: current work, governed operations, evidence, and local AI.",
        )
        grid = tk.Frame(self.content_host, bg=self._bg)
        grid.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        for row in range(2):
            grid.grid_rowconfigure(row, weight=1)
        for column in range(2):
            grid.grid_columnconfigure(column, weight=1)
        runtime_value, runtime_detail = self._runtime_counts()
        cards = (
            (
                "Current work",
                workspace,
                f"Active floor: {self.state.active_floor}. One context is retained across all modes.",
                lambda: self.navigate("operator"),
            ),
            (
                "Operational state",
                runtime_value,
                runtime_detail,
                lambda: self.navigate("operator", active_floor="Merovingian"),
            ),
            (
                "Evidence review",
                "Morpheus",
                "Compare two bounded text artifacts without changing either source.",
                lambda: self.navigate("review", active_floor="Morpheus"),
            ),
            (
                "Release gate",
                "Architect",
                "Inspect public-safe readiness before any Web or GO publication.",
                lambda: self.navigate("publish", active_floor="Architect"),
            ),
        )
        for index, (title, value, detail, command) in enumerate(cards):
            self._card(
                grid,
                title=title,
                value=value,
                detail=detail,
                command=command,
            ).grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=7,
                pady=7,
            )

    def _render_operator(self) -> None:
        floor = self.state.active_floor
        capabilities = FLOOR_CAPABILITIES[floor]
        self._title(
            f"{floor} Smart Floor",
            "A single floor context is mounted only when requested; other floor interfaces remain dormant.",
        )
        panel = tk.Frame(self.content_host, bg=self._panel)
        panel.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        tk.Label(
            panel,
            text="FUNCTION LANE",
            anchor="w",
            bg=self._panel,
            fg=self._gold,
            font=("Garamond", 10, "bold"),
        ).pack(fill="x", padx=18, pady=(16, 8))
        for index, capability in enumerate(capabilities, start=1):
            tk.Label(
                panel,
                text=f"{index:02d}  {capability}",
                anchor="w",
                bg=self._panel,
                fg=self._text,
                font=("Garamond", 13),
            ).pack(fill="x", padx=18, pady=5)
        actions = tk.Frame(panel, bg=self._panel)
        actions.pack(fill="x", padx=18, pady=18)
        tk.Button(
            actions,
            text="ENTER FLOOR WORKSPACE",
            command=self._mount_active_floor,
            bg=self._accent,
            fg=self._bg,
            relief="flat",
            font=("Garamond", 10, "bold"),
            padx=16,
            pady=8,
        ).pack(side="left")
        tk.Button(
            actions,
            text="ASK ACHILLES",
            command=self.achilles.focus_input,
            bg=self._panel_alt,
            fg=self._text,
            relief="flat",
            font=("Garamond", 10, "bold"),
            padx=16,
            pady=8,
        ).pack(side="left", padx=8)

    def _mount_active_floor(self, subtab_title: str = "") -> bool:
        self._clear_content()
        floor = self.state.active_floor
        renderer = getattr(self.host, "_render_floor_embedded", None)
        if not callable(renderer):
            self._title(
                f"{floor} unavailable",
                "The host does not expose the bounded embedded floor renderer.",
            )
            return False
        try:
            renderer(self.content_host, floor)
            self.status.configure(text=f"{floor} mounted in the Trinity shell")
        except Exception as exc:
            self._title(f"{floor} failed to mount", str(exc))
            return False
        if subtab_title:
            self.after(20, lambda: self._select_floor_subtab(floor, subtab_title))
        return True

    def _select_floor_subtab(self, floor: str, subtab_title: str) -> None:
        try:
            widget = getattr(self.host, "_floor_ui_widgets", {}).get(floor)
            notebook = getattr(widget, "notebook", None)
            tabs = getattr(widget, "_tabs", {})
            target = tabs.get(subtab_title) if isinstance(tabs, dict) else None
            if notebook is not None and target is not None:
                notebook.select(target)
        except Exception:
            pass

    def _render_review(self) -> None:
        self._title(
            "Review",
            "Morpheus compares evidence while preserving source ownership and provenance.",
        )
        path = (
            LIGHTSPEED_ROOT
            / "Z Axis"
            / "Z-1_Morpheus"
            / "components"
            / "comparison_workspace.py"
        )
        try:
            spec = importlib.util.spec_from_file_location(
                "lightspeed_comparison_workspace",
                path,
            )
            if spec is None or spec.loader is None:
                raise RuntimeError("comparison workspace loader unavailable")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            widget = module.ComparisonWorkspace(
                self.content_host,
                colors=self.colors,
            )
            widget.pack(fill="both", expand=True)
        except Exception as exc:
            self._title("Review surface unavailable", str(exc))

    def _release_readiness(self) -> str:
        runtime = getattr(self.host, "canonical_runtime", None)
        if runtime is None:
            return "Runtime not connected"
        for method_name in (
            "closure_readiness",
            "release_readiness",
            "build_closure_readiness",
        ):
            method = getattr(runtime, method_name, None)
            if callable(method):
                try:
                    payload = method()
                    return json.dumps(payload, indent=2, default=str)[:5000]
                except Exception:
                    continue
        return "Runtime connected. Detailed closure report is not exported."

    def _render_publish(self) -> None:
        self._title(
            "Publish Gate",
            "Desktop remains execution authority. Web and GO receive sanitized projections only.",
        )
        panel = tk.Frame(self.content_host, bg=self._panel)
        panel.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        checklist = (
            "No secrets, tokens, local paths, databases, or model files",
            "Restricted topics remain local/private Drive",
            "Public queue contains opaque references only",
            "Build, test, and result packet must pass",
        )
        for item in checklist:
            tk.Label(
                panel,
                text=f"[ ]  {item}",
                anchor="w",
                bg=self._panel,
                fg=self._text,
                font=("Garamond", 11),
            ).pack(fill="x", padx=18, pady=5)
        readiness = tk.Text(
            panel,
            height=12,
            wrap="word",
            bg=self._bg,
            fg=self._text,
            relief="flat",
            font=("Consolas", 9),
        )
        readiness.pack(fill="both", expand=True, padx=18, pady=12)
        readiness.insert("1.0", self._release_readiness())
        readiness.configure(state="disabled")
        tk.Button(
            panel,
            text="EXPORT HUMAN LEDGER",
            command=self._export_ledger,
            bg=self._accent,
            fg=self._bg,
            relief="flat",
            font=("Garamond", 10, "bold"),
            padx=14,
            pady=7,
        ).pack(anchor="e", padx=18, pady=(0, 16))

    def _export_ledger(self) -> None:
        self.status.configure(text="Exporting operational workbook")

        def worker() -> None:
            try:
                from lightspeed_runtime.log_ledger_export import (
                    DEFAULT_OUTPUT,
                    export_ledgers,
                )

                result = export_ledgers(LIGHTSPEED_ROOT, DEFAULT_OUTPUT)
                message = f"Ledger updated: {result['output_path']}"
                self.after(0, lambda: self.status.configure(text=message))
            except Exception as exc:
                self.after(
                    0,
                    lambda: self.status.configure(
                        text=f"Ledger export failed: {exc}"
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()

    def _render_settings(self) -> None:
        self._title(
            "Settings",
            "The slim shell exposes operating policy; specialist settings remain owned by their floor.",
        )
        panel = tk.Frame(self.content_host, bg=self._panel)
        panel.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        values = (
            ("Launch profile", getattr(self.host, "launch_profile_name", "resident")),
            ("Runtime root", str(LIGHTSPEED_ROOT)),
            ("Persistence", "SQLite + governed weekly JSONL"),
            ("Ollama endpoint", "http://127.0.0.1:11434"),
            ("Background work", "bounded and floor-owned"),
            ("Heavy surfaces", "lazy / explicit only"),
        )
        for row, (label, value) in enumerate(values):
            tk.Label(
                panel,
                text=label,
                anchor="w",
                bg=self._panel,
                fg=self._gold,
                font=("Garamond", 10, "bold"),
                width=22,
            ).grid(row=row, column=0, sticky="nw", padx=18, pady=8)
            tk.Label(
                panel,
                text=value,
                anchor="w",
                justify="left",
                bg=self._panel,
                fg=self._text,
                font=("Garamond", 11),
                wraplength=600,
            ).grid(row=row, column=1, sticky="nw", padx=8, pady=8)
        panel.grid_columnconfigure(1, weight=1)

    def _render_holospace(self) -> None:
        self._title(
            "Holospace",
            "The Construct is Desktop-bound and starts only on explicit operator request.",
        )
        panel = tk.Frame(self.content_host, bg=self._panel)
        panel.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        tk.Label(
            panel,
            text="3D and simulation resources remain dormant while workspace, review, or publish modes are active.",
            justify="left",
            bg=self._panel,
            fg=self._text,
            font=("Garamond", 13),
            wraplength=700,
        ).pack(anchor="w", padx=20, pady=(22, 14))
        command = getattr(self.host, "launch_immersive_interface", None)
        tk.Button(
            panel,
            text="ENTER THE CONSTRUCT",
            command=command if callable(command) else lambda: None,
            state="normal" if callable(command) else "disabled",
            bg=self._accent,
            fg=self._bg,
            relief="flat",
            font=("Garamond", 11, "bold"),
            padx=18,
            pady=9,
        ).pack(anchor="w", padx=20)

    def set_services(self, **services) -> None:
        self.services.update(services)

    def set_company_context(
        self,
        *,
        company_id=None,
        company_name=None,
    ) -> None:
        self.company_context = {
            "company_id": company_id,
            "company_name": company_name,
        }

    def set_project_manager(self, project_manager) -> None:
        self.project_manager = project_manager

    def open_floor_tab(self, floor_name: str, subtab_title: str = "") -> bool:
        if not self.navigate("operator", active_floor=floor_name):
            return False
        if subtab_title:
            return self._mount_active_floor(subtab_title)
        return True

    def _open_z_direct_view(
        self,
        *,
        channel: str = "Z+3",
        peer: str = "All",
        kind: str | None = None,
        tags: str | None = None,
        search: str | None = None,
    ) -> None:
        floor = FLOOR_CHANNELS.get(str(channel), "Trinity")
        context = "Z Direct"
        if peer and peer != "All":
            context += f" / {peer}"
        self.navigate(
            "operator",
            active_floor=normalize_floor(floor),
            workspace_context=context,
        )

    def lift(self) -> None:
        self.tkraise()
