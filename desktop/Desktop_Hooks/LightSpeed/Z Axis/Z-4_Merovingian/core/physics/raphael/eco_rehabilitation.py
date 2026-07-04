import numpy as np
import plotly.graph_objects as go
from fractal_expansion import generate_fractal_3d


def simulate_biodiversity_growth(num_points=500, growth_factor=0.2):
    """
    Simulates biodiversity growth as fractals expand over time.
    """
    x, y, z = generate_fractal_3d(levels=3, num_points=num_points)
    biodiversity = np.random.normal(1.0, growth_factor, len(x))
    return x, y, z, biodiversity


def visualize_eco_rehabilitation(time_steps=10):
    """
    Visualizes eco-rehabilitation dynamics over time.
    """
    x, y, z, biodiversity = simulate_biodiversity_growth()

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode="markers",
        marker=dict(
            size=3,
            color=biodiversity,
            colorscale="Viridis",
            opacity=0.8
        ),
        name="Biodiversity Nodes"
    ))

    fig.update_layout(
        title="Eco-Rehabilitation Simulation",
        scene=dict(
            xaxis=dict(title="X-axis"),
            yaxis=dict(title="Y-axis"),
            zaxis=dict(title="Z-axis"),
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        paper_bgcolor="black",
        font=dict(color="white")
    )

    fig.show()


def calculate_resource_distribution(resources, nodes):
    """
    Simulates the distribution of resources across eco-rehabilitation nodes.
    """
    distribution = {node: np.random.choice(resources) for node in range(nodes)}
    return distribution


# Example usage
if __name__ == "__main__":
    visualize_eco_rehabilitation(time_steps=10)
    resources = ["Water", "Energy", "Nutrients", "Carbon Sequestration"]
    print("Resource Distribution:", calculate_resource_distribution(resources, nodes=10))
