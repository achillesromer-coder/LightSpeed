import numpy as np
import matplotlib.pyplot as plt

# Constants
h_bar = 1.0545718e-34
m = 9.10938356e-31  # Electron mass
R = 1e3  # Ricci scalar

# Spatial and temporal grid
x = np.linspace(-10, 10, 100)
t = np.linspace(0, 10, 100)
X, T = np.meshgrid(x, t)

# Wavefunction evolution
def wavefunction(X, T):
    laplacian = -X**2
    curvature_effect = -(R / 6) * X
    return np.sin(X - T) * np.exp(-0.1 * (laplacian + curvature_effect))

Psi = wavefunction(X, T)

# Plot
plt.figure(figsize=(10, 6))
plt.contourf(X, T, Psi, levels=50, cmap='inferno')
plt.colorbar(label="Amplitude")
plt.title("Quantum Wavefunction in Curved Spacetime")
plt.xlabel("Spatial Coordinate")
plt.ylabel("Time")
plt.show()