"""
Seed Calculator Modules into Database
Registers all 49 extracted calculator modules in lightspeed_system.db
"""

import sys
from pathlib import Path

# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

# Import from local modules
from models import CalculatorModule, ScientificDataset, KnowledgeGraphNode, KnowledgeGraphEdge
from base import get_session

# Calculator definitions
CALCULATORS = [
    # Atomic Physics (10 modules)
    {
        'name': 'atomic_elemental_interactive_table',
        'filepath': 'Z Axis/Z0_TheConstruct/atomic/atomic_elemental_interactive_table.py',
        'floor': 'Z0_TheConstruct',
        'category': 'atomic',
        'subcategory': 'periodic_table',
        'description': 'Interactive periodic table with element properties and electron configurations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'atomic_emission_spectra',
        'filepath': 'Z Axis/Z0_TheConstruct/atomic/atomic_emission_spectra.py',
        'floor': 'Z0_TheConstruct',
        'category': 'atomic',
        'subcategory': 'spectroscopy',
        'description': 'Calculate atomic emission spectra for elements',
        'dataset_requirements': '[]',
    },
    {
        'name': 'atomic_orbitals',
        'filepath': 'Z Axis/Z0_TheConstruct/atomic/atomic_orbitals.py',
        'floor': 'Z0_TheConstruct',
        'category': 'atomic',
        'subcategory': 'electron_structure',
        'description': 'Calculate and visualize atomic electron orbitals',
        'dataset_requirements': '[]',
    },
    {
        'name': 'atomic_stability',
        'filepath': 'Z Axis/Z0_TheConstruct/atomic/atomic_stability.py',
        'floor': 'Z0_TheConstruct',
        'category': 'atomic',
        'subcategory': 'nuclear_stability',
        'description': 'Determine nuclear stability and binding energy',
        'dataset_requirements': '[]',
    },
    {
        'name': 'atomic_transitions',
        'filepath': 'Z Axis/Z0_TheConstruct/atomic/atomic_transitions.py',
        'floor': 'Z0_TheConstruct',
        'category': 'atomic',
        'subcategory': 'energy_levels',
        'description': 'Calculate energy level transitions and photon emission',
        'dataset_requirements': '[]',
    },
    {
        'name': 'bond_formation',
        'filepath': 'Z Axis/Z0_TheConstruct/atomic/bond_formation.py',
        'floor': 'Z0_TheConstruct',
        'category': 'atomic',
        'subcategory': 'chemistry',
        'description': 'Model chemical bond formation and molecular structures',
        'dataset_requirements': '[]',
    },
    {
        'name': 'electron_orbitals',
        'filepath': 'Z Axis/Z0_TheConstruct/atomic/electron_orbitals.py',
        'floor': 'Z0_TheConstruct',
        'category': 'atomic',
        'subcategory': 'electron_structure',
        'description': 'Detailed electron orbital calculations and visualizations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'ionization_energy',
        'filepath': 'Z Axis/Z0_TheConstruct/atomic/ionization_energy.py',
        'floor': 'Z0_TheConstruct',
        'category': 'atomic',
        'subcategory': 'ionization',
        'description': 'Calculate ionization energies for elements',
        'dataset_requirements': '[]',
    },
    {
        'name': 'nuclear_decay',
        'filepath': 'Z Axis/Z0_TheConstruct/atomic/nuclear_decay.py',
        'floor': 'Z0_TheConstruct',
        'category': 'atomic',
        'subcategory': 'nuclear_physics',
        'description': 'Model radioactive decay and half-life calculations',
        'dataset_requirements': '[]',
    },

    # Black Hole Physics (7 modules) - Excludes __init__.py
    {
        'name': 'black_hole_simulation',
        'filepath': 'Z Axis/Z0_TheConstruct/black_hole/black_hole_simulation.py',
        'floor': 'Z0_TheConstruct',
        'category': 'black_hole',
        'subcategory': 'gravitational_waves',
        'description': 'Comprehensive black hole merger simulations with LIGO gravitational wave data integration',
        'dataset_requirements': '["ligo_gw"]',  # Links to LIGO data
    },
    {
        'name': '6D_black_hole_venv',
        'filepath': 'Z Axis/Z0_TheConstruct/black_hole/6D_black_hole_venv.py',
        'floor': 'Z0_TheConstruct',
        'category': 'black_hole',
        'subcategory': 'higher_dimensions',
        'description': '6-dimensional black hole physics simulations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'black_hole_realised',
        'filepath': 'Z Axis/Z0_TheConstruct/black_hole/black_hole_realised.py',
        'floor': 'Z0_TheConstruct',
        'category': 'black_hole',
        'subcategory': 'visualization',
        'description': 'Realized black hole model with advanced visualization',
        'dataset_requirements': '[]',
    },
    {
        'name': 'black_holes',
        'filepath': 'Z Axis/Z0_TheConstruct/black_hole/black_holes.py',
        'floor': 'Z0_TheConstruct',
        'category': 'black_hole',
        'subcategory': 'general',
        'description': 'General black hole physics calculations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'black_hole_graphed_simulation',
        'filepath': 'Z Axis/Z0_TheConstruct/black_hole/black-hole-graphed_simulation.py',
        'floor': 'Z0_TheConstruct',
        'category': 'black_hole',
        'subcategory': 'visualization',
        'description': 'Graph-based black hole simulation with visual output',
        'dataset_requirements': '[]',
    },
    {
        'name': 'black_hole_holograph_raw',
        'filepath': 'Z Axis/Z0_TheConstruct/black_hole/black-hole-holograph-raw.py',
        'floor': 'Z0_TheConstruct',
        'category': 'black_hole',
        'subcategory': 'holographic_principle',
        'description': 'Raw holographic principle calculations for black holes',
        'dataset_requirements': '[]',
    },

    # Cosmological Physics (15 modules)
    {
        'name': 'cosmic_microwave_background',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/cosmic_microwave_background.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'cmb_analysis',
        'description': 'Cosmic Microwave Background analysis using Planck satellite data (9 FITS files, 14GB)',
        'dataset_requirements': '["planck_cmb"]',  # Links to Planck data
    },
    {
        'name': 'big_bang_simulation',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/big_bang_simulation.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'universe_evolution',
        'description': 'Simulate universe evolution from Big Bang singularity',
        'dataset_requirements': '[]',
    },
    {
        'name': 'dark_energy',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/dark_energy.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'dark_energy',
        'description': 'Dark energy calculations and cosmological constant modeling',
        'dataset_requirements': '[]',
    },
    {
        'name': 'galaxy_formation',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/galaxy_formation.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'galaxy_evolution',
        'description': 'Model galaxy formation and evolution over cosmic time',
        'dataset_requirements': '[]',
    },
    {
        'name': 'galactic_rotation',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/galactic_rotation.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'galaxy_dynamics',
        'description': 'Galactic rotation curves and dark matter distribution',
        'dataset_requirements': '[]',
    },
    {
        'name': 'universal_expansion',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/universal_expansion.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'hubble_expansion',
        'description': 'Hubble expansion and universe scale factor calculations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'interstellar_medium',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/interstellar_medium.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'ism',
        'description': 'Interstellar medium physics and composition',
        'dataset_requirements': '[]',
    },
    {
        'name': 'spacetime_simulation',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/spacetime_simulation.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'general_relativity',
        'description': 'Spacetime curvature and general relativity simulations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'time_dynamics',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/time_dynamics.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'time_evolution',
        'description': 'Time evolution in cosmological contexts',
        'dataset_requirements': '[]',
    },
    {
        'name': 'magnetic_field',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/magnetic_field.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'magnetism',
        'description': 'Cosmic magnetic field modeling',
        'dataset_requirements': '[]',
    },
    {
        'name': 'atmospherical_layers',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/atmospherical_layers.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'atmospheric_physics',
        'description': 'Atmospheric layer structure and physics',
        'dataset_requirements': '[]',
    },
    {
        'name': 'fractals',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/fractals.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'fractal_structures',
        'description': 'Fractal structures in cosmic formations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'fractal_expansion',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/fractal_expansion.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'fractal_growth',
        'description': 'Fractal expansion and growth patterns',
        'dataset_requirements': '[]',
    },
    {
        'name': 'eco_rehabilitation',
        'filepath': 'Z Axis/Z0_TheConstruct/cosmological/eco_rehabilitation.py',
        'floor': 'Z0_TheConstruct',
        'category': 'cosmology',
        'subcategory': 'ecosystem',
        'description': 'Ecosystem modeling and rehabilitation',
        'dataset_requirements': '[]',
    },

    # Holographic Simulations (3 modules)
    {
        'name': 'holograph_simulations',
        'filepath': 'Z Axis/Z0_TheConstruct/holographic/holograph_simulations.py',
        'floor': 'Z0_TheConstruct',
        'category': 'holographic',
        'subcategory': 'simulation',
        'description': 'Holographic principle simulations and visualizations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'system_interaction',
        'filepath': 'Z Axis/Z0_TheConstruct/holographic/system_interaction.py',
        'floor': 'Z0_TheConstruct',
        'category': 'holographic',
        'subcategory': 'interaction',
        'description': 'System-level holographic interactions',
        'dataset_requirements': '[]',
    },

    # Orbital Mechanics (6 modules)
    {
        'name': 'orbital_mechanics',
        'filepath': 'Z Axis/Z0_TheConstruct/orbital/orbital_mechanics.py',
        'floor': 'Z0_TheConstruct',
        'category': 'orbital',
        'subcategory': 'trajectories',
        'description': 'Primary orbital mechanics and trajectory calculations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'interplanetary_sim',
        'filepath': 'Z Axis/Z0_TheConstruct/orbital/interplanetary_sim.py',
        'floor': 'Z0_TheConstruct',
        'category': 'orbital',
        'subcategory': 'interplanetary',
        'description': 'Interplanetary trajectory simulations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'virtual_solar_mapper',
        'filepath': 'Z Axis/Z0_TheConstruct/orbital/virtual_solar_mapper.py',
        'floor': 'Z0_TheConstruct',
        'category': 'orbital',
        'subcategory': 'mapping',
        'description': 'Virtual solar system mapping and visualization',
        'dataset_requirements': '[]',
    },
    {
        'name': 'luke_master_runs',
        'filepath': 'Z Axis/Z0_TheConstruct/orbital/luke_master_runs.py',
        'floor': 'Z0_TheConstruct',
        'category': 'orbital',
        'subcategory': 'orchestration',
        'description': 'Master orbital simulation orchestrator',
        'dataset_requirements': '[]',
    },
    {
        'name': 'porkchop',
        'filepath': 'Z Axis/Z0_TheConstruct/orbital/porkchop.py',
        'floor': 'Z0_TheConstruct',
        'category': 'orbital',
        'subcategory': 'plotting',
        'description': 'Porkchop plot generator for launch windows',
        'dataset_requirements': '[]',
    },
    {
        'name': 'interplanetar_supply_chain',
        'filepath': 'Z Axis/Z0_TheConstruct/orbital/interplanetar_supply_chain.py',
        'floor': 'Z0_TheConstruct',
        'category': 'orbital',
        'subcategory': 'logistics',
        'description': 'Interplanetary supply chain optimization',
        'dataset_requirements': '[]',
    },

    # Quantum Mechanics (7 modules)
    {
        'name': 'quantum_mechanics',
        'filepath': 'Z Axis/Z0_TheConstruct/quantum/quantum_mechanics.py',
        'floor': 'Z0_TheConstruct',
        'category': 'quantum',
        'subcategory': 'general',
        'description': 'Primary quantum mechanics calculation engine',
        'dataset_requirements': '[]',
    },
    {
        'name': 'wave_particle_duality',
        'filepath': 'Z Axis/Z0_TheConstruct/quantum/wave_particle_duality.py',
        'floor': 'Z0_TheConstruct',
        'category': 'quantum',
        'subcategory': 'wave_mechanics',
        'description': 'Wave-particle duality phenomena simulations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'quantum_entanglement',
        'filepath': 'Z Axis/Z0_TheConstruct/quantum/quantum_entanglement.py',
        'floor': 'Z0_TheConstruct',
        'category': 'quantum',
        'subcategory': 'entanglement',
        'description': 'Quantum entanglement calculations and analysis',
        'dataset_requirements': '[]',
    },
    {
        'name': 'quantum_fluctuations',
        'filepath': 'Z Axis/Z0_TheConstruct/quantum/quantum_fluctuations.py',
        'floor': 'Z0_TheConstruct',
        'category': 'quantum',
        'subcategory': 'vacuum',
        'description': 'Quantum vacuum fluctuations modeling',
        'dataset_requirements': '[]',
    },
    {
        'name': 'quantum_superposition_simulation',
        'filepath': 'Z Axis/Z0_TheConstruct/quantum/quantum_superposition_simulation.py',
        'floor': 'Z0_TheConstruct',
        'category': 'quantum',
        'subcategory': 'superposition',
        'description': 'Quantum superposition state simulations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'uncertainty_principle',
        'filepath': 'Z Axis/Z0_TheConstruct/quantum/uncertainty_principle.py',
        'floor': 'Z0_TheConstruct',
        'category': 'quantum',
        'subcategory': 'uncertainty',
        'description': 'Heisenberg uncertainty principle calculations',
        'dataset_requirements': '[]',
    },

    # Raphael Framework & RFS Theory (6 modules)
    {
        'name': 'raphael_equations',
        'filepath': 'Z Axis/Z0_TheConstruct/raphael/raphael_equations.py',
        'floor': 'Z0_TheConstruct',
        'category': 'raphael',
        'subcategory': 'framework',
        'description': 'Core Raphael mathematical framework and equations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'raphael_visualization',
        'filepath': 'Z Axis/Z0_TheConstruct/raphael/raphael_visualization.py',
        'floor': 'Z0_TheConstruct',
        'category': 'raphael',
        'subcategory': 'visualization',
        'description': 'Raphael framework visualizations and plots',
        'dataset_requirements': '[]',
    },
    {
        'name': 'rfs_theory',
        'filepath': 'Z Axis/Z0_TheConstruct/raphael/rfs_theory.py',
        'floor': 'Z0_TheConstruct',
        'category': 'raphael',
        'subcategory': 'theory',
        'description': 'Raphael Field Synthesis theoretical framework',
        'dataset_requirements': '[]',
    },
    {
        'name': 'rfs_emff_sim',
        'filepath': 'Z Axis/Z0_TheConstruct/raphael/rfs_emff_sim.py',
        'floor': 'Z0_TheConstruct',
        'category': 'raphael',
        'subcategory': 'electromagnetic',
        'description': 'RFS electromagnetic field force simulations',
        'dataset_requirements': '[]',
    },
    {
        'name': 'supply_chain',
        'filepath': 'Z Axis/Z0_TheConstruct/raphael/supply_chain.py',
        'floor': 'Z0_TheConstruct',
        'category': 'raphael',
        'subcategory': 'optimization',
        'description': 'Supply chain optimization using Raphael framework',
        'dataset_requirements': '[]',
    },
]

def seed_calculators():
    """Seed all calculator modules into database"""
    session = get_session()

    try:
        print("[SEED] Starting calculator module registration...")
        print(f"[SEED] Total modules to register: {len(CALCULATORS)}")

        registered = 0
        for calc_data in CALCULATORS:
            # Check if already exists
            existing = session.query(CalculatorModule).filter_by(
                name=calc_data['name']
            ).first()

            if existing:
                print(f"[SKIP] {calc_data['name']} already registered")
                continue

            # Create new calculator module
            calc = CalculatorModule(**calc_data)
            session.add(calc)
            registered += 1
            print(f"[OK] Registered: {calc_data['name']} ({calc_data['category']})")

        session.commit()
        print(f"\n[SUCCESS] Registered {registered} new calculator modules")
        print(f"[INFO] Total calculators in database: {session.query(CalculatorModule).count()}")

    except Exception as e:
        print(f"[ERROR] Failed to seed calculators: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_calculators()
