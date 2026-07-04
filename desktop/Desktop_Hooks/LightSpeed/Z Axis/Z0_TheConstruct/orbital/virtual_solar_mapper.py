
# Imports

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot
import numpy


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-21 17:46:26

# Source files: 3



# virtual_solar_mapper.py

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

class CelestialObject:
    def __init__(self, name, a, e, i, omega, w, M, color='yellow'):
        self.name = name
        self.a = a  # semi-major axis in AU
        self.e = e  # eccentricity
        self.i = np.radians(i)  # inclination in radians
        self.omega = np.radians(omega)  # longitude of ascending node
        self.w = np.radians(w)  # argument of periapsis
        self.M = M  # mean anomaly
        self.color = color

def compute_orbit(obj, num_points=500):
    theta = np.linspace(0, 2 * np.pi, num_points)
    r = (obj.a * (1 - obj.e**2)) / (1 + obj.e * np.cos(theta))
    x_orbit = r * np.cos(theta)
    y_orbit = r * np.sin(theta)
    z_orbit = np.zeros_like(x_orbit)

    # Apply rotation for 3D inclination and orbit orientation
    x, y, z = [], [], []
    for xi, yi, zi in zip(x_orbit, y_orbit, z_orbit):
        x_rot = xi * np.cos(obj.w) - yi * np.sin(obj.w)
        y_rot = xi * np.sin(obj.w) + yi * np.cos(obj.w)
        x_final = x_rot * np.cos(obj.omega) - y_rot * np.sin(obj.omega)
        y_final = x_rot * np.sin(obj.omega) + y_rot * np.cos(obj.omega)
        z_final = zi + np.sin(obj.i) * np.sqrt(x_final**2 + y_final**2)
        x.append(x_final)
        y.append(y_final)
        z.append(z_final)
    return np.array(x), np.array(y), np.array(z)

def plot_3d_orbits(objects):
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    for obj in objects:
        x, y, z = compute_orbit(obj)
        ax.plot(x, y, z, label=obj.name, color=obj.color)
    ax.set_title("3D Holographic Solar System Orbital Map")
    ax.set_xlabel("X (AU)")
    ax.set_ylabel("Y (AU)")
    ax.set_zlabel("Z (AU)")
    ax.legend()
    plt.show()

def main():
    # Example celestial objects
    objects = [
        CelestialObject("Earth", 1.0, 0.0167, 0.0, 348.73936, 114.20783, 357.51716, color="blue"),
        CelestialObject("Mars", 1.524, 0.0935, 1.85, 49.57854, 286.502, 19.412, color="red"),
        CelestialObject("Psyche", 2.9, 0.13, 3.1, 150.2, 58.2, 0, color="gray"),
        CelestialObject("Ryugu", 1.189, 0.190, 5.883, 251.486, 130.564, 0, color="green")
    ]
    plot_3d_orbits(objects)

if __name__ == "__main__":
    main()
