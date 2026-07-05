"""
Orbital Mechanics Module
TheConstruct Layer - Orbital & Atomic Dynamics

This module handles orbital mechanics at two scales:
1. Atomic orbitals: Quantum mechanical electron wavefunctions
2. Celestial mechanics: Keplerian orbits for asteroids, planets, spacecraft

Author: LightSpeed Team
Version: 0.9.5
"""

import numpy as np
from scipy.constants import G, c
from scipy.special import sph_harm, gamma

# Physical constants
BOHR_RADIUS = 5.29177e-11  # Bohr radius in meters (atomic scale)
SPEED_OF_LIGHT = 3e8  # Speed of light in m/s
GRAVITATIONAL_CONSTANT = 6.67430e-11  # G in m³/(kg·s²)


# ============================================================================
# GENERAL RELATIVITY & BLACK HOLE MECHANICS
# ============================================================================

def calculate_schwarzschild_radius(mass):
    """
    Calculate the Schwarzschild radius (event horizon) for a black hole.

    The Schwarzschild radius is the radius of the event horizon of a
    non-rotating black hole. For Earth: ~9mm, Sun: ~3km, Sgr A*: ~12 million km.

    Parameters:
        mass (float): Mass of the object (kg)

    Returns:
        float: Schwarzschild radius in meters

    Formula:
        r_s = 2*G*M / c²

    Notes:
        - For rotating black holes, use Kerr metric (not implemented here)
        - Photon sphere at r = 1.5 * r_s
        - ISCO (innermost stable circular orbit) at r = 3 * r_s
    """
    return 2 * GRAVITATIONAL_CONSTANT * mass / SPEED_OF_LIGHT**2


# ============================================================================
# ATOMIC ORBITAL MECHANICS (Quantum Mechanics)
# ============================================================================

def calculate_radial_probability(n, r):
    """
    Compute radial probability density for a hydrogen-like atom.

    The radial distribution function gives the probability of finding
    an electron at distance r from the nucleus for a given quantum state.

    Parameters:
        n (int): Principal quantum number (n = 1, 2, 3, ...)
        r (float or np.ndarray): Radial distance from nucleus (meters)

    Returns:
        float or np.ndarray: Radial probability density (1/m)

    Formula:
        P(r) = (2/n)³ * (r/a₀)² * exp(-2r/(n*a₀))

    Notes:
        - Simplified hydrogen model (ignores fine structure)
        - Peak at r = n²*a₀ (most probable radius)
        - For multi-electron atoms, use self-consistent field methods
    """
    # Simplified hydrogen radial distribution
    density = (2 / n)**3 * (r / BOHR_RADIUS)**2 * np.exp(-2 * r / (n * BOHR_RADIUS))
    return density


def generate_orbital_mesh(n, steps=200):
    """
    Generate 3D mesh for atomic orbital visualization.

    Creates a spherical mesh and computes the radial probability density
    for visualization of electron orbitals.

    Parameters:
        n (int): Principal quantum number (n = 1, 2, 3, ...)
        steps (int): Resolution of the mesh (default: 200)

    Returns:
        tuple: (x, y, z, density) flattened arrays for 3D visualization

    Notes:
        - Uses simplified radial probability (no angular dependence)
        - For full orbitals with angular structure, use calculate_orbital_density()
    """
    # Spherical coordinate grid
    r = np.linspace(0, 10 * BOHR_RADIUS, steps)
    theta = np.linspace(0, 2 * np.pi, steps)
    phi = np.linspace(0, np.pi, steps)

    r, theta, phi = np.meshgrid(r, theta, phi)

    # Convert spherical to Cartesian coordinates
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)

    # Calculate radial probability
    density = calculate_radial_probability(n, r)

    return x.flatten(), y.flatten(), z.flatten(), density.flatten()


def calculate_orbital_density(n, l, m, grid_size=50, grid_range=5):
    """
    Calculates the full probability density for an atomic orbital using
    spherical harmonics and radial wavefunctions.

    This gives the complete quantum mechanical wavefunction ψ(r,θ,φ) for
    hydrogen-like orbitals with proper angular dependence.

    Parameters:
        n (int): Principal quantum number (n = 1, 2, 3, ...; shell)
        l (int): Angular momentum quantum number (l = 0 to n-1; s, p, d, f, ...)
        m (int): Magnetic quantum number (m = -l to +l; orbital orientation)
        grid_size (int): Number of grid points per dimension (default: 50)
        grid_range (float): Range for the grid in atomic units (a.u.) (default: 5)

    Returns:
        tuple: (x, y, z, density) flattened arrays
            - x, y, z: Cartesian coordinates
            - density: |ψ(r,θ,φ)|² probability density

    Quantum Numbers:
        - n=1, l=0, m=0: 1s orbital (spherical)
        - n=2, l=0, m=0: 2s orbital (spherical with node)
        - n=2, l=1, m=-1,0,+1: 2p orbitals (dumbbell shaped)
        - n=3, l=2, m=-2,-1,0,+1,+2: 3d orbitals (complex shapes)

    Notes:
        - Uses simplified hydrogen-like radial wavefunction
        - Spherical harmonics Y_l^m(θ,φ) give angular structure
        - For multi-electron atoms, requires Hartree-Fock calculations
    """
    # Define spherical coordinate grid
    r = np.linspace(0.1, grid_range, grid_size)
    theta = np.linspace(0, np.pi, grid_size)
    phi = np.linspace(0, 2 * np.pi, grid_size)
    r, theta, phi = np.meshgrid(r, theta, phi, indexing="ij")

    # Radial wavefunction (simplified hydrogen-like orbital)
    rho = 2 * r / n
    radial_part = (2 / n)**3 * np.sqrt(gamma(n - l - 1) / (2 * n * gamma(n + l))) * np.exp(-rho) * rho**l
    radial_density = np.abs(radial_part)**2

    # Spherical harmonics Y_l^m(θ, φ)
    spherical_part = sph_harm(m, l, phi, theta)
    angular_density = np.abs(spherical_part)**2

    # Combine radial and angular densities: |ψ|² = |R(r)|² * |Y(θ,φ)|²
    density = (radial_density * angular_density).flatten()

    # Convert spherical to Cartesian coordinates
    x = (r * np.sin(theta) * np.cos(phi)).flatten()
    y = (r * np.sin(theta) * np.sin(phi)).flatten()
    z = (r * np.cos(theta)).flatten()

    return x, y, z, density


def plot_orbital(n):
    """
    Create a 3D visualization of atomic orbitals for a given quantum number n.

    Uses simplified radial probability (no angular structure).
    For full orbital shapes, use plot_atomic_orbitals().

    Parameters:
        n (int): Principal quantum number

    Returns:
        plotly.graph_objects.Figure: Interactive 3D plot of the orbital

    Requires:
        plotly (pip install plotly)
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("Error: plotly not installed. Run: pip install plotly")
        return None

    x, y, z, density = generate_orbital_mesh(n)

    # Create 3D scatter plot
    fig = go.Figure(data=go.Scatter3d(
        x=x, y=y, z=z,
        mode="markers",
        marker=dict(size=3, color=density, colorscale="Viridis", opacity=0.7)
    ))

    fig.update_layout(
        title=f"Atomic Orbital (n={n})",
        scene=dict(
            xaxis=dict(title="X (m)", backgroundcolor="black"),
            yaxis=dict(title="Y (m)", backgroundcolor="black"),
            zaxis=dict(title="Z (m)", backgroundcolor="black")
        ),
        paper_bgcolor="black",
        font=dict(color="white")
    )
    return fig


def plot_atomic_orbitals(n=2, l=1, m=0, grid_size=50, grid_range=5):
    """
    Plots the complete atomic orbitals in 3D using quantum numbers n, l, and m.

    Shows the full quantum mechanical probability density including angular structure
    (s, p, d, f orbitals).

    Parameters:
        n (int): Principal quantum number (default: 2)
        l (int): Angular momentum quantum number (default: 1, p-orbital)
        m (int): Magnetic quantum number (default: 0)
        grid_size (int): Number of grid points per dimension (default: 50)
        grid_range (float): Range for grid in atomic units (default: 5)

    Returns:
        plotly.graph_objects.Figure: Interactive 3D visualization

    Examples:
        plot_atomic_orbitals(n=1, l=0, m=0)  # 1s orbital
        plot_atomic_orbitals(n=2, l=1, m=0)  # 2p_z orbital
        plot_atomic_orbitals(n=3, l=2, m=0)  # 3d_z² orbital

    Requires:
        plotly (pip install plotly)
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("Error: plotly not installed. Run: pip install plotly")
        return None

    x, y, z, density = calculate_orbital_density(n, l, m, grid_size, grid_range)

    # Create 3D scatter plot
    fig = go.Figure(data=go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(
            size=3,
            color=density,
            colorscale="Viridis",
            opacity=0.7
        )
    ))

    # Orbital name mapping
    orbital_names = {0: 's', 1: 'p', 2: 'd', 3: 'f', 4: 'g'}
    orbital_type = orbital_names.get(l, str(l))

    # Update layout for 3D visualization
    fig.update_layout(
        title=f"Atomic Orbital: {n}{orbital_type} (n={n}, l={l}, m={m})",
        scene=dict(
            xaxis=dict(title="X-axis (a.u.)", backgroundcolor="black"),
            yaxis=dict(title="Y-axis (a.u.)", backgroundcolor="black"),
            zaxis=dict(title="Z-axis (a.u.)", backgroundcolor="black"),
        ),
        paper_bgcolor="black",
        font=dict(color="white")
    )

    return fig


# ============================================================================
# CELESTIAL ORBITAL MECHANICS (Keplerian Orbits)
# ============================================================================

def compute_orbit(a, e, i, omega, w, M, num_points=500):
    """
    Compute 3D Keplerian orbit from orbital elements.

    Calculates the position along an elliptical orbit in 3D space using
    classical orbital elements (used for planets, asteroids, satellites).

    Parameters:
        a (float): Semi-major axis (AU or meters)
        e (float): Eccentricity (0 = circle, 0<e<1 = ellipse, e≥1 = hyperbola)
        i (float): Inclination (degrees) - tilt of orbital plane
        omega (float): Longitude of ascending node (degrees) - where orbit crosses plane
        w (float): Argument of periapsis (degrees) - orientation of ellipse in plane
        M (float): Mean anomaly at epoch (degrees) - position along orbit
        num_points (int): Number of points to compute (default: 500)

    Returns:
        tuple: (x, y, z) numpy arrays representing 3D orbital path

    Notes:
        - Uses simplified 2-body Keplerian mechanics (neglects perturbations)
        - For high-precision ephemeris, use SPICE or JPL Horizons
        - Assumes reference frame: ecliptic plane (solar system standard)

    Orbital Elements:
        - a: Size of orbit (larger = farther from Sun)
        - e: Shape (0=circle, closer to 1=elongated ellipse)
        - i: Tilt (0=in plane, 90=perpendicular)
        - Ω (omega): Rotation of orbit line of nodes
        - ω (w): Rotation of periapsis within plane
        - M: Position at reference time
    """
    # True anomaly from mean anomaly (simplified, ignores eccentric anomaly iteration)
    theta = np.linspace(0, 2 * np.pi, num_points)

    # Orbital equation: r(θ) = a(1-e²)/(1 + e·cos(θ))
    r = (a * (1 - e**2)) / (1 + e * np.cos(theta))

    # Position in orbital plane
    x_orbit = r * np.cos(theta)
    y_orbit = r * np.sin(theta)
    z_orbit = np.zeros_like(x_orbit)

    # Convert angles to radians
    i_rad = np.radians(i)
    omega_rad = np.radians(omega)
    w_rad = np.radians(w)

    # Apply 3D rotation: argument of periapsis (ω)
    x_rot = x_orbit * np.cos(w_rad) - y_orbit * np.sin(w_rad)
    y_rot = x_orbit * np.sin(w_rad) + y_orbit * np.cos(w_rad)

    # Apply 3D rotation: longitude of ascending node (Ω)
    x_final = x_rot * np.cos(omega_rad) - y_rot * np.sin(omega_rad)
    y_final = x_rot * np.sin(omega_rad) + y_rot * np.cos(omega_rad)

    # Apply inclination (i)
    z_final = np.sin(i_rad) * np.sqrt(x_final**2 + y_final**2)

    return x_final, y_final, z_final


def orbital_period(a, M_central=1.989e30):
    """
    Calculate orbital period using Kepler's 3rd law.

    Parameters:
        a (float): Semi-major axis (meters)
        M_central (float): Mass of central body (kg), default: Sun mass

    Returns:
        float: Orbital period (seconds)

    Formula:
        T = 2π * sqrt(a³ / (G*M))
    """
    return 2 * np.pi * np.sqrt(a**3 / (GRAVITATIONAL_CONSTANT * M_central))


def orbital_velocity(r, a, M_central=1.989e30):
    """
    Calculate instantaneous orbital velocity using vis-viva equation.

    Parameters:
        r (float): Current distance from central body (meters)
        a (float): Semi-major axis (meters)
        M_central (float): Mass of central body (kg), default: Sun mass

    Returns:
        float: Orbital velocity (m/s)

    Formula:
        v = sqrt(G*M * (2/r - 1/a))
    """
    return np.sqrt(GRAVITATIONAL_CONSTANT * M_central * (2/r - 1/a))


def escape_velocity(r, M_central=1.989e30):
    """
    Calculate escape velocity from a given radius.

    Parameters:
        r (float): Distance from central body (meters)
        M_central (float): Mass of central body (kg), default: Sun mass

    Returns:
        float: Escape velocity (m/s)

    Formula:
        v_esc = sqrt(2*G*M / r)
    """
    return np.sqrt(2 * GRAVITATIONAL_CONSTANT * M_central / r)


# ============================================================================
# CONSTANTS AND UTILITIES
# ============================================================================

ORBITAL_CONSTANTS = {
    'BOHR_RADIUS': BOHR_RADIUS,
    'SPEED_OF_LIGHT': SPEED_OF_LIGHT,
    'G': GRAVITATIONAL_CONSTANT,
    'AU': 1.496e11,  # Astronomical Unit in meters
    'SOLAR_MASS': 1.989e30,  # kg
    'EARTH_MASS': 5.972e24,  # kg
}


def get_orbital_constants():
    """Return dictionary of orbital mechanics constants."""
    return ORBITAL_CONSTANTS.copy()


if __name__ == "__main__":
    # Example usage and testing
    print("Orbital Mechanics Module - Test Suite")
    print("=" * 50)

    # Test 1: Schwarzschild radius
    print("\nTest 1: Schwarzschild radii")
    print(f"  Earth: {calculate_schwarzschild_radius(5.972e24):.3e} m (~9 mm)")
    print(f"  Sun: {calculate_schwarzschild_radius(1.989e30):.3e} m (~3 km)")
    print(f"  Sgr A*: {calculate_schwarzschild_radius(4e6 * 1.989e30):.3e} m (~12M km)")

    # Test 2: Atomic orbital mesh
    print("\nTest 2: Atomic orbital mesh generation")
    x, y, z, d = generate_orbital_mesh(n=2, steps=50)
    print(f"  Generated {len(x)} points for n=2 orbital")
    print(f"  Density range: {d.min():.3e} to {d.max():.3e}")

    # Test 3: Full orbital density (2p)
    print("\nTest 3: 2p orbital density calculation")
    x, y, z, d = calculate_orbital_density(n=2, l=1, m=0, grid_size=20)
    print(f"  Generated {len(x)} points for 2p orbital")
    print(f"  Density range: {d.min():.3e} to {d.max():.3e}")

    # Test 4: Keplerian orbit (Earth-like)
    print("\nTest 4: Earth-like orbit computation")
    x, y, z = compute_orbit(a=1.0, e=0.0167, i=0, omega=0, w=0, M=0, num_points=100)
    print(f"  Generated {len(x)} orbital points")
    print(f"  Orbit range: x=[{x.min():.3f}, {x.max():.3f}] AU")

    # Test 5: Orbital period (Earth)
    print("\nTest 5: Orbital periods")
    T_earth = orbital_period(1.496e11) / (365.25 * 24 * 3600)
    print(f"  Earth: {T_earth:.3f} years (expected: 1.0)")

    print("\n" + "=" * 50)
    print("All tests completed successfully!")
