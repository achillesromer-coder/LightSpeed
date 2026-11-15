/**
 * CGX / UniSpace facet projection, SOURCE-REVIEW ONLY.
 * Reuses the existing CGX object gate, LOAD library lens, and view-selection policy.
 * A CGX shorthand descriptor is not executable authority, a native mint, or an authenticated session.
 * No network, file IO, provider resolution, OS actions, or Smith/LS GO dispatch.
 */
const SCHEMA = 'UNISPACE-CGX-FACET-PROJECTION/0.1';
const OBJECT_SCHEMA = 'UNISPACE-CGX-ONE-OBJECT-VIEW-PLAN/0.1';
const LOAD_SCHEMA = 'UNISPACE-CGX-LOAD-LENS-PLAN/0.1';
const FAMILY = /^[A-Za-z][A-Za-z0-9_.-]*\.cgx$/;
const INTENTS = Object.freeze({
  browse: ['filespace-tree', 'topology-graph'],
  operate: ['hybrid-canonical-cells', 'active-object-inspector'],
  engineer: ['active-object-inspector', 'twin-3d', 'matrix', 'topology-graph'],
  ecology: ['map-spatial', 'active-object-inspector', 'timeline-dbr', 'topology-graph'],
  validate: ['evidence-claim', 'matrix', 'timeline-dbr', 'active-object-inspector'],
  runtime: ['network-runtime', 'active-object-inspector', 'timeline-dbr'],
  audit: ['evidence-claim', 'timeline-dbr', 'topology-graph', 'matrix'],
  mobile_quicklook: ['hybrid-canonical-cells', 'active-object-inspector']
});
const PALETTES = Object.freeze({
  'Cognigrex.cgx': 'neutral',
  'Romer.cgx': 'engineering',
  'Eco.cgx': 'ecological',
  'EMASSC.cgx': 'scientific',
  'LS.cgx': 'operational'
});
const FOCUS_KEYS = Object.freeze({
  '1': 'focus',
  '2': 'relationships',
  '3': 'spatial-preview'
});
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const record=o=>o!==null&&typeof o==='object'&&!Array.isArray(o);
const secretKeys=['token','api_key','authorization','cookie','source_bytes','private_path','source_locator','view_url','lease','dbr_root'];
const clean=o=>!record(o)||!secretKeys.some(k=>own(o,k));
const hold=(code)=>Object.freeze({
  schema:SCHEMA, state:'HOLD', hold_code:code,
  hydrated:false, dispatched:false, native_admitted:false,
  execution_performed:false, canonical_mutation:false,
  public_publish_authorized:false
});

/** Deterministic *schematic* triangle plus radiative vertex circles.
 * Returns numeric geometry for a client renderer, never provenance-bearing CAD. */
export function radialTrianglePreview(edgeLength, cx=0, cy=0) {
  if (![edgeLength,cx,cy].every(Number.isFinite)||edgeLength<=0||edgeLength>100000||
      Math.abs(cx)>1e7||Math.abs(cy)>1e7) return null;
  const h=Math.sqrt(3)*edgeLength/2;
  const vertices=[
    [cx,cy-2*h/3],
    [cx-edgeLength/2,cy+h/3],
    [cx+edgeLength/2,cy+h/3]
  ];
  return Object.freeze({
    schema:'CGX-TRIANGLE-VERTEX-RADIAL-PREVIEW/0.1',
    source_pattern:'LightSpeed triangle_renderer.py; r = L/2',
    coordinate_space:'schematic_2d_not_georeferenced',
    vertices, vertex_circle_radius:edgeLength/2,
    draw_primitives:['triangle','vertex-circle','vertex-circle','vertex-circle'],
    canonical_geometry:false, physical_simulation:false
  });
}

/** Input is the output of existing source-review planners, not a host-authenticated security grant. */
export function projectUniSpaceFacet(input) {
  if(!record(input)||!clean(input)||!clean(input.object_view)||!clean(input.load_lens))
    return hold('INVALID_OR_INLINE_PRIVATE_REQUEST');
  const o=input.object_view;
  if(!record(o)||o.schema!==OBJECT_SCHEMA||o.state!=='PLAN_ONLY_NOT_HYDRATED'||
      o.native_admitted!==false||o.canonical_mutation!==false||
      o.execution_performed!==false||o.public_publish_authorized!==false||
      o.source_bytes_included!==false||typeof o.object_id!=='string'||
      o.object_id.length<1||o.object_id.length>255||
      typeof o.filespace!=='string'||!FAMILY.test(o.filespace))
    return hold('OBJECT_VIEW_GATE_NOT_SATISFIED');
  if(input.load_lens!==undefined) {
    const l=input.load_lens;
    if(!record(l)||l.schema!==LOAD_SCHEMA||l.state!=='PLAN_ONLY_NOT_HYDRATED'||
       l.alias!=='LOAD.cgx'||l.object_id!==o.object_id||l.filespace!==o.filespace||
       l.native_admitted!==false||l.hydrated!==false||l.execution_performed!==false||
       l.public_publish_authorized!==false||l.canonical_mutation!==false)
      return hold('LOAD_ALIAS_OR_OBJECT_SCOPE_MISMATCH');
  }
  const intent=input.task_intent;
  if(intent==='publish')return hold('PUBLICATION_REQUIRES_SEPARATE_ACCEPTANCE');
  if(!own(INTENTS,intent))return hold('UNKNOWN_TASK_INTENT');
  const device=input.device_profile??'desktop';
  if(!['desktop','browser','mobile'].includes(device))
    return hold('UNSUPPORTED_DEVICE');
  const options=INTENTS[intent];
  // This review planner has no trusted host receipt verifier. Both remain
  // excluded regardless of caller-supplied 'verified' flags.
  const safe=options.filter(v=>v!=='map-spatial'&&v!=='twin-3d');
  const catalog=Array.isArray(input.declared_renderer_ids)
    ?input.declared_renderer_ids.filter(v=>typeof v==='string'):[];
  const matching=safe.filter(v=>catalog.includes(v));
  const primary=matching[0]??safe[0]??'active-object-inspector';
  const secondary=safe.filter(v=>v!==primary);
  const preview=input.preview_edge_length===undefined?null:radialTrianglePreview(input.preview_edge_length);
  return Object.freeze({
    schema:SCHEMA, state:'REVIEW_FACET_PLAN_ONLY', product:'UniSpace.cgx',
    canonical_parent:'Cognigrex.cgx',
    object_id:o.object_id, filespace:o.filespace, task_intent:intent,
    palette:PALETTES[o.filespace]??'family-derived',
    device_profile:device,
    view:{
      primary, secondary_on_demand:secondary,
      one_primary:true, selected_subgraph:[o.object_id],
      available_renderer_independently_verified:false,
      keyboard_presets:FOCUS_KEYS,
      geo_mapping_admitted:false, immersive_controls_enabled:false
    },
    geometric_preview:preview,
    shorthand:{
      kind:'cgx:facet:projection',
      ref:o.object_id,
      file:o.filespace,
      lens:primary,
      hydrate:'H0',
      runtime:'existing-LightSpeed',
      library_alias:'LOAD.cgx',
      capability_catalog:'CCC',
      execute_via:'Smith/LightSpeed-GO-after-lease'
    },
    dispatch:{state:'NOT_QUEUED', required_gate:'SIGNED_SMITH_SINGLETON_LEASE_AND_AUTHENTICATED_LSGO_RECEIPT'},
    authority:{
      object_gate:'CALLER_SUPPLIED_REVIEW_PLAN_NOT_INDEPENDENT_AUTH',
      load_gate:input.load_lens===undefined?'NOT_BOUND':'CALLER_SUPPLIED_REVIEW_PLAN_NOT_INDEPENDENT_AUTH'
    },
    hydrated:false, dispatched:false, native_admitted:false,
    execution_performed:false, canonical_mutation:false,
    public_publish_authorized:false
  });
}
