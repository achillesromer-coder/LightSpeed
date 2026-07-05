#!/usr/bin/env python
"""
LIGHTSPEED IMMERSIVE LAUNCHER
Quick launcher for the immersive 3D interface

This launches the new integrated 3D environment where the UI IS the 3D world.
"""

import sys
from pathlib import Path

# Add paths (this script may be launched from anywhere)
HERE = Path(__file__).resolve()
ROOT = None
for cand in (HERE, *HERE.parents):
    if (cand / "N.py").exists() and (cand / "Z Axis").exists():
        ROOT = cand
        break
if ROOT is not None:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "Z Axis"))

print("=" * 70)
print("  LIGHTSPEED IMMERSIVE INTERFACE V1.0.0")
print("  The 3D Environment IS the UI")
print("=" * 70)
print()
print("Initializing systems...")
print()

# Import and launch
try:
    from Z0_TheConstruct.gui.immersive_n_integrated import launch_immersive
    print(" Immersive engine loaded")
    print()
    print("CONTROLS:")
    print("  W/A/S/D    - Move forward/left/backward/right")
    print("  Mouse      - Look around (click and drag)")
    print("  Space      - Jump")
    print("  Space x2   - Double jump (tap twice quickly)")
    print("  F1         - Toggle UI overlay")
    print("  E          - Interact with nearby objects")
    print("  Esc        - Exit fullscreen / Quit")
    print()
    print("FEATURES:")
    print("   Real-time night sky with stars and constellations")
    print("   Your location detected from timezone (Australia)")
    print("   Walk through Z-Axis tower structure")
    print("   All simulations embedded as 3D panels")
    print("   UI Base.pdf aesthetic overlaid on 3D world")
    print("   Drag images to change scenery (future)")
    print()
    print("Starting in 3 seconds...")
    print()

    import time
    time.sleep(3)

    # Launch!
    launch_immersive(fullscreen=True)

except ImportError as e:
    print(f" ERROR: Could not import immersive engine: {e}")
    print()
    print("Make sure you have installed:")
    print("  pip install pillow")
    print("  pip install pytz")
    sys.exit(1)
except Exception as e:
    print(f" ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
