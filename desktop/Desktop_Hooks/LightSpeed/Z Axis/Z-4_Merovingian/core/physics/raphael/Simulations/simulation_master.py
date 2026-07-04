"""
SIMULATION MASTER CONTROLLER V0.9.11+
Integrates All Raphael Pure Simulations into 3D Environment

Complete Simulation Suite:
1. Black Hole Dynamics
2. Spacetime Curvature
3. Quantum Foam
4. Big Bang Cosmology
5. Gravitational Waves
6. Quantum Superposition
7. Particle Physics
8. Dark Matter/Energy

All simulations use pure Raphael equations with complete variable scales.
NO external libraries - only built-in Python (math, tkinter).

Integration with LightSpeed 3D Immersive Environment.

Author: LightSpeed / Raphael Physics Team
Version: 0.9.11+
"""

import math
import tkinter as tk
from tkinter import Canvas, Frame, Label, Button, Listbox, SINGLE, Scrollbar
import sys
from pathlib import Path

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from raphael_renderer_pure import RaphaelPureRenderer, RaphaelEquationComponents


class SimulationMaster:
    """
    Master controller for all Raphael physics simulations.

    Provides unified interface to launch and manage all simulations.
    """

    def __init__(self):
        """Initialize simulation master."""
        self.eq = RaphaelEquationComponents()

        # Available simulations
        self.simulations = {
            '1. Black Hole Dynamics': {
                'file': 'black_hole_pure.py',
                'description': 'Event horizon, lensing, accretion disk, Hawking radiation',
                'module': None
            },
            '2. Spacetime Curvature': {
                'file': 'spacetime_curvature_pure.py',
                'description': 'Metric tensor, geodesics, time dilation, gravitational waves',
                'module': None
            },
            '3. Quantum Foam': {
                'file': 'quantum_foam_pure.py',
                'description': 'Planck scale fluctuations, virtual particles, uncertainty',
                'module': None
            },
            '4. Big Bang Cosmology': {
                'file': 'big_bang_pure.py',
                'description': 'Universe expansion, CMB, nucleosynthesis, inflation',
                'module': None
            },
            '5. Gravitational Waves': {
                'file': 'gravitational_waves_pure.py',
                'description': 'Binary mergers, waveforms, LIGO detection, strain',
                'module': None
            },
            '6. Quantum Superposition': {
                'file': 'quantum_superposition_pure.py',
                'description': 'Wavefunction collapse, double-slit, entanglement',
                'module': None
            },
            '7. Particle Physics': {
                'file': 'particle_physics_pure.py',
                'description': 'Strong/weak forces, decay, collisions, cross-sections',
                'module': None
            },
            '8. Dark Matter & Energy': {
                'file': 'dark_matter_energy_pure.py',
                'description': 'NFW profile, cosmological constant, expansion rate',
                'module': None
            },
        }

        # Create GUI
        self._create_gui()

    def _create_gui(self):
        """Create master controller GUI."""
        self.root = tk.Tk()
        self.root.title("Raphael Simulation Master V0.9.11+")
        self.root.geometry("900x700")
        self.root.configure(bg='#0a0a0a')

        # Title
        title_frame = Frame(self.root, bg='#0a0a0a')
        title_frame.pack(pady=20)

        Label(title_frame,
              text="🌌 RAPHAEL PHYSICS SIMULATION MASTER 🌌",
              bg='#0a0a0a', fg='#00ffff',
              font=('Courier', 20, 'bold')).pack()

        Label(title_frame,
              text="Pure Python • Complete Variable Scales • Fundamental Equations",
              bg='#0a0a0a', fg='#00ff88',
              font=('Courier', 10)).pack()

        # Simulation list
        list_frame = Frame(self.root, bg='#1a1a1a')
        list_frame.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)

        Label(list_frame, text="Available Simulations:",
              bg='#1a1a1a', fg='white', font=('Courier', 12, 'bold')).pack(anchor='w')

        # Scrollbar
        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = Listbox(list_frame, yscrollcommand=scrollbar.set,
                               bg='#2a2a2a', fg='#00ff00',
                               font=('Courier', 11), selectmode=SINGLE,
                               height=12, activestyle='none',
                               selectbackground='#00ffff', selectforeground='#000000')
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Populate list
        for sim_name in self.simulations.keys():
            self.listbox.insert(tk.END, sim_name)

        # Bind selection
        self.listbox.bind('<<ListboxSelect>>', self._on_select)

        # Description panel
        desc_frame = Frame(self.root, bg='#1a1a1a')
        desc_frame.pack(pady=10, padx=40, fill=tk.X)

        self.desc_label = Label(desc_frame, text="Select a simulation to see details",
                                bg='#1a1a1a', fg='#ffff00',
                                font=('Courier', 10), justify=tk.LEFT,
                                wraplength=800)
        self.desc_label.pack()

        # Equation info panel
        eq_frame = Frame(self.root, bg='#0a0a0a')
        eq_frame.pack(pady=10, padx=40, fill=tk.X)

        self.eq_label = Label(eq_frame, text="",
                             bg='#0a0a0a', fg='#888888',
                             font=('Courier', 9), justify=tk.LEFT)
        self.eq_label.pack()

        # Buttons
        button_frame = Frame(self.root, bg='#0a0a0a')
        button_frame.pack(pady=20)

        Button(button_frame, text="🚀 Launch Simulation",
               command=self._launch_simulation,
               bg='#00ff00', fg='black', font=('Courier', 12, 'bold'),
               width=20, height=2).pack(side=tk.LEFT, padx=10)

        Button(button_frame, text="📊 Show All Stats",
               command=self._show_all_stats,
               bg='#00aaff', fg='white', font=('Courier', 12, 'bold'),
               width=20, height=2).pack(side=tk.LEFT, padx=10)

        Button(button_frame, text="📚 Equation Reference",
               command=self._show_equations,
               bg='#ff00ff', fg='white', font=('Courier', 12, 'bold'),
               width=20, height=2).pack(side=tk.LEFT, padx=10)

        # Status
        self.status_label = Label(self.root, text="Ready",
                                  bg='#0a0a0a', fg='#00ff00',
                                  font=('Courier', 10))
        self.status_label.pack(pady=10)

        # Footer
        footer = Label(self.root,
                      text="LightSpeed V0.9.11+ | Raphael Physics Engine | Pure Python Implementation",
                      bg='#0a0a0a', fg='#444444',
                      font=('Courier', 8))
        footer.pack(side=tk.BOTTOM, pady=10)

    def _on_select(self, event):
        """Handle simulation selection."""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            sim_name = self.listbox.get(index)
            sim_info = self.simulations[sim_name]

            # Update description
            self.desc_label.config(
                text=f"📝 {sim_name}\n\n{sim_info['description']}"
            )

            # Update equation info
            self._show_relevant_equations(sim_name)

    def _show_relevant_equations(self, sim_name: str):
        """Show relevant equations for selected simulation."""
        equations = {
            '1. Black Hole Dynamics': [
                "Schwarzschild Radius: r_s = 2GM/c²",
                "Hawking Temperature: T = ℏc³/(8πGMk_B)",
                "Event Horizon Area: A = 4πr_s²",
                "Bekenstein-Hawking Entropy: S = k_B×A/(4l_p²)"
            ],
            '2. Spacetime Curvature': [
                "Metric Tensor: g_00 = -(1 - r_s/r)",
                "Time Dilation: τ/t = √(1 - r_s/r)",
                "Geodesic Equation: d²x^μ/dτ² + Γ^μ_αβ(dx^α/dτ)(dx^β/dτ) = 0",
                "Einstein Deflection: α = 4GM/(c²b)"
            ],
            '3. Quantum Foam': [
                "Planck Length: l_p = √(ℏG/c³) ≈ 1.6×10⁻³⁵ m",
                "Planck Time: t_p = l_p/c ≈ 5.4×10⁻⁴⁴ s",
                "Uncertainty: ΔE×Δt ≥ ℏ/2",
                "Virtual Particle Energy: E_virt ~ ℏ/Δt"
            ],
            '4. Big Bang Cosmology': [
                "Hubble Law: v = H_0×d",
                "Friedmann Equation: H² = 8πGρ/3 - k/a²",
                "Scale Factor: a(t) ∝ t^(2/3) (matter-dominated)",
                "CMB Temperature: T_CMB = 2.725 K"
            ],
            '5. Gravitational Waves': [
                "Strain: h = ΔL/L",
                "Quadrupole Formula: P_GW = (G/5c⁵)⟨d³Q_ij/dt³⟩²",
                "Chirp Mass: M_c = (m₁m₂)^(3/5)/(m₁+m₂)^(1/5)",
                "Frequency Evolution: df/dt = (96π/5)(πGM_c/c³)^(5/3)f^(11/3)"
            ],
            '6. Quantum Superposition': [
                "Wavefunction: |ψ⟩ = α|0⟩ + β|1⟩",
                "Probability: P = |⟨φ|ψ⟩|²",
                "Schrödinger: iℏ∂ψ/∂t = Ĥψ",
                "Particle in Box: ψ_n(x) = √(2/L)sin(nπx/L)"
            ],
            '7. Particle Physics': [
                "Strong Force: F_strong = 0.8pn/(p+n)",
                "Weak Force: F_weak = 0.2pe/(p+e)",
                "Decay Rate: λ = ln(2)/t_(1/2)",
                "Cross Section: σ = πr²(interaction radius)"
            ],
            '8. Dark Matter & Energy': [
                "NFW Profile: ρ(r) = ρ_0/[(r/r_s)(1+r/r_s)²]",
                "Dark Energy Density: ρ_Λ = Λc²/(8πG)",
                "Hubble Expansion: H(t) = ȧ/a",
                "Critical Density: ρ_c = 3H²/(8πG)"
            ]
        }

        eq_text = equations.get(sim_name, ["No equations available"])
        self.eq_label.config(text="\n".join(eq_text))

    def _launch_simulation(self):
        """Launch selected simulation."""
        selection = self.listbox.curselection()
        if not selection:
            self.status_label.config(text="⚠ Please select a simulation", fg='#ff0000')
            return

        index = selection[0]
        sim_name = self.listbox.get(index)
        sim_info = self.simulations[sim_name]

        self.status_label.config(text=f"🚀 Launching {sim_name}...", fg='#00ff00')

        # Import and run simulation
        try:
            sim_file = sim_info['file']
            sim_path = Path(__file__).parent / sim_file

            if sim_path.exists():
                # Execute simulation file
                with open(sim_path, 'r') as f:
                    code = f.read()
                exec(code, {'__name__': '__main__'})
            else:
                # Create placeholder
                self._launch_placeholder(sim_name)

        except Exception as e:
            self.status_label.config(text=f"❌ Error: {str(e)}", fg='#ff0000')

    def _launch_placeholder(self, sim_name: str):
        """Launch placeholder for simulations not yet implemented."""
        placeholder = tk.Toplevel(self.root)
        placeholder.title(f"{sim_name} - Coming Soon")
        placeholder.geometry("600x400")
        placeholder.configure(bg='#0a0a0a')

        Label(placeholder, text=f"🚧 {sim_name} 🚧",
              bg='#0a0a0a', fg='#ffaa00',
              font=('Courier', 18, 'bold')).pack(pady=40)

        Label(placeholder, text="This simulation is being implemented using\npure Raphael equations with complete variable scales.",
              bg='#0a0a0a', fg='white',
              font=('Courier', 12), justify=tk.CENTER).pack(pady=20)

        Label(placeholder, text="All calculations will use fundamental physics components\nwith NO external dependencies.",
              bg='#0a0a0a', fg='#00ff88',
              font=('Courier', 10), justify=tk.CENTER).pack(pady=20)

        Button(placeholder, text="Close", command=placeholder.destroy,
               bg='#ff0000', fg='white', font=('Courier', 12)).pack(pady=20)

    def _show_all_stats(self):
        """Show statistics for all simulations."""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Simulation Statistics")
        stats_window.geometry("800x600")
        stats_window.configure(bg='#0a0a0a')

        Label(stats_window, text="📊 SIMULATION STATISTICS 📊",
              bg='#0a0a0a', fg='#00ffff',
              font=('Courier', 16, 'bold')).pack(pady=20)

        # Example calculations
        solar_mass = 1.989e30
        earth_mass = 5.972e24

        stats_text = f"""
BLACK HOLE (1 M☉):
  Schwarzschild Radius: {self.eq.schwarzschild_radius(solar_mass)/1000:.2f} km
  Hawking Temperature: {self.eq.black_hole_temperature(solar_mass):.2e} K
  Evaporation Time: {self.eq.black_hole_evaporation_time(solar_mass)/(365.25*24*3600):.2e} years

QUANTUM SCALES:
  Planck Length: 1.616×10⁻³⁵ m
  Planck Time: 5.391×10⁻⁴⁴ s
  Planck Mass: 2.176×10⁻⁸ kg
  Planck Energy: 1.956×10⁹ J

COSMOLOGY:
  Hubble Constant: ~70 km/s/Mpc
  Age of Universe: ~13.8 billion years
  CMB Temperature: 2.725 K
  Critical Density: ~10⁻²⁶ kg/m³

PARTICLE PHYSICS:
  Electron Mass: {self.eq.const.m_e:.3e} kg
  Proton Mass: {self.eq.const.m_p:.3e} kg
  Fine Structure Constant: {self.eq.const.alpha:.6f}
  Planck Constant: {self.eq.const.h:.3e} J·s
"""

        Label(stats_window, text=stats_text,
              bg='#0a0a0a', fg='#00ff00',
              font=('Courier', 10), justify=tk.LEFT).pack(pady=20)

        Button(stats_window, text="Close", command=stats_window.destroy,
               bg='#ff0000', fg='white').pack(pady=20)

    def _show_equations(self):
        """Show complete equation reference."""
        eq_window = tk.Toplevel(self.root)
        eq_window.title("Raphael Equation Reference")
        eq_window.geometry("900x700")
        eq_window.configure(bg='#0a0a0a')

        Label(eq_window, text="📚 RAPHAEL EQUATION REFERENCE 📚",
              bg='#0a0a0a', fg='#00ffff',
              font=('Courier', 16, 'bold')).pack(pady=20)

        # Create scrollable text
        frame = Frame(eq_window, bg='#1a1a1a')
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        scrollbar = Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text = tk.Text(frame, bg='#1a1a1a', fg='#00ff00',
                      font=('Courier', 9), yscrollcommand=scrollbar.set,
                      wrap=tk.WORD)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)

        # Insert all equations
        equations_text = """
═══════════════════════════════════════════════════════════════
                    FUNDAMENTAL CONSTANTS
═══════════════════════════════════════════════════════════════
Speed of Light: c = 299,792,458 m/s
Planck Constant: h = 6.626×10⁻³⁴ J·s
Reduced Planck: ℏ = h/(2π) = 1.055×10⁻³⁴ J·s
Gravitational Constant: G = 6.674×10⁻¹¹ m³/(kg·s²)
Boltzmann Constant: k_B = 1.381×10⁻²³ J/K
Fine Structure Constant: α = 7.297×10⁻³ ≈ 1/137

═══════════════════════════════════════════════════════════════
                    BLACK HOLE PHYSICS
═══════════════════════════════════════════════════════════════
Schwarzschild Radius:
  r_s = 2GM/c²

Hawking Temperature:
  T = ℏc³/(8πGMk_B)

Bekenstein-Hawking Entropy:
  S = k_B×A/(4l_p²)  where A = 4πr_s²

Evaporation Time:
  t_evap = (5120πG²M³)/(ℏc⁴)

Accretion Disk Temperature:
  T(r) = [3GMṀ/(8πσr³)]^(1/4)

═══════════════════════════════════════════════════════════════
                    GENERAL RELATIVITY
═══════════════════════════════════════════════════════════════
Schwarzschild Metric:
  ds² = -(1-r_s/r)c²dt² + (1-r_s/r)⁻¹dr² + r²dΩ²

Time Dilation:
  τ/t = √(1 - r_s/r)

Gravitational Redshift:
  λ_obs = λ_emit/√(1 - r_s/r)

Einstein Deflection Angle:
  α = 4GM/(c²b)

Einstein Ring Radius:
  θ_E = √[4GM/c² × D_LS/(D_L×D_S)]

═══════════════════════════════════════════════════════════════
                    QUANTUM MECHANICS
═══════════════════════════════════════════════════════════════
Schrödinger Equation:
  iℏ∂ψ/∂t = Ĥψ

Particle in Box Energy:
  E_n = n²π²ℏ²/(2mL²)

Wavefunction (Box):
  ψ_n(x) = √(2/L)sin(nπx/L)

Heisenberg Uncertainty:
  Δx×Δp ≥ ℏ/2
  ΔE×Δt ≥ ℏ/2

Tunneling Probability:
  T ≈ exp(-2κa)  where κ = √[2m(V-E)/ℏ²]

═══════════════════════════════════════════════════════════════
                    COSMOLOGY
═══════════════════════════════════════════════════════════════
Hubble's Law:
  v = H_0×d

Friedmann Equation:
  H² = 8πGρ/3 - kc²/a² + Λc²/3

Critical Density:
  ρ_c = 3H²/(8πG)

Dark Energy Density:
  ρ_Λ = Λc²/(8πG)

Scale Factor (matter-dominated):
  a(t) ∝ t^(2/3)

═══════════════════════════════════════════════════════════════
                    WAVE MECHANICS
═══════════════════════════════════════════════════════════════
Wave Amplitude (spherical):
  A(r) = A_0/r

Wave Phase:
  φ(r,t) = kr - ωt

Wave Number:
  k = 2π/λ

Angular Frequency:
  ω = 2πc/λ

Interference Pattern:
  A_total = √[(Σ A_i cos φ_i)² + (Σ A_i sin φ_i)²]

═══════════════════════════════════════════════════════════════
                    OPTICS (FRESNEL EQUATIONS)
═══════════════════════════════════════════════════════════════
Snell's Law:
  n₁sinθᵢ = n₂sinθₜ

Fresnel Reflection (s-polarization):
  R_s = [(n₁cosθᵢ - n₂cosθₜ)/(n₁cosθᵢ + n₂cosθₜ)]²

Fresnel Reflection (p-polarization):
  R_p = [(n₁cosθₜ - n₂cosθᵢ)/(n₁cosθₜ + n₂cosθᵢ)]²

Brewster Angle:
  θ_B = arctan(n₂/n₁)

Critical Angle:
  θ_c = arcsin(n₂/n₁)  (if n₁ > n₂)

═══════════════════════════════════════════════════════════════
                    DARK MATTER
═══════════════════════════════════════════════════════════════
NFW Density Profile:
  ρ(r) = ρ_0/[(r/r_s)(1 + r/r_s)²]

Rotation Curve (Dark Matter Dominated):
  v² = 4πGρ_0r_s²[ln(1+r/r_s) - r/(r+r_s)]/r

═══════════════════════════════════════════════════════════════
"""

        text.insert(tk.END, equations_text)
        text.config(state=tk.DISABLED)

        Button(eq_window, text="Close", command=eq_window.destroy,
               bg='#ff0000', fg='white', font=('Courier', 12)).pack(pady=10)

    def run(self):
        """Run simulation master."""
        self.root.mainloop()


if __name__ == "__main__":
    print("═══════════════════════════════════════════════════════════")
    print("   RAPHAEL SIMULATION MASTER V0.9.11+ - PURE PYTHON")
    print("═══════════════════════════════════════════════════════════")
    print("\nComplete Physics Simulation Suite:")
    print("  • Black Hole Dynamics")
    print("  • Spacetime Curvature")
    print("  • Quantum Mechanics")
    print("  • Cosmology & Dark Matter/Energy")
    print("\nAll simulations use fundamental Raphael equations")
    print("with complete variable scales and NO external libraries.\n")

    master = SimulationMaster()
    master.run()
