"""
Compatibility bridge for legacy `core.ui.spherical_ui` imports.

The full pre-bento spherical UI was retired during Z-axis cleanup. Active
callers now resolve through this thin adapter to the enhanced spherical glass
renderer while keeping the older workspace layout API stable.
"""

from __future__ import annotations

from typing import Optional

import tkinter as tk

from .enhanced_spherical_glass_ui import EnhancedSphericalGlassUI, GlassWidget3D


Widget3D = GlassWidget3D


class EquirectangularUI(EnhancedSphericalGlassUI):
    """Legacy workspace layout facade backed by `EnhancedSphericalGlassUI`."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        fov: float = 120.0,
        grid_width: int = 12,
        grid_height: int = 8,
        bg_color: Optional[str] = None,
        width: int = 900,
        height: int = 700,
    ):
        super().__init__(
            parent=parent,
            width=width,
            height=height,
            fov=fov,
            grid_width=grid_width,
            grid_height=grid_height,
        )
        if bg_color:
            try:
                self.canvas.configure(bg=bg_color)
            except Exception:
                pass

    @property
    def camera_angle(self) -> float:
        return self.camera_theta

    @camera_angle.setter
    def camera_angle(self, value: float) -> None:
        self.camera_theta = float(value)

    @property
    def camera_tilt(self) -> float:
        return self.camera_phi

    @camera_tilt.setter
    def camera_tilt(self, value: float) -> None:
        self.camera_phi = float(value)

    def add_widget_3d(self, widget_id: str, widget: tk.Widget, theta: float, phi: float, depth: float = 0.8) -> None:
        self.add_widget(widget_id=widget_id, widget=widget, theta=theta, phi=phi, depth=depth)

    def remove_widget_3d(self, widget_id: str) -> None:
        widget = self.widgets.pop(widget_id, None)
        if widget is not None:
            try:
                widget.widget.place_forget()
            except Exception:
                pass

    def create_grid(self) -> None:
        try:
            self.canvas.delete("grid")
        except Exception:
            pass
        self._draw_grid()

    def render(self) -> None:
        self._render()

    def pan_camera(self, delta_theta: float) -> None:
        self.rotate_camera(delta_theta, 0)

    def get_frame(self) -> tk.Widget:
        return self.canvas.master
