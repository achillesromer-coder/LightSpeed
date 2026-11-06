/**
 * UniSpace private-asset negative-probe review contract.
 * Source-only, one candidate Object_ID / one child FileSpace.
 * Never performs HTTP, reads a dist tree, grants authority or publishes assets.
 * Any observations are untrusted until an independent host/browser readback.
 */
export function planUniSpacePrivateRouteProbeReview(input) {
  const schema='UNISPACE-PRIVATE-ROUTE-PROBE-REVIEW/0.1';
  const hold=code=>Object.freeze({schema,state:'HOLD',hold_code:code,independent_http_verified:false,host_authenticated:false,release_accepted:false,canonical_mutation:false,network_fetch:false});
  const rec=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
  const banned=new Set(['token','cookie','password','secret','authorization','access_key','source_url','source_locator','source_bytes','private_path','public_path','asset_path','asset_url','endpoint','host_url','url','uri','carrier_path','dbr_root','state_root','response_body','payload','headers','session','credential']);
  function forbidden(x,depth=0,seen=new Set()){
    if(!x||typeof x!=='object')return false;
    if(depth>9||seen.has(x))return true;
    seen.add(x);
    for(const [key,val] of Object.entries(x)){
      if(banned.has(key.toLowerCase())||forbidden(val,depth+1,seen))return true;
    }
    seen.delete(x);return false;
  }
  if(!rec(input)||forbidden(input)||Object.keys(input).some(k=>!['command_plan','client_permissions','observations'].includes(k)))return hold('INVALID_OR_PRIVATE_INPUT');
  const {command_plan:c,client_permissions:p,observations=[]}=input;
  const id=/^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
  const children=new Set(['Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']);
  if(!rec(c)||c.schema!=='UNISPACE-LOAD-COMMAND-SURFACE/0.1'||c.state!=='SOURCE_REVIEW_ONLY'||c.parent_filespace!=='Cognigrex.cgx'||c.alias!=='LOAD.cgx'||!id.test(c.candidate_object_id||'')||c.candidate_object_id.startsWith('cgx:domain:')||c.candidate_object_id==='cgx:root:cognigrex'||!children.has(c.filespace)||c.identity_status!=='NOT_NATIVE_ACCEPTED'||c.native_admitted!==false||c.host_authenticated!==false||c.public_release!==false||c.canonical_mutation!==false||c.execution_performed!==false||c.network_fetch!==false||c.handlers_bound!==false||c.asset_urls_returned!==false||!Array.isArray(c.actions)||c.actions.some(a=>!rec(a)||a.enabled!==false||a.callback_bound!==false))return hold('EXACT_REVIEW_COMMAND_BINDING_REQUIRED');
  if(!rec(p)||p.mode!=='review_only'||p.revoked!==false||!Array.isArray(p.allowed_object_ids)||p.allowed_object_ids.length!==1||p.allowed_object_ids[0]!==c.candidate_object_id||!Array.isArray(p.allowed_filespaces)||p.allowed_filespaces.length!==1||p.allowed_filespaces[0]!==c.filespace)return hold('CLIENT_SCOPE_MISMATCH');
  const probes=[
    ['anonymous_catalogue','anonymous','private_catalogue','deny'],
    ['revoked_catalogue','revoked','private_catalogue','deny'],
    ['anonymous_preview','anonymous','private_preview','deny'],
    ['anonymous_binary','anonymous','private_binary','deny'],
    ['anonymous_metadata','anonymous','private_metadata','deny'],
    ['traversal_attempt','anonymous','traversal_private','deny'],
    ['owner_catalogue','owner','private_catalogue','owner_read'],
    ['dist_residual','build_scan','private_static_residual','absent']
  ];
  if(!Array.isArray(observations)||observations.length>probes.length)return hold('INVALID_OBSERVATIONS');
  const known=new Set(probes.map(x=>x[0])),seen=new Set(),observed=new Map();
  for(const o of observations){
    if(!rec(o)||!known.has(o.probe_id)||seen.has(o.probe_id))return hold('DUPLICATE_OR_UNKNOWN_PROBE');
    const isDist=o.probe_id==='dist_residual';
    const keys=Object.keys(o).sort().join(',');
    if(isDist?(keys!=='probe_id,residual_present'||typeof o.residual_present!=='boolean'):(keys!=='http_status,probe_id'||!Number.isSafeInteger(o.http_status)||o.http_status<100||o.http_status>599))return hold('MALFORMED_PROBE_OBSERVATION');
    seen.add(o.probe_id);observed.set(o.probe_id,o);
  }
  let risk=false;
  const cases=probes.map(([probe_id,actor,asset_class,expectation])=>{
    const o=observed.get(probe_id);
    let result='NOT_OBSERVED';
    if(o){
      if(expectation==='absent')result=o.residual_present?'POTENTIAL_PRIVATE_STATIC_RESIDUAL':'ABSENCE_CLAIM_UNATTESTED';
      else if(expectation==='owner_read')result=o.http_status===200?'OWNER_READ_CLAIM_UNATTESTED':'OWNER_READ_NOT_PROVEN';
      else if([401,403].includes(o.http_status))result='DENIAL_CLAIM_UNATTESTED';
      else if(o.http_status===404)result='NOT_FOUND_CLAIM_UNATTESTED';
      else if(o.http_status>=200&&o.http_status<400)result='POTENTIAL_PRIVATE_DISCLOSURE';
      else result='INCONCLUSIVE_UNATTESTED';
      if(result.startsWith('POTENTIAL_'))risk=true;
    }
    return Object.freeze({probe_id,actor,asset_class,expectation,observation_state:result,independently_verified:false});
  });
  return Object.freeze({
    schema,state:'SOURCE_REVIEW_ONLY',parent_filespace:'Cognigrex.cgx',
    filespace:c.filespace,candidate_object_id:c.candidate_object_id,
    evidence_class:c.evidence_class,alias:'LOAD.cgx',
    probes:Object.freeze(cases),observed_count:observed.size,required_count:probes.length,
    risk_signal:risk?'POTENTIAL_DISCLOSURE_REQUIRES_OWNER_INVESTIGATION':'NO_INDEPENDENT_SECURITY_CONCLUSION',
    gate:'HOLD_ISSUE_158_AND_161',next_gate:'REAL_HOST_AUTHENTICATED_AND_ANONYMOUS_HTTP_PLUS_DIST_READBACK',
    independent_http_verified:false,host_authenticated:false,release_accepted:false,
    canonical_mutation:false,network_fetch:false,source_bytes_transferred:0,
    claim_boundary:'Client-supplied status observations are untrusted. This planner performs no HTTP, build scan, authentication, DBR readback or deployment.'
  });
}
