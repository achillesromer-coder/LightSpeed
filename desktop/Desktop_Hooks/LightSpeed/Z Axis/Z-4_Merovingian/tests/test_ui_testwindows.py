"""
Test script for VenvTerminal and TestWindow components.
"""

import sys
import time
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.ui import TestWindow, VenvTerminal, OutputCapture
from core.ui.immersive_engine import Vector3D
from core.ui.test_window import TessellatedLayout


def main():
    print("VenvTerminal & TestWindow - Test Suite")
    print("=" * 70)

    # Test 1: VenvTerminal basic execution
    print("\n[1/4] Testing VenvTerminal execution...")
    terminal = VenvTerminal()
    print(f"  Venv path: {terminal.venv_path}")
    print(f"  Python: {terminal._get_venv_python()}")

    # Execute simple command
    print("\n  Executing: python --version")
    terminal.execute_command("python --version")
    time.sleep(0.5)

    history = terminal.output_capture.get_all_history()
    print(f"  Output lines captured: {len(history)}")
    if history:
        print(f"  First line: {history[0].content}")

    # Test 2: TestWindow rendering
    print("\n[2/4] Testing TestWindow rendering...")
    window = TestWindow(name="Physics Tests", terminal=terminal, width=60, height=10)

    print("\n  Rendered window:")
    print(window.render())

    # Test 3: Widget actions
    print("\n[3/4] Testing widget actions...")

    # Summary action
    summary = window.execute_action('summary')
    print(f"  Summary: {summary}")

    # Copy action
    copy_result = window.execute_action('copy')
    print(f"  Copy: {copy_result['lines']} lines copied")

    # Test 4: Tessellated layout
    print("\n[4/4] Testing tessellated layout...")
    layout = TessellatedLayout(max_windows=4)

    # Create multiple windows
    window1 = TestWindow("Raphael Tests", VenvTerminal(), width=40, height=8)
    window2 = TestWindow("Big Bang Tests", VenvTerminal(), width=40, height=8)
    window3 = TestWindow("Orbital Tests", VenvTerminal(), width=40, height=8)

    layout.add_window(window1)
    layout.add_window(window2)
    layout.add_window(window3)

    print(f"  Windows in layout: {len(layout.windows)}")

    # Arrange windows
    base_pos = Vector3D(0, 0, 15)
    layout.arrange_windows(base_pos)

    print(f"  Window positions:")
    for i, w in enumerate(layout.windows):
        print(f"    {w.name}: {w.position.to_tuple()}, Focus: {w.has_focus}")

    # Cycle focus
    layout.cycle_focus()
    print(f"\n  After focus cycle:")
    for i, w in enumerate(layout.windows):
        print(f"    {w.name}: Focus: {w.has_focus}")

    print("\n" + "=" * 70)
    print("Test windows ready for 3D integration!")
    print("- VenvTerminal: Command execution with output capture")
    print("- TestWindow: 3D widget for test display")
    print("- TessellatedLayout: Multi-window arrangement")
    print("- Actions: copy, extract, summary, clear, run_test")


if __name__ == "__main__":
    main()
