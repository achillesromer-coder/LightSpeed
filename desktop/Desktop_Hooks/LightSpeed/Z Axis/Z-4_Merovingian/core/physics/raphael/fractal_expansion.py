import numpy as np
import plotly.graph_objects as go

def mandelbrot_set(width, height, zoom, max_iter):
    """
    Generates a Mandelbrot fractal set for a 2D projection.
    """
    x = np.linspace(-2.0, 2.0, width) / zoom
    y = np.linspace(-2.0, 2.0, height) / zoom
    fractal = np.zeros((width, height))
    for i, x_val in enumerate(x):
        for j, y_val in enumerate(y):
            z = 0
            c = complex(x_val, y_val)
            for k in range(max_iter):
                if abs(z) > 2.0:
                    fractal[i, j] = k
                    break
                z = z * z + c
    return fractal

def generate_fractal_3d(levels=3, num_points=1000):
    """
    Generates a 3D fractal pattern using iterative refinements.
    """
    x, y, z = [], [], []
    for level in range(levels):
        for _ in range(num_points // levels):
            x.append(np.random.uniform(-1, 1) / (level + 1))
            y.append(np.random.uniform(-1, 1) / (level + 1))
            z.append(np.random.uniform(-1, 1) / (level + 1))
    return x, y, z

def visualize_fractal_3d(levels=3):
    """
    Visualize a 3D fractal structure.
    """
    x, y, z = generate_fractal_3d(levels=levels)
    fig = go.Figure(data=go.Scatter3d(
        x=x, y=y, z=z,
        mode='markers',
        marker=dict(size=2, color=z, colorscale="Viridis", opacity=0.8)
    ))
    fig.update_layout(
        title="3D Fractal Expansion",
        scene=dict(
            xaxis=dict(title="X-axis"),
            yaxis=dict(title="Y-axis"),
            zaxis=dict(title="Z-axis"),
        ),
        margin=dict(l=0, r=0, b=0, t=30),
    )
    fig.show()

# Fractal Steps Visualization (Expanded to 3 Steps Minimum)
def fractal_steps_visualization(num_steps=3):
    """
    Visualizes fractal refinements in 3+ iterations.
    """
    figs = []
    for step in range(1, num_steps + 1):
        x, y, z = generate_fractal_3d(levels=step)
        fig = go.Figure(data=go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(size=2, color=z, colorscale="Plasma", opacity=0.8)
        ))
        fig.update_layout(
            title=f"Fractal Expansion: Step {step}",
            scene=dict(
                xaxis=dict(title="X-axis"),
                yaxis=dict(title="Y-axis"),
                zaxis=dict(title="Z-axis"),
            ),
            margin=dict(l=0, r=0, b=0, t=30),
        )
        figs.append(fig)
    return figs

# Example usage
if __name__ == "__main__":
    # Visualize a single fractal expansion
    visualize_fractal_3d(levels=4)

    # Visualize fractal steps
    steps = fractal_steps_visualization(num_steps=3)
    for step_fig in steps:
        step_fig.show()
