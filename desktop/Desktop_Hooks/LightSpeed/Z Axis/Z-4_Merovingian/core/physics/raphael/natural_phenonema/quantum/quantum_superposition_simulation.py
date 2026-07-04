"""
Quantum Superposition Simulation
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
        html.H1("Quantum Superposition Simulation", style={"textAlign": "center", "color": "cyan"}),
        html.Div(
            children=[
                html.Label("Number of States:", style={"color": "white"}),
                dcc.Slider(
                    id="states-slider",
                    min=2,
                    max=10,
                    step=1,
                    value=3,
                    marks={i: str(i) for i in range(2, 11)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Label("Phase Difference:", style={"color": "white", "marginTop": "20px"}),
                dcc.Slider(
                    id="phase-slider",
                    min=0.0,
                    max=2 * np.pi,
                    step=0.1,
                    value=np.pi / 2,
                    marks={0: "0", np.pi: "π", 2 * np.pi: "2π"},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ],
            style={"margin": "20px"},
        ),
        dcc.Graph(id="superposition-graph", style={"height": "80vh"}),
    ],
)

# Generate superposition data
def generate_superposition_data(num_states=3, phase_difference=np.pi / 2):
    """
    Generates data for visualizing quantum superposition.

    Parameters:
        num_states (int): Number of basis states.
        phase_difference (float): Phase difference between basis states.

    Returns:
        x (np.ndarray): x-coordinates.
        y (np.ndarray): Superposition amplitude values.
    """
    x = np.linspace(-2 * np.pi, 2 * np.pi, 500)
    y = np.zeros_like(x)
    for n in range(num_states):
        y += np.sin(x + n * phase_difference)
    return x, y

# Callback to update the graph dynamically
@app.callback(
    Output("superposition-graph", "figure"),
    [Input("states-slider", "value"), Input("phase-slider", "value")],
)
def update_superposition_graph(num_states, phase_difference):
    """
    Updates the quantum superposition visualization based on user input.

    Parameters:
        num_states (int): Number of basis states.
        phase_difference (float): Phase difference between basis states.

    Returns:
        fig (plotly.graph_objects.Figure): Updated figure.
    """
    x, y = generate_superposition_data(num_states=num_states, phase_difference=phase_difference)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x, y=y, mode="lines",
            line=dict(color="cyan", width=3),
            name="Superposition State",
        )
    )

    fig.update_layout(
        title="Quantum Superposition",
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
