"""
Cosmic Microwave Background Simulation: Visualizing temperature fluctuations and anisotropies in the early universe.
"""

import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from dash.exceptions import PreventUpdate
from scipy.constants import c, k, G, pi

# Constants
CMB_TEMPERATURE = 2.725  # Average temperature in Kelvin
FLUCTUATION_SCALE = 0.0001  # Standard deviation for temperature fluctuations
GRID_SIZE = 512  # Resolution of the CMB map
FRACTAL_STEPS = 3  # Default fractal refinement steps

# Fractal Refinement for CMB
def fractal_cmb_refinement(base_map, scale_factor, iterations):
    """
    Refines the temperature fluctuation map using fractal noise.
    """
    refined_map = base_map
    for _ in range(iterations):
        noise = np.random.normal(0, scale_factor, base_map.shape)
        refined_map += noise
    return refined_map

# Generate CMB Map
def generate_cmb_map(grid_size=GRID_SIZE, fluctuation_scale=FLUCTUATION_SCALE, fractal_iterations=3):
    """
    Generates a simulated CMB temperature map with fractal refinement.
    """
    base_map = np.random.normal(CMB_TEMPERATURE, fluctuation_scale, (grid_size, grid_size))
    refined_map = fractal_cmb_refinement(base_map, fluctuation_scale / 2, fractal_iterations)
    return refined_map

# Raphael Equations for CMB
def calculate_cmb_raphael_equations(temperature, fluctuation):
    """
    Calculates Raphael equations for CMB energy and forces.
    """
    E_density = (k * temperature) / (c**2)  # Energy density approximation
    F_cmb = fluctuation * E_density  # Force influenced by fluctuation scale

    return {
        "Energy Density": E_density,
        "CMB Force": F_cmb,
    }

# Interactive Visualization
def plot_cmb(refined_map):
    """
    Visualizes the CMB temperature map in 2D using Plotly.
    """
    fig = go.Figure(data=go.Heatmap(
        z=refined_map,
        colorscale="Plasma",
        colorbar=dict(title="Temperature (K)")
    ))

    fig.update_layout(
        title="Cosmic Microwave Background Simulation",
        xaxis=dict(title="Right Ascension", showgrid=False, zeroline=False),
        yaxis=dict(title="Declination", showgrid=False, zeroline=False),
        paper_bgcolor="black",
        font=dict(color="white")
    )

    return fig

# Interactive CMB Simulation with Dash
app = Dash(__name__)

# Default CMB Map
cmb_map = generate_cmb_map(grid_size=GRID_SIZE, fractal_iterations=FRACTAL_STEPS)

# Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "fontFamily": "Arial"},
    children=[
        html.H1("Cosmic Microwave Background Simulation", style={"textAlign": "center"}),
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
            dcc.Graph(id="cmb-visualization", style={"height": "75vh"}),
        ]),
    ]
)

# Callbacks
@app.callback(
    Output("cmb-visualization", "figure"),
    [Input("fractal-slider", "value")]
)
def update_cmb_visualization(fractal_steps):
    if fractal_steps is None:
        raise PreventUpdate

    # Generate updated CMB map
    updated_map = generate_cmb_map(grid_size=GRID_SIZE, fractal_iterations=fractal_steps)

    # Generate updated plot
    fig = plot_cmb(updated_map)
    fig.update_layout(
        title=f"CMB Simulation - {fractal_steps} Fractal Refinement Steps"
    )
    return fig

# Run App
if __name__ == "__main__":
    app.run_server(debug=True)
