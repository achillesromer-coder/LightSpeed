
# Imports

from dash import Input
from dash import Output
from dash import callback_context
from dash import dcc
from dash import html
import dash
import numpy
import plotly.graph_objects


# ===== CONSOLIDATED FROM 10 FILES =====

# Merged on: 2025-11-21 17:46:23

# Source files: 10



# Imports

from dash import Input
from dash import Output
from dash import callback_context
from dash import dcc
from dash import html
import dash
import numpy
import plotly.graph_objects


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-17 13:43:28

# Source files: 3


import dash
from dash import dcc, html, Input, Output, callback_context
import numpy as np
import plotly.graph_objects as go

# Initialize the Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Interactive Black Hole Simulation", style={"text-align": "center"}),
    dcc.Dropdown(
        id="black-hole-preset",
        options=[
            {"label": "Stellar Black Hole", "value": "stellar"},
            {"label": "Supermassive Black Hole", "value": "supermassive"},
            {"label": "Intermediate Black Hole", "value": "intermediate"},
            {"label": "Primordial Black Hole", "value": "primordial"},
            {"label": "Quantum Black Hole", "value": "quantum"},
        ],
        value="stellar",
        placeholder="Select a black hole preset",
    ),
    dcc.Slider(
        id="spin-slider",
        min=0,
        max=1,
        step=0.1,
        value=0.5,
        marks={i / 10: str(i / 10) for i in range(11)},
    ),
    dcc.Slider(
        id="accretion-slider",
        min=0,
        max=1,
        step=0.1,
        value=0.5,
        marks={i / 10: str(i / 10) for i in range(11)},
    ),
    dcc.Graph(id="black-hole-graph"),
])

# Helper functions
def generate_holograph(spin, accretion, preset):
    # Create a 3D visualization of the black hole based on the inputs
    grid_size = 30
    x = np.linspace(-1, 1, grid_size)
    y = np.linspace(-1, 1, grid_size)
    x, y = np.meshgrid(x, y)

    z = np.exp(-np.sqrt(x**2 + y**2)) * spin * accretion  # Simplified curvature visualization
    colorscale = [[0, "black"], [0.5, "purple"], [1, "yellow"]]

    fig = go.Figure()

    # Accretion disk
    fig.add_trace(go.Surface(
        z=-0.1 * np.ones_like(z),
        x=x, y=y,
        surfacecolor=z,
        colorscale=colorscale,
        showscale=False,
        name="Accretion Disk"
    ))

    # Relativistic jets
    jet_length = 2
    jet_z = np.linspace(0, jet_length, grid_size)
    jet_r = 0.05
    jet_x = jet_r * np.sin(np.linspace(0, 2 * np.pi, grid_size))
    jet_y = jet_r * np.cos(np.linspace(0, 2 * np.pi, grid_size))

    fig.add_trace(go.Scatter3d(
        x=jet_x, y=jet_y, z=jet_z,
        mode="lines",
        line=dict(color="blue", width=3),
        name="Relativistic Jet"
    ))

    # Event horizon
    fig.add_trace(go.Surface(
        z=z,
        x=x, y=y,
        surfacecolor=z,
        colorscale="Inferno",
        showscale=False,
        name="Event Horizon"
    ))

    # Configure the layout
    fig.update_layout(
        title=f"Black Hole Holographic Visualization - {preset.title()}",
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Spacetime Curvature",
            aspectratio=dict(x=1, y=1, z=0.5),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5),
            ),
        ),
        template="plotly_dark",
    )
    return fig

# Callbacks
@app.callback(
    Output("black-hole-graph", "figure"),
    [
        Input("spin-slider", "value"),
        Input("accretion-slider", "value"),
        Input("black-hole-preset", "value"),
    ]
)
def update_black_hole_graph(spin, accretion, preset):
    # Identify which input triggered the callback
    ctx = callback_context
    triggered_input = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # Generate the holograph based on the inputs
    if triggered_input in ["spin-slider", "accretion-slider", "black-hole-preset"]:
        return generate_holograph(spin, accretion, preset)

    # Default graph if no input has changed
    return dash.no_update

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
