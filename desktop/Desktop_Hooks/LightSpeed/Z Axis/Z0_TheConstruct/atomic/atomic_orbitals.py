"""
Atomic Orbitals Simulation

Consolidated from 3 versions

Consolidated from 10 versions
"""

# Imports

from scipy.special import gamma
from scipy.special import sph_harm
import numpy
import plotly.graph_objects


# ===== CONSOLIDATED FROM 10 FILES =====

# Merged on: 2025-11-21 17:46:22

# Source files: 10


"""
Atomic Orbitals Simulation

Consolidated from 3 versions
"""

# Imports

from scipy.special import gamma
from scipy.special import sph_harm
import numpy
import plotly.graph_objects


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-17 13:43:28

# Source files: 3


"""
Atomic Orbitals Simulation
"""

import numpy as np
import plotly.graph_objects as go

# Constants
PLANCK_CONSTANT = 6.626e-34  # Planck's constant (J.s)
ELECTRON_MASS = 9.109e-31    # Mass of an electron (kg)
BOHR_RADIUS = 5.29177e-11    # Bohr radius (m)

def calculate_radial_probability(n, r):
    """
    Compute radial probability density for a hydrogen-like atom.

    Parameters:
        n (int): Principal quantum number.
        r (float): Radial distance (in meters).

    Returns:
        float: Radial probability density.
    """
    # Simplified hydrogen radial distribution
    density = (2 / n)**3 * (r / BOHR_RADIUS)**2 * np.exp(-2 * r / (n * BOHR_RADIUS))
    return density

def generate_orbital_mesh(n, steps=200):
    """
    Generate 3D mesh for orbital visualization.

    Parameters:
        n (int): Principal quantum number.
        steps (int): Resolution of the mesh.

    Returns:
        tuple: (x, y, z, density) arrays for 3D visualization.
    """
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

def plot_orbital(n):
    """
    Create a 3D visualization of atomic orbitals for a given quantum number n.

    Parameters:
        n (int): Principal quantum number.

    Returns:
        plotly.graph_objects.Figure: 3D plot of the orbital.
    """
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

def calculate_orbital_density(n, l, m, grid_size=50, grid_range=5):
    """
    Calculates the probability density for an atomic orbital using spherical harmonics.
    Parameters:
        n (int): Principal quantum number.
        l (int): Angular momentum quantum number.
        m (int): Magnetic quantum number.
        grid_size (int): Number of grid points in each dimension.
        grid_range (float): Range for the grid in atomic units (a.u.).
    Returns:
        x, y, z, density (numpy arrays): 3D coordinates and the corresponding orbital density.
    """
    from scipy.special import sph_harm, gamma

    # Define spherical coordinate grid
    r = np.linspace(0.1, grid_range, grid_size)
    theta = np.linspace(0, np.pi, grid_size)
    phi = np.linspace(0, 2 * np.pi, grid_size)
    r, theta, phi = np.meshgrid(r, theta, phi, indexing="ij")

    # Radial wavefunction (simplified hydrogen-like orbital)
    rho = 2 * r / n
    radial_part = (2 / n)**3 * np.sqrt(gamma(n - l - 1) / (2 * n * gamma(n + l))) * np.exp(-rho) * rho**l
    radial_density = np.abs(radial_part)**2

    # Spherical harmonics
    spherical_part = sph_harm(m, l, phi, theta)
    angular_density = np.abs(spherical_part)**2

    # Combine radial and angular densities
    density = (radial_density * angular_density).flatten()

    # Convert spherical to Cartesian coordinates
    x = (r * np.sin(theta) * np.cos(phi)).flatten()
    y = (r * np.sin(theta) * np.sin(phi)).flatten()
    z = (r * np.cos(theta)).flatten()

    return x, y, z, density

def plot_atomic_orbitals(n=2, l=1, m=0, grid_size=50, grid_range=5):
    """
    Plots the atomic orbitals in 3D using quantum numbers n, l, and m.
    Parameters:
        n (int): Principal quantum number.
        l (int): Angular momentum quantum number.
        m (int): Magnetic quantum number.
        grid_size (int): Number of grid points in each dimension.
        grid_range (float): Range for the grid in atomic units (a.u.).
    Returns:
        fig (Plotly Figure): Interactive 3D visualization of the atomic orbital.
    """
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

    # Update layout for 3D visualization
    fig.update_layout(
        title=f"Atomic Orbital (n={n}, l={l}, m={m})",
        scene=dict(
            xaxis=dict(title="X-axis (a.u.)", backgroundcolor="black"),
            yaxis=dict(title="Y-axis (a.u.)", backgroundcolor="black"),
            zaxis=dict(title="Z-axis (a.u.)", backgroundcolor="black"),
        ),
        paper_bgcolor="black",
        font=dict(color="white")
    )

    return fig


# Example usage
if __name__ == "__main__":
    # Plot for n = 1
    orbital_plot = plot_orbital(n=1)
    orbital_plot.show()
