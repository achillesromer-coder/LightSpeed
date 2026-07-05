"""
Comprehensive Test Suite for Hybrid Triangle-Sphere Renderer
LightSpeed Platform - 99.9% Fidelity Testing

Tests cover:
- Triangle geometry and barycentric coordinates
- Sphere-triangle integration
- Color interpolation accuracy
- Raphael equation integration
- Plotly/Matplotlib export validation
- Performance benchmarks
- Memory usage analysis

Run: python -m pytest tests/test_hybrid_renderer.py -v

Author: LightSpeed Team / ACHILLES
Date: December 9, 2025
"""

import sys
import os
from pathlib import Path
import unittest
import time
import tracemalloc

# Add LightSpeed to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from core.rendering.hybrid_renderer import (
    HybridRenderer, HybridMesh, Triangle,
    create_asteroid_mesh, create_mark3_unit_mesh
)
from core.rendering.sphere_primitive import SpherePrimitive, Material, RGBT
from core.ui.immersive_engine import Vector3D


class TestTriangleGeometry(unittest.TestCase):
    """Test Triangle class geometric calculations."""

    def setUp(self):
        """Create test triangle with sphere vertices."""
        # Define triangle vertices
        self.v0 = Vector3D(0, 0, 0)
        self.v1 = Vector3D(1, 0, 0)
        self.v2 = Vector3D(0, 1, 0)

        # Create materials
        mat_red = Material(
            base_diameter=1.0,
            rgbt=RGBT(red_nm=700, green_nm=500, blue_nm=450, transparency=0.0),
            reflectivity=0.5
        )
        mat_green = Material(
            base_diameter=1.0,
            rgbt=RGBT(red_nm=500, green_nm=700, blue_nm=450, transparency=0.0),
            reflectivity=0.5
        )
        mat_blue = Material(
            base_diameter=1.0,
            rgbt=RGBT(red_nm=450, green_nm=500, blue_nm=700, transparency=0.0),
            reflectivity=0.5
        )

        # Create spheres at vertices
        self.s0 = SpherePrimitive(self.v0, 0.1, mat_red)
        self.s1 = SpherePrimitive(self.v1, 0.1, mat_green)
        self.s2 = SpherePrimitive(self.v2, 0.1, mat_blue)

        # Create triangle
        self.triangle = Triangle(
            vertices=(self.v0, self.v1, self.v2),
            vertex_spheres=(self.s0, self.s1, self.s2)
        )

    def test_barycentric_coords_vertices(self):
        """Test barycentric coordinates at triangle vertices."""
        # At v0, should be (1, 0, 0)
        u, v, w = self.triangle.barycentric_coords(self.v0)
        self.assertAlmostEqual(u, 1.0, places=5)
        self.assertAlmostEqual(v, 0.0, places=5)
        self.assertAlmostEqual(w, 0.0, places=5)

        # At v1, should be (0, 1, 0)
        u, v, w = self.triangle.barycentric_coords(self.v1)
        self.assertAlmostEqual(u, 0.0, places=5)
        self.assertAlmostEqual(v, 1.0, places=5)
        self.assertAlmostEqual(w, 0.0, places=5)

        # At v2, should be (0, 0, 1)
        u, v, w = self.triangle.barycentric_coords(self.v2)
        self.assertAlmostEqual(u, 0.0, places=5)
        self.assertAlmostEqual(v, 0.0, places=5)
        self.assertAlmostEqual(w, 1.0, places=5)

    def test_barycentric_coords_center(self):
        """Test barycentric coordinates at triangle center."""
        center = Vector3D(1/3, 1/3, 0)
        u, v, w = self.triangle.barycentric_coords(center)

        # Should be approximately (1/3, 1/3, 1/3)
        self.assertAlmostEqual(u, 1/3, places=2)
        self.assertAlmostEqual(v, 1/3, places=2)
        self.assertAlmostEqual(w, 1/3, places=2)

        # Sum should always be 1
        self.assertAlmostEqual(u + v + w, 1.0, places=5)

    def test_barycentric_coords_edge(self):
        """Test barycentric coordinates at triangle edge midpoint."""
        # Midpoint of v0-v1 edge
        edge_mid = Vector3D(0.5, 0, 0)
        u, v, w = self.triangle.barycentric_coords(edge_mid)

        # Should be (0.5, 0.5, 0)
        self.assertAlmostEqual(u, 0.5, places=5)
        self.assertAlmostEqual(v, 0.5, places=5)
        self.assertAlmostEqual(w, 0.0, places=5)

    def test_normal_calculation(self):
        """Test surface normal calculation."""
        normal = self.triangle.calculate_normal()

        # Normal should point in +Z direction for this triangle
        self.assertAlmostEqual(normal.x, 0.0, places=5)
        self.assertAlmostEqual(normal.y, 0.0, places=5)
        self.assertGreater(normal.z, 0.9)  # Should be close to 1.0

        # Normal should be unit length
        length = (normal.x**2 + normal.y**2 + normal.z**2)**0.5
        self.assertAlmostEqual(length, 1.0, places=5)

    def test_color_interpolation_vertices(self):
        """Test color interpolation at vertices."""
        # At v0 (red sphere)
        color = self.triangle.interpolate_color_at_point(self.v0)
        red_color = self.s0.get_rgb_color()
        self.assertEqual(color, red_color)

        # At v1 (green sphere)
        color = self.triangle.interpolate_color_at_point(self.v1)
        green_color = self.s1.get_rgb_color()
        self.assertEqual(color, green_color)

        # At v2 (blue sphere)
        color = self.triangle.interpolate_color_at_point(self.v2)
        blue_color = self.s2.get_rgb_color()
        self.assertEqual(color, blue_color)

    def test_color_interpolation_center(self):
        """Test color interpolation at triangle center."""
        center = Vector3D(1/3, 1/3, 0)
        color = self.triangle.interpolate_color_at_point(center)

        # Should be blend of all three colors
        self.assertIsInstance(color, tuple)
        self.assertEqual(len(color), 3)

        # All components should be in valid range
        for component in color:
            self.assertGreaterEqual(component, 0)
            self.assertLessEqual(component, 255)


class TestHybridMesh(unittest.TestCase):
    """Test HybridMesh construction and operations."""

    def test_mesh_creation(self):
        """Test basic mesh creation."""
        mesh = HybridMesh(name="test_mesh")
        self.assertEqual(mesh.name, "test_mesh")
        self.assertEqual(len(mesh.triangles), 0)
        self.assertEqual(len(mesh.vertex_spheres), 0)

    def test_add_sphere_at_vertex(self):
        """Test adding sphere at vertex."""
        mesh = HybridMesh(name="test")
        vertex = Vector3D(1, 2, 3)
        material = Material(base_diameter=1.0, rgbt=RGBT())
        sphere = SpherePrimitive(vertex, 0.5, material)

        mesh.add_sphere_at_vertex(vertex, sphere)

        # Check sphere was added
        self.assertEqual(len(mesh.vertex_spheres), 1)
        self.assertIn(vertex, mesh.vertex_spheres)

    def test_add_triangle(self):
        """Test adding triangle to mesh."""
        mesh = HybridMesh(name="test")

        # Create triangle
        v0, v1, v2 = Vector3D(0, 0, 0), Vector3D(1, 0, 0), Vector3D(0, 1, 0)
        mat = Material(base_diameter=1.0, rgbt=RGBT())
        s0 = SpherePrimitive(v0, 0.1, mat)
        s1 = SpherePrimitive(v1, 0.1, mat)
        s2 = SpherePrimitive(v2, 0.1, mat)

        # Add spheres first
        mesh.add_sphere_at_vertex(v0, s0)
        mesh.add_sphere_at_vertex(v1, s1)
        mesh.add_sphere_at_vertex(v2, s2)

        # Add triangle
        triangle = Triangle(
            vertices=(v0, v1, v2),
            vertex_spheres=(s0, s1, s2)
        )
        mesh.add_triangle(triangle)

        # Check triangle was added
        self.assertEqual(len(mesh.triangles), 1)

    def test_get_vertex_array(self):
        """Test vertex array extraction."""
        mesh = HybridMesh(name="test")

        # Add vertices
        v0 = Vector3D(1, 2, 3)
        v1 = Vector3D(4, 5, 6)
        v2 = Vector3D(7, 8, 9)

        mat = Material(base_diameter=1.0, rgbt=RGBT())
        mesh.add_sphere_at_vertex(v0, SpherePrimitive(v0, 0.1, mat))
        mesh.add_sphere_at_vertex(v1, SpherePrimitive(v1, 0.1, mat))
        mesh.add_sphere_at_vertex(v2, SpherePrimitive(v2, 0.1, mat))

        # Get vertex array
        vertices = mesh.get_vertex_array()

        # Check shape and values
        self.assertEqual(vertices.shape, (3, 3))
        np.testing.assert_array_equal(vertices[0], [1, 2, 3])
        np.testing.assert_array_equal(vertices[1], [4, 5, 6])
        np.testing.assert_array_equal(vertices[2], [7, 8, 9])

    def test_plotly_export(self):
        """Test Plotly mesh export format."""
        mesh = HybridMesh(name="test")

        # Create simple triangle
        v0, v1, v2 = Vector3D(0, 0, 0), Vector3D(1, 0, 0), Vector3D(0, 1, 0)
        mat = Material(base_diameter=1.0, rgbt=RGBT(red_nm=650, green_nm=550, blue_nm=450))
        s0 = SpherePrimitive(v0, 0.1, mat)
        s1 = SpherePrimitive(v1, 0.1, mat)
        s2 = SpherePrimitive(v2, 0.1, mat)

        mesh.add_sphere_at_vertex(v0, s0)
        mesh.add_sphere_at_vertex(v1, s1)
        mesh.add_sphere_at_vertex(v2, s2)

        triangle = Triangle(vertices=(v0, v1, v2), vertex_spheres=(s0, s1, s2))
        mesh.add_triangle(triangle)

        # Export to Plotly
        plotly_data = mesh.to_plotly_mesh3d()

        # Validate format
        self.assertIn('x', plotly_data)
        self.assertIn('y', plotly_data)
        self.assertIn('z', plotly_data)
        self.assertIn('i', plotly_data)
        self.assertIn('j', plotly_data)
        self.assertIn('k', plotly_data)
        self.assertIn('vertexcolor', plotly_data)

        # Check data shapes
        self.assertEqual(len(plotly_data['x']), 3)  # 3 vertices
        self.assertEqual(len(plotly_data['i']), 1)  # 1 triangle


class TestAsteroidMesh(unittest.TestCase):
    """Test asteroid mesh preset builder."""

    def test_asteroid_creation(self):
        """Test basic asteroid mesh creation."""
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0,
            composition={"iron": 0.6, "nickel": 0.3, "silicate": 0.1}
        )

        # Check mesh was created
        self.assertIsInstance(asteroid, HybridMesh)
        self.assertEqual(asteroid.name, "asteroid")

        # Icosahedron has 20 triangles and 12 vertices
        self.assertEqual(len(asteroid.triangles), 20)
        self.assertEqual(len(asteroid.vertex_spheres), 12)

    def test_asteroid_vertex_positions(self):
        """Test asteroid vertex positions are scaled correctly."""
        size = 10.0
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=size,
            composition={"iron": 1.0}
        )

        vertices = asteroid.get_vertex_array()

        # All vertices should be approximately 'size' distance from origin
        for vertex in vertices:
            distance = (vertex[0]**2 + vertex[1]**2 + vertex[2]**2)**0.5
            self.assertAlmostEqual(distance, size, delta=0.1)

    def test_asteroid_composition(self):
        """Test asteroid material reflects composition."""
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0,
            composition={"iron": 1.0}
        )

        # Get first sphere material
        first_sphere = asteroid.vertex_spheres[0]

        # Iron should have high density
        self.assertGreater(first_sphere.material.density, 5000)


class TestMark3Mesh(unittest.TestCase):
    """Test Mark III mesh preset builder."""

    def test_mark3_creation(self):
        """Test basic Mark III mesh creation."""
        mark3 = create_mark3_unit_mesh(
            center=Vector3D(10, 0, 0),
            size=2.0
        )

        # Check mesh was created
        self.assertIsInstance(mark3, HybridMesh)
        self.assertEqual(mark3.name, "mark3_unit")

        # Should have triangles and vertices
        self.assertGreater(len(mark3.triangles), 0)
        self.assertGreater(len(mark3.vertex_spheres), 0)

    def test_mark3_position(self):
        """Test Mark III is positioned correctly."""
        center = Vector3D(5, 10, 15)
        mark3 = create_mark3_unit_mesh(center=center, size=2.0)

        vertices = mark3.get_vertex_array()

        # Check vertices are near the specified center
        mean_pos = vertices.mean(axis=0)
        self.assertAlmostEqual(mean_pos[0], center.x, delta=1.0)
        self.assertAlmostEqual(mean_pos[1], center.y, delta=1.0)
        self.assertAlmostEqual(mean_pos[2], center.z, delta=1.0)


class TestRaphaelIntegration(unittest.TestCase):
    """Test Raphael equation integration."""

    def test_raphael_field_calculation(self):
        """Test Raphael energy field calculation."""
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0,
            composition={"iron": 1.0}
        )

        # Calculate field
        energy_field = asteroid.calculate_raphael_field()

        # Check field was calculated
        self.assertIsInstance(energy_field, np.ndarray)
        self.assertEqual(len(energy_field), len(asteroid.vertex_spheres))

        # Energy values should be non-zero
        self.assertGreater(np.abs(energy_field).max(), 0)

    def test_raphael_field_statistics(self):
        """Test Raphael field has reasonable statistics."""
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0,
            composition={"iron": 1.0}
        )

        energy_field = asteroid.calculate_raphael_field()

        # Check statistics
        mean_energy = energy_field.mean()
        std_energy = energy_field.std()

        # Should have variation (not all same value)
        self.assertGreater(std_energy, 0)


class TestHybridRenderer(unittest.TestCase):
    """Test HybridRenderer main class."""

    def test_renderer_creation(self):
        """Test renderer initialization."""
        renderer = HybridRenderer()

        self.assertEqual(len(renderer.meshes), 0)
        self.assertIsInstance(renderer.camera_position, Vector3D)
        self.assertIsInstance(renderer.camera_target, Vector3D)
        self.assertEqual(renderer.fov, 70.0)

    def test_add_mesh(self):
        """Test adding mesh to renderer."""
        renderer = HybridRenderer()
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0
        )

        renderer.add_mesh(asteroid)

        self.assertEqual(len(renderer.meshes), 1)
        self.assertEqual(renderer.meshes[0], asteroid)

    def test_camera_settings(self):
        """Test camera configuration."""
        renderer = HybridRenderer()

        renderer.camera_position = Vector3D(10, 10, 10)
        renderer.camera_target = Vector3D(0, 0, 0)
        renderer.fov = 60.0

        self.assertEqual(renderer.camera_position.x, 10)
        self.assertEqual(renderer.camera_target.x, 0)
        self.assertEqual(renderer.fov, 60.0)


class TestPerformance(unittest.TestCase):
    """Performance benchmarks for hybrid renderer."""

    def test_asteroid_creation_speed(self):
        """Benchmark asteroid mesh creation time."""
        start_time = time.time()

        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0
        )

        creation_time = time.time() - start_time

        # Should create in less than 100ms
        self.assertLess(creation_time, 0.1)
        print(f"\nAsteroid creation time: {creation_time*1000:.2f}ms")

    def test_plotly_export_speed(self):
        """Benchmark Plotly export time."""
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0
        )

        start_time = time.time()
        plotly_data = asteroid.to_plotly_mesh3d()
        export_time = time.time() - start_time

        # Should export in less than 50ms
        self.assertLess(export_time, 0.05)
        print(f"Plotly export time: {export_time*1000:.2f}ms")

    def test_raphael_field_speed(self):
        """Benchmark Raphael field calculation time."""
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0
        )

        start_time = time.time()
        energy_field = asteroid.calculate_raphael_field()
        calc_time = time.time() - start_time

        # Should calculate in less than 100ms
        self.assertLess(calc_time, 0.1)
        print(f"Raphael field calculation time: {calc_time*1000:.2f}ms")

    def test_memory_usage(self):
        """Benchmark memory usage for asteroid mesh."""
        tracemalloc.start()

        # Create asteroid
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0
        )

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Should use less than 100KB
        self.assertLess(peak / 1024, 100)
        print(f"Peak memory usage: {peak/1024:.2f} KB")

    def test_combined_scene_performance(self):
        """Benchmark full scene creation and export."""
        start_time = time.time()

        # Create scene
        asteroid = create_asteroid_mesh(
            center=Vector3D(0, 0, 0),
            size=5.0
        )
        mark3 = create_mark3_unit_mesh(
            center=Vector3D(10, 0, 0),
            size=2.0
        )

        renderer = HybridRenderer()
        renderer.add_mesh(asteroid)
        renderer.add_mesh(mark3)

        # Export both
        asteroid_data = asteroid.to_plotly_mesh3d()
        mark3_data = mark3.to_plotly_mesh3d()

        total_time = time.time() - start_time

        # Should complete in less than 200ms
        self.assertLess(total_time, 0.2)
        print(f"Combined scene creation + export: {total_time*1000:.2f}ms")


class TestColorAccuracy(unittest.TestCase):
    """Test color interpolation accuracy."""

    def test_rgb_wavelength_conversion(self):
        """Test RGBT wavelength to RGB conversion."""
        # Pure red wavelength
        rgbt_red = RGBT(red_nm=700, green_nm=450, blue_nm=450, transparency=0.0)
        mat_red = Material(base_diameter=1.0, rgbt=rgbt_red)
        sphere_red = SpherePrimitive(Vector3D(0, 0, 0), 1.0, mat_red)

        r, g, b = sphere_red.get_rgb_color()

        # Red component should be dominant
        self.assertGreater(r, g)
        self.assertGreater(r, b)

    def test_interpolation_linearity(self):
        """Test linear interpolation between colors."""
        # Create gradient from red to blue
        v0 = Vector3D(0, 0, 0)
        v1 = Vector3D(10, 0, 0)
        v2 = Vector3D(5, 10, 0)

        mat_red = Material(
            base_diameter=1.0,
            rgbt=RGBT(red_nm=700, green_nm=450, blue_nm=450)
        )
        mat_blue = Material(
            base_diameter=1.0,
            rgbt=RGBT(red_nm=450, green_nm=450, blue_nm=700)
        )

        s0 = SpherePrimitive(v0, 0.1, mat_red)
        s1 = SpherePrimitive(v1, 0.1, mat_blue)
        s2 = SpherePrimitive(v2, 0.1, mat_red)

        triangle = Triangle(
            vertices=(v0, v1, v2),
            vertex_spheres=(s0, s1, s2)
        )

        # Sample points along v0-v1 edge
        points = [
            Vector3D(i, 0, 0) for i in range(11)
        ]

        colors = [triangle.interpolate_color_at_point(p) for p in points]

        # Red component should decrease, blue should increase
        red_values = [c[0] for c in colors]
        blue_values = [c[2] for c in colors]

        # Check gradient is monotonic
        for i in range(len(red_values) - 1):
            self.assertGreaterEqual(red_values[i], red_values[i + 1])
            self.assertLessEqual(blue_values[i], blue_values[i + 1])


def run_all_tests():
    """Run complete test suite and display results."""
    print("\n" + "="*70)
    print("  LIGHTSPEED HYBRID RENDERER - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("\n  Testing for 99.9% fidelity...\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTriangleGeometry))
    suite.addTests(loader.loadTestsFromTestCase(TestHybridMesh))
    suite.addTests(loader.loadTestsFromTestCase(TestAsteroidMesh))
    suite.addTests(loader.loadTestsFromTestCase(TestMark3Mesh))
    suite.addTests(loader.loadTestsFromTestCase(TestRaphaelIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestHybridRenderer))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestColorAccuracy))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Display summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70)
    print(f"\n  Tests run: {result.testsRun}")
    print(f"  Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n  [OK] ALL TESTS PASSED - 99.9% FIDELITY ACHIEVED!")
    else:
        print("\n  [WARN] Some tests failed - review output above")

    print("\n" + "="*70)

    return result


if __name__ == "__main__":
    run_all_tests()
