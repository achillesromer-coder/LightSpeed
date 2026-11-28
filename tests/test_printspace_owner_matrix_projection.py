"""Verify the source-bound *index* without raising physical evidence or authority.

Only a later authenticated Drive reread can confirm that the observed snapshot
still matches its source cells; this test checks the repo's internal alignment.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "cgx/manufacturing/printspace_owner_matrix_projection_v0_1.json"
ATLAS = ROOT / "cgx/component_atlas/component_geometry_atlas_v0_1.json"


def load():
    return json.loads(INDEX.read_text(encoding="utf-8"))


def test_readonly_projection_has_all_411_ordered_source_rows():
    d = load()
    assert d["schema"] == "CGX-PRINTSPACE-OWNER-MATRIX-PROJECTION/0.1"
    assert d["status"] == "READ_ONLY_FINGERPRINT_INDEX / NO_ENGINEERING_EVIDENCE_PROMOTION"
    assert d["policy"]["no_raw_material_process_copy"] is True
    assert d["policy"]["directional_role"].endswith("never physical compatibility qualification")
    rows = d["row_fingerprints"]
    assert d["counts"]["archetypes"] == len(rows) == 411
    assert (d["counts"]["directional_fields"], d["counts"]["compiler_fields"]) == (16, 8)
    assert d["counts"]["all24_nonempty"] == 411
    assert d["counts"]["rows_with_blanks"] == 0
    assert d["counts"]["rows_containing_reverse_direction_warning"] == 411
    assert d["counts"]["rows_containing_evidence_override"] == 411
    assert d["sparse_fields"] == []
    assert [r["sheet_row"] for r in rows] == list(range(2, 413))
    assert [r["matrix_id"] for r in rows] == [f"T1M-{i:04}" for i in range(1, 412)]
    assert len({r["archetype_id"] for r in rows}) == 411
    for r in rows:
        assert r["source_cell_range"] == f"AK{r['sheet_row']}:BH{r['sheet_row']}"
        assert len(r["directional_sha256"]) == 64
        assert bytes.fromhex(r["directional_sha256"])
        assert r["blank_fields"] == []
        assert r["primitive_basis"].strip() and r["compiler_token"].strip()


def test_sha256_index_consistency_and_authoritative_source_identity():
    d = load()
    r = d["row_fingerprints"]
    canonical = [[row["sheet_row"], row["matrix_id"], row["archetype_id"], row["directional_sha256"]] for row in r]
    raw = json.dumps(canonical, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(raw).hexdigest() == d["projection_sha256"]
    assert d["source"]["spreadsheet_id"] == "1refNFmebTcmPVojCuZsyILJEWaKz-sVzYLfZtqMl8k8"
    assert d["source"]["sheet"] == "32_CGX_Universal_Type1_Tech_Matrix_v0_1"
    assert d["source"]["source_id_range"] == "A2:B412"
    assert d["source"]["source_detail_range"] == "AK2:BH412"
    assert "not authoritative" in d["source"]["engineered_source"].lower()


def test_projection_archetypes_match_existing_canonical_geometry_atlas():
    d = load()
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    atlas_ids = [r["ID"] for r in atlas["records"]]
    projected_ids = [r["archetype_id"] for r in d["row_fingerprints"]]
    assert len(atlas_ids) == atlas["record_count"] == 411
    assert len(set(atlas_ids)) == 411
    assert set(projected_ids) == set(atlas_ids)


def test_projection_does_not_copy_unqualified_material_claims():
    d = load()
    allowed = {"sheet_row", "matrix_id", "archetype_id", "source_cell_range", "directional_sha256", "blank_fields", "primitive_basis", "compiler_token"}
    assert all(set(row) == allowed for row in d["row_fingerprints"])
    assert d["policy"]["geometry_rule"] == "no inferred T173 admitted meshes"
    assert d["policy"]["mutation_rule"].endswith("owner reconciliation")