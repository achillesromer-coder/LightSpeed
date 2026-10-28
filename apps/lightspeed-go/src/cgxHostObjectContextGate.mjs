/**
 * UniSpace read-only adapter for an EXISTING LightSpeed object-context response.
 * Source review only: this does not fetch, authenticate, hydrate, mint, or publish.
 * The lineage and child registry supplied by the caller are evidence candidates,
 * NOT independently verified by this client-side adapter.
 */
const HEX40 = /^[a-f0-9]{40}$/i;
const SCHEMA = 'UNISPACE-CGX-HOST-CONTEXT-GATE/0.1';
const hold = (code) => Object.freeze({
  schema: SCHEMA, state: 'HOLD', hold_code: code, native_admitted: false,
  private_hydration_authorized: false, public_publish_authorized: false,
  canonical_mutation: false, execution_performed: false,
});

export function projectCgxHostObjectContextGate(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return hold('INVALID_INPUT');
  const { requested_object_id: id, requested_layer: layer, expected_child: child,
    context_response: response, lineage_candidates: matches,
    lineage_git_blob_sha: lineageSha, registry_git_blob_sha: registrySha } = input;
  if (typeof id !== 'string' || !id || id.length > 128 || /[\x00-\x1f\x7f]/.test(id)) return hold('INVALID_OBJECT_ID');
  if (id.startsWith('cgx:domain:') || id === 'cgx:root:cognigrex') return hold('DOMAIN_ID_IS_NOT_INSTANCE_ID');
  if (!child || typeof child !== 'object' || !/^cgx:domain:[a-z]+$/.test(child.semantic_object_id || '') ||
      !/^[A-Za-z][A-Za-z0-9_.-]*\.cgx$/.test(child.filespace || '') ||
      !/^[a-z]+$/.test(child.domain || '') || !HEX40.test(lineageSha || '') || !HEX40.test(registrySha || ''))
    return hold('SOURCE_REGISTRY_BINDING_UNVERIFIED');
  if (!Array.isArray(matches) || matches.length !== 1 || matches[0]?.semantic_object_id !== id ||
      typeof matches[0]?.twin_id !== 'string' || !matches[0].twin_id)
    return hold('MISSING_OR_COLLIDING_SEMANTIC_ID');
  if (!response || response.execution_performed !== false || response.external_action_performed !== false ||
      response.canonical_mutation !== false || response.authority_transfer !== false)
    return hold('HOST_RESPONSE_BOUNDARY_UNVERIFIED');
  const context = response.object_context;
  if (context?.schema !== 'CGX-OBJECT-CONTEXT/0.1' || context.automatic_execution !== false ||
      context.canonical_mutation !== false) return hold('HOST_CONTEXT_SCHEMA_OR_BOUNDARY');
  if (context.semantic_resolution?.state !== 'exact_semantic_object' ||
      context.semantic_resolution.semantic_object_id !== id ||
      context.resolved_twin_id !== matches[0].twin_id)
    return hold('FAMILY_ONLY_OR_OBJECT_ID_MISMATCH');
  if (context.semantic_domain !== child.domain ||
      context.domain_identity?.semantic_object_id !== child.semantic_object_id ||
      context.domain_identity?.filespace !== child.filespace)
    return hold('CHILD_FILESPACE_MISMATCH');
  if (layer !== 'R0') return hold('PRIVATE_LAYER_REQUIRES_AUTH_AND_DBR');
  // Never echo source paths, representation, URLs, session data or raw provider records.
  return Object.freeze({
    schema: SCHEMA, state: 'PLAN_ONLY_NOT_HYDRATED', object_id: id,
    filespace: child.filespace, resolved_twin_id: matches[0].twin_id,
    requested_layer: 'R0', source_lineage_git_blob_sha: lineageSha,
    source_registry_git_blob_sha: registrySha,
    source_registry_independently_verified: false,
    host_context_readback_authenticated: false,
    private_hydration_authorized: false, private_data_returned: false,
    native_admitted: false, public_publish_authorized: false,
    canonical_mutation: false, execution_performed: false,
    claim_boundary: 'Metadata-only source-review plan. Provider readback, owner session, source rights and DBR must be independently checked by the authorised host.',
  });
}
