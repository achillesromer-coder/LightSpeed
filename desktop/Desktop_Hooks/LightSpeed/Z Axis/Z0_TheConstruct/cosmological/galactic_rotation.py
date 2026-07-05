
# Imports

from collections import Counter
from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import callback_context
from dash import dcc
from dash import html
from dash.dependencies import ALL
from scipy.constants import G
from scipy.constants import pi
from threading import Timer
import dash
import logging
import numpy
import plotly.graph_objects


# ===== CONSOLIDATED FROM 10 FILES =====

# Merged on: 2025-11-21 17:46:24

# Source files: 10



# Imports

from collections import Counter
from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import callback_context
from dash import dcc
from dash import html
from dash.dependencies import ALL
from scipy.constants import G
from scipy.constants import pi
from threading import Timer
import dash
import logging
import numpy
import plotly.graph_objects


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-17 13:43:29

# Source files: 3


import dash
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback_context
from scipy.constants import G, pi
from threading import Timer

# Constants
SOLAR_MASS_TO_KG = 1.989e30
LIGHT_YEAR_TO_M = 9.461e15
ROTATION_PERIOD = 60  # Seconds for a full galactic rotation
ROTATION_SPEED = (2 * pi) / ROTATION_PERIOD  # Radians per second
NUM_POINTS = 5000  # High-resolution for HD rendering

# Default Parameters
GALAXY_PRESETS = {
    "Milky Way": {"mass": 1.5e12, "radius": 5e4, "halo_mass": 5e12, "halo_radius": 1.5e5},
    "Andromeda": {"mass": 1.2e12, "radius": 6e4, "halo_mass": 4e12, "halo_radius": 1.8e5},
    "Triangulum": {"mass": 5e11, "radius": 3e4, "halo_mass": 2e12, "halo_radius": 1.2e5},
}

# Fractal refinement for high-resolution data
def fractal_refinement(base_positions, scale_factor, iterations):
    refined_positions = base_positions
    for _ in range(iterations):
        noise = np.random.uniform(-scale_factor, scale_factor, refined_positions.shape)
        refined_positions = np.concatenate([refined_positions, refined_positions + noise])
    return refined_positions

# Galactic simulation: density and velocity profiles
def simulate_galactic_data(params, fractal_iterations=3):
    radii = np.linspace(0.1, params["radius"], NUM_POINTS)
    mass_kg = params["mass"] * SOLAR_MASS_TO_KG
    halo_mass_kg = params["halo_mass"] * SOLAR_MASS_TO_KG
    radius_m = radii * LIGHT_YEAR_TO_M
    halo_radius_m = params["halo_radius"] * LIGHT_YEAR_TO_M

    # Velocity profiles
    v_baryonic = np.sqrt(G * mass_kg / radius_m)
    v_halo = np.sqrt((G * halo_mass_kg * radius_m**2) / (halo_radius_m**3))
    v_total = np.sqrt(v_baryonic**2 + v_halo**2)

    # Holographic density data
    x = fractal_refinement(np.random.uniform(-params["radius"], params["radius"], NUM_POINTS),
                           params["radius"] / 10, fractal_iterations)
    y = fractal_refinement(np.random.uniform(-params["radius"], params["radius"], NUM_POINTS),
                           params["radius"] / 10, fractal_iterations)
    z = fractal_refinement(np.random.uniform(-params["radius"] / 20, params["radius"] / 20, NUM_POINTS),
                           params["radius"] / 50, fractal_iterations)

    baryonic_density = np.exp(-np.sqrt(x**2 + y**2 + z**2) / (params["radius"] / 3))
    dark_matter_density = np.exp(-np.sqrt(x**2 + y**2 + z**2) / (params["radius"] / 2))
    dark_energy_density = np.abs(np.cos(np.sqrt(x**2 + y**2 + z**2) / (params["radius"] / 5)))

    return {
        "radii": radii,
        "v_baryonic": v_baryonic / 1e3,  # Convert to km/s
        "v_halo": v_halo / 1e3,  # Convert to km/s
        "v_total": v_total / 1e3,  # Convert to km/s
        "x": x, "y": y, "z": z,
        "baryonic_density": baryonic_density,
        "dark_matter_density": dark_matter_density,
        "dark_energy_density": dark_energy_density,
    }
# Plot rotation curve
def plot_rotation_curve(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["radii"], y=data["v_baryonic"], mode="lines",
                             name="Baryonic Matter", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=data["radii"], y=data["v_halo"], mode="lines",
                             name="Dark Matter Halo", line=dict(color="red", dash="dash")))
    fig.add_trace(go.Scatter(x=data["radii"], y=data["v_total"], mode="lines",
                             name="Total Velocity", line=dict(color="green")))
    fig.update_layout(
        title="Galactic Rotation Curve",
        xaxis_title="Radius (light-years)",
        yaxis_title="Velocity (km/s)",
        template="plotly_dark"
    )
    return fig

# Plot holographic galaxy
def plot_holographic_galaxy(data):
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=data["x"], y=data["y"], z=data["z"],
        mode="markers",
        marker=dict(size=3, color=data["baryonic_density"], colorscale="YlGnBu", opacity=0.7),
        name="Baryonic Matter"
    ))
    fig.add_trace(go.Scatter3d(
        x=data["x"], y=data["y"], z=data["z"],
        mode="markers",
        marker=dict(size=3, color=data["dark_matter_density"], colorscale="Blues", opacity=0.5),
        name="Dark Matter Halo"
    ))
    fig.add_trace(go.Scatter3d(
        x=data["x"], y=data["y"], z=data["z"],
        mode="markers",
        marker=dict(size=3, color=data["dark_energy_density"], colorscale="Purples", opacity=0.3),
        name="Dark Energy Field"
    ))
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (light-years)"),
            yaxis=dict(title="Y (light-years)"),
            zaxis=dict(title="Z (light-years)"),
        ),
        title="6D Galactic Holographic Visualization",
        template="plotly_dark"
    )
    return fig
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)

# Dash App Setup
app = Dash(__name__)
app.layout = html.Div(
    style={"backgroundColor": "#111", "color": "#FFF", "fontFamily": "Arial"},
    children=[
        html.H1("Interactive Galactic Rotation Simulation", style={"textAlign": "center"}),

        # Preset Selector
        html.Div([
            html.Label("Select Galaxy Preset:"),
            dcc.Dropdown(
                id="preset-selector",
                options=[{"label": k, "value": k} for k in GALAXY_PRESETS.keys()],
                value="Milky Way",
                style={"backgroundColor": "#222", "color": "#FFF"},
            ),
        ], style={"margin": "20px"}),

        # Custom Parameter Sliders
        html.Div([
            html.Label("Galaxy Mass (Solar Masses):"),
            dcc.Slider(
                id="mass-slider",
                min=1e12, max=2e12, step=1e11, value=1.5e12,
                marks={int(i): f"{i/1e12:.1f}T" for i in range(int(1e12), int(2e12 + 1), int(1e11))}
            ),
            html.Label("Galaxy Radius (Light-years):"),
            dcc.Slider(
                id="radius-slider",
                min=1e4, max=1e5, step=1e3, value=5e4,
                marks={int(i): f"{i/1e3:.0f}k" for i in range(int(1e4), int(1e5 + 1), int(1e4))}
            ),
        ], style={"margin": "20px"}),

        # Contribution Toggles
        html.Div([
            html.Label("Toggle Contributions:"),
            dcc.Checklist(
                id="contribution-toggles",
                options=[
                    {"label": "Baryonic Matter", "value": "baryonic_density"},
                    {"label": "Dark Matter", "value": "dark_matter_density"},
                    {"label": "Dark Energy", "value": "dark_energy_density"},
                ],
                value=["baryonic_density", "dark_matter_density", "dark_energy_density"],
                style={"color": "#FFF"},
            ),
        ], style={"margin": "20px"}),

        # Graphs for Rotation Curve and Holographic Galaxy
        html.Div([
            html.Label("Rotation Curve:"),
            dcc.Graph(id="rotation-curve", style={"height": "40vh"}),
            html.Label("Holographic Galaxy:"),
            dcc.Graph(id="holographic-galaxy", style={"height": "60vh"}),
        ]),

        # Play/Pause Controls
        html.Div([
            html.Button("Play Rotation", id="play-button", n_clicks=0, style={"marginRight": "10px"}),
            html.Button("Pause Rotation", id="pause-button", n_clicks=0),
            html.Label("Rotation Speed:"),
            dcc.Slider(
                id="speed-slider",
                min=0.01, max=0.1, step=0.01, value=ROTATION_SPEED,
                marks={i: f"{i:.2f}" for i in np.linspace(0.01, 0.1, 10)}
            ),
        ], style={"textAlign": "center", "margin": "20px"}),
    ]
)
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)

# Global Variables for Rotation State
play_active = False
rotation_angle = 0

# Callback for Updating Graphs
@app.callback(
    [Output("rotation-curve", "figure"), Output("holographic-galaxy", "figure")],
    [Input("preset-selector", "value"),
     Input("mass-slider", "value"),
     Input("radius-slider", "value"),
     Input("contribution-toggles", "value"),
     Input("speed-slider", "value"),
     Input("play-button", "n_clicks"),
     Input("pause-button", "n_clicks")]
)
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)
def update_visualizations(preset, mass, radius, contributions, speed, play_clicks, pause_clicks):
    global play_active, rotation_angle, ROTATION_SPEED

    # Toggle play state
    ctx = callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "play-button":
        play_active = True
        ROTATION_SPEED = speed
    elif ctx == "pause-button":
        play_active = False

    # Use preset or custom values
    params = GALAXY_PRESETS.get(preset, {"mass": mass, "radius": radius, "halo_mass": 5e12, "halo_radius": 1.5e5})
    params.update({"mass": mass, "radius": radius})

    # Simulate data
    data = simulate_galactic_data(params)

    # Apply rotation
    if play_active:
        rotation_angle = (rotation_angle + ROTATION_SPEED) % (2 * pi)
        rotation_matrix = np.array([
            [np.cos(rotation_angle), -np.sin(rotation_angle), 0],
            [np.sin(rotation_angle), np.cos(rotation_angle), 0],
            [0, 0, 1]
        ])
        positions = np.dot(rotation_matrix, np.array([data["x"], data["y"], data["z"]]))
        data["x"], data["y"], data["z"] = positions[0], positions[1], positions[2]

    # Plot graphs
    rotation_curve_fig = plot_rotation_curve(data)
    holograph_fig = plot_holographic_galaxy({k: data[k] for k in contributions})

    return rotation_curve_fig, holograph_fig

# Timer for Real-Time Updates
def rotation_loop():
    """
    Continuously updates the galaxy's rotation and triggers a visualization update.
    """
    global play_active, rotation_angle, ROTATION_SPEED

    if play_active:
        # Increment rotation angle
        rotation_angle = (rotation_angle + ROTATION_SPEED) % (2 * np.pi)

        # Trigger Dash callback manually for smooth updates
        ctx_id = "holographic-galaxy.figure"
        app.callback_map[ctx_id].callback(None)

        # Schedule the next frame update
        Timer(0.05, rotation_loop).start()

# Callback for Handling Rotation State
@app.callback(
    Output("holographic-galaxy", "figure"),
    [Input("play-button", "n_clicks"), Input("pause-button", "n_clicks")],
    [State("preset-selector", "value"),
     State("mass-slider", "value"),
     State("radius-slider", "value"),
     State("contribution-toggles", "value")]
)
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)

def manage_rotation(play_clicks, pause_clicks, preset, mass, radius, contributions):
    global play_active

    # Determine the trigger
    ctx = callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "play-button":
        play_active = True
        rotation_loop()  # Start the rotation loop
    elif ctx == "pause-button":
        play_active = False  # Stop the rotation loop

    # Generate data for the holographic galaxy
    params = GALAXY_PRESETS.get(preset, {"mass": mass, "radius": radius})
    params.update({"mass": mass, "radius": radius})

    data = simulate_galactic_data(params)
    holograph_fig = plot_holographic_galaxy({k: data[k] for k in contributions})

    return holograph_fig

# Enhanced Error Handling
def simulate_galactic_data_safe(params):
    """
    Wrapper for `simulate_galactic_data` with error handling for invalid inputs or unexpected shapes.
    """
    try:
        # Validate parameters
        if params["mass"] <= 0 or params["radius"] <= 0:
            raise ValueError("Mass and radius must be positive.")

        # Generate data
        return simulate_galactic_data(params)
    except Exception as e:
        print(f"Error during galactic data simulation: {e}")
        return generate_fallback_visualization()

def plot_holographic_galaxy_safe(data):
    """
    Wrapper for `plot_holographic_galaxy` to handle missing or invalid data.
    """
    try:
        return plot_holographic_galaxy(data)
    except Exception as e:
        print(f"Error during holographic galaxy plotting: {e}")
        return generate_fallback_visualization()

# Fallback Visualization for Missing Data
def generate_fallback_visualization():
    """
    Creates a fallback visualization to display when simulation data is invalid.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter3d(
            x=[0], y=[0], z=[0],
            mode="markers",
            marker=dict(size=10, color="red", opacity=1.0),
            name="Error Point"
        )
    )
    fig.update_layout(
        title="Fallback Visualization",
        scene=dict(
            xaxis=dict(title="X", showgrid=False),
            yaxis=dict(title="Y", showgrid=False),
            zaxis=dict(title="Z", showgrid=False)
        ),
        paper_bgcolor="black",
        font=dict(color="white")
    )
    return fig


# Add UI Controls for Contributions and Presets
app.layout.children.insert(1, html.Div([
    html.Label("Select Contributions:"),
    dcc.Checklist(
        id="contribution-toggles",
        options=[
            {"label": "Baryonic Matter", "value": "baryonic_density"},
            {"label": "Dark Matter", "value": "dark_matter_density"},
            {"label": "Dark Energy", "value": "dark_energy_density"}
        ],
        value=["baryonic_density", "dark_matter_density", "dark_energy_density"],
        inline=True,
        style={"color": "white"}
    ),
    html.Label("Select Galaxy Preset:"),
    dcc.Dropdown(
        id="preset-selector",
        options=[{"label": k, "value": k} for k in GALAXY_PRESETS.keys()],
        value="Milky Way",
        style={"backgroundColor": "black", "color": "white"}
    )
], style={"margin": "20px"}))

# Callback for Contribution Toggles
@app.callback(
    Output("holographic-galaxy", "figure"),
    [
        Input("contribution-toggles", "value"),
        Input("preset-selector", "value"),
        Input("mass-slider", "value"),
        Input("radius-slider", "value"),
        Input("play-button", "n_clicks"),
        Input("pause-button", "n_clicks")
    ]
)
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)
def update_holographic_visualization(contributions, preset, mass, radius, play_clicks, pause_clicks):
    global play_active, rotation_angle

    # Update parameters based on the preset or user-defined values
    params = GALAXY_PRESETS.get(preset, {"mass": mass, "radius": radius})
    params.update({"mass": mass, "radius": radius})

    # Generate simulation data
    data = simulate_galactic_data_safe(params)

    # Apply rotation if active
    if play_active:
        rotation_angle = (rotation_angle + ROTATION_SPEED) % (2 * np.pi)
        data = rotate_galaxy(data, rotation_angle)

    # Generate visualization with selected contributions
    holograph_fig = plot_holographic_galaxy_safe({k: data[k] for k in contributions})

    return holograph_fig

# Advanced 3D Holographic Visualization
def plot_holographic_galaxy_advanced(data, contributions):
    """
    Creates an advanced 3D holographic visualization with toggled contributions and color spectrum.
    """
    fig = go.Figure()

    # Add each contribution to the holograph
    for contribution in contributions:
        fig.add_trace(
            go.Scatter3d(
                x=data["x"],
                y=data["y"],
                z=data["z"],
                mode="markers",
                marker=dict(
                    size=2,
                    color=data[contribution],
                    colorscale="Viridis" if contribution == "baryonic_density" else "Reds",
                    opacity=0.7 if contribution == "baryonic_density" else 0.5
                ),
                name=contribution.replace("_", " ").capitalize()
            )
        )

    # Update layout for 3D holograph
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (light-years)", showbackground=True, backgroundcolor="black"),
            yaxis=dict(title="Y (light-years)", showbackground=True, backgroundcolor="black"),
            zaxis=dict(title="Z (light-years)", showbackground=True, backgroundcolor="black")
        ),
        paper_bgcolor="black",
        font=dict(color="white"),
        title="Advanced Galactic Holographic Visualization"
    )
    return fig

# Enhanced Callback for Advanced Visualization
@app.callback(
    [
        Output("rotation-curve", "figure"),
        Output("holographic-galaxy", "figure")
    ],
    [
        Input("mass-slider", "value"),
        Input("radius-slider", "value"),
        Input("play-button", "n_clicks"),
        Input("pause-button", "n_clicks"),
        Input("contribution-toggles", "value")
    ]
)
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)
def update_visualization_advanced(mass, radius, play_clicks, pause_clicks, contributions):
    global play_active, rotation_angle

    # Determine play state
    ctx = callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "play-button":
        play_active = True
    elif ctx == "pause-button":
        play_active = False

    # Update parameters and generate data
    params = {"mass": mass, "radius": radius, "num_points": DEFAULT_PARAMS["num_points"]}
    data = simulate_galactic_data_safe(params)

    # Apply rotation if active
    if play_active:
        rotation_angle = (rotation_angle + ROTATION_SPEED) % (2 * np.pi)
        data = rotate_galaxy(data, rotation_angle)

    # Generate plots
    rotation_curve_fig = plot_rotation_curve(data)
    holograph_fig = plot_holographic_galaxy_advanced(data, contributions)

    return rotation_curve_fig, holograph_fig

# Add Time Control Slider and Spectrum Range
app.layout.children.append(html.Div([
    html.Label("Time Control (Galactic Years):"),
    dcc.Slider(
        id="time-slider",
        min=0,
        max=10e9,
        step=1e8,
        value=5e9,
        marks={i: f"{int(i/1e9)} Gyr" for i in range(0, int(10e9+1), int(1e9))}
    ),
    html.Label("Spectrum Range:"),
    dcc.RangeSlider(
        id="spectrum-slider",
        min=0.1,
        max=1.0,
        step=0.1,
        value=[0.3, 0.7],
        marks={i: f"{i:.1f}" for i in np.arange(0.1, 1.1, 0.1)}
    )
], style={"margin": "20px"}))

# Callback for Spectrum and Time Updates
@app.callback(
    [
        Output("holographic-galaxy", "figure"),
        Output("rotation-curve", "figure")
    ],
    [
        Input("time-slider", "value"),
        Input("spectrum-slider", "value"),
        Input("contribution-toggles", "value"),
        Input("play-button", "n_clicks"),
        Input("pause-button", "n_clicks")
    ]
)
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)
def update_spectrum_and_time(time, spectrum_range, contributions, play_clicks, pause_clicks):
    global play_active, rotation_angle

    # Determine play state
    ctx = callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "play-button":
        play_active = True
    elif ctx == "pause-button":
        play_active = False

    # Generate data with time-dependent parameters
    params = {
        "mass": DEFAULT_PARAMS["mass"],
        "radius": DEFAULT_PARAMS["radius"],
        "halo_mass": DEFAULT_PARAMS["halo_mass"],
        "halo_radius": DEFAULT_PARAMS["halo_radius"],
        "num_points": DEFAULT_PARAMS["num_points"]
    }
    data = simulate_galactic_data_safe(params, time)

    # Apply spectrum range filters
    filtered_data = {
        key: np.clip(data[key], spectrum_range[0], spectrum_range[1])
        for key in contributions
    }
    filtered_data.update({"x": data["x"], "y": data["y"], "z": data["z"]})

    # Apply rotation if active
    if play_active:
        rotation_angle = (rotation_angle + ROTATION_SPEED) % (2 * np.pi)
        filtered_data = rotate_galaxy(filtered_data, rotation_angle)

    # Generate holographic visualization and rotation curve
    holograph_fig = plot_holographic_galaxy_advanced(filtered_data, contributions)
    rotation_curve_fig = plot_rotation_curve(data)

    return holograph_fig, rotation_curve_fig

# Add Error Handling and Fallback Visualization
def generate_fallback_figure():
    """
    Generates a fallback figure to display in case of errors.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0],
        mode="markers",
        marker=dict(size=10, color="red", opacity=1.0),
        name="Fallback Point"
    ))
    fig.update_layout(
        title="Error: Visualization Not Available",
        scene=dict(
            xaxis=dict(title="X", showgrid=False),
            yaxis=dict(title="Y", showgrid=False),
            zaxis=dict(title="Z", showgrid=False)
        ),
        paper_bgcolor="black",
        font=dict(color="white")
    )
    return fig

@app.callback(
    [
        Output("holographic-galaxy", "figure"),
        Output("rotation-curve", "figure")
    ],
    [
        Input("contribution-toggles", "value"),
        Input("time-slider", "value"),
        Input("spectrum-slider", "value")
    ]
)
def update_visualizations_with_error_handling(contributions, time, spectrum_range):
    try:
        # Simulate galaxy data with provided parameters
        params = {
            "mass": DEFAULT_PARAMS["mass"],
            "radius": DEFAULT_PARAMS["radius"],
            "halo_mass": DEFAULT_PARAMS["halo_mass"],
            "halo_radius": DEFAULT_PARAMS["halo_radius"],
            "num_points": DEFAULT_PARAMS["num_points"]
        }
        data = simulate_galactic_data_safe(params, time)

        # Filter data by spectrum range
        filtered_data = {
            key: np.clip(data[key], spectrum_range[0], spectrum_range[1])
            for key in contributions
        }
        filtered_data.update({"x": data["x"], "y": data["y"], "z": data["z"]})

        # Generate visualizations
        holograph_fig = plot_holographic_galaxy_advanced(filtered_data, contributions)
        rotation_curve_fig = plot_rotation_curve(data)

        return holograph_fig, rotation_curve_fig

    except Exception as e:
        print(f"Error in visualization update: {e}")
        return generate_fallback_figure(), generate_fallback_figure()
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)
# Advanced Holographic Rendering
def plot_holographic_galaxy_advanced(data, contributions):
    """
    Generates an advanced holographic galaxy visualization with multiple data layers.
    """
    fig = go.Figure()

    # Baryonic Matter
    if "Baryonic Matter" in contributions:
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(
                size=3,
                color=data["baryonic_density"],
                colorscale="YlGnBu",
                opacity=0.7
            ),
            name="Baryonic Matter"
        ))

    # Dark Matter
    if "Dark Matter" in contributions:
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(
                size=3,
                color=data["dark_matter_density"],
                colorscale="Purples",
                opacity=0.5
            ),
            name="Dark Matter"
        ))

    # Dark Energy
    if "Dark Energy" in contributions:
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(
                size=3,
                color=data["dark_energy_density"],
                colorscale="Reds",
                opacity=0.3
            ),
            name="Dark Energy"
        ))

    # Update Layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (light-years)", showgrid=False, backgroundcolor="black"),
            yaxis=dict(title="Y (light-years)", showgrid=False, backgroundcolor="black"),
            zaxis=dict(title="Z (light-years)", showgrid=False, backgroundcolor="black")
        ),
        paper_bgcolor="black",
        font=dict(color="white"),
        title="6D Holographic Galaxy Visualization"
    )
    return fig

# Add Customization Controls
app.layout.children.append(html.Div([
    html.Label("Customize Galaxy Parameters:"),
    html.Label("Galaxy Mass (Solar Masses):"),
    dcc.Slider(
        id="custom-mass-slider",
        min=1e12, max=5e12, step=1e11, value=1.5e12,
        marks={int(i): f"{i/1e12:.1f}T" for i in range(int(1e12), int(5e12 + 1), int(1e11))}
    ),
    html.Label("Galaxy Radius (Light-years):"),
    dcc.Slider(
        id="custom-radius-slider",
        min=1e4, max=1e5, step=1e3, value=5e4,
        marks={int(i): f"{i/1e3:.0f}k" for i in range(int(1e4), int(1e5 + 1), int(1e4))}
    ),
    html.Label("Density Multiplier:"),
    dcc.Slider(
        id="density-multiplier-slider",
        min=0.1, max=2.0, step=0.1, value=1.0,
        marks={i: f"{i:.1f}" for i in np.arange(0.1, 2.1, 0.2)}
    )
], style={"margin": "20px"}))

# Callback for Customization Updates
@app.callback(
    [
        Output("holographic-galaxy", "figure"),
        Output("rotation-curve", "figure")
    ],
    [
        Input("custom-mass-slider", "value"),
        Input("custom-radius-slider", "value"),
        Input("density-multiplier-slider", "value")
    ]
)
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)

def update_custom_parameters(mass, radius, density_multiplier):
    # Simulate galaxy with custom parameters
    params = {
        "mass": mass,
        "radius": radius,
        "halo_mass": DEFAULT_PARAMS["halo_mass"],
        "halo_radius": DEFAULT_PARAMS["halo_radius"],
        "num_points": DEFAULT_PARAMS["num_points"]
    }
    data = simulate_galactic_data_safe(params)
    data["baryonic_density"] *= density_multiplier
    data["dark_matter_density"] *= density_multiplier
    data["dark_energy_density"] *= density_multiplier

    # Generate visualizations
    holograph_fig = plot_holographic_galaxy_advanced(data, ["Baryonic Matter", "Dark Matter", "Dark Energy"])
    rotation_curve_fig = plot_rotation_curve(data)

    return holograph_fig, rotation_curve_fig

# Timer and Real-Time Rotation
rotation_angle = 0.0
play_active = False

def rotate_galaxy(data, angle):
    """
    Rotates the galaxy visualization in 3D.
    """
    rotation_matrix = np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
    ])

    positions = np.array([data["x"], data["y"], data["z"]])
    rotated_positions = np.dot(rotation_matrix, positions)

    return {
        "x": rotated_positions[0],
        "y": rotated_positions[1],
        "z": rotated_positions[2],
        "baryonic_density": data["baryonic_density"],
        "dark_matter_density": data["dark_matter_density"],
        "dark_energy_density": data["dark_energy_density"],
    }

# Timer Function for Real-Time Playback
def playback_loop():
    """
    Continuously updates rotation during playback.
    """
    global rotation_angle, play_active
    if play_active:
        rotation_angle = (rotation_angle + ROTATION_SPEED) % (2 * np.pi)
        app.callback_map["holographic-galaxy.figure"].callback(None)
        Timer(0.05, playback_loop).start()

# Play/Pause Callbacks
@app.callback(
    Output("play-button", "children"),
    [Input("play-button", "n_clicks"), Input("pause-button", "n_clicks")]
)
def toggle_play_pause(play_clicks, pause_clicks):
    global play_active
    ctx = callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "play-button":
        play_active = True
        playback_loop()
        return "Pause Rotation"
    elif ctx == "pause-button":
        play_active = False
        return "Play Rotation"
    return "Play Rotation"

# Unified Data Management
def simulate_galactic_data_safe(params):
    """
    Wrapper for data simulation with error handling.
    """
    try:
        radii = np.linspace(0.1, params["radius"], params["num_points"])
        v_baryonic, v_halo, v_total = calculate_velocity_profile(
            radii, params["mass"], params["halo_mass"], params["halo_radius"]
        )

        x, y, z, baryonic_density, dark_matter_density, dark_energy_density = generate_holographic_data(
            params["num_points"], params["radius"]
        )

        return {
            "radii": radii,
            "v_baryonic": v_baryonic,
            "v_halo": v_halo,
            "v_total": v_total,
            "x": x,
            "y": y,
            "z": z,
            "baryonic_density": baryonic_density,
            "dark_matter_density": dark_matter_density,
            "dark_energy_density": dark_energy_density
        }
    except Exception as e:
        print(f"Error during data simulation: {e}")
        return None

# Final Integration with Error Handling
@app.callback(
    [
        Output("rotation-curve", "figure"),
        Output("holographic-galaxy", "figure")
    ],
    [
        Input("mass-slider", "value"),
        Input("radius-slider", "value"),
        Input("play-button", "n_clicks"),
        Input("pause-button", "n_clicks")
    ]
)
# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)

def update_visualizations_safe(mass, radius, play_clicks, pause_clicks):
    global rotation_angle, play_active

    try:
        # Toggle playback state
        ctx = callback_context.triggered[0]["prop_id"].split(".")[0]
        if ctx == "play-button":
            play_active = True
        elif ctx == "pause-button":
            play_active = False

        # Simulate data
        params = DEFAULT_PARAMS.copy()
        params.update({"mass": mass, "radius": radius})
        data = simulate_galactic_data_safe(params)
        if data is None:
            raise ValueError("Failed to simulate galaxy data.")

        # Rotate data
        if play_active:
            rotated_data = rotate_galaxy(data, rotation_angle)
        else:
            rotated_data = data

        # Generate visualizations
        rotation_curve_fig = plot_rotation_curve(data)
        holographic_fig = plot_holographic_galaxy_advanced(rotated_data, ["Baryonic Matter", "Dark Matter", "Dark Energy"])

        return rotation_curve_fig, holographic_fig

    except Exception as e:
        print(f"Error during visualization update: {e}")
        return go.Figure(), go.Figure()

# Debugging Logs
import logging
logging.basicConfig(level=logging.INFO)
logging.info("Galactic Rotation Simulation Initialized")

# Error Handling for Duplicate Component IDs
def validate_layout(layout):
    """
    Validates the layout for duplicate component IDs.
    """
    from collections import Counter

    def extract_ids(children):
        ids = []
        for child in children:
            if isinstance(child, dict):
                if 'id' in child:
                    ids.append(child['id'])
                if 'children' in child:
                    ids.extend(extract_ids(child['children']))
            elif hasattr(child, 'id'):
                ids.append(child.id)
            if hasattr(child, 'children'):
                ids.extend(extract_ids(child.children))
        return ids

    ids = extract_ids(layout.children)
    duplicates = [item for item, count in Counter(ids).items() if count > 1]

    if duplicates:
        raise dash.exceptions.DuplicateIdError(
            f"Duplicate component IDs found: {duplicates}"
        )

# Validate Layout Before Running the App
try:
    validate_layout(app.layout)
except dash.exceptions.DuplicateIdError as e:
    print(f"Error: {e}")
    exit(1)

from collections import Counter
from dash.dependencies import ALL

def ensure_unique_ids(component, id_counter=None):
    """
    Recursively ensures unique IDs in callback outputs or nested components.
    """
    if id_counter is None:
        id_counter = Counter()

    if hasattr(component, 'id'):
        id_counter[component.id] += 1
        if id_counter[component.id] > 1:
            component.id += f"-{id_counter[component.id] - 1}"

    if hasattr(component, 'children'):
        if isinstance(component.children, list):
            component.children = [ensure_unique_ids(child, id_counter) for child in component.children]
        else:
            component.children = ensure_unique_ids(component.children, id_counter)

    return component

# Apply this function wherever IDs are dynamically generated
def resolve_duplicate_ids(layout):
    """
    Recursively resolves duplicate IDs in a Dash layout by renaming duplicates.
    """
    from collections import Counter

    id_counter = Counter()

    def modify_component(component):
        if isinstance(component, dict) and "id" in component:
            id_counter[component["id"]] += 1
            if id_counter[component["id"]] > 1:
                # Rename duplicate ID
                component["id"] += f"-{id_counter[component['id']] - 1}"
        if isinstance(component, dict) and "children" in component:
            component["children"] = modify_component(component["children"])
        elif isinstance(component, list):
            component = [modify_component(child) for child in component]
        return component

    layout.children = modify_component(layout.children)

# Apply the duplicate ID resolver to the layout
resolve_duplicate_ids(app.layout)

# Apply the Patch to Resolve Duplicate IDs
print("Before resolving IDs:")
print(app.layout)

resolve_duplicate_ids(app.layout)

print("After resolving IDs:")
print(app.layout)

from collections import Counter

def resolve_duplicate_ids(layout):
    """
    Recursively traverses the layout and assigns unique IDs to components with duplicate IDs.
    """
    id_counter = Counter()

    def traverse_layout(component):
        if isinstance(component, list):  # Traverse lists
            return [traverse_layout(child) for child in component]
        elif hasattr(component, "children"):  # Traverse components with children
            component.children = traverse_layout(component.children)
            return component
        elif hasattr(component, "id") and component.id:  # Check if the component has an ID
            id_counter[component.id] += 1
            if id_counter[component.id] > 1:  # If duplicate ID, append a suffix
                component.id = f"{component.id}-{id_counter[component.id]}"
            return component
        return component  # Return component as-is if it has no ID or children

    return traverse_layout(layout)

# Resolve duplicate IDs in the layout
app.layout = resolve_duplicate_ids(app.layout)

# Resolve duplicate IDs in the layout
app.layout = resolve_duplicate_ids(app.layout)

# Run the App
if __name__ == "__main__":
    app.run_server(debug=True)
