"""CGX PrintSpace -> existing UniSpace LOAD R0 host-review crosswalk.

This is one read-only adapter to the existing canonical CGX FileSpace graph,
NOT a native Object_ID registration or trusted ACL/rights/DBR authority.

For each product the exact symbolic source facet can be verified against the
original catalogue. Host/lineage evidence is a future independent readback:
caller-supplied Git blob SHA-1 and semantic IDs are *candidates*, never proof.
The output is the minimum, non-secret input for the existing
cgxHostObjectContextGate.mjs and cgxLoadLibraryLensPlan.mjs review adapters.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .printspace_cgx import CGXHold, build_bundle, check_bundle, h0_handshake, _raw
from .virtual_factory import canonical_digest

SCHEMA = 'CGX-PRINTSPACE-UNISPACE-HOST-R0-PREFLIGHT/0.1'
BACKTRACE_SCHEMA = 'CGX-PRINTSPACE-UNISPACE-HOST-R0-BACKTRACE/0.1'
VALID_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$')
SHA1 = re.compile(r'^[0-9a-f]{40}$')
MAX_BYTES = 32 * 1024
# Existing UniSpace host context gate accepts the Romer child, not a separately
# admitted PrintSpace.cgx root. PrintSpace here is a scope *within* Romer.
CHILD = {'semantic_object_id':'cgx:domain:romer','filespace':'Romer.cgx','domain':'romer'}
REQUIRED_HOLDS = [
    'EXACT_HOST_OBJECT_ID_AND_COLLISION_READBACK_PENDING',
    'SOURCE_LINEAGE_AND_REGISTRY_NOT_INDEPENDENTLY_AUTHENTICATED',
    'PARENT_RIGHTS_ACL_AND_DB_REVIEW_PENDING',
    'NATIVE_LOAD_AND_PRIVATE_HYDRATION_NOT_AUTHORISED',
    'PHYSICAL_MACHINE_C0_AND_MATERIAL_TESTS_PENDING',
]
FORBIDDEN = {
    'token','password','cookie','authorization','secret','api_key',
    'source_bytes','cad_source_bytes','material_source_bytes','private_path',
    'file_path','source_locator','asset_url','source_url','url','lease',
    'session','dbr_root','machine_command','gcode','toolpath','signature',
    'source_registry','material_lot_passport','signed_licence',
}


def _hold(reason: str) -> dict:
    return {
        'schema': SCHEMA, 'state': 'HOLD', 'hold_codes': [reason],
        'r0_cases': [], 'plan_sha256': None,
        'trusted_host_authenticated': False, 'native_admitted': False,
        'source_bytes_hydrated': 0, 'machine_authorised': False,
        'native_dbr_written': False, 'mint_authorised': False,
        'commercial_release_authorised': False,
    }


def _screen(data: Any, depth: int = 0) -> bool:
    if depth > 12:
        return False
    if isinstance(data, dict):
        if any(not isinstance(k, str) or k.lower() in FORBIDDEN for k in data):
            return False
        return all(_screen(v, depth+1) for v in data.values())
    if isinstance(data, list):
        return all(_screen(x, depth+1) for x in data)
    return data is None or isinstance(data, (str, int, float, bool))


def _digest(data: Any) -> str:
    return hashlib.sha256(_raw(data)).hexdigest()


def _valid_id(value: Any) -> bool:
    return (isinstance(value, str) and VALID_ID.fullmatch(value) is not None
            and not value.startswith('cgx:domain:')
            and value != 'cgx:root:cognigrex'
            and value not in ('LOAD.cgx', 'Romer.cgx','PrintSpace.cgx'))


def _safe_json(data: Any) -> bool:
    if not _screen(data):
        return False
    try:
        return len(_raw(data)) <= MAX_BYTES
    except (TypeError, ValueError, OverflowError, RecursionError, CGXHold):
        return False


def prepare_r0_host_review(bundle: Any, original_catalogue: Any,
                           product_bindings: Any = None) -> dict:
    """Build immutable product facet-to-candidate R0 requests with hard holds.

    product_bindings is optional: when present, provide one dictionary per
    product {product_id, candidate_object_id, twin_id,
    lineage_git_blob_sha, registry_git_blob_sha}. Even correct-looking IDs
    and SHA-1s are NOT source verified or host admission.

    An absent binding is intentionally reviewable as missing provenance.
    """
    if not isinstance(bundle, dict) or not isinstance(original_catalogue, dict):
        return _hold('MISSING_CANONICAL_CGX_SOURCES')
    try:
        expected = build_bundle(original_catalogue)
        check_bundle(bundle, expected_catalogue_sha256=canonical_digest(original_catalogue))
    except (CGXHold, ValueError, KeyError, TypeError, RecursionError):
        return _hold('SOURCE_GRAPH_OR_CATALOGUE_NOT_VERIFIED')
    if expected != bundle:
        return _hold('SOURCE_CATALOGUE_EXACT_REPLAY_MISMATCH')
    product_keys = {k.split('/',1)[1]:v for k,v in bundle['aliases'].items()
                    if k.startswith('product/')}
    if not product_keys or len(product_keys) > 32:
        return _hold('PRODUCT_SOURCE_SCOPE_INVALID')
    if product_bindings is None:
        product_bindings = []
    if not isinstance(product_bindings, list) or len(product_bindings) > len(product_keys):
        return _hold('BINDING_SCOPE_OR_LENGTH_INVALID')
    if not _safe_json(product_bindings):
        return _hold('PRIVATE_OR_NONCANONICAL_SOURCE_INPUT')
    bindings = {}
    used_ids = set()
    for row in product_bindings:
        if not isinstance(row, dict) or set(row) != {
            'product_id', 'candidate_object_id','twin_id',
            'lineage_git_blob_sha','registry_git_blob_sha'
        }:
            return _hold('BINDING_SCHEMA_OR_EXTRA_AUTHORITY')
        product_id = row['product_id']
        if not isinstance(product_id, str) or product_id not in product_keys or product_id in bindings:
            return _hold('UNKNOWN_OR_DUPLICATE_PRODUCT_BINDING')
        if not _valid_id(row['candidate_object_id']):
            return _hold('INVALID_NATIVE_CANDIDATE_ID')
        if row['candidate_object_id'] in used_ids:
            return _hold('NATIVE_SEMANTIC_ID_COLLISION_CANDIDATE')
        if not isinstance(row['twin_id'],str) or not _valid_id(row['twin_id']):
            return _hold('INVALID_TWIN_CANDIDATE')
        if not all(isinstance(row[k],str) and SHA1.fullmatch(row[k])
                   for k in ('lineage_git_blob_sha','registry_git_blob_sha')):
            return _hold('INVALID_REGISTRY_OR_LINEAGE_SHA1')
        bindings[product_id] = row
        used_ids.add(row['candidate_object_id'])

    h0 = h0_handshake(bundle, expected_catalogue_sha256=canonical_digest(original_catalogue))
    if (h0['source_bytes_hydrated'] != 0 or h0['native_admitted'] is not False
            or h0['parent_dbr_receipt'] is not None):
        return _hold('H0_SOURCE_AUTHORITY_BOUNDARY')
    cases=[]
    for product_id, facet_sha in sorted(product_keys.items()):
        row=bindings.get(product_id)
        compact={
            'product_id':product_id, 'product_alias':'product/'+product_id,
            'product_facet_sha256':facet_sha,
            'bundle_sha256':bundle['bundle_sha256'],
            'catalogue_sha256':bundle['source_catalogue_sha256'],
            'candidate_object_id':row['candidate_object_id'] if row else None,
            'twin_id_candidate':row['twin_id'] if row else None,
            'lineage_git_blob_sha_candidate':row['lineage_git_blob_sha'] if row else None,
            'registry_git_blob_sha_candidate':row['registry_git_blob_sha'] if row else None,
            'destination_filespace':'Romer.cgx',
            'parent_filespace':'Cognigrex.cgx',
            'child_domain':dict(CHILD),
            'r_layer':'R0', 'hydration':'H0',
            'host_context_request_ready':row is not None,
            'source_lineage_independently_verified':False,
            'source_rights_independently_verified':False,
            'native_object_admitted':False, 'physical_qualification':False,
        }
        cases.append(compact)
    plan={
        'schema':SCHEMA,
        'state':'R0_CANDIDATE_REVIEW_NOT_ADMITTED',
        'root_bundle_sha256':bundle['bundle_sha256'],
        'catalogue_sha256':bundle['source_catalogue_sha256'],
        'h0_sha256':_digest(h0),
        'parent_namespace':'Cognigrex.cgx',
        'host_child_filespace':'Romer.cgx',
        'product_count':len(cases),
        'candidate_count':len(bindings),
        'r0_cases':cases,
        'hold_codes':list(REQUIRED_HOLDS),
        'trusted_host_authenticated':False,
        'client_rights_are_not_host_authentication':True,
        'native_admitted':False,
        'source_bytes_hydrated':0,
        'machine_authorised':False,
        'native_dbr_written':False,
        'mint_authorised':False,
        'commercial_release_authorised':False,
    }
    plan['plan_sha256'] = _digest(plan)
    return plan


def verify_r0_host_review_back_down(plan: Any, bundle: Any,
                                    original_catalogue: Any,
                                    product_bindings: Any = None) -> dict:
    """Reconstruct review from original sources; fail on changed claims/aliases."""
    expected=prepare_r0_host_review(bundle, original_catalogue, product_bindings)
    ok=(isinstance(plan, dict)
        and expected.get('state') == 'R0_CANDIDATE_REVIEW_NOT_ADMITTED'
        and plan == expected)
    return {
        'schema':BACKTRACE_SCHEMA,
        'state':'PASS_DIGITAL_ONLY' if ok else 'HOLD',
        'expected_plan_sha256':expected.get('plan_sha256'),
        'declared_plan_sha256':plan.get('plan_sha256') if isinstance(plan,dict) else None,
        'exact_replay_matched':ok,
        'native_admitted':False,
        'source_rights_verified':False,
        'machine_authorised':False,
        'native_dbr_written':False,
    }
