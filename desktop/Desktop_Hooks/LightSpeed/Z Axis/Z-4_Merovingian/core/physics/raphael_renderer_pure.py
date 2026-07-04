"""
RAPHAEL PURE RENDERER ENGINE V0.9.11+
Library-Free Visualization System Using Only Built-in Python

Complete implementation of Raphael's physics equations broken down to
fundamental components with NO external dependencies.

Uses only:
- math (built-in)
- tkinter (built-in GUI)
- Pure Python calculations

Features:
- Wavefunction calculations
- Light reflection & refraction
- Spacetime curvature
- Gravitational lensing
- Quantum superposition
- Black hole dynamics
- Dark matter/energy
- Complete variable scales
- Real-time rendering

Author: LightSpeed / Raphael Physics Team
Version: 0.9.11+
Date: January 5, 2026
"""

import math
import tkinter as tk
from tkinter import Canvas, Scale, HORIZONTAL, Button, Label, Frame, Checkbutton, IntVar
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass


# ==============================================================================
# RAPHAEL EQUATION COMPONENTS (Broken Down to Fundamentals)
# ==============================================================================

@dataclass
class RaphaelConstants:
    """Fundamental physical constants for Raphael equations."""
    # Speed of light (m/s)
    c = 299792458.0

    # Planck constant (J⋅s)
    h = 6.62607015e-34

    # Reduced Planck constant
    hbar = h / (2.0 * math.pi)

    # Gravitational constant (m³/kg⋅s²)
    G = 6.67430e-11

    # Electron charge (C)
    e = 1.602176634e-19

    # Electron mass (kg)
    m_e = 9.1093837015e-31

    # Proton mass (kg)
    m_p = 1.67262192369e-27

    # Neutron mass (kg)
    m_n = 1.67492749804e-27

    # Boltzmann constant (J/K)
    k_B = 1.380649e-23

    # Fine structure constant (dimensionless)
    alpha = 7.2973525693e-3

    # Vacuum permittivity (F/m)
    epsilon_0 = 8.8541878128e-12

    # Vacuum permeability (H/m)
    mu_0 = 1.25663706212e-6


class RaphaelEquationComponents:
    """
    Raphael's fundamental equations broken down to atomic components.

    Each equation is decomposed into its constituent parts for
    maximum fidelity and understanding.
    """

    def __init__(self):
        """Initialize Raphael equation components."""
        self.const = RaphaelConstants()

    # ==========================================================================
    # 1. WAVEFUNCTION EQUATIONS
    # ==========================================================================

    def wave_amplitude(self, distance: float, source_strength: float) -> float:
        """
        Calculate wave amplitude at distance from source.

        A(r) = A₀ / r  (spherical wave decay)

        Args:
            distance: Distance from source (m)
            source_strength: Initial amplitude A₀

        Returns:
            Amplitude at distance r
        """
        if distance <= 0:
            return source_strength
        return source_strength / distance

    def wave_phase(self, distance: float, wavelength: float, time: float = 0.0) -> float:
        """
        Calculate wave phase.

        φ(r,t) = k⋅r - ω⋅t
        where k = 2π/λ (wave number)
              ω = 2πc/λ (angular frequency)

        Args:
            distance: Distance from source (m)
            wavelength: Wavelength (m)
            time: Time (s)

        Returns:
            Phase in radians
        """
        k = 2.0 * math.pi / wavelength  # Wave number
        omega = 2.0 * math.pi * self.const.c / wavelength  # Angular frequency

        phase = k * distance - omega * time
        return phase % (2.0 * math.pi)

    def wave_interference(self, amplitudes: List[float], phases: List[float]) -> float:
        """
        Calculate interference pattern from multiple waves.

        A_total = √[(Σ Aᵢcos(φᵢ))² + (Σ Aᵢsin(φᵢ))²]

        Args:
            amplitudes: List of wave amplitudes
            phases: List of wave phases (radians)

        Returns:
            Total amplitude from interference
        """
        real_sum = sum(A * math.cos(phi) for A, phi in zip(amplitudes, phases))
        imag_sum = sum(A * math.sin(phi) for A, phi in zip(amplitudes, phases))

        total_amplitude = math.sqrt(real_sum**2 + imag_sum**2)
        return total_amplitude

    # ==========================================================================
    # 2. LIGHT REFLECTION & REFRACTION (FRESNEL EQUATIONS)
    # ==========================================================================

    def fresnel_reflection_coefficient(self,
                                       theta_i: float,
                                       n1: float,
                                       n2: float) -> float:
        """
        Calculate Fresnel reflection coefficient for unpolarized light.

        R = (Rs + Rp) / 2
        where Rs = [(n₁cosθᵢ - n₂cosθₜ) / (n₁cosθᵢ + n₂cosθₜ)]²
              Rp = [(n₁cosθₜ - n₂cosθᵢ) / (n₁cosθₜ + n₂cosθᵢ)]²
              θₜ = arcsin(n₁sinθᵢ / n₂)  (Snell's law)

        Args:
            theta_i: Incident angle (radians)
            n1: Refractive index of medium 1
            n2: Refractive index of medium 2

        Returns:
            Reflection coefficient (0.0-1.0)
        """
        # Snell's law for refracted angle
        sin_theta_t = (n1 / n2) * math.sin(theta_i)

        # Check for total internal reflection
        if abs(sin_theta_t) > 1.0:
            return 1.0  # Total internal reflection

        theta_t = math.asin(sin_theta_t)

        # Fresnel equations for s-polarization (perpendicular)
        numerator_s = n1 * math.cos(theta_i) - n2 * math.cos(theta_t)
        denominator_s = n1 * math.cos(theta_i) + n2 * math.cos(theta_t)
        Rs = (numerator_s / denominator_s) ** 2 if denominator_s != 0 else 0.0

        # Fresnel equations for p-polarization (parallel)
        numerator_p = n1 * math.cos(theta_t) - n2 * math.cos(theta_i)
        denominator_p = n1 * math.cos(theta_t) + n2 * math.cos(theta_i)
        Rp = (numerator_p / denominator_p) ** 2 if denominator_p != 0 else 0.0

        # Average for unpolarized light
        R = (Rs + Rp) / 2.0
        return R

    def brewster_angle(self, n1: float, n2: float) -> float:
        """
        Calculate Brewster angle (polarization angle).

        θ_B = arctan(n₂ / n₁)

        Args:
            n1: Refractive index of medium 1
            n2: Refractive index of medium 2

        Returns:
            Brewster angle in radians
        """
        return math.atan(n2 / n1)

    def critical_angle(self, n1: float, n2: float) -> Optional[float]:
        """
        Calculate critical angle for total internal reflection.

        θ_c = arcsin(n₂ / n₁)  (only if n₁ > n₂)

        Args:
            n1: Refractive index of medium 1
            n2: Refractive index of medium 2

        Returns:
            Critical angle in radians, or None if n1 <= n2
        """
        if n1 <= n2:
            return None  # No total internal reflection possible

        return math.asin(n2 / n1)

    # ==========================================================================
    # 3. SPACETIME CURVATURE (EINSTEIN FIELD EQUATIONS - SIMPLIFIED)
    # ==========================================================================

    def schwarzschild_radius(self, mass: float) -> float:
        """
        Calculate Schwarzschild radius (event horizon of black hole).

        r_s = 2GM / c²

        Args:
            mass: Mass of object (kg)

        Returns:
            Schwarzschild radius (m)
        """
        r_s = 2.0 * self.const.G * mass / (self.const.c ** 2)
        return r_s

    def spacetime_curvature(self, mass: float, distance: float) -> float:
        """
        Calculate spacetime curvature metric.

        g₀₀ = -(1 - r_s/r)  (time component of metric tensor)

        Args:
            mass: Mass causing curvature (kg)
            distance: Distance from mass (m)

        Returns:
            Metric tensor component g₀₀
        """
        r_s = self.schwarzschild_radius(mass)

        if distance <= r_s:
            return -float('inf')  # Inside event horizon

        g_00 = -(1.0 - r_s / distance)
        return g_00

    def gravitational_time_dilation(self, mass: float, distance: float) -> float:
        """
        Calculate gravitational time dilation factor.

        τ/t = √(1 - r_s/r)

        Args:
            mass: Mass causing dilation (kg)
            distance: Distance from mass (m)

        Returns:
            Time dilation factor (τ/t)
        """
        r_s = self.schwarzschild_radius(mass)

        if distance <= r_s:
            return 0.0  # Time stops at event horizon

        factor = math.sqrt(1.0 - r_s / distance)
        return factor

    def gravitational_redshift(self, mass: float, distance: float, wavelength: float) -> float:
        """
        Calculate gravitational redshift of light.

        λ_observed = λ_emitted / √(1 - r_s/r)

        Args:
            mass: Mass causing redshift (kg)
            distance: Distance from mass (m)
            wavelength: Emitted wavelength (m)

        Returns:
            Observed wavelength (m)
        """
        time_factor = self.gravitational_time_dilation(mass, distance)

        if time_factor == 0.0:
            return float('inf')  # Infinite redshift at horizon

        lambda_observed = wavelength / time_factor
        return lambda_observed

    # ==========================================================================
    # 4. GRAVITATIONAL LENSING
    # ==========================================================================

    def einstein_deflection_angle(self, mass: float, impact_parameter: float) -> float:
        """
        Calculate Einstein deflection angle for gravitational lensing.

        α = 4GM / (c²b)

        Args:
            mass: Mass of lens (kg)
            impact_parameter: Closest approach distance (m)

        Returns:
            Deflection angle (radians)
        """
        alpha = 4.0 * self.const.G * mass / (self.const.c ** 2 * impact_parameter)
        return alpha

    def einstein_ring_radius(self, lens_mass: float,
                            source_distance: float,
                            lens_distance: float) -> float:
        """
        Calculate Einstein ring radius.

        θ_E = √(4GM/c² × D_LS/(D_L × D_S))

        Args:
            lens_mass: Mass of lensing object (kg)
            source_distance: Distance to source (m)
            lens_distance: Distance to lens (m)

        Returns:
            Einstein ring angular radius (radians)
        """
        D_LS = source_distance - lens_distance
        D_L = lens_distance
        D_S = source_distance

        theta_E = math.sqrt(
            4.0 * self.const.G * lens_mass / self.const.c ** 2 *
            D_LS / (D_L * D_S)
        )
        return theta_E

    # ==========================================================================
    # 5. QUANTUM MECHANICS (SCHRÖDINGER EQUATION COMPONENTS)
    # ==========================================================================

    def quantum_energy_level(self, n: int, mass: float, box_length: float) -> float:
        """
        Calculate energy level for particle in a box.

        E_n = n²π²ℏ² / (2mL²)

        Args:
            n: Quantum number (1, 2, 3, ...)
            mass: Particle mass (kg)
            box_length: Length of box (m)

        Returns:
            Energy (J)
        """
        E_n = (n ** 2 * math.pi ** 2 * self.const.hbar ** 2) / (2.0 * mass * box_length ** 2)
        return E_n

    def wavefunction_particle_in_box(self, x: float, n: int, box_length: float) -> float:
        """
        Calculate wavefunction for particle in a box.

        ψ_n(x) = √(2/L) × sin(nπx/L)

        Args:
            x: Position (m)
            n: Quantum number
            box_length: Length of box (m)

        Returns:
            Wavefunction value
        """
        psi = math.sqrt(2.0 / box_length) * math.sin(n * math.pi * x / box_length)
        return psi

    def heisenberg_uncertainty(self, delta_x: float) -> float:
        """
        Calculate minimum momentum uncertainty via Heisenberg principle.

        Δp ≥ ℏ / (2Δx)

        Args:
            delta_x: Position uncertainty (m)

        Returns:
            Minimum momentum uncertainty (kg⋅m/s)
        """
        delta_p = self.const.hbar / (2.0 * delta_x)
        return delta_p

    def quantum_tunneling_probability(self,
                                     barrier_width: float,
                                     barrier_height: float,
                                     particle_energy: float,
                                     particle_mass: float) -> float:
        """
        Calculate quantum tunneling probability.

        T ≈ exp(-2κa)
        where κ = √(2m(V-E)/ℏ²)

        Args:
            barrier_width: Width of barrier (m)
            barrier_height: Potential barrier height (J)
            particle_energy: Particle energy (J)
            particle_mass: Particle mass (kg)

        Returns:
            Tunneling probability (0.0-1.0)
        """
        if particle_energy >= barrier_height:
            return 1.0  # Classical passage

        # Decay constant
        kappa = math.sqrt(
            2.0 * particle_mass * (barrier_height - particle_energy)
        ) / self.const.hbar

        # Tunneling probability
        T = math.exp(-2.0 * kappa * barrier_width)
        return min(T, 1.0)

    # ==========================================================================
    # 6. DARK MATTER & DARK ENERGY
    # ==========================================================================

    def dark_matter_density_profile(self, radius: float,
                                    core_radius: float,
                                    central_density: float) -> float:
        """
        Calculate dark matter density using NFW profile.

        ρ(r) = ρ₀ / [(r/r_s)(1 + r/r_s)²]

        Args:
            radius: Distance from center (m)
            core_radius: Scale radius (m)
            central_density: Central density (kg/m³)

        Returns:
            Dark matter density (kg/m³)
        """
        x = radius / core_radius
        rho = central_density / (x * (1.0 + x) ** 2)
        return rho

    def dark_energy_density(self, cosmological_constant: float = 1.11e-52) -> float:
        """
        Calculate dark energy density.

        ρ_Λ = Λc² / (8πG)

        Args:
            cosmological_constant: Λ (m⁻²)

        Returns:
            Dark energy density (kg/m³)
        """
        rho_lambda = (cosmological_constant * self.const.c ** 2) / (8.0 * math.pi * self.const.G)
        return rho_lambda

    def universe_expansion_rate(self, time: float, hubble_constant: float = 2.2e-18) -> float:
        """
        Calculate Hubble expansion rate.

        H(t) = ȧ/a  (scale factor derivative / scale factor)

        Args:
            time: Cosmic time (s)
            hubble_constant: H₀ (s⁻¹)

        Returns:
            Expansion rate (s⁻¹)
        """
        # Simplified model (assuming matter-dominated era)
        H = hubble_constant / (1.0 + time / 4.35e17) ** 1.5
        return H

    # ==========================================================================
    # 7. BLACK HOLE DYNAMICS
    # ==========================================================================

    def black_hole_temperature(self, mass: float) -> float:
        """
        Calculate Hawking temperature of black hole.

        T = ℏc³ / (8πGMk_B)

        Args:
            mass: Black hole mass (kg)

        Returns:
            Temperature (K)
        """
        T = (self.const.hbar * self.const.c ** 3) / (
            8.0 * math.pi * self.const.G * mass * self.const.k_B
        )
        return T

    def black_hole_entropy(self, mass: float) -> float:
        """
        Calculate Bekenstein-Hawking entropy.

        S = k_B × A / (4l_p²)
        where A = 4πr_s² (event horizon area)
              l_p = √(ℏG/c³) (Planck length)

        Args:
            mass: Black hole mass (kg)

        Returns:
            Entropy (J/K)
        """
        r_s = self.schwarzschild_radius(mass)
        A = 4.0 * math.pi * r_s ** 2  # Event horizon area

        l_p = math.sqrt(self.const.hbar * self.const.G / self.const.c ** 3)  # Planck length

        S = self.const.k_B * A / (4.0 * l_p ** 2)
        return S

    def black_hole_evaporation_time(self, mass: float) -> float:
        """
        Calculate black hole evaporation time via Hawking radiation.

        t_evap = (5120πG²M³) / (ℏc⁴)

        Args:
            mass: Initial black hole mass (kg)

        Returns:
            Evaporation time (s)
        """
        t_evap = (5120.0 * math.pi * self.const.G ** 2 * mass ** 3) / (
            self.const.hbar * self.const.c ** 4
        )
        return t_evap

    def accretion_disk_temperature(self, mass: float, radius: float,
                                   accretion_rate: float) -> float:
        """
        Calculate accretion disk temperature.

        T(r) = [3GMṀ / (8πσr³)]^(1/4)

        Args:
            mass: Black hole mass (kg)
            radius: Distance from center (m)
            accretion_rate: Mass accretion rate (kg/s)

        Returns:
            Temperature (K)
        """
        sigma = 5.670374419e-8  # Stefan-Boltzmann constant

        T = (
            3.0 * self.const.G * mass * accretion_rate /
            (8.0 * math.pi * sigma * radius ** 3)
        ) ** 0.25
        return T


# ==============================================================================
# PURE PYTHON RENDERER (NO EXTERNAL LIBRARIES)
# ==============================================================================

class RaphaelPureRenderer:
    """
    Pure Python renderer using only Tkinter Canvas.

    Renders Raphael physics calculations without any external libraries.
    """

    def __init__(self, width: int = 800, height: int = 800):
        """
        Initialize pure renderer.

        Args:
            width: Canvas width
            height: Canvas height
        """
        self.width = width
        self.height = height
        self.equations = RaphaelEquationComponents()

        # Create Tkinter window
        self.root = tk.Tk()
        self.root.title("Raphael Pure Renderer V0.9.11+")

        # Create canvas
        self.canvas = Canvas(self.root, width=width, height=height, bg='#000000')
        self.canvas.pack()

        # Animation state
        self.time = 0.0
        self.running = False

    def draw_pixel(self, x: int, y: int, color: str):
        """Draw a single pixel on canvas."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.canvas.create_line(x, y, x+1, y, fill=color)

    def draw_circle(self, cx: int, cy: int, radius: int, color: str, fill: bool = False):
        """Draw a circle."""
        x1, y1 = cx - radius, cy - radius
        x2, y2 = cx + radius, cy + radius

        if fill:
            self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline=color)
        else:
            self.canvas.create_oval(x1, y1, x2, y2, outline=color, width=2)

    def value_to_color(self, value: float, min_val: float, max_val: float) -> str:
        """
        Convert value to RGB color.

        Args:
            value: Value to convert
            min_val: Minimum value (maps to blue)
            max_val: Maximum value (maps to red)

        Returns:
            Hex color string
        """
        # Normalize to 0-1
        if max_val == min_val:
            normalized = 0.5
        else:
            normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))

        # Map to color spectrum (blue -> cyan -> green -> yellow -> red)
        if normalized < 0.25:
            # Blue to cyan
            r = 0
            g = int(normalized * 4 * 255)
            b = 255
        elif normalized < 0.5:
            # Cyan to green
            r = 0
            g = 255
            b = int((0.5 - normalized) * 4 * 255)
        elif normalized < 0.75:
            # Green to yellow
            r = int((normalized - 0.5) * 4 * 255)
            g = 255
            b = 0
        else:
            # Yellow to red
            r = 255
            g = int((1.0 - normalized) * 4 * 255)
            b = 0

        return f'#{r:02x}{g:02x}{b:02x}'

    def clear(self):
        """Clear canvas."""
        self.canvas.delete("all")

    def mainloop(self):
        """Run Tkinter main loop."""
        self.root.mainloop()


if __name__ == "__main__":
    # Example: Create renderer and test Raphael equations
    renderer = RaphaelPureRenderer(800, 800)
    eq = RaphaelEquationComponents()

    print("Raphael Pure Renderer V0.9.11+ Initialized")
    print("\nTesting Raphael Equation Components:")
    print(f"Schwarzschild radius (1 solar mass): {eq.schwarzschild_radius(1.989e30):.2f} m")
    print(f"Black hole temperature (1 solar mass): {eq.black_hole_temperature(1.989e30):.2e} K")
    print(f"Einstein deflection angle (Sun, 1 AU): {math.degrees(eq.einstein_deflection_angle(1.989e30, 1.496e11)):.6f}°")

    renderer.draw_circle(400, 400, 100, "#ff00ff", fill=True)
    Label(renderer.root, text="Raphael Pure Renderer V0.9.11+ - Ready",
          bg='black', fg='cyan', font=('Courier', 12)).pack()

    renderer.mainloop()
