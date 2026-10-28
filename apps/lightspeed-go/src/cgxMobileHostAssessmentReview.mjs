/**
 * Source-only crosswalk for the 2026-10-13 Achilles->Neo mobile roaming handoff.
 * A caller-supplied host assessment is NEVER an authenticated host readback.
 * This module cannot grant CAN_DO, lease authority, enqueue work or issue DBR receipts.
 * Parent CCC: Cognigrex.cgx:/ccc; child: Cognigrex -> EMASSC -> LS.cgx.
 */
export const MOBILE_HOST_ASSESSMENT_REVIEW_SCHEMA = 'CGX-MOBILE-HOST-ASSESSMENT-REVIEW/0.1';
const ID = /^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,95}$/;
const HEX40 = /^[0-9a-f]{40}$/i;
const HEX64 = /^[0-9a-f]{64}$/i;
const SECRET = /(?:^|[_-])(secret|token|password|credential|private[_-]?key|authorization|cookie|session|api[_-]?key|bearer)(?:$|[_-])/i;
const record = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const hold = code => Object.freeze({
  schema: MOBILE_HOST_ASSESSMENT_REVIEW_SCHEMA, state: 'HOLD',
  hold_code: code, effective_decision: 'HELD', host_readback_authenticated: false,
  owner_lease_verified: false, native_admitted: false, execution_performed: false,
  dbr_receipt_verified: false, drive_backup_verified: false,
});
const unsafe = (x, depth = 0, seen = new Set()) => {
  if (depth > 5) return true;
  if (x === null || typeof x !== 'object') return false;
  if (seen.has(x)) return true;
  seen.add(x);
  if (Object.keys(x).length > 64) return true;
  for (const [k,v] of Object.entries(x)) {
    if (SECRET.test(k) || unsafe(v, depth + 1, seen)) return true;
  }
  seen.delete(x);
  return false;
};
const hashes = a => Array.isArray(a) && a.length <= 16 &&
  a.every(x => typeof x === 'string' && HEX64.test(x)) &&
  new Set(a.map(x => x.toLowerCase())).size === a.length;
const sameHashes = (a,b) => a.length === b.length &&
  [...a].map(x => x.toLowerCase()).sort().every((x,i) =>
    x === [...b].map(y => y.toLowerCase()).sort()[i]);
const utc = x => typeof x === 'string' &&
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(x) &&
  Number.isFinite(Date.parse(x));
const safeBase = (state, request_id, reported_decision = null) => Object.freeze({
  schema: MOBILE_HOST_ASSESSMENT_REVIEW_SCHEMA, state,
  request_id, reported_decision, effective_decision: 'HELD',
  host_readback_authenticated: false, owner_lease_verified: false,
  native_admitted: false, execution_performed: false,
  dbr_receipt_verified: false, drive_backup_verified: false,
  required_next_proof: 'authenticated existing-host capability/lease readback plus independent DBR receipt',
});
/**
 * @param {object} input - Untrusted source-review inputs. now_utc is a deterministic
 *   fixture clock, not proof of an authenticated host clock.
 * @returns {object} Immutable, non-authorizing review result.
 */
export function reviewCgxMobileHostCapabilityClaim(input) {
  if (!record(input) || !record(input.preflight) || !record(input.request))
    return hold('INVALID_INPUT');
  const {preflight:p, request:r, assessment:a = null, now_utc:now, seen_request_ids:seen=[]} = input;
  if (unsafe(r) || (a !== null && unsafe(a))) return hold('SENSITIVE_OR_UNBOUNDED_INPUT');
  if (p.schema !== 'CGX-CCC-MOBILE-SOURCE-GATE/0.1' ||
      !['PLAN_ONLY','DISCOVERY_ONLY'].includes(p.state) ||
      p.filespace !== 'LS.cgx' || p.parent_filespace !== 'EMASSC.cgx' ||
      p.ccc_location !== 'Cognigrex.cgx:/ccc' ||
      p.native_admitted !== false || p.owner_authorized !== false ||
      p.execution_performed !== false || p.provider_readback_authenticated !== false)
    return hold('SOURCE_PREFLIGHT_NOT_QUALIFIED');
  if (r.schema_version !== 'cgx-roaming-request-v1' ||
      !ID.test(r.request_id || '') || !ID.test(r.required_capability_id || '') ||
      r.required_capability_id !== p.capability_id ||
      !HEX40.test(r.expected_revision_or_cursor || '') ||
      r.expected_revision_or_cursor.toLowerCase() !== p.source_revision ||
      r.status !== 'staged' || r.requested_intent !== 'metadata_only' ||
      !hashes(r.input_content_hashes))
    return hold('REQUEST_IDENTITY_OR_SCOPE_INVALID');
  if (!utc(r.created_utc) || !utc(r.expires_utc) || !utc(now))
    return hold('CLOCK_OR_EXPIRY_FORMAT_INVALID');
  if (Date.parse(now) < Date.parse(r.created_utc) ||
      Date.parse(now) >= Date.parse(r.expires_utc))
    return hold('REQUEST_NOT_CURRENT_AT_FIXTURE_CLOCK');
  if (!Array.isArray(seen) || seen.length > 64 || seen.some(x => !ID.test(x)))
    return hold('REPLAY_SET_INVALID');
  if (seen.includes(r.request_id)) return hold('DUPLICATE_REQUEST_ID');
  if (a === null) return safeBase('WAIT_HOST', r.request_id);
  if (!record(a) || a.schema !== 'CGX-ROAMING-ASSESSMENT-CANDIDATE/0.1' ||
      a.request_id !== r.request_id || a.required_capability_id !== r.required_capability_id ||
      a.source_revision !== r.expected_revision_or_cursor ||
      !hashes(a.input_content_hashes) || !sameHashes(a.input_content_hashes, r.input_content_hashes))
    return hold('HOST_CLAIM_IDENTITY_OR_HASH_MISMATCH');
  if (!['CAN_DO','CAN_DO_WHEN_READY','UNSUPPORTED','HELD'].includes(a.decision) ||
      !['assessed','held'].includes(a.operation_state) ||
      a.execution_performed === true || a.operation_state === 'running' ||
      a.operation_state === 'executed')
    return hold('HOST_CLAIM_NOT_REVIEWABLE');
  if (a.decision === 'HELD') return hold('HOST_REPORTS_HELD');
  // Even CAN_DO is an unverified capability claim, never a permission to execute.
  return safeBase('UNVERIFIED_HOST_CLAIM', r.request_id, a.decision);
}
