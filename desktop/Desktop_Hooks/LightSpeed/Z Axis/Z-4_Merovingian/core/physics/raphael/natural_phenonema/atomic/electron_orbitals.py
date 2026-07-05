"""
Electron Orbitals Simulation
"""

import numpy as np
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Constants
PLANCK_CONSTANT = 6.626e-34  # Planck's constant in J.s
ELECTRON_MASS = 9.109e-31  # Mass of an electron in kg
PERMITTIVITY = 8.854e-12  # Permittivity of free space in F/m
ELEMENTARY_CHARGE = 1.602e-19  # Charge of an electron in C

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])

# Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "fontFamily": "Arial"},
    children=[
        html.H1("Electron Orbitals Simulation", style={"textAlign": "center", "color": "cyan"}),
        html.Label("Select Principal Quantum Number (n):", style={"color": "white"}),
        dcc.Slider(
            id="quantum-number-slider",
            min=1,
            max=5,
            step=1,
            value=1,
            marks={i: str(i) for i in range(1, 6)},
            tooltip={"placement": "bottom", "always_visible": True},
        ),
        dcc.Graph(id="orbital-visualization", style={"height": "80vh"}),
    ],
)

# Generate radial probability distribution
def radial_distribution(n, r):
    """
    Calculate radial probability density for hydrogen-like orbitals.

    Parameters:
        n (int): Principal quantum number.
        r (float): Radial distance.

    Returns:
        density (float): Probability density at r.
    """
    # Bohr radius (in meters)
    a0 = 5.29177e-11
    # Simplified probability density for hydrogen-like orbitals
    density = (2 / n)**3 * (r / a0)**2 * np.exp(-2 * r / (n * a0))
    return density

@app.callback(
    Output("orbital-visualization", "figure"),
    [Input("quantum-number-slider", "value")],
)
def update_orbital_visualization(n):
    """
    Update the visualization of electron orbitals for a given principal quantum number.

    Parameters:
        n (int): Principal quantum number.

    Returns:
        fig (plotly.graph_objects.Figure): 3D orbital visualization.
    """
    # Generate spherical coordinates
    r = np.linspace(0, 10, 500)  # Radial distance
    theta = np.linspace(0, 2 * np.pi, 100)
    phi = np.linspace(0, np.pi, 100)
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
            xaxis=dict(title="X", color="white", backgroundcolor="black"),
            yaxis=dict(title="Y", color="white", backgroundcolor="black"),
            zaxis=dict(title="Z", color="white", backgroundcolor="black"),
        ),
        paper_bgcolor="black",
        font=dict(color="white"),
    )
    return fig

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
