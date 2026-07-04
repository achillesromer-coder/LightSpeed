"""
LightSpeed V0.9.11 - Spatial UI Integration Module
Complete integration of enhanced Bento grid, wizard, environment, and flowchart

Features:
- Unified spatial UI manager
- All components working together
- Z-floor navigation integration
- Settings persistence
- Demo/test mode

Author: LightSpeed Team / ACHILLES
Version: 0.9.11
Date: January 4, 2026
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any
from pathlib import Path
import json

from .enhanced_bento_grid import EnhancedBentoGrid, BentoTile, TileType
from .add_new_wizard import AddNewWizard
from .environment_renderer import EnvironmentRenderer
from .flowchart_visualizer import FlowchartVisualizer
from core.config.paths import (
    TRINITY_SETTINGS, LIGHTSPEED_ROOT, Z_AXIS_ROOT,
    NEO_ROOT, MORPHEUS_ROOT, ARCHITECT_ROOT, CONSTRUCT_ROOT,
    ORACLE_ROOT, SMITH_ROOT, MEROVINGIAN_ROOT, TRINITY_ROOT
)


class SpatialUIManager:
    """
    Unified manager for complete spatial UI system.

    Integrates:
    - Enhanced Bento Grid (1.5m curved)
    - Add New Wizard (Ollama-powered)
    - Environment Renderer (3D backgrounds)
    - Flowchart Visualizer (Y-axis layout)
    - Z-floor navigation
    """

    # Z-floor definitions
    Z_FLOORS = {
        "Z+3_Trinity": {"path": TRINITY_ROOT, "color": "#00FFFF", "name": "Trinity"},
        "Z+2_Neo": {"path": NEO_ROOT, "color": "#FF0080", "name": "Neo"},
        "Z+1_Architect": {"path": ARCHITECT_ROOT, "color": "#00FF80", "name": "Architect"},
        "Z0_TheConstruct": {"path": CONSTRUCT_ROOT, "color": "#FFFF00", "name": "TheConstruct"},
        "Z-1_Morpheus": {"path": MORPHEUS_ROOT, "color": "#0080FF", "name": "Morpheus"},
        "Z-2_Oracle": {"path": ORACLE_ROOT, "color": "#FF8000", "name": "Oracle"},
        "Z-3_Smith": {"path": SMITH_ROOT, "color": "#8000FF", "name": "Smith"},
        "Z-4_Merovingian": {"path": MEROVINGIAN_ROOT, "color": "#FF0000", "name": "Merovingian"},
    }

    # Backward-compatible aliases (legacy floor IDs appear in older docs/configs)
    _LEGACY_FLOOR_ALIASES = {
        "Z+3_Neo": "Z+2_Neo",
        "Z+2_Morpheus": "Z-1_Morpheus",
        "Z-1_Oracle": "Z-2_Oracle",
        "Z-2_Smith": "Z-3_Smith",
        "Z-3_Merovingian": "Z-4_Merovingian",
        "Z-4_Trinity": "Z+3_Trinity",
    }
    for _legacy_id, _canonical_id in _LEGACY_FLOOR_ALIASES.items():
        if _canonical_id in Z_FLOORS:
            Z_FLOORS.setdefault(_legacy_id, Z_FLOORS[_canonical_id])

    def __init__(self, master: tk.Tk):
        """
        Initialize spatial UI manager.

        Args:
            master: Root Tkinter window
        """
        self.master = master
        self.master.title("LightSpeed V0.9.11 - Spatial UI")
        self.master.geometry("1400x900")
        self.master.configure(bg='#000000')

        # Current state
        self.current_floor = "Z0_TheConstruct"

        # Create UI
        self._create_ui()

        # Initialize components
        self.grid = EnhancedBentoGrid(self.canvas, self.canvas_width, self.canvas_height)
        self.environment = EnvironmentRenderer(self.canvas, self.canvas_width, self.canvas_height)
        self.flowchart = FlowchartVisualizer(self.grid)

        # Load settings
        self._load_settings()

        # Initial render
        self._change_floor(self.current_floor)

    def _create_ui(self):
        """Create main UI layout"""
        # Top toolbar
        toolbar = tk.Frame(self.master, bg='#0A1628', height=60)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Title
        title = tk.Label(
            toolbar,
            text="LightSpeed Spatial UI - V0.9.11",
            font=('Segoe UI', 16, 'bold'),
            bg='#0A1628',
            fg='#00FFFF'
        )
        title.pack(side=tk.LEFT, padx=20, pady=10)

        # Floor selector
        tk.Label(
            toolbar,
            text="Z-Floor:",
            font=('Segoe UI', 10),
            bg='#0A1628',
            fg='#FFFFFF'
        ).pack(side=tk.LEFT, padx=5)

        self.floor_var = tk.StringVar(value=self.current_floor)
        floor_menu = ttk.Combobox(
            toolbar,
            textvariable=self.floor_var,
            values=list(self.Z_FLOORS.keys()),
            state='readonly',
            width=20
        )
        floor_menu.pack(side=tk.LEFT, padx=5)
        floor_menu.bind('<<ComboboxSelected>>', lambda e: self._change_floor(self.floor_var.get()))

        # Add New button
        add_btn = tk.Button(
            toolbar,
            text="+ Add New Tile",
            command=self._open_wizard,
            bg='#00FFFF',
            fg='#000000',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        add_btn.pack(side=tk.LEFT, padx=10)

        # Load Environment button
        env_btn = tk.Button(
            toolbar,
            text="Load Environment",
            command=self._load_environment_image,
            bg='#1E3A5F',
            fg='#FFFFFF',
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        env_btn.pack(side=tk.LEFT, padx=5)

        # Show Flowchart button
        flow_btn = tk.Button(
            toolbar,
            text="Show Flowchart",
            command=self._show_flowchart,
            bg='#1E3A5F',
            fg='#FFFFFF',
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        flow_btn.pack(side=tk.LEFT, padx=5)

        # Settings button
        settings_btn = tk.Button(
            toolbar,
            text="Settings",
            command=self._open_settings,
            bg='#1E3A5F',
            fg='#FFFFFF',
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        settings_btn.pack(side=tk.RIGHT, padx=20)

        # Main canvas
        self.canvas_width = 1400
        self.canvas_height = 840

        self.canvas = tk.Canvas(
            self.master,
            width=self.canvas_width,
            height=self.canvas_height,
            bg='#000000',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Mouse controls
        self.canvas.bind('<MouseWheel>', self._on_scroll)
        self.canvas.bind('<Button-4>', self._on_scroll)  # Linux scroll up
        self.canvas.bind('<Button-5>', self._on_scroll)  # Linux scroll down

        # Status bar
        status_bar = tk.Frame(self.master, bg='#0A1628', height=30)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = tk.Label(
            status_bar,
            text="Ready",
            font=('Segoe UI', 9),
            bg='#0A1628',
            fg='#AAAAAA',
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

    def _change_floor(self, floor_name: str):
        """Change to different Z-floor"""
        if floor_name not in self.Z_FLOORS:
            return

        self.current_floor = floor_name
        floor_info = self.Z_FLOORS[floor_name]

        # Update status
        self.status_label.config(text=f"Floor: {floor_info['name']} ({floor_name})")

        # Clear existing tiles
        self.grid.tiles.clear()
        self.grid.refresh()

        # Load floor-specific content (placeholder - would load from saved state)
        self._load_floor_content(floor_name)

        print(f"[SPATIAL] Changed to floor: {floor_name}")

    def _load_floor_content(self, floor_name: str):
        """Load content for specific floor"""
        # This is a placeholder - in production, would load saved tiles
        # For now, create some demo tiles

        floor_info = self.Z_FLOORS[floor_name]

        # Create welcome tile
        welcome_tile = BentoTile(
            id=f"{floor_name}_welcome",
            type=TileType.PORTAL,
            label=f"Welcome to {floor_info['name']}",
            position=(0.0, 1.5, 0.0),
            size=(250, 150),
            depth=0.8,
            edge_color=floor_info['color']
        )
        self.grid.add_tile(welcome_tile)

        # Render
        self.grid.refresh()

    def _open_wizard(self):
        """Open Add New wizard"""
        wizard_window = tk.Toplevel(self.master)
        wizard = AddNewWizard(
            parent=wizard_window,
            current_floor=self.current_floor,
            on_complete=self._on_tile_created
        )

        print("[SPATIAL] Opened Add New wizard")

    def _on_tile_created(self, tile: BentoTile):
        """Handle tile creation from wizard"""
        # Add to grid
        self.grid.add_tile(tile)
        self.grid.refresh()

        # Save state
        self._save_floor_state()

        # Update status
        self.status_label.config(text=f"Created: {tile.label}")

        print(f"[SPATIAL] Created tile: {tile.label}")

    def _load_environment_image(self):
        """Load environment background from image"""
        file_path = filedialog.askopenfilename(
            title="Select Environment Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            self.environment.load_from_image(Path(file_path))
            self.environment.render()

            self.status_label.config(text=f"Environment loaded: {Path(file_path).name}")

            print(f"[SPATIAL] Loaded environment: {file_path}")

    def _show_flowchart(self):
        """Show project flowchart"""
        # Ask which root to visualize
        response = messagebox.askquestion(
            "Flowchart Source",
            "Show Z-Floors structure?\n\n"
            "Yes = Z-Floors\n"
            "No = Project Root"
        )

        if response == 'yes':
            self.flowchart.load_from_z_floors()
        else:
            self.flowchart.load_from_project_root()

        self.grid.refresh()
        self.status_label.config(text="Flowchart loaded")

        print("[SPATIAL] Loaded flowchart")

    def _open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Spatial UI Settings")
        settings_window.geometry("500x400")
        settings_window.configure(bg='#0A1628')

        # Title
        tk.Label(
            settings_window,
            text="Spatial UI Settings",
            font=('Segoe UI', 14, 'bold'),
            bg='#0A1628',
            fg='#00FFFF'
        ).pack(pady=20)

        # Settings frame
        frame = tk.Frame(settings_window, bg='#0A1628')
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Parallax strength
        tk.Label(
            frame,
            text="Parallax Strength:",
            bg='#0A1628',
            fg='#FFFFFF',
            font=('Segoe UI', 10)
        ).grid(row=0, column=0, sticky=tk.W, pady=10)

        parallax_var = tk.DoubleVar(value=self.environment.parallax_strength)
        parallax_scale = tk.Scale(
            frame,
            from_=0.0,
            to=1.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=parallax_var,
            bg='#102040',
            fg='#00FFFF',
            highlightthickness=0
        )
        parallax_scale.grid(row=0, column=1, sticky=tk.EW, pady=10)

        # Depth layers
        tk.Label(
            frame,
            text="Depth Layers:",
            bg='#0A1628',
            fg='#FFFFFF',
            font=('Segoe UI', 10)
        ).grid(row=1, column=0, sticky=tk.W, pady=10)

        layers_var = tk.IntVar(value=self.environment.depth_layers)
        layers_spinbox = tk.Spinbox(
            frame,
            from_=3,
            to=10,
            textvariable=layers_var,
            bg='#102040',
            fg='#FFFFFF',
            font=('Segoe UI', 10)
        )
        layers_spinbox.grid(row=1, column=1, sticky=tk.EW, pady=10)

        # Point cloud
        tk.Label(
            frame,
            text="Enable Point Cloud:",
            bg='#0A1628',
            fg='#FFFFFF',
            font=('Segoe UI', 10)
        ).grid(row=2, column=0, sticky=tk.W, pady=10)

        pointcloud_var = tk.BooleanVar(value=self.environment.enable_point_cloud)
        pointcloud_check = tk.Checkbutton(
            frame,
            variable=pointcloud_var,
            bg='#0A1628',
            fg='#00FFFF',
            selectcolor='#102040'
        )
        pointcloud_check.grid(row=2, column=1, sticky=tk.W, pady=10)

        frame.columnconfigure(1, weight=1)

        # Apply button
        def apply_settings():
            self.environment.parallax_strength = parallax_var.get()
            self.environment.depth_layers = layers_var.get()
            self.environment.enable_point_cloud = pointcloud_var.get()

            self._save_settings()
            self.environment.render()

            messagebox.showinfo("Settings", "Settings applied successfully")
            settings_window.destroy()

        apply_btn = tk.Button(
            settings_window,
            text="Apply",
            command=apply_settings,
            bg='#00FFFF',
            fg='#000000',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=10
        )
        apply_btn.pack(pady=20)

    def _on_scroll(self, event):
        """Handle mouse wheel scroll"""
        # Get scroll direction
        if event.num == 4 or event.delta > 0:
            delta = -50  # Scroll up
        else:
            delta = 50  # Scroll down

        # Scroll grid
        self.grid.scroll_y(delta)

    def _save_settings(self):
        """Save settings to Trinity"""
        settings = {
            "parallax_strength": self.environment.parallax_strength,
            "depth_layers": self.environment.depth_layers,
            "enable_point_cloud": self.environment.enable_point_cloud,
            "current_floor": self.current_floor
        }

        try:
            settings_file = TRINITY_SETTINGS / "spatial_ui.json"
            settings_file.parent.mkdir(parents=True, exist_ok=True)

            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            print("[SPATIAL] Settings saved")

        except Exception as e:
            print(f"[SPATIAL] Failed to save settings: {e}")

    def _load_settings(self):
        """Load settings from Trinity"""
        settings_file = TRINITY_SETTINGS / "spatial_ui.json"

        try:
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)

                self.environment.parallax_strength = settings.get("parallax_strength", 0.3)
                self.environment.depth_layers = settings.get("depth_layers", 5)
                self.environment.enable_point_cloud = settings.get("enable_point_cloud", False)
                self.current_floor = settings.get("current_floor", "Z0_TheConstruct")

                print("[SPATIAL] Settings loaded")

        except Exception as e:
            print(f"[SPATIAL] Failed to load settings: {e}")

    def _save_floor_state(self):
        """Save current floor tile state"""
        state = {
            "floor": self.current_floor,
            "tiles": []
        }

        for tile_id, tile in self.grid.tiles.items():
            tile_data = {
                "id": tile.id,
                "type": tile.type.value,
                "label": tile.label,
                "position": tile.position,
                "size": tile.size,
                "depth": tile.depth,
                "color": tile.color,
                "edge_color": tile.edge_color,
                "parent_tile": tile.parent_tile,
                "children": tile.children,
                "data": tile.data
            }
            state["tiles"].append(tile_data)

        try:
            state_file = TRINITY_SETTINGS / f"floor_state_{self.current_floor}.json"
            state_file.parent.mkdir(parents=True, exist_ok=True)

            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)

            print(f"[SPATIAL] Saved floor state: {self.current_floor}")

        except Exception as e:
            print(f"[SPATIAL] Failed to save floor state: {e}")


def launch_spatial_ui():
    """Launch spatial UI application"""
    root = tk.Tk()
    app = SpatialUIManager(root)
    root.mainloop()


# Demo mode for testing
if __name__ == "__main__":
    print("="*60)
    print("LightSpeed V0.9.11 - Spatial UI Integration")
    print("="*60)
    print()
    print("Features:")
    print("- Enhanced Bento Grid (1.5m curved surface)")
    print("- Ollama-powered Add New wizard")
    print("- 3D environment rendering (fake LIDAR)")
    print("- Project flowchart visualization")
    print("- Z-floor navigation")
    print()
    print("Launching...")
    print()

    launch_spatial_ui()


# Export
__all__ = ['SpatialUIManager', 'launch_spatial_ui']
