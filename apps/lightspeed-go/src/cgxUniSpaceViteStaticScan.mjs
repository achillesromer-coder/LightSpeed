/**
 * UniSpace source-only Vite public/dist asset inspection, one candidate Object_ID.
 * Reads only supplied review directories. Never authenticates a host, changes files,
 * serves bytes, or grants release. No original filenames, paths or contents returned.
 * Actual deployment and anonymous/revoked HTTP acceptance remain separate (#158).
 */
import { lstat, readdir, readFile } from 'node:fs/promises';
import { isAbsolute, join, relative, sep } from 'node:path';
import { createHash } from 'node:crypto';

export const SCHEMA = 'UNISPACE-VITE-STATIC-SCAN/0.1';
const CHILDREN = new Set(['Romer.cgx', 'Eco.cgx', 'EMASSC.cgx', 'LS.cgx']);
const OBJECT_ID = /^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const TEXT_EXT = /\.(?:json|svg|html|css|js|mjs|txt|map|xml|md)$/i;
const PRIVATE_MARKERS = /\b(?:INTERNAL_REVIEW|ACTIVE_INTERNAL_REVIEW|OWNER_PRIVATE|CONFIDENTIAL|PRIVATE_CGX|PRIVATE_SOURCE|NOT_PUBLIC)\b/i;
const PRIVATE_FIELDS = /["'](?:source_locator|private_path|carrier_path|access_token|api_key|credential|dbr_root|state_root)["']\s*:/i;
const hash = x => createHash('sha256').update(x).digest('hex');
const record = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const ownKeys = (x, keys) => record(x) && Object.keys(x).every(k => keys.includes(k));
const hold = code => Object.freeze({ schema: SCHEMA, state: 'HOLD', hold_code: code, source_scan_complete: false, dist_verified: false, host_http_verified: false, release_accepted: false, canonical_mutation: false });

export async function scanUniSpaceViteStaticReview(input) {
  if (!ownKeys(input, ['selection', 'client_permissions', 'public_root', 'dist_root', 'limits'])) return hold('INVALID_INPUT');
  const { selection: s, client_permissions: p, public_root, dist_root, limits = {} } = input;
  if (!ownKeys(s, ['parent_filespace','object_id','filespace','identity_status','evidence_class']) ||
      s.parent_filespace !== 'Cognigrex.cgx' || !OBJECT_ID.test(s.object_id || '') ||
      s.object_id.startsWith('cgx:domain:') || s.object_id === 'cgx:root:cognigrex' ||
      !CHILDREN.has(s.filespace) || s.identity_status !== 'SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED' ||
      !['scientific','creative','mixed','unknown'].includes(s.evidence_class)) return hold('EXACT_CANDIDATE_REQUIRED');
  if (!ownKeys(p, ['mode','revoked','allowed_object_ids','allowed_filespaces']) || p.mode !== 'review_only' || p.revoked !== false ||
      !Array.isArray(p.allowed_object_ids) || p.allowed_object_ids.length !== 1 || p.allowed_object_ids[0] !== s.object_id ||
      !Array.isArray(p.allowed_filespaces) || p.allowed_filespaces.length !== 1 || p.allowed_filespaces[0] !== s.filespace) return hold('CLIENT_SCOPE_MISMATCH');
  if (!ownKeys(limits, ['max_files','max_total_bytes','max_file_bytes']) ||
      !isAbsolute(public_root || '') || (dist_root !== null && dist_root !== undefined && !isAbsolute(dist_root || ''))) return hold('INVALID_SCAN_ROOT');
  const maxFiles = limits.max_files ?? 256;
  const maxTotal = limits.max_total_bytes ?? 16 * 1024 * 1024;
  const maxFile = limits.max_file_bytes ?? 2 * 1024 * 1024;
  if (![maxFiles,maxTotal,maxFile].every(Number.isSafeInteger) || maxFiles < 1 || maxFiles > 1024 ||
      maxTotal < 1 || maxTotal > 60 * 1024 * 1024 || maxFile < 1 || maxFile > 4 * 1024 * 1024 || maxFile > maxTotal) return hold('INVALID_SCAN_LIMIT');
  let files = 0, bytes = 0, complete = true;
  const findings = [];
  const add = (rootTag, rel, reasons, sha256 = null) => {
    if (reasons.some(x => ['SYMLINK_NOT_FOLLOWED','NONREGULAR_ASSET','UNINSPECTED_SIZE_LIMIT','UNINSPECTABLE_BINARY_RIGHTS_UNKNOWN','UNPARSEABLE_JSON'].includes(x))) complete = false;
    findings.push(Object.freeze({
    asset_key: hash(rootTag + "\0" + rel).slice(0, 24), sha256, reason_codes: Object.freeze([...new Set(reasons)].sort())
  }));
  };
  async function walk(root, rootTag) {
    const stat = await lstat(root);
    if (!stat.isDirectory() || stat.isSymbolicLink()) throw Error('INVALID_ROOT_TYPE');
    const queue = [''];
    while (queue.length) {
      const relDir = queue.shift();
      const names = (await readdir(join(root, relDir), { withFileTypes: true })).sort((a,b)=>a.name.localeCompare(b.name));
      for (const entry of names) {
        const rel = join(relDir, entry.name);
        const relCheck = relative(root, join(root, rel));
        if (relCheck.startsWith(".." + sep) || relCheck === '..' || isAbsolute(relCheck)) throw Error('PATH_OUTSIDE_ROOT');
        if (entry.isDirectory()) { queue.push(rel); continue; }
        if (++files > maxFiles) throw Error('FILE_COUNT_LIMIT');
        if (entry.isSymbolicLink()) { add(rootTag, rel, ['SYMLINK_NOT_FOLLOWED']); continue; }
        if (!entry.isFile()) { add(rootTag, rel, ['NONREGULAR_ASSET']); continue; }
        const stat = await lstat(join(root, rel));
        if (!stat.isFile() || stat.isSymbolicLink()) { add(rootTag, rel, ['NONREGULAR_ASSET']); continue; }
        if (stat.size > maxFile || bytes + stat.size > maxTotal) { add(rootTag, rel, ['UNINSPECTED_SIZE_LIMIT']); continue; }
        const body = await readFile(join(root, rel));
        bytes += body.length;
        const reasons = [];
        if (!TEXT_EXT.test(rel)) reasons.push('UNINSPECTABLE_BINARY_RIGHTS_UNKNOWN');
        else {
          const text = body.toString('utf8');
          if (PRIVATE_MARKERS.test(text)) reasons.push('PRIVATE_REVIEW_MARKER_IN_STATIC_TREE');
          if (PRIVATE_FIELDS.test(text)) reasons.push('POTENTIAL_PRIVATE_METADATA_IN_STATIC_TREE');
          if (/\.json$/i.test(rel)) {
            try {
              const parsed = JSON.parse(text);
              if (parsed && typeof parsed === 'object' && /INTERNAL|PRIVATE/i.test(String(parsed.status || '')))
                reasons.push('INTERNAL_STATUS_IN_STATIC_JSON');
            } catch { reasons.push('UNPARSEABLE_JSON'); }
          }
        }
        // File bytes and caller-provided metadata cannot establish independent owner rights.
        reasons.push('PUBLIC_RIGHTS_AND_OWNER_CLEARANCE_UNVERIFIED');
        add(rootTag, rel, reasons, hash(body));
      }
    }
  }
  try {
    await walk(public_root, 'public');
    if (dist_root !== null && dist_root !== undefined) await walk(dist_root, 'dist');
  } catch (err) {
    // Error messages may contain paths. Never return them.
    return hold(['INVALID_ROOT_TYPE','PATH_OUTSIDE_ROOT','FILE_COUNT_LIMIT'].includes(err?.message) ? err.message : 'SCAN_IO_OR_PERMISSION_FAILURE');
  }
  const ordered = findings.sort((a,b)=>a.asset_key.localeCompare(b.asset_key));
  return Object.freeze({ schema: SCHEMA, state: 'SOURCE_SCAN_REVIEW_ONLY',
    parent_filespace: s.parent_filespace, candidate_object_id: s.object_id, filespace: s.filespace,
    evidence_class: s.evidence_class, alias: 'LOAD.cgx', alias_role: 'ALEXANDRIA_ENTRY_NOT_PARENT',
    file_entries: files, bytes_inspected: bytes, source_scan_complete: complete,
    public_source_scanned: true, dist_source_scanned: dist_root !== null && dist_root !== undefined,
    findings: Object.freeze(ordered), risk_count: ordered.filter(x=>x.reason_codes.length).length,
    dist_verified: false, host_http_verified: false, release_accepted: false, canonical_mutation: false,
    native_admitted: false, offline_hydration: 'H0_METADATA_ONLY', gate: 'HOLD_ISSUE_158_AND_161',
    next_step: 'OWNER_CLEARED_PUBLIC_SUBSET_AND_INDEPENDENT_DEPLOYED_BUILD_PLUS_NEGATIVE_HTTP_READBACK',
    claim_boundary: 'Sandbox filesystem scan is not an authenticated deployed-host or browser test. No public-rights clearance inferred.' });
}
