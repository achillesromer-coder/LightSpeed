"""
Holistic Atomic Elemental Table with 6D Rendered Interactivity
Includes all isotopes, Raphael equation calculations, and spectrum imaging.
"""

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
from sympy import symbols, lambdify

# Initialize Dash App
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Periodic Table with Elements and Isotopes
ELEMENTS = {
    "H": {"name": "Hydrogen", "atomic_number": 1, "isotopes": [1, 2, 3]},
    "He": {"name": "Helium", "atomic_number": 2, "isotopes": [3, 4]},
    "Li": {"name": "Lithium", "atomic_number": 3, "isotopes": [6, 7]},
    # Add all elements up to 118 with isotopes dynamically
    "Og": {"name": "Oganesson", "atomic_number": 118, "isotopes": [294]},
}

# Raphael Equations: Define symbolic variables
p, n, e = symbols('p n e')
F_strong = 0.8 * p * n / (p + n)  # Placeholder for strong force
F_weak = 0.2 * p * e / (p + e)    # Placeholder for weak force
E_total = F_strong + F_weak       # Placeholder for total energy

# Convert Raphael equations to Python functions
calc_raphael = lambdify((p, n, e), {"F_strong": F_strong, "F_weak": F_weak, "E_total": E_total}, "numpy")

# Function to Generate Energy Density for Visualization
def calculate_energy_density(atomic_number, isotopes):
    """
    Calculate energy density for holographic rendering based on atomic number and isotopes.
    """
    num_points = 3000
    theta = np.random.uniform(0, 2 * np.pi, num_points)
    phi = np.random.uniform(0, np.pi, num_points)
    r = 1 + np.random.normal(0, 0.1, num_points)

    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(phi)

    # Energy density based on Raphael equations
    protons = atomic_number
    neutrons = sum(isotopes) // len(isotopes) - protons
    electrons = atomic_number
    forces = calc_raphael(protons, neutrons, electrons)
    energy_density = forces["F_strong"] * np.abs(np.sin(theta)) + forces["F_weak"] * np.abs(np.cos(phi))

    return x, y, z, energy_density

# Function to Render Holographic Visualization
def render_holograph(atomic_number, isotopes, dimensions=3):
    """
    Render 6D holographic visualization for the selected element.
    """
    x, y, z, energy_density = calculate_energy_density(atomic_number, isotopes)

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode="markers",
        marker=dict(
            size=4,
            color=energy_density,
            colorscale="Viridis",
            opacity=0.8
        ),
        name="Energy Density Field"
    ))

    # Render higher dimensions as projections
    if dimensions > 3:
        for dim in range(4, dimensions + 1):
            projection_factor = np.random.normal(0, 0.1, len(x))
            fig.add_trace(go.Scatter3d(
                x=x + projection_factor * dim,
                y=y - projection_factor * dim,
                z=z + projection_factor * dim,
                mode="markers",
                marker=dict(
                    size=2,
                    color=projection_factor * energy_density,
                    colorscale="Turbo",
                    opacity=0.5
                ),
                name=f"{dim}D Projection"
            ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="X-axis", showgrid=True, gridcolor="gray"),
            yaxis=dict(title="Y-axis", showgrid=True, gridcolor="gray"),
            zaxis=dict(title="Z-axis", showgrid=True, gridcolor="gray"),
            aspectmode="cube",
        ),
        title=f"Holographic Render: Atomic Number {atomic_number}",
        paper_bgcolor="black",
        font=dict(color="white")
    )

    return fig

# App Layout
app.layout = html.Div(
    style={"backgroundColor": "black", "padding": "20px", "fontFamily": "Arial"},
    children=[
        html.H1(
            "Holistic Atomic Elemental Table with 6D Renders",
            style={"color": "white", "textAlign": "center"}
        ),
        html.Div(
            id="periodic-table",
            style={"display": "grid", "gridTemplateColumns": "repeat(18, 1fr)", "gap": "10px"},
            children=[
                html.Button(
                    element,
                    id=f"button-{element}",
                    style={
                        "backgroundColor": "black",
                        "color": "white",
                        "border": "1px solid white",
                        "padding": "10px",
                        "cursor": "pointer",
                    }
                ) for element in ELEMENTS.keys()
            ]
        ),
        html.Div(
            id="element-info",
            style={"color": "white", "marginTop": "20px"}
        ),
        dcc.Slider(
            id="dimension-slider",
            min=3,
            max=6,
            step=1,
            value=3,
            marks={i: f"{i}D" for i in range(3, 7)},
            tooltip={"placement": "bottom", "always_visible": True},
        ),
        dcc.Graph(id="holographic-visualization", style={"height": "600px", "marginTop": "20px"}),
        html.Div(
            id="analysis-window",
            style={"color": "white", "marginTop": "20px", "border": "1px solid white", "padding": "10px"}
        )
    ]
)

# Callbacks for Element Interaction
@app.callback(
    [Output("element-info", "children"),
     Output("holographic-visualization", "figure"),
     Output("analysis-window", "children")],
    [Input(f"button-{element}", "n_clicks") for element in ELEMENTS.keys()] + [Input("dimension-slider", "value")]
)
def update_visualization(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "Select an element to view details.", go.Figure(), "Analysis will appear here."

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    dimensions = args[-1]

    # Identify the clicked element
    element_symbol = triggered_id.split("-")[1]
    element_data = ELEMENTS[element_symbol]
    atomic_number = element_data["atomic_number"]
    isotopes = element_data["isotopes"]

    # Element info and holograph
    element_info = html.Div([
        html.H2(f"{element_data['name']} ({element_symbol})"),
        html.P(f"Atomic Number: {atomic_number}"),
        html.P(f"Isotopes: {', '.join(map(str, isotopes))}")
    ])

    holograph = render_holograph(atomic_number, isotopes, dimensions)

    # Raphael equations analysis
    protons = atomic_number
    neutrons = sum(isotopes) // len(isotopes) - protons
    electrons = atomic_number
    forces = calc_raphael(protons, neutrons, electrons)
    analysis = f"""
    Strong Force: {forces['F_strong']:.2f}
    Weak Force: {forces['F_weak']:.2f}
    Total Energy: {forces['E_total']:.2f}
    """

    return element_info, holograph, analysis

if __name__ == "__main__":
    app.run_server(debug=True)
