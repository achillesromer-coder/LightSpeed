"""CGX PrintSpace virtual factory: *illustrative* printer/assembly emulation.

Reuses the existing manufacturer route family identifiers, digital geometry
reference policy, source index and review-only permissions. Visual blocks are
synthetic primitives, NOT source-verified CAD, BOM, material recipes, 4D
kinematics, validated G-code, real machine capabilities or functioning phones.
This service does not send physical motion or machine instructions.
"""
from __future__ import annotations
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any

CATALOGUE = Path(__file__).with_name('printspace_virtual_factory_catalog_v0_1.json')
SCHEMA = 'CGX-PRINTSPACE-VIRTUAL-FACTORY-REVIEW/0.1'
SHA = 'sha256:'
MODEL_BEDS_MM = {  # synthetic layout exercises, never manufacturer specifications
    'structural': (350, 350, 240), 'functional': (200, 200, 100),
    'fiber': (420, 360, 200), 'hybrid': (300, 300, 180),
    'feedstock': (300, 300, 180), 'metrology': (450, 450, 240),
    'mobile': (190, 200, 140),
}
MAX_SCENARIOS = 1024

def canonical_digest(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')).hexdigest()


def _hold(code: str) -> dict:
    return {'schema': SCHEMA,'state':'HOLD','hold_codes':[code], 'scene':None,
            'physical_machine_authorised':False,'native_dbr_written':False,
            'commercial_release_authorised':False,'printed_functionality_verified':False}


def load_catalogue(path: Path | None = None) -> dict:
    data = json.loads((path or CATALOGUE).read_text(encoding='utf-8'))
    validate_catalogue(data)
    return data


def _bounds(part: dict, bounding: list[float]) -> bool:
    if not isinstance(part, dict) or set(part) != {'id','title','xyz','size','kind','origin','parent','printer_family','status','colour','note'}:
        return False
    if not isinstance(part['id'],str) or not part['id'].strip():return False
    x,y,z = part['xyz']; dx,dy,dz = part['size']
    for value in (x,y,z,dx,dy,dz):
        if type(value) not in (int,float) or not math.isfinite(value):return False
    return all(v >= 0 for v in (x,y,z)) and all(v > 0 for v in (dx,dy,dz)) and all(a+b <= limit for a,b,limit in zip((x,y,z),(dx,dy,dz),bounding))


def validate_catalogue(data: dict) -> None:
    if not isinstance(data,dict) or data.get('schema') != 'CGX-PRINTSPACE-VIRTUAL-FACTORY-CATALOGUE/0.1':
        raise ValueError('CATALOGUE_SCHEMA')
    if data.get('status') != 'SYNTHETIC_DIGITAL_DESIGN_REVIEW_ONLY':raise ValueError('IMPROPER_SOURCE_STATUS')
    if not isinstance(data.get('attestations'),dict) or any(x is not False for x in data['attestations'].values()):
        raise ValueError('AUTHORITY_ESCALATION')
    families=data.get('printer_families'); products=data.get('products'); environments=data.get('environments')
    if not isinstance(families,list) or len(families)!=7 or not isinstance(products,list) or not 1<=len(products)<=128 or not isinstance(environments,list) or len(environments)!=3:
        raise ValueError('CATALOGUE_BOUNDS')
    keys=lambda seq:[x['id'] for x in seq]
    for seq in (families,products,environments):
        ids=keys(seq)
        if len(ids)!=len(set(ids)) or not all(isinstance(x,str) and x for x in ids):raise ValueError('CATALOGUE_DUPLICATE_IDS')
    if set(keys(families)) != set(MODEL_BEDS_MM):raise ValueError('UNSUPPORTED_FAMILY')
    for product in products:
        limits=product.get('bounds_mm')
        if not isinstance(limits,list) or len(limits)!=3 or any(type(v) not in (float,int) or v<=0 or not math.isfinite(v) for v in limits):raise ValueError('INVALID_PART_BOUNDS')
        parts=product.get('parts'); steps=product.get('steps')
        if not isinstance(parts,list) or not 1<=len(parts)<=32 or not isinstance(steps,list) or not 1<=len(steps)<=40:raise ValueError('PART_STEP_BUDGET')
        ids=[p['id'] for p in parts]
        if len(ids)!=len(set(ids)):raise ValueError('PART_IDS_DUPLICATED')
        for part in parts:
            if not _bounds(part,limits):raise ValueError('INVALID_PART_GEOMETRY')
            if part['printer_family'] not in keys(families):raise ValueError('UNSUPPORTED_PART_PROCESS')
            if part['origin'] not in ('digital','external','hybrid'):raise ValueError('UNDECLARED_SOURCE_KIND')
            if part['origin']=='external' and part['status']!='SOURCE_REQUIRED':raise ValueError('EXTERNAL_PART_FALSE_QUALIFICATION')
        seen=set()
        for step in steps:
            if not isinstance(step,list) or len(step)!=4 or not all(isinstance(x,str) or x is None for x in step):raise ValueError('MALFORMED_STEP')
            key,title,family,target=step
            if key in seen or family not in keys(families) or (target is not None and target not in ids):raise ValueError('UNKNOWN_STEP_TARGET')
            seen.add(key)
    children={product['id']:[p['parent'] for p in product['parts'] if p['parent'] is not None] for product in products}
    for product_id,parents in children.items():
        if any(parent not in keys(products) or parent==product_id for parent in parents):raise ValueError('UNRESOLVED_OR_SELF_PRODUCT_REFERENCE')
    def walk(node,chain):
        if node in chain:raise ValueError('PRODUCT_REFERENCE_CYCLE')
        for other in children[node]:walk(other,chain|{node})
    for product_id in children:walk(product_id,set())


def compile_scene(catalogue: dict, product_id: str, family_id: str, environment_id: str, scale: float=1.0, stage: int=0, *, printer_scale:float=1.0) -> dict:
    try:
        validate_catalogue(catalogue)
    except (TypeError,ValueError,KeyError):
        return _hold('CATALOGUE_INVALID')
    if type(scale) not in (int,float) or not math.isfinite(scale) or not 0.2<=scale<=5.0:return _hold('SCALE_UNSUPPORTED')
    if type(printer_scale) not in (int,float) or not math.isfinite(printer_scale) or not 0.5<=printer_scale<=4.0:return _hold('PRINTER_SCALE_UNSUPPORTED')
    if type(stage) is not int or stage<0:return _hold('STAGE_INVALID')
    find=lambda seq,key:next((x for x in seq if x['id']==key),None)
    product=find(catalogue['products'],product_id)
    family=find(catalogue['printer_families'],family_id)
    env=find(catalogue['environments'],environment_id)
    if any(x is None for x in (product,family,env)):return _hold('UNKNOWN_PRODUCT_PRINTER_OR_ENVIRONMENT')
    if stage>=len(product['steps']):return _hold('STAGE_OUT_OF_BOUNDS')
    bed=[round(x*printer_scale,6) for x in MODEL_BEDS_MM[family_id]]
    model_size=[round(x*scale,6) for x in product['bounds_mm']]
    fits=all(x<=b for x,b in zip(model_size,bed))
    steps=[]
    for i,(code,title,tool,target) in enumerate(product['steps']):
        part=find(product['parts'],target) if target else None
        steps.append({'stage_index':i,'code':code,'label':title,'tool_family':tool,
                      'target_part':target,'origin':part['origin'] if part else None,
                      'readiness': 'UNQUALIFIED_CONCEPT_ONLY',
                      'active':i==stage, 'completed_in_emulation':i<=stage,
                      'real_operation_executed':False,
                      'source_or_lot_receipt':None})
    visible={v['target_part'] for v in steps[:stage+1] if v['target_part'] is not None}
    shapes=[{'id':p['id'],'title':p['title'],'x_mm':list(p['xyz']),
             'size_mm':list(p['size']),'position_scaled_mm':[round(x*scale,6) for x in p['xyz']],
             'size_scaled_mm':[round(x*scale,6) for x in p['size']],
             'colour':p['colour'],'origin':p['origin'],'status':p['status'],
             'printer_family':p['printer_family'],'visible':p['id'] in visible,
             'origin_asset_authenticated':False,'material_qualified':False}
            for p in product['parts']]
    scene={'schema':SCHEMA,'state':'EMULATED_DESIGN_ONLY',
           'catalogue_sha256':canonical_digest(catalogue),'selection':{'product_id':product_id,'printer_family_id':family_id,
          'environment_id':environment_id,'scale':scale,'stage':stage,'printer_scale':printer_scale},
          'source_geometry':'ILLUSTRATIVE_BLOCKS_NOT_SOURCE_CAD',
          'material_library':'SOURCE_CLASS_POINTERS_NOT_OBSERVED_LOTS',
          'machine':{'family_ref':family['ref'],'family_title':family['title'],'tool':family['tool'],
                     'synthetic_bed_mm':list(bed),'printer_geometry_scale_illustrative':printer_scale,
                     'user_scaled_product_bounds_mm':model_size,
                     'illustrative_bed_fit':fits,'machine_dimensions_real':None,
                     'machine_kinematics_verified':False,'physical_motion_generated':False},
          'environment':{'profile':env['id'],'state':env['status'],
                         'assumed_pressure_pa':env['ambient_pressure_pa_assumed'],
                         'assumed_gravity_m_s2':env['gravity_m_s2_assumed'],
                         'actual_process_condition':None,'emc_or_low_g_qualified':False},
          'products':[p['id'] for p in catalogue['products']],
          'selected_product':{'id':product['id'],'title':product['title'],'key':product['key'],'assembly_model':'NOT_FUNCTIONALLY_VERIFIED',
                              'parent_subsystem_refs':sorted({p['parent'] for p in product['parts'] if p['parent'] is not None}),
                              'parts':shapes},
          'sequence':steps,'release_gates':list(catalogue['release_gates']),
          'hold_codes':['SOURCE_CAD_UNVERIFIED','REAL_TOOLING_AND_MATERIAL_LOTS_UNBOUND',
                        'PHYSICAL_PROCESS_NOT_VALIDATED','ASSEMBLY_FUNCTION_NOT_WITNESSED',
                        'ENVIRONMENT_UNQUALIFIED','C0_AND_PARENT_DBR_RELEASE_PENDING'] + ([] if fits else ['SYNTHETIC_BED_FIT_NOT_MET']),
          'physical_machine_authorised':False,'real_electrical_function_verified':False,
          'native_dbr_written':False,'commercial_release_authorised':False,'printed_functionality_verified':False}
    scene['scene_sha256']=canonical_digest(scene)
    return scene


def reverse_scene(scene: dict, catalogue:dict) -> dict:
    if not isinstance(scene,dict) or not isinstance(scene.get('selection'),dict):return {'state':'HOLD','reason':'SCENE_MISSING','physical_machine_authorised':False}
    choice=scene['selection']
    rebuilt=compile_scene(catalogue,choice.get('product_id'),choice.get('printer_family_id'),
                          choice.get('environment_id'),choice.get('scale'),choice.get('stage'),
                          printer_scale=choice.get('printer_scale'))
    return {'state':'PASS_DIGITAL_ONLY' if rebuilt==scene and rebuilt.get('state')=='EMULATED_DESIGN_ONLY' else 'HOLD',
            'scene_sha256_recomputed':rebuilt.get('scene_sha256'),
            'verified_source_authenticity':False,'physical_machine_authorised':False}


def sweep_scenarios(catalogue:dict, scales=(0.5,1.0,2.0,4.0), printer_scales=(0.5,1.0,2.0)) -> dict:
    validate_catalogue(catalogue)
    if (type(scales) not in (tuple,list) or not scales or len(scales)>6 or any(type(v) not in (int,float) or not math.isfinite(v) or v<0.2 or v>5 for v in scales)):raise ValueError('UNBOUNDED_SWEEP_SCALES')
    if (type(printer_scales) not in (tuple,list) or not printer_scales or len(printer_scales)>4
        or any(type(v) not in (int,float) or not math.isfinite(v) or v<0.5 or v>4 for v in printer_scales)):
        raise ValueError('UNBOUNDED_PRINTER_SCALES')
    cases=[]
    for product,family,environment,scale,printer_scale in itertools.product(catalogue['products'],catalogue['printer_families'],catalogue['environments'],scales,printer_scales):
        if len(cases)>=MAX_SCENARIOS:raise ValueError('SWEEP_LIMIT')
        item=compile_scene(catalogue,product['id'],family['id'],environment['id'],scale,0,printer_scale=printer_scale)
        assert item['state']=='EMULATED_DESIGN_ONLY'
        cases.append({'product_id':product['id'],'family_id':family['id'],'environment_id':environment['id'],
                      'scale':scale,'printer_scale':printer_scale,'illustrative_bed_fit':item['machine']['illustrative_bed_fit'],
                      'release_authorised':False,'scene_sha256':item['scene_sha256']})
    result={'schema':'CGX-PRINTSPACE-VIRTUAL-FACTORY-SWEEP/0.1','state':'SYNTHETIC_SCENARIO_SWEEP_COMPLETE_UNQUALIFIED',
            'case_count':len(cases),'catalogue_sha256':canonical_digest(catalogue),'cases':cases,
            'illustrative_fits':sum(x['illustrative_bed_fit'] for x in cases),
            'real_machine_and_environment_verified':False,'physical_machine_authorised':False}
    result['result_sha256']=canonical_digest(result)
    return result