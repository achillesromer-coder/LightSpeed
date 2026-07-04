"""
Raphael Equations Module
TheConstruct Layer - Core Physics Equations

This module contains Raphael's unified field equations that describe
the fundamental forces and energy dynamics across quantum to cosmic scales.

Author: LightSpeed Team
Version: 0.9.5
"""

import numpy as np
from sympy import symbols, lambdify
from scipy.constants import G, pi

# Symbolic variables for Raphael equations
p, n, e = symbols('p n e')  # protons, neutrons, electrons


def calculate_raphael_equations(protons, neutrons, electrons):
    """
    Calculate the fundamental forces for a given element using Raphael's equations.

    Raphael's equations provide a simplified unified field theory that combines
    strong and weak nuclear forces to determine total energy dynamics.

    Parameters:
        protons (int): Number of protons in the nucleus
        neutrons (int): Number of neutrons in the nucleus
        electrons (int): Number of electrons in the atom

    Returns:
        dict: Dictionary containing:
            - "Strong Force": Simplified strong nuclear force
            - "Weak Force": Simplified weak nuclear force
            - "Total Energy": Combined energy (sum of forces)

    Notes:
        These are simplified placeholder equations. For production use,
        should be replaced with QCD and electroweak calculations.
    """
    # Simplified strong force (nuclear binding)
    F_strong = 0.8 * p * n / (p + n)

    # Simplified weak force (beta decay interactions)
    F_weak = 0.2 * p * e / (p + e)

    # Total energy (combined force dynamics)
    E_total = F_strong + F_weak

    # Substitute values for protons, neutrons, and electrons
    forces = {
        "Strong Force": float(F_strong.subs({p: protons, n: neutrons})),
        "Weak Force": float(F_weak.subs({p: protons, e: electrons})),
        "Total Energy": float(E_total.subs({p: protons, n: neutrons, e: electrons})),
    }

    return forces


def raphael_equations_oval(r, theta, phi, t, mass, spin):
    """
    Elliptical Raphael equations for spacetime curvature, density, energy,
    and dark energy dynamics in spherical coordinates.

    These equations describe the evolution of spacetime around massive rotating objects
    (black holes, neutron stars, galactic cores) using an oval/elliptical geometry.

    Parameters:
        r (np.ndarray): Radial distance from center (meters)
        theta (np.ndarray): Polar angle (radians, 0 to π)
        phi (np.ndarray): Azimuthal angle (radians, 0 to 2π)
        t (float): Time parameter (seconds or normalized time step)
        mass (float): Mass of central object (kg)
        spin (float): Angular momentum/spin parameter (dimensionless)

    Returns:
        tuple: (curvature, density, energy, dark_energy)
            - curvature: Spacetime curvature field
            - density: Matter-energy density distribution
            - energy: Energy field dynamics
            - dark_energy: Dark energy contribution

    Notes:
        This is a phenomenological model inspired by the Kerr metric for rotating
        black holes, but simplified for computational visualization.
    """
    # Spacetime curvature with oscillating time component
    curvature = -np.exp(-r ** 2 / (2 * mass)) * np.cos(spin * t)

    # Density distribution with temporal evolution
    density = np.exp(-r / (mass * 10)) * np.sin(t)

    # Energy field with spatial and temporal dynamics
    energy = np.sin(r * np.sin(theta) * np.cos(phi) * t) * np.exp(-t / 50)

    # Dark energy (vacuum energy) - sigmoid activation of curvature-density coupling
    dark_energy = (1 / (1 + np.exp(-curvature * density))) * energy

    return curvature, density, energy, dark_energy


def calculate_big_bang_raphael_equations(time, density):
    """
    Calculates Raphael equations for cosmological evolution during Big Bang expansion.

    Parameters:
        time (float or np.ndarray): Time point(s) since Big Bang (seconds)
        density (float or np.ndarray): Matter-energy density (kg/m³)

    Returns:
        dict: Raphael equations for forces and energy density containing:
            - "Strong Force": Density-driven strong force
            - "Weak Force": Time-dependent weak force
            - "Energy Density": Combined energy density

    Notes:
        These equations model the evolution of fundamental forces during
        the early universe, from Planck epoch to matter-dominated era.
    """
    # Strong force dominance (density-dependent)
    F_strong = density / time

    # Weak force contribution (time-decay)
    F_weak = density / (time ** 2)

    # Total energy density
    E_density = F_strong + F_weak

    return {
        "Strong Force": F_strong,
        "Weak Force": F_weak,
        "Energy Density": E_density,
    }


def raphael_equation(x, y, t, spin, acc_rate):
    """
    Raphael equation for black hole dynamics in 2D+time representation.

    Calculates curvature, density, and force fields for rotating, accreting
    compact objects (black holes, neutron stars).

    Parameters:
        x (np.ndarray): X-coordinate grid (meters or normalized)
        y (np.ndarray): Y-coordinate grid (meters or normalized)
        t (float): Time parameter (seconds or time step)
        spin (float): Rotation/spin parameter (rad/s or dimensionless)
        acc_rate (float): Accretion rate parameter (kg/s or dimensionless)

    Returns:
        tuple: (curvature, density, forces)
            - curvature: Spacetime curvature field
            - density: Matter density distribution
            - forces: Force field magnitude

    Notes:
        This simplified 2D model enables real-time visualization of black hole
        dynamics including frame-dragging (spin) and accretion disk physics.
    """
    # Spacetime curvature with temporal oscillation and accretion damping
    curvature = np.sin(x**2 + y**2 - t) * np.exp(-acc_rate * (x**2 + y**2))

    # Density distribution with spin-induced asymmetry and time decay
    density = np.cos(spin * (x - y)) * np.exp(-t)

    # Force field magnitude (absolute value for visualization)
    forces = np.abs(np.sin(x * y * t))

    return curvature, density, forces


def generate_oval_data(mass, spin, resolution, scale, t):
    """
    Generate radial spacetime data for oval-shaped (elliptical) spacetime geometry.

    Creates 3D meshgrid in spherical coordinates and computes Raphael equations
    for visualization of rotating massive objects.

    Parameters:
        mass (float): Mass of central object (kg)
        spin (float): Angular momentum parameter (dimensionless)
        resolution (int): Grid resolution (number of points per dimension)
        scale (float): Spatial scale (meters)
        t (float): Time parameter (seconds or time step)

    Returns:
        tuple: (x, y, z, curvature, density, energy, dark_energy)
            All as numpy arrays representing 3D fields
    """
    # Create spherical coordinate meshgrid
    r = np.linspace(0, scale, resolution)
    theta = np.linspace(0, np.pi, resolution)
    phi = np.linspace(0, 2 * np.pi, resolution)
    r, theta, phi = np.meshgrid(r, theta, phi)

    # Calculate Raphael equations
    curvature, density, energy, dark_energy = raphael_equations_oval(
        r, theta, phi, t, mass, spin
    )

    # Convert to Cartesian coordinates for visualization
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)

    return x, y, z, curvature, density, energy, dark_energy


def calculate_grid_size(array):
    """
    Calculate optimal square grid size for visualization from flattened array.

    Parameters:
        array (np.ndarray): Input array

    Returns:
        int: Grid size for square reshaping
    """
    grid_size = int(np.sqrt(array.size))
    if grid_size**2 != array.size:
        grid_size = int(np.floor(np.sqrt(array.size)))
    return grid_size


# Physical constants specific to Raphael simulations
RAPHAEL_CONSTANTS = {
    'G': G,  # Gravitational constant
    'SPEED_OF_LIGHT': 3e8,  # Speed of light (m/s)
    'PLANCK_TIME': 5.39e-44,  # Planck time (s)
    'PLANCK_TEMPERATURE': 1.417e32,  # Planck temperature (K)
    'UNIVERSE_AGE': 4.35e17,  # Age of universe (s) ~ 13.8 billion years
}


def get_raphael_constants():
    """
    Return dictionary of physical constants used in Raphael equations.

    Returns:
        dict: Physical constants
    """
    return RAPHAEL_CONSTANTS.copy()


if __name__ == "__main__":
    # Example usage and testing
    print("Raphael Equations Module - Test Suite")
    print("=" * 50)

    # Test 1: Element forces (Hydrogen)
    print("\nTest 1: Hydrogen atom forces")
    forces = calculate_raphael_equations(protons=1, neutrons=0, electrons=1)
    for key, value in forces.items():
        print(f"  {key}: {value:.6e}")

    # Test 2: Element forces (Carbon-12)
    print("\nTest 2: Carbon-12 atom forces")
    forces = calculate_raphael_equations(protons=6, neutrons=6, electrons=6)
    for key, value in forces.items():
        print(f"  {key}: {value:.6e}")

    # Test 3: Oval spacetime (small scale)
    print("\nTest 3: Oval spacetime field generation")
    x, y, z, c, d, e, de = generate_oval_data(
        mass=1e30, spin=0.5, resolution=10, scale=1e6, t=0
    )
    print(f"  Generated fields with shape: {x.shape}")
    print(f"  Curvature range: [{c.min():.3e}, {c.max():.3e}]")
    print(f"  Density range: [{d.min():.3e}, {d.max():.3e}]")

    # Test 4: Big Bang equations
    print("\nTest 4: Big Bang Raphael equations")
    bb_forces = calculate_big_bang_raphael_equations(time=1e-10, density=1e20)
    for key, value in bb_forces.items():
        print(f"  {key}: {value:.6e}")

    print("\n" + "=" * 50)
    print("All tests completed successfully!")
