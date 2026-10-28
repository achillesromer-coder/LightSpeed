/**
 * UniSpace source-only Vite route/reference boundary audit.
 * One candidate Object_ID, one child FileSpace; no HTTP, install, publish or ACL proof.
 * Reads only caller-supplied review text and source metadata. Never emits paths or bytes.
 * A heuristic scan cannot prove absence of dynamic imports, bundled assets or leaks.
 */
import { createHash } from 'node:crypto';
export const SCHEMA = 'UNISPACE-STATIC-ROUTE-REFERENCE-REVIEW/0.1';
const CHILDREN = new Set(['Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']);
const ID = /^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const NAME = /^[a-z][a-z0-9_-]{0,63}$/;
const PATH = /^[A-Za-z0-9_./-]{1,240}$/;
const obj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const keys = (x, allowed) => obj(x) && Object.keys(x).every(k => allowed.includes(k));
const sha256 = x => createHash('sha256').update(x).digest('hex');
const hold = code => Object.freeze({ schema:SCHEMA, state:'HOLD', hold_code:code, native_admitted:false, host_http_verified:false, release_accepted:false, canonical_mutation:false });
const safePath = p => typeof p === 'string' && PATH.test(p) && !p.startsWith('/') && !p.includes('..') && !p.includes('//') && !p.includes('\\');
const publicRef = p => p.replace(/^\.\//,'').replace(/^\//,'');

export function reviewUniSpaceStaticRouteReferences(input) {
 if (!keys(input,['selection','client_permissions','entry_source','assets'])) return hold('INVALID_INPUT');
 const { selection:s, client_permissions:p, entry_source:src, assets } = input;
 if (!keys(s,['parent_filespace','object_id','filespace','identity_status','evidence_class']) ||
   s.parent_filespace !== 'Cognigrex.cgx' || !ID.test(s.object_id || '') ||
   s.object_id.startsWith('cgx:domain:') || s.object_id === 'cgx:root:cognigrex' ||
   !CHILDREN.has(s.filespace) || s.identity_status !== 'SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED' ||
   !['scientific','creative','mixed','unknown'].includes(s.evidence_class)) return hold('EXACT_CANDIDATE_REQUIRED');
 if (!keys(p,['mode','revoked','allowed_object_ids','allowed_filespaces']) ||
   p.mode !== 'review_only' || p.revoked !== false ||
   !Array.isArray(p.allowed_object_ids) || p.allowed_object_ids.length !== 1 || p.allowed_object_ids[0] !== s.object_id ||
   !Array.isArray(p.allowed_filespaces) || p.allowed_filespaces.length !== 1 || p.allowed_filespaces[0] !== s.filespace)
   return hold('CLIENT_SCOPE_MISMATCH');
 if (typeof src !== 'string' || !src.length || Buffer.byteLength(src,'utf8') > 512 * 1024 ||
   !Array.isArray(assets) || assets.length < 1 || assets.length > 64) return hold('SOURCE_OR_ASSET_LIMIT');
 const byPath = new Map(), seen = new Set();
 for (const a of assets) {
   if (!keys(a,['asset_id','public_relative_path','source_class','scope','rights','owner_clearance','object_id','filespace']) ||
     !NAME.test(a.asset_id || '') || seen.has(a.asset_id) || !safePath(a.public_relative_path) ||
     !['INTERNAL_REVIEW','OWNER_PRIVATE','PUBLIC_CANDIDATE','UNKNOWN'].includes(a.source_class) ||
     !['ONE_OBJECT','MULTI_OBJECT','UNKNOWN'].includes(a.scope) ||
     !['CLEARED_PUBLIC','UNRESOLVED','RESTRICTED'].includes(a.rights) ||
     typeof a.owner_clearance !== 'boolean' ||
     !(a.object_id === null || (typeof a.object_id === 'string' && ID.test(a.object_id))) ||
     !(a.filespace === null || CHILDREN.has(a.filespace)) || byPath.has(a.public_relative_path)) return hold('INVALID_OR_DUPLICATE_ASSET');
   seen.add(a.asset_id); byPath.set(a.public_relative_path,a);
 }
 // Only recognises simple literal browser URLs. Unknown/dynamic routes remain FRONTIER.
 const named = new Map();
 const declarations = /\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*new\s+URL\s*\(\s*(["'`])([^"'`]+)\2\s*,\s*document\.baseURI\s*\)\s*\.toString\s*\(\s*\)/g;
 for (const m of src.matchAll(declarations)) named.set(m[1],publicRef(m[3]));
 const fetches = /\bfetch\s*\(\s*([^,\)]+)/g;
 const refs = new Map(); let dynamic = 0;
 for (const m of src.matchAll(fetches)) {
   const expr = m[1].trim(); let path;
   if (/^[A-Za-z_$][\w$]*$/.test(expr)) path=named.get(expr);
   else if (/^["'`][^"'`]+["'`]$/.test(expr)) path=publicRef(expr.slice(1,-1));
   if (!path || !safePath(path)) { dynamic++; continue; }
   refs.set(path,(refs.get(path)||0)+1);
 }
 const results = [];
 for (const a of assets) {
   const reasons = [];
   if (a.source_class !== 'PUBLIC_CANDIDATE') reasons.push('NONPUBLIC_SOURCE_IN_VITE_PUBLIC');
   if (a.rights !== 'CLEARED_PUBLIC' || !a.owner_clearance) reasons.push('PUBLIC_RIGHTS_OR_CLEARANCE_UNVERIFIED');
   if (a.scope !== 'ONE_OBJECT' || a.object_id !== s.object_id || a.filespace !== s.filespace) reasons.push('NOT_EXACT_OBJECT_AND_CHILD_SCOPED');
   const fetchCount = refs.get(a.public_relative_path) || 0;
   if (fetchCount && reasons.length) reasons.push('SOURCE_CODE_FETCHES_HELD_PUBLIC_ASSET');
   results.push(Object.freeze({asset_key:sha256(a.asset_id).slice(0,24), referenced_by_fetch:fetchCount>0, fetch_count:fetchCount, risk_codes:Object.freeze(reasons)}));
 }
 const unmatched = [...refs.keys()].filter(k=>!byPath.has(k)).length;
 return Object.freeze({
   schema:SCHEMA,state:'SOURCE_REVIEW_ONLY',parent_filespace:s.parent_filespace,
   candidate_object_id:s.object_id,filespace:s.filespace,evidence_class:s.evidence_class,
   alias:'LOAD.cgx',alias_role:'ALEXANDRIA_ENTRY_NOT_PARENT',
   source_sha256:sha256(src),assets:Object.freeze(results),asset_count:results.length,
   held_public_asset_count:results.filter(x=>x.risk_codes.length).length,
   referenced_held_asset_count:results.filter(x=>x.referenced_by_fetch&&x.risk_codes.length).length,
   unmatched_literal_fetch_count:unmatched,unresolved_fetch_count:dynamic,
   gate:'HOLD_ISSUE_158_AND_161',native_admitted:false,host_http_verified:false,
   dist_verified:false,release_accepted:false,canonical_mutation:false,network_fetch:false,
   source_bytes_transferred:0,offline_hydration:'H0_METADATA_ONLY',
   claim_boundary:'Heuristic source review only. Does not establish compiled Vite dist, public HTTP exposure, negative ACL, host auth or absence of dynamic routes.'
 });
}
