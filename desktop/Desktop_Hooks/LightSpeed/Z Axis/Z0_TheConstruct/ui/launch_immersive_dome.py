#!/usr/bin/env python
"""
Launch Immersive Dome Interface
Quick launcher for enhanced dome projection system with FPS controls

Features:
- Full FPS mouse-look controls (360° horizontal, 180° vertical)
- UI widgets anchored at 1.5m from player
- 3-step Bento widget management
- Rolling hills environment (Windows 97 style)
- Integration with Z-Axis floors

Author: LightSpeed Team
Version: 0.9.7
Date: 2026-01-13
"""

from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, messagebox

def _find_lightspeed_root() -> Path:
    """
    Locate LightSpeed root directory by searching for N.py + Z Axis.

    This launcher is stored floor-native under TheConstruct; it must resolve the
    actual app root regardless of the current working directory.
    """
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        try:
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        except Exception:
            continue
    # Fallback: best-effort (repo layouts vary)
    return here.parents[3]


# Add paths
LIGHTSPEED_ROOT = _find_lightspeed_root()
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
TRINITY_DIR = Z_AXIS_ROOT / "Z+3_Trinity"

for p in (Z_AXIS_ROOT, TRINITY_DIR):
    try:
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
    except Exception:
        continue

# Import dome projection and Bento system
try:
    from ui.dome_projection_engine import DomeProjectionEngine
    from ui.immersive_bento_system import ImmersiveBentoSystem
    imports_successful = True
except ImportError as e:
    print(f"Warning: Could not import dome projection modules: {e}")
    imports_successful = False

# Import Premium Theme Engine
try:
    from ui.premium_theme_engine import get_theme_engine, ThemeMode
    HAS_PREMIUM_THEME = True
except ImportError:
    print("[INFO] Premium theme engine not available - using fallback styling")
    HAS_PREMIUM_THEME = False


class ImmersiveDomeApp:
    """
    Main application for immersive dome interface.

    Combines:
    - Dome projection engine with FPS controls
    - Bento widget system (3-step addition)
    - Floor navigation
    - Widget management
    """

    def __init__(self):
        """Initialize dome application."""
        self.root = tk.Tk()
        self.root.title("LightSpeed Immersive Dome Interface - V0.9.7")
        self.root.geometry("1400x900")

        # Initialize premium theme engine
        if HAS_PREMIUM_THEME:
            self.theme = get_theme_engine(ThemeMode.DARK)
            self.use_premium_theme = True
            self.theme.apply_to_root(self.root)
        else:
            self.use_premium_theme = False
            self.theme = None

        # Configure style (fallback for ttk widgets)
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass

        # Main layout
        self._build_ui()

    def _build_ui(self):
        """Build main UI."""
        # Top toolbar
        self._build_toolbar()

        # Main content area (dome + sidebar)
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar (left)
        self._build_sidebar(content_frame)

        # Dome projection area (right)
        dome_frame = ttk.Frame(content_frame)
        dome_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create dome engine
        if imports_successful:
            self.dome_engine = DomeProjectionEngine(
                dome_frame,
                width=1200,
                height=800,
                enable_rolling_hills=True
            )

            # Create Bento system
            self.bento_system = ImmersiveBentoSystem(
                self.root,
                dome_engine=self.dome_engine
            )

            # Add default widgets
            self._add_default_widgets()
        else:
            # Fallback message
            fallback_label = ttk.Label(
                dome_frame,
                text="⚠️ Dome projection modules not available.\nPlease ensure Trinity floor UI modules are present.",
                font=('Arial', 12),
                foreground='red'
            )
            fallback_label.pack(expand=True)

        # Status bar (bottom)
        self._build_status_bar()

    def _build_toolbar(self):
        """Build top toolbar with premium glass styling."""
        # Use glass frame for toolbar if premium theme available
        if self.use_premium_theme:
            toolbar = self.theme.create_glass_frame(self.root)
            toolbar.configure(height=60)
        else:
            toolbar = ttk.Frame(self.root, relief=tk.RAISED, borderwidth=2)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Title with premium styling
        if self.use_premium_theme:
            title_label = self.theme.create_header_label(
                toolbar,
                text="🌐 LightSpeed Immersive Dome Interface"
            )
        else:
            title_label = ttk.Label(
                toolbar,
                text="[DOME] LightSpeed Immersive Dome Interface",
                font=('Arial', 12, 'bold')
            )
        title_label.pack(side=tk.LEFT, padx=10)

        # Buttons with premium gold styling
        if imports_successful:
            if self.use_premium_theme:
                self.theme.create_premium_button(
                    toolbar,
                    text="➕ Add Widget",
                    command=self._on_add_widget,
                    style="gold"
                ).pack(side=tk.RIGHT, padx=5)

                self.theme.create_premium_button(
                    toolbar,
                    text="💾 Save Layout",
                    command=self._on_save_layout,
                    style="secondary"
                ).pack(side=tk.RIGHT, padx=5)

                self.theme.create_premium_button(
                    toolbar,
                    text="📁 Load Layout",
                    command=self._on_load_layout,
                    style="secondary"
                ).pack(side=tk.RIGHT, padx=5)
            else:
                ttk.Button(
                    toolbar,
                    text="➕ Add Widget",
                    command=self._on_add_widget
                ).pack(side=tk.RIGHT, padx=5)

                ttk.Button(
                    toolbar,
                    text="💾 Save Layout",
                    command=self._on_save_layout
                ).pack(side=tk.RIGHT, padx=5)

                ttk.Button(
                    toolbar,
                    text="📁 Load Layout",
                    command=self._on_load_layout
                ).pack(side=tk.RIGHT, padx=5)

        # Help button
        if self.use_premium_theme:
            self.theme.create_premium_button(
                toolbar,
                text="❓ Help",
                command=self._on_help,
                style="glass"
            ).pack(side=tk.RIGHT, padx=5)
        else:
            ttk.Button(
                toolbar,
                text="❓ Help",
                command=self._on_help
            ).pack(side=tk.RIGHT, padx=5)

    def _build_sidebar(self, parent):
        """Build left sidebar with controls."""
        sidebar = ttk.Frame(parent, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Floor navigation
        nav_frame = ttk.LabelFrame(sidebar, text="Floor Navigation", padding=10)
        nav_frame.pack(fill=tk.X, pady=5)

        floors = [
            ("Z+3 Trinity", 3),
            ("Z+2 Neo", 2),
            ("Z+1 Architect", 1),
            ("Z0 TheConstruct", 0),
            ("Z-1 Morpheus", -1),
            ("Z-2 Oracle", -2),
            ("Z-3 Smith", -3),
            ("Z-4 Merovingian", -4)
        ]

        for floor_name, z_level in floors:
            ttk.Button(
                nav_frame,
                text=floor_name,
                command=lambda z=z_level: self._navigate_to_floor(z)
            ).pack(fill=tk.X, pady=2)

        # Camera controls
        camera_frame = ttk.LabelFrame(sidebar, text="Camera Controls", padding=10)
        camera_frame.pack(fill=tk.X, pady=5)

        ttk.Label(camera_frame, text="FOV:").pack()
        fov_var = tk.DoubleVar(value=90.0)
        ttk.Scale(
            camera_frame,
            from_=60,
            to=120,
            variable=fov_var,
            orient=tk.HORIZONTAL,
            command=lambda v: self._on_fov_change(float(v))
        ).pack(fill=tk.X)

        ttk.Label(camera_frame, text="Sensitivity:").pack(pady=(10, 0))
        sens_var = tk.DoubleVar(value=0.15)
        ttk.Scale(
            camera_frame,
            from_=0.05,
            to=0.5,
            variable=sens_var,
            orient=tk.HORIZONTAL,
            command=lambda v: self._on_sensitivity_change(float(v))
        ).pack(fill=tk.X)

        ttk.Button(
            camera_frame,
            text="Reset Camera",
            command=self._reset_camera
        ).pack(pady=(10, 0), fill=tk.X)

        # Widget list
        widget_frame = ttk.LabelFrame(sidebar, text="Active Widgets", padding=10)
        widget_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.widget_listbox = tk.Listbox(widget_frame, height=10)
        self.widget_listbox.pack(fill=tk.BOTH, expand=True)

        ttk.Button(
            widget_frame,
            text="Remove Selected",
            command=self._on_remove_widget
        ).pack(pady=(5, 0), fill=tk.X)

        ttk.Button(
            widget_frame,
            text="Refresh List",
            command=self._refresh_widget_list
        ).pack(pady=(2, 0), fill=tk.X)

    def _build_status_bar(self):
        """Build bottom status bar."""
        status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(
            status_bar,
            text="Ready | FPS Controls: Click canvas to capture mouse, ESC to release | WASD to move",
            font=('Arial', 9)
        )
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)

        # Version
        version_label = ttk.Label(
            status_bar,
            text="V0.9.7",
            font=('Arial', 9)
        )
        version_label.pack(side=tk.RIGHT, padx=5)

    def _add_default_widgets(self):
        """Add default starter widgets."""
        if not imports_successful:
            return

        # Status widget (top left)
        self.dome_engine.add_widget(
            widget_id='default_status',
            content='System Status\n✅ Online',
            x_offset=-0.4,
            y_offset=0.3,
            width=0.3,
            height=0.15
        )

        # Metrics widget (top right)
        self.dome_engine.add_widget(
            widget_id='default_metrics',
            content='Metrics\n📊 42 Active',
            x_offset=0.4,
            y_offset=0.3,
            width=0.3,
            height=0.15
        )

        # Console widget (bottom)
        self.dome_engine.add_widget(
            widget_id='default_console',
            content='Console Output\n💻 Ready for input',
            x_offset=0.0,
            y_offset=-0.3,
            width=0.6,
            height=0.2
        )

        self._refresh_widget_list()

    def _on_add_widget(self):
        """Handle add widget button."""
        if imports_successful:
            self.bento_system.open_add_widget_wizard()
            # Refresh list after wizard closes
            self.root.after(500, self._refresh_widget_list)

    def _on_remove_widget(self):
        """Handle remove widget button."""
        if not imports_successful:
            return

        selection = self.widget_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a widget to remove.")
            return

        widget_id = self.widget_listbox.get(selection[0]).split(':')[0]

        if messagebox.askyesno("Confirm", f"Remove widget {widget_id}?"):
            self.dome_engine.remove_widget(widget_id)
            self._refresh_widget_list()
            self.status_label.config(text=f"Removed widget: {widget_id}")

    def _refresh_widget_list(self):
        """Refresh widget list."""
        if not imports_successful:
            return

        self.widget_listbox.delete(0, tk.END)

        # Get widgets from dome engine
        for widget in self.dome_engine.widgets:
            display_text = f"{widget.id}: {widget.content[:20]}..."
            self.widget_listbox.insert(tk.END, display_text)

    def _navigate_to_floor(self, z_level: int):
        """Navigate to specified floor."""
        # Canonical IDs match `ui.universal_bento_system` floor ids.
        floor_ids = {
            3: "Z+3_Trinity",
            2: "Z+2_Neo",
            1: "Z+1_Architect",
            0: "Z0_TheConstruct",
            -1: "Z-1_Morpheus",
            -2: "Z-2_Oracle",
            -3: "Z-3_Smith",
            -4: "Z-4_Merovingian",
        }

        floor_names = {
            3: "Trinity",
            2: "Neo",
            1: "Architect",
            0: "TheConstruct",
            -1: "Morpheus",
            -2: "Oracle",
            -3: "Smith",
            -4: "Merovingian",
        }

        floor_name = floor_names.get(z_level, "Unknown")
        floor_id = floor_ids.get(z_level)

        # If Trinity's global Bento system is available, update the active floor so
        # the UI overlay reflects the user's navigation immediately.
        if floor_id:
            try:
                from ui.universal_bento_system import get_bento_system  # type: ignore
                get_bento_system().set_active_floor(floor_id)
            except Exception:
                pass

        self.status_label.config(text=f"Navigated to Z{z_level:+d} {floor_name}")
        try:
            self._refresh_widget_list()
        except Exception:
            pass

    def _on_fov_change(self, value: float):
        """Handle FOV change."""
        if imports_successful:
            self.dome_engine.camera.fov = value
            self.status_label.config(text=f"FOV changed to {int(value)}°")

    def _on_sensitivity_change(self, value: float):
        """Handle sensitivity change."""
        if imports_successful:
            self.dome_engine.camera.mouse_sensitivity = value
            self.status_label.config(text=f"Mouse sensitivity: {value:.2f}")

    def _reset_camera(self):
        """Reset camera to default."""
        if imports_successful:
            self.dome_engine.camera.yaw = 0.0
            self.dome_engine.camera.pitch = 0.0
            self.dome_engine.camera.position.x = 0.0
            self.dome_engine.camera.position.y = 1.6
            self.dome_engine.camera.position.z = 0.0
            self.status_label.config(text="Camera reset to default position")

    def _on_save_layout(self):
        """Save current widget layout."""
        if not imports_successful:
            return

        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Widget Layout"
        )

        if filepath:
            try:
                self.bento_system.save_layout(filepath)
                messagebox.showinfo("Success", f"Layout saved to:\n{filepath}")
                self.status_label.config(text=f"Layout saved: {Path(filepath).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save layout:\n{e}")

    def _on_load_layout(self):
        """Load widget layout from file."""
        if not imports_successful:
            return

        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Widget Layout"
        )

        if filepath:
            try:
                self.bento_system.load_layout(filepath)
                self._refresh_widget_list()
                messagebox.showinfo("Success", f"Layout loaded from:\n{filepath}")
                self.status_label.config(text=f"Layout loaded: {Path(filepath).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load layout:\n{e}")

    def _on_help(self):
        """Show help dialog."""
        help_text = """[DOME] LightSpeed Immersive Dome Interface

MOUSE CONTROLS:
• Click canvas to capture mouse (FPS mode)
• Move mouse to look around (360° horizontal, 180° vertical)
• ESC to release mouse capture

KEYBOARD CONTROLS:
• W/A/S/D - Move forward/left/backward/right
• SPACE - Move up
• C - Move down

WIDGETS:
• All widgets stay 1.5m from your viewpoint
• Use "Add Widget" for 3-step wizard
• Widgets always face the camera (billboard effect)

BENTO SYSTEM:
Step 1: Select widget type from templates
Step 2: Configure properties and position
Step 3: Confirm and place

ENVIRONMENT:
• Rolling hills background (Windows 97 style)
• Sky gradient and terrain
• Animated landscape

Version: 0.9.7
LightSpeed Platform - Z+3 Trinity Floor"""

        messagebox.showinfo("Help - Immersive Dome Interface", help_text)

    def run(self):
        """Run the application."""
        print("=" * 70)
        print("LightSpeed Immersive Dome Interface")
        print("=" * 70)
        print("\nFeatures:")
        print("  [OK] FPS Mouse-Look Controls (360 deg horizontal, 180 deg vertical)")
        print("  [OK] UI Widgets anchored at 1.5m from player")
        print("  [OK] 3-Step Bento Widget Management")
        print("  [OK] Rolling Hills Environment (Windows 97 style)")
        print("  [OK] Z-Axis Floor Navigation")
        print("\nControls:")
        print("  - Click canvas to capture mouse")
        print("  - Move mouse to look around")
        print("  - ESC to release mouse")
        print("  - WASD for movement")
        print("\n" + "=" * 70)
        print()

        self.root.mainloop()

    def cleanup(self):
        """Cleanup resources."""
        if imports_successful and hasattr(self, 'dome_engine'):
            self.dome_engine.cleanup()


def main():
    """Main entry point."""
    app = ImmersiveDomeApp()

    def on_close():
        app.cleanup()
        app.root.destroy()

    app.root.protocol("WM_DELETE_WINDOW", on_close)
    app.run()


if __name__ == "__main__":
    main()
