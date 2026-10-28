/**
 * Bounded, metadata-only CGX CCC capability preflight for the LS GO mobile surface.
 * Source-review helper, NOT a native CCC resolver, owner session, install or executor.
 * The caller-supplied registries and source metadata are not independently trusted.
 * Parent topology: Cognigrex.cgx -> EMASSC.cgx -> LS.cgx; CCC lives at parent.
 */
export const MOBILE_CCC_SOURCE_GATE_SCHEMA = 'CGX-CCC-MOBILE-SOURCE-GATE/0.1';
const HEX40 = /^[0-9a-f]{40}$/i;
const HEX64 = /^[0-9a-f]{64}$/i;
const ID = /^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$/;
const VERSION = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;
const SECRET_KEY = /(?:^|[_-])(secret|token|password|credential|private[_-]?key|authorization|cookie|session)(?:$|[_-])/i;
const isRecord = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

const hold = (code) => Object.freeze({
  schema: MOBILE_CCC_SOURCE_GATE_SCHEMA, state: 'HOLD', hold_code: code,
  native_admitted: false, capability_installed: false, execution_performed: false,
  owner_authorized: false, provider_readback_authenticated: false,
  canonical_mutation: false, public_publish_authorized: false,
});

// Reject credential-bearing inputs, cycles and excessive nesting; never echo input.
const hasUnsafeShape = (value, depth = 0, seen = new Set()) => {
  if (depth > 5) return true;
  if (value === null || typeof value !== 'object') return false;
  if (seen.has(value)) return true;
  seen.add(value);
  const keys = Object.keys(value);
  if (keys.length > 64 || (Array.isArray(value) && value.length > 64)) return true;
  for (const key of keys) {
    if (SECRET_KEY.test(key) || hasUnsafeShape(value[key], depth + 1, seen)) return true;
  }
  seen.delete(value);
  return false;
};

export function planCgxMobileCccSourceCapability(input) {
  if (!isRecord(input) || !isRecord(input.toolkit_registry) ||
      !isRecord(input.parent_topology) || !isRecord(input.candidate) ||
      !isRecord(input.request)) return hold('INVALID_INPUT');
  const { toolkit_registry: registry, parent_topology: topology,
    candidate: c, request: r } = input;
  if (hasUnsafeShape(c) || hasUnsafeShape(r)) return hold('SENSITIVE_OR_UNBOUNDED_INPUT');
  if (registry.schema_version !== '0.1' ||
      registry.secrets_policy !== 'references-only-no-secret-bytes' ||
      !Array.isArray(registry.toolkits)) return hold('CCC_REGISTRY_SCHEMA_UNVERIFIED');
  const ccc = registry.toolkits.filter((v) => v?.id === 'ccc');
  if (ccc.length !== 1 || ccc[0].kind !== 'package-registry' ||
      ccc[0].binding !== 'cgx-native' || !Array.isArray(ccc[0].capabilities))
    return hold('CCC_PARENT_BINDING_UNVERIFIED');
  const emassc = topology.root?.children?.filter((v) => v?.id === 'emassc') || [];
  const ls = emassc[0]?.children?.filter((v) => v?.id === 'lightspeed') || [];
  const shared = topology.shared_root_services?.filter((v) => v?.id === 'ccc') || [];
  if (topology.schema !== 'CGX-COGNIGREX-PARENT-TOPOLOGY/0.2' ||
      topology.root?.file !== 'Cognigrex.cgx' || emassc.length !== 1 ||
      emassc[0].file !== 'EMASSC.cgx' || ls.length !== 1 ||
      ls[0].file !== 'LS.cgx' || shared.length !== 1 ||
      shared[0].location !== 'Cognigrex.cgx:/ccc')
    return hold('CHILD_OR_CCC_TOPOLOGY_UNVERIFIED');
  if (c.schema !== 'CGX-CCC-CAPABILITY-CANDIDATE/0.1' ||
      c.parent_filespace !== 'EMASSC.cgx' || c.filespace !== 'LS.cgx' ||
      c.ccc_location !== 'Cognigrex.cgx:/ccc')
    return hold('WRONG_CHILD_FILESPACE');
  if (typeof c.package_id !== 'string' || !ID.test(c.package_id) ||
      typeof c.capability_id !== 'string' || !ID.test(c.capability_id) ||
      typeof c.version !== 'string' || !VERSION.test(c.version) ||
      c.abi !== 'CGX-CCC-METADATA-PLAN/0.1')
    return hold('CANDIDATE_ID_VERSION_OR_ABI_INVALID');
  if (!isRecord(c.source) || c.source.provider !== 'github' ||
      typeof c.source.repository !== 'string' || !/^[\w.-]+\/[\w.-]+$/.test(c.source.repository) ||
      typeof c.source.path !== 'string' || !/^[\w./-]+$/.test(c.source.path) ||
      c.source.path.startsWith('/') || c.source.path.split('/').includes('..') ||
      !HEX40.test(c.source.revision || '') || !HEX40.test(c.source.blob_sha || '') ||
      !HEX64.test(c.source.content_sha256 || ''))
    return hold('SOURCE_IDENTITY_OR_HASH_INVALID');
  if (typeof c.licence_ref !== 'string' || !c.licence_ref.trim() ||
      c.licence_ref.length > 200 || c.rights_review_state !== 'unverified' ||
      !Array.isArray(c.permissions) || c.permissions.length !== 1 ||
      c.permissions[0] !== 'metadata:read')
    return hold('RIGHTS_OR_PERMISSIONS_UNVERIFIED');
  if (r.execution_requested !== false || r.requested_scope !== 'metadata_only' ||
      r.authority_transfer !== false || r.canonical_mutation !== false ||
      r.public_publish_authorized !== false) return hold('EXECUTION_OR_AUTHORITY_REQUESTED');
  if (!['discover', 'plan'].includes(r.operation) ||
      !ccc[0].capabilities.includes(r.operation)) return hold('OPERATION_NOT_MOBILE_SOURCE_SAFE');
  // No network calls, package install, file writes, mint, hydration or token handling.
  return Object.freeze({
    schema: MOBILE_CCC_SOURCE_GATE_SCHEMA,
    state: r.operation === 'discover' ? 'DISCOVERY_ONLY' : 'PLAN_ONLY',
    package_id: c.package_id, capability_id: c.capability_id,
    candidate_version: c.version, candidate_abi: c.abi,
    parent_filespace: 'EMASSC.cgx', filespace: 'LS.cgx',
    ccc_location: 'Cognigrex.cgx:/ccc',
    source_revision: c.source.revision.toLowerCase(),
    source_git_blob_sha: c.source.blob_sha.toLowerCase(),
    source_content_sha256: c.source.content_sha256.toLowerCase(),
    source_registry_independently_verified: false,
    source_rights_verified: false, abi_conformance_verified: false,
    owner_authorized: false, provider_readback_authenticated: false,
    native_admitted: false, capability_installed: false,
    execution_performed: false, canonical_mutation: false,
    public_publish_authorized: false,
    claim_boundary: 'Source-only CCC metadata projection; authenticated registry readback, licence, owner lease, native DBR and host conformance remain required.',
  });
}
