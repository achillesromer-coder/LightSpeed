"""LightSpeed physics calculator library for Z0 TheConstruct.

This file is an active Construct-owned scientific library used by the root
Construct coordinator and Trinity context actions. Keep user-facing orchestration
in the runtime/coordination layer; keep this module focused on deterministic
calculators and explicit physical constants.
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════════════════════
# PHYSICAL CONSTANTS (Raphael Pure Engine)
# ═══════════════════════════════════════════════════════════════════════════

class RaphaelConstants:
    """Fundamental physical constants - SI units"""

    # Gravitational
    G = 6.67430e-11  # Gravitational constant (m³ kg⁻¹ s⁻²)

    # Electromagnetic
    c = 299792458  # Speed of light in vacuum (m/s)
    epsilon_0 = 8.8541878128e-12  # Vacuum permittivity (F/m)
    mu_0 = 1.25663706212e-6  # Vacuum permeability (H/m)

    # Quantum
    h = 6.62607015e-34  # Planck constant (J⋅s)
    hbar = h / (2 * math.pi)  # Reduced Planck constant
    e = 1.602176634e-19  # Elementary charge (C)
    m_e = 9.1093837015e-31  # Electron mass (kg)

    # Thermodynamic
    k_B = 1.380649e-23  # Boltzmann constant (J/K)
    sigma = 5.670374419e-8  # Stefan-Boltzmann constant (W m⁻² K⁻⁴)
    R = 8.314462618  # Gas constant (J mol⁻¹ K⁻¹)

    # Astronomical
    M_sun = 1.98892e30  # Solar mass (kg)
    AU = 1.495978707e11  # Astronomical unit (m)
    pc = 3.0856775814671916e16  # Parsec (m)

    # Cosmological
    H_0 = 2.197e-18  # Hubble constant (s⁻¹) ~67.4 km/s/Mpc


# ═══════════════════════════════════════════════════════════════════════════
# CALCULATION RESULT DATA STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CalculationResult:
    """Standardized calculation result"""
    function_name: str
    inputs: Dict[str, float]
    result: float
    unit: str
    formula: str
    interpretation: str
    category: str
    floor: str = "Z0_TheConstruct"


# ═══════════════════════════════════════════════════════════════════════════
# GRAVITATION CALCULATIONS (Category 1)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_schwarzschild_radius(mass: float) -> CalculationResult:
    """
    Calculate Schwarzschild radius (event horizon) of a black hole

    Args:
        mass: Mass of black hole in kg (e.g., 1.989e30 for 1 solar mass)

    Returns:
        CalculationResult with radius in meters
    """
    r_s = (2 * RaphaelConstants.G * mass) / (RaphaelConstants.c ** 2)

    # Interpretation
    solar_masses = mass / RaphaelConstants.M_sun
    interpretation = f"A black hole of {solar_masses:.2e} solar masses has an event horizon at {r_s/1000:.2f} km"

    return CalculationResult(
        function_name="calculate_schwarzschild_radius",
        inputs={"mass": mass},
        result=r_s,
        unit="meters",
        formula="r_s = 2GM/c²",
        interpretation=interpretation,
        category="gravitation"
    )


def calculate_hawking_temperature(mass: float) -> CalculationResult:
    """
    Calculate Hawking temperature of a black hole

    Args:
        mass: Mass of black hole in kg

    Returns:
        CalculationResult with temperature in Kelvin
    """
    # T = ℏc³ / (8πGMk_B)
    T = (RaphaelConstants.hbar * RaphaelConstants.c ** 3) / \
        (8 * math.pi * RaphaelConstants.G * mass * RaphaelConstants.k_B)

    solar_masses = mass / RaphaelConstants.M_sun
    interpretation = f"Black hole of {solar_masses:.2e} solar masses emits Hawking radiation at {T:.2e} K"

    return CalculationResult(
        function_name="calculate_hawking_temperature",
        inputs={"mass": mass},
        result=T,
        unit="Kelvin",
        formula="T = ℏc³/(8πGMk_B)",
        interpretation=interpretation,
        category="thermodynamics"
    )


def calculate_time_dilation(mass: float, distance: float) -> CalculationResult:
    """
    Calculate gravitational time dilation near a massive object

    Args:
        mass: Mass of gravitational source (kg)
        distance: Distance from center of mass (m)

    Returns:
        CalculationResult with time dilation factor (1 = no dilation)
    """
    r_s = (2 * RaphaelConstants.G * mass) / (RaphaelConstants.c ** 2)

    if distance <= r_s:
        factor = 0.0  # Inside event horizon - time stops
        interpretation = "Inside event horizon - time dilation infinite"
    else:
        factor = math.sqrt(1 - (r_s / distance))
        percent = (1 - factor) * 100
        interpretation = f"Time dilated by {percent:.4f}% at {distance/1000:.0f} km from center"

    return CalculationResult(
        function_name="calculate_time_dilation",
        inputs={"mass": mass, "distance": distance},
        result=factor,
        unit="dimensionless",
        formula="t' = t√(1 - r_s/r)",
        interpretation=interpretation,
        category="relativity"
    )


def calculate_einstein_ring(lens_mass: float, source_dist: float, lens_dist: float) -> CalculationResult:
    """
    Calculate Einstein ring radius for gravitational lensing

    Args:
        lens_mass: Mass of lensing object (kg)
        source_dist: Distance to background source (m)
        lens_dist: Distance to lens (m)

    Returns:
        CalculationResult with angular radius in radians
    """
    # θ_E = √(4GM/c² * D_LS/(D_L * D_S))
    D_LS = source_dist - lens_dist  # Lens to source distance

    theta_E = math.sqrt(
        (4 * RaphaelConstants.G * lens_mass / RaphaelConstants.c ** 2) *
        (D_LS / (lens_dist * source_dist))
    )

    # Convert to arc seconds for interpretation
    theta_arcsec = theta_E * 206265

    interpretation = f"Einstein ring radius: {theta_arcsec:.4f} arcseconds"

    return CalculationResult(
        function_name="calculate_einstein_ring",
        inputs={"lens_mass": lens_mass, "source_dist": source_dist, "lens_dist": lens_dist},
        result=theta_E,
        unit="radians",
        formula="θ_E = √(4GM/c² · D_LS/(D_L·D_S))",
        interpretation=interpretation,
        category="relativity"
    )


def calculate_orbital_velocity(mass: float, radius: float) -> CalculationResult:
    """
    Calculate orbital velocity around a massive object

    Args:
        mass: Mass of central object (kg)
        radius: Orbital radius (m)

    Returns:
        CalculationResult with velocity in m/s
    """
    v = math.sqrt(RaphaelConstants.G * mass / radius)

    v_km_s = v / 1000
    interpretation = f"Orbital velocity at {radius/1000:.0f} km: {v_km_s:.2f} km/s"

    return CalculationResult(
        function_name="calculate_orbital_velocity",
        inputs={"mass": mass, "radius": radius},
        result=v,
        unit="m/s",
        formula="v = √(GM/r)",
        interpretation=interpretation,
        category="gravitation"
    )


def calculate_escape_velocity(mass: float, radius: float) -> CalculationResult:
    """
    Calculate escape velocity from a massive object

    Args:
        mass: Mass of object (kg)
        radius: Distance from center (m)

    Returns:
        CalculationResult with velocity in m/s
    """
    v_esc = math.sqrt(2 * RaphaelConstants.G * mass / radius)

    v_km_s = v_esc / 1000
    interpretation = f"Escape velocity from {radius/1000:.0f} km: {v_km_s:.2f} km/s"

    return CalculationResult(
        function_name="calculate_escape_velocity",
        inputs={"mass": mass, "radius": radius},
        result=v_esc,
        unit="m/s",
        formula="v_esc = √(2GM/r)",
        interpretation=interpretation,
        category="gravitation"
    )


# ═══════════════════════════════════════════════════════════════════════════
# QUANTUM MECHANICS CALCULATIONS (Category 2)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_quantum_energy(n: int, mass: float, length: float) -> CalculationResult:
    """
    Calculate energy level for particle in a box

    Args:
        n: Quantum number (1, 2, 3, ...)
        mass: Particle mass (kg)
        length: Box length (m)

    Returns:
        CalculationResult with energy in Joules
    """
    E = (n ** 2 * RaphaelConstants.h ** 2) / (8 * mass * length ** 2)

    # Convert to eV for interpretation
    E_eV = E / RaphaelConstants.e

    interpretation = f"Quantum state n={n}: Energy = {E_eV:.2e} eV"

    return CalculationResult(
        function_name="calculate_quantum_energy",
        inputs={"n": float(n), "mass": mass, "length": length},
        result=E,
        unit="Joules",
        formula="E_n = n²h²/(8mL²)",
        interpretation=interpretation,
        category="quantum_mechanics"
    )


def calculate_tunneling_probability(width: float, height: float, energy: float, mass: float) -> CalculationResult:
    """
    Calculate quantum tunneling probability through a barrier

    Args:
        width: Barrier width (m)
        height: Barrier height (J)
        energy: Particle energy (J)
        mass: Particle mass (kg)

    Returns:
        CalculationResult with probability (0-1)
    """
    if energy >= height:
        T = 1.0
        interpretation = "Particle energy exceeds barrier - classical passage (T=1)"
    else:
        # κ = √(2m(V-E))/ℏ
        kappa = math.sqrt(2 * mass * (height - energy)) / RaphaelConstants.hbar

        # T ≈ e^(-2κa)
        T = math.exp(-2 * kappa * width)

        percent = T * 100
        interpretation = f"Tunneling probability: {percent:.4e}% through {width*1e9:.2f} nm barrier"

    return CalculationResult(
        function_name="calculate_tunneling_probability",
        inputs={"width": width, "height": height, "energy": energy, "mass": mass},
        result=T,
        unit="probability",
        formula="T ≈ e^(-2κa), κ=√(2m(V-E))/ℏ",
        interpretation=interpretation,
        category="quantum_mechanics"
    )


def calculate_de_broglie_wavelength(mass: float, velocity: float) -> CalculationResult:
    """
    Calculate de Broglie wavelength of a particle

    Args:
        mass: Particle mass (kg)
        velocity: Particle velocity (m/s)

    Returns:
        CalculationResult with wavelength in meters
    """
    # λ = h/(mv)
    momentum = mass * velocity
    wavelength = RaphaelConstants.h / momentum

    interpretation = f"de Broglie wavelength: {wavelength*1e9:.2e} nm at v={velocity} m/s"

    return CalculationResult(
        function_name="calculate_de_broglie_wavelength",
        inputs={"mass": mass, "velocity": velocity},
        result=wavelength,
        unit="meters",
        formula="λ = h/(mv)",
        interpretation=interpretation,
        category="quantum_mechanics"
    )


# ═══════════════════════════════════════════════════════════════════════════
# COSMOLOGY CALCULATIONS (Category 3)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_hubble_distance(recession_velocity: float) -> CalculationResult:
    """
    Calculate distance to galaxy using Hubble's Law

    Args:
        recession_velocity: Recession velocity (m/s)

    Returns:
        CalculationResult with distance in meters
    """
    # d = v/H_0
    distance = recession_velocity / RaphaelConstants.H_0

    # Convert to Mpc for interpretation
    distance_Mpc = distance / RaphaelConstants.pc / 1e6

    interpretation = f"Galaxy distance: {distance_Mpc:.2f} Mpc (v={recession_velocity/1000:.0f} km/s)"

    return CalculationResult(
        function_name="calculate_hubble_distance",
        inputs={"recession_velocity": recession_velocity},
        result=distance,
        unit="meters",
        formula="d = v/H₀",
        interpretation=interpretation,
        category="cosmology"
    )


def calculate_dark_matter_density(radius: float, core_radius: float, central_density: float) -> CalculationResult:
    """
    Calculate dark matter density using NFW profile

    Args:
        radius: Distance from galactic center (m)
        core_radius: Core radius of halo (m)
        central_density: Central density (kg/m³)

    Returns:
        CalculationResult with density in kg/m³
    """
    # NFW profile: ρ(r) = ρ_0 / (r/r_s · (1 + r/r_s)²)
    x = radius / core_radius
    rho = central_density / (x * (1 + x) ** 2)

    interpretation = f"Dark matter density at r={radius/1000:.0f} km: {rho:.2e} kg/m³"

    return CalculationResult(
        function_name="calculate_dark_matter_density",
        inputs={"radius": radius, "core_radius": core_radius, "central_density": central_density},
        result=rho,
        unit="kg/m³",
        formula="ρ(r) = ρ₀/(x(1+x)²), x=r/r_s",
        interpretation=interpretation,
        category="cosmology"
    )


def calculate_critical_density(hubble_rate: float) -> CalculationResult:
    """
    Calculate critical density of the universe

    Args:
        hubble_rate: Hubble rate (s⁻¹)

    Returns:
        CalculationResult with density in kg/m³
    """
    # ρ_c = 3H²/(8πG)
    rho_c = (3 * hubble_rate ** 2) / (8 * math.pi * RaphaelConstants.G)

    interpretation = f"Critical density: {rho_c:.2e} kg/m³ (flat universe)"

    return CalculationResult(
        function_name="calculate_critical_density",
        inputs={"hubble_rate": hubble_rate},
        result=rho_c,
        unit="kg/m³",
        formula="ρ_c = 3H²/(8πG)",
        interpretation=interpretation,
        category="cosmology"
    )


# ═══════════════════════════════════════════════════════════════════════════
# CALCULATOR REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

PHYSICS_CALCULATORS = {
    # Gravitation
    "schwarzschild_radius": calculate_schwarzschild_radius,
    "hawking_temperature": calculate_hawking_temperature,
    "time_dilation": calculate_time_dilation,
    "einstein_ring": calculate_einstein_ring,
    "orbital_velocity": calculate_orbital_velocity,
    "escape_velocity": calculate_escape_velocity,

    # Quantum Mechanics
    "quantum_energy": calculate_quantum_energy,
    "tunneling_probability": calculate_tunneling_probability,
    "de_broglie_wavelength": calculate_de_broglie_wavelength,

    # Cosmology
    "hubble_distance": calculate_hubble_distance,
    "dark_matter_density": calculate_dark_matter_density,
    "critical_density": calculate_critical_density,
}


def get_calculator(name: str):
    """Get calculator function by name"""
    return PHYSICS_CALCULATORS.get(name)


def list_calculators() -> List[str]:
    """List all available calculators"""
    return list(PHYSICS_CALCULATORS.keys())


def get_calculators_by_category(category: str) -> List[str]:
    """Get calculators in a specific category"""
    # This would need metadata - simplified for now
    categories = {
        "gravitation": ["schwarzschild_radius", "hawking_temperature", "time_dilation",
                       "einstein_ring", "orbital_velocity", "escape_velocity"],
        "quantum_mechanics": ["quantum_energy", "tunneling_probability", "de_broglie_wavelength"],
        "cosmology": ["hubble_distance", "dark_matter_density", "critical_density"]
    }
    return categories.get(category, [])
