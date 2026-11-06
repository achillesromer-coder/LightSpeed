/**
 * CGX UniSpace R3 object viewport projection — source-only review contract.
 * This is NOT authentication or authorization. Its `grant` MUST be constructed
 * by an authenticated, server-side resolver after issuer/session/revocation,
 * root/DBR ACL, lease, source rights and exact Object_ID/child checks.
 * No client-provided grant, localStorage flag or localhost status is trusted.
 * Do not import private source data into Vite public paths.
 */
export const VIEWPORT_SCHEMA = 'CGX-UNISPACE-OBJECT-VIEW/0.1';
const VIEWS = new Set(['document', 'graph', '3d', 'chat', 'interactive', 'matrix']);
const STAGES = new Set(['SOURCE_FOUND', 'R1_TYPED', 'R2_MODELLED', 'SANDBOX_STAGED', 'NATIVE_ADMITTED', 'LIVE_VERIFIED', 'OWNER_ACCEPTED']);
const SHA256 = /^[a-f0-9]{64}$/i;
const ID = /^cgx:[a-z0-9][a-z0-9:_./-]{3,199}$/i;
const CHILD = /^Cognigrex\.cgx:\/[a-z0-9][a-z0-9/_-]{0,99}$/i;
const integer = (n, cap) => Number.isSafeInteger(n) && n >= 0 ? Math.min(n, cap) : 0;
const hold = (reason) => ({ schema: VIEWPORT_SCHEMA, state: 'HOLD', reason, layers: [], execution_available: false, canonical_mutation: false });

/**
 * @param {object} args
 * @param {object} args.request - selected exact object/child/view (untrusted UI input)
 * @param {object} args.grant - authenticated server resolver output, NEVER browser-created
 * @param {object} args.record - server-redacted object summary, NEVER original source bytes
 * @returns {object} allowlisted, non-effectful R3 projection or an opaque HOLD
 */
export function projectPermissionedObject({ request, grant, record } = {}) {
  if (!request || !grant || !record) return hold('NO_AUTHENTICATED_PROJECTION');
  // These flags are presentation assertions only; the server must enforce them.
  if (grant.issuer_verified !== true || grant.session_active !== true ||
      grant.revocation_checked !== true || grant.root_acl_verified !== true ||
      grant.dbr_scope_verified !== true || grant.lease_active !== true) {
    return hold('AUTHORITY_NOT_VERIFIED');
  }
  if (!ID.test(request.object_id ?? '') || !CHILD.test(request.child_filespace ?? '') ||
      request.object_id !== grant.object_id || request.object_id !== record.object_id ||
      request.child_filespace !== grant.child_filespace ||
      request.child_filespace !== record.child_filespace) {
    return hold('EXACT_SCOPE_MISMATCH');
  }
  if (grant.source_rights_approved !== true || record.source_rights_approved !== true ||
      record.release_class !== 'OWNER_PRIVATE') {
    return hold('SOURCE_RIGHTS_OR_CLASS_HOLD');
  }
  if (!SHA256.test(record.source_sha256 ?? '') || !STAGES.has(record.admission_stage)) {
    return hold('SOURCE_IDENTITY_OR_STAGE_UNQUALIFIED');
  }
  const view = VIEWS.has(request.view) ? request.view : 'document';
  const geometry = record.geometry;
  const hasMetricGeometry = geometry?.source_verified === true &&
    typeof geometry.frame === 'string' && geometry.frame.length > 0 &&
    typeof geometry.units === 'string' && geometry.units.length > 0 &&
    geometry.metric_validated === true;
  const effectiveView = view === '3d' && !hasMetricGeometry ? 'document' : view;
  // Never project source locators, original text, paths, model prompts, tokens,
  // graph edge identities or server-only authority fields to the UI.
  return {
    schema: VIEWPORT_SCHEMA,
    state: 'R3_REVIEW_PROJECTION',
    object_id: record.object_id,
    child_filespace: record.child_filespace,
    primary_view: effectiveView,
    requested_view: view,
    frontier: view === '3d' && !hasMetricGeometry ? 'GEOMETRY_FRAME_UNITS_OR_PROOF_MISSING' : null,
    evidence_class: typeof record.evidence_class === 'string' &&
      ['R0_EXACT', 'R1_TYPED', 'R2_CANDIDATE', 'R2_VALIDATED'].includes(record.evidence_class)
      ? record.evidence_class : 'UNQUALIFIED',
    admission_stage: record.admission_stage,
    layers: [
      { id: 'H0', state: 'IDENTITY_BOUND' },
      { id: 'H1', state: 'SCOPED_EDGE_COUNTS', count: integer(record.permitted_edge_count, 10000) },
      { id: 'H2', state: 'PROVENANCE_METADATA_ONLY', count: integer(record.permitted_source_count, 10000) },
      { id: 'H3', state: 'QUALIFIED_CAPABILITY_COUNTS', count: integer(record.qualified_capability_count, 10000) },
      { id: 'H4', state: 'EXECUTION_HELD' },
    ],
    execution_available: false,
    canonical_mutation: false,
    live_host_verified: false,
  };
}
