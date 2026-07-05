"""
Wave-particle duality simulation with dynamic visualization.
"""

import numpy as np
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])

# Layout for the Dash app
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "fontFamily": "Arial"},
    children=[
        html.H1("Wave-Particle Duality Simulation", style={"textAlign": "center", "color": "cyan"}),
        html.Div(
            children=[
                html.Label("Wave Contribution:", style={"color": "white"}),
                dcc.Slider(
                    id="wave-slider",
                    min=0.0,
                    max=1.0,
                    step=0.01,
                    value=0.5,
                    marks={i / 10: f"{i / 10}" for i in range(0, 11)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Label("Number of Points:", style={"color": "white", "marginTop": "20px"}),
                dcc.Slider(
                    id="points-slider",
                    min=100,
                    max=1000,
                    step=50,
                    value=500,
                    marks={i: str(i) for i in range(100, 1100, 200)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ],
            style={"margin": "20px"},
        ),
        dcc.Graph(id="wave-particle-graph", style={"height": "80vh"}),
    ],
)

# Generate wave-particle duality data
def generate_wave_particle_duality(num_points=500, wave_contribution=0.5):
    """
    Generates data for visualizing wave-particle duality.

    Parameters:
        num_points (int): Number of data points.
        wave_contribution (float): Proportion of wave behavior (0.0 to 1.0).

    Returns:
        x (np.ndarray): x-coordinates.
        y_wave (np.ndarray): Wave-like component.
        y_particle (np.ndarray): Particle-like component.
        y_combined (np.ndarray): Combined wave-particle data.
    """
    x = np.linspace(-10, 10, num_points)
    wave_amplitude = np.sin(2 * np.pi * x) * wave_contribution
    particle_peaks = np.exp(-x**2) * (1 - wave_contribution)
    y_combined = wave_amplitude + particle_peaks
    return x, wave_amplitude, particle_peaks, y_combined

# Callback to update the graph dynamically
@app.callback(
    Output("wave-particle-graph", "figure"),
    [Input("wave-slider", "value"), Input("points-slider", "value")],
)
def update_wave_particle_graph(wave_contribution, num_points):
    """
    Updates the wave-particle duality visualization based on user input.

    Parameters:
        wave_contribution (float): User-defined wave contribution (0.0 to 1.0).
        num_points (int): Number of data points to generate.

    Returns:
        fig (plotly.graph_objects.Figure): Updated figure.
    """
    x, y_wave, y_particle, y_combined = generate_wave_particle_duality(
        num_points=num_points, wave_contribution=wave_contribution
    )

    fig = go.Figure()

    # Wave component
    fig.add_trace(
        go.Scatter(
            x=x, y=y_wave, mode="lines", name="Wave Component",
            line=dict(color="blue", width=2),
        )
    )

    # Particle component
    fig.add_trace(
        go.Scatter(
            x=x, y=y_particle, mode="lines", name="Particle Component",
            line=dict(color="orange", width=2),
        )
    )

    # Combined behavior
    fig.add_trace(
        go.Scatter(
            x=x, y=y_combined, mode="lines", name="Combined Behavior",
            line=dict(color="red", width=3),
        )
    )

    fig.update_layout(
        title="Wave-Particle Duality",
        xaxis=dict(title="Position (x)", color="white", showgrid=True, gridcolor="gray"),
        yaxis=dict(title="Amplitude (y)", color="white", showgrid=True, gridcolor="gray"),
        paper_bgcolor="black",
        plot_bgcolor="black",
        font=dict(color="white"),
        legend=dict(x=0, y=1, bgcolor="rgba(0,0,0,0)", bordercolor="cyan"),
    )

    return fig

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
