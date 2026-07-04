#!/usr/bin/env python
"""
Unified Bento Hub - Single Source for All Bento Interface Systems
Consolidates: smart_bento_hub.py, immersive_bento_system.py, universal_bento_system.py
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import tkinter as tk
from tkinter import ttk
import math


class WidgetType(Enum):
    """Standard Bento widget types"""
    STATUS_MONITOR = "status_monitor"
    METRICS_DISPLAY = "metrics_display"
    TASK_QUEUE = "task_queue"
    CONSOLE_OUTPUT = "console_output"
    FILE_BROWSER = "file_browser"
    AI_CHAT = "ai_chat"
    GRAPH_CHART = "graph_chart"
    QUICK_ACTIONS = "quick_actions"
    NOTIFICATIONS = "notifications"
    SYSTEM_INFO = "system_info"
    THEME_MANAGER = "theme_manager"
    WIZARD_LAUNCHER = "wizard_launcher"
    SETTINGS_HUB = "settings_hub"
    ANALYTICS_DASHBOARD = "analytics_dashboard"
    WORKFLOW_DESIGNER = "workflow_designer"
    DOCUMENT_VIEWER = "document_viewer"
    TOOL_BROWSER = "tool_browser"
    THREE_D_VISUALIZER = "3d_visualizer"


class SettingType(Enum):
    """Setting input types"""
    TOGGLE = "toggle"
    SLIDER = "slider"
    DROPDOWN = "dropdown"
    COLOR = "color"
    TEXT = "text"
    NUMBER = "number"
    FONT = "font"


@dataclass
class BentoWidget:
    """
    Bento widget descriptor with 3D positioning

    Attributes:
        type: Widget type identifier
        title: Display title
        floor: Floor that provides this widget
        position: (col, row) in grid
        size: (cols, rows) widget dimensions
        widget_instance: Actual tkinter widget
        resizable: Allow user resizing
        min_size: Minimum (cols, rows)
        offset_3d: (x, y, z) offset in meters for 3D view
        visible: Widget visibility state
        config: Additional configuration
    """
    type: WidgetType
    title: str
    floor: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    widget_instance: Optional[tk.Widget] = None
    resizable: bool = True
    min_size: Tuple[int, int] = (1, 1)
    offset_3d: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    visible: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FloorBentoConfig:
    """
    Configuration for a floor's Bento contributions

    Attributes:
        floor_name: Floor identifier
        widgets: List of widget descriptors
        settings: List of setting descriptors
        default_active_widgets: Widget types active by default
    """
    floor_name: str
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    settings: List[Dict[str, Any]] = field(default_factory=list)
    default_active_widgets: List[str] = field(default_factory=list)


class UnifiedBentoHub:
    """
    Single unified Bento interface system

    Consolidates:
    - smart_bento_hub.py (Settings management, phone notification aesthetic)
    - immersive_bento_system.py (3-step wizard, 3D positioning)
    - universal_bento_system.py (1.5m curved interface, floor aggregation)

    Provides:
    - Unified widget management across all floors
    - Settings hub for all 60+ settings
    - 3D curved interface at 1.5m radius
    - 4 cols × 12 rows grid layout
    - Glassmorphism aesthetic
    - Phone notification shade UI pattern
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.widgets: Dict[str, BentoWidget] = {}
        self.settings: Dict[str, Dict[str, Any]] = {}
        self.floor_configs: Dict[str, FloorBentoConfig] = {}
        self.active_widgets: List[str] = []

        from .base_portal_glass import BentoConstraints
        self.constraints = BentoConstraints()

        self.event_bus = None
        self._load_event_bus()
        self._subscribe_to_events()

    def _load_event_bus(self):
        """Load Event Bus for floor communication"""
        try:
            from core.services import get_event_bus
            self.event_bus = get_event_bus()
        except Exception:
            self.event_bus = None

    def _subscribe_to_events(self):
        """Subscribe to widget and settings registration events"""
        if self.event_bus:
            self.event_bus.subscribe('bento.register_widgets', self._on_register_widgets)
            self.event_bus.subscribe('settings.register_floor', self._on_register_settings)

    def _on_register_widgets(self, data: Dict[str, Any]):
        """Handle widget registration event"""
        floor = data.get('floor')
        widgets = data.get('widgets', [])

        if floor:
            for widget_desc in widgets:
                self.register_widget(floor, widget_desc)

    def _on_register_settings(self, data: Dict[str, Any]):
        """Handle settings registration event"""
        floor = data.get('floor')
        settings = data.get('settings', [])

        if floor:
            for setting in settings:
                key = f"{floor}.{setting['name']}"
                self.settings[key] = setting

    def register_floor(self, config: FloorBentoConfig):
        """
        Register a floor's Bento configuration

        Args:
            config: FloorBentoConfig with widgets and settings
        """
        self.floor_configs[config.floor_name] = config

        for widget_desc in config.widgets:
            self.register_widget(config.floor_name, widget_desc)

        for setting in config.settings:
            key = f"{config.floor_name}.{setting['name']}"
            self.settings[key] = setting

        for widget_type in config.default_active_widgets:
            widget_key = f"{config.floor_name}.{widget_type}"
            if widget_key not in self.active_widgets:
                self.active_widgets.append(widget_key)

    def register_widget(self, floor: str, widget_desc: Dict[str, Any]):
        """
        Register a widget from a floor

        Args:
            floor: Floor name
            widget_desc: Widget descriptor dict
        """
        widget_type_str = widget_desc.get('type', 'STATUS_MONITOR')

        try:
            widget_type = WidgetType(widget_type_str.lower())
        except ValueError:
            widget_type = WidgetType.STATUS_MONITOR

        key = f"{floor}.{widget_type.value}"

        widget = BentoWidget(
            type=widget_type,
            title=widget_desc.get('title', widget_type.value.replace('_', ' ').title()),
            floor=floor,
            position=widget_desc.get('position', (0, 0)),
            size=widget_desc.get('size', (1, 2)),
            resizable=widget_desc.get('resizable', True),
            min_size=widget_desc.get('min_size', (1, 1)),
            config=widget_desc.get('config', {})
        )

        self.widgets[key] = widget

    def create_interface(self, parent) -> tk.Frame:
        """
        Create the unified Bento interface

        Args:
            parent: Parent widget

        Returns:
            Main Bento frame
        """
        main_frame = tk.Frame(
            parent,
            bg=self.constraints.bg
        )

        header = self._create_header(main_frame)
        header.pack(fill='x', pady=(0, 10))

        grid_frame = self._create_grid(main_frame)
        grid_frame.pack(fill='both', expand=True)

        return main_frame

    def _create_header(self, parent) -> tk.Frame:
        """Create Bento Hub header"""
        header = tk.Frame(parent, bg=self.constraints.bg)

        title = tk.Label(
            header,
            text="Bento Hub",
            font=('Arial', 16, 'bold'),
            fg=self.constraints.accent_cyan,
            bg=self.constraints.bg
        )
        title.pack(side='left', padx=10)

        widget_count = tk.Label(
            header,
            text=f"{len(self.widgets)} widgets available",
            font=('Arial', 9),
            fg=self.constraints.text,
            bg=self.constraints.bg
        )
        widget_count.pack(side='left', padx=10)

        return header

    def _create_grid(self, parent) -> tk.Frame:
        """
        Create 4×12 Bento grid

        Returns:
            Grid frame with cells
        """
        grid = tk.Frame(parent, bg=self.constraints.bg)

        for row in range(self.constraints.grid_rows):
            for col in range(self.constraints.grid_cols):
                cell = tk.Frame(
                    grid,
                    bg=self.constraints.panel,
                    bd=1,
                    relief='flat'
                )
                cell.grid(
                    row=row,
                    column=col,
                    padx=2,
                    pady=2,
                    sticky='nsew'
                )

                grid.rowconfigure(row, weight=1)
                grid.columnconfigure(col, weight=1)

        return grid

    def position_widget_3d(
        self,
        widget: BentoWidget,
        camera_position: Tuple[float, float, float],
        camera_rotation: Tuple[float, float, float]
    ) -> Tuple[float, float, float]:
        """
        Calculate 3D position for widget on 1.5m radius sphere

        Args:
            widget: BentoWidget to position
            camera_position: (x, y, z) camera position
            camera_rotation: (pitch, yaw, roll) in radians

        Returns:
            (screen_x, screen_y, depth) position
        """
        radius = self.constraints.radius_3d

        col, row = widget.position
        theta = (col / self.constraints.grid_cols) * 2 * math.pi
        phi = (row / self.constraints.grid_rows) * math.pi

        x = radius * math.sin(phi) * math.cos(theta) + widget.offset_3d[0]
        y = radius * math.cos(phi) + widget.offset_3d[1]
        z = radius * math.sin(phi) * math.sin(theta) + widget.offset_3d[2]

        x -= camera_position[0]
        y -= camera_position[1]
        z -= camera_position[2]

        pitch, yaw, roll = camera_rotation

        x_rot = x * math.cos(yaw) - z * math.sin(yaw)
        z_rot = x * math.sin(yaw) + z * math.cos(yaw)
        y_rot = y * math.cos(pitch) - z_rot * math.sin(pitch)
        z_final = y * math.sin(pitch) + z_rot * math.cos(pitch)

        if z_final <= 0:
            return (0, 0, -1)

        fov = 90
        screen_width = 1920
        screen_height = 1080

        focal_length = screen_width / (2 * math.tan(math.radians(fov) / 2))

        screen_x = (x_rot / z_final) * focal_length + screen_width / 2
        screen_y = (y_rot / z_final) * focal_length + screen_height / 2

        return (screen_x, screen_y, z_final)

    def render_3d_overlay(
        self,
        canvas,
        camera_position: Tuple[float, float, float],
        camera_rotation: Tuple[float, float, float]
    ):
        """
        Render Bento widgets as 3D overlay on canvas

        Args:
            canvas: tkinter Canvas to render on
            camera_position: Camera position
            camera_rotation: Camera rotation
        """
        canvas.delete('bento_widget')

        sorted_widgets = sorted(
            self.active_widgets,
            key=lambda w: self.position_widget_3d(
                self.widgets[w],
                camera_position,
                camera_rotation
            )[2],
            reverse=True
        )

        for widget_key in sorted_widgets:
            widget = self.widgets[widget_key]
            screen_x, screen_y, depth = self.position_widget_3d(
                widget,
                camera_position,
                camera_rotation
            )

            if depth <= 0:
                continue

            scale = 1.0 / max(depth, 0.1)
            width = widget.size[0] * 100 * scale
            height = widget.size[1] * 80 * scale

            canvas.create_rectangle(
                screen_x - width / 2,
                screen_y - height / 2,
                screen_x + width / 2,
                screen_y + height / 2,
                fill=self.constraints.panel,
                outline=self.constraints.border,
                tags='bento_widget'
            )

            canvas.create_text(
                screen_x,
                screen_y,
                text=widget.title,
                fill=self.constraints.text,
                font=('Arial', int(12 * scale)),
                tags='bento_widget'
            )

    def get_widget(self, floor: str, widget_type: str) -> Optional[BentoWidget]:
        """Get widget by floor and type"""
        key = f"{floor}.{widget_type}"
        return self.widgets.get(key)

    def get_widgets_by_floor(self, floor: str) -> List[BentoWidget]:
        """Get all widgets from a floor"""
        return [w for key, w in self.widgets.items() if key.startswith(f"{floor}.")]

    def get_all_widgets(self) -> List[BentoWidget]:
        """Get all registered widgets"""
        return list(self.widgets.values())

    def activate_widget(self, floor: str, widget_type: str):
        """Add widget to active list"""
        key = f"{floor}.{widget_type}"
        if key in self.widgets and key not in self.active_widgets:
            self.active_widgets.append(key)

    def deactivate_widget(self, floor: str, widget_type: str):
        """Remove widget from active list"""
        key = f"{floor}.{widget_type}"
        if key in self.active_widgets:
            self.active_widgets.remove(key)

    def get_setting(self, floor: str, setting_name: str) -> Optional[Any]:
        """Get setting value"""
        key = f"{floor}.{setting_name}"
        setting = self.settings.get(key)
        if setting:
            return setting.get('value', setting.get('default'))
        return None

    def set_setting(self, floor: str, setting_name: str, value: Any):
        """Set setting value"""
        key = f"{floor}.{setting_name}"
        if key in self.settings:
            self.settings[key]['value'] = value

            if self.event_bus:
                self.event_bus.publish(
                    'settings.changed',
                    {
                        'floor': floor,
                        'setting': setting_name,
                        'value': value
                    }
                )

    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get all settings"""
        return self.settings.copy()

    def export_config(self) -> Dict[str, Any]:
        """
        Export complete Bento configuration

        Returns:
            Dict with widgets, settings, and active state
        """
        return {
            'widgets': [
                {
                    'type': w.type.value,
                    'title': w.title,
                    'floor': w.floor,
                    'position': w.position,
                    'size': w.size,
                    'visible': w.visible,
                }
                for w in self.widgets.values()
            ],
            'settings': self.settings,
            'active_widgets': self.active_widgets,
            'constraints': {
                'radius_3d': self.constraints.radius_3d,
                'grid_cols': self.constraints.grid_cols,
                'grid_rows': self.constraints.grid_rows,
            }
        }


def get_bento_hub() -> UnifiedBentoHub:
    """
    Get singleton Bento Hub instance

    Returns:
        UnifiedBentoHub instance
    """
    if not hasattr(get_bento_hub, '_instance'):
        get_bento_hub._instance = UnifiedBentoHub()
    return get_bento_hub._instance
