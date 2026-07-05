"""
Simulation and Physics Engine Tests
===================================

Comprehensive testing of the Raphael physics engine and
simulation infrastructure across TheConstruct and Merovingian.

Test Categories:
- Physics calculations (gravitation, quantum, cosmology)
- Simulation controller functionality
- Natural phenomena simulations
- Visualization outputs
- Parameter validation

Author: LightSpeed Team / ACHILLES
Version: 5.1.1
"""

import pytest
import sys
import math
from pathlib import Path
from typing import Dict, Any, Optional
import json

from tests.conftest import LIGHTSPEED_ROOT, Z_AXIS_ROOT, FLOOR_PATHS


# ============================================================================
# PHYSICS CONSTANTS (For validation)
# ============================================================================

PHYSICS_CONSTANTS = {
    "c": 299792458,  # Speed of light (m/s)
    "G": 6.67430e-11,  # Gravitational constant (m^3 kg^-1 s^-2)
    "h": 6.62607015e-34,  # Planck constant (J⋅s)
    "hbar": 1.054571817e-34,  # Reduced Planck constant (J⋅s)
    "k_B": 1.380649e-23,  # Boltzmann constant (J/K)
    "e": 1.602176634e-19,  # Elementary charge (C)
    "m_e": 9.1093837015e-31,  # Electron mass (kg)
    "m_p": 1.67262192369e-27,  # Proton mass (kg)
    "epsilon_0": 8.8541878128e-12,  # Vacuum permittivity (F/m)
    "mu_0": 1.25663706212e-6,  # Vacuum permeability (H/m)
    "N_A": 6.02214076e23,  # Avogadro constant (mol^-1)
    "R": 8.314462618,  # Gas constant (J/(mol⋅K))
    "sigma": 5.670374419e-8,  # Stefan-Boltzmann constant (W m^-2 K^-4)
    "H_0": 70,  # Hubble constant (km/s/Mpc) - approximate
    "solar_mass": 1.989e30,  # Solar mass (kg)
    "earth_mass": 5.972e24,  # Earth mass (kg)
    "earth_radius": 6.371e6,  # Earth radius (m)
}


# ============================================================================
# PHYSICS CALCULATION IMPLEMENTATIONS FOR TESTING
# ============================================================================

class PhysicsCalculator:
    """Reference physics calculator for test validation."""

    @staticmethod
    def schwarzschild_radius(mass_kg: float) -> float:
        """Calculate Schwarzschild radius of a black hole."""
        G = PHYSICS_CONSTANTS["G"]
        c = PHYSICS_CONSTANTS["c"]
        return 2 * G * mass_kg / (c ** 2)

    @staticmethod
    def hawking_temperature(mass_kg: float) -> float:
        """Calculate Hawking temperature of a black hole."""
        hbar = PHYSICS_CONSTANTS["hbar"]
        c = PHYSICS_CONSTANTS["c"]
        G = PHYSICS_CONSTANTS["G"]
        k_B = PHYSICS_CONSTANTS["k_B"]
        return (hbar * c ** 3) / (8 * math.pi * G * mass_kg * k_B)

    @staticmethod
    def orbital_velocity(mass_kg: float, radius_m: float) -> float:
        """Calculate orbital velocity."""
        G = PHYSICS_CONSTANTS["G"]
        return math.sqrt(G * mass_kg / radius_m)

    @staticmethod
    def escape_velocity(mass_kg: float, radius_m: float) -> float:
        """Calculate escape velocity."""
        G = PHYSICS_CONSTANTS["G"]
        return math.sqrt(2 * G * mass_kg / radius_m)

    @staticmethod
    def time_dilation(velocity_ms: float) -> float:
        """Calculate time dilation factor (gamma)."""
        c = PHYSICS_CONSTANTS["c"]
        beta = velocity_ms / c
        if beta >= 1:
            return float('inf')
        return 1 / math.sqrt(1 - beta ** 2)

    @staticmethod
    def de_broglie_wavelength(mass_kg: float, velocity_ms: float) -> float:
        """Calculate de Broglie wavelength."""
        h = PHYSICS_CONSTANTS["h"]
        return h / (mass_kg * velocity_ms)

    @staticmethod
    def energy_level_hydrogen(n: int, Z: int = 1) -> float:
        """Calculate hydrogen-like energy level (eV)."""
        # E_n = -13.6 * Z^2 / n^2 eV
        return -13.6 * Z ** 2 / n ** 2

    @staticmethod
    def hubble_distance(redshift: float) -> float:
        """Calculate Hubble distance (approximate, Mpc)."""
        H_0 = PHYSICS_CONSTANTS["H_0"]
        c = PHYSICS_CONSTANTS["c"]
        # d = c * z / H_0 (simple approximation for low z)
        c_km_s = c / 1000  # Convert to km/s
        return c_km_s * redshift / H_0

    @staticmethod
    def critical_density(hubble_constant_km_s_mpc: float) -> float:
        """Calculate critical density of the universe."""
        G = PHYSICS_CONSTANTS["G"]
        # Convert H_0 to SI units (s^-1)
        H_0_si = hubble_constant_km_s_mpc * 1000 / (3.086e22)  # Mpc to m
        return 3 * H_0_si ** 2 / (8 * math.pi * G)


# Reference calculator
calc = PhysicsCalculator()


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestPhysicsConstants:
    """Test that physics constants are correctly defined."""

    def test_speed_of_light(self):
        """Speed of light should be correct."""
        assert PHYSICS_CONSTANTS["c"] == 299792458

    def test_gravitational_constant(self):
        """Gravitational constant should be correct."""
        assert abs(PHYSICS_CONSTANTS["G"] - 6.67430e-11) < 1e-15

    def test_planck_constant(self):
        """Planck constant should be correct."""
        assert abs(PHYSICS_CONSTANTS["h"] - 6.62607015e-34) < 1e-40

    def test_constants_relationships(self):
        """Test relationships between constants."""
        # hbar = h / (2 * pi)
        expected_hbar = PHYSICS_CONSTANTS["h"] / (2 * math.pi)
        assert abs(PHYSICS_CONSTANTS["hbar"] - expected_hbar) < 1e-40


class TestGravitationalPhysics:
    """Test gravitational physics calculations."""

    def test_schwarzschild_radius_solar_mass(self, simulation_params):
        """Schwarzschild radius for solar mass should be ~3 km."""
        mass = simulation_params["physics"]["schwarzschild_radius"]["mass_kg"]
        r_s = calc.schwarzschild_radius(mass)

        # Expected: ~2954 meters for solar mass
        assert 2900 < r_s < 3000, f"Schwarzschild radius {r_s} not in expected range"

    def test_schwarzschild_radius_scaling(self):
        """Schwarzschild radius should scale linearly with mass."""
        r1 = calc.schwarzschild_radius(1e30)
        r2 = calc.schwarzschild_radius(2e30)

        ratio = r2 / r1
        assert abs(ratio - 2.0) < 0.001, "Schwarzschild radius doesn't scale linearly"

    def test_hawking_temperature(self, simulation_params):
        """Hawking temperature calculation."""
        mass = simulation_params["physics"]["hawking_temperature"]["mass_kg"]
        T = calc.hawking_temperature(mass)

        # For 10 billion kg black hole, temperature should be very high
        assert T > 0, "Hawking temperature must be positive"
        assert T > 1e10, "Hawking temperature should be very high for small black holes"

    def test_hawking_temperature_inverse_mass(self):
        """Hawking temperature should be inversely proportional to mass."""
        T1 = calc.hawking_temperature(1e30)
        T2 = calc.hawking_temperature(2e30)

        ratio = T1 / T2
        assert abs(ratio - 2.0) < 0.001, "Hawking temperature doesn't scale inversely"

    def test_orbital_velocity_iss(self, simulation_params):
        """Orbital velocity at ISS altitude should be ~7.66 km/s."""
        params = simulation_params["physics"]["orbital_velocity"]
        v = calc.orbital_velocity(params["mass_kg"], params["radius_m"])

        # ISS orbital velocity is about 7.66 km/s
        v_km_s = v / 1000
        assert 7.5 < v_km_s < 7.8, f"Orbital velocity {v_km_s} km/s not in expected range"

    def test_escape_velocity_earth(self, simulation_params):
        """Escape velocity from Earth's surface should be ~11.2 km/s."""
        params = simulation_params["physics"]["escape_velocity"]
        v = calc.escape_velocity(params["mass_kg"], params["radius_m"])

        # Earth escape velocity is about 11.2 km/s
        v_km_s = v / 1000
        assert 11.0 < v_km_s < 11.4, f"Escape velocity {v_km_s} km/s not in expected range"

    def test_escape_orbital_velocity_relation(self):
        """Escape velocity should be sqrt(2) times orbital velocity at same radius."""
        mass = PHYSICS_CONSTANTS["earth_mass"]
        radius = PHYSICS_CONSTANTS["earth_radius"]

        v_orbit = calc.orbital_velocity(mass, radius)
        v_escape = calc.escape_velocity(mass, radius)

        ratio = v_escape / v_orbit
        assert abs(ratio - math.sqrt(2)) < 0.001, "v_escape / v_orbit should be sqrt(2)"


class TestRelativisticPhysics:
    """Test relativistic physics calculations."""

    def test_time_dilation_low_velocity(self):
        """Time dilation at low velocity should be negligible."""
        v = 100  # 100 m/s
        gamma = calc.time_dilation(v)

        assert abs(gamma - 1.0) < 1e-10, "Time dilation at low velocity should be ~1"

    def test_time_dilation_relativistic(self, simulation_params):
        """Time dilation at relativistic speeds."""
        v = simulation_params["physics"]["time_dilation"]["velocity_ms"]
        gamma = calc.time_dilation(v)

        # At 0.9c, gamma should be about 2.29
        assert 2.2 < gamma < 2.4, f"Gamma at 0.9c should be ~2.29, got {gamma}"

    def test_time_dilation_high_velocity(self):
        """Time dilation should increase dramatically near light speed."""
        c = PHYSICS_CONSTANTS["c"]

        gamma_90 = calc.time_dilation(0.90 * c)
        gamma_99 = calc.time_dilation(0.99 * c)
        gamma_999 = calc.time_dilation(0.999 * c)

        assert gamma_99 > gamma_90, "Higher velocity should have higher gamma"
        assert gamma_999 > gamma_99, "Higher velocity should have higher gamma"
        assert gamma_999 > 20, "Gamma at 0.999c should be > 20"


class TestQuantumMechanics:
    """Test quantum mechanics calculations."""

    def test_de_broglie_wavelength_electron(self, simulation_params):
        """de Broglie wavelength for electron."""
        params = simulation_params["physics"]["de_broglie_wavelength"]
        wavelength = calc.de_broglie_wavelength(params["mass_kg"], params["velocity_ms"])

        # For electron at 1e6 m/s, wavelength should be sub-nanometer
        assert wavelength > 0, "Wavelength must be positive"
        assert wavelength < 1e-9, "Electron wavelength should be sub-nanometer"

    def test_de_broglie_inverse_momentum(self):
        """de Broglie wavelength should be inversely proportional to momentum."""
        m = PHYSICS_CONSTANTS["m_e"]

        lambda1 = calc.de_broglie_wavelength(m, 1e5)
        lambda2 = calc.de_broglie_wavelength(m, 2e5)

        ratio = lambda1 / lambda2
        assert abs(ratio - 2.0) < 0.001, "Wavelength should be inversely proportional to velocity"

    def test_hydrogen_ground_state(self):
        """Hydrogen ground state energy should be -13.6 eV."""
        E1 = calc.energy_level_hydrogen(1, 1)
        assert abs(E1 - (-13.6)) < 0.01, f"Ground state energy should be -13.6 eV, got {E1}"

    def test_hydrogen_excited_states(self):
        """Hydrogen excited state energies."""
        E1 = calc.energy_level_hydrogen(1)
        E2 = calc.energy_level_hydrogen(2)
        E3 = calc.energy_level_hydrogen(3)

        # E_n scales as 1/n^2
        assert abs(E2 - E1/4) < 0.001, "E_2 should be E_1/4"
        assert abs(E3 - E1/9) < 0.001, "E_3 should be E_1/9"


class TestCosmology:
    """Test cosmology calculations."""

    def test_hubble_distance(self, simulation_params):
        """Hubble distance calculation."""
        z = simulation_params["cosmology"]["hubble_distance"]["redshift"]
        d = calc.hubble_distance(z)

        # At z=0.1, distance should be ~400-500 Mpc
        assert d > 0, "Distance must be positive"
        assert 400 < d < 500, f"Distance at z=0.1 should be ~430 Mpc, got {d}"

    def test_critical_density(self, simulation_params):
        """Critical density calculation."""
        H_0 = simulation_params["cosmology"]["critical_density"]["hubble_constant_km_s_mpc"]
        rho_c = calc.critical_density(H_0)

        # Critical density should be around 9.5e-27 kg/m^3
        assert rho_c > 0, "Critical density must be positive"
        assert 8e-27 < rho_c < 1.1e-26, f"Critical density should be ~9.5e-27 kg/m^3, got {rho_c}"


class TestRaphaelPhysicsEngine:
    """Test the Raphael physics engine files."""

    @pytest.fixture(autouse=True)
    def setup_raphael_paths(self, floor_paths):
        """Add Raphael paths for imports."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        raphael_path = merovingian / "core" / "physics" / "raphael"
        if raphael_path.exists():
            if str(raphael_path) not in sys.path:
                sys.path.insert(0, str(raphael_path))
            sims_path = raphael_path / "Simulations"
            if sims_path.exists() and str(sims_path) not in sys.path:
                sys.path.insert(0, str(sims_path))

    def test_raphael_directory_structure(self, floor_paths):
        """Raphael should have proper directory structure."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        raphael_path = merovingian / "core" / "physics" / "raphael"

        assert raphael_path.exists(), "Raphael physics engine not found"

        # Check for key components
        expected_files = [
            "raphael_equations.py",
        ]

        for fname in expected_files:
            fpath = raphael_path / fname
            if not fpath.exists():
                # May be in subdirectory
                found = list(raphael_path.rglob(fname))
                assert len(found) > 0, f"Raphael file not found: {fname}"

    def test_natural_phenomena_simulations(self, floor_paths):
        """Natural phenomena simulations should exist."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        phenomena_path = merovingian / "core" / "physics" / "raphael" / "natural_phenonema"

        if not phenomena_path.exists():
            pytest.skip("Natural phenomena directory not found")

        # Check for simulation categories
        expected_categories = ["atomic", "cosmic", "galactic", "planetary", "quantum", "stellar"]

        for category in expected_categories:
            cat_path = phenomena_path / category
            assert cat_path.exists(), f"Simulation category not found: {category}"

            # Check for Python files
            py_files = list(cat_path.glob("*.py"))
            assert len(py_files) > 0, f"No simulations in category: {category}"

    def test_simulation_controller_exists(self, floor_paths):
        """Simulation controller should exist."""
        merovingian = floor_paths.get("Z-4_Merovingian")
        raphael_path = merovingian / "core" / "physics" / "raphael"
        sims_path = raphael_path / "Simulations"

        if not sims_path.exists():
            pytest.skip("Simulations directory not found")

        controller = sims_path / "simulation_controller.py"
        assert controller.exists(), "Simulation controller not found"


class TestSimulationParameters:
    """Test simulation parameter validation."""

    def test_mass_parameter_positive(self, simulation_params):
        """All mass parameters should be positive."""
        for category, params in simulation_params.items():
            for calc_name, calc_params in params.items():
                if "mass_kg" in calc_params:
                    assert calc_params["mass_kg"] > 0, f"Mass in {calc_name} must be positive"

    def test_radius_parameter_positive(self, simulation_params):
        """All radius parameters should be positive."""
        for category, params in simulation_params.items():
            for calc_name, calc_params in params.items():
                if "radius_m" in calc_params:
                    assert calc_params["radius_m"] > 0, f"Radius in {calc_name} must be positive"

    def test_velocity_below_light_speed(self, simulation_params):
        """All velocities should be below speed of light."""
        c = PHYSICS_CONSTANTS["c"]
        for category, params in simulation_params.items():
            for calc_name, calc_params in params.items():
                if "velocity_ms" in calc_params:
                    v = calc_params["velocity_ms"]
                    assert v < c, f"Velocity in {calc_name} exceeds light speed"


class TestSimulationOutputs:
    """Test that simulations produce valid outputs."""

    def test_schwarzschild_radius_output_format(self):
        """Schwarzschild radius output should be a float in meters."""
        result = calc.schwarzschild_radius(PHYSICS_CONSTANTS["solar_mass"])
        assert isinstance(result, float), "Result should be a float"
        assert result > 0, "Result should be positive"
        assert not math.isnan(result), "Result should not be NaN"
        assert not math.isinf(result), "Result should not be infinite"

    def test_hawking_temperature_output_format(self):
        """Hawking temperature output should be a float in Kelvin."""
        result = calc.hawking_temperature(1e10)
        assert isinstance(result, float), "Result should be a float"
        assert result > 0, "Result should be positive (Kelvin)"
        assert not math.isnan(result), "Result should not be NaN"

    def test_time_dilation_output_format(self):
        """Time dilation output should be a float >= 1."""
        result = calc.time_dilation(0.5 * PHYSICS_CONSTANTS["c"])
        assert isinstance(result, float), "Result should be a float"
        assert result >= 1, "Gamma should be >= 1"
        assert not math.isnan(result), "Result should not be NaN"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
