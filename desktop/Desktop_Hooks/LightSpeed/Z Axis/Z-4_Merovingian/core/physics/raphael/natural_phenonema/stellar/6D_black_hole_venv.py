# file: oval_spacetime_holomap.py

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

# Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
app.title = "Oval Spacetime Holomap Simulation"

# Raphael Equations for Elliptical Spacetime
def raphael_equations_oval(r, theta, phi, t, mass, spin):
    """
    Elliptical Raphael equations for curvature, density, energy, and dark energy dynamics.
    """
    curvature = -np.exp(-r ** 2 / (2 * mass)) * np.cos(spin * t)
    density = np.exp(-r / (mass * 10)) * np.sin(t)
    energy = np.sin(r * np.sin(theta) * np.cos(phi) * t) * np.exp(-t / 50)
    dark_energy = (1 / (1 + np.exp(-curvature * density))) * energy
    return curvature, density, energy, dark_energy

# Generate Oval Spacetime Data
def generate_oval_data(mass, spin, resolution, scale, t):
    """
    Generate radial spacetime data for oval-shaped spacetime.
    """
    r = np.linspace(0, scale, resolution)
    theta = np.linspace(0, np.pi, resolution)
    phi = np.linspace(0, 2 * np.pi, resolution)
    r, theta, phi = np.meshgrid(r, theta, phi)
    curvature, density, energy, dark_energy = raphael_equations_oval(r, theta, phi, t, mass, spin)
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)
    return x, y, z, curvature, density, energy, dark_energy

# Calamity Presets
calamity_presets = {
    "None": {"mass": 50, "spin": 1, "scale": 1e5, "resolution": 30},
    "Black Hole Merge": {"mass": 100, "spin": 7, "scale": 5e5, "resolution": 50},
    "Supernova": {"mass": 500, "spin": 3, "scale": 2e5, "resolution": 40},
    "Quantum Fluctuation": {"mass": 20, "spin": 0.5, "scale": 1e4, "resolution": 20},
}

# Visualization Function
def create_oval_figure(x, y, z, curvature, density, energy, dark_energy, overlays):
    """
    Create holographic oval spacetime visualization.
    """
    fig = go.Figure()

    # Fluid Dynamic Holomapping
    if overlays.get("fluid"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=curvature.flatten(),
            isomin=-1,
            isomax=1,
            opacity=0.72,
            colorscale="Viridis",
            name="Fluid Dynamics"
        ))

    # Dark Energy Expansion
    if overlays.get("expansion"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=dark_energy.flatten(),
            isomin=0,
            isomax=1,
            opacity=0.7,
            colorscale="Reds",
            name="Dark Energy Expansion"
        ))

    # CMB Layer (Outer Shell)
    if overlays.get("cmb"):
        fig.add_trace(go.Surface(
            x=x[:, :, -1],
            y=y[:, :, -1],
            z=z[:, :, -1],
            surfacecolor=density[:, :, -1],
            colorscale="Blues",
            opacity=0.5,
            name="CMB Layer"
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            camera=dict(eye=dict(x=2, y=2, z=2))
        ),
        margin=dict(l=0, r=0, t=50, b=50),
        title="Oval Spacetime Holomap"
    )
    return fig

# App Layout
app.layout = html.Div([
    html.H1("Oval Spacetime Holomap Simulation", style={"textAlign": "center"}),

    # Calamity Preset Dropdown
    dbc.Row([
        dbc.Col(html.Label("Calamity Preset"), width=3),
        dbc.Col(dcc.Dropdown(
            id="calamity-dropdown",
            options=[{"label": key, "value": key} for key in calamity_presets.keys()],
            value="None"
        ), width=9)
    ], style={"marginBottom": "20px"}),

    # Overlay Toggles
    dbc.Checklist(
        options=[
            {"label": "Fluid Dynamics", "value": "fluid"},
            {"label": "Dark Energy Expansion", "value": "expansion"},
            {"label": "CMB Layer", "value": "cmb"}
        ],
        value=["fluid", "expansion", "cmb"],
        id="overlay-checklist",
        inline=True
    ),

    # Graph
    dcc.Graph(id="oval-spacetime-graph", style={"height": "80vh"}),

    # Playback and Reset Buttons
    html.Div([
        html.Button("Play", id="play-button", n_clicks=0, style={"margin": "10px"}),
        html.Button("Reset", id="reset-button", n_clicks=0, style={"margin": "10px"})
    ]),

    # Interval for Updates
    dcc.Interval(id="simulation-interval", interval=100, n_intervals=0, disabled=True)
])

# Callbacks
@app.callback(
    Output("oval-spacetime-graph", "figure"),
    [
        Input("calamity-dropdown", "value"),
        Input("overlay-checklist", "value"),
        Input("simulation-interval", "n_intervals")
    ]
)
def update_simulation(calamity, overlays, n_intervals):
    params = calamity_presets[calamity]
    overlays = {key: key in overlays for key in ["fluid", "expansion", "cmb"]}
    x, y, z, curvature, density, energy, dark_energy = generate_oval_data(
        params["mass"], params["spin"], params["resolution"], params["scale"], n_intervals
    )
    return create_oval_figure(x, y, z, curvature, density, energy, dark_energy, overlays)

@app.callback(
    Output("simulation-interval", "disabled"),
    Input("play-button", "n_clicks")
)
def toggle_playback(n_clicks):
    return n_clicks % 2 == 0

@app.callback(
    Output("simulation-interval", "n_intervals"),
    Input("reset-button", "n_clicks")
)
def reset_simulation(n_clicks):
    return 0

if __name__ == "__main__":
    app.run_server(debug=True)
