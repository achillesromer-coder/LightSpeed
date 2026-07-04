"""
LightSpeed V0.9.5 - 3D Spatial Navigation Engine
True Z-axis floor traversal with portal transitions

Implements 2026 Spatial UI Standards:
- Z-Floor stacking with camera transitions
- -50° to 50° Bento grid FOV
- Portal-link branching navigation
- Ease-in/out motion damping
- Adaptive curvature (1.5m radius)
- Gaze-reactive interactions

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
Date: January 3, 2026
"""

import tkinter as tk
from tkinter import Canvas
import math
import time
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ZFloorLevel(Enum):
    """Z-axis floor levels"""
    # Entry / setup surfaces (not a "floor file", but useful as a navigation hub)
    SURFACE = 4       # IT Portal / Home surface
    FIRSTRUN = 5      # First-run setup (optional)

    # Primary Z-stack floors (match `Z Axis/*.py` LAYER_ID values)
    TRINITY = 3       # Z+3
    NEO = 2           # Z+2
    ARCHITECT = 1     # Z+1
    CONSTRUCT = 0     # Z0 (TheConstruct)
    MORPHEUS = -1     # Z-1
    ORACLE = -2       # Z-2
    SMITH = -3        # Z-3
    MEROVINGIAN = -4  # Z-4


@dataclass
class SpatialPosition:
    """3D position in spatial navigation space"""
    x: float  # Horizontal position
    y: float  # Vertical position
    z: float  # Depth (floor level)
    pitch: float = 0.0   # Camera pitch (-90 to 90)
    yaw: float = 0.0     # Camera yaw (rotation)
    fov: float = 100.0   # Field of view (90-110 recommended)


@dataclass
class BentoCell:
    """Bento grid cell configuration"""
    id: str
    label: str
    floor: ZFloorLevel
    position: Tuple[float, float]  # (angle, distance) in degrees/meters
    size: Tuple[int, int]  # (width, height) in points
    target_floor: Optional[ZFloorLevel] = None  # For portal links
    callback: Optional[Callable] = None
    icon: str = ""
    color: str = "#102040"


class SpatialNavigator:
    """
    3D Spatial Navigation Engine for Z-Floor Architecture.

    Features:
    - True Z-axis camera movement
    - Portal transitions with dissolve effects
    - Billboarded Bento grids (-50° to 50°)
    - Adaptive curvature (1.5m radius)
    - Motion damping for smooth travel
    - Gaze-reactive cells
    """

    # Spatial constants (2026 standards)
    FOV_MIN = 90.0
    FOV_MAX = 110.0
    FOV_DEFAULT = 100.0

    GRID_ANGLE_MIN = -50.0  # degrees
    GRID_ANGLE_MAX = 50.0   # degrees

    REACH_ZONE_MIN = 0.5  # meters
    REACH_ZONE_MAX = 1.5  # meters
    REACH_ZONE_OPTIMAL = 1.5  # meters (adaptive curvature radius)

    CELL_MIN_SIZE = 60  # points (1.5-2 degrees visual arc)

    TRANSITION_DURATION = 0.8  # seconds
    DAMPING_FACTOR = 0.3  # ease-in/out strength

    def __init__(self, canvas: Canvas, width: int = 1920, height: int = 1080):
        """
        Initialize spatial navigator.

        Args:
            canvas: Tkinter canvas for rendering
            width: Canvas width (default Full HD)
            height: Canvas height (default Full HD)
        """
        self.canvas = canvas
        self.width = width
        self.height = height

        # Current camera position
        self.position = SpatialPosition(
            x=0.0,
            y=0.0,
            z=float(ZFloorLevel.SURFACE.value),  # Start at Surface hub
            fov=self.FOV_DEFAULT
        )

        # Target position (for smooth transitions)
        self.target_position = SpatialPosition(
            x=0.0, y=0.0, z=0.0, fov=self.FOV_DEFAULT
        )

        # Floor configurations
        self.floors: Dict[ZFloorLevel, List[BentoCell]] = {}
        self.current_floor = ZFloorLevel.SURFACE

        # Animation state
        self.is_transitioning = False
        self.transition_start_time = 0.0
        self.transition_start_pos = None
        self.transition_progress = 0.0

        # Gaze tracking (simulated with mouse for now)
        self.gaze_x = width // 2
        self.gaze_y = height // 2

        # Bind mouse for gaze simulation
        self.canvas.bind('<Motion>', self._on_mouse_move)
        self.canvas.bind('<Button-1>', self._on_click)

        # Start render loop
        self._loop_started = True
        self._render_loop()

    def register_floor(self, floor: ZFloorLevel, cells: List[BentoCell]):
        """
        Register Bento cells for a floor.

        Args:
            floor: Z-floor level
            cells: List of Bento cells for this floor
        """
        self.floors[floor] = cells

    def add_cell(self, cell: BentoCell):
        """Compatibility helper: add a single cell to its declared floor."""
        self.floors.setdefault(cell.floor, []).append(cell)

    def start_render_loop(self):
        """Compatibility helper: SpatialNavigator starts rendering on init."""
        if getattr(self, "_loop_started", False):
            return
        self._loop_started = True
        self._render_loop()

    def resize(self, width: int, height: int):
        """Resize render surface."""
        self.width = max(1, int(width))
        self.height = max(1, int(height))

    def hit_test(self, x: int, y: int) -> Optional[BentoCell]:
        """Return the BentoCell under the given screen coordinate (if any)."""
        self.gaze_x = int(x)
        self.gaze_y = int(y)
        for cell in self._get_bento_cells_for_current_floor():
            coords = self._project_cell_to_screen(cell)
            if coords and self._is_gaze_on_cell(coords):
                return cell
        return None

    def navigate_to_floor(self, target_floor: ZFloorLevel, transition: bool = True):
        """
        Navigate to a different Z-floor.

        Args:
            target_floor: Target floor level
            transition: Use smooth transition (True) or instant (False)
        """
        if target_floor == self.current_floor:
            return

        # Set target position
        self.target_position = SpatialPosition(
            x=self.position.x,
            y=self.position.y,
            z=float(target_floor.value),
            fov=self.FOV_DEFAULT
        )

        if transition:
            # Start smooth transition
            self.is_transitioning = True
            self.transition_start_time = time.time()
            self.transition_start_pos = SpatialPosition(
                x=self.position.x,
                y=self.position.y,
                z=self.position.z,
                fov=self.position.fov
            )
        else:
            # Instant jump
            self.position = self.target_position
            self.current_floor = target_floor
            self.transition_progress = 0.0

    def _ease_in_out(self, t: float) -> float:
        """
        Ease-in/out interpolation for smooth motion.

        Args:
            t: Time parameter (0.0-1.0)

        Returns:
            Eased value (0.0-1.0)
        """
        # Cubic ease-in-out
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2

    def _update_camera(self):
        """Update camera position (smooth transitions)"""
        if not self.is_transitioning:
            self.transition_progress = 0.0
            return

        # Calculate transition progress
        elapsed = time.time() - self.transition_start_time
        progress = min(1.0, elapsed / self.TRANSITION_DURATION)
        self.transition_progress = progress

        # Apply easing
        eased_progress = self._ease_in_out(progress)

        # Interpolate position
        self.position.x = self._lerp(
            self.transition_start_pos.x,
            self.target_position.x,
            eased_progress
        )
        self.position.y = self._lerp(
            self.transition_start_pos.y,
            self.target_position.y,
            eased_progress
        )
        self.position.z = self._lerp(
            self.transition_start_pos.z,
            self.target_position.z,
            eased_progress
        )

        # Complete transition
        if progress >= 1.0:
            self.is_transitioning = False
            self.position = self.target_position
            self.transition_progress = 0.0

            # Update current floor
            for floor in ZFloorLevel:
                if abs(floor.value - self.position.z) < 0.1:
                    self.current_floor = floor
                    break

    def _lerp(self, start: float, end: float, t: float) -> float:
        """Linear interpolation"""
        return start + (end - start) * t

    def _get_bento_cells_for_current_floor(self) -> List[BentoCell]:
        """Get Bento cells for current floor"""
        return self.floors.get(self.current_floor, [])

    def _project_cell_to_screen(self, cell: BentoCell) -> Optional[Tuple[int, int, int, int]]:
        """
        Project 3D Bento cell to 2D screen coordinates.

        Uses billboarding and adaptive curvature.

        Args:
            cell: Bento cell to project

        Returns:
            (x1, y1, x2, y2) screen coordinates or None if off-screen
        """
        angle, distance = cell.position

        # Skip if outside FOV
        if angle < self.GRID_ANGLE_MIN or angle > self.GRID_ANGLE_MAX:
            return None

        # Adaptive curvature (1.5m radius arc)
        # Convert angle to screen x position
        angle_rad = math.radians(angle)
        arc_length = self.REACH_ZONE_OPTIMAL * angle_rad

        # Map to screen space (-50° to 50° → 0 to width)
        angle_norm = (angle - self.GRID_ANGLE_MIN) / (self.GRID_ANGLE_MAX - self.GRID_ANGLE_MIN)
        screen_x = int(angle_norm * self.width)

        # Calculate depth-based scale (perspective)
        depth_factor = self.REACH_ZONE_OPTIMAL / max(distance, 0.5)
        scaled_width = int(cell.size[0] * depth_factor)
        scaled_height = int(cell.size[1] * depth_factor)

        # Center on Y-axis
        screen_y = self.height // 2 - scaled_height // 2

        return (
            screen_x - scaled_width // 2,
            screen_y,
            screen_x + scaled_width // 2,
            screen_y + scaled_height
        )

    def _is_gaze_on_cell(self, cell_coords: Tuple[int, int, int, int]) -> bool:
        """Check if gaze is on cell"""
        x1, y1, x2, y2 = cell_coords
        return (x1 <= self.gaze_x <= x2 and y1 <= self.gaze_y <= y2)

    def _render_frame(self):
        """Render current frame"""
        # Clear canvas
        self.canvas.delete('all')

        # Update camera
        self._update_camera()

        # Get cells for current floor
        cells = self._get_bento_cells_for_current_floor()

        # Render each cell
        for cell in cells:
            # Enforce minimum interaction target size (2026 standard)
            w, h = cell.size
            if w < self.CELL_MIN_SIZE or h < self.CELL_MIN_SIZE:
                cell = BentoCell(
                    id=cell.id,
                    label=cell.label,
                    floor=cell.floor,
                    position=cell.position,
                    size=(max(w, self.CELL_MIN_SIZE), max(h, self.CELL_MIN_SIZE)),
                    target_floor=cell.target_floor,
                    callback=cell.callback,
                    icon=cell.icon,
                    color=cell.color
                )

            coords = self._project_cell_to_screen(cell)
            if not coords:
                continue

            x1, y1, x2, y2 = coords
            is_gazed = self._is_gaze_on_cell(coords)

            # Gaze-reactive expansion
            if is_gazed:
                expand = 10
                x1 -= expand
                y1 -= expand
                x2 += expand
                y2 += expand

            # Draw cell background
            cell_color = cell.color
            glow_color = '#00FFFF' if is_gazed else '#1E3A5F'

            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=cell_color,
                outline=glow_color,
                width=3 if is_gazed else 1,
                tags=f'cell_{cell.id}'
            )

            # Parallax occlusion effect (floating icon)
            if cell.icon:
                icon_offset = 5 if is_gazed else 0
                self.canvas.create_text(
                    (x1 + x2) // 2,
                    (y1 + y2) // 2 - icon_offset,
                    text=cell.icon,
                    fill='#FFFFFF',
                    font=('Segoe UI', 24),
                    tags=f'icon_{cell.id}'
                )

            # Cell label
            self.canvas.create_text(
                (x1 + x2) // 2,
                y2 - 20,
                text=cell.label,
                fill='#88CCFF' if is_gazed else '#FFFFFF',
                font=('Segoe UI', 10, 'bold' if is_gazed else 'normal'),
                tags=f'label_{cell.id}'
            )

        # Peripheral dimming during high-speed travel (blindered transition)
        self._render_blinders()

        # Render floor indicator
        self._render_floor_indicator()

    def _render_blinders(self):
        """Render a subtle "blindered" vignette during transitions to reduce discomfort."""
        if not self.is_transitioning:
            return
        progress = self.transition_progress
        if progress <= 0.05 or progress >= 0.95:
            return

        eased = self._ease_in_out(progress)
        strength = 0.25 + (eased * 0.55)
        band = int(min(self.width, self.height) * (0.08 + strength * 0.12))
        stipple = 'gray50' if strength < 0.5 else 'gray25'

        # Top / bottom / left / right bands
        self.canvas.create_rectangle(0, 0, self.width, band, fill='#000000', stipple=stipple, width=0)
        self.canvas.create_rectangle(0, self.height - band, self.width, self.height, fill='#000000', stipple=stipple, width=0)
        self.canvas.create_rectangle(0, 0, band, self.height, fill='#000000', stipple=stipple, width=0)
        self.canvas.create_rectangle(self.width - band, 0, self.width, self.height, fill='#000000', stipple=stipple, width=0)
    def _render_floor_indicator(self):
        """Render current floor indicator"""
        floor_name = self.current_floor.name
        self.canvas.create_text(
            20, 20,
            text=f"Floor: {floor_name} (Z{self.current_floor.value:+d})",
            fill='#00FFFF',
            font=('Segoe UI', 12, 'bold'),
            anchor='nw'
        )

    def _render_loop(self):
        """Main render loop (60 FPS)"""
        self._render_frame()
        self.canvas.after(16, self._render_loop)  # ~60 FPS

    def _on_mouse_move(self, event):
        """Handle mouse movement (gaze simulation)"""
        self.gaze_x = event.x
        self.gaze_y = event.y

    def _on_click(self, event):
        """Handle mouse click (cell selection)"""
        cells = self._get_bento_cells_for_current_floor()

        for cell in cells:
            coords = self._project_cell_to_screen(cell)
            if not coords:
                continue

            if self._is_gaze_on_cell(coords):
                # Cell clicked
                if cell.target_floor:
                    # Portal transition to another floor
                    self.navigate_to_floor(cell.target_floor)
                elif cell.callback:
                    # Execute callback
                    cell.callback()
                break


# Export
__all__ = ['SpatialNavigator', 'ZFloorLevel', 'SpatialPosition', 'BentoCell']
