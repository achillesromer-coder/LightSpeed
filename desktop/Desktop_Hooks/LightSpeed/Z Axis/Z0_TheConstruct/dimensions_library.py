"""Physical-dimension and constants reference library for Z0 TheConstruct.

This module is kept as a deterministic reference layer for simulation and
calculator inputs. Oracle owns proofed source knowledge; TheConstruct owns the
simulation-facing dimension and unit references derived from that knowledge.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import math


# ============================================================================
# PHYSICAL DIMENSIONS
# ============================================================================

@dataclass
class PhysicalDimension:
    """
    A physical dimension with units and known values.

    Example:
        mass = PhysicalDimension('Mass', 'm', 'kg', 'Amount of matter', [1.989e30])
    """
    name: str
    symbol: str
    si_unit: str
    description: str
    known_values: List[float] = field(default_factory=list)
    alternative_units: Dict[str, float] = field(default_factory=dict)


# Base SI dimensions
DIMENSIONS = {
    'mass': PhysicalDimension(
        name='Mass',
        symbol='m',
        si_unit='kg',
        description='Amount of matter in an object',
        known_values=[
            9.1093837015e-31,    # Electron mass
            1.67262192369e-27,   # Proton mass
            1.989e30,             # Solar mass
            5.972e24,             # Earth mass
        ],
        alternative_units={
            'g': 0.001,
            'ton': 1000,
            'solar_mass': 1.989e30,
            'earth_mass': 5.972e24,
        }
    ),

    'length': PhysicalDimension(
        name='Length',
        symbol='l',
        si_unit='m',
        description='Spatial extent in one dimension',
        known_values=[
            1.616255e-35,         # Planck length
            5.29177210903e-11,   # Bohr radius
            1.496e11,             # Astronomical unit
            9.461e15,             # Light year
        ],
        alternative_units={
            'mm': 0.001,
            'cm': 0.01,
            'km': 1000,
            'AU': 1.496e11,
            'light_year': 9.461e15,
            'parsec': 3.086e16,
        }
    ),

    'time': PhysicalDimension(
        name='Time',
        symbol='t',
        si_unit='s',
        description='Duration of events',
        known_values=[
            5.391247e-44,         # Planck time
            86400,                # Day
            31557600,             # Year
            4.3e17,               # Age of universe
        ],
        alternative_units={
            'ms': 0.001,
            'min': 60,
            'hour': 3600,
            'day': 86400,
            'year': 31557600,
        }
    ),

    'temperature': PhysicalDimension(
        name='Temperature',
        symbol='T',
        si_unit='K',
        description='Measure of thermal energy',
        known_values=[
            2.725,                # CMB temperature
            5778,                 # Sun surface
            1.417e32,             # Planck temperature
        ],
        alternative_units={
            'celsius': 273.15,    # Offset
            'fahrenheit': 255.372,  # Offset
        }
    ),

    'electric_current': PhysicalDimension(
        name='Electric Current',
        symbol='I',
        si_unit='A',
        description='Flow of electric charge',
        known_values=[],
        alternative_units={
            'mA': 0.001,
            'kA': 1000,
        }
    ),

    'amount_of_substance': PhysicalDimension(
        name='Amount of Substance',
        symbol='n',
        si_unit='mol',
        description='Number of particles (Avogadro number)',
        known_values=[6.02214076e23],  # Avogadro constant
        alternative_units={
            'mmol': 0.001,
            'kmol': 1000,
        }
    ),

    'luminous_intensity': PhysicalDimension(
        name='Luminous Intensity',
        symbol='I_v',
        si_unit='cd',
        description='Luminous power per solid angle',
        known_values=[],
        alternative_units={}
    ),
}


# ============================================================================
# PHYSICAL CONSTANTS
# ============================================================================

@dataclass
class PhysicalConstant:
    """
    A fundamental physical constant.

    Example:
        G = PhysicalConstant('Gravitational constant', 6.67430e-11, 'm³/(kg·s²)', 'gravitation')
    """
    name: str
    value: float
    unit: str
    category: str
    symbol: Optional[str] = None
    uncertainty: Optional[float] = None
    codata_year: int = 2018


# Auto-populated from physics_calculators.RaphaelConstants
CONSTANTS = {
    # Fundamental constants
    'c': PhysicalConstant(
        name='Speed of light in vacuum',
        symbol='c',
        value=299792458,
        unit='m/s',
        category='fundamental',
        uncertainty=0.0,  # Exact by definition
        codata_year=2018
    ),

    'h': PhysicalConstant(
        name='Planck constant',
        symbol='h',
        value=6.62607015e-34,
        unit='J·s',
        category='quantum',
        uncertainty=0.0,  # Exact by definition
        codata_year=2018
    ),

    'hbar': PhysicalConstant(
        name='Reduced Planck constant',
        symbol='ℏ',
        value=6.62607015e-34 / (2.0 * math.pi),
        unit='J·s',
        category='quantum',
        uncertainty=0.0,
        codata_year=2018
    ),

    'G': PhysicalConstant(
        name='Gravitational constant',
        symbol='G',
        value=6.67430e-11,
        unit='m³/(kg·s²)',
        category='gravitation',
        uncertainty=1.5e-5,  # Relative uncertainty
        codata_year=2018
    ),

    'e': PhysicalConstant(
        name='Elementary charge',
        symbol='e',
        value=1.602176634e-19,
        unit='C',
        category='electromagnetic',
        uncertainty=0.0,  # Exact by definition
        codata_year=2018
    ),

    'm_e': PhysicalConstant(
        name='Electron mass',
        symbol='m_e',
        value=9.1093837015e-31,
        unit='kg',
        category='particle',
        uncertainty=3.0e-10,
        codata_year=2018
    ),

    'm_p': PhysicalConstant(
        name='Proton mass',
        symbol='m_p',
        value=1.67262192369e-27,
        unit='kg',
        category='particle',
        uncertainty=3.1e-10,
        codata_year=2018
    ),

    'm_n': PhysicalConstant(
        name='Neutron mass',
        symbol='m_n',
        value=1.67492749804e-27,
        unit='kg',
        category='particle',
        uncertainty=5.7e-10,
        codata_year=2018
    ),

    'k_B': PhysicalConstant(
        name='Boltzmann constant',
        symbol='k_B',
        value=1.380649e-23,
        unit='J/K',
        category='thermodynamic',
        uncertainty=0.0,  # Exact by definition
        codata_year=2018
    ),

    'N_A': PhysicalConstant(
        name='Avogadro constant',
        symbol='N_A',
        value=6.02214076e23,
        unit='mol⁻¹',
        category='thermodynamic',
        uncertainty=0.0,  # Exact by definition
        codata_year=2018
    ),

    'alpha': PhysicalConstant(
        name='Fine-structure constant',
        symbol='α',
        value=7.2973525693e-3,
        unit='dimensionless',
        category='electromagnetic',
        uncertainty=1.5e-10,
        codata_year=2018
    ),

    'epsilon_0': PhysicalConstant(
        name='Vacuum permittivity',
        symbol='ε₀',
        value=8.8541878128e-12,
        unit='F/m',
        category='electromagnetic',
        uncertainty=1.3e-10,
        codata_year=2018
    ),

    'mu_0': PhysicalConstant(
        name='Vacuum permeability',
        symbol='μ₀',
        value=1.25663706212e-6,
        unit='H/m',
        category='electromagnetic',
        uncertainty=1.9e-10,
        codata_year=2018
    ),

    'R': PhysicalConstant(
        name='Gas constant',
        symbol='R',
        value=8.314462618,
        unit='J/(mol·K)',
        category='thermodynamic',
        uncertainty=0.0,
        codata_year=2018
    ),

    'sigma': PhysicalConstant(
        name='Stefan-Boltzmann constant',
        symbol='σ',
        value=5.670374419e-8,
        unit='W/(m²·K⁴)',
        category='thermodynamic',
        uncertainty=0.0,
        codata_year=2018
    ),
}


# Derived/computed constants
DERIVED_CONSTANTS = {
    'l_p': PhysicalConstant(
        name='Planck length',
        symbol='l_P',
        value=math.sqrt(CONSTANTS['hbar'].value * CONSTANTS['G'].value / CONSTANTS['c'].value**3),
        unit='m',
        category='planck_units'
    ),

    't_p': PhysicalConstant(
        name='Planck time',
        symbol='t_P',
        value=math.sqrt(CONSTANTS['hbar'].value * CONSTANTS['G'].value / CONSTANTS['c'].value**5),
        unit='s',
        category='planck_units'
    ),

    'm_p_planck': PhysicalConstant(
        name='Planck mass',
        symbol='m_P',
        value=math.sqrt(CONSTANTS['hbar'].value * CONSTANTS['c'].value / CONSTANTS['G'].value),
        unit='kg',
        category='planck_units'
    ),

    'T_p': PhysicalConstant(
        name='Planck temperature',
        symbol='T_P',
        value=math.sqrt(CONSTANTS['hbar'].value * CONSTANTS['c'].value**5 / (CONSTANTS['G'].value * CONSTANTS['k_B'].value**2)),
        unit='K',
        category='planck_units'
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_constant(symbol: str) -> Optional[PhysicalConstant]:
    """Get a physical constant by its symbol"""
    const = CONSTANTS.get(symbol)
    if const:
        return const
    return DERIVED_CONSTANTS.get(symbol)


def get_dimension(name: str) -> Optional[PhysicalDimension]:
    """Get a physical dimension by name"""
    return DIMENSIONS.get(name.lower())


def convert_unit(value: float, from_unit: str, to_unit: str, dimension: str) -> float:
    """
    Convert between units of the same dimension.

    Example:
        convert_unit(1, 'km', 'm', 'length')  # Returns 1000
    """
    dim = get_dimension(dimension)
    if not dim:
        raise ValueError(f"Unknown dimension: {dimension}")

    if from_unit == dim.si_unit:
        from_factor = 1.0
    else:
        from_factor = dim.alternative_units.get(from_unit)
        if from_factor is None:
            raise ValueError(f"Unknown unit {from_unit} for dimension {dimension}")

    if to_unit == dim.si_unit:
        to_factor = 1.0
    else:
        to_factor = dim.alternative_units.get(to_unit)
        if to_factor is None:
            raise ValueError(f"Unknown unit {to_unit} for dimension {dimension}")

    # Convert to SI, then to target unit
    si_value = value * from_factor
    result = si_value / to_factor

    return result


def list_constants_by_category(category: str) -> List[PhysicalConstant]:
    """Get all constants in a specific category"""
    result = []
    for const in CONSTANTS.values():
        if const.category == category:
            result.append(const)
    for const in DERIVED_CONSTANTS.values():
        if const.category == category:
            result.append(const)
    return result


def search_constants(query: str) -> List[PhysicalConstant]:
    """Search constants by name or symbol"""
    query = query.lower()
    results = []

    for symbol, const in CONSTANTS.items():
        if query in symbol.lower() or query in const.name.lower():
            results.append(const)

    for symbol, const in DERIVED_CONSTANTS.items():
        if query in symbol.lower() or query in const.name.lower():
            results.append(const)

    return results


# ============================================================================
# AUTO-DISCOVERY FROM DOCUMENTS
# ============================================================================

def update_from_document_ingestion(ingestion_summary: Dict[str, Any]):
    """
    Update dimensions and constants from document ingestion results.

    This is called after Oracle ingests all documents to populate
    known values and discover new dimensions.
    """
    dimensions_found = ingestion_summary.get('dimensions_found', [])
    constants_found = ingestion_summary.get('constants_found', [])

    print(f"[DimensionsLibrary] Updating from ingestion:")
    print(f"  - {len(dimensions_found)} dimensions discovered")
    print(f"  - {len(constants_found)} constants discovered")

    # Add discovered values to existing dimensions
    for dim_data in dimensions_found:
        dim_name = dim_data.get('name', '').lower()
        value = dim_data.get('value')

        if dim_name in DIMENSIONS and value:
            dim = DIMENSIONS[dim_name]
            if value not in dim.known_values:
                dim.known_values.append(value)
                print(f"  + Added {value} to {dim.name}")

    # Add newly discovered constants (if not already in CONSTANTS)
    for const_data in constants_found:
        symbol = const_data.get('symbol')
        if symbol and symbol not in CONSTANTS and symbol not in DERIVED_CONSTANTS:
            new_const = PhysicalConstant(
                name=const_data.get('name', f'Constant {symbol}'),
                symbol=symbol,
                value=const_data.get('value', 0.0),
                unit=const_data.get('unit', ''),
                category='discovered'
            )
            DERIVED_CONSTANTS[symbol] = new_const
            print(f"  + New constant: {symbol} = {new_const.value} {new_const.unit}")


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'PhysicalDimension',
    'PhysicalConstant',
    'DIMENSIONS',
    'CONSTANTS',
    'DERIVED_CONSTANTS',
    'get_constant',
    'get_dimension',
    'convert_unit',
    'list_constants_by_category',
    'search_constants',
    'update_from_document_ingestion',
]


if __name__ == '__main__':
    # Demo
    print("=" * 70)
    print("LIGHTSPEED DIMENSIONS & CONSTANTS LIBRARY")
    print("=" * 70)

    print("\nPhysical Dimensions:")
    for name, dim in DIMENSIONS.items():
        print(f"  {dim.name} ({dim.symbol}): {dim.si_unit}")
        print(f"    {dim.description}")
        if dim.known_values:
            print(f"    Known values: {len(dim.known_values)}")

    print("\nFundamental Constants:")
    fundamental = list_constants_by_category('fundamental')
    for const in fundamental:
        print(f"  {const.symbol}: {const.value} {const.unit}")
        print(f"    {const.name}")

    print("\nPlanck Units:")
    planck = list_constants_by_category('planck_units')
    for const in planck:
        print(f"  {const.symbol}: {const.value:.6e} {const.unit}")

    print("\nUnit Conversion Example:")
    km_in_m = convert_unit(5, 'km', 'm', 'length')
    print(f"  5 km = {km_in_m} m")

    print("\nConstant Search Example:")
    results = search_constants('mass')
    print(f"  Search 'mass': {len(results)} results")
    for const in results:
        print(f"    - {const.name} ({const.symbol})")

    print("\n" + "=" * 70)
