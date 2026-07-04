import numpy as np
import plotly.graph_objects as go
from scipy.constants import G, pi
from dash import Dash, dcc, html, Input, Output, callback_context, State

# Constants
LIGHT_YEAR_TO_METER = 9.461e15
SOLAR_MASS_TO_KG = 1.989e30
ISM_COMPONENTS = {
    "Molecular Clouds": {"scale": 0.1, "color": "Blues", "opacity": 0.7},
    "HII Regions": {"scale": 0.05, "color": "Reds", "opacity": 0.6},
    "Neutral Hydrogen": {"scale": 0.2, "color": "Greens", "opacity": 0.5},
    "Dust and Metals": {"scale": 0.03, "color": "Oranges", "opacity": 0.4},
}
TIME_STEPS = 500
FRACTAL_STEPS = 3

app = Dash(__name__)

# Fractal refinement for ISM regions
def fractal_refinement(base_positions, scale_factor, iterations):
    refined_positions = base_positions
    for _ in range(iterations):
        noise = np.random.uniform(-scale_factor, scale_factor, refined_positions.shape)
        refined_positions = np.concatenate([refined_positions, refined_positions + noise])
    return refined_positions

# ISM Simulation
def simulate_ism(fractal_iterations=FRACTAL_STEPS, region_radius=500, component_scale=ISM_COMPONENTS):
    """
    Simulates the interstellar medium, including molecular clouds, HII regions, and neutral hydrogen.
    """
    positions = {}
    for component, params in component_scale.items():
        base_x = np.random.normal(0, region_radius, size=TIME_STEPS)
        base_y = np.random.normal(0, region_radius, size=TIME_STEPS)
        base_z = np.random.normal(0, region_radius / 10, size=TIME_STEPS)
        scale = params["scale"] * region_radius

        refined_x = fractal_refinement(base_x, scale, fractal_iterations)
        refined_y = fractal_refinement(base_y, scale, fractal_iterations)
        refined_z = fractal_refinement(base_z, scale, fractal_iterations)

        positions[component] = {
            "x": refined_x,
            "y": refined_y,
            "z": refined_z,
            "density": np.exp(-np.sqrt(refined_x**2 + refined_y**2) / region_radius),
        }
    return positions

# Render ISM Components
def render_ism(positions):
    fig = go.Figure()

    for component, data in positions.items():
        fig.add_trace(go.Scatter3d(
            x=data["x"], y=data["y"], z=data["z"],
            mode="markers",
            marker=dict(
                size=2,
                color=data["density"],
                colorscale=ISM_COMPONENTS[component]["color"],
                opacity=ISM_COMPONENTS[component]["opacity"],
            ),
            name=component
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X (light-years)", showbackground=False),
            yaxis=dict(title="Y (light-years)", showbackground=False),
            zaxis=dict(title="Z (light-years)", showbackground=False),
        ),
        paper_bgcolor="black",
        font=dict(color="white"),
        title="Interstellar Medium Simulation"
    )
    return fig

# Dash App Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "fontFamily": "Arial"},
    children=[
        html.H1("Interstellar Medium Simulation", style={"textAlign": "center"}),

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
        ], style={"margin": "20px"}),

        # Rendered Visualization
        dcc.Graph(id="ism-visualization", style={"height": "75vh"}),
    ]
)

# Callback for ISM Visualization
@app.callback(
    Output("ism-visualization", "figure"),
    Input("fractal-slider", "value"),
)
def update_ism_visualization(fractal_steps):
    positions = simulate_ism(fractal_iterations=fractal_steps)
    return render_ism(positions)

# Run the App
if __name__ == "__main__":
    app.run_server(debug=True)
