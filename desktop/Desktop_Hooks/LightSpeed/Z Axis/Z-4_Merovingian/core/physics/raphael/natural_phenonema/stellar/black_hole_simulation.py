# file: immersive_fluid_dynamic_blackhole_simulation.py
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

# Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Immersive Black Hole Simulation - Raphael Equations"


# Spacetime Generation Function Using Raphael Equations
def raphael_equations(x, y, z, t, mass, spin):
    """
    Calculates curvature, density, energy, dark matter, and dark energy.
    """
    t = float(t)
    spin = float(spin)
    curvature = -np.exp(-(x ** 2 + y ** 2 + z ** 2) / (2 * mass)) * np.cos(spin * t)
    density = np.exp(-(x ** 2 + y ** 2) / (mass * 10)) * np.sin(t)
    energy = np.sin(x * y * z * t) * np.exp(-t / 50)
    dark_energy = (1 / (1 + np.exp(-curvature * density))) * energy
    dark_matter_guide = np.abs(curvature * density) / (1 + np.abs(curvature) + np.abs(density))
    return curvature, density, energy, dark_energy, dark_matter_guide


# Generate Data Based on the Raphael Equations
def generate_data(mass, spin, resolution, scale, t):
    """Generate 3D data for spacetime (curvature, density, energy, etc.)."""
    x = np.linspace(-scale, scale, resolution)
    y = np.linspace(-scale, scale, resolution)
    z = np.linspace(-scale, scale, resolution)
    x, y, z = np.meshgrid(x, y, z)
    curvature, density, energy, dark_energy, dark_matter_guide = raphael_equations(x, y, z, t, mass, spin)
    return x, y, z, curvature, density, energy, dark_energy, dark_matter_guide


# Define Presets for Calamity (Event) Types (Black Hole Merge, Supernova, etc.)
calamity_presets = {
    "None": {"mass": 50, "spin": 1, "scale": 1e5, "resolution": 30},
    "Black Hole Merge": {"mass": 100, "spin": 5, "scale": 5e5, "resolution": 50},
    "Supernova": {"mass": 500, "spin": 3, "scale": 2e5, "resolution": 40},
    "Quantum Fluctuation": {"mass": 10, "spin": 0.5, "scale": 1e4, "resolution": 20},
}


# Visualization Function for Fluid Dynamics and Full Spectrum Rendering
def create_figure(x, y, z, curvature, density, energy, dark_energy, dark_matter_guide, overlays):
    fig = go.Figure()

    # Fluid Dynamics: Curvature Visualization
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

    # Dark Energy Visualization
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

    # Dark Matter Guide
    if overlays.get("dark_matter"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=dark_matter_guide.flatten(),
            isomin=0,
            isomax=0.1,
            opacity=0.5,
            colorscale="Purples",
            name="Dark Matter Guide"
        ))

    # Energy Field Visualization
    if overlays.get("energy"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=energy.flatten(),
            isomin=-1,
            isomax=1,
            opacity=0.4,
            colorscale="Magma",
            name="Energy Field"
        ))

    # Spacetime Density Visualization
    if overlays.get("density"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=density.flatten(),
            isomin=0,
            isomax=1,
            opacity=0.72,
            colorscale="Blues",
            name="Density Field"
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            camera=dict(eye=dict(x=2, y=2, z=2))
        ),
        margin=dict(l=0, r=0, t=50, b=50),
        title="Immersive Black Hole Simulation"
    )
    return fig


# Layout for Interactive UI (Minimap, Full View, Controls, and Scalar Adjustments)
app.layout = html.Div([
    html.H1("Immersive Real-Time Black Hole Simulation", style={"textAlign": "center"}),

    # Calamity Preset Dropdown for Selecting Simulation Type
    dbc.Row([
        dbc.Col(html.Label("Calamity Preset"), width=3),
        dbc.Col(dcc.Dropdown(
            id="calamity-dropdown",
            options=[{"label": key, "value": key} for key in calamity_presets.keys()],
            value="None"
        ), width=9)
    ], style={"marginBottom": "20px"}),

    # Minimap Display for Smaller View of Spacetime Simulation
    dcc.Graph(id="minimap-graph", style={"height": "30vh"}),  # Minimap for overview

    # Full Simulation View
    dcc.Graph(id="spacetime-graph", style={"height": "70vh"}),  # Immersive 3D view of spacetime

    # Scalar Controls for Adjusting Size and Spin Complexity
    html.Label("Calamity Size Scalar"),
    dcc.Slider(
        id="size-scalar",
        min=-1,
        max=1,
        step=0.1,
        value=0,
        marks={-1: "Null Spacetime", 0: "Critical Singularity", 1: "Supermassive Event"}
    ),
    html.Label("Spin/Complexity Scalar"),
    dcc.Slider(
        id="spin-scalar",
        min=0.5,
        max=10,
        step=0.5,
        value=1,
        marks={0.5: "Low Complexity", 10: "High Complexity"}
    ),

    # Overlay Controls for Visualization Layers
    dbc.Checklist(
        options=[
            {"label": "Fluid Dynamics", "value": "fluid"},
            {"label": "Dark Energy Expansion", "value": "expansion"},
            {"label": "Dark Matter Guide", "value": "dark_matter"},
            {"label": "Energy Field", "value": "energy"},
            {"label": "Density Visualization", "value": "density"},
            {"label": "Electromagnetic Spectrum", "value": "electromagnetic"}
        ],
        value=["fluid", "expansion", "dark_matter", "energy", "density", "electromagnetic"],
        id="overlay-checklist",
        inline=True
    ),

    # Playback and Reset Buttons
    html.Div([
        html.Button("Play", id="play-button", n_clicks=0, style={"margin": "10px"}),
        html.Button("Reset", id="reset-button", n_clicks=0, style={"margin": "10px"})
    ]),

    # Interval for Time Steps (Simulation Speed Control)
    dcc.Interval(id="simulation-interval", interval=100, n_intervals=0, disabled=True)
])


# Callbacks for Real-Time Dynamic Updates
@app.callback(
    Output("spacetime-graph", "figure"),
    Output("minimap-graph", "figure"),
    [
        Input("calamity-dropdown", "value"),
        Input("size-scalar", "value"),
        Input("spin-scalar", "value"),
        Input("overlay-checklist", "value"),
        Input("simulation-interval", "n_intervals")
    ]
)
def update_simulation(calamity, size_scalar, spin_scalar, overlays, n_intervals):
    params = calamity_presets[calamity]

    # Adjust scale and spin dynamically based on scalar values
    params["scale"] *= (1 + size_scalar)
    params["spin"] *= spin_scalar

    overlays = {key: key in overlays for key in
                ["fluid", "expansion", "dark_matter", "energy", "density", "electromagnetic"]}
    x, y, z, curvature, density, energy, dark_energy, dark_matter_guide = generate_data(
        params["mass"], params["spin"], params["resolution"], params["scale"], n_intervals
    )

    # Generate the full simulation and minimap
    full_figure = create_figure(x, y, z, curvature, density, energy, dark_energy, dark_matter_guide, overlays)
    minimap_figure = create_figure(x, y, z, curvature, density, energy, dark_energy, dark_matter_guide, {"fluid": True})

    return full_figure, minimap_figure


@app.callback(
    Output("simulation-interval", "disabled"),
    Input("play-button", "n_clicks")
)
def toggle_playback(n_clicks):
    return n_clicks % 2 == 0  # Toggle between play and pause


@app.callback(
    Output("simulation-interval", "n_intervals"),
    Input("reset-button", "n_clicks")
)
def reset_simulation(n_clicks):
    return 0


if __name__ == "__main__":
    app.run_server(debug=True)

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

# Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Immersive Fluid Dynamic Black Hole Simulation"


# Raphael Equations for Fluid Dynamic Spacetime Mapping
def raphael_equations(x, y, z, t, mass, spin):
    """
    Comprehensive Raphael equations for fluid dynamics of spacetime.
    """
    t = float(t)  # Ensure time is treated as a float
    spin = float(spin)  # Ensure spin is treated as a float

    # Calculate spacetime curvature, density, and energy
    curvature = -np.exp(-(x ** 2 + y ** 2 + z ** 2) / (2 * mass)) * np.cos(spin * t)
    density = np.exp(-(x ** 2 + y ** 2) / (mass * 10)) * np.sin(t)
    energy = np.sin(x * y * z * t) * np.exp(-t / 50)
    dark_energy = (1 / (1 + np.exp(-curvature * density))) * energy
    dark_matter_guide = np.abs(curvature * density) / (1 + np.abs(curvature) + np.abs(density))

    return curvature, density, energy, dark_energy, dark_matter_guide


# Generate Fluid Dynamic Data for Spacetime Simulation
def generate_data(mass, spin, resolution, scale, t):
    """
    Generate data for fluid dynamics in spacetime, including curvature, density, and energy.
    """
    x = np.linspace(-scale, scale, resolution)
    y = np.linspace(-scale, scale, resolution)
    z = np.linspace(-scale, scale, resolution)
    x, y, z = np.meshgrid(x, y, z)
    curvature, density, energy, dark_energy, dark_matter_guide = raphael_equations(x, y, z, t, mass, spin)
    return x, y, z, curvature, density, energy, dark_energy, dark_matter_guide


# Calamity Presets for Interactive Simulation
calamity_presets = {
    "None": {"mass": 50, "spin": 1, "scale": 1e5, "resolution": 30},
    "Black Hole Merge": {"mass": 100, "spin": 5, "scale": 5e5, "resolution": 50},
    "Supernova": {"mass": 500, "spin": 3, "scale": 2e5, "resolution": 40},
    "Quantum Fluctuation": {"mass": 10, "spin": 0.5, "scale": 1e4, "resolution": 20},
}


# Visualization Function for Fluid Dynamics and Full Spectrum Rendering
def create_figure(x, y, z, curvature, density, energy, dark_energy, dark_matter_guide, overlays):
    fig = go.Figure()

    # Fluid Dynamics Mapping for Curvature (Spacetime Bending)
    if overlays.get("fluid"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=curvature.flatten(),
            isomin=-1,
            isomax=1,
            opacity=0.72,
            colorscale="Viridis",  # Color scale for fluid dynamics
            name="Fluid Dynamics"
        ))

    # Visualize Dark Energy Expansion (Red to Yellow color mapping for energy levels)
    if overlays.get("expansion"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=dark_energy.flatten(),
            isomin=0,
            isomax=1,
            opacity=0.7,
            colorscale="Reds",  # Red color for energy expansion
            name="Dark Energy Expansion"
        ))

    # Visualize Dark Matter Guide (Purple gradient based on curvature)
    if overlays.get("dark_matter"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=dark_matter_guide.flatten(),
            isomin=0,
            isomax=0.1,
            opacity=0.5,
            colorscale="Purples",  # Purple gradient for dark matter interactions
            name="Dark Matter Guide"
        ))

    # Energy Visualization Layer (Energy distribution across spacetime)
    if overlays.get("energy"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=energy.flatten(),
            isomin=-1,
            isomax=1,
            opacity=0.4,
            colorscale="Magma",  # Magma color scale for energy distribution
            name="Energy Field"
        ))

    # Spacetime Density Mapping (Blue to Dark Blue)
    if overlays.get("density"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=density.flatten(),
            isomin=0,
            isomax=1,
            opacity=0.72,
            colorscale="Blues",  # Blue for spacetime density
            name="Density Field"
        ))

    # Customize Color Map for Electromagnetic Spectrum: (Red to Yellow)
    if overlays.get("electromagnetic"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=energy.flatten(),
            isomin=0,
            isomax=1,
            opacity=0.6,
            colorscale="YlOrRd",  # Yellow to Red for electromagnetic spectrum
            name="Electromagnetic Spectrum"
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            camera=dict(eye=dict(x=2, y=2, z=2))
        ),
        margin=dict(l=0, r=0, t=50, b=50),
        title="Immersive Hypercomplex Black Hole Simulation"
    )
    return fig


# Layout for Interactive UI
app.layout = html.Div([
    html.H1("Immersive Hypercomplex Black Hole Simulation", style={"textAlign": "center"}),

    # Calamity Preset Dropdown for Selecting Simulation Type
    dbc.Row([
        dbc.Col(html.Label("Calamity Preset"), width=3),
        dbc.Col(dcc.Dropdown(
            id="calamity-dropdown",
            options=[{"label": key, "value": key} for key in calamity_presets.keys()],
            value="None"
        ), width=9)
    ], style={"marginBottom": "20px"}),

    # Scalar Controls for Adjusting Size and Spin Complexity
    html.Label("Calamity Size Scalar"),
    dcc.Slider(
        id="size-scalar",
        min=-1,
        max=1,
        step=0.1,
        value=0,
        marks={-1: "Null Spacetime", 0: "Critical Singularity", 1: "Supermassive Event"}
    ),
    html.Label("Spin/Complexity Scalar"),
    dcc.Slider(
        id="spin-scalar",
        min=0.5,
        max=10,
        step=0.5,
        value=1,
        marks={0.5: "Low Complexity", 10: "High Complexity"}
    ),

    # Overlay Controls for Visualization Layers
    dbc.Checklist(
        options=[
            {"label": "Fluid Dynamics", "value": "fluid"},
            {"label": "Dark Energy Expansion", "value": "expansion"},
            {"label": "Dark Matter Guide", "value": "dark_matter"},
            {"label": "Energy Field", "value": "energy"},
            {"label": "Density Visualization", "value": "density"},
            {"label": "Electromagnetic Spectrum", "value": "electromagnetic"}
        ],
        value=["fluid", "expansion", "dark_matter", "energy", "density", "electromagnetic"],
        id="overlay-checklist",
        inline=True
    ),

    # Graph Component to Render the Simulation
    dcc.Graph(id="spacetime-graph", style={"height": "80vh"}),

    # Playback and Reset Buttons
    html.Div([
        html.Button("Play", id="play-button", n_clicks=0, style={"margin": "10px"}),
        html.Button("Reset", id="reset-button", n_clicks=0, style={"margin": "10px"})
    ]),

    # Interval for Time Steps
    dcc.Interval(id="simulation-interval", interval=100, n_intervals=0, disabled=True)
])


# Callbacks for Real-Time Dynamic Updates
@app.callback(
    Output("spacetime-graph", "figure"),
    [
        Input("calamity-dropdown", "value"),
        Input("size-scalar", "value"),
        Input("spin-scalar", "value"),
        Input("overlay-checklist", "value"),
        Input("simulation-interval", "n_intervals")
    ]
)
def update_simulation(calamity, size_scalar, spin_scalar, overlays, n_intervals):
    params = calamity_presets[calamity]

    # Adjust scale and spin dynamically based on scalar values
    params["scale"] *= (1 + size_scalar)  # Scale adjustment for calamity size
    params["spin"] *= spin_scalar  # Spin adjustment for complexity

    overlays = {key: key in overlays for key in
                ["fluid", "expansion", "dark_matter", "energy", "density", "electromagnetic"]}
    x, y, z, curvature, density, energy, dark_energy, dark_matter_guide = generate_data(
        params["mass"], params["spin"], params["resolution"], params["scale"], n_intervals
    )

    # Apply an offset to the calamity location for dynamic simulation
    calamity_offset = (np.sin(n_intervals * 0.01) * params["scale"],
                       np.cos(n_intervals * 0.01) * params["scale"],
                       np.sin(n_intervals * 0.01) * params["scale"] / 2)

    return create_figure(x, y, z, curvature, density, energy, dark_energy, dark_matter_guide, overlays)


@app.callback(
    Output("simulation-interval", "disabled"),
    Input("play-button", "n_clicks")
)
def toggle_playback(n_clicks):
    return n_clicks % 2 == 0  # Toggle between play and pause


@app.callback(
    Output("simulation-interval", "n_intervals"),
    Input("reset-button", "n_clicks")
)
def reset_simulation(n_clicks):
    return 0


if __name__ == "__main__":
    app.run_server(debug=True)

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go

# Initialize Dash App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "Immersive Black Hole Simulation - Raphael Equations"


# Spacetime Generation Function Using Raphael Equations
def raphael_equations(x, y, z, t, mass, spin):
    """
    Calculates curvature, density, energy, dark matter, and dark energy.
    """
    t = float(t)
    spin = float(spin)
    curvature = -np.exp(-(x ** 2 + y ** 2 + z ** 2) / (2 * mass)) * np.cos(spin * t)
    density = np.exp(-(x ** 2 + y ** 2) / (mass * 10)) * np.sin(t)
    energy = np.sin(x * y * z * t) * np.exp(-t / 50)
    dark_energy = (1 / (1 + np.exp(-curvature * density))) * energy
    dark_matter_guide = np.abs(curvature * density) / (1 + np.abs(curvature) + np.abs(density))
    return curvature, density, energy, dark_energy, dark_matter_guide


# Generate Data Based on the Raphael Equations
def generate_data(mass, spin, resolution, scale, t):
    """Generate 3D data for spacetime (curvature, density, energy, etc.)."""
    x = np.linspace(-scale, scale, resolution)
    y = np.linspace(-scale, scale, resolution)
    z = np.linspace(-scale, scale, resolution)
    x, y, z = np.meshgrid(x, y, z)
    curvature, density, energy, dark_energy, dark_matter_guide = raphael_equations(x, y, z, t, mass, spin)
    return x, y, z, curvature, density, energy, dark_energy, dark_matter_guide


# Define Presets for Calamity (Event) Types (Black Hole Merge, Supernova, etc.)
calamity_presets = {
    "None": {"mass": 50, "spin": 1, "scale": 1e5, "resolution": 30},
    "Black Hole Merge": {"mass": 100, "spin": 5, "scale": 5e5, "resolution": 50},
    "Supernova": {"mass": 500, "spin": 3, "scale": 2e5, "resolution": 40},
    "Quantum Fluctuation": {"mass": 10, "spin": 0.5, "scale": 1e4, "resolution": 20},
}


# Visualization Function for Fluid Dynamics and Full Spectrum Rendering
def create_figure(x, y, z, curvature, density, energy, dark_energy, dark_matter_guide, overlays):
    fig = go.Figure()

    # Fluid Dynamics: Curvature Visualization
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

    # Dark Energy Visualization
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

    # Dark Matter Guide
    if overlays.get("dark_matter"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=dark_matter_guide.flatten(),
            isomin=0,
            isomax=0.1,
            opacity=0.5,
            colorscale="Purples",
            name="Dark Matter Guide"
        ))

    # Energy Field Visualization
    if overlays.get("energy"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=energy.flatten(),
            isomin=-1,
            isomax=1,
            opacity=0.4,
            colorscale="Magma",
            name="Energy Field"
        ))

    # Spacetime Density Visualization
    if overlays.get("density"):
        fig.add_trace(go.Volume(
            x=x.flatten(),
            y=y.flatten(),
            z=z.flatten(),
            value=density.flatten(),
            isomin=0,
            isomax=1,
            opacity=0.72,
            colorscale="Blues",
            name="Density Field"
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            camera=dict(eye=dict(x=2, y=2, z=2))
        ),
        margin=dict(l=0, r=0, t=50, b=50),
        title="Immersive Black Hole Simulation"
    )
    return fig


# Layout for Interactive UI (Minimap, Full View, Controls, and Scalar Adjustments)
app.layout = html.Div([
    html.H1("Immersive Real-Time Black Hole Simulation", style={"textAlign": "center"}),

    # Calamity Preset Dropdown for Selecting Simulation Type
    dbc.Row([
        dbc.Col(html.Label("Calamity Preset"), width=3),
        dbc.Col(dcc.Dropdown(
            id="calamity-dropdown",
            options=[{"label": key, "value": key} for key in calamity_presets.keys()],
            value="None"
        ), width=9)
    ], style={"marginBottom": "20px"}),

    # Minimap Display for Smaller View of Spacetime Simulation
    dcc.Graph(id="minimap-graph", style={"height": "30vh"}),  # Minimap for overview

    # Full Simulation View
    dcc.Graph(id="spacetime-graph", style={"height": "70vh"}),  # Immersive 3D view of spacetime

    # Scalar Controls for Adjusting Size and Spin Complexity
    html.Label("Calamity Size Scalar"),
    dcc.Slider(
        id="size-scalar",
        min=-1,
        max=1,
        step=0.1,
        value=0,
        marks={-1: "Null Spacetime", 0: "Critical Singularity", 1: "Supermassive Event"}
    ),
    html.Label("Spin/Complexity Scalar"),
    dcc.Slider(
        id="spin-scalar",
        min=0.5,
        max=10,
        step=0.5,
        value=1,
        marks={0.5: "Low Complexity", 10: "High Complexity"}
    ),

    # Overlay Controls for Visualization Layers
    dbc.Checklist(
        options=[
            {"label": "Fluid Dynamics", "value": "fluid"},
            {"label": "Dark Energy Expansion", "value": "expansion"},
            {"label": "Dark Matter Guide", "value": "dark_matter"},
            {"label": "Energy Field", "value": "energy"},
            {"label": "Density Visualization", "value": "density"},
            {"label": "Electromagnetic Spectrum", "value": "electromagnetic"}
        ],
        value=["fluid", "expansion", "dark_matter", "energy", "density", "electromagnetic"],
        id="overlay-checklist",
        inline=True
    ),

    # Playback and Reset Buttons
    html.Div([
        html.Button("Play", id="play-button", n_clicks=0, style={"margin": "10px"}),
        html.Button("Reset", id="reset-button", n_clicks=0, style={"margin": "10px"})
    ]),

    # Interval for Time Steps (Simulation Speed Control)
    dcc.Interval(id="simulation-interval", interval=100, n_intervals=0, disabled=True)
])


# Callbacks for Real-Time Dynamic Updates
@app.callback(
    Output("spacetime-graph", "figure"),
    Output("minimap-graph", "figure"),
    [
        Input("calamity-dropdown", "value"),
        Input("size-scalar", "value"),
        Input("spin-scalar", "value"),
        Input("overlay-checklist", "value"),
        Input("simulation-interval", "n_intervals")
    ]
)
def update_simulation(calamity, size_scalar, spin_scalar, overlays, n_intervals):
    params = calamity_presets[calamity]

    # Adjust scale and spin dynamically based on scalar values
    params["scale"] *= (1 + size_scalar)
    params["spin"] *= spin_scalar

    overlays = {key: key in overlays for key in
                ["fluid", "expansion", "dark_matter", "energy", "density", "electromagnetic"]}
    x, y, z, curvature, density, energy, dark_energy, dark_matter_guide = generate_data(
        params["mass"], params["spin"], params["resolution"], params["scale"], n_intervals
    )

    # Generate the full simulation and minimap
    full_figure = create_figure(x, y, z, curvature, density, energy, dark_energy, dark_matter_guide, overlays)
    minimap_figure = create_figure(x, y, z, curvature, density, energy, dark_energy, dark_matter_guide, {"fluid": True})

    return full_figure, minimap_figure


@app.callback(
    Output("simulation-interval", "disabled"),
    Input("play-button", "n_clicks")
)
def toggle_playback(n_clicks):
    return n_clicks % 2 == 0  # Toggle between play and pause


@app.callback(
    Output("simulation-interval", "n_intervals"),
    Input("reset-button", "n_clicks")
)
def reset_simulation(n_clicks):
    return 0


if __name__ == "__main__":
    app.run_server(debug=True)
