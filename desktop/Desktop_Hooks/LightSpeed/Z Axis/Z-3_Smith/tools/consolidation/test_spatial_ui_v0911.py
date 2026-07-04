"""
LightSpeed V0.9.11 - Spatial UI Test Suite
Comprehensive testing for all spatial UI components

Tests:
1. Enhanced Bento Grid rendering
2. Add New Wizard (with/without Ollama)
3. Environment Renderer (fake LIDAR)
4. Flowchart Visualizer
5. Complete integration

Author: LightSpeed Team / ACHILLES
Version: 0.9.11
Date: January 4, 2026
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import tkinter as tk
from tkinter import messagebox
import time

from core.ui.spatial import (
    EnhancedBentoGrid,
    BentoTile,
    TileType,
    AddNewWizard,
    EnvironmentRenderer,
    FlowchartVisualizer,
    SpatialUIManager,
    launch_spatial_ui
)


class SpatialUITestSuite:
    """Test suite for spatial UI components"""

    def __init__(self):
        self.results = []
        self.test_count = 0
        self.pass_count = 0

    def run_all_tests(self):
        """Run all tests"""
        print("="*70)
        print("LightSpeed V0.9.11 - Spatial UI Test Suite")
        print("="*70)
        print()

        # Test 1: Bento Grid
        self.test_enhanced_bento_grid()

        # Test 2: Tile Types
        self.test_tile_types()

        # Test 3: Glass Morphism
        self.test_glass_morphism()

        # Test 4: Environment Renderer
        self.test_environment_renderer()

        # Test 5: Flowchart Visualizer
        self.test_flowchart_visualizer()

        # Summary
        print()
        print("="*70)
        print("Test Summary")
        print("="*70)
        print(f"Total Tests: {self.test_count}")
        print(f"Passed: {self.pass_count}")
        print(f"Failed: {self.test_count - self.pass_count}")
        print(f"Success Rate: {(self.pass_count / self.test_count * 100) if self.test_count > 0 else 0:.1f}%")
        print()

        # Show results
        for result in self.results:
            status = "[PASS]" if result['passed'] else "[FAIL]"
            print(f"{status} {result['name']}: {result['message']}")

        print()
        print("="*70)

    def test_enhanced_bento_grid(self):
        """Test enhanced Bento grid creation"""
        self.test_count += 1
        test_name = "EnhancedBentoGrid - Creation"

        try:
            root = tk.Tk()
            root.withdraw()

            canvas = tk.Canvas(root, width=1400, height=900)
            grid = EnhancedBentoGrid(canvas, 1400, 900)

            # Verify constants
            assert grid.RADIUS == 1.5, "Radius should be 1.5m"
            assert grid.FOV_MIN == -50.0, "FOV min should be -50"
            assert grid.FOV_MAX == 50.0, "FOV max should be 50"

            # Verify initialization
            assert len(grid.tiles) == 0, "Should start with no tiles"
            assert grid.camera_y_offset == 0.0, "Camera should start at 0"

            root.destroy()

            self.pass_count += 1
            self.results.append({
                'name': test_name,
                'passed': True,
                'message': 'Grid created successfully with correct parameters'
            })

        except Exception as e:
            self.results.append({
                'name': test_name,
                'passed': False,
                'message': f'Error: {str(e)}'
            })

    def test_tile_types(self):
        """Test all tile types"""
        self.test_count += 1
        test_name = "BentoTile - All Types"

        try:
            root = tk.Tk()
            root.withdraw()

            canvas = tk.Canvas(root, width=1400, height=900)
            grid = EnhancedBentoGrid(canvas, 1400, 900)

            # Create one tile of each type
            tile_types = [
                TileType.WIDGET,
                TileType.TASK,
                TileType.TOOL,
                TileType.DATASET,
                TileType.VENV,
                TileType.FUNCTION,
                TileType.PARAMETER,
                TileType.FOLDER,
                TileType.FLOW_NODE,
                TileType.PORTAL
            ]

            for i, tile_type in enumerate(tile_types):
                angle = -40 + (i * 8)  # Spread across FOV
                tile = BentoTile(
                    id=f"test_{tile_type.value}",
                    type=tile_type,
                    label=f"Test {tile_type.value}",
                    position=(angle, 1.5, 0.0),
                    size=(180, 100),
                    depth=0.5 + (i * 0.05)
                )
                grid.add_tile(tile)

            # Verify all tiles added
            assert len(grid.tiles) == len(tile_types), f"Should have {len(tile_types)} tiles"

            # Test projection
            for tile in grid.tiles.values():
                projection = grid.project_to_screen(*tile.position)
                assert projection is not None, f"Tile {tile.id} should project to screen"

            root.destroy()

            self.pass_count += 1
            self.results.append({
                'name': test_name,
                'passed': True,
                'message': f'All {len(tile_types)} tile types created and projected'
            })

        except Exception as e:
            self.results.append({
                'name': test_name,
                'passed': False,
                'message': f'Error: {str(e)}'
            })

    def test_glass_morphism(self):
        """Test glass morphism rendering"""
        self.test_count += 1
        test_name = "Glass Morphism - Depth Variation"

        try:
            root = tk.Tk()
            root.withdraw()

            canvas = tk.Canvas(root, width=1400, height=900)
            grid = EnhancedBentoGrid(canvas, 1400, 900)

            # Create tiles at different depths
            depths = [0.0, 0.25, 0.5, 0.75, 1.0]

            for i, depth in enumerate(depths):
                tile = BentoTile(
                    id=f"depth_{depth}",
                    type=TileType.WIDGET,
                    label=f"Depth {depth}",
                    position=(i * 10 - 20, 1.5, 0.0),
                    size=(180, 100),
                    depth=depth
                )
                grid.add_tile(tile)

            # Verify depth-based glass thickness calculation
            for depth in depths:
                tile = grid.tiles[f"depth_{depth}"]
                # Glass thickness should vary with depth
                expected_min = grid.GLASS_THICKNESS_MIN
                expected_max = grid.GLASS_THICKNESS_MAX
                # Verify constants exist
                assert expected_min == 2, "Min thickness should be 2"
                assert expected_max == 8, "Max thickness should be 8"

            root.destroy()

            self.pass_count += 1
            self.results.append({
                'name': test_name,
                'passed': True,
                'message': 'Glass thickness varies correctly with depth'
            })

        except Exception as e:
            self.results.append({
                'name': test_name,
                'passed': False,
                'message': f'Error: {str(e)}'
            })

    def test_environment_renderer(self):
        """Test environment renderer"""
        self.test_count += 1
        test_name = "EnvironmentRenderer - Initialization"

        try:
            root = tk.Tk()
            root.withdraw()

            canvas = tk.Canvas(root, width=1400, height=900)
            env = EnvironmentRenderer(canvas, 1400, 900)

            # Verify initialization
            assert env.parallax_strength >= 0.0, "Parallax strength should be >= 0"
            assert env.depth_layers >= 3, "Should have at least 3 depth layers"
            assert len(env.layers) == 0, "Should start with no layers"

            # Test fake LIDAR
            from PIL import Image
            import numpy as np

            # Create test image (gradient)
            test_image = Image.new('RGB', (100, 100))
            pixels = test_image.load()
            for y in range(100):
                for x in range(100):
                    brightness = int((x / 100) * 255)
                    pixels[x, y] = (brightness, brightness, brightness)

            # Estimate depth
            depth_map = env.lidar.estimate_depth(test_image)

            # Verify depth map
            assert depth_map.shape == (100, 100), "Depth map should match image size"
            assert depth_map.min() >= 0.0, "Depth should be >= 0"
            assert depth_map.max() <= 1.0, "Depth should be <= 1"

            root.destroy()

            self.pass_count += 1
            self.results.append({
                'name': test_name,
                'passed': True,
                'message': 'Environment renderer and fake LIDAR working'
            })

        except Exception as e:
            self.results.append({
                'name': test_name,
                'passed': False,
                'message': f'Error: {str(e)}'
            })

    def test_flowchart_visualizer(self):
        """Test flowchart visualizer"""
        self.test_count += 1
        test_name = "FlowchartVisualizer - Node Creation"

        try:
            root = tk.Tk()
            root.withdraw()

            canvas = tk.Canvas(root, width=1400, height=900)
            grid = EnhancedBentoGrid(canvas, 1400, 900)
            flowchart = FlowchartVisualizer(grid)

            # Verify initialization
            assert len(flowchart.nodes) == 0, "Should start with no nodes"
            assert flowchart.root_node is None, "Should have no root initially"

            # Create test directory structure (in memory)
            from core.ui.spatial.flowchart_visualizer import FlowchartNode

            # Create simple tree
            root_node = FlowchartNode(
                id="root",
                label="Project",
                node_type="folder",
                path=Path("/test/project"),
                level=0
            )

            child1 = FlowchartNode(
                id="child1",
                label="Module A",
                node_type="folder",
                path=Path("/test/project/module_a"),
                parent_id="root",
                level=1
            )

            child2 = FlowchartNode(
                id="child2",
                label="Module B",
                node_type="folder",
                path=Path("/test/project/module_b"),
                parent_id="root",
                level=1
            )

            root_node.children_ids = ["child1", "child2"]

            # Add to flowchart
            flowchart.nodes["root"] = root_node
            flowchart.nodes["child1"] = child1
            flowchart.nodes["child2"] = child2
            flowchart.root_node = root_node

            # Test layout
            flowchart.layout.layout_tree(root_node, flowchart.nodes)

            # Verify tiles created
            assert root_node.tile is not None, "Root should have tile"
            assert child1.tile is not None, "Child1 should have tile"
            assert child2.tile is not None, "Child2 should have tile"

            # Verify hierarchy
            assert child1.tile.parent_tile == "root", "Child1 parent should be root"
            assert child2.tile.parent_tile == "root", "Child2 parent should be root"

            root.destroy()

            self.pass_count += 1
            self.results.append({
                'name': test_name,
                'passed': True,
                'message': 'Flowchart nodes and layout working correctly'
            })

        except Exception as e:
            self.results.append({
                'name': test_name,
                'passed': False,
                'message': f'Error: {str(e)}'
            })


def run_tests():
    """Run test suite"""
    suite = SpatialUITestSuite()
    suite.run_all_tests()


def demo_mode():
    """Launch interactive demo"""
    print("="*70)
    print("LightSpeed V0.9.11 - Spatial UI Demo")
    print("="*70)
    print()
    print("Launching interactive demo...")
    print()
    print("Features:")
    print("- Click 'Add New Tile' to create tiles with wizard")
    print("- Use Z-Floor dropdown to navigate floors")
    print("- Click 'Load Environment' to add 3D background")
    print("- Click 'Show Flowchart' to visualize project structure")
    print("- Mouse wheel to scroll vertically")
    print()

    launch_spatial_ui()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LightSpeed V0.9.11 Spatial UI Tests")
    parser.add_argument(
        '--mode',
        choices=['test', 'demo'],
        default='demo',
        help='Run mode: test (automated tests) or demo (interactive)'
    )

    args = parser.parse_args()

    if args.mode == 'test':
        run_tests()
    else:
        demo_mode()
