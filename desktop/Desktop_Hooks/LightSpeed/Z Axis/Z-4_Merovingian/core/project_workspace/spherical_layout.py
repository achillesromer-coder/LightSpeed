"""
Spherical Layout Manager - v5.1.2
Equirectangular workspace layout bridge for Construct project workspaces.

Uses the compact `core.ui.spherical_ui` compatibility bridge for workspace
component positioning without restoring the old standalone spherical UI stack.

Author: LightSpeed Team
Date: April 8, 2026
"""

import tkinter as tk
from typing import Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass

# Import the compact Merovingian UI compatibility bridge.
from core.ui.spherical_ui import EquirectangularUI, Widget3D

# Import workspace models
from .workspace_creator import (
    WorkspaceComponent,
    SphericalPosition,
    ProjectWorkspace
)
from .category_positions import CATEGORY_DEFAULT_POSITIONS, get_category_default_position


# ==============================================================================
# Layout Modes
# ==============================================================================

class LayoutMode:
    """Layout mode configurations"""
    STANDARD_GRID = "standard_grid"  # 8x6 default
    COMPACT_VIEW = "compact_view"    # 12x8 more dense
    FULLSCREEN_FOCUS = "fullscreen"  # Single component maximized
    MULTI_WORKSPACE = "multi_workspace"  # Split view

    @staticmethod
    def get_grid_size(mode: str) -> Tuple[int, int]:
        """Get grid dimensions for layout mode"""
        return {
            LayoutMode.STANDARD_GRID: (8, 6),
            LayoutMode.COMPACT_VIEW: (12, 8),
            LayoutMode.FULLSCREEN_FOCUS: (1, 1),
            LayoutMode.MULTI_WORKSPACE: (16, 8)
        }.get(mode, (8, 6))


# ==============================================================================
# Category-Based Positioning
# ==============================================================================

# ==============================================================================
# Workspace Spherical Layout Manager
# ==============================================================================

class WorkspaceSphericalLayout:
    """
    Manages spherical layout for project workspaces

    Extends EquirectangularUI with workspace-specific features:
    - Component management
    - Automatic positioning
    - Interaction handling
    - Save/load layout state
    """

    def __init__(
        self,
        parent: tk.Widget,
        workspace: ProjectWorkspace,
        on_component_click: Optional[Callable[[WorkspaceComponent], None]] = None,
        on_component_config: Optional[Callable[[WorkspaceComponent], None]] = None
    ):
        """
        Initialize workspace spherical layout

        Args:
            parent: Parent Tkinter widget
            workspace: Project workspace
            on_component_click: Callback when component is clicked
            on_component_config: Callback when component config is requested
        """
        self.parent = parent
        self.workspace = workspace
        self.on_component_click = on_component_click
        self.on_component_config = on_component_config

        # Component widgets mapping
        self.component_widgets: Dict[str, Widget3D] = {}

        # Layout mode
        self.layout_mode = LayoutMode.STANDARD_GRID

        # Initialize base spherical UI
        layout_config = workspace.spherical_layout
        self.spherical_ui = EquirectangularUI(
            parent=parent,
            fov=layout_config.fov,
            grid_width=layout_config.grid_width,
            grid_height=layout_config.grid_height,
            bg_color=layout_config.background_color
        )

        # Apply saved camera state
        self.spherical_ui.camera_angle = layout_config.camera_angle
        self.spherical_ui.camera_tilt = layout_config.camera_tilt
        self.spherical_ui.camera_zoom = layout_config.camera_zoom

        # Load workspace components into spherical space
        self._load_workspace_components()

        # Bind component interactions
        self._setup_interactions()

    def _load_workspace_components(self):
        """Load all workspace components into spherical layout"""
        for component in self.workspace.components:
            if component.visible:
                self.add_component(component)

    def add_component(self, component: WorkspaceComponent):
        """
        Add component to spherical layout

        Args:
            component: Workspace component to add
        """
        # Create widget representation
        # Note: In full implementation, this would load the actual component widget
        # For now, we create a placeholder widget
        widget = tk.Frame(self.parent, bg='#00d4ff', width=100, height=80)
        label = tk.Label(
            widget,
            text=component.component_name,
            bg='#00d4ff',
            fg='white',
            font=('Arial', 9, 'bold'),
            wraplength=90
        )
        label.pack(expand=True)

        # Add to spherical UI
        pos = component.position
        self.spherical_ui.add_widget_3d(
            widget_id=component.component_id,
            widget=widget,
            theta=pos.theta,
            phi=pos.phi,
            depth=pos.depth
        )

        # Store mapping
        self.component_widgets[component.component_id] = Widget3D(
            id=component.component_id,
            widget=widget,
            theta=pos.theta,
            phi=pos.phi,
            depth=pos.depth,
            visible=True
        )

    def remove_component(self, component_id: str):
        """Remove component from layout"""
        if component_id in self.component_widgets:
            self.spherical_ui.remove_widget_3d(component_id)
            del self.component_widgets[component_id]

    def update_component_position(
        self,
        component_id: str,
        position: SphericalPosition
    ):
        """Update component position in spherical space"""
        if component_id in self.component_widgets:
            widget_3d = self.component_widgets[component_id]
            widget_3d.theta = position.theta
            widget_3d.phi = position.phi
            widget_3d.depth = position.depth

            # Update in workspace
            for component in self.workspace.components:
                if component.component_id == component_id:
                    component.position = position
                    break

            self.spherical_ui.render()

    def set_layout_mode(self, mode: str):
        """
        Change layout mode

        Args:
            mode: Layout mode (from LayoutMode constants)
        """
        self.layout_mode = mode
        grid_width, grid_height = LayoutMode.get_grid_size(mode)

        # Update spherical UI grid
        self.spherical_ui.grid_width = grid_width
        self.spherical_ui.grid_height = grid_height
        self.spherical_ui.create_grid()
        self.spherical_ui.render()

        # Update workspace config
        self.workspace.spherical_layout.grid_width = grid_width
        self.workspace.spherical_layout.grid_height = grid_height

    def auto_arrange_components(self, strategy: str = "category"):
        """
        Automatically arrange components

        Args:
            strategy: Arrangement strategy ('category', 'z_floor', 'circular')
        """
        if strategy == "category":
            self._arrange_by_category()
        elif strategy == "z_floor":
            self._arrange_by_z_floor()
        elif strategy == "circular":
            self._arrange_circular()

    def _arrange_by_category(self):
        """Arrange components based on category defaults"""
        for component in self.workspace.components:
            if component.category in CATEGORY_DEFAULT_POSITIONS:
                default_pos = get_category_default_position(component.category)
                self.update_component_position(component.component_id, default_pos)

    def _arrange_by_z_floor(self):
        """Arrange components by Z-floor (floors stacked vertically)"""
        # Z-floors from bottom to top
        z_floors = [
            'Z-4_Merovingian', 'Z-3_Smith', 'Z-2_Oracle', 'Z-1_Morpheus',
            'Z0_TheConstruct', 'Z+1_Architect', 'Z+2_Neo', 'Z+3_Trinity'
        ]

        # Calculate vertical spacing
        phi_min, phi_max = -60, 60
        phi_step = (phi_max - phi_min) / len(z_floors)

        # Group components by floor
        floor_components = {}
        for component in self.workspace.components:
            floor = component.z_floor
            if floor not in floor_components:
                floor_components[floor] = []
            floor_components[floor].append(component)

        # Position components
        for i, floor in enumerate(z_floors):
            if floor not in floor_components:
                continue

            phi = phi_min + (i * phi_step)
            components = floor_components[floor]

            # Distribute horizontally
            theta_step = 360 / max(len(components), 1)

            for j, component in enumerate(components):
                theta = j * theta_step
                depth = 0.7 + (j % 3) * 0.05
                position = SphericalPosition(theta, phi, depth)
                self.update_component_position(component.component_id, position)

    def _arrange_circular(self):
        """Arrange components in circular pattern around equator"""
        component_count = len(self.workspace.components)
        if component_count == 0:
            return

        theta_step = 360 / component_count

        for i, component in enumerate(self.workspace.components):
            theta = i * theta_step
            phi = 0  # Keep on equator
            depth = 0.7 + (i % 5) * 0.04  # Slight depth variation
            position = SphericalPosition(theta, phi, depth)
            self.update_component_position(component.component_id, position)

    def focus_component(self, component_id: str):
        """Focus camera on specific component"""
        if component_id in self.component_widgets:
            widget_3d = self.component_widgets[component_id]
            # Pan camera to component
            self.spherical_ui.pan_camera(widget_3d.theta - self.spherical_ui.camera_angle)
            self.spherical_ui.camera_tilt = widget_3d.phi

    def save_layout_state(self):
        """Save current layout state to workspace"""
        self.workspace.spherical_layout.camera_angle = self.spherical_ui.camera_angle
        self.workspace.spherical_layout.camera_tilt = self.spherical_ui.camera_tilt
        self.workspace.spherical_layout.camera_zoom = self.spherical_ui.camera_zoom
        self.workspace.spherical_layout.fov = self.spherical_ui.fov

        # Save component positions
        for component in self.workspace.components:
            if component.component_id in self.component_widgets:
                widget_3d = self.component_widgets[component.component_id]
                component.position = SphericalPosition(
                    theta=widget_3d.theta,
                    phi=widget_3d.phi,
                    depth=widget_3d.depth
                )

    def _setup_interactions(self):
        """Setup component interaction handlers"""
        # Bind canvas clicks to component selection
        self.spherical_ui.canvas.bind('<Button-1>', self._on_canvas_click)
        self.spherical_ui.canvas.bind('<Double-Button-1>', self._on_canvas_double_click)
        self.spherical_ui.canvas.bind('<Button-3>', self._on_canvas_right_click)

    def _on_canvas_click(self, event):
        """Handle canvas click (select component)"""
        # Find component at click position
        component_id = self._find_component_at_position(event.x, event.y)

        if component_id and self.on_component_click:
            component = self._get_component_by_id(component_id)
            if component:
                self.on_component_click(component)

    def _on_canvas_double_click(self, event):
        """Handle canvas double-click (focus on component)"""
        component_id = self._find_component_at_position(event.x, event.y)

        if component_id:
            self.focus_component(component_id)

    def _on_canvas_right_click(self, event):
        """Handle canvas right-click (component config menu)"""
        component_id = self._find_component_at_position(event.x, event.y)

        if component_id and self.on_component_config:
            component = self._get_component_by_id(component_id)
            if component:
                self.on_component_config(component)

    def _find_component_at_position(self, x: int, y: int) -> Optional[str]:
        """Find component at canvas position"""
        # Simple proximity check to canvas items
        # In full implementation, this would use canvas.find_closest()
        # and check if it's a component widget

        canvas = self.spherical_ui.canvas
        items = canvas.find_overlapping(x-5, y-5, x+5, y+5)

        for item in items:
            tags = canvas.gettags(item)
            for tag in tags:
                if tag in self.component_widgets:
                    return tag

        return None

    def _get_component_by_id(self, component_id: str) -> Optional[WorkspaceComponent]:
        """Get workspace component by ID"""
        for component in self.workspace.components:
            if component.component_id == component_id:
                return component
        return None

    def get_frame(self) -> tk.Frame:
        """Get the main frame"""
        return self.spherical_ui.get_frame()


# ==============================================================================
# Layout Presets
# ==============================================================================

class LayoutPreset:
    """Pre-configured layout presets"""

    @staticmethod
    def research_layout() -> Dict[str, Any]:
        """Research workspace layout preset"""
        return {
            'layout_mode': LayoutMode.STANDARD_GRID,
            'fov': 70.0,
            'grid': (8, 6),
            'arrangement': 'category',
            'focused_categories': ['ai_intelligence', 'knowledge_discovery']
        }

    @staticmethod
    def engineering_layout() -> Dict[str, Any]:
        """Engineering workspace layout preset"""
        return {
            'layout_mode': LayoutMode.COMPACT_VIEW,
            'fov': 80.0,
            'grid': (10, 6),
            'arrangement': 'category',
            'focused_categories': ['simulation_physics', 'ui_visualization']
        }

    @staticmethod
    def simulation_layout() -> Dict[str, Any]:
        """Simulation workspace layout preset"""
        return {
            'layout_mode': LayoutMode.FULLSCREEN_FOCUS,
            'fov': 90.0,
            'grid': (12, 8),
            'arrangement': 'z_floor',
            'focused_categories': ['simulation_physics']
        }

    @staticmethod
    def collaboration_layout() -> Dict[str, Any]:
        """Collaboration workspace layout preset"""
        return {
            'layout_mode': LayoutMode.MULTI_WORKSPACE,
            'fov': 70.0,
            'grid': (16, 8),
            'arrangement': 'circular',
            'focused_categories': ['planning_goals', 'automation']
        }


# ==============================================================================
# Convenience Functions
# ==============================================================================

def create_workspace_layout(
    parent: tk.Widget,
    workspace: ProjectWorkspace,
    preset: Optional[str] = None
) -> WorkspaceSphericalLayout:
    """
    Create workspace spherical layout

    Args:
        parent: Parent widget
        workspace: Project workspace
        preset: Optional preset name ('research', 'engineering', etc.)

    Returns:
        WorkspaceSphericalLayout instance
    """
    layout = WorkspaceSphericalLayout(parent, workspace)

    if preset:
        preset_configs = {
            'research': LayoutPreset.research_layout(),
            'engineering': LayoutPreset.engineering_layout(),
            'simulation': LayoutPreset.simulation_layout(),
            'collaboration': LayoutPreset.collaboration_layout()
        }

        if preset in preset_configs:
            config = preset_configs[preset]
            layout.set_layout_mode(config['layout_mode'])
            layout.auto_arrange_components(config['arrangement'])

    return layout
