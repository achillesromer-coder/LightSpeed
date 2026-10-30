#!/usr/bin/env python3
"""JPL Horizons VECTORS request specification; source review only.

No network access, ephemeris parser, numerical solver, source admission,
signed lease, DBR readback, or publication authority is implemented here.
Source: https://ssd-api.jpl.nasa.gov/doc/horizons.html (API v1.3, 2025 June).
"""
from __future__ import annotations

from urllib.parse import quote, urlencode

SCHEMA = "CGX-HORIZONS-VECTORS-REQUEST-REVIEW/0.1"
ENDPOINT = "https://ssd.jpl.nasa.gov/api/horizons.api"
DOC = "https://ssd-api.jpl.nasa.gov/doc/horizons.html"
TARGETS = (199, 299, 399, 499, 599, 699, 799, 899)
EPOCH_UT = "2025-Jun-04 12:00:00"

def plan_vector_request(target_naif: int) -> dict:
    """Specify one exact, unexecuted heliocentric state-vector request.

    Distinguishes Earth center 399 from Earth-Moon barycenter 3.
    UT is the Horizons input/output time-scale request, not a claim that
    returned dynamical epochs are numerically identical to TDB.
    """
    if type(target_naif) is not int or target_naif not in TARGETS:
        raise ValueError("TARGET_MUST_BE_ONE_OF_EIGHT_PLANET_CENTERS")
    params = {
        "format": "text",
        "COMMAND": f"'{target_naif}'",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'VECTORS'",
        "CENTER": "'500@10'",
        "TLIST": f"'{EPOCH_UT}'",
        "TLIST_TYPE": "'CAL'",
        "TIME_TYPE": "'UT'",
        "REF_PLANE": "'ECLIPTIC'",
        "REF_SYSTEM": "'ICRF'",
        "OUT_UNITS": "'KM-S'",
        "VEC_TABLE": "'2'",
        "VEC_CORR": "'NONE'",
        "TIME_DIGITS": "'SECONDS'",
    }
    url = ENDPOINT + "?" + urlencode(params, quote_via=quote)
    return {
        "schema": SCHEMA,
        "source_documentation": DOC,
        "target_naif": target_naif,
        "epoch_input": EPOCH_UT,
        "time_scale_requested": "UT",
        "origin": "500@10",
        "reference_plane": "ECLIPTIC",
        "reference_system": "ICRF",
        "units": "KM-S",
        "vector_table": 2,
        "correction": "NONE",
        "url": url,
        "evidence_stage": "REQUEST_SPEC_ONLY",
        "network_executed": False,
        "raw_source_verified": False,
        "numerical_result_verified": False,
        "native_admitted": False,
        "runtime_verified": False,
    }
