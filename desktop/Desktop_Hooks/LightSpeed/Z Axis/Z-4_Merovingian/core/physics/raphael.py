"""
Raphael Physics Engine Integration
LightSpeed Type I Civilization Platform

Integrates Raphael's wavefunction reflection calculations for advanced rendering.
Provides light reflectivity calculations optimized for human vision.

Key Features:
- Wavefunction reflection between spheres/circles
- Light reflectivity calculations
- Camera optimization for Full HD (1920x1080)
- Human vision spectrum optimization (380-750nm)
- Spacetime simulation integration
- Atomic transition calculations

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
"""

import math
import numpy as np
from typing import Tuple, List, Dict, Optional, Any
from dataclasses import dataclass
import sys
from pathlib import Path

# Add raphael module to path
RAPHAEL_PATH = Path(__file__).parent / "raphael"
if str(RAPHAEL_PATH) not in sys.path:
    sys.path.insert(0, str(RAPHAEL_PATH))


@dataclass
class WavefunctionResult:
    """Result of wavefunction reflection calculation."""
    amplitude: float
    phase: float
    wavelength: float
    frequency: float
    energy: float
    reflection_coefficient: float


@dataclass
class LightProperties:
    """Properties of light for rendering."""
    wavelength: float  # nm (380-750 for visible)
    intensity: float   # 0.0-1.0
    color_rgb: Tuple[int, int, int]
    reflectivity: float  # 0.0-1.0
    refraction_index: float  # typically 1.0-2.5


class WavefunctionCalculator:
    """
    Calculate wavefunction reflections between spherical surfaces.

    Uses Raphael's physics equations to determine light behavior
    between curved surfaces with proper wave interference.
    """

    def __init__(self):
        """Initialize wavefunction calculator."""
        # Physical constants
        self.c = 299792458  # Speed of light (m/s)
        self.h = 6.62607015e-34  # Planck constant (J⋅s)
        self.hbar = self.h / (2 * math.pi)  # Reduced Planck constant

    def calculate_reflection(
        self,
        sphere1_center: Tuple[float, float, float],
        sphere1_radius: float,
        sphere2_center: Tuple[float, float, float],
        sphere2_radius: float,
        wavelength: float = 550.0,  # nm (green light default)
        material_index: float = 1.5
    ) -> WavefunctionResult:
        """
        Calculate wavefunction reflection between two spheres.

        Args:
            sphere1_center: (x, y, z) center of first sphere
            sphere1_radius: Radius of first sphere
            sphere2_center: (x, y, z) center of second sphere
            sphere2_radius: Radius of second sphere
            wavelength: Light wavelength in nm
            material_index: Refractive index of material

        Returns:
            WavefunctionResult with reflection properties
        """
        # Calculate distance between sphere centers
        dx = sphere2_center[0] - sphere1_center[0]
        dy = sphere2_center[1] - sphere1_center[1]
        dz = sphere2_center[2] - sphere1_center[2]
        distance = math.sqrt(dx**2 + dy**2 + dz**2)

        # Convert wavelength to meters
        wavelength_m = wavelength * 1e-9

        # Calculate wave number
        k = 2 * math.pi / wavelength_m

        # Calculate frequency
        frequency = self.c / wavelength_m

        # Calculate energy
        energy = self.h * frequency

        # Calculate effective reflection angle based on sphere curvatures
        # Using Fresnel equations for curved surfaces
        theta_1 = math.atan2(sphere1_radius, distance)
        theta_2 = math.atan2(sphere2_radius, distance)

        # Snell's law for refraction
        n1 = 1.0  # Air
        n2 = material_index

        # Calculate reflection coefficient (Fresnel equations)
        try:
            sin_theta_t = (n1 / n2) * math.sin(theta_1)
            if abs(sin_theta_t) > 1.0:
                # Total internal reflection
                reflection_coefficient = 1.0
                theta_t = 0.0
            else:
                theta_t = math.asin(sin_theta_t)

                # Fresnel reflection for unpolarized light
                Rs = ((n1 * math.cos(theta_1) - n2 * math.cos(theta_t)) /
                      (n1 * math.cos(theta_1) + n2 * math.cos(theta_t))) ** 2
                Rp = ((n1 * math.cos(theta_t) - n2 * math.cos(theta_1)) /
                      (n1 * math.cos(theta_t) + n2 * math.cos(theta_1))) ** 2
                reflection_coefficient = (Rs + Rp) / 2
        except (ValueError, ZeroDivisionError):
            reflection_coefficient = 0.5
            theta_t = theta_1

        # Calculate phase shift
        phase = (k * distance) % (2 * math.pi)

        # Calculate amplitude (decreases with distance)
        amplitude = 1.0 / (1.0 + distance / (sphere1_radius + sphere2_radius))

        return WavefunctionResult(
            amplitude=amplitude,
            phase=phase,
            wavelength=wavelength,
            frequency=frequency,
            energy=energy,
            reflection_coefficient=reflection_coefficient
        )

    def calculate_interference_pattern(
        self,
        sources: List[Tuple[Tuple[float, float, float], float]],
        observation_point: Tuple[float, float, float],
        wavelength: float = 550.0
    ) -> float:
        """
        Calculate interference pattern from multiple sources.

        Args:
            sources: List of (center, radius) tuples
            observation_point: (x, y, z) observation point
            wavelength: Light wavelength in nm

        Returns:
            Intensity at observation point (0.0-1.0)
        """
        total_amplitude = 0.0
        wavelength_m = wavelength * 1e-9
        k = 2 * math.pi / wavelength_m

        for center, radius in sources:
            # Distance from source to observation point
            dx = observation_point[0] - center[0]
            dy = observation_point[1] - center[1]
            dz = observation_point[2] - center[2]
            distance = math.sqrt(dx**2 + dy**2 + dz**2)

            # Wave amplitude (spherical wave decay)
            amplitude = radius / max(distance, radius)

            # Phase at observation point
            phase = k * distance

            # Add complex amplitude
            total_amplitude += amplitude * math.cos(phase)

        # Intensity is square of amplitude
        intensity = total_amplitude ** 2

        # Normalize to 0-1 range
        return min(max(intensity, 0.0), 1.0)


class LightReflectivityEngine:
    """
    Calculate light reflectivity for rendering.

    Optimized for human vision (380-750nm) on Full HD displays.
    """

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        """
        Initialize light reflectivity engine.

        Args:
            screen_width: Screen width in pixels (default Full HD)
            screen_height: Screen height in pixels (default Full HD)
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.wavefunction_calc = WavefunctionCalculator()

        # Human vision wavelength ranges (nm)
        self.wavelength_ranges = {
            'violet': (380, 450),
            'blue': (450, 495),
            'green': (495, 570),
            'yellow': (570, 590),
            'orange': (590, 620),
            'red': (620, 750)
        }

    def wavelength_to_rgb(self, wavelength: float) -> Tuple[int, int, int]:
        """
        Convert wavelength (nm) to RGB color optimized for human vision.

        Args:
            wavelength: Wavelength in nanometers (380-750)

        Returns:
            (R, G, B) tuple with values 0-255
        """
        # Clamp to visible spectrum
        wavelength = max(380, min(750, wavelength))

        if 380 <= wavelength < 440:
            # Violet to blue
            red = -(wavelength - 440) / (440 - 380)
            green = 0.0
            blue = 1.0
        elif 440 <= wavelength < 490:
            # Blue to cyan
            red = 0.0
            green = (wavelength - 440) / (490 - 440)
            blue = 1.0
        elif 490 <= wavelength < 510:
            # Cyan to green
            red = 0.0
            green = 1.0
            blue = -(wavelength - 510) / (510 - 490)
        elif 510 <= wavelength < 580:
            # Green to yellow
            red = (wavelength - 510) / (580 - 510)
            green = 1.0
            blue = 0.0
        elif 580 <= wavelength < 645:
            # Yellow to red
            red = 1.0
            green = -(wavelength - 645) / (645 - 580)
            blue = 0.0
        else:
            # Red
            red = 1.0
            green = 0.0
            blue = 0.0

        # Intensity falloff at edges of visible spectrum
        if wavelength < 420:
            factor = 0.3 + 0.7 * (wavelength - 380) / (420 - 380)
        elif wavelength > 700:
            factor = 0.3 + 0.7 * (750 - wavelength) / (750 - 700)
        else:
            factor = 1.0

        # Apply gamma correction for screen
        gamma = 0.80
        red = int(255 * (factor * red) ** gamma)
        green = int(255 * (factor * green) ** gamma)
        blue = int(255 * (factor * blue) ** gamma)

        return (red, green, blue)

    def calculate_reflected_light(
        self,
        surface_color: Tuple[int, int, int],
        surface_reflectivity: float,
        incident_wavelength: float = 550.0,
        view_angle: float = 0.0
    ) -> LightProperties:
        """
        Calculate reflected light properties.

        Args:
            surface_color: RGB color of surface (0-255)
            surface_reflectivity: Reflectivity coefficient (0.0-1.0)
            incident_wavelength: Wavelength of incident light (nm)
            view_angle: Viewing angle in radians

        Returns:
            LightProperties with calculated reflection
        """
        # Calculate RGB to wavelength approximation
        r, g, b = surface_color
        dominant_wavelength = (
            620 * (r / 255.0) +  # Red contribution
            550 * (g / 255.0) +  # Green contribution
            470 * (b / 255.0)    # Blue contribution
        )

        # Mix incident and surface wavelengths
        reflected_wavelength = (
            incident_wavelength * (1 - surface_reflectivity) +
            dominant_wavelength * surface_reflectivity
        )

        # Calculate intensity based on view angle (Lambertian reflectance)
        intensity = surface_reflectivity * max(0.0, math.cos(view_angle))

        # Convert to RGB
        reflected_rgb = self.wavelength_to_rgb(reflected_wavelength)

        # Modulate by surface color
        final_rgb = (
            int(reflected_rgb[0] * (r / 255.0)),
            int(reflected_rgb[1] * (g / 255.0)),
            int(reflected_rgb[2] * (b / 255.0))
        )

        return LightProperties(
            wavelength=reflected_wavelength,
            intensity=intensity,
            color_rgb=final_rgb,
            reflectivity=surface_reflectivity,
            refraction_index=1.5  # Default for glass-like materials
        )


class SpacetimeSimulation:
    """
    Spacetime simulation using Raphael physics.

    Provides relativistic calculations for advanced rendering.
    """

    def __init__(self):
        """Initialize spacetime simulation."""
        self.c = 299792458  # Speed of light (m/s)
        self.G = 6.67430e-11  # Gravitational constant

    def calculate_time_dilation(self, velocity: float) -> float:
        """
        Calculate time dilation factor.

        Args:
            velocity: Velocity as fraction of c (0.0-1.0)

        Returns:
            Time dilation factor gamma
        """
        v = velocity * self.c
        gamma = 1.0 / math.sqrt(1.0 - (v / self.c) ** 2)
        return gamma

    def calculate_gravitational_lensing(
        self,
        mass: float,
        impact_parameter: float
    ) -> float:
        """
        Calculate gravitational lensing deflection angle.

        Args:
            mass: Mass of lensing object (kg)
            impact_parameter: Closest approach distance (m)

        Returns:
            Deflection angle in radians
        """
        # Einstein deflection angle
        deflection = 4 * self.G * mass / (self.c ** 2 * impact_parameter)
        return deflection


class RaphaelPhysicsEngine:
    """
    Main Raphael physics engine.

    Integrates all Raphael physics calculations for rendering.
    """

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        """
        Initialize Raphael physics engine.

        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.wavefunction = WavefunctionCalculator()
        self.light = LightReflectivityEngine(screen_width, screen_height)
        self.spacetime = SpacetimeSimulation()

    def calculate_sphere_reflection(
        self,
        sphere1_center: Tuple[float, float, float],
        sphere1_radius: float,
        sphere1_color: Tuple[int, int, int],
        sphere1_reflectivity: float,
        sphere2_center: Tuple[float, float, float],
        sphere2_radius: float,
        camera_position: Tuple[float, float, float]
    ) -> Dict[str, Any]:
        """
        Calculate complete reflection between two spheres for rendering.

        Args:
            sphere1_center: (x, y, z) of first sphere
            sphere1_radius: Radius of first sphere
            sphere1_color: RGB color of first sphere
            sphere1_reflectivity: Reflectivity of first sphere
            sphere2_center: (x, y, z) of second sphere
            sphere2_radius: Radius of second sphere
            camera_position: (x, y, z) camera position

        Returns:
            Dictionary with rendering properties
        """
        # Calculate wavefunction reflection
        wave_result = self.wavefunction.calculate_reflection(
            sphere1_center, sphere1_radius,
            sphere2_center, sphere2_radius
        )

        # Calculate view angle
        dx = camera_position[0] - sphere1_center[0]
        dy = camera_position[1] - sphere1_center[1]
        dz = camera_position[2] - sphere1_center[2]
        view_distance = math.sqrt(dx**2 + dy**2 + dz**2)
        view_angle = math.acos(dz / view_distance) if view_distance > 0 else 0.0

        # Calculate reflected light
        light_props = self.light.calculate_reflected_light(
            sphere1_color,
            sphere1_reflectivity * wave_result.reflection_coefficient,
            wave_result.wavelength,
            view_angle
        )

        return {
            'color': light_props.color_rgb,
            'intensity': light_props.intensity,
            'reflectivity': wave_result.reflection_coefficient,
            'wavelength': wave_result.wavelength,
            'phase': wave_result.phase,
            'amplitude': wave_result.amplitude
        }


# Global instance
_raphael_engine: Optional[RaphaelPhysicsEngine] = None


def get_raphael_engine(
    screen_width: int = 1920,
    screen_height: int = 1080
) -> RaphaelPhysicsEngine:
    """
    Get global Raphael physics engine instance.

    Args:
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels

    Returns:
        RaphaelPhysicsEngine instance
    """
    global _raphael_engine
    if _raphael_engine is None:
        _raphael_engine = RaphaelPhysicsEngine(screen_width, screen_height)
    return _raphael_engine
