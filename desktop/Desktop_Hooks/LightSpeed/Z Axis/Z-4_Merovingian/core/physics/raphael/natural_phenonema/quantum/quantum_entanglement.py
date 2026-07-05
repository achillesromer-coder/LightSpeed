"""
Quantum Entanglement Simulation
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
        html.H1("Quantum Entanglement Simulation", style={"textAlign": "center", "color": "cyan"}),
        html.Div(
            children=[
                html.Label("Spin Correlation Strength:", style={"color": "white"}),
                dcc.Slider(
                    id="correlation-slider",
                    min=0.0,
                    max=1.0,
                    step=0.01,
                    value=0.8,
                    marks={i / 10: f"{i / 10}" for i in range(0, 11)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Label("Number of Pairs:", style={"color": "white", "marginTop": "20px"}),
                dcc.Slider(
                    id="pairs-slider",
                    min=50,
                    max=1000,
                    step=50,
                    value=200,
                    marks={i: str(i) for i in range(50, 1050, 200)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ],
            style={"margin": "20px"},
        ),
        dcc.Graph(id="entanglement-graph", style={"height": "80vh"}),
    ],
)

# Generate entangled states
def generate_entangled_states(num_pairs=200, correlation_strength=0.8):
    """
    Generates data for visualizing quantum entanglement.

    Parameters:
        num_pairs (int): Number of entangled particle pairs.
        correlation_strength (float): Degree of correlation between the particles (0.0 to 1.0).

    Returns:
        angles_A (np.ndarray): Measurement angles for particle A.
        angles_B (np.ndarray): Measurement angles for particle B.
        correlations (np.ndarray): Correlation values between particles A and B.
    """
    angles_A = np.random.uniform(0, 2 * np.pi, num_pairs)
    angles_B = angles_A + np.random.uniform(-np.pi * (1 - correlation_strength), np.pi * (1 - correlation_strength), num_pairs)
    correlations = np.cos(angles_A - angles_B)
    return angles_A, angles_B, correlations

# Callback to update the graph dynamically
@app.callback(
    Output("entanglement-graph", "figure"),
    [Input("correlation-slider", "value"), Input("pairs-slider", "value")],
)
def update_entanglement_graph(correlation_strength, num_pairs):
    """
    Updates the quantum entanglement visualization based on user input.

    Parameters:
        correlation_strength (float): User-defined correlation strength (0.0 to 1.0).
        num_pairs (int): Number of entangled pairs to generate.

    Returns:
        fig (plotly.graph_objects.Figure): Updated figure.
    """
    angles_A, angles_B, correlations = generate_entangled_states(
        num_pairs=num_pairs, correlation_strength=correlation_strength
    )

    fig = go.Figure()

    # Scatter plot for entangled states
    fig.add_trace(
        go.Scatter(
            x=angles_A, y=angles_B, mode="markers",
            marker=dict(size=8, color=correlations, colorscale="Viridis", showscale=True),
            name="Entangled Pairs",
        )
    )

    fig.update_layout(
        title="Quantum Entanglement: Correlation of Entangled Pairs",
        xaxis=dict(title="Angle A (radians)", color="white", showgrid=True, gridcolor="gray"),
        yaxis=dict(title="Angle B (radians)", color="white", showgrid=True, gridcolor="gray"),
        paper_bgcolor="black",
        plot_bgcolor="black",
        font=dict(color="white"),
        legend=dict(x=0, y=1, bgcolor="rgba(0,0,0,0)", bordercolor="cyan"),
    )

    return fig

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
