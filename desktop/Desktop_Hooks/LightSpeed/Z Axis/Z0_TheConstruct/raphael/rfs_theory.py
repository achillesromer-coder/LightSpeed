"""
RFS (Resonant Field Suppression) Theory Module
Electromagnetic frequency-based asteroid material extraction

Core IP: EMASSC / Römer Industries
Patent Status: Filed
Conversations: 150+ archived
"""

import numpy as np
from scipy.constants import c, epsilon_0, mu_0, e

# RFS Constants
RHO_CU = 1.68e-8  # Copper resistivity (Ω·m)
MU0 = mu_0  # Permeability of free space
EPSILON0 = epsilon_0  # Permittivity of free space

# Typical asteroid material properties
ASTEROID_MATERIALS = {
    "iron": {"conductivity": 1.0e7, "density": 7874, "resonance_mhz": 2450},
    "nickel": {"conductivity": 1.43e7, "density": 8908, "resonance_mhz": 2380},
    "platinum": {"conductivity": 9.43e6, "density": 21450, "resonance_mhz": 3100},
    "water_ice": {"conductivity": 1e-6, "density": 917, "resonance_mhz": 22500},
    "silicate": {"conductivity": 1e-12, "density": 2650, "resonance_mhz": 915},
}

def calculate_resonant_frequency(material_type, geometry="sphere", size_m=1.0):
    """
    Calculate optimal resonant frequency for material extraction

    RFS uses electromagnetic resonance to selectively vibrate and
    separate materials based on their conductivity and structure.

    Parameters:
    -----------
    material_type : str
        Material name (iron, nickel, platinum, etc.)
    geometry : str
        Particle geometry (sphere, cylinder, plate)
    size_m : float
        Characteristic dimension (m)

    Returns:
    --------
    dict : Resonant frequency and extraction parameters
    """
    if material_type not in ASTEROID_MATERIALS:
        raise ValueError(f"Unknown material: {material_type}")

    material = ASTEROID_MATERIALS[material_type]

    # Base resonant frequency (from material properties)
    f_base = material['resonance_mhz'] * 1e6  # Convert to Hz

    # Geometry factor
    geometry_factors = {"sphere": 1.0, "cylinder": 0.85, "plate": 1.2}
    g_factor = geometry_factors.get(geometry, 1.0)

    # Size correction (smaller particles resonate at higher frequencies)
    f_resonant = f_base * g_factor * (0.01 / size_m)**0.5

    # Skin depth (penetration of EM field)
    sigma = material['conductivity']
    delta = np.sqrt(2 / (2 * np.pi * f_resonant * MU0 * sigma))

    # Quality factor (how sharp the resonance is)
    Q_factor = 2 * np.pi * f_resonant * delta / c

    return {
        'resonant_frequency_hz': f_resonant,
        'resonant_frequency_mhz': f_resonant / 1e6,
        'skin_depth_m': delta,
        'skin_depth_mm': delta * 1000,
        'q_factor': Q_factor,
        'conductivity': sigma,
        'density_kg_m3': material['density']
    }

def extraction_rate(power_kw, material_type, target_mass_kg, efficiency=0.75):
    """
    Estimate material extraction rate using RFS

    Parameters:
    -----------
    power_kw : float
        Applied electromagnetic power (kW)
    material_type : str
        Target material
    target_mass_kg : float
        Total mass to extract (kg)
    efficiency : float
        System efficiency (0 to 1)

    Returns:
    --------
    dict : Extraction rate and time estimates
    """
    material = ASTEROID_MATERIALS[material_type]
    density = material['density']

    # Energy per kg (empirical from RFS tests)
    # Higher conductivity materials extract more efficiently
    energy_per_kg_kwh = 50 / (material['conductivity'] / 1e6)

    # Extraction rate (kg/hour)
    rate_kg_hr = (power_kw * efficiency) / energy_per_kg_kwh

    # Time to extract target mass
    time_hours = target_mass_kg / rate_kg_hr

    # Power cost (at $0.08/kWh in space - solar power)
    power_cost = time_hours * power_kw * 0.08

    return {
        'extraction_rate_kg_hr': rate_kg_hr,
        'extraction_rate_kg_day': rate_kg_hr * 24,
        'time_to_extract_hours': time_hours,
        'time_to_extract_days': time_hours / 24,
        'total_energy_kwh': power_kw * time_hours,
        'power_cost_usd': power_cost,
        'efficiency': efficiency
    }

def emf_field_strength(power_w, distance_m, frequency_hz):
    """
    Calculate electromagnetic field strength at distance

    Parameters:
    -----------
    power_w : float
        Transmitter power (W)
    distance_m : float
        Distance from transmitter (m)
    frequency_hz : float
        Operating frequency (Hz)

    Returns:
    --------
    dict : Electric and magnetic field strengths
    """
    # Free space impedance
    Z0 = np.sqrt(MU0 / EPSILON0)

    # Wavelength
    wavelength = c / frequency_hz

    # Power density (W/m²)
    S = power_w / (4 * np.pi * distance_m**2)

    # Electric field (V/m)
    E = np.sqrt(S * Z0)

    # Magnetic field (A/m)
    H = E / Z0

    # Magnetic flux density (T)
    B = MU0 * H

    return {
        'power_density_w_m2': S,
        'electric_field_v_m': E,
        'magnetic_field_a_m': H,
        'magnetic_flux_density_t': B,
        'wavelength_m': wavelength,
        'is_safe_for_equipment': E < 1000  # Safety threshold
    }

def asteroid_composition_analysis(rfs_response):
    """
    Analyze asteroid composition from RFS spectral response

    Different materials respond differently to EM frequencies,
    creating a unique spectral signature.

    Parameters:
    -----------
    rfs_response : dict
        Frequency response data {freq_hz: amplitude}

    Returns:
    --------
    dict : Estimated composition percentages
    """
    # Simplified composition analysis
    # Real implementation would use machine learning on spectral data

    composition = {}
    total_response = sum(rfs_response.values())

    # Identify peaks in response spectrum
    frequencies = sorted(rfs_response.keys())
    amplitudes = [rfs_response[f] for f in frequencies]

    # Match peaks to known material resonances
    for material, props in ASTEROID_MATERIALS.items():
        target_freq = props['resonance_mhz'] * 1e6

        # Find closest frequency in response
        closest_idx = min(range(len(frequencies)),
                         key=lambda i: abs(frequencies[i] - target_freq))

        # Estimate percentage from amplitude
        if amplitudes[closest_idx] > 0.1 * max(amplitudes):
            composition[material] = (amplitudes[closest_idx] / total_response) * 100

    return composition

def mark_iii_extraction_sim(asteroid_mass_kg, composition, power_kw=15):
    """
    Simulate Mark III mining unit extraction performance

    Parameters:
    -----------
    asteroid_mass_kg : float
        Total asteroid mass (kg)
    composition : dict
        Material composition {material: percentage}
    power_kw : float
        Mark III power output (kW)

    Returns:
    --------
    dict : Extraction simulation results
    """
    results = {}
    total_time_hours = 0
    total_value_usd = 0

    # Material values ($/kg)
    material_values = {
        "iron": 0.5,
        "nickel": 15,
        "platinum": 30000,
        "water_ice": 1000,  # High value in space!
        "silicate": 0.1
    }

    for material, percentage in composition.items():
        mass_kg = asteroid_mass_kg * (percentage / 100)

        extraction = extraction_rate(power_kw, material, mass_kg)

        value = mass_kg * material_values.get(material, 0)
        total_value_usd += value

        results[material] = {
            'mass_kg': mass_kg,
            'extraction_time_days': extraction['time_to_extract_days'],
            'value_usd': value,
            'extraction_details': extraction
        }

        total_time_hours += extraction['time_to_extract_hours']

    return {
        'materials': results,
        'total_time_days': total_time_hours / 24,
        'total_value_usd': total_value_usd,
        'total_mass_kg': asteroid_mass_kg,
        'average_rate_kg_day': asteroid_mass_kg / (total_time_hours / 24),
        'roi_ratio': total_value_usd / (power_kw * total_time_hours * 0.08)  # Value / power cost
    }

if __name__ == '__main__':
    print("=== RFS Theory Module Test ===\n")

    # Test resonant frequency calculation
    print("Resonant Frequency for Platinum:")
    platinum_rfs = calculate_resonant_frequency("platinum", "sphere", 0.001)
    print(f"  Frequency: {platinum_rfs['resonant_frequency_mhz']:.2f} MHz")
    print(f"  Skin depth: {platinum_rfs['skin_depth_mm']:.4f} mm")
    print(f"  Q-factor: {platinum_rfs['q_factor']:.2f}")

    # Test extraction rate
    print("\n=== Mark III Extraction Test ===")
    extraction = extraction_rate(15, "platinum", 100, efficiency=0.78)
    print(f"  Power: 15 kW")
    print(f"  Target: 100 kg platinum")
    print(f"  Rate: {extraction['extraction_rate_kg_hr']:.2f} kg/hr")
    print(f"  Time: {extraction['time_to_extract_days']:.2f} days")
    print(f"  Energy: {extraction['total_energy_kwh']:.2f} kWh")
    print(f"  Cost: ${extraction['power_cost_usd']:.2f}")

    # Test asteroid simulation (2m³ example)
    print("\n=== 2m³ Asteroid Simulation ===")
    # Typical density ~3000 kg/m³
    asteroid_mass = 2 * 3000  # 6000 kg
    composition = {
        "iron": 40,
        "nickel": 25,
        "platinum": 0.01,
        "silicate": 34.99
    }

    sim = mark_iii_extraction_sim(asteroid_mass, composition, power_kw=15)
    print(f"  Total mass: {sim['total_mass_kg']:.0f} kg")
    print(f"  Extraction time: {sim['total_time_days']:.2f} days")
    print(f"  Total value: ${sim['total_value_usd']:,.2f}")
    print(f"  ROI ratio: {sim['roi_ratio']:.2f}x")
    print(f"  Average rate: {sim['average_rate_kg_day']:.2f} kg/day")

    print("\n  Material breakdown:")
    for material, data in sim['materials'].items():
        if data['mass_kg'] > 0.1:
            print(f"    {material}: {data['mass_kg']:.2f} kg, ${data['value_usd']:,.2f}, {data['extraction_time_days']:.2f} days")

    print("\nRFS theory module ready!")
