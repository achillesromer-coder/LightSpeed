from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from database_loader import load_elements_database
from fractals import generate_atomic_fractal, generate_eco_fractal

# Load databases
ELEMENTS = load_elements_database("data/elements.json")

# Create Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# Side menu with toggle options
def create_side_menu():
    return dbc.Col(
        [
            html.H3("Settings", style={"color": "white"}),
            html.Label("Select Element:", style={"color": "white"}),
            dcc.Dropdown(
                id="element-dropdown",
                options=[{"label": k, "value": k} for k in ELEMENTS.keys()],
                value="Hydrogen",
                style={"backgroundColor": "black", "color": "white"}
            ),
            html.Label("Visualization Mode:", style={"color": "white"}),
            dcc.RadioItems(
                id="visualization-mode",
                options=[
                    {"label": "Atomic", "value": "atomic"},
                    {"label": "Eco-Rehabilitation", "value": "eco"},
                ],
                value="atomic",
                style={"color": "white"}
            ),
            html.Label("Fractal Levels:", style={"color": "white"}),
            dcc.Slider(
                id="fractal-levels",
                min=1, max=5, step=1, value=3,
                marks={i: str(i) for i in range(1, 6)}
            ),
        ],
        width=3,
        style={"padding": "20px", "backgroundColor": "#2C2F33", "borderRight": "2px solid #7289DA"}
    )

# Main graph area
def create_main_graph():
    return dbc.Col(
        [
            dcc.Graph(id="main-visualization", style={"height": "75vh"}),
        ],
        width=9
    )

# Full layout
app.layout = html.Div(
    style={"backgroundColor": "black", "color": "white", "height": "100vh"},
    children=[
        html.H1(
            "6D Scientific Visualizer",
            style={"textAlign": "center", "marginBottom": "20px", "color": "#7289DA"}
        ),
        dbc.Row([create_side_menu(), create_main_graph()])
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
