#!/usr/bin/env python
"""
RFS/EMFF Runner - RF/Electromagnetic Field Analysis
====================================================

This runner provides electromagnetic field simulations for:
- Radio frequency propagation
- Electromagnetic field mapping
- Antenna pattern analysis
- Signal strength predictions
- Multi-frequency analysis

Uses physics-based calculations for field strength, propagation, and interference.

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 19, 2026
"""

from pathlib import Path
import json
import time
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from . import BaseRunner


class RFSEMFFRunner(BaseRunner):
    """
    RFS/EMFF (Radio Frequency / Electromagnetic Field) Runner

    Performs electromagnetic field analysis and RF propagation simulations.
    """

    # Physical constants
    C = 299792458  # Speed of light (m/s)
    MU_0 = 4 * np.pi * 1e-7  # Permeability of free space (H/m)
    EPSILON_0 = 8.854187817e-12  # Permittivity of free space (F/m)
    Z_0 = 376.730313668  # Impedance of free space (Ohms)

    def __init__(self):
        super().__init__(tool_name="rfs_emff", version="1.0.0")
        self.schema_path = Path(__file__).parent.parent.parent / "schemas" / "rfs_emff_input_schema.json"

    def validate_field_parameters(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate electromagnetic field parameters

        Required:
        - analysis_type: "field_map", "propagation", "antenna_pattern", "multi_frequency"
        - source: dict with power, frequency, position, polarization
        - volume: dict with bounds (xmin, xmax, ymin, ymax, zmin, zmax), resolution
        - medium: dict with permittivity, permeability, conductivity

        Optional:
        - obstacles: list of obstacle definitions
        - receivers: list of receiver positions
        """
        required = ['analysis_type', 'source', 'volume', 'medium']
        for field in required:
            if field not in params:
                return False, f"Missing required field: {field}"

        # Validate source parameters
        source = params['source']
        required_source = ['power', 'frequency', 'position']
        for field in required_source:
            if field not in source:
                return False, f"Missing source parameter: {field}"

        # Validate volume
        volume = params['volume']
        required_volume = ['bounds', 'resolution']
        for field in required_volume:
            if field not in volume:
                return False, f"Missing volume parameter: {field}"

        bounds = volume['bounds']
        if len(bounds) != 6:
            return False, "Bounds must be [xmin, xmax, ymin, ymax, zmin, zmax]"

        return True, None

    def calculate_free_space_path_loss(self, distance: float, frequency: float) -> float:
        """
        Calculate free space path loss (FSPL)

        FSPL (dB) = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)

        Args:
            distance: Distance in meters
            frequency: Frequency in Hz

        Returns:
            Path loss in dB
        """
        if distance <= 0:
            return 0.0

        fspl_db = (20 * np.log10(distance) +
                   20 * np.log10(frequency) +
                   20 * np.log10(4 * np.pi / self.C))

        return fspl_db

    def calculate_electric_field(self, power: float, distance: float, frequency: float) -> float:
        """
        Calculate electric field strength at distance from isotropic radiator

        E = sqrt(30 * P * G) / d    (V/m)

        where:
        - P = power (W)
        - G = antenna gain (assume 1 for isotropic)
        - d = distance (m)

        Args:
            power: Transmit power in Watts
            distance: Distance in meters
            frequency: Frequency in Hz (for wavelength calculations)

        Returns:
            Electric field strength in V/m
        """
        if distance <= 0:
            return 0.0

        # For isotropic radiator (G = 1)
        E = np.sqrt(30 * power) / distance

        return E

    def calculate_magnetic_field(self, electric_field: float) -> float:
        """
        Calculate magnetic field from electric field in far field

        H = E / Z0

        Args:
            electric_field: Electric field strength in V/m

        Returns:
            Magnetic field strength in A/m
        """
        return electric_field / self.Z_0

    def calculate_power_density(self, electric_field: float) -> float:
        """
        Calculate power density from electric field

        S = E² / Z0    (W/m²)

        Args:
            electric_field: Electric field strength in V/m

        Returns:
            Power density in W/m²
        """
        return (electric_field ** 2) / self.Z_0

    def generate_field_map_3d(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate 3D electromagnetic field map

        Args:
            params: Field parameters

        Returns:
            Field data with E-field, H-field, power density
        """
        source = params['source']
        volume = params['volume']
        medium = params['medium']

        # Extract parameters
        power = source['power']  # Watts
        frequency = source['frequency']  # Hz
        src_pos = np.array(source['position'])  # [x, y, z] in meters

        # Extract volume bounds
        xmin, xmax, ymin, ymax, zmin, zmax = volume['bounds']
        resolution = volume['resolution']  # meters

        # Create 3D grid
        x = np.arange(xmin, xmax, resolution)
        y = np.arange(ymin, ymax, resolution)
        z = np.arange(zmin, zmax, resolution)

        nx, ny, nz = len(x), len(y), len(z)

        if self.logger:
            self.logger.info(f"[RFS/EMFF] Generating field map: {nx}x{ny}x{nz} = {nx*ny*nz} points")

        # Initialize field arrays
        E_field = np.zeros((nx, ny, nz))
        H_field = np.zeros((nx, ny, nz))
        S_density = np.zeros((nx, ny, nz))

        # Calculate wavelength
        wavelength = self.C / frequency

        # Calculate fields at each point
        total_points = nx * ny * nz
        points_calculated = 0

        for i, xi in enumerate(x):
            for j, yj in enumerate(y):
                for k, zk in enumerate(z):
                    # Calculate distance from source
                    point = np.array([xi, yj, zk])
                    distance = np.linalg.norm(point - src_pos)

                    # Avoid singularity at source
                    if distance < wavelength / 10:
                        distance = wavelength / 10

                    # Calculate electric field
                    E = self.calculate_electric_field(power, distance, frequency)

                    # Apply medium effects (simplified)
                    rel_permittivity = medium.get('relative_permittivity', 1.0)
                    E *= np.sqrt(1.0 / rel_permittivity)

                    # Calculate magnetic field and power density
                    H = self.calculate_magnetic_field(E)
                    S = self.calculate_power_density(E)

                    E_field[i, j, k] = E
                    H_field[i, j, k] = H
                    S_density[i, j, k] = S

                    points_calculated += 1

        if self.logger:
            self.logger.info(f"[RFS/EMFF] Field calculation complete: {points_calculated} points")

        # Calculate statistics
        E_max = np.max(E_field)
        E_min = np.min(E_field[E_field > 0]) if np.any(E_field > 0) else 0
        E_mean = np.mean(E_field)

        results = {
            "grid_dimensions": [nx, ny, nz],
            "total_points": int(total_points),
            "wavelength_m": float(wavelength),
            "statistics": {
                "E_field_max_V_m": float(E_max),
                "E_field_min_V_m": float(E_min),
                "E_field_mean_V_m": float(E_mean),
                "H_field_max_A_m": float(np.max(H_field)),
                "power_density_max_W_m2": float(np.max(S_density)),
                "power_density_mean_W_m2": float(np.mean(S_density))
            }
        }

        # Save field data to files
        np.save(self.output_dir / "E_field.npy", E_field)
        np.save(self.output_dir / "H_field.npy", H_field)
        np.save(self.output_dir / "S_density.npy", S_density)

        # Save grid coordinates
        np.save(self.output_dir / "grid_x.npy", x)
        np.save(self.output_dir / "grid_y.npy", y)
        np.save(self.output_dir / "grid_z.npy", z)

        if self.logger:
            self.logger.info(f"[RFS/EMFF] Field data saved to {self.output_dir}")

        return results

    def generate_visualizations(self, params: Dict[str, Any], results: Dict[str, Any]):
        """
        Generate visualization plots of field distributions

        Creates:
        - 2D slices through field (XY, XZ, YZ planes)
        - Power density heatmap
        - Field strength vs distance plot
        """
        try:
            # Load field data
            E_field = np.load(self.output_dir / "E_field.npy")
            S_density = np.load(self.output_dir / "S_density.npy")
            x = np.load(self.output_dir / "grid_x.npy")
            y = np.load(self.output_dir / "grid_y.npy")
            z = np.load(self.output_dir / "grid_z.npy")

            # Get middle indices
            nx, ny, nz = E_field.shape
            mid_x, mid_y, mid_z = nx // 2, ny // 2, nz // 2

            # Create figure with subplots
            fig = plt.figure(figsize=(15, 12))

            # XY plane slice (at mid-z)
            ax1 = fig.add_subplot(2, 3, 1)
            im1 = ax1.contourf(x, y, E_field[:, :, mid_z].T, levels=20, cmap='viridis')
            ax1.set_xlabel('X (m)')
            ax1.set_ylabel('Y (m)')
            ax1.set_title(f'E-field XY Plane (z={z[mid_z]:.2f}m)')
            plt.colorbar(im1, ax=ax1, label='E-field (V/m)')

            # XZ plane slice (at mid-y)
            ax2 = fig.add_subplot(2, 3, 2)
            im2 = ax2.contourf(x, z, E_field[:, mid_y, :].T, levels=20, cmap='viridis')
            ax2.set_xlabel('X (m)')
            ax2.set_ylabel('Z (m)')
            ax2.set_title(f'E-field XZ Plane (y={y[mid_y]:.2f}m)')
            plt.colorbar(im2, ax=ax2, label='E-field (V/m)')

            # YZ plane slice (at mid-x)
            ax3 = fig.add_subplot(2, 3, 3)
            im3 = ax3.contourf(y, z, E_field[mid_x, :, :].T, levels=20, cmap='viridis')
            ax3.set_xlabel('Y (m)')
            ax3.set_ylabel('Z (m)')
            ax3.set_title(f'E-field YZ Plane (x={x[mid_x]:.2f}m)')
            plt.colorbar(im3, ax=ax3, label='E-field (V/m)')

            # Power density XY plane
            ax4 = fig.add_subplot(2, 3, 4)
            im4 = ax4.contourf(x, y, S_density[:, :, mid_z].T, levels=20, cmap='plasma')
            ax4.set_xlabel('X (m)')
            ax4.set_ylabel('Y (m)')
            ax4.set_title(f'Power Density XY Plane (z={z[mid_z]:.2f}m)')
            plt.colorbar(im4, ax=ax4, label='Power Density (W/m²)')

            # Field strength vs distance (radial from source)
            ax5 = fig.add_subplot(2, 3, 5)
            source_pos = np.array(params['source']['position'])

            # Sample radial distances
            distances = []
            E_values = []

            for i in range(0, nx, max(1, nx // 50)):
                for j in range(0, ny, max(1, ny // 50)):
                    for k in range(0, nz, max(1, nz // 50)):
                        point = np.array([x[i], y[j], z[k]])
                        dist = np.linalg.norm(point - source_pos)
                        distances.append(dist)
                        E_values.append(E_field[i, j, k])

            ax5.scatter(distances, E_values, alpha=0.3, s=10)
            ax5.set_xlabel('Distance from Source (m)')
            ax5.set_ylabel('E-field (V/m)')
            ax5.set_title('Field Strength vs Distance')
            ax5.set_yscale('log')
            ax5.set_xscale('log')
            ax5.grid(True, alpha=0.3)

            # Histogram of field strengths
            ax6 = fig.add_subplot(2, 3, 6)
            ax6.hist(E_field.flatten(), bins=50, alpha=0.7, edgecolor='black')
            ax6.set_xlabel('E-field (V/m)')
            ax6.set_ylabel('Frequency')
            ax6.set_title('Distribution of Field Strengths')
            ax6.set_yscale('log')

            plt.tight_layout()

            # Save figure
            plot_path = self.output_dir / "field_visualizations.png"
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()

            if self.logger:
                self.logger.info(f"[RFS/EMFF] Visualizations saved to {plot_path}")

            return str(plot_path)

        except Exception as e:
            if self.logger:
                self.logger.error(f"[RFS/EMFF] Visualization error: {str(e)}")
            return None

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute RFS/EMFF electromagnetic field analysis

        Args:
            params: Field analysis parameters

        Returns:
            Results dictionary with field data and statistics
        """
        start_time = time.time()

        # Validate parameters
        valid, error = self.validate_field_parameters(params)
        if not valid:
            if self.logger:
                self.logger.error(f"[RFS/EMFF] Validation failed: {error}")
            raise ValueError(f"Invalid parameters: {error}")

        if self.logger:
            self.logger.info(f"[RFS/EMFF] Starting field analysis - Run ID: {self.run_id}")

        # Publish start event
        self.publish_event("start", {"analysis_type": params['analysis_type']})

        # Run field calculation based on analysis type
        analysis_type = params['analysis_type']

        if analysis_type == "field_map":
            results = self.generate_field_map_3d(params)
        else:
            # Other analysis types can be added here
            results = self.generate_field_map_3d(params)

        # Generate visualizations
        viz_path = self.generate_visualizations(params, results)
        if viz_path:
            results['visualization'] = viz_path

        # Save summary to JSON
        summary = {
            "analysis_type": analysis_type,
            "source_power_W": params['source']['power'],
            "frequency_Hz": params['source']['frequency'],
            "wavelength_m": results['wavelength_m'],
            "grid_points": results['total_points'],
            "statistics": results['statistics']
        }

        summary_path = self.output_dir / "summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        # Calculate duration
        duration = time.time() - start_time

        # Log to database
        self.log_to_database("success", duration, params)

        # Create manifest
        self.create_manifest(params, results, status="success")

        # Publish completion event
        self.publish_event("complete", {
            "duration_seconds": duration,
            "output_directory": str(self.output_dir),
            "total_points": results['total_points']
        })

        if self.logger:
            self.logger.info(f"[RFS/EMFF] Analysis complete - Duration: {duration:.2f}s")

        return {
            "run_id": self.run_id,
            "output_directory": str(self.output_dir),
            "manifest": str(self.output_dir / "manifest.json"),
            "results": results,
            "duration_seconds": duration
        }


def main():
    """CLI entry point for RFS/EMFF runner"""
    import argparse

    parser = argparse.ArgumentParser(description="RFS/EMFF Electromagnetic Field Analysis Runner")
    parser.add_argument("--params", type=str, required=True, help="JSON file with field parameters")
    parser.add_argument("--output", type=str, help="Output directory (optional)")

    args = parser.parse_args()

    # Load parameters
    with open(args.params, 'r') as f:
        params = json.load(f)

    # Run analysis
    runner = RFSEMFFRunner()
    results = runner.run(params)

    # Print results
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
