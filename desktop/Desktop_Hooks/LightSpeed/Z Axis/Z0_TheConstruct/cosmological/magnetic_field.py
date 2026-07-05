
# Imports

from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import callback_context
from dash import dcc
from dash import html
import dash_bootstrap_components
import numpy
import plotly.graph_objs


# ===== CONSOLIDATED FROM 10 FILES =====

# Merged on: 2025-11-21 17:46:24

# Source files: 10



# Imports

from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import callback_context
from dash import dcc
from dash import html
import dash_bootstrap_components
import numpy
import plotly.graph_objs


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-17 13:43:29

# Source files: 3


import numpy as np
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash import callback_context as ctx

# Constants
G = 6.67430e-11  # Gravitational constant
RADIUS_EARTH = 6.371e6  # Earth's radius in meters
ATMOSPHERIC_SCALE_HEIGHT = 8500  # Scale height of Earth's atmosphere in meters
DEFAULT_ROTATION_PERIOD = 8  # Default rotation period (seconds per planetary rotation)

# Default Parameters
default_core_mass = 5.972e24  # Earth's mass (kg)
default_temperature = 288  # Average surface temperature (K)
resolution = 50  # Grid resolution
scale = RADIUS_EARTH * 1.1  # Slightly larger than Earth's radius

# Initialize Dash App
app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE])


# Generate Atmospheric Data
def generate_atmosphere(core_mass, temperature, time):
    """Generates atmospheric data over time based on gravitational effects and rotation."""
    theta = np.linspace(0, np.pi, resolution)
    phi = np.linspace(0, 2 * np.pi, resolution)
    r = np.linspace(RADIUS_EARTH, scale, resolution)

    r, theta, phi = np.meshgrid(r, theta, phi)

    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.sin(phi)
    z = r * np.cos(theta)

    # Density and pressure decay with altitude
    density = np.exp(-(r - RADIUS_EARTH) / ATMOSPHERIC_SCALE_HEIGHT) * (temperature / 288)
    pressure = density * np.cos(time * 2 * np.pi / DEFAULT_ROTATION_PERIOD)

    return x, y, z, density, pressure


# Create 3D Figure
def create_figure(x, y, z, density, pressure, time):
    """Creates a 3D visualization of atmospheric layers with density and pressure."""
    fig = go.Figure()

    # Density Visualization
    fig.add_trace(go.Volume(
        x=x.flatten(), y=y.flatten(), z=z.flatten(),
        value=density.flatten(),
        isomin=density.min(), isomax=density.max(),
        opacity=0.1, surface_count=15, colorscale="Viridis",
        name="Density"
    ))

    # Pressure Visualization (time-dependent oscillations)
    fig.add_trace(go.Volume(
        x=x.flatten(), y=y.flatten(), z=z.flatten(),
        value=pressure.flatten(),
        isomin=pressure.min(), isomax=pressure.max(),
        opacity=0.1, surface_count=10, colorscale="Inferno",
        name="Pressure"
    ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X Axis", range=[-scale, scale]),
            yaxis=dict(title="Y Axis", range=[-scale, scale]),
            zaxis=dict(title="Z Axis", range=[-scale, scale]),
        ),
        title=f"Atmospheric Simulation at Time: {time:.2f}s",
        margin=dict(l=0, r=0, t=50, b=50)
    )

    return fig


# App Layout
app.layout = html.Div([
    html.H1("Dynamic Atmospheric Layers Simulation", style={"textAlign": "center"}),

    # 3D Visualization
    dcc.Graph(id="atmosphere-visualization", style={"height": "80vh"}),

    # Sliders for Parameter Adjustment
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Core Mass (kg)"),
                dcc.Slider(id="core-mass-slider", min=1e24, max=1e28, step=1e24, value=default_core_mass,
                           marks={1e24: "1e24", 1e28: "1e28"})
            ], width=6),
            dbc.Col([
                html.Label("Temperature (K)"),
                dcc.Slider(id="temperature-slider", min=200, max=1000, step=10, value=default_temperature,
                           marks={200: "200", 1000: "1000"})
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                html.Label("Time (s)"),
                dcc.Slider(id="time-slider", min=0, max=DEFAULT_ROTATION_PERIOD, step=0.1, value=0,
                           marks={0: "0s", DEFAULT_ROTATION_PERIOD: f"{DEFAULT_ROTATION_PERIOD}s"})
            ], width=12),
        ])
    ], style={"padding": "20px"}),

    # Play Button
    html.Div([
        html.Button("Play", id="play-button", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Pause", id="pause-button", n_clicks=0),
    ], style={"textAlign": "center"}),

    # Interval for Animation
    dcc.Interval(id="animation-interval", interval=100, n_intervals=0, disabled=True),
])


# Callback for Animation
@app.callback(
    Output("animation-interval", "disabled"),
    [Input("play-button", "n_clicks"), Input("pause-button", "n_clicks")],
    prevent_initial_call=True
)
def toggle_animation(play_clicks, pause_clicks):
    triggered_id = ctx.triggered_id
    return triggered_id == "pause-button"


# Callback for Updating the Simulation
@app.callback(
    Output("atmosphere-visualization", "figure"),
    [Input("animation-interval", "n_intervals"), Input("time-slider", "value")],
    [State("core-mass-slider", "value"), State("temperature-slider", "value")]
)
def update_simulation(n_intervals, time_slider_value, core_mass, temperature):
    time = n_intervals * 0.1 if ctx.triggered_id == "animation-interval" else time_slider_value
    x, y, z, density, pressure = generate_atmosphere(core_mass, temperature, time)
    return create_figure(x, y, z, density, pressure, time)


# Run the App
if __name__ == "__main__":
    app.run_server(debug=True)
