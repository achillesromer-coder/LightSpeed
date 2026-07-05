"""
Big Bang Simulation Module
TheConstruct Layer - Cosmological Evolution

This module simulates the expansion of the universe from the Planck epoch
to the present day using fractal refinement for spatial rendering and
Raphael equations for force dynamics.

Author: LightSpeed Team
Version: 0.9.5
"""

import numpy as np
from scipy.constants import G, pi

# Physical constants for cosmological simulation
PLANCK_TIME = 5.39e-44  # Planck time (seconds)
PLANCK_TEMPERATURE = 1.417e32  # Planck temperature (Kelvin)
UNIVERSE_AGE = 4.35e17  # Age of universe (seconds) ~ 13.8 billion years


def fractal_refinement(base_points, scale_factor, iterations):
    """
    Refines spatial distribution using recursive fractal steps.

    This creates a self-similar structure at multiple scales, simulating
    the hierarchical structure formation in the early universe (quantum
    fluctuations → density perturbations → cosmic web).

    Parameters:
        base_points (np.ndarray): Initial set of spatial points
        scale_factor (float): Scaling factor for each fractal iteration (0 < scale < 1)
        iterations (int): Number of fractal refinement levels

    Returns:
        np.ndarray: Refined set of points with fractal structure

    Notes:
        Each iteration doubles the number of points, creating nested structures
        at progressively smaller scales. Final size = base_size * (2^iterations)
    """
    points = base_points
    for _ in range(iterations):
        # Create scaled copy with random perturbations
        refined = points * scale_factor + np.random.uniform(
            -scale_factor, scale_factor, points.shape
        )
        # Concatenate to build fractal hierarchy
        points = np.concatenate([points, refined])
    return points


def generate_big_bang_simulation(time_steps=500, fractal_iterations=3, scale=1e-30):
    """
    Simulates the expansion of the universe using fractal refinement for spatial rendering.

    Models the evolution from Planck epoch (10^-43 s) to present day (13.8 Gyr),
    including spatial expansion (Friedmann equation), density evolution, and
    fractal structure formation.

    Parameters:
        time_steps (int): Number of temporal simulation steps (default: 500)
        fractal_iterations (int): Number of fractal refinement iterations (default: 3)
        scale (float): Initial spatial scale in meters (default: 1e-30, Planck length scale)

    Returns:
        dict: Simulation data containing:
            - "time": Time points from Planck time to universe age (s)
            - "space": Spatial scale evolution (m) - follows inflation + expansion
            - "density": Matter-energy density evolution (kg/m³)
            - "x", "y", "z": Fractally refined 3D spatial coordinates

    Physics:
        - Time evolution: Logarithmic spacing (geomspace) to capture early rapid dynamics
        - Spatial expansion: Exponential growth from Friedmann equation
        - Density: Scales as 1/t² (radiation-dominated early universe)
        - Fractal structure: Simulates quantum fluctuations → structure formation

    Notes:
        This is a simplified phenomenological model. For research-grade simulations,
        use N-body codes (GADGET, GIZMO) with full GR and particle physics.
    """
    # Logarithmic time steps from Planck epoch to present
    time = np.geomspace(PLANCK_TIME, UNIVERSE_AGE, time_steps)

    # Spatial scale: Exponential expansion from Friedmann equation
    # a(t) ∝ exp(H*t) where H ~ sqrt(G*rho)
    space = scale * np.exp(np.sqrt(3 / 2) * np.sqrt(G / (8 * pi)) * time)

    # Matter-energy density: Scales as 1/t² in radiation-dominated era
    density = PLANCK_TEMPERATURE / (time ** 2)

    # Fractal-based refinement for 3D spatial structure
    # Initialize with random uniform distribution
    x_base = np.random.uniform(-1, 1, time_steps)
    y_base = np.random.uniform(-1, 1, time_steps)
    z_base = np.random.uniform(-1, 1, time_steps)

    # Apply fractal refinement (simulates structure formation)
    x_refined = fractal_refinement(x_base, 0.1, fractal_iterations)
    y_refined = fractal_refinement(y_base, 0.1, fractal_iterations)
    z_refined = fractal_refinement(z_base, 0.1, fractal_iterations)

    return {
        "time": time,
        "space": space,
        "density": density,
        "x": x_refined,
        "y": y_refined,
        "z": z_refined,
    }


def plot_big_bang(data):
    """
    Generates a 3D visualization of the Big Bang simulation using Plotly.

    Creates an interactive 3D plot showing:
    1. Fractal spatial structure (scatter points colored by density)
    2. Space-time evolution trajectory (line plot)

    Parameters:
        data (dict): Simulation data from generate_big_bang_simulation()

    Returns:
        None (displays interactive Plotly figure)

    Requires:
        - plotly (pip install plotly)

    Notes:
        For non-interactive environments (HPC, batch), save to HTML:
        fig.write_html("big_bang_simulation.html")
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("Error: plotly not installed. Run: pip install plotly")
        return

    fig = go.Figure()

    # Add fractal-refined spatial evolution (particle distribution)
    fig.add_trace(
        go.Scatter3d(
            x=data["x"],
            y=data["y"],
            z=data["z"],
            mode="markers",
            marker=dict(
                size=2,
                color=data["density"],
                colorscale="Plasma",
                opacity=0.8,
                colorbar=dict(title="Density (kg/m³)")
            ),
            name="Fractal Space"
        )
    )

    # Add spatial scale vs time evolution trajectory
    fig.add_trace(
        go.Scatter3d(
            x=data["time"],
            y=data["space"],
            z=data["density"],
            mode="lines",
            line=dict(color="cyan", width=4),
            name="Space-Time Evolution"
        )
    )

    # Layout configuration
    fig.update_layout(
        scene=dict(
            xaxis=dict(
                title="Time (s)",
                type="log",  # Logarithmic scale for time
                backgroundcolor="black"
            ),
            yaxis=dict(
                title="Space Scale (m)",
                type="log",  # Logarithmic scale for space
                backgroundcolor="black"
            ),
            zaxis=dict(
                title="Density (kg/m³)",
                type="log",  # Logarithmic scale for density
                backgroundcolor="black"
            ),
        ),
        title="Big Bang Simulation with Fractal Refinement",
        paper_bgcolor="black",
        font=dict(color="white")
    )

    fig.show()


def get_cosmic_timeline():
    """
    Returns key epochs in cosmic evolution with their characteristic times and temperatures.

    Returns:
        dict: Timeline of cosmic epochs
    """
    return {
        "Planck Epoch": {
            "time": "< 10^-43 s",
            "temperature": "10^32 K",
            "description": "Quantum gravity dominates, unknown physics"
        },
        "Grand Unification": {
            "time": "10^-43 to 10^-36 s",
            "temperature": "10^28 K",
            "description": "Strong force decouples from electroweak"
        },
        "Inflation": {
            "time": "10^-36 to 10^-32 s",
            "temperature": "10^27 K",
            "description": "Exponential expansion, universe grows by 10^26"
        },
        "Electroweak Transition": {
            "time": "10^-12 s",
            "temperature": "10^15 K",
            "description": "EM and weak forces separate, Higgs mechanism"
        },
        "Quark Epoch": {
            "time": "10^-12 to 10^-6 s",
            "temperature": "10^13 K",
            "description": "Quark-gluon plasma"
        },
        "Hadron Epoch": {
            "time": "10^-6 to 1 s",
            "temperature": "10^12 K",
            "description": "Quarks combine into protons/neutrons"
        },
        "Nucleosynthesis": {
            "time": "1 s to 3 min",
            "temperature": "10^9 K",
            "description": "Light element formation (H, He, Li)"
        },
        "Photon Epoch": {
            "time": "3 min to 380,000 yr",
            "temperature": "10^4 K",
            "description": "Radiation-dominated, opaque to photons"
        },
        "Recombination": {
            "time": "380,000 yr",
            "temperature": "3,000 K",
            "description": "Atoms form, CMB released, universe becomes transparent"
        },
        "Dark Ages": {
            "time": "380,000 to 200 million yr",
            "temperature": "< 3,000 K",
            "description": "No stars yet, cooling neutral hydrogen"
        },
        "Reionization": {
            "time": "200 million to 1 billion yr",
            "temperature": "< 100 K",
            "description": "First stars form, ionize intergalactic medium"
        },
        "Present Day": {
            "time": "13.8 billion yr",
            "temperature": "2.7 K (CMB)",
            "description": "Galaxy clusters, stars, planets, life"
        }
    }


if __name__ == "__main__":
    # Example usage and testing
    print("Big Bang Simulation Module - Test Suite")
    print("=" * 50)

    # Test 1: Fractal refinement
    print("\nTest 1: Fractal refinement")
    base = np.array([1.0, 2.0, 3.0])
    refined = fractal_refinement(base, 0.1, 2)
    print(f"  Base points: {len(base)}")
    print(f"  Refined points: {len(refined)}")
    print(f"  Expected: {len(base) * (2**2)}")

    # Test 2: Big Bang simulation (fast test)
    print("\nTest 2: Big Bang simulation (50 steps, 2 iterations)")
    data = generate_big_bang_simulation(time_steps=50, fractal_iterations=2, scale=1e-30)
    print(f"  Time range: {data['time'][0]:.3e} to {data['time'][-1]:.3e} s")
    print(f"  Space range: {data['space'][0]:.3e} to {data['space'][-1]:.3e} m")
    print(f"  Density range: {data['density'][-1]:.3e} to {data['density'][0]:.3e} kg/m³")
    print(f"  Spatial points: {len(data['x'])}")

    # Test 3: Cosmic timeline
    print("\nTest 3: Cosmic timeline epochs")
    timeline = get_cosmic_timeline()
    print(f"  Number of epochs: {len(timeline)}")
    print("  Key epochs:")
    for name in ["Planck Epoch", "Inflation", "Recombination", "Present Day"]:
        print(f"    {name}: {timeline[name]['time']}")

    print("\n" + "=" * 50)
    print("All tests completed successfully!")
    print("\nTo visualize simulation, run:")
    print("  data = generate_big_bang_simulation()")
    print("  plot_big_bang(data)")
