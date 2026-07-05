from __future__ import annotations

from pathlib import Path

from lightspeed_runtime.definition_library import (
    build_it_dictionary,
    build_proof_first_it_entries,
    proof_first_dictionary_entry,
    search_it_dictionary,
)


def test_it_dictionary_includes_light_speed_seed_terms() -> None:
    entries = build_proof_first_it_entries(Path.cwd())
    terms = {entry["canonical_term"]: entry for entry in entries}

    for expected in [
        "Z Axis",
        "Z Direct",
        "Smart Floor",
        "Bento",
        "Neo",
        "Achilles",
        "Cognigrex",
        "Oracle",
        "Morpheus",
        "Smith",
        "Merovingian",
        "TheConstruct",
        "Architect",
        "Trinity",
    ]:
        assert expected in terms


def test_floor_aliases_and_proof_first_fields_are_present() -> None:
    entries = build_proof_first_it_entries(Path.cwd())
    by_term = {entry["canonical_term"]: entry for entry in entries}

    construct = by_term["TheConstruct"]
    neo = by_term["Neo"]
    bento = by_term["Bento"]

    assert "C-A" in construct["aliases"]
    assert "Z0" in construct["aliases"]
    assert "Z+2" in neo["aliases"]
    assert "N" in neo["aliases"]
    assert bento["category"] == "ui"
    assert bento["owner_floor"] == "Trinity"
    assert bento["confidence"] == "high"
    assert bento["provenance"]["source"] == "curated_seed_set"
    assert bento["provenance"]["proofing_status"] == "curated_definition"


def test_search_it_dictionary_supports_category_lookup_and_suffix_search() -> None:
    entries = build_proof_first_it_entries(Path.cwd())

    all_it = search_it_dictionary("IT", entries=entries)
    neo = search_it_dictionary("neo.IT", entries=entries)
    c_a = search_it_dictionary("C-A.IT", entries=entries)

    assert len(all_it) == len(entries)
    assert any(entry["canonical_term"] == "Neo" for entry in neo)
    assert any(entry["canonical_term"] == "Construct-Architect Bridge" for entry in c_a)
    assert any("C-A" in entry["aliases"] for entry in c_a)


def test_dictionary_build_includes_proof_first_index_and_alias_lookup() -> None:
    payload = build_it_dictionary(Path.cwd())

    assert payload["dictionary"] == "IT"
    assert "proof_first_terms" in payload
    assert "alias_index" in payload
    assert payload["alias_index"]["neo"] == ["neo"]
    assert any(item["canonical_term"] == "Smart Floor" for item in payload["proof_first_terms"])
    assert any(item["term"] == "Bento" for item in payload["proof_first_terms"])


def test_proof_first_dictionary_entry_shape() -> None:
    entry = proof_first_dictionary_entry(
        "neo",
        {
            "term": "Neo",
            "category": "floor",
            "dictionary_category": "IT",
            "shorthand": "N",
            "definition": "The operator shell.",
            "owner_floor": "Neo",
            "aliases": ["operator shell"],
            "floor_aliases": ["Z+2", "N"],
            "confidence": "high",
            "operational_use": "Explain and route actions.",
        },
    )

    assert entry["category"] == "floor"
    assert entry["canonical_term"] == "Neo"
    assert "operator shell" in entry["aliases"]
    assert "Z+2" in entry["aliases"]
    assert entry["owner_floor"] == "Neo"
    assert entry["confidence"] == "high"
    assert entry["provenance"]["operational_use"] == "Explain and route actions."
