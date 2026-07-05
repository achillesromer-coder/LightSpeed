"""
LightSpeed V0.9.11 - Enhanced Curved Bento Grid System
1.5m radius locked curvature with glass morphism and dynamic tile management

Features:
- 1.5m radius curved surface (locked)
- Smooth edge transitions
- Glass thickness variation by depth
- "Add New" wizard integration
- Dynamic tile creation/removal
- Project flowchart visualization (Y-axis)
- Real-time depth perception

Author: LightSpeed Team / ACHILLES
Version: 0.9.11
Date: January 3, 2026
"""

import tkinter as tk
from tkinter import ttk
import math
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class TileType(Enum):
    """Types of Bento tiles that can be created"""
    WIDGET = "widget"
    TASK = "task"
    TOOL = "tool"
    DATASET = "dataset"
    VENV = "venv"
    FUNCTION = "function"
    PARAMETER = "parameter"
    FOLDER = "folder"
    FLOW_NODE = "flow_node"
    PORTAL = "portal"


@dataclass
class BentoTile:
    """Enhanced Bento tile with 3D depth properties"""
    id: str
    type: TileType
    label: str
    position: Tuple[float, float, float]  # (angle, distance, y_offset)
    size: Tuple[int, int]  # (width, height)
    depth: float = 0.0  # Z-depth for glass thickness (0.0 to 1.0)
    color: str = "#102040"
    edge_color: str = "#00FFFF"
    glass_alpha: float = 0.85  # Transparency
    callback: Optional[Callable] = None
    data: Dict[str, Any] = None
    parent_tile: Optional[str] = None  # For flowchart hierarchy
    children: List[str] = None  # Child tiles in flowchart

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.children is None:
            self.children = []


class EnhancedBentoGrid:
    """
    Enhanced curved Bento grid with 1.5m radius and glass morphism.

    Key features:
    - Locked 1.5m radius curvature
    - Smooth edge transitions (cubic bezier)
    - Glass thickness varies with depth
    - Dynamic tile creation
    - Flowchart visualization
    """

    # Constants (2026 Spatial UI Standards)
    RADIUS = 1.5  # meters (LOCKED)
    FOV_MIN = -50.0  # degrees
    FOV_MAX = 50.0  # degrees
    CURVE_SMOOTHING = 0.92  # Smooth edge factor
    GLASS_THICKNESS_MIN = 2  # pixels
    GLASS_THICKNESS_MAX = 8  # pixels
    EDGE_GLOW_RADIUS = 3  # pixels

    # Glass morphism colors
    GLASS_BASE = "#0A1628"
    GLASS_HIGHLIGHT = "#1E3A5F"
    GLASS_SHADOW = "#050B14"

    def __init__(self, canvas: tk.Canvas, width: int, height: int):
        """
        Initialize enhanced Bento grid.

        Args:
            canvas: Tkinter canvas for rendering
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        self.canvas = canvas
        self.width = width
        self.height = height

        self.tiles: Dict[str, BentoTile] = {}
        self.tile_widgets: Dict[str, int] = {}  # tile_id -> canvas item ID

        # Camera/view parameters
        self.camera_y_offset = 0.0  # Vertical scroll for flowcharts
        self.zoom_level = 1.0

        # Interaction state
        self.hovered_tile: Optional[str] = None
        self.selected_tile: Optional[str] = None

    def add_tile(self, tile: BentoTile):
        """Add a tile to the grid"""
        self.tiles[tile.id] = tile
        self._render_tile(tile)

    def remove_tile(self, tile_id: str):
        """Remove a tile from the grid"""
        if tile_id in self.tiles:
            # Remove from canvas
            if tile_id in self.tile_widgets:
                self.canvas.delete(self.tile_widgets[tile_id])
                del self.tile_widgets[tile_id]

            # Remove from data structure
            tile = self.tiles[tile_id]

            # Update parent's children list
            if tile.parent_tile and tile.parent_tile in self.tiles:
                parent = self.tiles[tile.parent_tile]
                if tile_id in parent.children:
                    parent.children.remove(tile_id)

            del self.tiles[tile_id]

    def project_to_screen(self, angle: float, distance: float, y_offset: float = 0.0) -> Optional[Tuple[int, int, float]]:
        """
        Project 3D curved position to 2D screen coordinates.

        Args:
            angle: Horizontal angle in degrees (-50 to 50)
            distance: Distance from viewer in meters
            y_offset: Vertical offset in meters

        Returns:
            (screen_x, screen_y, depth_factor) or None if out of view
        """
        # Check FOV bounds
        if angle < self.FOV_MIN or angle > self.FOV_MAX:
            return None

        # Convert angle to radians
        angle_rad = math.radians(angle)

        # Calculate arc position on 1.5m radius sphere
        arc_x = self.RADIUS * math.sin(angle_rad)
        arc_z = self.RADIUS * (1.0 - math.cos(angle_rad))  # Forward displacement

        # Apply distance (depth perception)
        effective_distance = distance + arc_z

        # Perspective projection
        if effective_distance <= 0.1:
            effective_distance = 0.1  # Prevent division by zero

        # Screen mapping
        # Normalize angle to 0-1 range
        angle_norm = (angle - self.FOV_MIN) / (self.FOV_MAX - self.FOV_MIN)

        # Apply cubic smoothing for edge transitions
        if angle_norm < 0.1:
            # Smooth left edge
            t = angle_norm / 0.1
            angle_norm = self._cubic_ease_in(t) * 0.1
        elif angle_norm > 0.9:
            # Smooth right edge
            t = (angle_norm - 0.9) / 0.1
            angle_norm = 0.9 + self._cubic_ease_out(t) * 0.1

        screen_x = int(angle_norm * self.width)

        # Vertical position with perspective
        y_pixels = y_offset * 200  # meters to pixels (rough scale)
        y_perspective = y_pixels / effective_distance
        screen_y = int(self.height / 2 + y_perspective - self.camera_y_offset)

        # Depth factor for scaling/glass thickness (0.0 = far, 1.0 = near)
        depth_factor = 1.0 / effective_distance
        depth_factor = max(0.0, min(1.0, depth_factor))

        return (screen_x, screen_y, depth_factor)

    def _cubic_ease_in(self, t: float) -> float:
        """Cubic ease-in for smooth edges"""
        return t * t * t

    def _cubic_ease_out(self, t: float) -> float:
        """Cubic ease-out for smooth edges"""
        return 1 - pow(1 - t, 3)

    def _render_tile(self, tile: BentoTile):
        """Render a single tile with glass morphism"""
        angle, distance, y_offset = tile.position

        # Project to screen
        projection = self.project_to_screen(angle, distance, y_offset)
        if not projection:
            return  # Out of view

        screen_x, screen_y, depth_factor = projection

        # Calculate size with perspective scaling
        base_width, base_height = tile.size
        scale = depth_factor * self.zoom_level
        width = int(base_width * scale)
        height = int(base_height * scale)

        # Calculate glass thickness based on depth
        glass_thickness = int(
            self.GLASS_THICKNESS_MIN +
            (self.GLASS_THICKNESS_MAX - self.GLASS_THICKNESS_MIN) * (tile.depth + depth_factor * 0.3)
        )

        # Tile bounds
        x1 = screen_x - width // 2
        y1 = screen_y - height // 2
        x2 = screen_x + width // 2
        y2 = screen_y + height // 2

        # Layer 1: Shadow (back layer)
        shadow_offset = glass_thickness
        shadow_id = self.canvas.create_rectangle(
            x1 + shadow_offset, y1 + shadow_offset,
            x2 + shadow_offset, y2 + shadow_offset,
            fill=self.GLASS_SHADOW,
            outline='',
            tags=(tile.id, 'tile', 'shadow')
        )

        # Layer 2: Base glass
        base_id = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=tile.color,
            outline='',
            tags=(tile.id, 'tile', 'base')
        )

        # Layer 3: Glass highlight (top-left)
        highlight_id = self.canvas.create_rectangle(
            x1, y1,
            x1 + width // 3, y1 + height // 3,
            fill=self.GLASS_HIGHLIGHT,
            outline='',
            stipple='gray50',
            tags=(tile.id, 'tile', 'highlight')
        )

        # Layer 4: Edge glow
        edge_id = self.canvas.create_rectangle(
            x1 - self.EDGE_GLOW_RADIUS, y1 - self.EDGE_GLOW_RADIUS,
            x2 + self.EDGE_GLOW_RADIUS, y2 + self.EDGE_GLOW_RADIUS,
            fill='',
            outline=tile.edge_color,
            width=2,
            tags=(tile.id, 'tile', 'edge')
        )

        # Layer 5: Label
        label_id = self.canvas.create_text(
            screen_x, screen_y,
            text=tile.label,
            fill='#FFFFFF',
            font=('Segoe UI', int(10 * scale), 'bold'),
            tags=(tile.id, 'tile', 'label')
        )

        # Layer 6: Type indicator (icon)
        icon = self._get_tile_icon(tile.type)
        icon_id = self.canvas.create_text(
            screen_x, screen_y - height // 3,
            text=icon,
            fill=tile.edge_color,
            font=('Segoe UI', int(16 * scale)),
            tags=(tile.id, 'tile', 'icon')
        )

        # Store canvas item ID (use base for primary reference)
        self.tile_widgets[tile.id] = base_id

        # Bind interactions
        for tag_id in [shadow_id, base_id, highlight_id, edge_id, label_id, icon_id]:
            self.canvas.tag_bind(tag_id, '<Button-1>', lambda e, t=tile: self._on_tile_click(t))
            self.canvas.tag_bind(tag_id, '<Enter>', lambda e, t=tile: self._on_tile_hover(t))
            self.canvas.tag_bind(tag_id, '<Leave>', lambda e: self._on_tile_unhover())

    def _get_tile_icon(self, tile_type: TileType) -> str:
        """Get icon for tile type"""
        icons = {
            TileType.WIDGET: '📊',
            TileType.TASK: '✓',
            TileType.TOOL: '🔧',
            TileType.DATASET: '📁',
            TileType.VENV: '🐍',
            TileType.FUNCTION: 'ƒ',
            TileType.PARAMETER: '⚙',
            TileType.FOLDER: '📂',
            TileType.FLOW_NODE: '⬡',
            TileType.PORTAL: '🌀',
        }
        return icons.get(tile_type, '⬢')

    def _on_tile_click(self, tile: BentoTile):
        """Handle tile click"""
        self.selected_tile = tile.id

        if tile.callback:
            tile.callback(tile)

        # Visual feedback - brighten edge
        self.canvas.itemconfig(f"{tile.id}&&edge", outline='#00FFFF', width=3)

    def _on_tile_hover(self, tile: BentoTile):
        """Handle tile hover"""
        self.hovered_tile = tile.id

        # Glow effect
        self.canvas.itemconfig(f"{tile.id}&&edge", width=3)

    def _on_tile_unhover(self):
        """Handle tile unhover"""
        if self.hovered_tile and self.hovered_tile != self.selected_tile:
            self.canvas.itemconfig(f"{self.hovered_tile}&&edge", width=2)

        self.hovered_tile = None

    def render_flowchart_connections(self):
        """Render connection lines between parent/child tiles (flowchart)"""
        # Clear existing connections
        self.canvas.delete('connection')

        for tile_id, tile in self.tiles.items():
            if tile.parent_tile and tile.parent_tile in self.tiles:
                parent = self.tiles[tile.parent_tile]

                # Get screen positions
                parent_proj = self.project_to_screen(*parent.position)
                child_proj = self.project_to_screen(*tile.position)

                if parent_proj and child_proj:
                    px, py, _ = parent_proj
                    cx, cy, _ = child_proj

                    # Draw curved connection
                    mid_x = (px + cx) // 2
                    mid_y = (py + cy) // 2 + 30  # Curve downward

                    self.canvas.create_line(
                        px, py, mid_x, mid_y, cx, cy,
                        fill='#00FFFF',
                        width=2,
                        smooth=True,
                        tags='connection'
                    )

                    # Arrow at child
                    self.canvas.create_polygon(
                        cx, cy - 5,
                        cx - 5, cy - 10,
                        cx + 5, cy - 10,
                        fill='#00FFFF',
                        outline='',
                        tags='connection'
                    )

    def scroll_y(self, delta: float):
        """Scroll vertically (for flowcharts)"""
        self.camera_y_offset += delta
        self.refresh()

    def refresh(self):
        """Re-render all tiles"""
        self.canvas.delete('tile')
        self.tile_widgets.clear()

        for tile in self.tiles.values():
            self._render_tile(tile)

        self.render_flowchart_connections()


# Export
__all__ = ['EnhancedBentoGrid', 'BentoTile', 'TileType']
