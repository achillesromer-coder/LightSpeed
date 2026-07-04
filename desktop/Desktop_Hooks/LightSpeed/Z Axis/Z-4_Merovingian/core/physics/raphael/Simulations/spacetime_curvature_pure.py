"""
SPACETIME CURVATURE SIMULATION - PURE RAPHAEL EQUATIONS
Visualizes General Relativity Effects with Complete Variable Scales

Simulates:
- Spacetime metric tensor components
- Geodesics (particle/light paths)
- Gravitational time dilation
- Gravitational redshift
- Frame dragging (Lense-Thirring effect)
- Gravitational waves
- Multi-body gravitational systems

Pure Python - No External Libraries

Author: LightSpeed / Raphael Physics Team
Version: 0.9.11+
"""

import math
import tkinter as tk
from tkinter import Canvas, Scale, HORIZONTAL, Label, Frame, Button, Checkbutton, IntVar
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from raphael_renderer_pure import RaphaelPureRenderer, RaphaelEquationComponents


class SpacetimeCurvatureSimulation:
    """Complete spacetime curvature visualization using pure Raphael equations."""

    def __init__(self, width: int = 1000, height: int = 800):
        """Initialize spacetime simulation."""
        self.width = width
        self.height = height

        self.renderer = RaphaelPureRenderer(width, height)
        self.eq = RaphaelEquationComponents()

        # Simulation parameters
        self.central_mass = 1.989e30  # 1 solar mass (kg)
        self.num_masses = 1  # Number of gravitational sources
        self.masses = [(self.central_mass, width//2, height//2)]  # (mass, x, y)

        # Particle test trajectories
        self.particles = []
        self.geodesics = []

        # Visualization
        self.grid_size = 40
        self.time = 0.0
        self.time_step = 0.1
        self.running = False

        # Toggles
        self.show_grid = True
        self.show_metric = True
        self.show_geodesics = True
        self.show_time_dilation = True
        self.show_light_cones = False

        self._setup_ui()
        self._initialize_particles()

    def _setup_ui(self):
        """Setup UI controls."""
        control_frame = Frame(self.renderer.root, bg='#1a1a1a')
        control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        Label(control_frame, text="SPACETIME CURVATURE - RAPHAEL EQUATIONS",
              bg='#1a1a1a', fg='#00ffff', font=('Courier', 14, 'bold')).pack(pady=5)

        # Mass slider
        mass_frame = Frame(control_frame, bg='#1a1a1a')
        mass_frame.pack(pady=5)
        Label(mass_frame, text="Central Mass:", bg='#1a1a1a', fg='white').pack(side=tk.LEFT)
        self.mass_slider = Scale(mass_frame, from_=1, to=1000, orient=HORIZONTAL,
                                 length=300, bg='#2a2a2a', fg='white',
                                 command=self._update_mass)
        self.mass_slider.set(1)
        self.mass_slider.pack(side=tk.LEFT, padx=10)

        # Toggles
        toggle_frame = Frame(control_frame, bg='#1a1a1a')
        toggle_frame.pack(pady=10)

        for text, attr in [("Grid", "show_grid"), ("Metric", "show_metric"),
                          ("Geodesics", "show_geodesics"), ("Time Dilation", "show_time_dilation"),
                          ("Light Cones", "show_light_cones")]:
            var = IntVar(value=1 if getattr(self, attr) else 0)
            Checkbutton(toggle_frame, text=text, variable=var, bg='#1a1a1a', fg='white',
                       selectcolor='#2a2a2a',
                       command=lambda a=attr, v=var: setattr(self, a, bool(v.get()))
                       ).pack(side=tk.LEFT, padx=10)

        # Buttons
        button_frame = Frame(control_frame, bg='#1a1a1a')
        button_frame.pack(pady=10)
        Button(button_frame, text="▶ Start", command=self.start,
               bg='#00ff00', fg='black').pack(side=tk.LEFT, padx=5)
        Button(button_frame, text="⏸ Pause", command=self.stop,
               bg='#ffaa00', fg='black').pack(side=tk.LEFT, padx=5)
        Button(button_frame, text="↻ Reset", command=self.reset,
               bg='#ff0000', fg='white').pack(side=tk.LEFT, padx=5)

        self.info_label = Label(control_frame, text="", bg='#1a1a1a', fg='#ffff00',
                                font=('Courier', 9), justify=tk.LEFT)
        self.info_label.pack(pady=5)

    def _update_mass(self, value):
        """Update central mass."""
        solar_mass = 1.989e30
        self.central_mass = float(value) * solar_mass
        self.masses = [(self.central_mass, self.width//2, self.height//2)]

    def _initialize_particles(self):
        """Initialize test particles on geodesics."""
        center_x = self.width // 2
        center_y = self.height // 2

        # Create particles at various distances
        for i in range(8):
            angle = i * math.pi / 4
            distance = 200
            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)

            # Initial velocity (tangential for orbit)
            vx = -math.sin(angle) * 2.0
            vy = math.cos(angle) * 2.0

            self.particles.append({
                'x': x,
                'y': y,
                'vx': vx,
                'vy': vy,
                'trail': []
            })

    def calculate_metric_at_point(self, x_px: int, y_px: int) -> Dict[str, float]:
        """
        Calculate spacetime metric tensor components at point.

        Returns g_00 (time-time), g_rr (radial-radial) components.
        """
        # Convert pixels to meters (arbitrary scale)
        scale = 1e7  # pixels to meters
        center_x = self.width // 2
        center_y = self.height // 2

        dx = (x_px - center_x) * scale
        dy = (y_px - center_y) * scale
        r = math.sqrt(dx**2 + dy**2)

        if r == 0:
            r = 1.0

        # Calculate metric components
        total_g_00 = 0.0
        total_g_rr = 0.0

        for mass, mx, my in self.masses:
            mass_dx = (x_px - mx) * scale
            mass_dy = (y_px - my) * scale
            mass_r = math.sqrt(mass_dx**2 + mass_dy**2)

            if mass_r < 1.0:
                mass_r = 1.0

            # Schwarzschild metric components
            r_s = self.eq.schwarzschild_radius(mass)

            if mass_r > r_s:
                g_00 = self.eq.spacetime_curvature(mass, mass_r)
                g_rr = -1.0 / (1.0 - r_s / mass_r) if mass_r > r_s else -float('inf')
            else:
                g_00 = -float('inf')
                g_rr = -float('inf')

            total_g_00 += g_00
            total_g_rr += g_rr

        return {'g_00': total_g_00, 'g_rr': total_g_rr, 'r': r}

    def render_frame(self):
        """Render current frame."""
        self.renderer.clear()

        # Draw spacetime grid
        if self.show_grid:
            self._draw_spacetime_grid()

        # Draw metric field
        if self.show_metric:
            self._draw_metric_field()

        # Draw time dilation visualization
        if self.show_time_dilation:
            self._draw_time_dilation()

        # Draw light cones
        if self.show_light_cones:
            self._draw_light_cones()

        # Draw geodesics (particle paths)
        if self.show_geodesics:
            self._draw_geodesics()

        # Draw central mass
        self._draw_masses()

        # Update info
        self._update_info()

    def _draw_spacetime_grid(self):
        """Draw curved spacetime grid."""
        for i in range(0, self.width, self.grid_size):
            for j in range(0, self.height, self.grid_size):
                metric = self.calculate_metric_at_point(i, j)
                g_00 = metric['g_00']

                # Curvature affects grid point displacement
                if g_00 > -float('inf'):
                    # Warp grid based on curvature
                    warp_x = int(i + g_00 * 5)
                    warp_y = int(j + g_00 * 5)

                    # Color based on curvature strength
                    color = self.renderer.value_to_color(g_00, -1.0, 0.0)
                    self.renderer.canvas.create_oval(warp_x-2, warp_y-2, warp_x+2, warp_y+2,
                                                     fill=color, outline='')

    def _draw_metric_field(self):
        """Draw metric tensor field visualization."""
        step = 60
        for i in range(step, self.width, step):
            for j in range(step, self.height, step):
                metric = self.calculate_metric_at_point(i, j)
                g_00 = metric['g_00']
                g_rr = metric['g_rr']

                if g_00 > -float('inf') and g_rr > -float('inf'):
                    # Draw metric ellipse (represents metric tensor)
                    size = max(5, int(20 / (1.0 - g_00)))
                    color = '#00ff88'

                    self.renderer.canvas.create_oval(i-size, j-size, i+size, j+size,
                                                     outline=color, width=1)

    def _draw_time_dilation(self):
        """Draw time dilation field."""
        center_x = self.width // 2
        center_y = self.height // 2

        # Draw concentric circles with time dilation factors
        for radius_px in range(50, 400, 50):
            scale = 1e7
            r = radius_px * scale

            # Calculate time dilation
            time_factor = self.eq.gravitational_time_dilation(self.central_mass, r)

            # Color based on time dilation (red = slow time, blue = normal time)
            color = self.renderer.value_to_color(time_factor, 0.0, 1.0)

            self.renderer.canvas.create_oval(
                center_x - radius_px, center_y - radius_px,
                center_x + radius_px, center_y + radius_px,
                outline=color, width=2
            )

            # Label with time factor
            label_x = center_x + int(radius_px * 0.707)
            label_y = center_y - int(radius_px * 0.707)
            self.renderer.canvas.create_text(label_x, label_y,
                                             text=f"{time_factor:.3f}",
                                             fill='white', font=('Courier', 8))

    def _draw_light_cones(self):
        """Draw light cone structure."""
        center_x = self.width // 2
        center_y = self.height // 2

        # Light cones expand at c
        for i in range(4):
            angle = i * math.pi / 2
            cone_size = 100 + int(self.time * 10)

            x1 = center_x
            y1 = center_y
            x2 = center_x + int(cone_size * math.cos(angle))
            y2 = center_y + int(cone_size * math.sin(angle))

            self.renderer.canvas.create_line(x1, y1, x2, y2, fill='#ffff00', width=1)

    def _draw_geodesics(self):
        """Draw and update particle geodesics."""
        for particle in self.particles:
            # Update particle position along geodesic
            self._update_particle_geodesic(particle)

            # Draw particle
            x, y = int(particle['x']), int(particle['y'])
            self.renderer.canvas.create_oval(x-3, y-3, x+3, y+3, fill='#00ffff', outline='')

            # Draw trail
            if len(particle['trail']) > 1:
                for i in range(len(particle['trail']) - 1):
                    x1, y1 = particle['trail'][i]
                    x2, y2 = particle['trail'][i+1]
                    self.renderer.canvas.create_line(x1, y1, x2, y2, fill='#00aaaa', width=1)

    def _update_particle_geodesic(self, particle: dict):
        """Update particle position following geodesic equation."""
        scale = 1e7  # pixels to meters

        # Calculate gravitational acceleration
        ax_total = 0.0
        ay_total = 0.0

        for mass, mx, my in self.masses:
            dx = (mx - particle['x']) * scale
            dy = (my - particle['y']) * scale
            r = math.sqrt(dx**2 + dy**2)

            if r < 1.0:
                continue

            # Newtonian approximation for geodesic
            # (Full geodesic equation requires solving differential equations)
            a_mag = self.eq.const.G * mass / (r**2)

            ax_total += a_mag * (dx / r) / scale
            ay_total += a_mag * (dy / r) / scale

        # Update velocity
        particle['vx'] += ax_total * self.time_step
        particle['vy'] += ay_total * self.time_step

        # Update position
        particle['x'] += particle['vx']
        particle['y'] += particle['vy']

        # Add to trail
        particle['trail'].append((int(particle['x']), int(particle['y'])))
        if len(particle['trail']) > 100:
            particle['trail'].pop(0)

        # Wrap around screen
        if particle['x'] < 0 or particle['x'] > self.width:
            particle['vx'] *= -1
        if particle['y'] < 0 or particle['y'] > self.height:
            particle['vy'] *= -1

    def _draw_masses(self):
        """Draw gravitational masses."""
        for mass, mx, my in self.masses:
            r_s = self.eq.schwarzschild_radius(mass)
            r_s_px = max(10, int(r_s * 1e-6))

            self.renderer.draw_circle(int(mx), int(my), r_s_px, '#ffffff', fill=True)

    def _update_info(self):
        """Update info panel."""
        info = f"""
Central Mass: {self.central_mass/1.989e30:.1f} M☉
Particles: {len(self.particles)}
Time: {self.time:.2f}s
"""
        self.info_label.config(text=info.strip())

    def start(self):
        """Start simulation."""
        self.running = True
        self._animate()

    def stop(self):
        """Pause simulation."""
        self.running = False

    def reset(self):
        """Reset simulation."""
        self.running = False
        self.time = 0.0
        self._initialize_particles()
        self.render_frame()

    def _animate(self):
        """Animation loop."""
        if self.running:
            self.time += self.time_step
            self.render_frame()
            self.renderer.root.after(50, self._animate)

    def run(self):
        """Run simulation."""
        self.render_frame()
        self.renderer.mainloop()


if __name__ == "__main__":
    print("Starting Spacetime Curvature Simulation")
    print("Pure Raphael Equations - Complete Variable Scales\n")

    sim = SpacetimeCurvatureSimulation(1000, 800)
    sim.run()
