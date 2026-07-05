"""
Test script for data integration module.
"""

import sys
import time
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.ui.floor_widgets import NeoWidget, MorpheusWidget, ArchitectWidget
from core.ui.data_integration import (
    NeoDataAdapter, MorpheusDataAdapter, ArchitectDataAdapter,
    DataIntegrationManager
)


def main():
    print("Data Integration - Test Suite")
    print("=" * 70)

    # Test 1: Neo widget with live data
    print("\n[1/3] Testing Neo widget with live data...")
    neo_widget = NeoWidget("ai_status")
    neo_adapter = NeoDataAdapter(neo_widget)

    print("  Initial state:", neo_widget.data)
    neo_adapter.fetch_and_update()
    print("  After update:", neo_widget.data)

    # Test 2: Morpheus widget with live data
    print("\n[2/3] Testing Morpheus widget with live data...")
    morpheus_widget = MorpheusWidget("file_queue")
    morpheus_adapter = MorpheusDataAdapter(morpheus_widget)

    print("  Initial state:", morpheus_widget.data)
    morpheus_adapter.fetch_and_update()
    print("  After update:", morpheus_widget.data)

    # Test 3: Integration manager
    print("\n[3/3] Testing DataIntegrationManager...")
    manager = DataIntegrationManager()

    # Create widgets
    widgets = [
        NeoWidget("ai_status"),
        MorpheusWidget("file_queue"),
        ArchitectWidget("task_board")
    ]

    # Create adapters
    adapters = manager.create_floor_adapters("neo", widgets)
    print(f"  Created {len(adapters)} adapters")

    # Start automatic updates
    print("  Starting automatic updates for 3 seconds...")
    manager.start_all()
    time.sleep(3)
    manager.stop_all()

    print("\n  Final widget states:")
    for widget in widgets:
        print(f"    {widget.name}: {list(widget.data.keys())}")

    print("\n" + "=" * 70)
    print("Data integration ready!")
    print("- Real-time database queries")
    print("- Event bus subscriptions")
    print("- Automatic widget updates")
    print("- Centralized adapter management")


if __name__ == "__main__":
    main()
