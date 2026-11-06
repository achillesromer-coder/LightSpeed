/**
 * UniSpace single-object drag/drop R0 text intake PREFLIGHT only.
 * Accepts File-like metadata; never reads bytes, opens a provider, or writes a CGX.
 * Existing CGX owner-session intake must separately hash, preserve, check rights,
 * run the native source-envelope/conversion registry and obtain DBR acceptance.
 * A caller-supplied context plan is NOT authentication or source verification.
 */
const SCHEMA = 'UNISPACE-CGX-ONE-OBJECT-TEXT-DROP-PREFLIGHT/0.1';
const HEX40 = /^[a-f0-9]{40}$/i;
const SAFE_ID = /^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const SAFE_SPACE = /^[A-Za-z][A-Za-z0-9_.-]*\.cgx$/;
const MAX_BYTES = 1048576;
const hold = code => Object.freeze({
  schema: SCHEMA, state: 'HOLD', hold_code: code,
  uploaded: false, native_admitted: false, canonical_mutation: false,
  source_bytes_read: false, private_route_authorized: false,
  public_publish_authorized: false
});

export function preflightCgxOneObjectTextDrop(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return hold('INVALID_REQUEST');
  if (input.intake_mode !== 'review_only' || input.requested_layer !== 'R0')
    return hold('UNSUPPORTED_INTAKE_MODE_OR_LAYER');
  if (!Array.isArray(input.files) || input.files.length !== 1)
    return hold('EXACTLY_ONE_FILE_REQUIRED');
  const p = input.context_plan;
  if (!p || p.schema !== 'UNISPACE-CGX-HOST-CONTEXT-GATE/0.1' ||
      p.state !== 'PLAN_ONLY_NOT_HYDRATED' ||
      p.native_admitted !== false || p.canonical_mutation !== false ||
      p.execution_performed !== false || p.private_hydration_authorized !== false ||
      p.public_publish_authorized !== false ||
      p.host_context_readback_authenticated !== false ||
      p.source_registry_independently_verified !== false)
    return hold('CONTEXT_PLAN_IS_NOT_SAFE_REVIEW_BOUNDARY');
  const id = input.target_object_id;
  const space = input.destination_filespace;
  if (typeof id !== 'string' || !SAFE_ID.test(id) || id.startsWith('cgx:domain:') ||
      id === 'cgx:root:cognigrex' || p.object_id !== id ||
      typeof space !== 'string' || !SAFE_SPACE.test(space) || p.filespace !== space ||
      !HEX40.test(p.source_lineage_git_blob_sha || '') ||
      !HEX40.test(p.source_registry_git_blob_sha || ''))
    return hold('OBJECT_ID_OR_CHILD_FILESPACE_MISMATCH');
  // No token, source bytes, arbitrary public path or caller-provided upload URL.
  for (const k of ['token','authorization','source_bytes','payload','upload_url','public_path','file_path']) {
    if (Object.prototype.hasOwnProperty.call(input,k))
      return hold('UNSAFE_INLINE_OR_ROUTE_INPUT');
  }
  const file = input.files[0];
  if (!file || typeof file !== 'object') return hold('INVALID_FILE_DESCRIPTOR');
  for (const k of ['bytes','content','source_bytes','token','path','webkitRelativePath']) {
    if (Object.prototype.hasOwnProperty.call(file,k) && file[k])
      return hold('UNSAFE_FILE_PAYLOAD_OR_PATH');
  }
  const name = file.name;
  if (typeof name !== 'string' || name.length < 5 || name.length > 180 ||
      name.startsWith('.') || /[\/\\\x00-\x1f\x7f]/.test(name) ||
      !/^[^\/\\]+\.txt$/i.test(name))
    return hold('UNSUPPORTED_OR_UNSAFE_FILE_NAME');
  if (!Number.isSafeInteger(file.size) || file.size < 1 || file.size > MAX_BYTES)
    return hold('FILE_SIZE_OUT_OF_BOUNDS');
  if (file.type !== '' && file.type !== 'text/plain')
    return hold('MIME_EXTENSION_MISMATCH');
  // File metadata is untrusted. No signature, bytes, digest or rights verified.
  return Object.freeze({
    schema: SCHEMA, state: 'PREFLIGHT_ONLY_NOT_UPLOADED',
    object_id: id, filespace: space, requested_layer: 'R0',
    file_class: 'text/plain', size_bytes_declared: file.size,
    source_name_returned: false, source_bytes_read: false, source_sha256_verified: false,
    signature_verified: false, rights_verified: false, acl_verified: false,
    owner_session_verified: false, provider_readback_verified: false,
    native_admitted: false, uploaded: false, canonical_mutation: false,
    private_route_authorized: false, public_publish_authorized: false,
    next_gate: 'EXISTING_AUTHENTICATED_CGX_NATIVE_INTAKE_R0_SOURCE_ENVELOPE_AND_DBR',
    claim_boundary: 'Review-only metadata preflight. File extension/MIME are untrusted; no content, rights, host, session, provider or DBR proof.'
  });
}
