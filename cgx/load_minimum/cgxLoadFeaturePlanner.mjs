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
    schema: CONTRACT, action, target: { kind:target.kind, fileSpace:target.fileSpace, owner:target.owner, objectId:id??null, parentFileSpace:parent },
    requestedMode:mode, requestedHydration:hydration,
    sourceByteCount, sourceCopied:false,
    requestedCapability: action === 'ccc.install' ? capabilityId : action === 'ccc.discover' ? 'CCC_DISCOVERY_ONLY' : 'ALEXANDRIA_LOAD',
    canonicalMutation:false, networkFetch:false, install:false, execute:false, publish:false,
    status: 'REVIEW_ONLY', blockers:[],
  };
  if (allow(request.offline)) intent.offlineMode = 'MINIMAL_LOCAL_REFERENCE';
  if (!allow(request.readable)) intent.blockers.push('SCOPE_READ_UNVERIFIED');
  if (!safeText(id)) intent.blockers.push('EXACT_OBJECT_ID_UNRESOLVED');
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
