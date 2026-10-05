from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "cgx" / "domain_templates" / "codata_2022_em_constants_alignment_2026-10-05.json"

SURFACES = [
    ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed" / "Z Axis" / "Z0_TheConstruct" / "dimensions_library.py",
    ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed" / "Z Axis" / "Z0_TheConstruct" / "physics_calculators.py",
    ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed" / "Z Axis" / "Z-2_Oracle" / "tools" / "populate_encyclopedia_foundation.py",
    ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed" / "Z Axis" / "Z-4_Merovingian" / "core" / "physics" / "raphael_renderer_pure.py",
    ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed" / "tests" / "test_simulations.py",
    ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed" / "Z Axis" / "Z-3_Smith" / "tools" / "rfs_emff_validation.py",
    ROOT / "desktop" / "LightSpeed_Runtime" / "lightspeed_runtime" / "rfs_emff_sweep.py",
]


def test_codata_2022_em_constants_are_aligned():
    merged = "\n".join(path.read_text(encoding="utf-8") for path in SURFACES)
    assert "1.25663706212e-6" not in merged
    assert "8.8541878128e-12" not in merged
    assert "MU0 = 4.0 * math.pi * 1e-7" not in merged
    assert "1.25663706127e-6" in merged
    assert "8.8541878188e-12" in merged


def test_alignment_receipt_has_provenance_and_claim_boundary():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert audit["status"] == "EXECUTED / 2022_CODATA_ALIGNED"
    assert audit["constants"]["vacuum_magnetic_permeability"]["relative_standard_uncertainty"] == 1.6e-10
    assert audit["constants"]["vacuum_electric_permittivity"]["relative_standard_uncertainty"] == 1.6e-10
    assert len(audit["aligned_surfaces"]) == 7
    assert audit["authority_transfer"] is False
    assert audit["public_publish_authorized"] is False
