#!/usr/bin/env python
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   LIGHTSPEED PLATFORM V1.0.0 - UNIFIED LAUNCHER              ║
║                         "The Future is Immersive"                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

LIGHTSPEED UNIFIED ENTRY POINT
Single launcher for the complete integrated immersive smart floor platform

What This Does:
- Initializes all core services (EventBus, Database, Trinity, SmartFloor, Neo AI)
- Launches InterfaceOrchestrator for unified state management
- Starts Immersive N Integrated as primary interface
- Connects all systems for seamless interoperability

How It Works:
1. Core services initialized first (event bus, database, settings)
2. Smart floor systems activated (function library, Neo AI learning)
3. Interface orchestrator coordinates all UIs
4. Immersive 3D environment launches as THE interface (not separate)
5. All functionality accessible through 3D space navigation

Vision Realized:
✓ 3D environment IS the UI (not a separate view)
✓ Walk through functions instead of clicking tabs
✓ All simulations embedded as 3D panels in space
✓ SmartFloor amalgamation - all resources available everywhere
✓ Neo AI learning from all interactions
✓ UI Base.pdf aesthetic throughout
✓ Real-time astronomy with actual star positions
✓ Complete motion controls (WASD, jump, double jump)

Author: LightSpeed Team
Date: January 5, 2026
"""

import sys
import os
from pathlib import Path
import argparse

# Ensure Unicode output is stable on Windows consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return start.parent

# ═══════════════════════════════════════════════════════════════════════════
# PATH SETUP
# ═══════════════════════════════════════════════════════════════════════════

# Get LightSpeed root directory
LIGHTSPEED_ROOT = _find_lightspeed_root(Path(__file__))
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
for p in (LIGHTSPEED_ROOT, Z_AXIS_ROOT):
    try:
        sys.path.insert(0, str(p))
    except Exception:
        pass

# Ensure all core modules are accessible
print("[INIT] LightSpeed root:", LIGHTSPEED_ROOT)


# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════

def check_dependencies():
    """Check for required dependencies"""
    required = {
        'tkinter': 'Built-in GUI framework',
        'PIL': 'Image processing (pillow)',
        'pytz': 'Timezone handling'
    }

    missing = []

    # Check tkinter
    try:
        import tkinter
        print("[DEPS] ✓ tkinter available")
    except ImportError:
        missing.append('tkinter')
        print("[DEPS] ✗ tkinter missing")

    # Check PIL
    try:
        from PIL import Image
        print("[DEPS] ✓ PIL/Pillow available")
    except ImportError:
        missing.append('PIL')
        print("[DEPS] ✗ PIL/Pillow missing (pip install pillow)")

    # Check pytz
    try:
        import pytz
        print("[DEPS] ✓ pytz available")
    except ImportError:
        missing.append('pytz')
        print("[DEPS] ✗ pytz missing (pip install pytz)")

    if missing:
        print()
        print("[ERROR] Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}: {required[dep]}")
        print()
        print("Install with:")
        if 'PIL' in missing or 'pytz' in missing:
            print(f"  pip install {' '.join([d.lower() if d != 'PIL' else 'pillow' for d in missing])}")
        return False

    return True


def import_core_services():
    """Import core service modules"""
    global EventBus, DatabaseManager, TrinityManager
    global NeoLearningEngine, SmartFloorLibrary
    global InterfaceOrchestrator, launch_immersive_n

    print("[INIT] Importing core services...")

    # Event Bus
    try:
        from core.services.event_bus import EventBus
        print("[INIT] ✓ EventBus imported")
    except ImportError as e:
        print(f"[INIT] ⚠ EventBus not available, creating minimal implementation")
        # Create minimal event bus if not exists
        EventBus = create_minimal_event_bus()

    # Database Manager
    try:
        from core.database.db_manager import DatabaseManager
        print("[INIT] ✓ DatabaseManager imported")
    except ImportError:
        print(f"[INIT] ⚠ DatabaseManager not available, creating minimal implementation")
        DatabaseManager = create_minimal_database()

    # Trinity Settings Manager
    try:
        from core.storage.trinity import TrinityManager
        print("[INIT] ✓ TrinityManager imported")
    except ImportError:
        print(f"[INIT] ⚠ TrinityManager not available, creating minimal implementation")
        TrinityManager = create_minimal_trinity()

    # Smart Floor Library
    try:
        from core.services.smart_floor_library import SmartFloorLibrary
        print("[INIT] ✓ SmartFloorLibrary imported")
    except ImportError:
        print(f"[INIT] ⚠ SmartFloorLibrary not available yet (will be extracted)")
        SmartFloorLibrary = None

    # Neo Learning Engine
    try:
        from core.ai.neo_learning import NeoLearningEngine
        print("[INIT] ✓ NeoLearningEngine imported")
    except ImportError:
        print(f"[INIT] ⚠ NeoLearningEngine not available yet (will be extracted)")
        NeoLearningEngine = None

    # Interface Orchestrator
    try:
        from core.ui.interface_orchestrator import InterfaceOrchestrator
        print("[INIT] ✓ InterfaceOrchestrator imported")
    except ImportError:
        print(f"[INIT] ⚠ InterfaceOrchestrator not available yet (will be created)")
        InterfaceOrchestrator = None

    # Immersive N Integrated
    try:
        from Z0_TheConstruct.gui.immersive_n_integrated import launch_immersive as launch_immersive_n
        print("[INIT] ✓ Immersive N Integrated imported")
    except ImportError as e:
        print(f"[INIT] ✗ Immersive N Integrated not available: {e}")
        launch_immersive_n = None

    print("[INIT] Core services imported")


# ═══════════════════════════════════════════════════════════════════════════
# MINIMAL IMPLEMENTATIONS (for when services don't exist yet)
# ═══════════════════════════════════════════════════════════════════════════

def create_minimal_event_bus():
    """Create minimal event bus if core version doesn't exist"""
    class MinimalEventBus:
        def __init__(self):
            self.subscribers = {}

        def subscribe(self, event_name, callback):
            if event_name not in self.subscribers:
                self.subscribers[event_name] = []
            self.subscribers[event_name].append(callback)

        def publish(self, event_name, data=None):
            if event_name in self.subscribers:
                for callback in self.subscribers[event_name]:
                    try:
                        callback(data)
                    except Exception as e:
                        print(f"[EventBus] Error in subscriber for {event_name}: {e}")

    return MinimalEventBus


def create_minimal_database():
    """Create minimal database if core version doesn't exist"""
    class MinimalDatabase:
        def __init__(self):
            self.data = {}

        def get(self, key, default=None):
            return self.data.get(key, default)

        def set(self, key, value):
            self.data[key] = value

        def get_widget(self, widget_id):
            return None

        def save_widget(self, widget_id, widget_data):
            pass

    return MinimalDatabase


def create_minimal_trinity():
    """Create minimal Trinity if core version doesn't exist"""
    import json

    class MinimalTrinity:
        def __init__(self):
            self.root = LIGHTSPEED_ROOT / 'data' / 'trinity'
            self.root.mkdir(parents=True, exist_ok=True)

        def load(self, filename):
            path = self.root / filename
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
            return {}

        def save(self, filename, data):
            path = self.root / filename
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

    return MinimalTrinity


# ═══════════════════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════════════════

def print_banner():
    """Print startup banner"""
    print()
    print("═" * 78)
    print("║" + " " * 76 + "║")
    print("║" + "LIGHTSPEED PLATFORM V1.0.0".center(76) + "║")
    print("║" + "Immersive Smart Floor Interface".center(76) + "║")
    print("║" + " " * 76 + "║")
    print("═" * 78)
    print()
    print("  The 3D Environment IS the User Interface")
    print()
    print("  Vision Realized:")
    print("    ✓ Walk through functions instead of clicking tabs")
    print("    ✓ All simulations embedded as 3D panels in space")
    print("    ✓ Real-time astronomy with actual star positions")
    print("    ✓ SmartFloor amalgamation across all floors")
    print("    ✓ Neo AI learning from every interaction")
    print("    ✓ UI Base.pdf aesthetic throughout")
    print()
    print("═" * 78)
    print()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main launcher function"""

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='LightSpeed Platform V1.0.0 - Immersive Smart Floor Interface'
    )
    parser.add_argument(
        '--mode',
        choices=['immersive', 'legacy', 'compatibility'],
        default='immersive',
        help='Launch mode (default: immersive)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    args = parser.parse_args()

    # Print banner
    print_banner()

    # Check dependencies
    print("[INIT] Checking dependencies...")
    if not check_dependencies():
        print()
        print("[ERROR] Missing dependencies. Please install them and try again.")
        print()
        return 1

    print()

    # Import core services
    import_core_services()

    print()
    print("─" * 78)
    print()

    # Initialize based on mode
    if args.mode == 'immersive':
        launch_immersive_mode()
    elif args.mode == 'legacy':
        launch_legacy_mode()
    elif args.mode == 'compatibility':
        launch_compatibility_mode()

    return 0


def launch_immersive_mode():
    """Launch immersive 3D interface (primary mode)"""
    print("[LAUNCH] Starting Immersive Mode (Primary)")
    print()

    # Initialize core services
    print("[INIT] Initializing core services...")
    event_bus = EventBus()
    database = DatabaseManager() if DatabaseManager else create_minimal_database()()
    trinity = TrinityManager() if TrinityManager else create_minimal_trinity()()
    print("[INIT] ✓ Core services initialized")

    # Initialize smart floor systems
    print("[INIT] Initializing smart floor systems...")
    if SmartFloorLibrary and NeoLearningEngine:
        smart_floor = SmartFloorLibrary()
        neo_ai = NeoLearningEngine(smart_floor)
        print("[INIT] ✓ Smart floor systems initialized")
    else:
        smart_floor = None
        neo_ai = None
        print("[INIT] ⚠ Smart floor systems not available yet")

    # Initialize interface orchestrator
    print("[INIT] Initializing interface orchestrator...")
    if InterfaceOrchestrator:
        orchestrator = InterfaceOrchestrator(
            event_bus=event_bus,
            database=database,
            trinity=trinity,
            smart_floor=smart_floor,
            neo_ai=neo_ai
        )
        print("[INIT] ✓ Interface orchestrator initialized")
    else:
        orchestrator = None
        print("[INIT] ⚠ Interface orchestrator not available yet")

    # Load user preferences
    print("[INIT] Loading user preferences...")
    user_prefs = trinity.load('user_preferences.json')
    if user_prefs:
        print(f"[INIT] ✓ User preferences loaded")
    else:
        print(f"[INIT] ⚠ No saved preferences, using defaults")

    print()
    print("─" * 78)
    print()
    print("[LAUNCH] Launching Immersive N Integrated...")
    print()
    print("CONTROLS:")
    print("  W/A/S/D       - Move forward/left/backward/right")
    print("  Mouse         - Look around (click and drag)")
    print("  Space         - Jump")
    print("  Space (x2)    - Double jump (tap twice quickly)")
    print("  E             - Interact with nearby objects")
    print("  F1            - Toggle UI overlay")
    print("  Esc           - Exit fullscreen / Quit")
    print()
    print("FEATURES:")
    print("  ✓ Real-time night sky with actual stars and constellations")
    print("  ✓ Your location detected from system timezone")
    print("  ✓ Walk through Z-Axis tower structure (8 floors)")
    print("  ✓ All simulations embedded as 3D panels")
    print("  ✓ UI Base.pdf aesthetic overlaid on 3D world")
    print()
    print("Starting in 2 seconds...")
    print()

    import time
    time.sleep(2)

    # Launch immersive interface
    if launch_immersive_n:
        launch_immersive_n(orchestrator=orchestrator)
    else:
        print("[ERROR] Immersive N Integrated not available!")
        print("Fallback: Launching legacy 3D engine...")
        try:
            from core.ui.immersive_3d_engine import launch_immersive_3d_environment
            launch_immersive_3d_environment()
        except ImportError:
            print("[ERROR] No 3D interfaces available!")
            print("Please ensure core/ui/immersive_n_integrated.py exists.")
            return 1


def launch_legacy_mode():
    """Launch legacy N.py interface (2D compatibility mode)"""
    print("[LAUNCH] Starting Legacy Mode (2D Compatibility)")
    print()
    print("⚠ WARNING: Legacy mode uses traditional 2D interface")
    print("⚠ This does not reflect the true vision (immersive smart floor)")
    print("⚠ Recommended: Use --mode immersive instead")
    print()
    print("Starting N.py...")
    print()

    try:
        import N
        # N.py will launch its own Tk mainloop
    except ImportError:
        print("[ERROR] N.py not found!")
        return 1


def launch_compatibility_mode():
    """Launch both immersive and legacy (dual mode)"""
    print("[LAUNCH] Starting Compatibility Mode (Dual Interface)")
    print()
    print("This mode launches both:")
    print("  1. Immersive 3D interface (primary)")
    print("  2. Legacy N.py 2D interface (compatibility)")
    print()
    print("Both interfaces will be synchronized via orchestrator")
    print()

    # Initialize shared services
    event_bus = EventBus()
    database = DatabaseManager() if DatabaseManager else create_minimal_database()()
    trinity = TrinityManager() if TrinityManager else create_minimal_trinity()()

    if SmartFloorLibrary and NeoLearningEngine:
        smart_floor = SmartFloorLibrary()
        neo_ai = NeoLearningEngine(smart_floor)
    else:
        smart_floor = None
        neo_ai = None

    if InterfaceOrchestrator:
        orchestrator = InterfaceOrchestrator(
            event_bus=event_bus,
            database=database,
            trinity=trinity,
            smart_floor=smart_floor,
            neo_ai=neo_ai
        )
    else:
        orchestrator = None

    # Launch immersive in separate thread
    import threading

    def launch_immersive_thread():
        if launch_immersive_n:
            launch_immersive_n(orchestrator=orchestrator)

    immersive_thread = threading.Thread(target=launch_immersive_thread, daemon=True)
    immersive_thread.start()

    # Launch N.py in main thread
    try:
        import N
    except ImportError:
        print("[ERROR] N.py not found!")
        return 1


# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print()
        print("[EXIT] User interrupted. Shutting down...")
        print()
        print("Thank you for using LightSpeed!")
        print()
        sys.exit(0)
    except Exception as e:
        print()
        print(f"[FATAL ERROR] {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        sys.exit(1)
