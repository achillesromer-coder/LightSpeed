"""
Dark Energy Simulation: Modeling the accelerating expansion of the universe.
"""

import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from dash.exceptions import PreventUpdate
from scipy.constants import c, G, pi

# Constants
UNIVERSE_AGE = 13.8e9 * 365 * 24 * 3600  # seconds (13.8 billion years)
DARK_ENERGY_DENSITY = 7.3e-10  # kg/m^3 (approx. 70% of critical density)
FRACTAL_STEPS = 3  # Default fractal refinement steps

# Fractal Refinement
def fractal_refinement(base_points, scale_factor, iterations):
    """
    Refines spatial distribution using fractal principles.
    """
    points = base_points
    for _ in range(iterations):
        points = np.concatenate([points, points * scale_factor + np.random.uniform(-scale_factor, scale_factor, points.shape)])
    return points

# Dark Energy Simulation Data
def simulate_dark_energy(time_steps=500, fractal_iterations=3, scale=1e25):
    """
    Simulates the effect of dark energy on the accelerating universe.
    """
    time = np.geomspace(1e7, UNIVERSE_AGE, time_steps)  # Time in seconds (start after galaxy formation)
    expansion = scale * np.exp(np.sqrt((8 * pi * G * DARK_ENERGY_DENSITY) / 3) * time)  # Exponential expansion

    # Fractal refinement for spatial distribution
    x_base = np.random.uniform(-1, 1, time_steps)
    y_base = np.random.uniform(-1, 1, time_steps)
    z_base = np.random.uniform(-1, 1, time_steps)

    x_refined = fractal_refinement(x_base, 0.05, fractal_iterations)
    y_refined = fractal_refinement(y_base, 0.05, fractal_iterations)
    z_refined = fractal_refinement(z_base, 0.05, fractal_iterations)

    return {
        "time": time,
        "expansion": expansion,
        "x": x_refined,
        "y": y_refined,
        "z": z_refined,
    }

# Raphael Equations for Dark Energy
def calculate_dark_energy_raphael_equations(time, expansion):
    """
    Calculates Raphael equations for dark energy effects.
    """
    E_density = DARK_ENERGY_DENSITY * c**2
    F_dark = E_density / expansion

    return {
        "Dark Energy Density": E_density,
        "Dark Force": F_dark,
    }

# Visualization
def plot_dark_energy(data):
    """
    Visualizes dark energy dynamics using 3D scatter plots.
    """
    fig = go.Figure()

    # Add fractal spatial evolution
    fig.add_trace(
        go.Scatter3d(
            x=data["x"],
            y=data["y"],
            z=data["z"],
            mode="markers",
            marker=dict(size=2, color=data["expansion"], colorscale="Inferno", opacity=0.7),
            name="Fractal Expansion"
        )
    )

    # Add time-expansion trace
    fig.add_trace(
        go.Scatter3d(
            x=data["time"],
            y=data["expansion"],
            z=np.zeros_like(data["time"]),
            mode="lines",
            line=dict(color="cyan", width=4),
            name="Expansion Over Time"
        )
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="Time (s)", backgroundcolor="black"),
            yaxis=dict(title="Expansion Scale (m)", backgroundcolor="black"),
            zaxis=dict(title="Spatial Distribution", backgroundcolor="black"),
        ),
        title="Dark Energy Simulation with Fractal Refinement",
        paper_bgcolor="black",
        font=dict(color="white")
    )

    fig.show()

# Interactive Dark Energy Simulation with Dash
app = Dash(__name__)

# Default Simulation Data
data = simulate_dark_energy(time_steps=500, fractal_iterations=FRACTAL_STEPS)

# Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "fontFamily": "Arial"},
    children=[
        html.H1("Dark Energy Simulation with Fractal Refinement", style={"textAlign": "center"}),
        html.Div([
            html.Label("Fractal Refinement Steps:"),
            dcc.Slider(
                id="fractal-slider",
                min=1,
                max=5,
                step=1,
                value=FRACTAL_STEPS,
                marks={i: str(i) for i in range(1, 6)},
            ),
        ], style={"margin": "20px"}),

        html.Div([
            dcc.Graph(id="dark-energy-visualization", style={"height": "75vh"}),
        ]),
    ]
)

# Callbacks
@app.callback(
    Output("dark-energy-visualization", "figure"),
    [Input("fractal-slider", "value")]
)
def update_visualization(fractal_steps):
    if fractal_steps is None:
        raise PreventUpdate

    # Update simulation data with refined fractal steps
    updated_data = simulate_dark_energy(time_steps=500, fractal_iterations=fractal_steps)

    # Generate updated plot
    fig = go.Figure()

    # Add fractal spatial evolution
    fig.add_trace(
        go.Scatter3d(
            x=updated_data["x"],
            y=updated_data["y"],
            z=updated_data["z"],
            mode="markers",
            marker=dict(size=2, color=updated_data["expansion"], colorscale="Inferno", opacity=0.7),
            name="Fractal Expansion"
        )
    )

    # Add time-expansion trace
    fig.add_trace(
        go.Scatter3d(
            x=updated_data["time"],
            y=updated_data["expansion"],
            z=np.zeros_like(updated_data["time"]),
            mode="lines",
            line=dict(color="cyan", width=4),
            name="Expansion Over Time"
        )
    )

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="Time (s)", backgroundcolor="black"),
            yaxis=dict(title="Expansion Scale (m)", backgroundcolor="black"),
            zaxis=dict(title="Spatial Distribution", backgroundcolor="black"),
        ),
        title=f"Dark Energy Simulation - {fractal_steps} Fractal Refinement Steps",
        paper_bgcolor="black",
        font=dict(color="white")
    )

    return fig

# Run App
if __name__ == "__main__":
    app.run_server(debug=True)
