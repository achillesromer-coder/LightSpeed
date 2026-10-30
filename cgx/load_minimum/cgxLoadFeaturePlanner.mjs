/** CGX LOAD + CCC invocation planning, pure and authority-free. No transport, tokens, disk, or execution. */
export const CONTRACT = 'CGX-UNISPACE-FILESPACE-FEATURE-PLAN/0.1';
export const ACTIONS = Object.freeze({
  'alexandria.open': 'read',
  'alexandria.resolve': 'review',
  'alexandria.sources': 'read',
  'load.attach': 'wizard',
  'load.hydrate': 'review',
  'ccc.discover': 'review',
  'ccc.install': 'wizard',
  'load.switch_view': 'review',
  'load.match_novel': 'review',
  'load.tune_context': 'review',
});
export const MENUS = Object.freeze({
  filespace: ['alexandria.open','alexandria.resolve','load.attach','load.hydrate','ccc.discover','ccc.install','load.switch_view','load.match_novel','load.tune_context'],
  object: ['alexandria.resolve','alexandria.sources','ccc.discover','load.switch_view','load.match_novel','load.tune_context'],
  file: ['alexandria.resolve','alexandria.sources','load.match_novel'],
});
const BAD = /[\u0000-\u001f]/;
const UNSAFE = /(?:^|[\\/])\.\.(?:[\\/]|$)/;
const safeText = (s) => typeof s === 'string' && s.trim().length > 0 && s.length <= 512 && !BAD.test(s) && !UNSAFE.test(s);
const isObj = (x) => !!x && typeof x === 'object' && !Array.isArray(x);
const allow = (x) => x === true;
// Source-review scope check: a menu declaration is not native Object_ID authority.
const childSpaces=Object.freeze({eco:'Eco.cgx',romer:'Romer.cgx',emassc:'EMASSC.cgx',ls:'LS.cgx'});
const reservedSpaces=Object.freeze(Object.fromEntries(Object.entries(childSpaces).map(([domain,space])=>[space,domain])));
const unambiguous=s=>safeText(s)&&s===s.normalize('NFC')&&!/[\p{Default_Ignorable_Code_Point}\p{Cc}]/u.test(s);
const childMatches=(domain,space)=>!Object.hasOwn(childSpaces,domain)||childSpaces[domain]===space;
const reservedMatches=(domain,space)=>!Object.hasOwn(reservedSpaces,space)||reservedSpaces[space]===domain;

/** Return only menu identifiers; host UI controls labels / icons and attaches callbacks separately. */
export function menuForTarget(kind, { readable = false } = {}) {
  if (!Object.hasOwn(MENUS, kind) || !readable) return [];
  return [...MENUS[kind]];
}

/**
 * A native host MUST verify target id and incoming lease against current authority.
 * This planner cannot grant permissions or assume a downloaded carrier has been admitted.
 */
export function planFeature(request) {
  if (!isObj(request)) return { state: 'DENIED', reason: 'INVALID_REQUEST' };
  const { action, target, capabilityId, mode = 'TRACK', hydration = 'minimal', sourceByteCount = 0 } = request;
  if (!Object.hasOwn(ACTIONS, action)) return { state: 'DENIED', reason: 'UNKNOWN_ACTION' };
  if (!isObj(target) || !Object.hasOwn(MENUS, target.kind) || !safeText(target.fileSpace) || !safeText(target.owner)) {
    return { state: 'DENIED', reason: 'INVALID_TARGET' };
  }
  if (!MENUS[target.kind].includes(action)) return { state: 'DENIED', reason: 'ACTION_NOT_APPLICABLE' };
  if (target.objectId != null && !safeText(target.objectId)) return {state:'DENIED',reason:'INVALID_OBJECT_ID'};
  if (!unambiguous(target.fileSpace)||!unambiguous(target.owner)||
      (target.domain != null&&!unambiguous(target.domain))||
      (target.objectId != null&&!unambiguous(target.objectId))||
      (capabilityId != null&&!unambiguous(capabilityId)))
    return {state:'DENIED',reason:'AMBIGUOUS_IDENTITY_OR_SCOPE'};
  if (target.parentFileSpace != null && target.parentFileSpace !== 'Cognigrex.cgx')
    return {state:'DENIED',reason:'COMPETING_PARENT_ROOT'};
  if (target.domain != null && (!childMatches(target.domain,target.fileSpace)||
      !reservedMatches(target.domain,target.fileSpace)))
    return {state:'DENIED',reason:'CHILD_FILESPACE_SCOPE_CONFLICT'};
  if (!['TRACK','REFERENCE','PIN','EMBED'].includes(mode)) return { state:'DENIED', reason:'UNKNOWN_COMPOSITION_MODE' };
  if (!['minimal','offline','on-demand','full-approved'].includes(hydration)) return { state:'DENIED', reason:'UNKNOWN_HYDRATION' };
  if (!Number.isSafeInteger(sourceByteCount) || sourceByteCount < 0 || sourceByteCount > 60*1024*1024) return { state:'DENIED', reason:'BOUNDED_SOURCE_EXCEEDED' };
  const mutating = action === 'load.attach' || action === 'ccc.install';
  if (mutating && target.kind !== 'filespace') return { state:'DENIED', reason:'TARGET_NOT_A_FILESPACE' };
  if (action === 'ccc.install' && !safeText(capabilityId)) return {state:'DENIED',reason:'CAPABILITY_ID_REQUIRED'};
  const id = target.objectId;
  // Do not guess object identity from file names, paths, labels, or domain IDs.
  if (id != null && !safeText(id)) return { state:'DENIED',reason:'INVALID_OBJECT_ID' };
  const parent = target.parentFileSpace || 'Cognigrex.cgx';
  if (!safeText(parent)) return { state:'DENIED',reason:'INVALID_PARENT' };
  const intent = {
    schema: CONTRACT, action, target: { kind:target.kind, fileSpace:target.fileSpace, domain:target.domain??null, owner:target.owner, objectId:id??null, parentFileSpace:parent },
    requestedMode:mode, requestedHydration:hydration,
    sourceByteCount, sourceCopied:false,
    requestedCapability: action === 'ccc.install' ? capabilityId : action === 'ccc.discover' ? 'CCC_DISCOVERY_ONLY' : 'ALEXANDRIA_LOAD',
    canonicalMutation:false, networkFetch:false, install:false, execute:false, publish:false,
    status: 'REVIEW_ONLY', blockers:[],
  };
  if (allow(request.offline)) intent.offlineMode = 'MINIMAL_LOCAL_REFERENCE';
  if (!allow(request.readable)) intent.blockers.push('SCOPE_READ_UNVERIFIED');
  if (!safeText(id)) intent.blockers.push('EXACT_OBJECT_ID_UNRESOLVED');
  if (target.domain == null) intent.blockers.push('CHILD_DOMAIN_UNVERIFIED');
  if (mutating) {
    intent.wizard = ['scope-target-and-current-accepted-parent','resolve-existing-LOAD-and-Alexandria-aliases',
      'choose-TRACK-REFERENCE-PIN-EMBED','verify-source-rights-and-hydration-policy',
      'show-delta-and-negative-preflight','host-permitted-apply-with-DBR-readback'];
    if (!allow(request.acceptedParent)) intent.blockers.push('PARENT_AUTHORITY_UNVERIFIED');
    if (!allow(request.existingAliasChecked)) intent.blockers.push('LOAD_ALIAS_COLLISION_CHECK_REQUIRED');
    if (!allow(request.ownerApproved)) intent.blockers.push('OWNER_CONSENT_REQUIRED');
    if (!allow(request.rightsVerified)) intent.blockers.push('SOURCE_RIGHTS_UNVERIFIED');
    if (!allow(request.signedLeaseVerified)) intent.blockers.push('LEASE_UNVERIFIED');
    if (!allow(request.providerReadbackReady)) intent.blockers.push('DBR_READBACK_UNVERIFIED');
  }
  if (action === 'load.hydrate' && hydration !== 'minimal' && !allow(request.networkPermission)) {
    intent.blockers.push('NETWORK_HYDRATION_NOT_AUTHORIZED');
  }
  if (action.startsWith('ccc.') && !allow(request.registeredCapabilityVerified)) {
    intent.blockers.push('CCC_CAPABILITY_REGISTRATION_UNVERIFIED');
  }
  if (!intent.blockers.length && mutating) intent.status='READY_FOR_AUTHENTICATED_HOST_PREFLIGHT';
  // Explicitly still a plan. Host makes the authoritative acceptance decision and records separate signed DBR.
  return intent;
}


/**
 * Private UniSpace browser drag/drop metadata preflight. A File's name, type,
 * size and optional digest are caller claims, never provider evidence. This
 * does not read File bytes, assign Object_ID, call a native intake adapter,
 * publish an asset, or grant host rights. Actual R0 byte ingestion requires
 * an independently authorised provider transaction and readback.
 */
export const DROP_PREFLIGHT_SCHEMA='CGX-UNISPACE-DROP-PREFLIGHT/0.1';
const dropName=s=>unambiguous(s)&&s.length<=255&&s.trim()===s&&
 !s.startsWith('.')&&!/[\\/:*?"<>|&]/.test(s)&&
 !/^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(s);
const dropMime=s=>s===''||(typeof s==='string'&&s.length<=127&&
 /^[a-z0-9.+-]+\/[a-z0-9.+-]+$/i.test(s));
const dropRights=new Set(['PUBLIC_SAFE','OWNER_PRIVATE','LICENSE_RESTRICTED','UNKNOWN']);
const dropProof=new Set(['creative','scientific','engineering','historical','operational','unknown']);

export function planSourceDropPreflight({target,file,readable=false,offline=false}={}){
 const deny=reason=>({schema:DROP_PREFLIGHT_SCHEMA,state:'DENIED',reason,
  canonicalMutation:false,sourceBytesRead:false,hashVerified:false,publicRelease:false});
 if(!isObj(target)||target.kind!=='filespace')return deny('DROP_REQUIRES_CHILD_FILESPACE');
 if(typeof offline!=='boolean'||typeof readable!=='boolean')return deny('INVALID_PREFLIGHT_MODE');
 if(!isObj(file)||!dropName(file.name)||!dropMime(file.type??''))
  return deny('INVALID_SOURCE_METADATA');
 if(!Number.isSafeInteger(file.size)||file.size<0||file.size>60*1024*1024)
  return deny('BOUNDED_SOURCE_EXCEEDED');
 for(const key of ['sourceId','revision','owner','licenseId']){
  if(file[key]!=null&&!unambiguous(file[key]))return deny('AMBIGUOUS_SOURCE_METADATA');
 }
 if(file.sha256!=null&&!(typeof file.sha256==='string'&&/^[0-9a-f]{64}$/i.test(file.sha256)))
  return deny('INVALID_UNVERIFIED_DIGEST_CLAIM');
 if(file.rights!=null&&!dropRights.has(file.rights))return deny('UNKNOWN_RIGHTS_DECLARATION');
 if(file.proofClass!=null&&!dropProof.has(file.proofClass))return deny('UNKNOWN_PROOF_CLASS');
 const scope=planFeature({action:'alexandria.resolve',target,readable,
  offline,hydration:'minimal',sourceByteCount:file.size});
 if(scope.state==='DENIED')return deny(scope.reason);
 const blockers=[...scope.blockers,'SOURCE_BYTES_NOT_READ','SOURCE_HASH_NOT_PROVIDER_VERIFIED',
  'CURRENT_HOST_ACL_UNVERIFIED','SOURCE_RIGHTS_NOT_PROVIDER_VERIFIED',
  'NATIVE_OBJECT_ID_AND_DBR_UNVERIFIED','PUBLIC_STATIC_ASSET_ROUTE_FORBIDDEN'];
 if(!file.sha256)blockers.push('SOURCE_DIGEST_NOT_SUPPLIED');
 if(!file.sourceId||!file.revision)blockers.push('SOURCE_ID_OR_REVISION_UNRESOLVED');
 if(!file.owner)blockers.push('SOURCE_OWNER_UNRESOLVED');
 if(!file.rights||file.rights==='UNKNOWN')blockers.push('SOURCE_RIGHTS_UNKNOWN');
 if(file.rights==='LICENSE_RESTRICTED'&&!file.licenseId)
  blockers.push('LICENSE_TERMS_UNRESOLVED');
 if(!file.proofClass||file.proofClass==='unknown')blockers.push('PROOF_CLASS_UNRESOLVED');
 if(!file.type)blockers.push('MIME_UNVERIFIED');
 if(file.size===0)blockers.push('EMPTY_SOURCE_REVIEW_REQUIRED');
 if(offline)blockers.push('OFFLINE_AUTHORITY_AND_REVOCATION_UNVERIFIED');
 return {
  schema:DROP_PREFLIGHT_SCHEMA,state:'REVIEW_ONLY',admissionStage:'R0_METADATA_PREFLIGHT',
  target:scope.target,source:{
   name:file.name,byteCount:file.size,mimeType:file.type||null,
   proofClass:file.proofClass??'unknown',rightsClaim:file.rights??'UNKNOWN',
   digestClaimPresent:!!file.sha256,providerReferenceClaimPresent:!!file.sourceId,
   revisionClaimPresent:!!file.revision
  },
  blockers:[...new Set(blockers)],
  transferBudgetBytes:0,sourceBytesRead:false,hashVerified:false,
  hostAuthenticated:false,providerReadback:false,nativeAdmitted:false,
  canonicalMutation:false,networkFetch:false,install:false,execute:false,
  publicRelease:false,rendered:false
 };
}
