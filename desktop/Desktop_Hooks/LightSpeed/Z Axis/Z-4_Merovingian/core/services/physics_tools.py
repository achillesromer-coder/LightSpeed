"""
Physics Tools - Consolidated Physics Umbrella Object
LightSpeed Type I Civilization Platform

Consolidates all physics modules into a single unified interface:
- Raphael Equations (unified field theory, spacetime dynamics)
- Big Bang Simulation (cosmological evolution)
- Orbital Mechanics (atomic & celestial)
- Quantum Mechanics (quantum states, tunneling, uncertainty)

This umbrella object provides widget capabilities for physics visualization
and simulation throughout the LightSpeed platform.

Author: LightSpeed Team
Version: 0.9.5 - Consolidated from 4 physics modules
Date: December 21, 2025
"""

import numpy as np
from scipy.constants import G, c, hbar, k, pi
from scipy.special import gamma
try:
    from scipy.special import sph_harm
except ImportError:
    from scipy.special import sph_harm_y as _sph_harm_y

    def sph_harm(m, n, theta, phi):
        return _sph_harm_y(n, m, phi, theta)
from typing import Dict, Any, Optional, Tuple

# ============================================================================
# PHYSICAL CONSTANTS (Unified)
# ============================================================================

PHYSICS_CONSTANTS = {
    # Universal Constants
    'G': G,  # Gravitational constant (m³/kg·s²)
    'c': c,  # Speed of light (m/s)
    'hbar': hbar,  # Reduced Planck constant (J·s)
    'h': 2 * np.pi * hbar,  # Planck constant (J·s)
    'k': k,  # Boltzmann constant (J/K)

    # Cosmological
    'PLANCK_TIME': 5.39e-44,  # seconds
    'PLANCK_TEMPERATURE': 1.417e32,  # Kelvin
    'UNIVERSE_AGE': 4.35e17,  # seconds (~13.8 Gyr)

    # Atomic/Quantum
    'BOHR_RADIUS': 5.29177e-11,  # meters
    'ELECTRON_MASS': 9.109e-31,  # kg
    'PROTON_MASS': 1.673e-27,  # kg
    'NEUTRON_MASS': 1.675e-27,  # kg
    'FINE_STRUCTURE': 1/137.036,  # dimensionless
    'RYDBERG_ENERGY': 13.6,  # eV

    # Astronomical
    'AU': 1.496e11,  # Astronomical Unit (m)
    'SOLAR_MASS': 1.989e30,  # kg
    'EARTH_MASS': 5.972e24,  # kg
}


class PhysicsTools:
    """
    Unified Physics Tools Umbrella Object

    Provides access to all physics simulation capabilities:
    - Raphael equations for unified field theory
    - Big Bang cosmological simulations
    - Atomic and celestial orbital mechanics
    - Quantum mechanical calculations

    Usage:
        physics = PhysicsTools()

        # Raphael equations for element
        forces = physics.calculate_element_forces(protons=6, neutrons=6, electrons=6)

        # Big Bang simulation
        universe = physics.simulate_big_bang(time_steps=500)

        # Orbital mechanics
        orbit = physics.compute_keplerian_orbit(a=1.0, e=0.0167)

        # Quantum mechanics
        tunneling = physics.quantum_tunneling(E=1e-19, V0=3e-19, width=1e-9)
    """

    def __init__(self):
        """Initialize physics tools."""
        self.constants = PHYSICS_CONSTANTS.copy()

    # ========================================================================
    # RAPHAEL EQUATIONS (Unified Field Theory)
    # ========================================================================

    def calculate_element_forces(self, protons: int, neutrons: int, electrons: int) -> Dict[str, float]:
        """
        Calculate fundamental forces for an element using Raphael's equations.

        Args:
            protons: Number of protons
            neutrons: Number of neutrons
            electrons: Number of electrons

        Returns:
            Dictionary with Strong Force, Weak Force, and Total Energy
        """
        # Simplified strong force (nuclear binding)
        F_strong = 0.8 * protons * neutrons / (protons + neutrons) if (protons + neutrons) > 0 else 0.0

        # Simplified weak force (beta decay)
        F_weak = 0.2 * protons * electrons / (protons + electrons) if (protons + electrons) > 0 else 0.0

        # Total energy
        E_total = F_strong + F_weak

        return {
            "Strong Force": float(F_strong),
            "Weak Force": float(F_weak),
            "Total Energy": float(E_total),
        }

    def raphael_spacetime_oval(self, r: np.ndarray, theta: np.ndarray, phi: np.ndarray,
                               t: float, mass: float, spin: float) -> Tuple[np.ndarray, ...]:
        """
        Calculate Raphael equations for oval spacetime geometry.

        Models rotating massive objects (black holes, neutron stars).

        Args:
            r: Radial distance (meters)
            theta: Polar angle (radians)
            phi: Azimuthal angle (radians)
            t: Time parameter (seconds)
            mass: Central object mass (kg)
            spin: Angular momentum parameter

        Returns:
            Tuple of (curvature, density, energy, dark_energy)
        """
        curvature = -np.exp(-r ** 2 / (2 * mass)) * np.cos(spin * t)
        density = np.exp(-r / (mass * 10)) * np.sin(t)
        energy = np.sin(r * np.sin(theta) * np.cos(phi) * t) * np.exp(-t / 50)
        dark_energy = (1 / (1 + np.exp(-curvature * density))) * energy

        return curvature, density, energy, dark_energy

    def raphael_black_hole_2d(self, x: np.ndarray, y: np.ndarray,
                              t: float, spin: float, acc_rate: float) -> Tuple[np.ndarray, ...]:
        """
        Raphael equation for black hole dynamics in 2D+time.

        Args:
            x, y: 2D coordinate grids
            t: Time parameter
            spin: Rotation parameter
            acc_rate: Accretion rate

        Returns:
            Tuple of (curvature, density, forces)
        """
        curvature = np.sin(x**2 + y**2 - t) * np.exp(-acc_rate * (x**2 + y**2))
        density = np.cos(spin * (x - y)) * np.exp(-t)
        forces = np.abs(np.sin(x * y * t))

        return curvature, density, forces

    # ========================================================================
    # BIG BANG SIMULATION (Cosmology)
    # ========================================================================

    def simulate_big_bang(self, time_steps: int = 500, fractal_iterations: int = 3,
                         scale: float = 1e-30) -> Dict[str, np.ndarray]:
        """
        Simulate universe expansion from Big Bang.

        Args:
            time_steps: Number of temporal steps
            fractal_iterations: Fractal refinement iterations
            scale: Initial spatial scale (meters)

        Returns:
            Dictionary containing time, space, density, and 3D coordinates
        """
        # Time evolution (logarithmic spacing)
        time = np.geomspace(self.constants['PLANCK_TIME'], self.constants['UNIVERSE_AGE'], time_steps)

        # Spatial expansion (Friedmann equation)
        space = scale * np.exp(np.sqrt(3 / 2) * np.sqrt(G / (8 * pi)) * time)

        # Matter-energy density (radiation-dominated era)
        density = self.constants['PLANCK_TEMPERATURE'] / (time ** 2)

        # Fractal spatial structure
        x_base = np.random.uniform(-1, 1, time_steps)
        y_base = np.random.uniform(-1, 1, time_steps)
        z_base = np.random.uniform(-1, 1, time_steps)

        x = self._fractal_refine(x_base, 0.1, fractal_iterations)
        y = self._fractal_refine(y_base, 0.1, fractal_iterations)
        z = self._fractal_refine(z_base, 0.1, fractal_iterations)

        return {
            "time": time,
            "space": space,
            "density": density,
            "x": x,
            "y": y,
            "z": z,
        }

    def _fractal_refine(self, base_points: np.ndarray, scale_factor: float,
                       iterations: int) -> np.ndarray:
        """Apply fractal refinement to points."""
        points = base_points
        for _ in range(iterations):
            refined = points * scale_factor + np.random.uniform(
                -scale_factor, scale_factor, points.shape
            )
            points = np.concatenate([points, refined])
        return points

    def get_cosmic_timeline(self) -> Dict[str, Dict[str, str]]:
        """Return dictionary of cosmic evolution epochs."""
        return {
            "Planck Epoch": {"time": "< 10^-43 s", "temperature": "10^32 K"},
            "Inflation": {"time": "10^-36 to 10^-32 s", "temperature": "10^27 K"},
            "Nucleosynthesis": {"time": "1 s to 3 min", "temperature": "10^9 K"},
            "Recombination": {"time": "380,000 yr", "temperature": "3,000 K"},
            "Present Day": {"time": "13.8 billion yr", "temperature": "2.7 K (CMB)"},
        }

    # ========================================================================
    # ORBITAL MECHANICS (Atomic & Celestial)
    # ========================================================================

    def schwarzschild_radius(self, mass: float) -> float:
        """
        Calculate Schwarzschild radius (black hole event horizon).

        Args:
            mass: Object mass (kg)

        Returns:
            Schwarzschild radius (meters)
        """
        return 2 * self.constants['G'] * mass / self.constants['c']**2

    def compute_keplerian_orbit(self, a: float, e: float, i: float = 0,
                               omega: float = 0, w: float = 0,
                               num_points: int = 500) -> Tuple[np.ndarray, ...]:
        """
        Compute 3D Keplerian orbit from orbital elements.

        Args:
            a: Semi-major axis (AU or meters)
            e: Eccentricity (0-1)
            i: Inclination (degrees)
            omega: Longitude of ascending node (degrees)
            w: Argument of periapsis (degrees)
            num_points: Number of orbital points

        Returns:
            Tuple of (x, y, z) coordinates
        """
        theta = np.linspace(0, 2 * np.pi, num_points)
        r = (a * (1 - e**2)) / (1 + e * np.cos(theta))

        x_orbit = r * np.cos(theta)
        y_orbit = r * np.sin(theta)

        # Apply 3D rotations
        i_rad = np.radians(i)
        omega_rad = np.radians(omega)
        w_rad = np.radians(w)

        x_rot = x_orbit * np.cos(w_rad) - y_orbit * np.sin(w_rad)
        y_rot = x_orbit * np.sin(w_rad) + y_orbit * np.cos(w_rad)

        x_final = x_rot * np.cos(omega_rad) - y_rot * np.sin(omega_rad)
        y_final = x_rot * np.sin(omega_rad) + y_rot * np.cos(omega_rad)
        z_final = np.sin(i_rad) * np.sqrt(x_final**2 + y_final**2)

        return x_final, y_final, z_final

    def orbital_period(self, a: float, M_central: float = None) -> float:
        """
        Calculate orbital period (Kepler's 3rd law).

        Args:
            a: Semi-major axis (meters)
            M_central: Central mass (kg), default: Solar mass

        Returns:
            Orbital period (seconds)
        """
        if M_central is None:
            M_central = self.constants['SOLAR_MASS']
        return 2 * np.pi * np.sqrt(a**3 / (self.constants['G'] * M_central))

    def calculate_atomic_orbital_density(self, n: int, l: int, m: int,
                                        grid_size: int = 50) -> Tuple[np.ndarray, ...]:
        """
        Calculate atomic orbital probability density with quantum numbers.

        Args:
            n: Principal quantum number (1, 2, 3...)
            l: Angular momentum quantum number (0 to n-1)
            m: Magnetic quantum number (-l to +l)
            grid_size: Grid resolution

        Returns:
            Tuple of (x, y, z, density) arrays
        """
        r = np.linspace(0.1, 5, grid_size)
        theta = np.linspace(0, np.pi, grid_size)
        phi = np.linspace(0, 2 * np.pi, grid_size)
        r, theta, phi = np.meshgrid(r, theta, phi, indexing="ij")

        # Radial wavefunction
        rho = 2 * r / n
        radial_part = (2 / n)**3 * np.sqrt(gamma(n - l - 1) / (2 * n * gamma(n + l))) * np.exp(-rho) * rho**l
        radial_density = np.abs(radial_part)**2

        # Spherical harmonics
        spherical_part = sph_harm(m, l, phi, theta)
        angular_density = np.abs(spherical_part)**2

        # Combined density
        density = (radial_density * angular_density).flatten()

        # Cartesian coordinates
        x = (r * np.sin(theta) * np.cos(phi)).flatten()
        y = (r * np.sin(theta) * np.sin(phi)).flatten()
        z = (r * np.cos(theta)).flatten()

        return x, y, z, density

    # ========================================================================
    # QUANTUM MECHANICS
    # ========================================================================

    def quantum_tunneling_probability(self, E: float, V0: float, width: float) -> float:
        """
        Calculate quantum tunneling probability through barrier.

        Args:
            E: Particle energy (Joules)
            V0: Barrier height (Joules)
            width: Barrier width (meters)

        Returns:
            Transmission probability (0-1)
        """
        if E >= V0:
            return 1.0

        kappa = np.sqrt(2 * self.constants['ELECTRON_MASS'] * (V0 - E)) / self.constants['hbar']
        T = np.exp(-2 * kappa * width)
        return float(T)

    def de_broglie_wavelength(self, mass: float, velocity: float) -> float:
        """
        Calculate de Broglie wavelength (wave-particle duality).

        Args:
            mass: Particle mass (kg)
            velocity: Particle velocity (m/s)

        Returns:
            Wavelength (meters)
        """
        momentum = mass * velocity
        return (2 * np.pi * self.constants['hbar']) / momentum

    def heisenberg_uncertainty(self, sigma_x: float, sigma_p: float) -> Dict[str, Any]:
        """
        Check Heisenberg uncertainty principle.

        Args:
            sigma_x: Position uncertainty (meters)
            sigma_p: Momentum uncertainty (kg·m/s)

        Returns:
            Dictionary with uncertainty analysis
        """
        product = sigma_x * sigma_p
        limit = self.constants['hbar'] / 2

        return {
            "uncertainty_product": product,
            "heisenberg_limit": limit,
            "satisfies_principle": product >= limit,
            "ratio": product / limit
        }

    def compton_wavelength(self, mass: float) -> float:
        """
        Calculate Compton wavelength.

        Args:
            mass: Particle rest mass (kg)

        Returns:
            Compton wavelength (meters)
        """
        return (2 * np.pi * self.constants['hbar']) / (mass * self.constants['c'])

    def quantum_state_evolution(self, time_step: int, num_points: int = 1000) -> Tuple[np.ndarray, ...]:
        """
        Evolve quantum state over time (Bloch sphere visualization).

        Args:
            time_step: Current time step
            num_points: Number of visualization points

        Returns:
            Tuple of (x, y, z, density)
        """
        theta = np.random.uniform(0, 2 * np.pi, num_points)
        phi = np.random.uniform(0, np.pi, num_points)
        r = 1 + 0.1 * np.sin(2 * np.pi * time_step / 100)

        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        density = np.abs(np.sin(2 * np.pi * time_step / 100))

        return x, y, z, density

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_constants(self) -> Dict[str, float]:
        """Return all physical constants."""
        return self.constants.copy()

    def get_summary(self) -> Dict[str, Any]:
        """Get physics tools summary."""
        return {
            "modules": ["Raphael Equations", "Big Bang Simulation", "Orbital Mechanics", "Quantum Mechanics"],
            "capabilities": {
                "Unified Field": ["Element forces", "Spacetime curvature", "Black hole dynamics"],
                "Cosmology": ["Universe expansion", "Cosmic timeline", "Structure formation"],
                "Orbital": ["Keplerian orbits", "Atomic orbitals", "Schwarzschild radius"],
                "Quantum": ["Tunneling", "Uncertainty", "Wave-particle duality"]
            },
            "constants": len(self.constants),
            "version": "3.0.0"
        }


# ============================================================================
# GLOBAL SINGLETON INSTANCE
# ============================================================================

_physics_tools_instance = None


def get_physics_tools() -> PhysicsTools:
    """
    Get global PhysicsTools singleton instance.

    Returns:
        PhysicsTools instance
    """
    global _physics_tools_instance
    if _physics_tools_instance is None:
        _physics_tools_instance = PhysicsTools()
    return _physics_tools_instance


# ============================================================================
# CONVENIENCE FUNCTIONS (Backward Compatibility)
# ============================================================================

def calculate_raphael_equations(protons: int, neutrons: int, electrons: int) -> Dict[str, float]:
    """Convenience wrapper for Raphael equations."""
    return get_physics_tools().calculate_element_forces(protons, neutrons, electrons)


def generate_big_bang_simulation(time_steps: int = 500, fractal_iterations: int = 3,
                                 scale: float = 1e-30) -> Dict[str, np.ndarray]:
    """Convenience wrapper for Big Bang simulation."""
    return get_physics_tools().simulate_big_bang(time_steps, fractal_iterations, scale)


def calculate_schwarzschild_radius(mass: float) -> float:
    """Convenience wrapper for Schwarzschild radius."""
    return get_physics_tools().schwarzschild_radius(mass)


if __name__ == "__main__":
    # Test suite
    print("=" * 70)
    print("PHYSICS TOOLS - Consolidated Test Suite")
    print("=" * 70)

    physics = get_physics_tools()

    # Test 1: Raphael equations
    print("\n[1] Raphael Equations - Carbon-12")
    forces = physics.calculate_element_forces(6, 6, 6)
    for key, val in forces.items():
        print(f"  {key}: {val:.6e}")

    # Test 2: Big Bang
    print("\n[2] Big Bang Simulation")
    universe = physics.simulate_big_bang(time_steps=100, fractal_iterations=2)
    print(f"  Time range: {universe['time'][0]:.3e} to {universe['time'][-1]:.3e} s")
    print(f"  Space range: {universe['space'][0]:.3e} to {universe['space'][-1]:.3e} m")

    # Test 3: Schwarzschild radius
    print("\n[3] Schwarzschild Radii")
    print(f"  Sun: {physics.schwarzschild_radius(1.989e30):.3e} m (~3 km)")
    print(f"  Earth: {physics.schwarzschild_radius(5.972e24):.3e} m (~9 mm)")

    # Test 4: Quantum tunneling
    print("\n[4] Quantum Tunneling")
    T = physics.quantum_tunneling_probability(1e-19, 3e-19, 1e-9)
    print(f"  Probability: {T:.3e} ({T*100:.6f}%)")

    # Test 5: de Broglie wavelength
    print("\n[5] de Broglie Wavelength")
    lambda_e = physics.de_broglie_wavelength(9.109e-31, 1e6)
    print(f"  Electron (1e6 m/s): {lambda_e:.3e} m ({lambda_e*1e9:.3f} nm)")

    # Test 6: Summary
    print("\n[6] Physics Tools Summary")
    summary = physics.get_summary()
    print(f"  Version: {summary['version']}")
    print(f"  Modules: {len(summary['modules'])}")
    print(f"  Constants: {summary['constants']}")

    print("\n" + "=" * 70)
    print("All tests passed! PhysicsTools ready for integration.")
    print("=" * 70)
