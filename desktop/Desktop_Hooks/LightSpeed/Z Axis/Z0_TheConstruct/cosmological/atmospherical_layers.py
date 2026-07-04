
# Imports

from dash import Dash
from dash import Input
from dash import Output
from dash import dcc
from dash import html
import dash_bootstrap_components
import numpy
import plotly.graph_objs


# ===== CONSOLIDATED FROM 10 FILES =====

# Merged on: 2025-11-21 17:46:22

# Source files: 10



# Imports

from dash import Dash
from dash import Input
from dash import Output
from dash import dcc
from dash import html
import dash_bootstrap_components
import numpy
import plotly.graph_objs


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-17 13:43:28

# Source files: 3


import numpy as np
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Initialize Dash App
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.SLATE])

# Constants
G = 6.67430e-11  # Gravitational constant
SPEED_OF_LIGHT = 3e8  # Speed of light (m/s)

# Default Parameters
default_core_mass = 5.972e24  # Earth's mass in kg
default_core_density = 5514  # Earth's average density in kg/m^3
default_spin = 0.1  # Fraction of Earth's spin
default_tilt = 23.5  # Earth's axial tilt in degrees
default_temperature = 288  # Average temperature in Kelvin
default_composition = {"N2": 0.78, "O2": 0.21, "CO2": 0.01}  # Atmospheric composition
resolution = 50  # Grid resolution
scale = 1e6  # Render scale in meters

# Function to Calculate Schwarzschild Radius
def calculate_schwarzschild_radius(mass):
    return 2 * G * mass / SPEED_OF_LIGHT**2

# Generate Planetary Core
def generate_core(core_mass, core_density, resolution, scale):
    radius = (3 * core_mass / (4 * np.pi * core_density))**(1 / 3)
    r = np.linspace(-radius, radius, resolution)
    x, y, z = np.meshgrid(r, r, r)
    inside = x**2 + y**2 + z**2 <= radius**2
    core_density_grid = np.zeros_like(x)
    core_density_grid[inside] = core_density
    return x, y, z, core_density_grid

# Generate Atmospheric Layers
def generate_atmosphere(core_radius, temperature, composition, resolution, scale):
    layers = 10  # Number of atmospheric layers
    r = np.linspace(core_radius, core_radius + scale, resolution)
    x, y, z = np.meshgrid(r, r, r)
    atmospheric_density = np.zeros_like(x)

    for i, layer in enumerate(np.linspace(0, scale, layers)):
        layer_density = np.exp(-layer / scale) * (composition["N2"] + composition["O2"] + composition["CO2"])
        atmospheric_density += layer_density

    return x, y, z, atmospheric_density

# Create Planetary Visualization
def create_figure(core_data, atmosphere_data, overlays):
    fig = go.Figure()

    # Core Visualization
    x, y, z, density = core_data
    fig.add_trace(go.Volume(
        x=x.flatten(), y=y.flatten(), z=z.flatten(),
        value=density.flatten(),
        isomin=density.min(), isomax=density.max(),
        opacity=0.8, colorscale="YlGnBu",
        name="Planetary Core"
    ))

    # Atmospheric Visualization
    x, y, z, density = atmosphere_data
    if overlays["atmosphere"]:
        fig.add_trace(go.Volume(
            x=x.flatten(), y=y.flatten(), z=z.flatten(),
            value=density.flatten(),
            isomin=density.min(), isomax=density.max(),
            opacity=0.3, colorscale="RdBu",
            name="Atmosphere"
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title="X Axis",
            yaxis_title="Y Axis",
            zaxis_title="Z Axis"
        ),
        title="Planetary Simulation"
    )
    return fig

# App Layout
app.layout = html.Div([
    html.H1("Dynamic Planetary Simulation", style={"textAlign": "center"}),
    dcc.Graph(id="planet-simulation", style={"height": "80vh"}),
    html.Div([
        html.Label("Core Mass (kg)"),
        dcc.Slider(id="core-mass-slider", min=1e24, max=1e27, step=1e24, value=default_core_mass,
                   marks={1e24: "1e24", 1e27: "1e27"}),

        html.Label("Core Density (kg/m^3)"),
        dcc.Slider(id="core-density-slider", min=3000, max=10000, step=100, value=default_core_density,
                   marks={3000: "3000", 10000: "10000"}),

        html.Label("Temperature (K)"),
        dcc.Slider(id="temperature-slider", min=200, max=1000, step=50, value=default_temperature,
                   marks={200: "200", 1000: "1000"}),

        html.Label("Composition"),
        dcc.Checklist(
            id="composition-checklist",
            options=[
                {"label": "Nitrogen", "value": "N2"},
                {"label": "Oxygen", "value": "O2"},
                {"label": "Carbon Dioxide", "value": "CO2"}
            ],
            value=["N2", "O2", "CO2"]
        ),

        html.Label("Overlays"),
        dcc.Checklist(
            id="overlay-checklist",
            options=[
                {"label": "Show Atmosphere", "value": "atmosphere"}
            ],
            value=["atmosphere"]
        )
    ])
])

# Callbacks for Updates
@app.callback(
    Output("planet-simulation", "figure"),
    [Input("core-mass-slider", "value"),
     Input("core-density-slider", "value"),
     Input("temperature-slider", "value"),
     Input("composition-checklist", "value"),
     Input("overlay-checklist", "value")]
)
def update_simulation(core_mass, core_density, temperature, composition_keys, overlays):
    composition = {key: default_composition[key] for key in composition_keys}
    core_data = generate_core(core_mass, core_density, resolution, scale)
    atmosphere_data = generate_atmosphere(core_data[0].max(), temperature, composition, resolution, scale)
    overlay_flags = {"atmosphere": "atmosphere" in overlays}
    return create_figure(core_data, atmosphere_data, overlay_flags)

# Run App
if __name__ == "__main__":
    app.run_server(debug=True)
