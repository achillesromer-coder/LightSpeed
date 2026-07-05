"""
LightSpeed V0.9.5 - 3D Breadcrumb Dollhouse Minimap
Visual Z-stack hierarchy navigator

Shows user's current position in multi-level Z-floor structure
Prevents disorientation during floor transitions

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
Date: January 3, 2026
"""

import tkinter as tk
from tkinter import Canvas
from typing import Dict, List
from .spatial_navigator import ZFloorLevel


class DollhouseMinimap:
    """
    3D Dollhouse-style minimap showing Z-floor hierarchy.

    Features:
    - Stacked floor visualization
    - Current position indicator
    - Clickable floor navigation
    - Smooth animations
    - Breadcrumb trail
    """

    FLOOR_HEIGHT = 30  # pixels per floor
    FLOOR_WIDTH = 150
    FLOOR_SPACING = 10

    COLORS = {
        'current': '#00FFFF',
        'visited': '#0088FF',
        'unvisited': '#1E3A5F',
        'bg': '#0A1628',
        'text': '#FFFFFF'
    }

    def __init__(self, canvas: Canvas, navigator, x: int = 20, y: int = 100):
        """
        Initialize dollhouse minimap.

        Args:
            canvas: Tkinter canvas
            navigator: SpatialNavigator instance
            x: X position on canvas
            y: Y position on canvas
        """
        self.canvas = canvas
        self.navigator = navigator
        self.x = x
        self.y = y

        self.visited_floors: List[ZFloorLevel] = [getattr(ZFloorLevel, "SURFACE", ZFloorLevel.CONSTRUCT)]

        # Render initial state
        self.render()

    def render(self):
        """Render minimap"""
        # Clear previous minimap
        self.canvas.delete('minimap')

        # Background
        total_height = len(ZFloorLevel) * (self.FLOOR_HEIGHT + self.FLOOR_SPACING)
        self.canvas.create_rectangle(
            self.x - 10,
            self.y - 10,
            self.x + self.FLOOR_WIDTH + 10,
            self.y + total_height + 10,
            fill=self.COLORS['bg'],
            outline=self.COLORS['current'],
            width=2,
            tags='minimap'
        )

        # Title
        self.canvas.create_text(
            self.x + self.FLOOR_WIDTH // 2,
            self.y - 30,
            text="Z-Floor Navigator",
            fill=self.COLORS['text'],
            font=('Segoe UI', 10, 'bold'),
            tags='minimap'
        )

        # Render each floor
        floors_sorted = sorted(ZFloorLevel, key=lambda f: f.value, reverse=True)

        for i, floor in enumerate(floors_sorted):
            floor_y = self.y + i * (self.FLOOR_HEIGHT + self.FLOOR_SPACING)

            # Determine color
            if floor == self.navigator.current_floor:
                color = self.COLORS['current']
                outline_width = 3
            elif floor in self.visited_floors:
                color = self.COLORS['visited']
                outline_width = 2
            else:
                color = self.COLORS['unvisited']
                outline_width = 1

            # Floor rectangle
            floor_id = f'floor_{floor.name}'
            self.canvas.create_rectangle(
                self.x,
                floor_y,
                self.x + self.FLOOR_WIDTH,
                floor_y + self.FLOOR_HEIGHT,
                fill=color,
                outline='#FFFFFF',
                width=outline_width,
                tags=('minimap', floor_id)
            )

            # Floor label
            if floor == getattr(ZFloorLevel, "SURFACE", None):
                label = "SURFACE"
            elif floor == getattr(ZFloorLevel, "FIRSTRUN", None):
                label = "FIRSTRUN"
            else:
                label = f"{floor.name} (Z{floor.value:+d})"
            self.canvas.create_text(
                self.x + self.FLOOR_WIDTH // 2,
                floor_y + self.FLOOR_HEIGHT // 2,
                text=label,
                fill='#FFFFFF' if floor == self.navigator.current_floor else '#88CCFF',
                font=('Segoe UI', 8, 'bold' if floor == self.navigator.current_floor else 'normal'),
                tags=('minimap', floor_id)
            )

            # Click binding
            self.canvas.tag_bind(floor_id, '<Button-1>',
                               lambda e, f=floor: self._on_floor_click(f))

    def _on_floor_click(self, floor: ZFloorLevel):
        """Handle floor click in minimap"""
        self.navigator.navigate_to_floor(floor)

        if floor not in self.visited_floors:
            self.visited_floors.append(floor)

        self.render()

    def update(self):
        """Update minimap (call periodically)"""
        current = self.navigator.current_floor
        if current not in self.visited_floors:
            self.visited_floors.append(current)

        self.render()


__all__ = ['DollhouseMinimap']
