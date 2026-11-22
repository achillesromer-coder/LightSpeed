"""CGX PrintSpace portable digital object/facet projection, not native LOAD or mint.

Pure, bounded, deterministic JSON object graph from the owner-referenced virtual
factory catalogue. Geometry facets are deduplicated, products reference children,
source references remain opaque (no material bodies, secrets, CAD or rights copied).
Integrity hashes are SELF-CONSISTENCY only. Independent source/rights signatures,
native FileSpace/DataSpace admission, and all physical manufacture remain external.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
import zlib
from typing import Any

from .virtual_factory import canonical_digest, validate_catalogue

SCHEMA = 'CGX-PRINTSPACE-FILESPACE-BUNDLE/0.1'
H0_SCHEMA = 'CGX-PRINTSPACE-LOAD-LITE-H0/0.1'
TRANSPORT_SCHEMA = 'CGX-PRINTSPACE-CANONICAL-ZLIB-TRANSPORT/0.1'
REVIEW_SCHEMA = 'CGX-PRINTSPACE-HYDRATION-REVIEW/0.1'
MAX_OBJECTS = 512
MAX_SOURCE_BYTES = 1024 * 1024
MAX_DEPTH = 24
SHA = re.compile(r'^sha256:[0-9a-f]{64}$')
ALIAS = re.compile(r'^(?:source|printer|environment|primitive|part|stage|product|root)/[a-zA-Z0-9._/-]{1,150}$')
FORBIDDEN = {'machine_command','gcode','native_dbr_receipt','calibration_certificate',
             'signed_licence','material_source_bytes','cad_source_bytes','toolpath',
             'private_data','password','token','api_key'}

class CGXHold(ValueError):
    """Fail-closed bundle/transport review; never implies device authorisation."""

def _raw(data: Any) -> bytes:
    try:
        value = json.dumps(data, ensure_ascii=True, sort_keys=True,
                           separators=(',', ':'), allow_nan=False).encode('ascii')
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        raise CGXHold('NONCANONICAL_OR_NONFINITE_JSON') from exc
    if len(value) > MAX_SOURCE_BYTES:
        raise CGXHold('BUNDLE_SIZE_BUDGET')
    return value

def _sha(data: Any) -> str:
    return 'sha256:' + hashlib.sha256(_raw(data)).hexdigest()

def _check_no_authority(data: Any, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise CGXHold('MAX_JSON_NESTING')
    if isinstance(data, dict):
        if any(str(k).lower() in FORBIDDEN for k in data):
            raise CGXHold('UNAUTHORISED_NATIVE_OR_MACHINE_FIELD')
        for v in data.values():
            _check_no_authority(v, depth+1)
    elif isinstance(data, list):
        for v in data:
            _check_no_authority(v, depth+1)

def _node(kind: str, payload: dict, deps: list[str]) -> dict:
    if not isinstance(payload, dict) or len(deps) != len(set(deps)):
        raise CGXHold('NONCANONICAL_NODE_DEPENDENCIES')
    return {'kind':kind, 'payload':payload, 'deps':sorted(deps),
            'device_authorised':False, 'native_admitted':False}


def build_bundle(catalogue: dict) -> dict:
    """Deterministic immutable shorthand facets, compositional product DAG.

    This is a source-addressed projection of the previously accepted synthetic
    catalogue, NOT an assertion that every geometric sub-part can be printed.
    """
    try:
        validate_catalogue(catalogue)
    except (ValueError, KeyError, TypeError, RecursionError) as exc:
        raise CGXHold('SOURCE_CATALOGUE_INVALID') from exc
    source_sha = canonical_digest(catalogue)
    objects: dict[str, dict] = {}
    aliases: dict[str, str] = {}
    def add(alias: str, kind: str, payload: dict, deps: list[str] = None) -> str:
        if not isinstance(alias, str) or not ALIAS.fullmatch(alias):
            raise CGXHold('INVALID_ALIAS')
        if alias in aliases:
            raise CGXHold('DUPLICATE_ALIAS')
        item = _node(kind, payload, deps or [])
        _check_no_authority(item)
        key = _sha(item)
        if len(objects) >= MAX_OBJECTS and key not in objects:
            raise CGXHold('OBJECT_BUDGET')
        objects[key] = item
        aliases[alias] = key
        return key

    for name, ref in sorted(catalogue['source_refs'].items()):
        if not isinstance(ref,str) or not ref.strip():
            raise CGXHold('INVALID_EXTERNAL_SOURCE_REF')
        add('source/'+name, 'opaque-source-reference',
            {'ref':ref, 'original_bytes_embedded':False,
             'signature_verified':False,'owner_rights_verified':False})

    by_machine = {}
    for role in sorted(catalogue['printer_families'],key=lambda o:o['id']):
        by_machine[role['id']] = add('printer/'+role['id'], 'printer-family-role',
            {'source_role':copy.deepcopy(role),
             'nominal_machine_dimensions':None,'real_toolheads_verified':False})
    for env in sorted(catalogue['environments'],key=lambda o:o['id']):
        add('environment/'+env['id'],'operating-environment-assumption',
            {'source_profile':copy.deepcopy(env), 'real_environment_qualified':False})

    product_by_id={x['id']:x for x in catalogue['products']}
    product_keys:dict[str,str]={}
    primitive_keys:dict[str,str]={}
    active:set[str]=set()
    def product_key(product_id: str) -> str:
        if product_id in product_keys:
            return product_keys[product_id]
        if product_id in active:
            raise CGXHold('PRODUCT_REFERENCE_CYCLE')
        active.add(product_id)
        p = product_by_id[product_id]
        child_refs = {part['parent']: product_key(part['parent'])
                      for part in p['parts'] if part['parent'] is not None}
        part_keys={}
        for part in sorted(p['parts'],key=lambda x:x['id']):
            box_key = 'primitive/box-'+_sha({'units':'mm','size_mm':part['size']})[-64:]
            if box_key not in aliases:
                add(box_key,'illustrative-geometry-primitive',
                    {'shape':'axis-aligned-box','units':'mm','nominal_size_mm':copy.deepcopy(part['size']),
                     'cad_source_verified':False,'geometry_mesh_admitted':False})
            primitive_keys[box_key] = aliases[box_key]
            deps=[aliases[box_key],by_machine[part['printer_family']]]
            if part['parent'] is not None:
                deps.append(child_refs[part['parent']])
            part_keys[part['id']]=add('part/'+product_id+'/'+part['id'],'product-part-placement',
                {'product_id':product_id,'part_id':part['id'], 'title':part['title'],
                 'position_mm':copy.deepcopy(part['xyz']), 'source_kind':part['origin'],
                 'status':part['status'], 'shape_alias':box_key,
                 'child_product_id':part['parent'],
                 'electrical_or_material_function_verified':False}, deps)
        stages=[]
        for i,step in enumerate(p['steps']):
            code,title,tool,target=step
            stage_deps=[by_machine[tool]]+([part_keys[target]] if target else [])
            stages.append(add('stage/'+product_id+'/'+str(i),'nonactuating-process-stage',
                {'ordinal':i, 'name':code, 'title':title,'machine_role':tool,
                 'target_part_id':target,'executed':False,'real_sensor_receipt':None},stage_deps))
        pk=add('product/'+product_id,'nested-digital-assembly',
            {'product_id':product_id,'product_key':p['key'],'title':p['title'],
             'bounds_mm':copy.deepcopy(p['bounds_mm']),
             'source_assembly_authentic':False, 'physical_printability_verified':False,
             'external_parts_require_individual_source_rights':True},
            list(part_keys.values())+stages+list(child_refs.values()))
        active.remove(product_id)
        product_keys[product_id]=pk
        return pk
    for p in sorted(catalogue['products'],key=lambda p:p['id']):
        product_key(p['id'])

    sources = [aliases['source/'+k] for k in sorted(catalogue['source_refs'])]
    root=add('root/printspace','printspace-digital-root',
        {'catalogue_identity':catalogue['catalogue_id'],'catalogue_sha256':source_sha,
         'release_gates':copy.deepcopy(catalogue['release_gates']),
         'product_ids':sorted(product_keys), 'material_lots_verified':False,
         'source_cad_verified':False, 'in_situ_qualified':False,
         'printer_physically_built_and_verified':False,
         'private_load_hydration_enabled':False,'native_dbr_written':False,
         'physical_machine_authorised':False,'commercial_release_authorised':False},
        list(product_keys.values())+sources+list(by_machine.values())+[aliases["environment/"+x["id"]] for x in catalogue["environments"]])
    document={'schema':SCHEMA,'format':'CANONICAL_JSON_UTF8_SHA256_SELF_CHECK_ONLY',
              'state':'DIGITAL_REFERENCE_ONLY_NATIVE_UNADMITTED',
              'source_catalogue_sha256':source_sha, 'root':root,
              'aliases':dict(sorted(aliases.items())), 'objects':dict(sorted(objects.items())),
              'source_bytes_hydrated':0, 'content_addressed':True,
              'native_load_hydration':False, 'machine_authorised':False,
              'mint_authorised':False,'commercial_release_authorised':False}
    document['bundle_sha256']=_sha(document)
    check_bundle(document, expected_catalogue_sha256=source_sha)
    return document


def check_bundle(bundle: Any, *, expected_catalogue_sha256: str | None = None) -> dict:
    """Verify internal hash, exact dependency closure and acyclic graph.

    An unauthenticated, self-signed substitute can still be self-consistent.
    Require a trusted separately held source SHA for identity assurance.
    """
    if not isinstance(bundle,dict) or set(bundle) != {
        'schema','format','state','source_catalogue_sha256','root','aliases','objects',
        'source_bytes_hydrated','content_addressed','native_load_hydration',
        'machine_authorised','mint_authorised','commercial_release_authorised','bundle_sha256'}:
        raise CGXHold('BUNDLE_SCHEMA_OR_UNEXPECTED_FIELDS')
    if (bundle['schema']!=SCHEMA or bundle['state']!='DIGITAL_REFERENCE_ONLY_NATIVE_UNADMITTED'
        or bundle['format']!='CANONICAL_JSON_UTF8_SHA256_SELF_CHECK_ONLY'
        or bundle['source_bytes_hydrated']!=0 or bundle['native_load_hydration'] is not False
        or bundle['content_addressed'] is not True
        or any(bundle[k] is not False for k in ('machine_authorised','mint_authorised','commercial_release_authorised'))):
        raise CGXHold('AUTHORITY_ESCALATION')
    _check_no_authority(bundle)
    if not isinstance(bundle['source_catalogue_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',bundle['source_catalogue_sha256']):
        raise CGXHold('INVALID_SOURCE_SHA')
    if (expected_catalogue_sha256 is not None
        and expected_catalogue_sha256!=bundle['source_catalogue_sha256']):
        raise CGXHold('TRUSTED_CATALOGUE_SHA_MISMATCH')
    objects=bundle['objects'];aliases=bundle['aliases']
    if not isinstance(objects,dict) or not 1<=len(objects)<=MAX_OBJECTS or not isinstance(aliases,dict):
        raise CGXHold('OBJECT_OR_INDEX_BUDGET')
    if len(_raw(bundle))>MAX_SOURCE_BYTES:
        raise CGXHold('BUNDLE_SIZE_BUDGET')
    if not isinstance(bundle['root'],str) or bundle['root'] not in objects:
        raise CGXHold('ROOT_MISSING')
    if aliases.get('root/printspace') != bundle['root']:
        raise CGXHold('ROOT_ALIAS_MISMATCH')
    for alias,key in aliases.items():
        if not isinstance(alias,str) or not ALIAS.fullmatch(alias) or key not in objects:
            raise CGXHold('BROKEN_ALIAS')
    for key, obj in objects.items():
        if not isinstance(key,str) or not SHA.fullmatch(key) or not isinstance(obj,dict) or set(obj)!={'kind','payload','deps','device_authorised','native_admitted'}:
            raise CGXHold('OBJECT_SCHEMA')
        if obj['device_authorised'] is not False or obj['native_admitted'] is not False:
            raise CGXHold('OBJECT_AUTHORITY_ESCALATION')
        if not isinstance(obj['payload'],dict) or not isinstance(obj['kind'],str) or not obj['kind']:
            raise CGXHold('OBJECT_BODY_INVALID')
        if not isinstance(obj['deps'],list) or obj['deps']!=sorted(set(obj['deps'])) or any(x not in objects for x in obj['deps']):
            raise CGXHold('INVALID_DEPENDENCY_REFERENCE')
        if _sha(obj)!=key:
            raise CGXHold('OBJECT_HASH_MISMATCH')
    visited:set[str]=set();active:set[str]=set()
    def walk(key: str, depth: int) -> None:
        if depth>MAX_DEPTH:raise CGXHold('DEPENDENCY_DEPTH_BUDGET')
        if key in active:raise CGXHold('CYCLE')
        if key in visited:return
        active.add(key)
        for dep in objects[key]['deps']:walk(dep,depth+1)
        active.remove(key);visited.add(key)
    walk(bundle['root'],0)
    if len(visited)!=len(objects):
        raise CGXHold('UNREACHABLE_OR_UNINDEXED_FACETS')
    body={k:v for k,v in bundle.items() if k!='bundle_sha256'}
    if _sha(body)!=bundle['bundle_sha256']:
        raise CGXHold('ROOT_MANIFEST_TAMPERED')
    return {'state':'PASS_DIGITAL_INTEGRITY_ONLY', 'bundle_sha256':bundle['bundle_sha256'],
            'objects':len(objects),'aliases':len(aliases),
            'source_bodies_authenticated':False,'rights_verified':False,
            'machine_authorised':False,'native_dbr_written':False}


def h0_handshake(bundle: dict, *, expected_catalogue_sha256: str | None = None) -> dict:
    """Small non-hydrating first-contact index, never serialises source bodies."""
    audit=check_bundle(bundle,expected_catalogue_sha256=expected_catalogue_sha256)
    return {'schema':H0_SCHEMA,'state':'H0_NONHYDRATING_SOURCE_INDEX_ONLY',
            'bundle_sha256':bundle['bundle_sha256'],'catalogue_sha256':bundle['source_catalogue_sha256'],
            'root_ref':bundle['root'],'products':{alias:key for alias,key in bundle['aliases'].items() if alias.startswith('product/')},
            'root_namespace':'cgx://romer.industries/romer/printspace/','object_count':audit['objects'],
            'source_bytes_hydrated':0,'native_admitted':False,
            'machine_authorised':False, 'parent_dbr_receipt':None}


def hydrate(bundle: dict, *, product_id: str | None = None,
            mode: str = 'SUBTREE_DIGITAL', max_nodes: int = 128,
            max_bytes: int = MAX_SOURCE_BYTES,
            expected_catalogue_sha256: str | None = None) -> dict:
    """Read-only selective hydration, full provenance preserved as hashes.

    H0 does not resolve object bodies. SUBTREE_DIGITAL hydrates selected assembly,
    its child products, parts, geometry, stage and printer-role dependencies.
    ALL_DIGITAL resolves all self-contained symbolic facets, not external assets.
    """
    audit=check_bundle(bundle,expected_catalogue_sha256=expected_catalogue_sha256)
    if mode not in ('H0','SUBTREE_DIGITAL','ALL_DIGITAL'):
        raise CGXHold('NATIVE_OR_UNSUPPORTED_HYDRATION_REQUEST')
    if type(max_nodes) is not int or not 1<=max_nodes<=MAX_OBJECTS:
        raise CGXHold('NODE_BUDGET_INVALID')
    if type(max_bytes) is not int or not 1024<=max_bytes<=MAX_SOURCE_BYTES:
        raise CGXHold('BYTE_BUDGET_INVALID')
    if mode=='H0':
        return {'schema':REVIEW_SCHEMA,'state':'H0_NO_OBJECTS_RESOLVED',
                'h0':h0_handshake(bundle,expected_catalogue_sha256=expected_catalogue_sha256),
                'objects':{},'objects_hydrated':0,'machine_authorised':False}
    if mode=='SUBTREE_DIGITAL':
        if not isinstance(product_id,str) or ('product/'+product_id) not in bundle['aliases']:
            raise CGXHold('UNKNOWN_PRODUCT_ALIAS')
        starts=[bundle['aliases']['product/'+product_id]]
    else:
        if product_id is not None:raise CGXHold('PRODUCT_SELECTOR_IN_FULL_MODE')
        starts=[bundle['root']]
    selected:set[str]=set()
    def walk(k: str, depth: int) -> None:
        if depth>MAX_DEPTH:raise CGXHold('SUBTREE_DEPTH_BUDGET')
        if k in selected:return
        selected.add(k)
        if len(selected)>max_nodes:raise CGXHold('HYDRATION_NODE_BUDGET')
        for d in bundle['objects'][k]['deps']:walk(d,depth+1)
    for k in starts:walk(k,0)
    resolved={k:copy.deepcopy(bundle['objects'][k]) for k in sorted(selected)}
    body={'schema':REVIEW_SCHEMA,'state':'DIGITAL_SYMBOLIC_FACETS_ONLY',
          'bundle_sha256':bundle['bundle_sha256'],'selected_product':product_id,
          'resolved_anchors':sorted(starts), 'objects':resolved,
          'aliases':{a:k for a,k in bundle['aliases'].items() if k in selected},
          'objects_hydrated':len(resolved), 'source_bytes_hydrated':0,
          'external_asset_downloads':0,'native_load_hydrated':False,
          'machine_authorised':False,'material_qualified':False,
          'commercial_release_authorised':False}
    if len(_raw(body))>max_bytes:raise CGXHold('HYDRATION_BYTE_BUDGET')
    return body


def verify_back_down(bundle: Any, original_catalogue: dict) -> dict:
    """Recompile against the original source, not the bundle's own hash alone."""
    try:
        expected=build_bundle(original_catalogue)
        check_bundle(bundle,expected_catalogue_sha256=canonical_digest(original_catalogue))
    except (CGXHold,ValueError,KeyError,TypeError):
        return {'state':'HOLD','reason':'SOURCE_OR_INTERNAL_IDENTITY_UNVERIFIED',
                'machine_authorised':False,'source_authenticated':False}
    return {'state':'PASS_DIGITAL_ONLY' if expected==bundle else 'HOLD',
            'reason':'SOURCE_RECOMPILE_EXACT' if expected==bundle else 'SOURCE_OR_FACET_DRIFT',
            'root_sha256':expected['bundle_sha256'],'objects':len(expected['objects']),
            'source_authenticated':False,'rights_verified':False,
            'physical_qualification':False,'machine_authorised':False,'native_dbr_written':False}



# The source mesh on the separate review branch declares these five views of
# ONE root. They are not five engines, stores, filespaces or native abilities.
SPACE_FACETS = frozenset((
    'file_space', 'data_space', 'print_space', 'social_space', 'intelligence_space',
))
PARENT_ROOT = 'Cognigrex.cgx'
ROMER_CHILD = 'Romer.cgx'
ROMER_URI = 'cgx://romer.industries/romer'


def project_space_context(bundle: dict, original_catalogue: dict,
                          domains: dict, topology: dict, *,
                          product_id: str = 'diode', facet: str = 'print_space',
                          representation: str = 'auto') -> dict:
    """Use existing source metadata to inspect ONE space through ONE CGX root.

    The contract inputs must be re-read from independently checked source files
    upstream. Their hashes in this result are self-consistency, NOT signed
    authority. T173 mesh and native ternary require independent admission; a
    synthetic box and zlib JSON do not become either by renaming a field.
    """
    if facet not in SPACE_FACETS or type(product_id) is not str:
        raise CGXHold('UNKNOWN_SPACE_OR_PRODUCT')
    if representation not in ('auto', 'canonical_json', 't173', 'ternary'):
        raise CGXHold('UNKNOWN_REPRESENTATION')
    if representation == 't173':
        raise CGXHold('T173_EXACT_MESH_AND_RIGHTS_ADMISSION_MISSING')
    if representation == 'ternary':
        raise CGXHold('NATIVE_TERNARY_TRANSPORT_NOT_ADMITTED')
    if (not isinstance(domains, dict) or not isinstance(topology, dict)
            or domains.get('schema') != 'CGX-DOMAIN-TEMPLATES/0.4'
            or topology.get('schema') != 'CGX-COGNIGREX-PARENT-TOPOLOGY/0.2'
            or domains.get('parent_filespace', {}).get('file') != PARENT_ROOT
            or topology.get('root', {}).get('file') != PARENT_ROOT):
        raise CGXHold('CANONICAL_PARENT_SOURCE_MISMATCH')
    child = domains.get('domains', {}).get('romer')
    actual_children = topology.get('root', {}).get('children')
    if (not isinstance(child, dict) or not isinstance(actual_children, list)
            or child.get('file') != ROMER_CHILD
            or child.get('namespace') != ROMER_URI
            or sum(type(c) is dict and c.get('id') == 'romer'
                   and c.get('file') == ROMER_CHILD for c in actual_children) != 1):
        raise CGXHold('ROMER_CHILD_SOURCE_MISMATCH')
    _check_no_authority(domains)
    _check_no_authority(topology)
    # It is essential that a self-consistent substitute bundle cannot supply
    # the original expected source without a recompilation and comparison.
    if verify_back_down(bundle, original_catalogue)['state'] != 'PASS_DIGITAL_ONLY':
        raise CGXHold('ORIGINAL_CATALOGUE_REPLAY_REQUIRED')
    alias='product/'+product_id
    if alias not in bundle['aliases']:
        raise CGXHold('UNKNOWN_PRODUCT_ALIAS')
    audit=check_bundle(bundle, expected_catalogue_sha256=canonical_digest(original_catalogue))
    key=bundle['aliases'][alias]
    # No physical or private source data is hydrated by these views.
    details={
        'file_space': {'view': 'CONTENT_ADDRESS_AND_H0', 'geometry':'NOT_RESOLVED',
                       'payload_objects': 0, 'external_asset_bytes':0},
        'data_space': {'view': 'EVIDENCE_REFS_ONLY', 'geometry':'NOT_RESOLVED',
                       'payload_objects':0, 'measured_readings':None,
                       'source_rights_and_lot_attestations':None},
        'print_space': {'view':'NOMINAL_DIGITAL_GEOMETRY_AND_SEQUENCE',
                        'geometry':'SYNTHETIC_AXIS_ALIGNED_BOX_MM',
                        'payload_objects':hydrate(bundle,product_id=product_id,
                                                 expected_catalogue_sha256=bundle['source_catalogue_sha256'])['objects_hydrated'],
                        't173_admitted':False, 'real_toolpath':None},
        'social_space': {'view':'PROVENANCE_CONTEXT_ONLY', 'geometry':'NOT_RESOLVED',
                         'payload_objects':0, 'messages_sent':0},
        'intelligence_space': {'view':'SOURCE_AWARE_PLANNING_ONLY', 'geometry':'NOT_RESOLVED',
                               'payload_objects':0, 'model_inference_executed':False},
    }
    projection={
        'schema':'CGX-PRINTSPACE-SINGLE-ROOT-SPACE-PROJECTION/0.1',
        'state':'SOURCE_REPLAYED_DIGITAL_REVIEW_ONLY',
        'root_carrier':PARENT_ROOT, 'child_carrier':ROMER_CHILD,
        'canonical_child_namespace':ROMER_URI,
        'product_alias':alias, 'product_facet_sha256':key,
        'selected_space':facet, 'representation':'CANONICAL_JSON_DIGITAL_REVIEW_ONLY',
        'facet_view':details[facet],
        'source_refs':{'domain_registry_sha256':_sha(domains),
                       'parent_topology_sha256':_sha(topology),
                       'catalogue_sha256':bundle['source_catalogue_sha256'],
                       'bundle_sha256':bundle['bundle_sha256']},
        'available_spaces':sorted(SPACE_FACETS),
        'source_facets':audit['objects'], 'h0_native_admitted':False,
        'source_rights_authenticated':False, 'native_ternary_encoded':False,
        't173_exact_mesh_admitted':False, 'native_file_or_data_space_attached':False,
        'native_dbr_written':False, 'machine_authorised':False,
        'commercial_release_authorised':False,
    }
    projection['projection_sha256']=_sha(projection)
    return projection


def verify_space_context_back_down(claimed: Any, bundle: dict,
                                   original_catalogue: dict, domains: dict,
                                   topology: dict, *, product_id: str = 'diode',
                                   facet: str = 'print_space',
                                   representation: str = 'auto') -> dict:
    """Recompute from all four original inputs, never trust claimed hashes."""
    try:
        expected=project_space_context(bundle,original_catalogue,domains,topology,
                                       product_id=product_id,facet=facet,
                                       representation=representation)
    except (CGXHold,KeyError,TypeError,ValueError,RecursionError):
        return {'state':'HOLD','native_admitted':False,'machine_authorised':False}
    return {'state':'PASS_DIGITAL_ONLY' if type(claimed) is dict and claimed==expected else 'HOLD',
            'projection_sha256':expected['projection_sha256'],
            'native_admitted':False,'machine_authorised':False}


def pack_lite(bundle: dict, *, expected_catalogue_sha256: str | None = None) -> dict:
    """Portable deterministic zlib bridge. Not native ternary CGX compression."""
    check_bundle(bundle,expected_catalogue_sha256=expected_catalogue_sha256)
    raw=_raw(bundle)
    compressed=zlib.compress(raw,level=9)
    return {'schema':TRANSPORT_SCHEMA,'codec':'CANONICAL_JSON_ZLIB_LEVEL9_BASE64',
            'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'raw_bytes':len(raw),'compressed_bytes':len(compressed),
            'payload_b64':base64.b64encode(compressed).decode('ascii'),
            'native_ternary_encoder':False, 'native_dbr_written':False,
            'physical_machine_authorised':False}


def unpack_lite(envelope: Any, *, expected_catalogue_sha256: str | None = None) -> dict:
    if not isinstance(envelope,dict) or set(envelope)!={
        'schema','codec','raw_sha256','raw_bytes','compressed_bytes','payload_b64',
        'native_ternary_encoder','native_dbr_written','physical_machine_authorised'}:
        raise CGXHold('TRANSPORT_SCHEMA')
    if (envelope['schema']!=TRANSPORT_SCHEMA or envelope['codec']!='CANONICAL_JSON_ZLIB_LEVEL9_BASE64'
        or any(envelope[k] is not False for k in ('native_ternary_encoder','native_dbr_written','physical_machine_authorised'))
        or type(envelope['raw_bytes']) is not int or not 1<=envelope['raw_bytes']<=MAX_SOURCE_BYTES
        or type(envelope['compressed_bytes']) is not int or not 1<=envelope['compressed_bytes']<=MAX_SOURCE_BYTES):
        raise CGXHold('TRANSPORT_HEADER_INVALID')
    try:
        compressed=base64.b64decode(envelope['payload_b64'],validate=True)
        if len(compressed)!=envelope['compressed_bytes']:raise CGXHold('TRANSPORT_LENGTH_MISMATCH')
        decompressor=zlib.decompressobj()
        raw=decompressor.decompress(compressed,MAX_SOURCE_BYTES+1)
        if len(raw)>MAX_SOURCE_BYTES or not decompressor.eof or decompressor.unconsumed_tail or decompressor.unused_data:
            raise CGXHold('TRANSPORT_BUDGET_OR_TRAILING_BYTES')
        if len(raw)!=envelope['raw_bytes'] or hashlib.sha256(raw).hexdigest()!=envelope['raw_sha256']:
            raise CGXHold('TRANSPORT_HASH_MISMATCH')
        bundle=json.loads(raw)
        if _raw(bundle)!=raw:raise CGXHold('NONCANONICAL_TRANSPORT_BODY')
        check_bundle(bundle,expected_catalogue_sha256=expected_catalogue_sha256)
        return bundle
    except (ValueError,TypeError,KeyError,zlib.error,RecursionError) as exc:
        raise CGXHold('TRANSPORT_INVALID_OR_UNREADABLE') from exc