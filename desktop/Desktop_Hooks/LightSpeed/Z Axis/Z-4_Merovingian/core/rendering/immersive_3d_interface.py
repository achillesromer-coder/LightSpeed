"""
Immersive 3D Interface (Lightweight)
LightSpeed Type I Civilization Platform

This module provides a minimal, dependency-free 3D viewer suitable for
Tkinter-based workflows. It is intentionally lightweight:

- Vector math + simple perspective projection
- Tkinter Canvas renderer
- Optional pan/rotate controls

It exists primarily to satisfy TheConstruct (Z0) floor expectations and to
provide a functional baseline 3D scene viewer without external 3D libraries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import math
import tkinter as tk
from tkinter import ttk


@dataclass
class Vector3:
    x: float
    y: float
    z: float

    def __add__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vector3") -> "Vector3":
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vector3":
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)


@dataclass
class Camera:
    position: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, -10.0))
    target: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))
    fov: float = 70.0  # degrees


@dataclass
class Triangle3D:
    vertices: Tuple[Vector3, Vector3, Vector3]
    color: str = "#00FFFF"
    outline: str = "#003355"
    width: int = 2
    alpha: float = 1.0


class Scene3D:
    """Simple scene container."""

    def __init__(self):
        self.triangles: List[Triangle3D] = []

    def add_triangle(self, tri: Triangle3D) -> None:
        self.triangles.append(tri)

    def clear(self) -> None:
        self.triangles.clear()


class ImmersiveViewer3D:
    """
    Lightweight 3D viewer using Tkinter Canvas.

    Controls:
    - Click+drag: rotate
    - Mouse wheel: zoom
    """

    def __init__(self, parent: tk.Widget, bg: str = "#000B1F"):
        self.parent = parent
        self.bg = bg
        self.camera = Camera()
        self.scene = Scene3D()

        self._yaw = 0.0
        self._pitch = 0.0
        self._zoom = 1.0

        self._dragging = False
        self._drag_start = (0, 0)

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.frame, bg=self.bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._build_controls()
        self._bind_controls()

        self.render()

    def _build_controls(self) -> None:
        bar = ttk.Frame(self.frame)
        bar.pack(side="bottom", fill="x")

        ttk.Button(bar, text="Reset View", command=self.reset_view).pack(side="left", padx=6, pady=6)

        self.info_var = tk.StringVar(value="3D Viewer Ready")
        ttk.Label(bar, textvariable=self.info_var).pack(side="right", padx=8)

    def _bind_controls(self) -> None:
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self.canvas.bind("<MouseWheel>", self._on_zoom)

    def reset_view(self) -> None:
        self._yaw = 0.0
        self._pitch = 0.0
        self._zoom = 1.0
        self.render()

    def set_scene(self, scene: Scene3D) -> None:
        self.scene = scene
        self.render()

    def add_triangle(
        self,
        v1: Vector3,
        v2: Vector3,
        v3: Vector3,
        color: str = "#00FFFF",
        outline: str = "#003355",
        width: int = 2
    ) -> None:
        self.scene.add_triangle(Triangle3D(vertices=(v1, v2, v3), color=color, outline=outline, width=width))
        self.render()

    def _rotate_point(self, p: Vector3) -> Vector3:
        # Yaw (around Y axis)
        yaw = self._yaw
        cy, sy = math.cos(yaw), math.sin(yaw)
        x1 = p.x * cy + p.z * sy
        z1 = -p.x * sy + p.z * cy

        # Pitch (around X axis)
        pitch = self._pitch
        cp, sp = math.cos(pitch), math.sin(pitch)
        y2 = p.y * cp - z1 * sp
        z2 = p.y * sp + z1 * cp

        return Vector3(x1, y2, z2)

    def _project(self, p: Vector3, w: int, h: int) -> Optional[Tuple[float, float]]:
        # Translate into camera space (very simple: assume camera at (0,0,-d) looking at origin).
        rel = p - self.camera.target
        rel = self._rotate_point(rel)

        # Apply zoom
        rel = rel * self._zoom

        # Perspective projection
        fov_rad = math.radians(max(10.0, min(160.0, self.camera.fov)))
        focal = (w / 2) / math.tan(fov_rad / 2)

        # Place camera on negative Z looking toward +Z; avoid divide-by-zero
        z = (rel.z + 10.0)
        if z <= 0.05:
            return None

        sx = (rel.x * focal) / z + w / 2
        sy = (-rel.y * focal) / z + h / 2
        return (sx, sy)

    def render(self) -> None:
        self.canvas.delete("all")

        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())

        # If not realized yet, schedule a render when size is available.
        if w <= 2 or h <= 2:
            self.canvas.after(50, self.render)
            return

        # Simple reference axes
        self._draw_axes(w, h)

        # Render triangles with naive painter's algorithm (by average z)
        tris = list(self.scene.triangles)
        tris.sort(key=lambda t: sum(v.z for v in t.vertices) / 3.0, reverse=True)

        for tri in tris:
            pts = []
            for v in tri.vertices:
                proj = self._project(v, w, h)
                if proj is None:
                    pts = []
                    break
                pts.extend([proj[0], proj[1]])
            if not pts:
                continue

            self.canvas.create_polygon(
                *pts,
                fill=tri.color,
                outline=tri.outline,
                width=tri.width
            )

        self.info_var.set(f"Yaw {int(math.degrees(self._yaw))}° | Pitch {int(math.degrees(self._pitch))}° | Zoom {int(self._zoom*100)}%")

    def _draw_axes(self, w: int, h: int) -> None:
        origin = self._project(Vector3(0, 0, 0), w, h)
        if origin is None:
            return

        def draw_axis(vec: Vector3, color: str):
            end = self._project(vec, w, h)
            if end is None:
                return
            self.canvas.create_line(origin[0], origin[1], end[0], end[1], fill=color, width=2)

        draw_axis(Vector3(3, 0, 0), "#FF0088")  # X
        draw_axis(Vector3(0, 3, 0), "#00FF88")  # Y
        draw_axis(Vector3(0, 0, 3), "#00DDFF")  # Z

    def _on_drag_start(self, event):
        self._dragging = True
        self._drag_start = (event.x, event.y)

    def _on_drag(self, event):
        if not self._dragging:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]

        self._yaw += dx * 0.01
        self._pitch += dy * 0.01
        self._pitch = max(-math.pi / 2 + 0.01, min(math.pi / 2 - 0.01, self._pitch))

        self._drag_start = (event.x, event.y)
        self.render()

    def _on_drag_end(self, _event):
        self._dragging = False

    def _on_zoom(self, event):
        if event.delta > 0:
            self._zoom *= 1.1
        else:
            self._zoom *= 0.9
        self._zoom = max(0.2, min(5.0, self._zoom))
        self.render()


def demo_scene() -> Scene3D:
    scene = Scene3D()
    scene.add_triangle(Triangle3D(vertices=(Vector3(-1, -1, 2), Vector3(1, -1, 2), Vector3(0, 1, 2)), color="#00FFFF"))
    scene.add_triangle(Triangle3D(vertices=(Vector3(-2, 0, 4), Vector3(-1, 2, 4), Vector3(-3, 2, 4)), color="#FF00FF"))
    return scene


if __name__ == "__main__":
    root = tk.Tk()
    root.title("LightSpeed ImmersiveViewer3D (Lightweight)")
    root.geometry("1200x800")

    viewer = ImmersiveViewer3D(root)
    viewer.set_scene(demo_scene())

    root.mainloop()
