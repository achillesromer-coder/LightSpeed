"""
LIGHTSPEED 3D IMMERSIVE ENGINE V0.9.11+
Core 3D environment system with WASD navigation and Z-Axis tower exploration

Features:
- WASD movement + mouse camera control
- Windows 97 rolling hills ground floor (N.py)
- Z-Axis vertical tower navigation
- 1.5m radius curved UI overlay
- Double-tap Caps Lock to toggle UI
- Interactive 3D objects for all functions
- Flowchart tree quick-jump system
"""

# CODEX NOTE (2026-01-29):
# - Current platform direction: treat TheConstruct as a dynamic background/environment host for the Bento overlay (no WASD/room-scale dependency for core UX).
# - This module now supports an "ambient" embed mode where input bindings are disabled so N.py can render the world without capturing keyboard/mouse.
# - Canonical spec: `dataindex/02_MASTER_BUILD_SPEC_SHEET.md`.

import tkinter as tk
from tkinter import Canvas
import json
import math
import time
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import threading
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


class FloorType(Enum):
    """Z-Axis floor types"""
    N_EXTERNAL = "N External Ground"
    Z_MINUS_4 = "Z-4 Merovingian"
    Z_MINUS_3 = "Z-3 Smith"
    Z_MINUS_2 = "Z-2 Oracle"
    Z_MINUS_1 = "Z-1 Morpheus"
    Z_ZERO = "Z0 TheConstruct (Lobby)"
    Z_PLUS_1 = "Z+1 Architect"
    Z_PLUS_2 = "Z+2 Neo"
    Z_PLUS_3 = "Z+3 Trinity"


@dataclass
class Camera:
    """3D camera with position and rotation"""
    x: float = 0.0
    y: float = 5.0  # Eye height
    z: float = 0.0
    yaw: float = 0.0  # Horizontal rotation (degrees)
    pitch: float = 0.0  # Vertical rotation (degrees)
    fov: float = 90.0  # Field of view

    def get_forward_vector(self) -> Tuple[float, float]:
        """Get forward direction vector (x, z)"""
        yaw_rad = math.radians(self.yaw)
        return (math.sin(yaw_rad), math.cos(yaw_rad))

    def get_right_vector(self) -> Tuple[float, float]:
        """Get right direction vector (x, z)"""
        yaw_rad = math.radians(self.yaw + 90)
        return (math.sin(yaw_rad), math.cos(yaw_rad))


@dataclass
class Vector3D:
    """3D point in space"""
    x: float
    y: float
    z: float


@dataclass
class Interactive3DObject:
    """Interactive 3D object in the environment"""
    id: str
    name: str
    position: Vector3D
    size: Tuple[float, float, float]  # width, height, depth
    color: str
    object_type: str  # "widget", "door", "display", "sphere", "window"
    floor: FloorType
    callback: Optional[Callable] = None
    data: Optional[Dict] = None

    def _project_camera_space(self, camera: Camera) -> Optional[Tuple[float, float, float]]:
        """Project into camera space, returning (rx, dy, rz)."""
        dx = self.position.x - camera.x
        dy = self.position.y - camera.y
        dz = self.position.z - camera.z

        yaw_rad = math.radians(-camera.yaw)
        rx = dx * math.cos(yaw_rad) - dz * math.sin(yaw_rad)
        rz = dx * math.sin(yaw_rad) + dz * math.cos(yaw_rad)
        if rz <= 0:
            return None
        return (rx, dy, rz)

    def get_screen_position(self, camera: Camera, screen_width: int, screen_height: int) -> Optional[Tuple[int, int, float]]:
        """
        Project 3D position to 2D screen coordinates, returns (x, y, depth).

        Depth is camera-space Z (rz). For UI sizing/interaction we want depth rather than
        euclidean distance.
        """
        proj = self._project_camera_space(camera)
        if not proj:
            return None
        rx, dy, rz = proj

        fov_scale = 1.0 / math.tan(math.radians(camera.fov / 2))
        fx = screen_width * fov_scale / 2
        fy = screen_height * fov_scale / 2

        screen_x = int(screen_width / 2 + (rx / rz) * fx)
        screen_y = int(screen_height / 2 - ((dy - 1.0) / rz) * fy)  # -1.0 offset for eye height
        return (screen_x, screen_y, float(rz))

    def get_screen_rect(
        self,
        camera: Camera,
        screen_width: int,
        screen_height: int,
        *,
        min_px: int = 18,
    ) -> Optional[Tuple[int, int, int, int, float]]:
        """
        Return an approximate screen-space bounding rect for interaction/render sizing.

        Returns: (x1, y1, x2, y2, depth)
        """
        proj = self._project_camera_space(camera)
        if not proj:
            return None
        rx, dy, rz = proj

        fov_scale = 1.0 / math.tan(math.radians(camera.fov / 2))
        fx = screen_width * fov_scale / 2
        fy = screen_height * fov_scale / 2

        sx = int(screen_width / 2 + (rx / rz) * fx)
        sy = int(screen_height / 2 - ((dy - 1.0) / rz) * fy)

        half_w = max(int((float(self.size[0]) / 2.0) * fx / rz), int(min_px))
        half_h = max(int((float(self.size[1]) / 2.0) * fy / rz), int(min_px))
        return (sx - half_w, sy - half_h, sx + half_w, sy + half_h, float(rz))


class Windows97TerrainGenerator:
    """Generate Windows 97 rolling hills terrain"""

    @staticmethod
    def generate_hills(width: int = 100, depth: int = 100, hill_height: float = 3.0) -> List[Vector3D]:
        """Generate rolling hills terrain points"""
        points = []
        for x in range(-width//2, width//2, 2):
            for z in range(-depth//2, depth//2, 2):
                # Multiple sine waves for rolling hills effect
                y = (math.sin(x * 0.1) * 0.5 +
                     math.sin(z * 0.15) * 0.5 +
                     math.sin((x + z) * 0.08) * 0.3) * hill_height
                points.append(Vector3D(float(x), y, float(z)))
        return points

    @staticmethod
    def get_height_at(x: float, z: float, hill_height: float = 3.0) -> float:
        """Get terrain height at specific position"""
        return (math.sin(x * 0.1) * 0.5 +
                math.sin(z * 0.15) * 0.5 +
                math.sin((x + z) * 0.08) * 0.3) * hill_height


class CurvedUIOverlay:
    """1.5m radius curved UI overlay with Bento widgets (Caps Lock toggle)"""

    def __init__(self):
        self.radius = 1.5  # meters
        self.visible = False
        self.grid_cols = 4  # Bento grid columns
        self.grid_rows = 12  # Bento grid rows
        self.cell_width = 0.25
        self.cell_height = 0.30
        self.ui_panels: List[Dict] = []
        self.bento_widgets: List[Dict] = []
        # Camera-anchored menu behavior (set by the engine when toggled on).
        self.anchor: Optional[Dict[str, float]] = None
        self.front_arc_degrees: float = 150.0  # how wide the curved menu spans in front of the user
        self.ui_scale: float = 1.25  # scale panels/spacing for readability
        # Screen-space floor for hit-testing + readability (meters->pixels projection can get small on wide FOVs).
        self.ui_overlay_min_px: int = 60

        # Try to load Bento system
        self.bento_system = None
        try:
            # Import from Trinity (canonical owner of `ui.*`).
            # When launched via `N.py`, sys.path is already seeded, but keep this
            # robust for standalone launches of the Construct engine.
            import sys
            from pathlib import Path

            here = Path(__file__).resolve()
            lightspeed_root = None
            for cand in (here, *here.parents):
                try:
                    if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                        lightspeed_root = cand
                        break
                except Exception:
                    continue
            if lightspeed_root is None:
                lightspeed_root = here.parents[3]

            z_axis_root = Path(lightspeed_root) / "Z Axis"
            trinity_floor = z_axis_root / "Z+3_Trinity"
            for p in (Path(lightspeed_root), z_axis_root, trinity_floor):
                try:
                    if p.exists() and str(p) not in sys.path:
                        sys.path.insert(0, str(p))
                except Exception:
                    pass

            # Ensure `ui` resolves to Trinity. If `ui` was previously imported from
            # another location (common when launching via different entrypoints),
            # Python may keep a cached package/module that doesn't contain the
            # Bento system.
            ui_mod = sys.modules.get("ui")
            if ui_mod is not None:
                ui_file = (getattr(ui_mod, "__file__", "") or "").replace("\\", "/")
                ui_paths = [str(p).replace("\\", "/") for p in getattr(ui_mod, "__path__", [])] if hasattr(ui_mod, "__path__") else []
                ui_is_trinity = ("Z+3_Trinity" in ui_file) or any("Z+3_Trinity" in p for p in ui_paths)
                if not ui_is_trinity:
                    for key in list(sys.modules.keys()):
                        if key == "ui" or key.startswith("ui."):
                            sys.modules.pop(key, None)

            from ui.universal_bento_system import get_bento_system
            self.bento_system = get_bento_system()
            # Mirror Bento system geometry so the 3D overlay honors configured grid/scale.
            try:
                self.radius = float(getattr(self.bento_system, "radius", self.radius))
                self.grid_cols = int(getattr(self.bento_system, "grid_cols", self.grid_cols))
                self.grid_rows = int(getattr(self.bento_system, "grid_rows", self.grid_rows))
                self.cell_width = float(getattr(self.bento_system, "cell_width", self.cell_width))
                self.cell_height = float(getattr(self.bento_system, "cell_height", self.cell_height))
            except Exception:
                pass

            # Optional tuning knobs for the 3D overlay. Stored in unified_config alongside
            # the Bento geometry so operators can tune the menu feel without code edits.
            try:
                cfg_path = Path(lightspeed_root) / "config" / "unified_config.json"
                if cfg_path.exists():
                    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                    bento_cfg = cfg.get("bento", {}) or {}
                    self.front_arc_degrees = float(bento_cfg.get("front_arc_degrees", self.front_arc_degrees))
                    self.ui_scale = float(bento_cfg.get("ui_scale", self.ui_scale))
                    try:
                        v = int(bento_cfg.get("ui_overlay_min_px", self.ui_overlay_min_px))
                        self.ui_overlay_min_px = max(24, min(240, v))
                    except Exception:
                        pass
            except Exception:
                pass

            print("[3D Engine] Bento system loaded successfully")
        except Exception as e:
            print(f"[3D Engine] Bento system not available: {e}")

    def set_anchor(self, camera: Camera):
        """
        Anchor the overlay to the current camera pose.

        Without anchoring, UI panels are created near world origin and become distant/unreadable
        after the user moves. This mirrors open-world game "pause menu" behavior: the menu is
        attached to the player viewpoint.
        """
        try:
            self.anchor = {
                "x": float(camera.x),
                "y": float(camera.y),
                "z": float(camera.z),
                "yaw": float(camera.yaw),
            }
        except Exception:
            self.anchor = None

    def toggle(self):
        """Toggle UI visibility (double-tap Caps Lock)"""
        self.visible = not self.visible

    def _anchor_transform(self, local: Vector3D) -> Vector3D:
        """
        Transform a camera-local position into world space using the stored anchor.

        local.x: right, local.z: forward.
        """
        a = self.anchor or {"x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0}
        yaw = math.radians(float(a.get("yaw", 0.0)))
        lx = float(local.x)
        lz = float(local.z)
        wx = float(a.get("x", 0.0)) + (lx * math.cos(yaw) + lz * math.sin(yaw))
        wz = float(a.get("z", 0.0)) + (-lx * math.sin(yaw) + lz * math.cos(yaw))
        wy = float(a.get("y", 0.0)) + float(local.y)
        return Vector3D(wx, wy, wz)

    def create_bento_grid(self) -> List[Interactive3DObject]:
        """Create curved Bento grid UI at 1.5m radius with actual widgets"""
        panels = []
        arc_rad = math.radians(max(30.0, float(self.front_arc_degrees)))

        if self.bento_system:
            # Get widgets from Bento system (scope-aware: all/active/fav/recent).
            try:
                scope = "all"
                try:
                    prefs = getattr(self.bento_system, "user_prefs", None)
                    if prefs is not None and hasattr(prefs, "get_preference"):
                        raw = prefs.get_preference("bento.scope", "all")
                        if isinstance(raw, str) and raw.strip():
                            scope = raw.strip().lower()
                except Exception:
                    scope = "all"

                if scope == "active":
                    active_floor = getattr(self.bento_system, "active_floor", None)
                    if active_floor and hasattr(self.bento_system, "get_widgets_for_floor"):
                        all_widgets = self.bento_system.get_widgets_for_floor(active_floor)
                    else:
                        all_widgets = self.bento_system.get_all_widgets()
                else:
                    all_widgets = self.bento_system.get_all_widgets()

                if scope == "fav":
                    favs = set()
                    try:
                        favs = set(self.bento_system.get_favorite_widget_ids() or [])
                    except Exception:
                        favs = set()
                    if favs:
                        all_widgets = [w for w in all_widgets if getattr(w, "id", None) in favs]
                    else:
                        all_widgets = []
                elif scope == "recent":
                    ids = []
                    try:
                        ids = list(self.bento_system.get_recent_widget_ids(limit=80) or [])
                    except Exception:
                        ids = []
                    by_id = {}
                    for w in all_widgets:
                        try:
                            wid = getattr(w, "id", None)
                            if isinstance(wid, str) and wid:
                                by_id[wid] = w
                        except Exception:
                            continue
                    ordered = []
                    for wid in ids:
                        if wid in by_id:
                            ordered.append(by_id[wid])
                    all_widgets = ordered
            except Exception:
                all_widgets = self.bento_system.get_all_widgets()

            # Safety cap: overlay is a pause-menu surface, not an infinite scroll list.
            try:
                max_items = int(self.grid_cols) * int(self.grid_rows)
            except Exception:
                max_items = 48
            all_widgets = list(all_widgets)[: max(1, max_items)]

            # Optional packed layout (supports widget spans when available).
            layout = None
            try:
                if hasattr(self.bento_system, "layout_for_widgets"):
                    layout = self.bento_system.layout_for_widgets(all_widgets)
            except Exception:
                layout = None

            for idx, widget in enumerate(all_widgets):
                # Calculate camera-local 3D position for a front-facing "menu" arc.
                entry = None
                try:
                    wid = getattr(widget, "id", "")
                    if layout and isinstance(wid, str) and wid:
                        entry = layout.get(wid)
                except Exception:
                    entry = None
                if not isinstance(entry, dict):
                    entry = {}

                try:
                    col = int(entry.get("col", idx % max(1, self.grid_cols)))
                    row = int(entry.get("row", idx // max(1, self.grid_cols)))
                    sc = int(entry.get("span_cols", 1))
                    sr = int(entry.get("span_rows", 1))
                except Exception:
                    col, row, sc, sr = 0, 0, 1, 1

                cols = max(1, int(self.grid_cols))
                col = max(0, min(col, cols - 1))
                sc = max(1, min(sc, cols))

                # Map columns to an arc in front of the user (open-world pause menu pattern).
                norm = ((col + (sc / 2.0)) / float(cols)) - 0.5  # -0.5..+0.5
                ang = norm * arc_rad
                local_x = math.sin(ang) * float(self.radius)
                local_z = math.cos(ang) * float(self.radius)

                # Vertical stacking relative to eye level (0 = eye height).
                ch = float(self.cell_height) * float(self.ui_scale)
                y_off = -(float(row) * ch) - ((max(1, sr) - 1) * ch / 2.0)

                # Panel size in meters; scale for readability.
                try:
                    if hasattr(self.bento_system, "get_widget_position_3d_for"):
                        pos_3d = self.bento_system.get_widget_position_3d_for(widget, idx, layout=layout)
                    else:
                        pos_3d = self.bento_system.get_widget_position_3d(idx)
                except Exception:
                    pos_3d = {}

                width_m = float(pos_3d.get("width_m", self.cell_width)) * float(self.ui_scale)
                height_m = float(pos_3d.get("height_m", self.cell_height)) * float(self.ui_scale)

                # Route clicks through Bento so callbacks receive the widget object.
                cb = None
                try:
                    wid = getattr(widget, "id", "")
                    if wid:
                        cb = lambda _wid=wid: self.bento_system.handle_widget_click(_wid)
                except Exception:
                    cb = None

                pos_world = self._anchor_transform(Vector3D(local_x, y_off, local_z)) if self.anchor else Vector3D(local_x, (1.5 + y_off), local_z)

                # Create interactive 3D object for widget
                panel = Interactive3DObject(
                    id=f"bento_{widget.id}",
                    name=widget.title,
                    position=pos_world,
                    size=(width_m, height_m, 0.05),
                    color="#1a2332",
                    object_type="window",
                    floor=FloorType.N_EXTERNAL,
                    callback=cb,
                    data={
                        'curved': True,
                        'bento_widget': True,
                        'widget_id': widget.id,
                        'widget_type': widget.widget_type.value,
                        'floor': widget.floor,
                        # ASCII fallback to avoid Windows mojibake for UTF-8 bullets/emojis.
                        'icon': widget.config.get('icon', '?'),
                        'callback': widget.callback
                    }
                )
                panels.append(panel)

            print(f"[3D Engine] Created {len(panels)} Bento widgets")
        else:
            # Fallback: create basic panels
            num_panels = min(self.grid_cols * 3, 12)  # First 3 rows
            for i in range(num_panels):
                row = i // self.grid_cols
                col = i % self.grid_cols

                cols = max(1, int(self.grid_cols))
                norm = ((col + 0.5) / float(cols)) - 0.5
                ang = norm * arc_rad
                x = math.sin(ang) * self.radius
                z = math.cos(ang) * self.radius
                y = -(row * (self.cell_height * self.ui_scale))
                pos = self._anchor_transform(Vector3D(x, y, z)) if self.anchor else Vector3D(x, 1.5 + y, z)

                panel = Interactive3DObject(
                    id=f"ui_panel_{i}",
                    name=f"Panel {i+1}",
                    position=pos,
                    size=(self.cell_width * self.ui_scale, self.cell_height * self.ui_scale, 0.05),
                    color="#1a2332",
                    object_type="window",
                    floor=FloorType.N_EXTERNAL,
                    data={'index': i, 'curved': True}
                )
                panels.append(panel)

        return panels


class FloorNavigationSystem:
    """Navigate between Z-Axis floors"""

    def __init__(self):
        # N.py is the external ground floor; Z0 (TheConstruct) is the lobby aligned at ground height.
        # Floors stack above and below Z0 in equal spacing for intuitive navigation.
        self.current_floor = FloorType.N_EXTERNAL
        step = 10.0
        self.floor_heights = {
            FloorType.N_EXTERNAL: 0.0,
            FloorType.Z_ZERO: 0.0,
            FloorType.Z_PLUS_1: step,
            FloorType.Z_PLUS_2: step * 2,
            FloorType.Z_PLUS_3: step * 3,
            FloorType.Z_MINUS_1: -step,
            FloorType.Z_MINUS_2: -step * 2,
            FloorType.Z_MINUS_3: -step * 3,
            FloorType.Z_MINUS_4: -step * 4,
        }

    def get_floor_y_position(self, floor: FloorType) -> float:
        """Get Y coordinate for floor"""
        return self.floor_heights.get(floor, 0.0)

    def transition_to_floor(self, camera: Camera, target_floor: FloorType, duration: float = 1.0):
        """Smoothly transition camera to target floor"""
        target_y = self.get_floor_y_position(target_floor) + 5.0  # +5 for eye height
        self.current_floor = target_floor
        return target_y

    def create_floor_portals(self) -> List[Interactive3DObject]:
        """Create elevator/stairway portals between floors"""
        portals = []

        for floor in FloorType:
            if floor == FloorType.N_EXTERNAL:
                continue  # External ground floor has entrance

            y = self.floor_heights[floor]

            # Elevator door
            elevator = Interactive3DObject(
                id=f"elevator_{floor.name}",
                name=f"Elevator to {floor.value}",
                position=Vector3D(0.0, y + 2.0, 0.0),
                size=(2.0, 3.0, 0.5),
                color="#2a3f5f",
                object_type="door",
                floor=floor,
                data={'target_floor': floor}
            )
            portals.append(elevator)

        return portals


class FlowchartTreeQuickJump:
    """3D flowchart tree for quick navigation"""

    def __init__(self):
        self.nodes: List[Interactive3DObject] = []
        self.visible = False

    def create_project_tree(self) -> List[Interactive3DObject]:
        """Create 3D hierarchical project tree"""
        nodes = []

        # Root node (center)
        root = Interactive3DObject(
            id="root_node",
            name="LightSpeed Platform",
            position=Vector3D(0.0, 10.0, 0.0),
            size=(2.0, 2.0, 2.0),
            color="#ff00ff",
            object_type="sphere",
            floor=FloorType.Z_ZERO,
            data={'type': 'root', 'children': []}
        )
        nodes.append(root)

        # Child nodes in circular arrangement
        floor_types = [f for f in FloorType if f != FloorType.N_EXTERNAL]
        radius = 8.0
        for i, floor in enumerate(floor_types):
            angle = math.radians(i * (360 / len(floor_types)))
            x = math.sin(angle) * radius
            z = math.cos(angle) * radius

            node = Interactive3DObject(
                id=f"node_{floor.name}",
                name=floor.value,
                position=Vector3D(x, 10.0, z),
                size=(1.5, 1.5, 1.5),
                color="#00ffff",
                object_type="sphere",
                floor=FloorType.Z_ZERO,
                data={'type': 'floor', 'target_floor': floor}
            )
            nodes.append(node)

        return nodes


class Immersive3DEngine:
    """Main 3D engine for LightSpeed immersive environment"""

    def __init__(
        self,
        width: int = 1200,
        height: int = 800,
        on_action: Optional[Callable[[Interactive3DObject], None]] = None,
        event_bus: Optional[object] = None,
        physics: Optional[Dict[str, float]] = None,
        capture_mouse: bool = True,
    ):
        self.width = width
        self.height = height
        self.camera = Camera()
        self.objects: List[Interactive3DObject] = []
        self.on_action = on_action
        self.event_bus = event_bus

        # Systems
        self.terrain = Windows97TerrainGenerator()
        self.ui_overlay = CurvedUIOverlay()
        self.floor_nav = FloorNavigationSystem()
        self.flowchart = FlowchartTreeQuickJump()

        # Input state
        self.keys_pressed = set()
        self.mouse_x = width // 2
        self.mouse_y = height // 2
        self.capture_mouse_default = bool(capture_mouse)
        self.mouse_captured = bool(capture_mouse)
        self.caps_lock_taps = []
        self._last_space_press_ts = 0.0
        self._bound_canvas: Optional[Canvas] = None

        # Pause state (used when curved UI overlay is visible).
        self.paused = False
        # Hover state (used when overlay/flowchart is visible and the mouse is released).
        self._hovered_object_id: Optional[str] = None

        # Movement settings (Minecraft-style with momentum)
        self.move_speed = 0.22  # units per frame (walk) - increased for Minecraft feel
        self.run_speed_multiplier = 2.5  # Sprinting is faster
        self.mouse_sensitivity = 0.15
        self.running = False

        # Momentum system (Minecraft-like smooth movement)
        self.velocity_x = 0.0
        self.velocity_z = 0.0
        self.acceleration = 0.08  # How quickly we reach max speed
        self.deceleration = 0.12  # How quickly we slow down (higher = snappier)
        self.max_velocity = self.move_speed

        # Simple physics (Minecraft-style jump/double-jump)
        physics = physics or {}
        self.gravity = float(physics.get("gravity_m_s2", 20.0))
        self.jump_strength = float(physics.get("jump_strength", 7.0))
        self.double_jump_strength = float(physics.get("double_jump_strength", 6.0))
        self._vy = 0.0
        self._jump_count = 0
        self._grounded = True

        # Initialize environment
        self._initialize_environment()
        try:
            z0_y = self.floor_nav.get_floor_y_position(FloorType.Z_ZERO)
            self.camera.y = z0_y + 5.0
            self.camera.z = -18.0
            self.camera.yaw = 0.0
            self.camera.pitch = 0.0
        except Exception:
            pass

    def _publish(self, event_type: str, data: Dict[str, Any]):
        bus = getattr(self, "event_bus", None)
        if bus is None:
            return
        try:
            publish = getattr(bus, "publish", None)
            if callable(publish):
                publish(event_type, data)
        except Exception:
            return

    def refresh_ui_overlay_widgets(self):
        """
        Rebuild curved UI overlay widget panels from the Bento registry.

        Used when:
        - the active floor changes
        - widgets are created/updated dynamically
        """
        try:
            # Remove existing overlay window panels (both Bento-backed and fallback).
            self.objects = [
                o for o in self.objects
                if not (
                    o.object_type == "window"
                    and isinstance(getattr(o, "data", None), dict)
                    and o.data.get("curved")
                )
            ]
        except Exception:
            pass

        # Sync active floor into Bento so we only show floor-local widgets when desired.
        try:
            if self.ui_overlay and getattr(self.ui_overlay, "bento_system", None):
                floor_id_map = {
                    FloorType.Z_MINUS_4: "Z-4_Merovingian",
                    FloorType.Z_MINUS_3: "Z-3_Smith",
                    FloorType.Z_MINUS_2: "Z-2_Oracle",
                    FloorType.Z_MINUS_1: "Z-1_Morpheus",
                    FloorType.Z_ZERO: "Z0_TheConstruct",
                    FloorType.Z_PLUS_1: "Z+1_Architect",
                    FloorType.Z_PLUS_2: "Z+2_Neo",
                    FloorType.Z_PLUS_3: "Z+3_Trinity",
                    FloorType.N_EXTERNAL: "Z0_TheConstruct",
                }
                active = floor_id_map.get(self.floor_nav.current_floor, "Z0_TheConstruct")
                setter = getattr(self.ui_overlay.bento_system, "set_active_floor", None)
                if callable(setter):
                    setter(active)
        except Exception:
            pass

        # Anchor the overlay to the current camera pose so it behaves like a pause menu
        # instead of a distant in-world object cluster near origin.
        try:
            setter = getattr(self.ui_overlay, "set_anchor", None)
            if callable(setter):
                setter(self.camera)
        except Exception:
            pass

        try:
            self.objects.extend(self.ui_overlay.create_bento_grid())
        except Exception:
            pass

    def _load_symbol_from_file(self, rel_path: str, symbol: str):
        root = Path(__file__).resolve()
        for cand in (root, *root.parents):
            if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                root = cand
                break
        path = (Path(root) / rel_path).resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        mod_name = f"lightspeed_dynamic_{path.stem}_{abs(hash(str(path)))%1_000_000}"
        spec = spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {path}")
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, symbol):
            raise AttributeError(f"{symbol} not found in {path}")
        return getattr(mod, symbol)

    def _initialize_environment(self):
        """Initialize all 3D objects in environment"""
        print("[3D Engine] Initializing immersive environment...")

        z0_y = self.floor_nav.get_floor_y_position(FloorType.Z_ZERO)
        trinity_y = self.floor_nav.get_floor_y_position(FloorType.Z_PLUS_3)

        # Add Achilles AI sphere at center of Z0
        achilles_sphere = Interactive3DObject(
            id="achilles_sphere",
            name="Achilles AI",
            position=Vector3D(0.0, z0_y + 5.0, 0.0),
            size=(2.0, 2.0, 2.0),
            color="#ff1493",  # Deep pink
            object_type="sphere",
            floor=FloorType.Z_ZERO,
            data={'pulsing': True, 'ai_active': True}
        )
        self.objects.append(achilles_sphere)

        # Add a visible tower stack (simple slabs) so the Z-axis is obvious in the scene.
        for floor in (
            FloorType.Z_MINUS_4,
            FloorType.Z_MINUS_3,
            FloorType.Z_MINUS_2,
            FloorType.Z_MINUS_1,
            FloorType.Z_ZERO,
            FloorType.Z_PLUS_1,
            FloorType.Z_PLUS_2,
            FloorType.Z_PLUS_3,
        ):
            y = self.floor_nav.get_floor_y_position(floor)
            slab = Interactive3DObject(
                id=f"tower_slab_{floor.name}",
                name=f"Tower Slab {floor.value}",
                position=Vector3D(0.0, y, 0.0),
                size=(8.0, 0.8, 8.0),
                color="#1a2332" if floor != FloorType.Z_ZERO else "#0ea5e9",
                object_type="platform",
                floor=floor,
                data={"type": "tower_slab", "floor": floor.value},
            )
            self.objects.append(slab)

        # Add floor portals
        self.objects.extend(self.floor_nav.create_floor_portals())

        # Add UI overlay panels (hidden by default)
        self.objects.extend(self.ui_overlay.create_bento_grid())

        # Add flowchart tree nodes (hidden by default)
        self.objects.extend(self.flowchart.create_project_tree())

        # Add built-in 3D widgets for all floors
        try:
            create_builtin_3d_widgets = self._load_symbol_from_file(
                "Z Axis/Z0_TheConstruct/ui/floor_widgets_3d.py",
                "create_builtin_3d_widgets",
            )
            builtin_widgets = create_builtin_3d_widgets()
            self.objects.extend(builtin_widgets)
            print(f"[3D Engine] Added {len(builtin_widgets)} built-in widgets")
        except Exception as e:
            print(f"[3D Engine] Floor widgets 3D not available: {e}")

        physics_sim_widget = Interactive3DObject(
            id="raphael_physics_simulations",
            name="Raphael Physics Simulations",
            position=Vector3D(-10.0, z0_y + 5.0, 10.0),
            size=(3.5, 2.5, 0.5),
            color="#00ff00",
            object_type="window",
            floor=FloorType.Z_ZERO,
            data={'type': 'physics_simulation_launcher'}
        )
        self.objects.append(physics_sim_widget)

        bento_ui_widget = Interactive3DObject(
            id="immersive_bento_ui",
            name="Immersive Bento UI - Variable Testing",
            position=Vector3D(10.0, z0_y + 5.0, 10.0),
            size=(3.5, 2.5, 0.5),
            color="#ff00ff",
            object_type="window",
            floor=FloorType.Z_ZERO,
            data={'type': 'bento_ui_launcher'}
        )
        self.objects.append(bento_ui_widget)

        neo_library_widget = Interactive3DObject(
            id="neo_function_library",
            name="Neo AI Function Library",
            position=Vector3D(0.0, trinity_y + 5.0, 8.0),
            size=(3.0, 2.5, 0.5),
            color="#00ff88",
            object_type="window",
            floor=FloorType.Z_PLUS_3,
            data={'type': 'neo_library_launcher'}
        )
        self.objects.append(neo_library_widget)

        print(f"[3D Engine] Initialized with {len(self.objects)} 3D objects")

    def handle_key_press(self, event):
        """Handle key press events"""
        key = event.keysym.lower()

        # Open-world pause-menu behavior: ESC toggles the overlay on/off.
        if key == "escape":
            try:
                self._set_overlay_visible(not bool(self.ui_overlay.visible))
            except Exception:
                pass
            self.caps_lock_taps = []
            return

        # While the overlay is visible, treat the keyboard like a menu controller: do not
        # capture movement keys into `keys_pressed` (prevents "creeping" after closing the menu).
        if bool(getattr(self.ui_overlay, "visible", False)):
            try:
                prefs = None
                if self.ui_overlay and getattr(self.ui_overlay, "bento_system", None):
                    prefs = getattr(self.ui_overlay.bento_system, "user_prefs", None)

                def _set_scope(value: str) -> None:
                    try:
                        if prefs is not None and hasattr(prefs, "set_preference"):
                            prefs.set_preference("bento.scope", value)
                    except Exception:
                        pass

                if key == "tab":
                    order = ["all", "active", "fav", "recent"]
                    cur = "all"
                    try:
                        if prefs is not None and hasattr(prefs, "get_preference"):
                            cur = str(prefs.get_preference("bento.scope", "all") or "all").strip().lower()
                    except Exception:
                        cur = "all"
                    try:
                        idx = order.index(cur)
                    except Exception:
                        idx = 0
                    _set_scope(order[(idx + 1) % len(order)])
                    self.refresh_ui_overlay_widgets()
                    return

                if key in {"1", "2", "3", "4"}:
                    mapping = {"1": "all", "2": "active", "3": "fav", "4": "recent"}
                    _set_scope(mapping.get(key, "all"))
                    self.refresh_ui_overlay_widgets()
                    return

                if key == "v":
                    hid = getattr(self, "_hovered_object_id", None)
                    wid = None
                    if isinstance(hid, str) and hid.startswith("bento_"):
                        wid = hid[len("bento_") :]
                    if wid and self.ui_overlay and getattr(self.ui_overlay, "bento_system", None):
                        try:
                            toggle = getattr(self.ui_overlay.bento_system, "toggle_favorite_widget", None)
                            if callable(toggle):
                                toggle(wid)
                        except Exception:
                            pass
                        self.refresh_ui_overlay_widgets()
                    return
            except Exception:
                return

            return

        # Check for Caps Lock double-tap
        if key == 'caps_lock':
            current_time = time.time()
            self.caps_lock_taps.append(current_time)

            # Check for double-tap within 0.5 seconds
            if len(self.caps_lock_taps) >= 2:
                if self.caps_lock_taps[-1] - self.caps_lock_taps[-2] < 0.5:
                    try:
                        self._set_overlay_visible(not bool(self.ui_overlay.visible))
                    except Exception:
                        pass
                self.caps_lock_taps = []

        # Normal gameplay input (only when not paused).
        self.keys_pressed.add(key)

        # Toggle flowchart tree with 'F' key
        if key == 'f':
            self.flowchart.visible = not self.flowchart.visible
            print(f"[3D Engine] Flowchart Tree: {'ON' if self.flowchart.visible else 'OFF'}")
            self._publish(
                "flowchart_toggled",
                {"visible": bool(self.flowchart.visible), "source": "immersive_3d"},
            )

        # Jump / Double-jump (Space)
        if key == "space":
            now = time.time()
            if now - self._last_space_press_ts < 0.08:
                return
            self._last_space_press_ts = now
            self._try_jump()

    def _try_jump(self):
        if self._jump_count == 0 and self._grounded:
            self._vy = self.jump_strength
            self._grounded = False
            self._jump_count = 1
            return
        if self._jump_count == 1:
            self._vy = max(self._vy, self.double_jump_strength)
            self._grounded = False
            self._jump_count = 2

    def handle_key_release(self, event):
        """Handle key release events"""
        key = event.keysym.lower()
        self.keys_pressed.discard(key)

    def handle_mouse_motion(self, event):
        """Handle mouse movement for camera control"""
        prev_x = self.mouse_x
        prev_y = self.mouse_y
        try:
            mx = int(event.x)
            my = int(event.y)
        except Exception:
            return

        if not self.mouse_captured:
            # With mouse released, treat this as a pointer device and update hover state.
            self.mouse_x = mx
            self.mouse_y = my
            try:
                if bool(self.ui_overlay.visible) or bool(getattr(self.flowchart, "visible", False)):
                    obj = self._pick_object_at(mx, my)
                    self._hovered_object_id = getattr(obj, "id", None) if obj else None
                else:
                    self._hovered_object_id = None
            except Exception:
                self._hovered_object_id = None
            return

        # Calculate mouse delta
        dx = mx - prev_x
        dy = my - prev_y

        # Update camera rotation
        self.camera.yaw += dx * self.mouse_sensitivity
        self.camera.pitch = max(-89, min(89, self.camera.pitch - dy * self.mouse_sensitivity))

        # Update mouse position
        self.mouse_x = mx
        self.mouse_y = my

    def _set_overlay_visible(self, visible: bool):
        """
        Toggle overlay visibility and apply the "pause menu" behavior.

        - When visible: freeze movement + release mouse look; refresh overlay contents.
        - When hidden: restore mouse capture default; clear hover state.
        """
        self.ui_overlay.visible = bool(visible)
        self.paused = bool(self.ui_overlay.visible)
        if self.paused:
            try:
                self.refresh_ui_overlay_widgets()
            except Exception:
                pass
            self.keys_pressed.clear()
            self.mouse_captured = False
        else:
            # Never "buffer" keys typed while paused; closing the menu should be safe/boring.
            self.keys_pressed.clear()
            self.mouse_captured = bool(self.capture_mouse_default)
            self._hovered_object_id = None
        try:
            if self._bound_canvas is not None and hasattr(self._bound_canvas, "configure"):
                self._bound_canvas.configure(cursor=("arrow" if self.ui_overlay.visible else "crosshair"))
        except Exception:
            pass
        try:
            print(f"[3D Engine] UI Overlay: {'ON' if self.ui_overlay.visible else 'OFF'}")
        except Exception:
            pass
        self._publish(
            "ui_overlay_toggled",
            {"visible": bool(self.ui_overlay.visible), "source": "immersive_3d"},
        )

    def _pick_object_at(self, x: int, y: int) -> Optional[Interactive3DObject]:
        """Pick the nearest projected object under a screen-space point."""
        best = None
        best_dist = 1e9
        for obj in self.objects:
            try:
                min_px = 40 if (obj.data or {}).get("bento_widget") else 14
            except Exception:
                min_px = 14
            rect = obj.get_screen_rect(self.camera, self.width, self.height, min_px=min_px)
            if not rect:
                continue
            x1, y1, x2, y2, depth = rect
            if x1 <= x <= x2 and y1 <= y <= y2:
                if depth < best_dist:
                    best = obj
                    best_dist = depth
        return best

    def update_camera_position(self):
        """Update camera position based on WASD input with Minecraft-style momentum"""
        if getattr(self, "paused", False):
            # Keep eye height stable while paused, but do not accept movement input.
            try:
                current_floor_y = self.floor_nav.get_floor_y_position(self.floor_nav.current_floor)
                ground_y = current_floor_y
                if self.floor_nav.current_floor == FloorType.N_EXTERNAL:
                    try:
                        ground_y = current_floor_y + self.terrain.get_height_at(self.camera.x, self.camera.z)
                    except Exception:
                        ground_y = current_floor_y
                desired_eye_y = ground_y + 5.0
                if self.camera.y < desired_eye_y:
                    self.camera.y = desired_eye_y
            except Exception:
                pass
            return
        # In embedded/preview mode (mouse not captured), keep the camera fixed but still
        # maintain correct eye height relative to the ground plane.
        if not self.mouse_captured:
            current_floor_y = self.floor_nav.get_floor_y_position(self.floor_nav.current_floor)
            ground_y = current_floor_y
            if self.floor_nav.current_floor == FloorType.N_EXTERNAL:
                try:
                    ground_y = current_floor_y + self.terrain.get_height_at(self.camera.x, self.camera.z)
                except Exception:
                    ground_y = current_floor_y
            desired_eye_y = ground_y + 5.0
            if self.camera.y < desired_eye_y:
                self.camera.y = desired_eye_y
            return

        forward = self.camera.get_forward_vector()
        right = self.camera.get_right_vector()

        # Calculate target velocity based on input
        target_vx = 0.0
        target_vz = 0.0
        speed = self.move_speed * (self.run_speed_multiplier if "shift_l" in self.keys_pressed or "shift_r" in self.keys_pressed else 1.0)

        # WASD movement (target velocity)
        if 'w' in self.keys_pressed:
            target_vx += forward[0] * speed
            target_vz += forward[1] * speed
        if 's' in self.keys_pressed:
            target_vx -= forward[0] * speed
            target_vz -= forward[1] * speed
        if 'a' in self.keys_pressed:
            target_vx -= right[0] * speed
            target_vz -= right[1] * speed
        if 'd' in self.keys_pressed:
            target_vx += right[0] * speed
            target_vz += right[1] * speed

        # Apply momentum (Minecraft-style smooth movement)
        if target_vx != 0 or target_vz != 0:
            # Accelerate towards target velocity
            self.velocity_x += (target_vx - self.velocity_x) * self.acceleration
            self.velocity_z += (target_vz - self.velocity_z) * self.acceleration
        else:
            # Decelerate to stop (smoother than instant stop)
            self.velocity_x *= (1.0 - self.deceleration)
            self.velocity_z *= (1.0 - self.deceleration)

            # Stop completely when very slow (prevent endless drift)
            if abs(self.velocity_x) < 0.001:
                self.velocity_x = 0.0
            if abs(self.velocity_z) < 0.001:
                self.velocity_z = 0.0

        # Update camera position with momentum
        self.camera.x += self.velocity_x
        self.camera.z += self.velocity_z

        # Vertical physics
        dt = 1.0 / 60.0
        if not self._grounded:
            self._vy -= self.gravity * dt
            self.camera.y += self._vy * dt

        # Compute ground plane at current floor.
        current_floor_y = self.floor_nav.get_floor_y_position(self.floor_nav.current_floor)
        ground_y = current_floor_y
        if self.floor_nav.current_floor == FloorType.N_EXTERNAL:
            ground_y = current_floor_y + self.terrain.get_height_at(self.camera.x, self.camera.z)

        desired_eye_y = ground_y + 5.0
        if self.camera.y <= desired_eye_y:
            self.camera.y = desired_eye_y
            self._vy = 0.0
            self._grounded = True
            self._jump_count = 0

    def handle_mouse_click(self, event):
        """Handle clicking on interactive 3D objects."""
        # Find nearest clickable object under cursor.
        try:
            best = self._pick_object_at(int(event.x), int(event.y))
        except Exception:
            best = None

        if best is None:
            return

        # Doors teleport within the 3D tower.
        if best.object_type == "door" and best.data and best.data.get("target_floor"):
            # In preview/embedded mode (mouse not captured), treat door clicks as UI actions.
            if not self.mouse_captured and callable(self.on_action):
                try:
                    self.on_action(best)
                except Exception:
                    pass
                return
            try:
                target = best.data.get("target_floor")
                if isinstance(target, FloorType):
                    self.floor_nav.current_floor = target
                    self.camera.y = self.floor_nav.get_floor_y_position(target) + 5.0
                    self._vy = 0.0
                    self._jump_count = 0
                    self._grounded = True
                    try:
                        self.refresh_ui_overlay_widgets()
                    except Exception:
                        pass
                if callable(self.on_action):
                    try:
                        self.on_action(best)
                    except Exception:
                        pass
                return
            except Exception:
                return

        # Flowchart quick-jump nodes.
        if best.object_type == "sphere" and best.data and best.data.get("type") == "floor":
            if not self.mouse_captured and callable(self.on_action):
                try:
                    self.on_action(best)
                except Exception:
                    pass
                return
            try:
                target = best.data.get("target_floor")
                if isinstance(target, FloorType):
                    self.floor_nav.current_floor = target
                    self.camera.y = self.floor_nav.get_floor_y_position(target) + 5.0
                    self._vy = 0.0
                    self._jump_count = 0
                    self._grounded = True
                    try:
                        self.refresh_ui_overlay_widgets()
                    except Exception:
                        pass
                if callable(self.on_action):
                    try:
                        self.on_action(best)
                    except Exception:
                        pass
                return
            except Exception:
                pass

        # Widgets/windows/spheres can invoke callbacks or bubble to host.
        try:
            if callable(best.callback):
                best.callback()
        except Exception:
            pass

        if callable(self.on_action):
            try:
                self.on_action(best)
            except Exception:
                pass

    def render_frame(self, canvas: Canvas):
        """Render current frame to canvas"""
        canvas.delete("all")

        # Render sky/background
        self._render_background(canvas)

        # Render terrain if on N.py external ground
        if self.floor_nav.current_floor == FloorType.N_EXTERNAL:
            self._render_terrain(canvas)
        else:
            self._render_floor_environment(canvas)

        # Dimming rules:
        # - Curved overlay visible => always dim
        # - Host shells (e.g., N lobby) may request dimming via `canvas._lightspeed_dim`
        dim = 0.0
        try:
            dim = float(getattr(canvas, "_lightspeed_dim", 0.0) or 0.0)
        except Exception:
            dim = 0.0
        if getattr(self.ui_overlay, "visible", False):
            dim = max(dim, 0.5)

        if dim > 0.05:
            if dim >= 0.6:
                stipple = "gray75"
            elif dim >= 0.35:
                stipple = "gray50"
            elif dim >= 0.2:
                stipple = "gray25"
            else:
                stipple = "gray12"
            canvas.create_rectangle(0, 0, self.width, self.height, fill="#000000", outline="", stipple=stipple)

        # Sort objects by distance (painter's algorithm)
        visible_objects = []
        for obj in self.objects:
            # Filter by visibility
            # Only hide the curved UI overlay panels when the UI overlay is off.
            if obj.object_type == "window":
                try:
                    if (obj.data or {}).get("curved") and not self.ui_overlay.visible:
                        continue
                except Exception:
                    pass
            if obj.object_type == "sphere" and obj.data and obj.data.get('type') in ['root', 'floor']:
                if not self.flowchart.visible:
                    continue

            screen_pos = obj.get_screen_position(self.camera, self.width, self.height)
            if screen_pos:
                visible_objects.append((obj, screen_pos))

        # Sort by distance (farthest first)
        visible_objects.sort(key=lambda x: x[1][2], reverse=True)

        # Render objects
        for obj, (sx, sy, dist) in visible_objects:
            hovered = bool(getattr(obj, "id", None)) and (obj.id == self._hovered_object_id)
            self._render_object(canvas, obj, sx, sy, dist, hovered=hovered)

        # Render UI elements
        self._render_ui_info(canvas)

    def _render_background(self, canvas: Canvas):
        """Render sky gradient background"""
        # Sky gradient (top to horizon)
        for i in range(0, self.height // 2, 10):
            color_intensity = int(10 + (i / (self.height / 2)) * 30)
            color = f"#{color_intensity:02x}{color_intensity+20:02x}{color_intensity+40:02x}"
            canvas.create_rectangle(0, i, self.width, i+10, fill=color, outline="")

        # Ground color (below horizon)
        canvas.create_rectangle(0, self.height//2, self.width, self.height,
                              fill="#1a4d1a", outline="")

    def _render_terrain(self, canvas: Canvas):
        """Render Windows 97 rolling hills terrain"""
        # Render grid lines for hills
        grid_size = 5
        for x in range(-50, 50, grid_size):
            for z in range(-50, 50, grid_size):
                # Get corner heights
                h1 = self.terrain.get_height_at(float(x), float(z))
                h2 = self.terrain.get_height_at(float(x + grid_size), float(z))
                h3 = self.terrain.get_height_at(float(x), float(z + grid_size))

                # Project to screen
                p1 = Vector3D(float(x), h1, float(z))
                p2 = Vector3D(float(x + grid_size), h2, float(z))
                p3 = Vector3D(float(x), h3, float(z + grid_size))

                # Create temporary objects for projection
                obj1 = Interactive3DObject("", "", p1, (0,0,0), "", "", FloorType.N_EXTERNAL)
                obj2 = Interactive3DObject("", "", p2, (0,0,0), "", "", FloorType.N_EXTERNAL)
                obj3 = Interactive3DObject("", "", p3, (0,0,0), "", "", FloorType.N_EXTERNAL)

                s1 = obj1.get_screen_position(self.camera, self.width, self.height)
                s2 = obj2.get_screen_position(self.camera, self.width, self.height)
                s3 = obj3.get_screen_position(self.camera, self.width, self.height)

                # Draw grid lines
                if s1 and s2:
                    canvas.create_line(s1[0], s1[1], s2[0], s2[1], fill="#2a5a2a", width=1)
                if s1 and s3:
                    canvas.create_line(s1[0], s1[1], s3[0], s3[1], fill="#2a5a2a", width=1)

    def _render_floor_environment(self, canvas: Canvas):
        """Render interior floor environment"""
        floor_name = self.floor_nav.current_floor.value

        # Draw floor plane
        canvas.create_rectangle(0, self.height//2, self.width, self.height,
                              fill="#0a1628", outline="")

        # Draw floor label
        canvas.create_text(self.width//2, 30, text=f"Floor: {floor_name}",
                          font=("Consolas", 20, "bold"), fill="#00ffff")

    def _render_object(
        self,
        canvas: Canvas,
        obj: Interactive3DObject,
        screen_x: int,
        screen_y: int,
        distance: float,
        *,
        hovered: bool = False,
    ):
        """Render a 3D object on canvas"""
        # Calculate size based on distance
        base_size = 100 if obj.object_type == "sphere" else 50
        size = int(base_size / max(distance, 0.5))

        if obj.object_type == "sphere":
            # Render sphere as circle with glow
            if obj.data and obj.data.get('pulsing'):
                pulse = math.sin(time.time() * 3) * 0.3 + 0.7
                glow_size = int(size * (1.0 + pulse * 0.5))
                canvas.create_oval(screen_x - glow_size, screen_y - glow_size,
                                 screen_x + glow_size, screen_y + glow_size,
                                 fill="", outline=obj.color, width=2)

            canvas.create_oval(screen_x - size, screen_y - size,
                             screen_x + size, screen_y + size,
                             fill=obj.color, outline="white", width=2)

        elif obj.object_type == "window":
            # Check if this is a Bento widget
            is_bento = obj.data and obj.data.get('bento_widget', False)

            if is_bento:
                # Use physical widget size (meters) -> pixels so the overlay is readable like a menu.
                min_px = 60
                try:
                    min_px = int(getattr(self.ui_overlay, "ui_overlay_min_px", min_px))
                except Exception:
                    pass
                rect = obj.get_screen_rect(self.camera, self.width, self.height, min_px=min_px)
                if rect:
                    x1, y1, x2, y2, _depth = rect
                    w = max(1, x2 - x1)
                    h = max(1, y2 - y1)
                    cx = x1 + w // 2

                    # Use an ASCII fallback icon to avoid mojibake on Windows.
                    icon = obj.data.get('icon', '?')
                    outline = "#00ff88" if hovered else "#00ffff"
                    outline_w = 3 if hovered else 2

                    # Fake translucency with stipple (Tk canvas has no alpha fills).
                    canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=obj.color,
                        outline=outline,
                        width=outline_w,
                        stipple="gray50",
                    )
                    canvas.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3, outline="#1A5F5F", width=1)

                    icon_size = max(16, min(36, int(h * 0.35)))
                    title_size = max(10, min(16, int(h * 0.16)))
                    canvas.create_text(
                        cx,
                        y1 + int(h * 0.34),
                        text=str(icon),
                        font=("Segoe UI Emoji", icon_size),
                        fill="white",
                    )
                    canvas.create_text(
                        cx,
                        y1 + int(h * 0.78),
                        text=obj.name,
                        font=("Consolas", title_size, "bold"),
                        fill="#00ffff",
                        width=max(60, int(w * 0.92)),
                    )
                    return

                # Render Bento widget with enhanced styling
                # Use an ASCII fallback icon to avoid mojibake on Windows.
                icon = obj.data.get('icon', '?')
                widget_floor = obj.data.get('floor', '')

                outline = "#00ff88" if hovered else "#00ffff"
                outline_w = 3 if hovered else 2

                # Glass effect background
                canvas.create_rectangle(
                    screen_x - size,
                    screen_y - size,
                    screen_x + size,
                    screen_y + size,
                    fill=obj.color,
                    outline=outline,
                    width=outline_w,
                )

                # Icon (large)
                icon_size = max(12, size//3)
                canvas.create_text(screen_x, screen_y - size//3,
                                 text=icon,
                                 font=("Segoe UI Emoji", icon_size),
                                 fill="white")

                # Widget title (small)
                title_size = max(7, size//12)
                canvas.create_text(screen_x, screen_y + size//2,
                                 text=obj.name,
                                 font=("Consolas", title_size),
                                 fill="#00ffff",
                                 width=size*2)
            else:
                # Regular window rendering
                canvas.create_rectangle(screen_x - size, screen_y - size,
                                      screen_x + size, screen_y + size,
                                      fill=obj.color,
                                      outline=("#00ff88" if hovered else "#00ffff"),
                                      width=(3 if hovered else 2))
                canvas.create_text(screen_x, screen_y, text=obj.name,
                                 font=("Consolas", max(8, size//10)), fill="white")

        elif obj.object_type == "door":
            # Render door/portal
            canvas.create_rectangle(screen_x - size, screen_y - size*2,
                                  screen_x + size, screen_y + size,
                                  fill=obj.color,
                                  outline=("#00ff88" if hovered else "#ffff00"),
                                  width=(4 if hovered else 3))
            canvas.create_text(screen_x, screen_y, text=obj.name,
                             font=("Consolas", max(8, size//10)), fill="white",
                             width=size*2)
        elif obj.object_type == "platform":
            # Render platform/slab (tower floors)
            canvas.create_rectangle(
                screen_x - size * 2,
                screen_y - max(6, size // 3),
                screen_x + size * 2,
                screen_y + max(6, size // 3),
                fill=obj.color,
                outline="#00ffff",
                width=2,
            )

        # Show name if close
        if distance < 5.0:
            canvas.create_text(screen_x, screen_y - size - 10, text=obj.name,
                             font=("Consolas", 10, "bold"), fill="white")

    def _render_ui_info(self, canvas: Canvas):
        """Render UI information overlay"""
        # Camera info
        info_text = f"Position: ({self.camera.x:.1f}, {self.camera.y:.1f}, {self.camera.z:.1f})\n"
        info_text += f"Rotation: Yaw {self.camera.yaw:.1f}° Pitch {self.camera.pitch:.1f}°\n"
        info_text += f"Floor: {self.floor_nav.current_floor.value}\n"
        scope = "all"
        try:
            prefs = None
            if self.ui_overlay and getattr(self.ui_overlay, "bento_system", None):
                prefs = getattr(self.ui_overlay.bento_system, "user_prefs", None)
            if prefs is not None and hasattr(prefs, "get_preference"):
                scope = str(prefs.get_preference("bento.scope", "all") or "all").strip().lower()
        except Exception:
            scope = "all"
        info_text += f"UI Overlay: {'ON' if self.ui_overlay.visible else 'OFF'} (Esc / CapsLock x2)\n"
        info_text += f"Menu Scope: {scope}\n"
        info_text += f"Flowchart: {'ON' if self.flowchart.visible else 'OFF'} (F key)"

        info_y = 10
        if bool(getattr(self.ui_overlay, "visible", False)):
            # Dedicated pause-menu banner so the overlay reads as a real menu (not distant diegetic HUD glass).
            try:
                canvas.create_rectangle(0, 0, self.width, 56, fill="#000000", outline="", stipple="gray50")
                canvas.create_text(
                    self.width // 2,
                    18,
                    text="MENU",
                    font=("Consolas", 16, "bold"),
                    fill="#00ffff",
                )
                canvas.create_text(
                    self.width // 2,
                    40,
                    text=f"Scope: {scope.upper()}   Tab: cycle   1-4: set   V: favorite   Esc: close",
                    font=("Consolas", 10, "bold"),
                    fill="white",
                )
                info_y = 64
            except Exception:
                info_y = 10

        canvas.create_text(10, info_y, text=info_text, anchor="nw",
                          font=("Consolas", 10), fill="white")

        # Controls help
        controls = "WASD: Move | Shift: Run | Space: Jump/Double | Mouse: Look | F: Flowchart | Esc: Menu | Overlay: Tab/1-4 Scope, V Fav"
        canvas.create_text(self.width//2, self.height - 20, text=controls,
                          font=("Consolas", 10, "bold"), fill="#00ff00")

        # Crosshair: only when mouse look is captured (not in menu/overlay mode).
        if self.mouse_captured:
            ch_size = 10
            canvas.create_line(self.width//2 - ch_size, self.height//2,
                              self.width//2 + ch_size, self.height//2,
                              fill="white", width=2)
            canvas.create_line(self.width//2, self.height//2 - ch_size,
                              self.width//2, self.height//2 + ch_size,
                              fill="white", width=2)


def attach_immersive_3d_environment(
    root: tk.Misc,
    canvas: Canvas,
    *,
    on_action: Optional[Callable[[Interactive3DObject], None]] = None,
    event_bus: Optional[object] = None,
    physics: Optional[Dict[str, float]] = None,
    capture_mouse: bool = True,
    enable_input: bool = True,
) -> Immersive3DEngine:
    """
    Attach the immersive 3D engine to an existing Tk root + canvas.
    Enables embedding inside N.py or other Trinity/Construct UIs.
    """
    try:
        width = int(canvas.winfo_width() or canvas["width"] or 1200)
        height = int(canvas.winfo_height() or canvas["height"] or 800)
    except Exception:
        width, height = 1200, 800

    engine = Immersive3DEngine(
        width,
        height,
        on_action=on_action,
        event_bus=event_bus,
        physics=physics,
        capture_mouse=capture_mouse,
    )
    # Keep a handle so the engine can adjust cursor behavior when toggling menu/overlay.
    engine._bound_canvas = canvas
    try:
        canvas.configure(cursor=("crosshair" if capture_mouse else "arrow"))
    except Exception:
        pass

    # Bind controls to the canvas (keeps bindings scoped for embedding in N.py).
    #
    # When N.py uses the Construct as an ambient background, it should not capture
    # keyboard/mouse input. In that case, we skip bindings entirely.
    if enable_input:
        try:
            canvas.focus_set()
        except Exception:
            pass
        # Keep Escape scoped to the immersive engine so N.py doesn't interpret it as "go back".
        def _on_key_press(ev):
            try:
                engine.handle_key_press(ev)
            except Exception:
                pass
            try:
                if str(getattr(ev, "keysym", "") or "").lower() == "escape":
                    return "break"
            except Exception:
                pass
            return None

        canvas.bind('<KeyPress>', _on_key_press)
        canvas.bind('<KeyRelease>', engine.handle_key_release)
        canvas.bind('<Motion>', engine.handle_mouse_motion)
        canvas.bind('<Button-1>', engine.handle_mouse_click)
        canvas.bind('<Button-1>', lambda _e: canvas.focus_set(), add="+")

    def _on_resize(_evt=None):
        try:
            engine.width = int(canvas.winfo_width())
            engine.height = int(canvas.winfo_height())
        except Exception:
            return

    canvas.bind("<Configure>", _on_resize)

    def game_loop():
        try:
            if not canvas.winfo_exists():
                return
        except Exception:
            return
        try:
            engine.update_camera_position()
            engine.render_frame(canvas)
        except Exception:
            return
        try:
            root.after(16, game_loop)  # ~60 FPS
        except Exception:
            return

    game_loop()
    return engine


def launch_immersive_3d_environment(parent: tk.Misc | None = None):
    """
    Launch the 3D immersive environment.

    - If `parent` is None: creates its own Tk root and runs `mainloop()` (standalone mode).
    - If `parent` is provided: creates a Toplevel window and relies on the caller's
      existing event loop (integrated mode).
    """
    standalone = parent is None
    win: tk.Misc
    if standalone:
        win = tk.Tk()
    else:
        win = tk.Toplevel(parent)

    try:
        win.title("LightSpeed V0.9.11+ - 3D Immersive Environment")
    except Exception:
        pass

    try:
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        win.geometry(f"{screen_width}x{screen_height}")
    except Exception:
        screen_width = 1200
        screen_height = 800
        try:
            win.geometry(f"{screen_width}x{screen_height}")
        except Exception:
            pass

    canvas = Canvas(win, width=screen_width, height=screen_height, bg='#000000', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    attach_immersive_3d_environment(win, canvas)

    print("[3D Engine] Starting immersive environment...")
    print("[3D Engine] Controls: WASD, Shift, Space, Mouse | CapsLock x2 UI | F Flowchart")

    if standalone:
        win.mainloop()
    return win


if __name__ == "__main__":
    launch_immersive_3d_environment()
