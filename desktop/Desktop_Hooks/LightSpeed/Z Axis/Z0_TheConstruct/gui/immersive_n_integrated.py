"""
LIGHTSPEED UNIFIED IMMERSIVE INTERFACE V1.0.0
Primary 3D interface integrating all immersive components

This is the MAIN ENTRY POINT for the immersive 3D experience. It unifies:
- Immersive 3D Engine (WASD navigation, physics, floors)
- Z-Tower Renderer (see-through floor visualization)
- Immersive Bento UI (curved 1.5m UI overlay)
- Interface Orchestrator (event coordination)

Created: January 9, 2026
Purpose: M3 Phase 2 - Core Integration
"""

import tkinter as tk
from tkinter import Canvas
from typing import Optional, Callable, Dict, Any
from pathlib import Path
import sys
from importlib.util import module_from_spec, spec_from_file_location

# Add Z Axis to path for imports
Z_AXIS_ROOT = Path(__file__).resolve().parents[2]  # Up to "Z Axis"
if str(Z_AXIS_ROOT) not in sys.path:
    sys.path.insert(0, str(Z_AXIS_ROOT))

# Add Trinity floor to path so `ui.*` is importable (Trinity owns UI).
TRINITY_ROOT = Z_AXIS_ROOT / "Z+3_Trinity"
if str(TRINITY_ROOT) not in sys.path:
    sys.path.insert(0, str(TRINITY_ROOT))

# Import immersive 3D engine
from Z0_TheConstruct.ui.immersive_3d_engine import (
    attach_immersive_3d_environment,
    Interactive3DObject,
    FloorType
)

# Import interface orchestrator
try:
    from ui.interface_orchestrator import InterfaceOrchestrator
except Exception:
    print("[Unified Interface] Warning: Interface Orchestrator not available")
    InterfaceOrchestrator = None


def _load_symbol_from_file(rel_path: str, symbol: str):
    """
    Load a symbol from a file path relative to `Z Axis/`.

    This avoids invalid import package names such as `Z+2_Neo`.
    """
    file_path = (Z_AXIS_ROOT / rel_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    mod_name = f"lightspeed_dynamic_{file_path.stem}_{abs(hash(str(file_path)))%1_000_000}"
    spec = spec_from_file_location(mod_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    mod = module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    if not hasattr(mod, symbol):
        raise AttributeError(f"{symbol} not found in {file_path}")
    return getattr(mod, symbol)


class UnifiedImmersiveInterface:
    """
    Unified immersive interface coordinating all 3D components

    This is the PRIMARY interface for LightSpeed. It creates a full-screen
    3D environment where users can:
    - Navigate with WASD + mouse
    - Jump and double-jump (Space key)
    - Explore all Z-floors in 3D space
    - Access Bento UI overlay (Caps Lock x2)
    - Use flowchart quick-jump (F key)
    - Click interactive widgets and objects
    """

    def __init__(
        self,
        orchestrator: Optional[Any] = None,
        parent: Optional[tk.Misc] = None,
        on_exit: Optional[Callable] = None,
        physics_config: Optional[Dict[str, float]] = None,
        fullscreen: bool = True
    ):
        """
        Initialize unified immersive interface

        Args:
            orchestrator: Interface orchestrator instance (optional)
            parent: Parent Tk window (None = standalone)
            on_exit: Callback when user exits
            physics_config: Custom physics parameters
            fullscreen: Launch in fullscreen mode
        """
        self.orchestrator = orchestrator
        self.on_exit = on_exit
        self.physics_config = physics_config or {}
        self.fullscreen = fullscreen
        self.event_bus = getattr(orchestrator, "event_bus", None) if orchestrator else None

        # Create window
        self.standalone = parent is None
        if self.standalone:
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(parent)

        self.setup_window()
        self.engine = None
        self._setup_complete = False

    def setup_window(self):
        """Configure the main window"""
        try:
            self.root.title("LightSpeed V1.0.0 - Immersive 3D Environment")
        except:
            pass

        # Get screen dimensions
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
        except:
            screen_width = 1920
            screen_height = 1080

        # Set fullscreen or window mode
        if self.fullscreen:
            try:
                self.root.attributes('-fullscreen', True)
                self.root.bind('<Escape>', lambda e: self.toggle_fullscreen())
            except:
                self.root.geometry(f"{screen_width}x{screen_height}")
        else:
            self.root.geometry(f"{screen_width}x{screen_height}")

        # Create canvas
        self.canvas = Canvas(
            self.root,
            width=screen_width,
            height=screen_height,
            bg='#000000',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind escape to exit
        self.root.bind('<Escape>', lambda e: self.handle_exit() if not self.fullscreen else None)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        try:
            self.root.attributes('-fullscreen', self.fullscreen)
        except:
            pass

    def handle_exit(self):
        """Handle user exit"""
        if callable(self.on_exit):
            try:
                self.on_exit()
            except:
                pass
        try:
            self.root.destroy()
        except:
            pass

    def handle_object_action(self, obj: Interactive3DObject):
        """
        Handle user interaction with 3D objects

        This is called when user clicks on widgets, doors, spheres, etc.
        It coordinates with the orchestrator to handle actions.
        """
        print(f"[Unified Interface] Object clicked: {obj.name} (type={obj.object_type})")

        def _publish(event_type: str, data: Dict[str, Any]):
            bus = self.event_bus
            if bus is None:
                return
            try:
                publish = getattr(bus, "publish", None)
                if callable(publish):
                    publish(event_type, data)
            except Exception:
                return

        # Publish widget activation to the shared event bus (orchestrator is subscribed there).
        _publish(
            "widget_activated",
            {
                "widget_id": obj.id,
                "widget_name": obj.name,
                "widget_type": obj.object_type,
                "floor": obj.floor.value if hasattr(obj.floor, "value") else str(obj.floor),
                "data": obj.data,
                "source": "immersive_3d",
            },
        )

        # Handle specific object types
        if obj.object_type in ("door", "sphere") and obj.data:
            # Floor transition: the engine may have already applied it; publish canonical floor ID.
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
            cur = None
            try:
                cur = self.engine.floor_nav.current_floor if self.engine else None
            except Exception:
                cur = None
            cur_id = floor_id_map.get(cur, "Z0_TheConstruct")
            _publish("floor_changed", {"floor": cur_id, "source": "immersive_3d"})

        elif obj.object_type == "window" and obj.data:
            # Widget launcher
            widget_type = obj.data.get('type')
            if widget_type == 'bento_ui_launcher':
                print("[Unified Interface] Launching Bento UI...")
                self.launch_bento_ui()
            elif widget_type == 'physics_simulation_launcher':
                print("[Unified Interface] Launching Physics Simulations...")
                self.launch_physics_sims()
            elif widget_type == 'neo_library_launcher':
                print("[Unified Interface] Launching Neo Function Library...")
                self.launch_neo_library()

    def launch_bento_ui(self):
        """Launch Immersive Bento UI"""
        try:
            # Canonical behavior: Bento is the in-world pause menu (CapsLock overlay).
            if self.engine:
                if not self.engine.ui_overlay.visible:
                    self.engine.ui_overlay.toggle()
                self.engine.paused = True
                self.engine.mouse_captured = False
            print("[Unified Interface] Bento overlay toggled")
        except Exception as e:
            print(f"[Unified Interface] Error launching Bento UI: {e}")
            # Fallback: just toggle the overlay in the 3D engine
            if self.engine:
                self.engine.ui_overlay.toggle()

    def launch_physics_sims(self):
        """Launch Raphael Physics Simulations"""
        try:
            print("[Unified Interface] Physics Simulations launching...")
            TheConstructPortalGlass = _load_symbol_from_file(
                "Z0_TheConstruct/components/TheConstruct_portal_glass.py",
                "TheConstructPortalGlass",
            )
            TheConstructPortalGlass(parent=self.root)
            print("[Unified Interface] TheConstruct portal opened")
        except Exception as e:
            print(f"[Unified Interface] Error launching Physics Sims: {e}")

    def launch_neo_library(self):
        """Launch Neo Function Library"""
        try:
            print("[Unified Interface] Neo Function Library launching...")
            NeoPortalGlass = _load_symbol_from_file(
                "Z+2_Neo/components/Neo_portal_glass.py",
                "NeoPortalGlass",
            )
            NeoPortalGlass(parent=self.root)
            print("[Unified Interface] Neo portal opened")
        except Exception as e:
            print(f"[Unified Interface] Error launching Neo Library: {e}")

    def setup_3d_engine(self):
        """Initialize the 3D engine with all components"""
        print("[Unified Interface] Initializing 3D environment...")

        # Attach immersive 3D engine to canvas
        bus = getattr(self.orchestrator, "event_bus", None) if self.orchestrator else None
        self.engine = attach_immersive_3d_environment(
            self.root,
            self.canvas,
            on_action=self.handle_object_action,
            event_bus=bus,
            physics=self.physics_config,
            capture_mouse=True
        )

        print("[Unified Interface] 3D engine initialized successfully")
        print("[Unified Interface] Controls:")
        print("  - WASD: Move")
        print("  - Shift: Run")
        print("  - Space: Jump (tap again mid-air for double-jump)")
        print("  - Mouse: Look around")
        print("  - Caps Lock x2: Toggle UI overlay")
        print("  - F: Toggle flowchart quick-jump")
        print("  - Escape: Exit fullscreen / Exit app")
        print("  - Click objects to interact")

        self._setup_complete = True

    def connect_orchestrator(self):
        """Connect to interface orchestrator for event coordination"""
        if not self.orchestrator:
            print("[Unified Interface] No orchestrator provided, running standalone")
            return

        print("[Unified Interface] Connecting to Interface Orchestrator...")
        try:
            if hasattr(self.orchestrator, "register_interface"):
                self.orchestrator.register_interface("immersive_3d", self)
        except Exception:
            pass

        # Subscribe to orchestrator broadcasts via shared event bus.
        bus = getattr(self.orchestrator, "event_bus", None)
        if bus is None:
            return
        try:
            subscribe = getattr(bus, "subscribe", None)
            if not callable(subscribe):
                return

            def _wrap(handler):
                def _h(evt):
                    try:
                        handler(evt)
                    except Exception as e:
                        print(f"[Unified Interface] Event handler error: {e}")
                return _h

            subscribe("orchestrator_floor_changed", _wrap(self.on_floor_changed), floor="UnifiedImmersive")
            subscribe("orchestrator_widget_created", _wrap(self.on_widget_created), floor="UnifiedImmersive")
            subscribe("orchestrator_camera_navigate", _wrap(self.on_camera_navigate), floor="UnifiedImmersive")
            print("[Unified Interface] Connected to orchestrator via Event Bus")
        except Exception as e:
            print(f"[Unified Interface] Error connecting to orchestrator: {e}")

    def on_floor_changed(self, event):
        """Handle floor change broadcast from orchestrator"""
        data = getattr(event, "data", {}) if event is not None else {}
        floor_id = data.get("floor")
        print(f"[Unified Interface] Floor changed: {floor_id}")

        if not self.engine or not floor_id:
            return

        reverse_map = {
            "Z-4_Merovingian": FloorType.Z_MINUS_4,
            "Z-3_Smith": FloorType.Z_MINUS_3,
            "Z-2_Oracle": FloorType.Z_MINUS_2,
            "Z-1_Morpheus": FloorType.Z_MINUS_1,
            "Z0_TheConstruct": FloorType.Z_ZERO,
            "Z+1_Architect": FloorType.Z_PLUS_1,
            "Z+2_Neo": FloorType.Z_PLUS_2,
            "Z+3_Trinity": FloorType.Z_PLUS_3,
        }
        target = reverse_map.get(floor_id)
        if target is None:
            return

        try:
            self.engine.floor_nav.current_floor = target
            self.engine.camera.y = self.engine.floor_nav.get_floor_y_position(target) + 5.0
            if hasattr(self.engine, "refresh_ui_overlay_widgets"):
                self.engine.refresh_ui_overlay_widgets()
        except Exception:
            return

    def on_widget_created(self, event):
        """Handle widget created broadcast from orchestrator"""
        data = getattr(event, "data", {}) if event is not None else {}
        widget_id = data.get("widget_id")
        print(f"[Unified Interface] Widget created: {widget_id}")
        if self.engine and hasattr(self.engine, "refresh_ui_overlay_widgets"):
            try:
                self.engine.refresh_ui_overlay_widgets()
            except Exception:
                pass

    def on_camera_navigate(self, event):
        """Handle orchestrator camera navigation requests"""
        data = getattr(event, "data", {}) if event is not None else {}
        target = data.get("target_position") or {}
        if not self.engine or not isinstance(target, dict):
            return
        try:
            self.engine.camera.x = float(target.get("x", self.engine.camera.x))
            self.engine.camera.y = float(target.get("y", self.engine.camera.y))
            self.engine.camera.z = float(target.get("z", self.engine.camera.z))
        except Exception:
            return

    def start(self):
        """Start the unified immersive interface"""
        print("[Unified Interface] Starting LightSpeed Immersive 3D Environment...")

        # Setup 3D engine
        self.setup_3d_engine()

        # Connect to orchestrator
        self.connect_orchestrator()

        # Start main loop if standalone
        if self.standalone:
            print("[Unified Interface] Entering main loop...")
            self.root.mainloop()

        return self.root


def launch_immersive(
    orchestrator: Optional[Any] = None,
    parent: Optional[tk.Misc] = None,
    on_exit: Optional[Callable] = None,
    physics_config: Optional[Dict[str, float]] = None,
    fullscreen: bool = True
) -> UnifiedImmersiveInterface:
    """
    Launch the unified immersive 3D interface

    This is the PRIMARY entry point for the immersive experience.
    Called from N.py or can be run standalone.

    Args:
        orchestrator: Interface orchestrator instance
        parent: Parent Tk window (None = standalone)
        on_exit: Callback when user exits
        physics_config: Custom physics parameters (gravity, jump_strength, etc.)
        fullscreen: Launch in fullscreen mode (default: True)

    Returns:
        UnifiedImmersiveInterface instance

    Example:
        # From N.py:
        from Z0_TheConstruct.gui.immersive_n_integrated import launch_immersive

        orchestrator = InterfaceOrchestrator()
        interface = launch_immersive(orchestrator=orchestrator, fullscreen=True)
    """
    interface = UnifiedImmersiveInterface(
        orchestrator=orchestrator,
        parent=parent,
        on_exit=on_exit,
        physics_config=physics_config,
        fullscreen=fullscreen
    )

    interface.start()
    return interface


# Standalone mode
if __name__ == "__main__":
    print("=" * 80)
    print("LIGHTSPEED V1.0.0 - IMMERSIVE 3D ENVIRONMENT")
    print("=" * 80)
    print()
    print("Launching in standalone mode...")
    print("Note: For full integration, launch from N.py")
    print()

    # Launch with default physics
    physics = {
        "gravity_m_s2": 20.0,
        "jump_strength": 7.0,
        "double_jump_strength": 6.0
    }

    interface = launch_immersive(physics_config=physics, fullscreen=False)
    print()
    print("=" * 80)
    print("Environment closed. Goodbye!")
    print("=" * 80)
