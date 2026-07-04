"""
LightSpeed Z-Tower Renderer V1.0.0
See-through tower visualization with all 8 Z-floors visible

Purpose:
Renders the complete LightSpeed tower structure with transparent walls,
allowing users to see all floors simultaneously and peek inside each floor
to view libraries, laboratories, and other internal components.

The tower is the central visual element of the immersive interface -
users can see the entire structure and navigate through it in 3D space.

Features:
- 8 Z-floors stacked vertically
- Semi-transparent walls (see-through)
- Floor-specific colors and themes
- Interior icons visible from outside:
  * Library shelves (Z-1 Oracle)
  * Laboratory equipment (Z0 TheConstruct)
  * AI core (Z+2 Neo)
  * Control panels (Z+3 Trinity)
  * Server racks (Z-4 Core)
- Active floor highlighting
- Elevator shaft in center
- Distance-based transparency

Architecture:
```
ZTowerRenderer
    ├─> FloorRenderer (individual floors)
    ├─> WallRenderer (transparent walls)
    ├─> InteriorRenderer (floor contents)
    ├─> IconRenderer (visible markers)
    └─> LightingSystem (glow effects)
```

Visual Design:
- Each floor is a horizontal platform at specific Y height
- Transparent cylindrical walls around each floor
- Interior objects visible through walls
- Color-coded by floor (from FLOOR_DEFINITIONS)
- Glow effects on active floor
- See-through effect increases with distance

Author: LightSpeed Team
Date: January 5, 2026
"""

import tkinter as tk
from tkinter import Canvas
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
# FLOOR INTERIOR DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FloorInterior:
    """Definition of floor interior contents"""
    floor_id: str
    icons: List[str]
    objects: List[str]
    theme_color: str
    description: str
    glow_intensity: float = 0.3


# Floor interior configurations
FLOOR_INTERIORS = {
    'Z+3_Trinity': FloorInterior(
        floor_id='Z+3_Trinity',
        icons=['dashboard', 'settings', 'user_profile', 'control_panel'],
        objects=['holographic_displays', 'control_consoles', 'ui_panels'],
        theme_color='#00FFFF',  # Cyan
        description='Glass control center with holographic displays',
        glow_intensity=0.4
    ),
    'Z+2_Neo': FloorInterior(
        floor_id='Z+2_Neo',
        icons=['brain', 'neural_network', 'ai_core', 'learning'],
        objects=['ai_processors', 'data_streams', 'correlation_graphs'],
        theme_color='#FF0080',  # Magenta
        description='Pulsing AI core with flowing data streams',
        glow_intensity=0.5
    ),
    'Z+1_Architect': FloorInterior(
        floor_id='Z+1_Architect',
        icons=['blueprint', 'planning', 'strategy', 'mission'],
        objects=['mission_boards', 'timelines', 'okr_dashboards'],
        theme_color='#00FF80',  # Green
        description='Strategic planning center with project boards',
        glow_intensity=0.3
    ),
    'Z0_TheConstruct': FloorInterior(
        floor_id='Z0_TheConstruct',
        icons=['atom', 'physics', 'simulation', 'laboratory'],
        objects=['physics_engines', 'black_hole_sim', 'quantum_foam', 'particle_accelerator'],
        theme_color='#FFFF00',  # Yellow
        description='Physics laboratory with active simulations',
        glow_intensity=0.6
    ),
    'Z-2_Oracle': FloorInterior(
        floor_id='Z-2_Oracle',
        icons=['books', 'documents', 'vault', 'library'],
        objects=['library_shelves', 'filing_systems', 'ip_vault', 'knowledge_base'],
        theme_color='#FF8000',  # Orange
        description='Library with glowing document archives',
        glow_intensity=0.3
    ),
    'Z-3_Smith': FloorInterior(
        floor_id='Z-3_Smith',
        icons=['cogs', 'automation', 'tasks', 'background'],
        objects=['task_queues', 'automation_bots', 'schedulers'],
        theme_color='#8000FF',  # Purple
        description='Automated task processing center',
        glow_intensity=0.3
    ),
    'Z-4_Merovingian': FloorInterior(
        floor_id='Z-4_Merovingian',
        icons=['monitor', 'logs', 'alerts', 'system'],
        objects=['log_streams', 'monitoring_dashboards', 'alert_systems'],
        theme_color='#FF0000',  # Red
        description='Monitoring center with flowing log data',
        glow_intensity=0.4
    ),
    'Z-4_Core': FloorInterior(
        floor_id='Z-4_Core',
        icons=['server', 'core', 'infrastructure', 'foundation'],
        objects=['server_racks', 'core_systems', 'power_conduits'],
        theme_color='#FFFFFF',  # White
        description='Core infrastructure with glowing servers',
        glow_intensity=0.5
    )
}

# Backward-compatible aliases (legacy floor IDs appear in older docs/configs)
_LEGACY_FLOOR_ALIASES = {
    'Z-1_Oracle': 'Z-2_Oracle',
    'Z-2_Smith': 'Z-3_Smith',
    'Z-3_Merovingian': 'Z-4_Merovingian',
    'Z-4_Core': 'Z-4_Merovingian',
}
for _legacy_id, _canonical_id in _LEGACY_FLOOR_ALIASES.items():
    if _canonical_id in FLOOR_INTERIORS:
        FLOOR_INTERIORS.setdefault(_legacy_id, FLOOR_INTERIORS[_canonical_id])


# ═══════════════════════════════════════════════════════════════════════════
# 3D VECTOR AND CAMERA (minimal definitions for rendering)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Vector3D:
    """3D point"""
    x: float
    y: float
    z: float


@dataclass
class Camera:
    """Camera for projection"""
    x: float = 0.0
    y: float = 55.0
    z: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0
    fov: float = 90.0


# ═══════════════════════════════════════════════════════════════════════════
# Z-TOWER RENDERER
# ═══════════════════════════════════════════════════════════════════════════

class ZTowerRenderer:
    """
    Renders the complete see-through Z-tower structure

    The tower is the central visual element - users can see all floors
    at once and peek inside to see what's on each level.
    """

    def __init__(self, floor_definitions: Dict[str, Any]):
        """
        Initialize Z-Tower Renderer

        Args:
            floor_definitions: Floor configuration from orchestrator
        """
        self.floors = floor_definitions
        self.floor_interiors = FLOOR_INTERIORS

        # Tower geometry
        self.tower_radius = 15.0  # meters
        self.floor_height = 3.0  # meters per floor
        self.wall_segments = 32  # for cylindrical approximation

        # Visual settings
        self.base_wall_opacity = 0.15  # Very transparent
        self.active_floor_opacity = 0.3  # Slightly more visible
        self.glow_pulse_speed = 2.0  # Hz

        # Interior object settings
        self.icon_size = 1.5  # meters
        self.icon_glow = True

        print("[ZTower] Renderer initialized")
        print(f"[ZTower] Tower radius: {self.tower_radius}m, {len(self.floors)} floors")


    # ═══════════════════════════════════════════════════════════════════════
    # MAIN RENDERING
    # ═══════════════════════════════════════════════════════════════════════

    def render_complete_tower(
        self,
        canvas: Canvas,
        camera: Camera,
        screen_size: Tuple[int, int],
        active_floor: Optional[str] = None
    ):
        """
        Render complete tower structure

        Args:
            canvas: Tkinter canvas to draw on
            camera: Camera for 3D projection
            screen_size: (width, height) of screen
            active_floor: Currently active floor (highlighted)
        """
        screen_width, screen_height = screen_size

        # Sort floors by distance from camera (painter's algorithm)
        floor_distances = []

        for floor_id, floor_def in self.floors.items():
            floor_y = floor_def.y_position
            distance = abs(camera.y - floor_y)
            floor_distances.append((floor_id, floor_def, distance))

        # Sort farthest first
        floor_distances.sort(key=lambda x: x[2], reverse=True)

        # Render each floor
        for floor_id, floor_def, distance in floor_distances:
            is_active = (floor_id == active_floor)

            self.render_floor(
                canvas,
                floor_id,
                floor_def,
                camera,
                screen_size,
                is_active=is_active,
                distance=distance
            )


    def render_floor(
        self,
        canvas: Canvas,
        floor_id: str,
        floor_def: Any,
        camera: Camera,
        screen_size: Tuple[int, int],
        is_active: bool = False,
        distance: float = 0.0
    ):
        """Render single floor with interior"""
        floor_y = floor_def.y_position

        # Render floor platform
        self._render_floor_platform(canvas, floor_y, floor_def.color, camera, screen_size)

        # Render transparent walls
        self._render_floor_walls(
            canvas, floor_y, floor_def.color,
            camera, screen_size, is_active, distance
        )

        # Render interior contents
        if floor_id in self.floor_interiors:
            interior = self.floor_interiors[floor_id]
            self._render_floor_interior(
                canvas, floor_y, interior, camera, screen_size
            )

        # Render floor label
        self._render_floor_label(
            canvas, floor_y, floor_def.name, floor_id,
            floor_def.color, camera, screen_size
        )


    # ═══════════════════════════════════════════════════════════════════════
    # FLOOR COMPONENTS
    # ═══════════════════════════════════════════════════════════════════════

    def _render_floor_platform(
        self,
        canvas: Canvas,
        floor_y: float,
        color: str,
        camera: Camera,
        screen_size: Tuple[int, int]
    ):
        """Render floor platform (solid disk)"""
        # Sample points around circle
        points_2d = []

        for i in range(self.wall_segments):
            angle = (i / self.wall_segments) * 2 * math.pi

            x_3d = math.cos(angle) * self.tower_radius
            z_3d = math.sin(angle) * self.tower_radius

            # Project to screen
            screen_pos = self._project_to_screen(
                Vector3D(x_3d, floor_y, z_3d),
                camera,
                screen_size
            )

            if screen_pos:
                points_2d.append(screen_pos)

        # Draw platform
        if len(points_2d) >= 3:
            # Flatten points for polygon
            flat_points = []
            for x, y in points_2d:
                flat_points.extend([x, y])

            canvas.create_polygon(
                flat_points,
                fill='#0a0a1a',  # Dark platform
                outline=color,
                width=2,
                tags='tower_platform'
            )


    def _render_floor_walls(
        self,
        canvas: Canvas,
        floor_y: float,
        color: str,
        camera: Camera,
        screen_size: Tuple[int, int],
        is_active: bool,
        distance: float
    ):
        """Render transparent cylindrical walls"""
        # Wall goes from floor_y to floor_y + floor_height

        # Sample points around cylinder
        for i in range(self.wall_segments):
            angle1 = (i / self.wall_segments) * 2 * math.pi
            angle2 = ((i + 1) / self.wall_segments) * 2 * math.pi

            # Bottom edge points
            x1_bottom = math.cos(angle1) * self.tower_radius
            z1_bottom = math.sin(angle1) * self.tower_radius

            x2_bottom = math.cos(angle2) * self.tower_radius
            z2_bottom = math.sin(angle2) * self.tower_radius

            # Top edge points
            x1_top = x1_bottom
            z1_top = z1_bottom

            x2_top = x2_bottom
            z2_top = z2_bottom

            # Project to screen
            p1_bottom = self._project_to_screen(
                Vector3D(x1_bottom, floor_y, z1_bottom),
                camera, screen_size
            )

            p2_bottom = self._project_to_screen(
                Vector3D(x2_bottom, floor_y, z2_bottom),
                camera, screen_size
            )

            p1_top = self._project_to_screen(
                Vector3D(x1_top, floor_y + self.floor_height, z1_top),
                camera, screen_size
            )

            p2_top = self._project_to_screen(
                Vector3D(x2_top, floor_y + self.floor_height, z2_top),
                camera, screen_size
            )

            # Draw wall segment (quad)
            if p1_bottom and p2_bottom and p1_top and p2_top:
                # Calculate opacity based on active state and distance
                opacity = self.active_floor_opacity if is_active else self.base_wall_opacity

                # Draw as very faint line (simulates transparency)
                canvas.create_line(
                    p1_bottom[0], p1_bottom[1],
                    p1_top[0], p1_top[1],
                    fill=color,
                    width=1,
                    tags='tower_wall'
                )

                canvas.create_line(
                    p1_top[0], p1_top[1],
                    p2_top[0], p2_top[1],
                    fill=color,
                    width=1,
                    tags='tower_wall'
                )


    def _render_floor_interior(
        self,
        canvas: Canvas,
        floor_y: float,
        interior: FloorInterior,
        camera: Camera,
        screen_size: Tuple[int, int]
    ):
        """Render interior contents of floor (visible through walls)"""
        # Place icons around the floor
        num_icons = len(interior.icons)

        for i, icon_name in enumerate(interior.icons):
            # Position around circle, slightly inward
            angle = (i / num_icons) * 2 * math.pi
            radius = self.tower_radius * 0.6  # Inside the walls

            x_3d = math.cos(angle) * radius
            z_3d = math.sin(angle) * radius
            y_3d = floor_y + self.floor_height / 2  # Middle of floor

            # Project to screen
            screen_pos = self._project_to_screen(
                Vector3D(x_3d, y_3d, z_3d),
                camera,
                screen_size
            )

            if screen_pos:
                # Draw icon
                self._draw_icon(
                    canvas,
                    screen_pos,
                    icon_name,
                    interior.theme_color,
                    interior.glow_intensity
                )


    def _render_floor_label(
        self,
        canvas: Canvas,
        floor_y: float,
        floor_name: str,
        floor_id: str,
        color: str,
        camera: Camera,
        screen_size: Tuple[int, int]
    ):
        """Render floor label (always visible)"""
        # Position label outside tower wall
        label_x = self.tower_radius * 1.3
        label_z = 0.0
        label_y = floor_y + self.floor_height / 2

        screen_pos = self._project_to_screen(
            Vector3D(label_x, label_y, label_z),
            camera,
            screen_size
        )

        if screen_pos:
            # Draw label with background
            canvas.create_text(
                screen_pos[0], screen_pos[1],
                text=f"{floor_name}\n{floor_id}",
                fill=color,
                font=('Consolas', 10, 'bold'),
                anchor='w',
                tags='tower_label'
            )


    # ═══════════════════════════════════════════════════════════════════════
    # ICON RENDERING
    # ═══════════════════════════════════════════════════════════════════════

    def _draw_icon(
        self,
        canvas: Canvas,
        screen_pos: Tuple[int, int],
        icon_name: str,
        color: str,
        glow_intensity: float
    ):
        """Draw an interior icon (simplified representation)"""
        x, y = screen_pos
        size = 15  # pixels

        # Icon-specific shapes
        if 'brain' in icon_name or 'ai' in icon_name or 'neural' in icon_name:
            # Brain/AI: pulsing circle
            import time
            pulse = math.sin(time.time() * 3) * 0.3 + 0.7
            glow_size = int(size * (1 + pulse * glow_intensity))

            # Glow
            canvas.create_oval(
                x - glow_size, y - glow_size,
                x + glow_size, y + glow_size,
                fill='', outline=color, width=2,
                tags='tower_interior'
            )

            # Core
            canvas.create_oval(
                x - size, y - size,
                x + size, y + size,
                fill=color, outline='white', width=1,
                tags='tower_interior'
            )

        elif 'book' in icon_name or 'document' in icon_name or 'library' in icon_name:
            # Library: stacked rectangles
            for i in range(3):
                offset = i * 3
                canvas.create_rectangle(
                    x - size + offset, y - size + offset,
                    x + size - 5 + offset, y + size - 5 + offset,
                    fill='', outline=color, width=2,
                    tags='tower_interior'
                )

        elif 'atom' in icon_name or 'physics' in icon_name or 'simulation' in icon_name:
            # Physics: atom-like structure
            # Nucleus
            canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                fill=color, outline='white', width=1,
                tags='tower_interior'
            )

            # Orbits
            for angle in [0, 60, 120]:
                rad = math.radians(angle)
                orbit_x = x + math.cos(rad) * size
                orbit_y = y + math.sin(rad) * size

                canvas.create_line(
                    x, y, orbit_x, orbit_y,
                    fill=color, width=1,
                    tags='tower_interior'
                )

                canvas.create_oval(
                    orbit_x - 3, orbit_y - 3,
                    orbit_x + 3, orbit_y + 3,
                    fill=color, outline='white', width=1,
                    tags='tower_interior'
                )

        elif 'server' in icon_name or 'core' in icon_name:
            # Server: stacked bars
            for i in range(4):
                y_offset = i * 5
                canvas.create_rectangle(
                    x - size, y - size + y_offset,
                    x + size, y - size + y_offset + 3,
                    fill=color, outline='white', width=1,
                    tags='tower_interior'
                )

        else:
            # Default: simple square
            canvas.create_rectangle(
                x - size, y - size,
                x + size, y + size,
                fill='', outline=color, width=2,
                tags='tower_interior'
            )


    # ═══════════════════════════════════════════════════════════════════════
    # PROJECTION UTILITIES
    # ═══════════════════════════════════════════════════════════════════════

    def _project_to_screen(
        self,
        point: Vector3D,
        camera: Camera,
        screen_size: Tuple[int, int]
    ) -> Optional[Tuple[int, int]]:
        """
        Project 3D point to 2D screen coordinates

        Returns None if point is behind camera
        """
        screen_width, screen_height = screen_size

        # Translate to camera space
        dx = point.x - camera.x
        dy = point.y - camera.y
        dz = point.z - camera.z

        # Rotate by camera yaw
        yaw_rad = math.radians(-camera.yaw)
        rx = dx * math.cos(yaw_rad) - dz * math.sin(yaw_rad)
        rz = dx * math.sin(yaw_rad) + dz * math.cos(yaw_rad)

        # Check if behind camera
        if rz <= 0.1:
            return None

        # Simple perspective projection
        fov_scale = 1.0 / math.tan(math.radians(camera.fov / 2))

        screen_x = int(screen_width / 2 + (rx / rz) * screen_width * fov_scale / 2)
        screen_y = int(screen_height / 2 - (dy / rz) * screen_height * fov_scale / 2)

        return (screen_x, screen_y)


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'ZTowerRenderer',
    'FloorInterior',
    'FLOOR_INTERIORS'
]
