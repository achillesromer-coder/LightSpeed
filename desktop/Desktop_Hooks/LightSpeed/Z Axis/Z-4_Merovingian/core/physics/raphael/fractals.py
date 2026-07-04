import numpy as np


def generate_fractal(num_points, iterations=3, scale=1.0):
    """
    Generates fractal-like patterns for scaling simulations.
    """
    x, y, z = np.random.uniform(-1, 1, num_points), np.random.uniform(-1, 1, num_points), np.random.uniform(-1, 1, num_points)

    for _ in range(iterations):
        r = np.sqrt(x**2 + y**2 + z**2)
        x += np.sin(r) * scale
        y += np.cos(r) * scale
        z += np.tan(r) * scale

    density = np.exp(-r / scale)  # Density fades with distance
    return x, y, z, density

def generate_fractal_3d(levels=3, num_points=1000):
    """
    Generates a 3D fractal pattern based on the specified number of levels.
    """
    x, y, z = [], [], []
    for level in range(levels):
        theta = np.random.uniform(0, 2 * np.pi, num_points)
        phi = np.random.uniform(0, np.pi, num_points)
        r = np.random.normal(1 + level * 0.5, 0.2, num_points)

        x += (r * np.sin(phi) * np.cos(theta)).tolist()
        y += (r * np.sin(phi) * np.sin(theta)).tolist()
        z += (r * np.cos(phi)).tolist()

    return np.array(x), np.array(y), np.array(z)

def apply_fractal_color_map(x, y, z, color_map="Viridis"):
    """
    Applies a color map to fractal data for visualization.
    """
    density = np.sqrt(x**2 + y**2 + z**2)
    return density

# Generate fractal for atomic visualization
def generate_atomic_fractal(element_data, levels=3):
    """
    Generates fractals specific to atomic structures.
    """
    protons = element_data["protons"]
    neutrons = element_data["neutrons"]
    electrons = element_data["electrons"]

    base_points = protons + neutrons + electrons
    x, y, z = generate_fractal_3d(levels=levels, num_points=base_points)
    return x, y, z

# Fractal scaling for eco-rehabilitation nodes
def generate_eco_fractal(nodes=10, levels=3):
    """
    Generates fractals specific to eco-rehabilitation resource nodes.
    """
    x, y, z = generate_fractal_3d(levels=levels, num_points=nodes * 100)
    return x, y, z

# Example usage
if __name__ == "__main__":
    x, y, z = generate_fractal_3d(levels=4, num_points=1000)
    density = apply_fractal_color_map(x, y, z)
    print(f"Generated fractal with {len(x)} points.")
