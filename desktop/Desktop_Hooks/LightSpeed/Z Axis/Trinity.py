#!/usr/bin/env python
"""
Trinity (Z+3) - Operator Surface

Thin runtime-backed facade for the active D-root shell.
Trinity is exposed as a compact operator surface that routes to live functions.
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


def _trinity_summary(app: Any) -> str:
    runtime = getattr(app, "canonical_runtime", None)
    lines = []
    if runtime is None:
        lines.append("Canonical runtime unavailable. Trinity is operating in shell-only mode.")
    else:
        catalog = runtime.source_catalog() if hasattr(runtime, "source_catalog") else []
        lines.extend(
            [
                f"Runtime root: {runtime.root}",
                f"Configured sources: {len(catalog)}",
                f"Resolved package root: {runtime.resolve_package_output_dir('Romer')}",
            ]
        )

    bridge = getattr(app, "agent_home_bridge", None)
    if bridge is not None:
        try:
            summary = bridge.summary()
            queue = summary.get("consolidation_queue") or {}
            floor_models = summary.get("floor_models") or {}
            roster = summary.get("presence_roster") or {}
            lanes = summary.get("workspace_lanes") or {}
            population = summary.get("agent_population") or {}
            staging = summary.get("input_staging_matrix") or {}
            build = summary.get("backend_frontend_build") or {}
            realization = summary.get("floor_environment_realization") or {}
            alignment = summary.get("floor_alignment") or {}
            de_sporte = summary.get("de_sporte_runtime") or {}
            trinity = (floor_models.get("by_floor") or {}).get("Trinity") or {}
            trinity_alignment = (alignment.get("floors") or {}).get("Trinity") or {}
            trinity_build = (build.get("by_floor") or {}).get("Trinity") or {}
            trinity_backend = trinity_build.get("backend") or {}
            trinity_frontend = trinity_build.get("frontend") or {}
            trinity_build_state = trinity_build.get("build") or {}
            trinity_realization = (realization.get("by_floor") or {}).get("Trinity") or {}
            trinity_ui = trinity_realization.get("ui_realization") or {}
            lines.append(
                "Agent home: "
                f"{summary.get('profile_id', 'unknown')} | "
                f"queue={queue.get('total_items', 0)} | "
                f"Trinity model={trinity.get('model', 'unknown')}"
            )
            lines.append(
                "Shell contract: "
                f"{lanes.get('interface_mode', 'unknown')} | "
                f"density={lanes.get('surface_density', 'unknown')} | "
                f"floors={alignment.get('total_floors', 0)}"
            )
            lines.append(
                "Presence roster: "
                f"LS={roster.get('lightspeed_logged_in_percent', 'n/a')}% | "
                f"DS idle={roster.get('de_sporte_idle_persistence_percent_of_remaining_window', 'n/a')}% | "
                f"DS active={roster.get('de_sporte_active_percent_of_remaining_window', 'n/a')}% | "
                f"overlap={roster.get('cascade_overlap_percent', 'n/a')}%"
            )
            lines.append(
                "Population: "
                f"agent={trinity_alignment.get('assigned_agent_id', 'unknown')} | "
                f"support={trinity_alignment.get('de_sporte_support_resident_id', 'none')} | "
                f"components={trinity_alignment.get('live_component_count', 0)}/"
                f"{trinity_alignment.get('staging_component_count', 0)} live"
            )
            lines.append(
                "De Sporte: "
                f"zone={de_sporte.get('current_zone', 'unknown')} | "
                f"residents={de_sporte.get('resident_count', 0)} | "
                f"support_exports={de_sporte.get('support_export_count', 0)}"
            )
            lines.append(
                "Contracts: "
                f"floors={population.get('floor_assignment_count', 0)} | "
                f"staging_live={staging.get('live_component_count', 0)}/"
                f"{staging.get('total_components', 0)}"
            )
            lines.append(
                "Backend/frontend: "
                f"all_floors={build.get('backend_enabled_count', 0)}/{build.get('floor_count', 0)} backend | "
                f"{build.get('frontend_enabled_count', 0)}/{build.get('floor_count', 0)} frontend | "
                f"Trinity backend={'on' if trinity_backend.get('enabled') else 'off'} | "
                f"frontend={'on' if trinity_frontend.get('enabled') else 'off'} | "
                f"state={trinity_build_state.get('state', 'unknown')}"
            )
            lines.append(
                "Realization: "
                f"{trinity_realization.get('environment_label', 'not exported')} | "
                f"model_confirmed={((trinity_realization.get('model') or {}).get('confirmed_installed'))} | "
                f"adapts_to={', '.join(str(item) for item in (trinity_ui.get('adapts_to') or [])[:3])}"
            )
        except Exception as exc:
            lines.append(f"Agent home export unavailable: {exc}")

    return "\n".join(lines)

def _populate(frame: ttk.Frame, app: Any) -> ttk.Frame:
    frame.columnconfigure(0, weight=1)

    ttk.Label(frame, text="Trinity Operator Surface", font=("Consolas", 16, "bold")).grid(
        row=0, column=0, sticky="w", padx=16, pady=(16, 6)
    )
    ttk.Label(
        frame,
        text="Compact host for settings, governance, spatial tools, and function routing.",
        justify="left",
    ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

    status = tk.Text(frame, height=7, wrap="word", font=("Consolas", 9))
    status.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 12))
    status.insert("1.0", _trinity_summary(app))

    next_row = 3
    try:
        from lightspeed_runtime.desktop_adapters import build_trinity_operator_home_panel

        operator_panel = build_trinity_operator_home_panel(frame, app)
        if operator_panel is not None:
            operator_panel.grid(row=next_row, column=0, sticky="nsew", padx=16, pady=(0, 12))
            next_row += 1
    except Exception:
        pass

    actions = ttk.Frame(frame)
    actions.grid(row=next_row, column=0, sticky="w", padx=16, pady=(0, 10))

    ttk.Button(actions, text="Settings Hub", command=getattr(app, "show_settings", lambda: None)).pack(side="left")
    ttk.Button(actions, text="Governance Hub", command=getattr(app, "open_it_portal", lambda: None)).pack(
        side="left", padx=(8, 0)
    )
    ttk.Button(actions, text="Workflow Designer", command=getattr(app, "open_workflow_designer", lambda: None)).pack(
        side="left", padx=(8, 0)
    )

    secondary = ttk.Frame(frame)
    secondary.grid(row=next_row + 1, column=0, sticky="w", padx=16, pady=(0, 16))
    ttk.Button(secondary, text="Workspace Layout", command=getattr(app, "open_workspace_layout", lambda: None)).pack(
        side="left"
    )
    ttk.Button(secondary, text="Immersive World", command=getattr(app, "open_3d_view", lambda: None)).pack(
        side="left", padx=(8, 0)
    )
    ttk.Button(secondary, text="Functions Hub", command=lambda: app.show_floors_hub(select_floor="Trinity")).pack(
        side="left", padx=(8, 0)
    )

    return frame


def build(app: Any, parent: tk.Misc):
    frame = ttk.Frame(parent)
    return _populate(frame, app)


class TrinityUI(ttk.Frame):
    """Compatibility wrapper for legacy manifest-driven floor loading."""

    def __init__(self, parent: tk.Misc, app: Any | None = None, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        _populate(self, _resolve_app(parent, app))


def create_gui(parent: tk.Misc, _colors=None):
    return build(_resolve_app(parent), parent)
