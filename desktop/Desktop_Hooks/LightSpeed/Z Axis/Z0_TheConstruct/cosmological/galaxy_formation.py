
# Imports

from dash import Dash
from dash import Input
from dash import Output
from dash import State
from dash import callback_context
from dash import dcc
from dash import html
from scipy.constants import G
from threading import Timer
import numpy
import plotly.graph_objects


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
from scipy.constants import G
from threading import Timer
import numpy
import plotly.graph_objects


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-17 13:43:29

# Source files: 3


import numpy as np
import plotly.graph_objects as go
from scipy.constants import G
from dash import Dash, dcc, html, Input, Output, callback_context, State
from threading import Timer

# Constants
SOLAR_MASS_TO_KG = 1.9885e30
LIGHT_YEAR_TO_METER = 9.461e15
GALAXY_PRESETS = {
    "Milky Way": {"mass": 1.5e12, "radius": 5e4},
    "Andromeda": {"mass": 1.2e12, "radius": 6e4},
    "Triangulum": {"mass": 5e11, "radius": 3e4},
}
TIME_STEPS = 500
FRACTAL_STEPS = 100
ROTATION_SPEED = 0.02

# Initialize Dash App
app = Dash(__name__)

# Fractal Refinement
def fractal_galaxy_refinement(base_positions, scale_factor, iterations):
    refined_positions = base_positions
    for _ in range(iterations):
        noise = np.random.uniform(-scale_factor, scale_factor, refined_positions.shape)
        refined_positions = np.concatenate([refined_positions, refined_positions + noise])
    return refined_positions

# Galaxy Simulation
def simulate_galaxy_formation(time_steps, fractal_iterations, mass, radius):
    time = np.linspace(0, 10e9, time_steps)  # Time in years
    x = np.random.normal(0, radius, size=time_steps)
    y = np.random.normal(0, radius, size=time_steps)
    z = np.random.normal(0, radius / 10, size=time_steps)

    x_refined = fractal_galaxy_refinement(x, radius / 20, fractal_iterations)
    y_refined = fractal_galaxy_refinement(y, radius / 20, fractal_iterations)
    z_refined = fractal_galaxy_refinement(z, radius / 100, fractal_iterations)

    r = np.sqrt(x_refined**2 + y_refined**2)
    density = np.exp(-r / radius)  # Exponential disk model

    baryonic_density = density * 0.2
    dark_matter_density = density * 0.7
    dark_energy_density = density * 0.1

    return {
        "time": time,
        "x": x_refined,
        "y": y_refined,
        "z": z_refined,
        "baryonic_density": baryonic_density,
        "dark_matter_density": dark_matter_density,
        "dark_energy_density": dark_energy_density,
    }

# Raphael Equations
def calculate_raphael_equations(mass, radius, density):
    gravitational_force = (G * mass * density) / (radius**2)
    potential_energy = -G * mass / radius
    return {
        "Gravitational Force": gravitational_force,
        "Potential Energy": potential_energy,
    }

# Full Spectrum HD Render
def full_spectrum_render(data, contributions):
    fig = go.Figure()
    if "Baryonic Matter" in contributions:
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(size=2, color=data["baryonic_density"], colorscale="YlGnBu", opacity=0.8),
            name="Baryonic Matter"
        ))
    if "Dark Matter" in contributions:
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(size=2, color=data["dark_matter_density"], colorscale="Blues", opacity=0.6),
            name="Dark Matter"
        ))
    if "Dark Energy" in contributions:
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(size=2, color=data["dark_energy_density"], colorscale="Purples", opacity=0.5),
            name="Dark Energy"
        ))
    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (light-years)", showbackground=False),
            yaxis=dict(title="Y (light-years)", showbackground=False),
            zaxis=dict(title="Z (light-years)", showbackground=False),
        ),
        paper_bgcolor="black",
        font=dict(color="white"),
        title="HD Galaxy Formation Render"
    )
    return fig
# Dash App Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white"},
    children=[
        html.H1("Galaxy Formation HD Visualization", style={"textAlign": "center"}),

        # Galaxy Preset Selector
        html.Div([
            html.Label("Select Galaxy Preset:"),
            dcc.Dropdown(
                id="preset-selector",
                options=[{"label": k, "value": k} for k in GALAXY_PRESETS.keys()],
                value="Milky Way",
                style={"backgroundColor": "black", "color": "white"}
            ),
        ]),

        # Contribution Toggles
        html.Div([
            html.Label("Toggle Contributions:"),
            dcc.Checklist(
                id="contribution-toggles",
                options=[
                    {"label": "Baryonic Matter", "value": "Baryonic Matter"},
                    {"label": "Dark Matter", "value": "Dark Matter"},
                    {"label": "Dark Energy", "value": "Dark Energy"},
                ],
                value=["Baryonic Matter", "Dark Matter", "Dark Energy"],
                style={"color": "white"}
            ),
        ]),

        # Fractal Refinement Slider
        html.Div([
            html.Label("Fractal Refinement Steps:"),
            dcc.Slider(
                id="fractal-slider",
                min=1,
                max=5,
                step=1,
                value=FRACTAL_STEPS,
                marks={i: str(i) for i in range(1, 6)},
            ),
        ]),

        # Rendered Visualization
        dcc.Graph(id="galaxy-visualization", style={"height": "75vh"}),

        # Raphael Equations Output
        html.Div(
            id="raphael-equations",
            style={
                "color": "white",
                "marginTop": "20px",
                "padding": "10px",
                "border": "1px solid white",
                "backgroundColor": "#111",
            },
        )
    ]
)

# Callbacks for Interactivity
@app.callback(
    [
        Output("galaxy-visualization", "figure"),
        Output("raphael-equations", "children"),
    ],
    [
        Input("preset-selector", "value"),
        Input("contribution-toggles", "value"),
        Input("fractal-slider", "value"),
    ],
)
def update_visualization(selected_preset, contributions, fractal_steps):
    preset = GALAXY_PRESETS[selected_preset]
    mass = preset["mass"] * SOLAR_MASS_TO_KG
    radius = preset["radius"] * LIGHT_YEAR_TO_METER

    data = simulate_galaxy_formation(
        time_steps=TIME_STEPS,
        fractal_iterations=fractal_steps,
        mass=mass,
        radius=radius,
    )
    figure = full_spectrum_render(data, contributions)

    # Raphael Equations
    density_sample = np.mean(data["baryonic_density"])
    raphael = calculate_raphael_equations(mass, radius, density_sample)
    raphael_text = "<br>".join([f"{key}: {value:.2e}" for key, value in raphael.items()])

    return figure, f"Raphael Equations:<br>{raphael_text}"


    # Initialize global variables for live play
    current_angle = 0
    play_active = False

    # Full Spectrum 6D Holographic Renderer
    def holographic_render(data):
        """
        Combines all holographic layers (Baryonic Matter, Dark Matter, Dark Energy, Electromagnetic Spectrum)
        into a unified full-spectrum dynamic visualization.
        """
        fig = go.Figure()

        # Baryonic Matter
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(size=2, color=data["baryonic_density"], colorscale="YlGnBu", opacity=0.8),
            name="Baryonic Matter"
        ))

        # Dark Matter
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(size=2, color=data["dark_matter_density"], colorscale="Greys", opacity=0.6),
            name="Dark Matter"
        ))

        # Electromagnetic Spectrum
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(size=2, color=np.sin(data["x"]), colorscale="Rainbow", opacity=0.5),
            name="Electromagnetic Spectrum"
        ))

        # Dark Energy
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(size=2, color=data["dark_energy_density"], colorscale="Purples", opacity=0.3),
            name="Dark Energy"
        ))

        fig.update_layout(
            scene=dict(
                xaxis=dict(title="X (light-years)", showbackground=False),
                yaxis=dict(title="Y (light-years)", showbackground=False),
                zaxis=dict(title="Z (light-years)", showbackground=False),
            ),
            paper_bgcolor="black",
            font=dict(color="white"),
            title="Live Full-Spectrum Galactic Holograph"
        )
        return fig

    # Timer Callback for Live Spiral Play
    def live_spiral_animation():
        """
        Rotates the galaxy dynamically with live updates, enabling full-spectrum interactive holographs.
        """
        global current_angle, play_active

        if play_active:
            current_angle = (current_angle + ROTATION_SPEED) % (2 * np.pi)

            # Generate the data for current rotation
            preset = GALAXY_PRESETS["Milky Way"]
            mass = preset["mass"] * SOLAR_MASS_TO_KG
            radius = preset["radius"] * LIGHT_YEAR_TO_METER
            data = simulate_galaxy_formation(
                TIME_STEPS, FRACTAL_STEPS, mass, radius
            )

            # Rotate the data
            rotation_matrix = np.array([
                [np.cos(current_angle), -np.sin(current_angle), 0],
                [np.sin(current_angle), np.cos(current_angle), 0],
                [0, 0, 1],
            ])
            positions = np.array([data["x"], data["y"], data["z"]])
            rotated_positions = np.dot(rotation_matrix, positions)

            data["x"], data["y"], data["z"] = rotated_positions[0], rotated_positions[1], rotated_positions[2]

            # Trigger live update for visualization
            app.callback_map["galaxy-visualization.figure"].callback(
                holographic_render(data)
            )

            # Schedule next frame
            Timer(0.05, live_spiral_animation).start()

    # Add UI Enhancements for Live Controls
    app.layout.children.insert(0, html.Div([
        html.Button("Play Spiral", id="play-spiral", n_clicks=0, style={"marginRight": "10px"}),
        html.Button("Pause Spiral", id="pause-spiral", n_clicks=0),
        html.Label("Speed Control:"),
        dcc.Slider(
            id="speed-slider",
            min=1, max=10, step=1, value=5,
            marks={i: f"{i}x" for i in range(1, 11)}
        ),
    ], style={"textAlign": "center", "marginBottom": "20px"}))

    # Callback for Play/Pause and Speed Control
    @app.callback(
        [Output("galaxy-visualization", "figure"),
        Output("hidden-div", "children")],
        [
            Input("play-spiral", "n_clicks"),
            Input("pause-spiral", "n_clicks"),
            Input("speed-slider", "value")
        ],
        allow_duplicate=True, prevent_initial_call=True
    )
    def handle_play_pause(play_clicks, pause_clicks, speed_value):
        """
        Manages play/pause states and updates rotational speed for the live spiral animation.
        """
        global play_active, ROTATION_SPEED

        ctx = callback_context.triggered[0]["prop_id"].split(".")[0]
        if ctx == "play-spiral":
            play_active = True
            ROTATION_SPEED = speed_value * 2
            live_spiral_animation()
            return [holographic_render(data), 'play']
        elif ctx == "pause-spiral":
            play_active = False
            return [holographic_render(data), 'play']

        # Generate fallback visualization
        preset = GALAXY_PRESETS["Milky Way"]
        mass = preset["mass"] * SOLAR_MASS_TO_KG
        radius = preset["radius"] * LIGHT_YEAR_TO_METER
        data = simulate_galaxy_formation(
            TIME_STEPS, FRACTAL_STEPS, mass, radius
        )
        return [holographic_render(data), 'pause']

# Final Block: Enhanced Galaxy Simulation with Holographic Layers and Live Spiral Animation
if __name__ == "__main__":
    app.run_server(debug=True)
