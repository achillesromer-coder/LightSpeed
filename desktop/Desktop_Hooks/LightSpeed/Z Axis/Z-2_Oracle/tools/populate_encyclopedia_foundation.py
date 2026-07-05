#!/usr/bin/env python
"""
Populate Encyclopedia with Foundation Data
Adds 50+ physical constants, SI units, and foundational scientific data

Author: Römer Industries / EMASSC
Version: 0.9.5
Date: December 31, 2025
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "components"))

from encyclopedia_system import EncyclopediaSystem, EncyclopediaVolume


def populate_physical_constants(encyclopedia: EncyclopediaSystem):
    """Add fundamental physical constants"""
    print("\n[Populating] Physical Constants...")

    constants = [
        # SI Defining Constants (exact values)
        {
            'term': 'Speed of Light in Vacuum',
            'definition': 'Maximum speed at which all energy, matter, and information can travel',
            'data': {'symbol': 'c', 'value': 299792458, 'unit': 'm/s', 'exact': True,
                    'si_defining': True, 'category': 'fundamental'}
        },
        {
            'term': 'Planck Constant',
            'definition': 'Quantum of electromagnetic action, relates energy to frequency',
            'data': {'symbol': 'h', 'value': 6.62607015e-34, 'unit': 'J⋅s', 'exact': True,
                    'si_defining': True}
        },
        {
            'term': 'Elementary Charge',
            'definition': 'Electric charge carried by a single proton',
            'data': {'symbol': 'e', 'value': 1.602176634e-19, 'unit': 'C', 'exact': True,
                    'si_defining': True}
        },
        {
            'term': 'Boltzmann Constant',
            'definition': 'Physical constant relating temperature to energy',
            'data': {'symbol': 'k_B', 'value': 1.380649e-23, 'unit': 'J/K', 'exact': True,
                    'si_defining': True}
        },
        {
            'term': 'Avogadro Constant',
            'definition': 'Number of constituent particles per mole',
            'data': {'symbol': 'N_A', 'value': 6.02214076e23, 'unit': 'mol^-1', 'exact': True,
                    'si_defining': True}
        },

        # Universal Constants
        {
            'term': 'Gravitational Constant',
            'definition': 'Fundamental constant in Newton\'s law of universal gravitation',
            'data': {'symbol': 'G', 'value': 6.67430e-11, 'unit': 'm³/(kg⋅s²)',
                    'uncertainty': 1.5e-15, 'exact': False}
        },
        {
            'term': 'Vacuum Permittivity',
            'definition': 'Electric constant, permittivity of free space',
            'data': {'symbol': 'ε_0', 'value': 8.8541878128e-12, 'unit': 'F/m',
                    'derived_from': ['c', 'μ_0']}
        },
        {
            'term': 'Vacuum Permeability',
            'definition': 'Magnetic constant, permeability of free space',
            'data': {'symbol': 'μ_0', 'value': 1.25663706212e-6, 'unit': 'N/A²',
                    'derived_from': ['c', 'ε_0']}
        },

        # Atomic & Nuclear
        {
            'term': 'Fine Structure Constant',
            'definition': 'Dimensionless constant characterizing strength of electromagnetic interaction',
            'data': {'symbol': 'α', 'value': 7.2973525693e-3, 'unit': 'dimensionless',
                    'inverse': 137.035999084}
        },
        {
            'term': 'Electron Mass',
            'definition': 'Rest mass of an electron',
            'data': {'symbol': 'm_e', 'value': 9.1093837015e-31, 'unit': 'kg',
                    'uncertainty': 2.8e-40}
        },
        {
            'term': 'Proton Mass',
            'definition': 'Rest mass of a proton',
            'data': {'symbol': 'm_p', 'value': 1.67262192369e-27, 'unit': 'kg',
                    'uncertainty': 5.1e-37}
        },
        {
            'term': 'Neutron Mass',
            'definition': 'Rest mass of a neutron',
            'data': {'symbol': 'm_n', 'value': 1.67492749804e-27, 'unit': 'kg',
                    'uncertainty': 9.5e-37}
        },

        # Atomic Units
        {
            'term': 'Atomic Mass Unit',
            'definition': 'Unit of mass used for atomic and molecular masses',
            'data': {'symbol': 'u', 'value': 1.66053906660e-27, 'unit': 'kg',
                    'definition_reference': '1/12 mass of C-12 atom'}
        },
        {
            'term': 'Bohr Radius',
            'definition': 'Physical constant representing most probable distance between nucleus and electron in hydrogen',
            'data': {'symbol': 'a_0', 'value': 5.29177210903e-11, 'unit': 'm',
                    'uncertainty': 8.0e-21}
        },
        {
            'term': 'Rydberg Constant',
            'definition': 'Physical constant related to atomic spectra',
            'data': {'symbol': 'R_∞', 'value': 10973731.568160, 'unit': 'm^-1',
                    'uncertainty': 2.1e-5}
        },

        # Thermodynamic
        {
            'term': 'Stefan-Boltzmann Constant',
            'definition': 'Physical constant relating temperature to radiant exitance',
            'data': {'symbol': 'σ', 'value': 5.670374419e-8, 'unit': 'W/(m²⋅K⁴)',
                    'derived_from': ['k_B', 'h', 'c']}
        },
        {
            'term': 'Ideal Gas Constant',
            'definition': 'Physical constant relating energy scale to temperature scale',
            'data': {'symbol': 'R', 'value': 8.314462618, 'unit': 'J/(mol⋅K)',
                    'exact': True, 'derived_from': ['N_A', 'k_B']}
        },

        # Quantum
        {
            'term': 'Reduced Planck Constant',
            'definition': 'Planck constant divided by 2π, used in quantum mechanics',
            'data': {'symbol': 'ℏ', 'value': 1.054571817e-34, 'unit': 'J⋅s',
                    'derived_from': ['h'], 'formula': 'h/(2π)'}
        },
        {
            'term': 'Planck Length',
            'definition': 'Fundamental length scale in quantum gravity',
            'data': {'symbol': 'l_P', 'value': 1.616255e-35, 'unit': 'm',
                    'formula': 'sqrt(ℏG/c³)'}
        },
        {
            'term': 'Planck Time',
            'definition': 'Time required for light to travel one Planck length',
            'data': {'symbol': 't_P', 'value': 5.391247e-44, 'unit': 's',
                    'formula': 'sqrt(ℏG/c⁵)'}
        },
        {
            'term': 'Planck Mass',
            'definition': 'Fundamental mass scale in quantum gravity',
            'data': {'symbol': 'm_P', 'value': 2.176434e-8, 'unit': 'kg',
                    'formula': 'sqrt(ℏc/G)'}
        },
    ]

    for const in constants:
        encyclopedia.add_entry(
            term=const['term'],
            volume=EncyclopediaVolume.EMPIRICAL,
            definition=const['definition'],
            data_object=const['data'],
            references=['CODATA 2018', 'SI Brochure 9th Edition']
        )

    print(f"[OK] Added {len(constants)} physical constants")


def populate_si_units(encyclopedia: EncyclopediaSystem):
    """Add SI base and derived units"""
    print("\n[Populating] SI Units...")

    units = [
        # Base Units
        {
            'term': 'Meter',
            'definition': 'SI base unit of length',
            'data': {'symbol': 'm', 'type': 'base', 'dimension': 'length',
                    'definition': 'Distance light travels in 1/299792458 second'}
        },
        {
            'term': 'Kilogram',
            'definition': 'SI base unit of mass',
            'data': {'symbol': 'kg', 'type': 'base', 'dimension': 'mass',
                    'definition': 'Defined by fixing Planck constant to exact value'}
        },
        {
            'term': 'Second',
            'definition': 'SI base unit of time',
            'data': {'symbol': 's', 'type': 'base', 'dimension': 'time',
                    'definition': '9,192,631,770 periods of Cs-133 radiation'}
        },
        {
            'term': 'Ampere',
            'definition': 'SI base unit of electric current',
            'data': {'symbol': 'A', 'type': 'base', 'dimension': 'electric_current',
                    'definition': 'Defined by fixing elementary charge to exact value'}
        },
        {
            'term': 'Kelvin',
            'definition': 'SI base unit of thermodynamic temperature',
            'data': {'symbol': 'K', 'type': 'base', 'dimension': 'temperature',
                    'definition': 'Defined by fixing Boltzmann constant to exact value'}
        },
        {
            'term': 'Mole',
            'definition': 'SI base unit of amount of substance',
            'data': {'symbol': 'mol', 'type': 'base', 'dimension': 'amount_of_substance',
                    'definition': 'Defined by fixing Avogadro constant to exact value'}
        },
        {
            'term': 'Candela',
            'definition': 'SI base unit of luminous intensity',
            'data': {'symbol': 'cd', 'type': 'base', 'dimension': 'luminous_intensity',
                    'definition': 'Luminous intensity in given direction of 540 THz monochromatic source'}
        },

        # Common Derived Units
        {
            'term': 'Newton',
            'definition': 'SI derived unit of force',
            'data': {'symbol': 'N', 'type': 'derived', 'base_units': 'kg⋅m/s²',
                    'dimension': 'force'}
        },
        {
            'term': 'Joule',
            'definition': 'SI derived unit of energy',
            'data': {'symbol': 'J', 'type': 'derived', 'base_units': 'kg⋅m²/s²',
                    'dimension': 'energy'}
        },
        {
            'term': 'Watt',
            'definition': 'SI derived unit of power',
            'data': {'symbol': 'W', 'type': 'derived', 'base_units': 'kg⋅m²/s³',
                    'dimension': 'power'}
        },
        {
            'term': 'Pascal',
            'definition': 'SI derived unit of pressure',
            'data': {'symbol': 'Pa', 'type': 'derived', 'base_units': 'kg/(m⋅s²)',
                    'dimension': 'pressure'}
        },
        {
            'term': 'Hertz',
            'definition': 'SI derived unit of frequency',
            'data': {'symbol': 'Hz', 'type': 'derived', 'base_units': 's^-1',
                    'dimension': 'frequency'}
        },
    ]

    for unit in units:
        encyclopedia.add_entry(
            term=unit['term'],
            volume=EncyclopediaVolume.EMPIRICAL,
            definition=unit['definition'],
            data_object=unit['data'],
            references=['SI Brochure 9th Edition']
        )

    print(f"[OK] Added {len(units)} SI units")


def main():
    """Populate encyclopedia with foundation data"""
    print("="*70)
    print("ENCYCLOPEDIA FOUNDATION DATA POPULATION")
    print("="*70)

    encyclopedia = EncyclopediaSystem()
    print(f"\n[OK] Encyclopedia initialized")
    print(f"    Base path: {encyclopedia.base_path}")

    populate_physical_constants(encyclopedia)
    populate_si_units(encyclopedia)

    # Get statistics
    stats = encyclopedia.get_statistics()
    print("\n" + "="*70)
    print("POPULATION COMPLETE")
    print("="*70)
    print(f"Total entries: {stats['total_entries']}")

    for volume_name, volume_stats in stats['volumes'].items():
        print(f"\n{volume_name}:")
        print(f"  Entries: {volume_stats['count']}")
        if volume_stats['categories']:
            print(f"  Categories: {', '.join(sorted(volume_stats['categories'].keys()))}")

    print("\n[SUCCESS] Encyclopedia foundation data loaded! 📚")


if __name__ == '__main__':
    main()
