"""
Cosmic Phenomena Package: Unified access to cosmic simulations with a grid-free holographic render.
"""

from dash import Dash, dcc, html, Input, Output
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from .big_bang_simulation import generate_big_bang_simulation, plot_big_bang
from .dark_energy_simulation import simulate_dark_energy, plot_dark_energy
from .cosmic_microwave_background import generate_cmb_map, plot_cmb

# Initialize Dash App
app = Dash(__name__)

# Phenomena Mapping
PHENOMENA = {
    "Big Bang": {"generator": generate_big_bang_simulation, "plotter": plot_big_bang},
    "Dark Energy": {"generator": simulate_dark_energy, "plotter": plot_dark_energy},
    "Cosmic Microwave Background": {"generator": generate_cmb_map, "plotter": plot_cmb},
}

# Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "fontFamily": "Arial"},
    children=[
        html.H1("Cosmic Phenomena Simulations", style={"textAlign": "center"}),

        # Phenomenon Selection Menu
        html.Div([
            html.Label("Select Phenomenon:"),
            dcc.Dropdown(
                id="phenomenon-selector",
                options=[{"label": name, "value": name} for name in PHENOMENA.keys()],
                value="Big Bang",
                style={"backgroundColor": "black", "color": "white"}
            ),
        ], style={"margin": "20px"}),

        # Fractal Refinement Slider
        html.Div([
            html.Label("Fractal Refinement Steps:"),
            dcc.Slider(
                id="fractal-slider",
                min=1,
                max=5,
                step=1,
                value=3,
                marks={i: str(i) for i in range(1, 6)},
            ),
        ], style={"margin": "20px"}),

        # Rendered Visualization
        html.Div([
            dcc.Graph(id="cosmic-visualization", style={"height": "75vh"}),
        ]),

        # Dynamic Raphael Equations
        html.Div(
            id="raphael-equations",
            style={
                "color": "white",
                "marginTop": "20px",
                "padding": "10px",
                "border": "1px solid white",
                "backgroundColor": "#111",
            }
        ),
    ]
)

# Callbacks
@app.callback(
    [Output("cosmic-visualization", "figure"), Output("raphael-equations", "children")],
    [Input("phenomenon-selector", "value"), Input("fractal-slider", "value")]
)
def update_visualization(selected_phenomenon, fractal_steps):
    if selected_phenomenon is None or fractal_steps is None:
        raise PreventUpdate

    # Generate data and render visualization
    generator = PHENOMENA[selected_phenomenon]["generator"]
    plotter = PHENOMENA[selected_phenomenon]["plotter"]

    if selected_phenomenon == "Big Bang":
        data = generator(time_steps=500, fractal_iterations=fractal_steps)
        figure = plotter(data)

        # Calculate Raphael Equations for a sample time point
        sample_time = data["time"][100]
        sample_density = data["density"][100]
        raphael = {
            "Strong Force": sample_density / sample_time,
            "Weak Force": sample_density / (sample_time**2),
            "Energy Density": sample_density / sample_time + sample_density / (sample_time**2)
        }

    elif selected_phenomenon == "Dark Energy":
        data = generator(time_steps=500, fractal_iterations=fractal_steps)
        figure = plotter(data)

        # Calculate Raphael Equations for expansion at a sample time
        sample_time = data["time"][100]
        sample_expansion = data["expansion"][100]
        raphael = {
            "Dark Energy Density": DARK_ENERGY_DENSITY * c**2,
            "Dark Force": DARK_ENERGY_DENSITY * c**2 / sample_expansion,
        }

    elif selected_phenomenon == "Cosmic Microwave Background":
        refined_map = generator(grid_size=512, fractal_iterations=fractal_steps)
        figure = plotter(refined_map)

        # Calculate Raphael Equations for a sample fluctuation
        sample_temperature = np.mean(refined_map)
        fluctuation = np.std(refined_map)
        raphael = {
            "Energy Density": (k * sample_temperature) / (c**2),
            "CMB Force": fluctuation * (k * sample_temperature) / (c**2),
        }

    # Format Raphael equations for display
    raphael_text = "Raphael Equations:<br>" + "<br>".join([f"{key}: {value:.2e}" for key, value in raphael.items()])

    return figure, html.Div(raphael_text)

# Run App
if __name__ == "__main__":
    app.run_server(debug=True)
