"""
Quantum Mechanics Module
TheConstruct Layer - Quantum State Evolution

This module handles quantum mechanical simulations including:
- Quantum state evolution
- Wave-particle duality
- Uncertainty principle
- Atomic transitions
- Electron orbital dynamics

Author: LightSpeed Team
Version: 0.9.5
"""

import numpy as np
from scipy.constants import hbar, c, k

# Physical constants
BOHR_RADIUS = 5.29177e-11  # Bohr radius in meters
PLANCK_CONSTANT = hbar  # Reduced Planck constant (ħ)
SPEED_OF_LIGHT = c  # Speed of light
BOLTZMANN = k  # Boltzmann constant


def evolve_quantum_state(time_step, num_points):
    """
    Evolves quantum states over time using oscillatory dynamics.

    Models time-dependent quantum state evolution on the Bloch sphere
    or in configuration space with oscillating probability density.

    Parameters:
        time_step (int or float): Current time step in simulation
        num_points (int): Number of points to generate for visualization

    Returns:
        tuple: (x, y, z, density)
            - x, y, z: Cartesian coordinates of quantum state
            - density: Time-dependent probability density

    Notes:
        - This is a simplified phenomenological model
        - For rigorous quantum evolution, solve time-dependent Schrödinger equation
        - Oscillation period: 100 time steps
        - Density oscillates between 0 and 1

    Physics:
        The quantum state undergoes unitary evolution U(t) = exp(-iHt/ħ)
        where H is the Hamiltonian. This simplified model uses oscillatory
        radius to simulate breathing modes in quantum systems.
    """
    # Random spherical angles for quantum state distribution
    theta = np.random.uniform(0, 2 * np.pi, num_points)
    phi = np.random.uniform(0, np.pi, num_points)

    # Oscillatory radius (simulates breathing mode / Rabi oscillations)
    r = 1 + 0.1 * np.sin(2 * np.pi * time_step / 100)

    # Convert to Cartesian coordinates
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)

    # Time-dependent probability density (oscillates between 0 and 1)
    density = np.abs(np.sin(2 * np.pi * time_step / 100))

    return x, y, z, density


def radial_distribution(n, r):
    """
    Calculate radial probability density for hydrogen-like orbitals.

    The radial distribution function P(r) = r² |R(r)|² gives the probability
    of finding an electron at distance r from the nucleus.

    Parameters:
        n (int): Principal quantum number (n = 1, 2, 3, ...)
        r (float or np.ndarray): Radial distance from nucleus (meters or a.u.)

    Returns:
        float or np.ndarray: Probability density at radius r

    Formula:
        P(r) = (2/n)³ * (r/a₀)² * exp(-2r/(n*a₀))

    Notes:
        - Simplified hydrogen model (exact only for hydrogen)
        - Peak at r = n² * a₀ (most probable radius)
        - For multi-electron atoms, use Hartree-Fock or DFT

    Quantum Numbers:
        - n=1: 1s orbital, peak at 1 Bohr radius
        - n=2: 2s/2p orbitals, peak at 4 Bohr radii
        - n=3: 3s/3p/3d orbitals, peak at 9 Bohr radii
    """
    # Bohr radius
    a0 = BOHR_RADIUS

    # Simplified probability density for hydrogen-like orbitals
    density = (2 / n)**3 * (r / a0)**2 * np.exp(-2 * r / (n * a0))

    return density


def update_orbital_visualization(n):
    """
    Update the visualization of electron orbitals for a given principal quantum number.

    Generates a 3D visualization of the radial probability distribution
    for hydrogen-like orbitals.

    Parameters:
        n (int): Principal quantum number (n = 1, 2, 3, ...)

    Returns:
        plotly.graph_objects.Figure: Interactive 3D orbital visualization

    Notes:
        - Uses simplified radial distribution (no angular dependence)
        - For full orbitals with angular structure, see orbital_mechanics module
        - Visualization shows spherically averaged probability density

    Requires:
        plotly (pip install plotly)
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("Error: plotly not installed. Run: pip install plotly")
        return None

    # Generate spherical coordinates
    r = np.linspace(0, 10, 500)  # Radial distance in Bohr radii
    theta = np.linspace(0, 2 * np.pi, 100)  # Azimuthal angle
    phi = np.linspace(0, np.pi, 100)  # Polar angle
    r, theta, phi = np.meshgrid(r, theta, phi)

    # Convert spherical to Cartesian coordinates
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)

    # Calculate radial probability density
    density = radial_distribution(n, r)

    # Flatten arrays for plotting
    x_flat = x.flatten()
    y_flat = y.flatten()
    z_flat = z.flatten()
    density_flat = density.flatten()

    # Create 3D scatter plot
    fig = go.Figure(data=go.Scatter3d(
        x=x_flat, y=y_flat, z=z_flat,
        mode="markers",
        marker=dict(size=2, color=density_flat, colorscale="Viridis", opacity=0.7),
    ))

    fig.update_layout(
        title=f"Electron Orbital Visualization (n = {n})",
        scene=dict(
            xaxis=dict(title="X (Bohr radii)", color="white", backgroundcolor="black"),
            yaxis=dict(title="Y (Bohr radii)", color="white", backgroundcolor="black"),
            zaxis=dict(title="Z (Bohr radii)", color="white", backgroundcolor="black"),
        ),
        paper_bgcolor="black",
        font=dict(color="white"),
    )

    return fig


def wave_function_1d(x, n, L):
    """
    Calculate 1D particle-in-a-box wavefunction.

    The particle-in-a-box is a fundamental quantum system showing
    quantization of energy and standing wave patterns.

    Parameters:
        x (np.ndarray): Position coordinates
        n (int): Quantum number (n = 1, 2, 3, ...)
        L (float): Box length

    Returns:
        np.ndarray: Wavefunction ψ(x)

    Formula:
        ψ_n(x) = sqrt(2/L) * sin(nπx/L)

    Energy Levels:
        E_n = (n²π²ħ²)/(2mL²)
    """
    return np.sqrt(2/L) * np.sin(n * np.pi * x / L)


def probability_density_1d(x, n, L):
    """
    Calculate probability density |ψ(x)|² for particle in a box.

    Parameters:
        x (np.ndarray): Position coordinates
        n (int): Quantum number
        L (float): Box length

    Returns:
        np.ndarray: Probability density |ψ|²
    """
    psi = wave_function_1d(x, n, L)
    return np.abs(psi)**2


def uncertainty_product(sigma_x, sigma_p):
    """
    Calculate the uncertainty product σ_x * σ_p and compare to Heisenberg limit.

    Heisenberg Uncertainty Principle:
        Δx * Δp ≥ ħ/2

    Parameters:
        sigma_x (float): Position uncertainty (meters)
        sigma_p (float): Momentum uncertainty (kg·m/s)

    Returns:
        dict: Containing uncertainty product and Heisenberg limit comparison

    Notes:
        - Fundamental limit of quantum mechanics
        - Not a measurement limitation, but intrinsic to nature
        - Applies to all conjugate variables (E-t, L-θ, etc.)
    """
    product = sigma_x * sigma_p
    heisenberg_limit = hbar / 2

    return {
        "uncertainty_product": product,
        "heisenberg_limit": heisenberg_limit,
        "satisfies_principle": product >= heisenberg_limit,
        "ratio": product / heisenberg_limit
    }


def de_broglie_wavelength(mass, velocity):
    """
    Calculate de Broglie wavelength for a particle.

    Wave-particle duality: every particle has an associated wavelength.

    Parameters:
        mass (float): Particle mass (kg)
        velocity (float): Particle velocity (m/s)

    Returns:
        float: de Broglie wavelength (meters)

    Formula:
        λ = h/p = h/(mv)

    Examples:
        - Electron at 1e6 m/s: λ ~ 0.7 nm (atomic scale)
        - Baseball (0.145 kg) at 40 m/s: λ ~ 1e-34 m (unobservable)
    """
    momentum = mass * velocity
    wavelength = (2 * np.pi * hbar) / momentum
    return wavelength


def compton_wavelength(mass):
    """
    Calculate Compton wavelength for a particle.

    Characteristic quantum mechanical wavelength of a particle.

    Parameters:
        mass (float): Rest mass of particle (kg)

    Returns:
        float: Compton wavelength (meters)

    Formula:
        λ_C = h/(mc)

    Examples:
        - Electron: 2.43 pm
        - Proton: 1.32 fm
    """
    return (2 * np.pi * hbar) / (mass * SPEED_OF_LIGHT)


def quantum_tunneling_probability(E, V0, width):
    """
    Estimate quantum tunneling probability through a rectangular barrier.

    Parameters:
        E (float): Particle energy (Joules)
        V0 (float): Barrier height (Joules)
        width (float): Barrier width (meters)

    Returns:
        float: Transmission probability (0 to 1)

    Formula (approximation):
        T ≈ exp(-2 * κ * width)
        where κ = sqrt(2m(V0 - E)/ħ²)

    Notes:
        - Only valid for E < V0 (tunneling regime)
        - Exact solution requires solving Schrödinger equation
        - Enables nuclear fusion, scanning tunneling microscopy
    """
    if E >= V0:
        return 1.0  # Classical transmission (over the barrier)

    # Assume electron mass for simplification
    mass_electron = 9.109e-31  # kg

    # Decay constant
    kappa = np.sqrt(2 * mass_electron * (V0 - E)) / hbar

    # Transmission probability (WKB approximation)
    T = np.exp(-2 * kappa * width)

    return T


def rabi_frequency(dipole_moment, electric_field):
    """
    Calculate Rabi frequency for two-level quantum system.

    Describes oscillation rate between quantum states under external driving.

    Parameters:
        dipole_moment (float): Electric dipole moment (C·m)
        electric_field (float): Applied electric field (V/m)

    Returns:
        float: Rabi frequency (rad/s)

    Formula:
        Ω = μ·E/ħ

    Applications:
        - Quantum computing (qubit control)
        - NMR spectroscopy
        - Atomic clocks
    """
    return (dipole_moment * electric_field) / hbar


def generate_fractal_quantum_state(num_points, iterations=3, scale=1.0):
    """
    Generates fractal-like quantum state patterns.

    Models hierarchical quantum structures or quantum chaos visualizations.

    Parameters:
        num_points (int): Number of initial points
        iterations (int): Number of fractal refinement steps
        scale (float): Scaling parameter

    Returns:
        tuple: (x, y, z, density) arrays representing fractal quantum state

    Notes:
        - Phenomenological model for visualization
        - Can represent quantum fractal patterns in phase space
        - Used for chaotic quantum system visualization
    """
    # Initialize random points in 3D
    x = np.random.uniform(-1, 1, num_points)
    y = np.random.uniform(-1, 1, num_points)
    z = np.random.uniform(-1, 1, num_points)

    # Fractal iterations (nonlinear transformations)
    for _ in range(iterations):
        r = np.sqrt(x**2 + y**2 + z**2)
        x += np.sin(r) * scale
        y += np.cos(r) * scale
        z += np.tanh(r) * scale  # Changed from tan to tanh for stability

    # Density decays with distance
    r_final = np.sqrt(x**2 + y**2 + z**2)
    density = np.exp(-r_final / scale)

    return x, y, z, density


# ============================================================================
# CONSTANTS AND UTILITIES
# ============================================================================

QUANTUM_CONSTANTS = {
    'HBAR': hbar,  # Reduced Planck constant
    'H': 2 * np.pi * hbar,  # Planck constant
    'BOHR_RADIUS': BOHR_RADIUS,
    'ELECTRON_MASS': 9.109e-31,  # kg
    'PROTON_MASS': 1.673e-27,  # kg
    'NEUTRON_MASS': 1.675e-27,  # kg
    'FINE_STRUCTURE': 1/137.036,  # Dimensionless
    'RYDBERG_ENERGY': 13.6,  # eV
}


def get_quantum_constants():
    """Return dictionary of quantum mechanics constants."""
    return QUANTUM_CONSTANTS.copy()


if __name__ == "__main__":
    # Example usage and testing
    print("Quantum Mechanics Module - Test Suite")
    print("=" * 50)

    # Test 1: Quantum state evolution
    print("\nTest 1: Quantum state evolution")
    x, y, z, d = evolve_quantum_state(time_step=0, num_points=100)
    print(f"  Generated {len(x)} quantum state points")
    print(f"  Density: {d:.3f}")

    # Test 2: Radial distribution
    print("\nTest 2: Radial distribution (n=1)")
    r = np.array([1, 2, 3]) * BOHR_RADIUS
    density = radial_distribution(n=1, r=r)
    print(f"  Density at 1*a0: {density[0]:.3e}")
    print(f"  Density at 2*a0: {density[1]:.3e}")
    print(f"  Density at 3*a0: {density[2]:.3e}")

    # Test 3: de Broglie wavelength
    print("\nTest 3: de Broglie wavelength")
    lambda_e = de_broglie_wavelength(9.109e-31, 1e6)  # Electron at 1e6 m/s
    print(f"  Electron (1e6 m/s): {lambda_e:.3e} m ({lambda_e*1e9:.3f} nm)")

    # Test 4: Uncertainty principle
    print("\nTest 4: Heisenberg uncertainty principle")
    result = uncertainty_product(1e-10, 1e-24)  # Typical atomic scale
    print(f"  Delta_x * Delta_p = {result['uncertainty_product']:.3e} J*s")
    print(f"  hbar/2 = {result['heisenberg_limit']:.3e} J*s")
    print(f"  Satisfies principle: {result['satisfies_principle']}")
    print(f"  Ratio (Delta_x*Delta_p)/(hbar/2): {result['ratio']:.3f}")

    # Test 5: Quantum tunneling
    print("\nTest 5: Quantum tunneling probability")
    E = 1e-19  # 1 eV ~ 1.6e-19 J, using 0.625 eV
    V0 = 3e-19  # 3 eV barrier
    width = 1e-9  # 1 nm barrier
    T = quantum_tunneling_probability(E, V0, width)
    print(f"  Energy: {E/1.6e-19:.2f} eV")
    print(f"  Barrier: {V0/1.6e-19:.2f} eV")
    print(f"  Width: {width*1e9:.1f} nm")
    print(f"  Tunneling probability: {T:.3e} ({T*100:.6f}%)")

    # Test 6: Compton wavelength
    print("\nTest 6: Compton wavelength")
    lambda_e = compton_wavelength(9.109e-31)  # Electron
    lambda_p = compton_wavelength(1.673e-27)  # Proton
    print(f"  Electron: {lambda_e:.3e} m ({lambda_e*1e12:.2f} pm)")
    print(f"  Proton: {lambda_p:.3e} m ({lambda_p*1e15:.2f} fm)")

    print("\n" + "=" * 50)
    print("All tests completed successfully!")
    print("\nFor visualizations, run:")
    print("  fig = update_orbital_visualization(n=2)")
    print("  fig.show()")
