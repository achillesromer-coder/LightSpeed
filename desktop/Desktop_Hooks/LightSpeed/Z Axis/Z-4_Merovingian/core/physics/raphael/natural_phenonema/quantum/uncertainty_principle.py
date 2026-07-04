"""
Uncertainty Principle Simulation
"""

import numpy as np
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])

# Layout for the Dash app
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "fontFamily": "Arial"},
    children=[
        html.H1("Uncertainty Principle Simulation", style={"textAlign": "center", "color": "cyan"}),
        html.Div(
            children=[
                html.Label("Uncertainty in Position (Δx):", style={"color": "white"}),
                dcc.Slider(
                    id="position-slider",
                    min=0.1,
                    max=10.0,
                    step=0.1,
                    value=1.0,
                    marks={i: f"{i:.1f}" for i in np.arange(0.1, 10.1, 1.0)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
                html.Label("Uncertainty in Momentum (Δp):", style={"color": "white", "marginTop": "20px"}),
                dcc.Slider(
                    id="momentum-slider",
                    min=0.1,
                    max=10.0,
                    step=0.1,
                    value=1.0,
                    marks={i: f"{i:.1f}" for i in np.arange(0.1, 10.1, 1.0)},
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ],
            style={"margin": "20px"},
        ),
        dcc.Graph(id="uncertainty-graph", style={"height": "80vh"}),
    ],
)

# Heisenberg's Uncertainty Principle
def calculate_uncertainty(delta_x):
    """
    Calculate the uncertainty in momentum given the uncertainty in position (Δx).

    Parameters:
        delta_x (float): Uncertainty in position.

    Returns:
        delta_p (float): Uncertainty in momentum.
    """
    hbar = 1.0  # Reduced Planck constant (normalized)
    delta_p = hbar / (2 * delta_x)  # Δp = ℏ / (2 * Δx)
    return delta_p

# Callback to update graph dynamically
@app.callback(
    Output("uncertainty-graph", "figure"),
    [Input("position-slider", "value")],
)
def update_uncertainty_graph(delta_x):
    """
    Update the visualization of the uncertainty principle based on position uncertainty.

    Parameters:
        delta_x (float): Uncertainty in position (Δx).

    Returns:
        fig (plotly.graph_objects.Figure): Updated figure.
    """
    delta_p = calculate_uncertainty(delta_x)

    # Create Gaussian-like distributions for position and momentum
    x = np.linspace(-10, 10, 500)
    position_distribution = np.exp(-x**2 / (2 * delta_x**2))
    momentum_distribution = np.exp(-x**2 / (2 * delta_p**2))

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=position_distribution,
            mode="lines",
            line=dict(color="blue", width=3),
            name=f"Position (Δx = {delta_x:.2f})",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x,
            y=momentum_distribution,
            mode="lines",
            line=dict(color="red", width=3),
            name=f"Momentum (Δp = {delta_p:.2f})",
        )
    )

    fig.update_layout(
        title="Uncertainty Principle: Position vs Momentum",
        xaxis=dict(title="x / p", color="white", showgrid=True, gridcolor="gray"),
        yaxis=dict(title="Probability Density", color="white", showgrid=True, gridcolor="gray"),
        paper_bgcolor="black",
        plot_bgcolor="black",
        font=dict(color="white"),
        legend=dict(x=0, y=1, bgcolor="rgba(0,0,0,0)", bordercolor="cyan"),
    )

    return fig

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
