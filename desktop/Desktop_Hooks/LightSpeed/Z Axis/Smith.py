#!/usr/bin/env python
"""
Smith (Z-3) - Job Router Floor

Thin runtime-backed facade for the active D-root shell.
Smith is treated as an operations/router surface, not a separate legacy app tree.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


def _resolve_app(parent: tk.Misc, app: Any | None = None) -> Any:
    if app is not None:
        return app
    if hasattr(parent, "open_z_floor"):
        return parent
    try:
        host = parent.winfo_toplevel()
    except Exception:
        return parent
    return host


def _status_line(app: Any) -> str:
    runtime = getattr(app, "canonical_runtime", None)
    lines = []
    if runtime is None:
        lines.append("Canonical runtime unavailable. Smith can only expose local shell actions.")
    else:
        lines.extend(
            [
                f"Runtime root: {runtime.root}",
                f"Exports root: {runtime.resolve_export_root()}",
                f"Romer package root: {runtime.resolve_package_output_dir('Romer')}",
            ]
        )

    bridge = getattr(app, "agent_home_bridge", None)
    if bridge is not None:
        try:
            summary = bridge.summary()
            queue = summary.get("consolidation_queue") or {}
            tasks = summary.get("gated_build_tasks") or {}
            staging = summary.get("input_staging_matrix") or {}
            build = summary.get("backend_frontend_build") or {}
            realization = summary.get("floor_environment_realization") or {}
            alignment = summary.get("floor_alignment") or {}
            smith_alignment = (alignment.get("floors") or {}).get("Smith") or {}
            smith_build = (build.get("by_floor") or {}).get("Smith") or {}
            smith_backend = smith_build.get("backend") or {}
            smith_frontend = smith_build.get("frontend") or {}
            smith_build_state = smith_build.get("build") or {}
            smith_realization = (realization.get("by_floor") or {}).get("Smith") or {}
            smith_ui = smith_realization.get("ui_realization") or {}
            lines.append(
                "Agent home queue: "
                f"{queue.get('total_items', 0)} items | "
                f"high={((queue.get('by_priority') or {}).get('high', 0))}"
            )
            lines.append(
                "Build alignment: "
                f"tasks={tasks.get('total_tasks', 0)} | "
                f"ready={tasks.get('ready_count', 0)} | "
                f"floors={alignment.get('total_floors', 0)}"
            )
            lines.append(
                "Population: "
                f"agent={smith_alignment.get('assigned_agent_id', 'unknown')} | "
                f"support={smith_alignment.get('de_sporte_support_resident_id', 'none')} | "
                f"components={smith_alignment.get('live_component_count', 0)}/"
                f"{smith_alignment.get('staging_component_count', 0)} live | "
                f"global_staging={staging.get('live_component_count', 0)}/"
                f"{staging.get('total_components', 0)}"
            )
            lines.append(
                "Backend/frontend: "
                f"Smith backend={'on' if smith_backend.get('enabled') else 'off'} | "
                f"frontend={'on' if smith_frontend.get('enabled') else 'off'} | "
                f"state={smith_build_state.get('state', 'unknown')} | "
                f"all_floors={build.get('backend_enabled_count', 0)}/{build.get('floor_count', 0)}"
            )
            lines.append(
                "Realization: "
                f"{smith_realization.get('environment_label', 'not exported')} | "
                f"model_confirmed={((smith_realization.get('model') or {}).get('confirmed_installed'))} | "
                f"adapts_to={', '.join(str(item) for item in (smith_ui.get('adapts_to') or [])[:3])}"
            )
        except Exception as exc:
            lines.append(f"Agent home export unavailable: {exc}")
    return "\n".join(lines)

def _populate(frame: ttk.Frame, app: Any) -> ttk.Frame:
    frame.columnconfigure(0, weight=1)

    ttk.Label(frame, text="Smith Function Router", font=("Consolas", 16, "bold")).grid(
        row=0, column=0, sticky="w", padx=16, pady=(16, 6)
    )
    ttk.Label(
        frame,
        text="Smith is hosted here as a compact routing and operations surface.",
        justify="left",
    ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

    status = tk.Text(frame, height=7, wrap="word", font=("Consolas", 9))
    status.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 12))
    status.insert("1.0", _status_line(app))

    next_row = 3
    try:
        from lightspeed_runtime.desktop_adapters import build_smith_queue_router_panel

        router_panel = build_smith_queue_router_panel(frame, app)
        if router_panel is not None:
            router_panel.grid(row=next_row, column=0, sticky="nsew", padx=16, pady=(0, 12))
            next_row += 1
    except Exception:
        pass

    actions = ttk.Frame(frame)
    actions.grid(row=next_row, column=0, sticky="w", padx=16, pady=(0, 16))

    ttk.Button(actions, text="Open Workflow Designer", command=getattr(app, "open_workflow_designer", lambda: None)).pack(
        side="left"
    )
    ttk.Button(actions, text="Open Architect", command=lambda: app.open_z_floor("Architect")).pack(
        side="left", padx=(8, 0)
    )
    ttk.Button(actions, text="Open Trinity", command=lambda: app.open_z_floor("Trinity")).pack(
        side="left", padx=(8, 0)
    )

    return frame


def build(app: Any, parent: tk.Misc):
    frame = ttk.Frame(parent)
    return _populate(frame, app)


class SmithUI(ttk.Frame):
    """Compatibility wrapper for legacy manifest-driven floor loading."""

    def __init__(self, parent: tk.Misc, app: Any | None = None, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        _populate(self, _resolve_app(parent, app))


def create_gui(parent: tk.Misc, _colors=None):
    return build(_resolve_app(parent), parent)
