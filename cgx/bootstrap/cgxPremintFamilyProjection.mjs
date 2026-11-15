/**
 * LOAD -> CGX family -> UniSpace source-review projection.
 * Reuses the existing batch convergence and leaf code. Never mints,
 * dispatches agents, publishes data, writes a DBR, or transfers sources.
 */
import {buildReviewEnvelope,verifyEnvelope,planHydration} from './cgxLeafEnvelopeReview.mjs';
import {convergeCGXBatch} from './cgxBatchConvergence.mjs';
export const SCHEMA='CGX-PREMINT-FAMILY-PROJECTION/0.1';
const FAMILIES=new Set(['Cognigrex.cgx','Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']);
const RIGHTS=new Set(['public_clear','internal_only','restricted','unknown']);
const ACLS=new Set(['public','internal','owner_only','unknown']);
const id=/^[a-z][a-z0-9:_./-]{0,127}$/;
const valid=x=>typeof x==='string'&&id.test(x)&&!x.includes('..')&&!x.includes('://');
const denied=x=>({schema:SCHEMA,state:'DENIED',reason:x,canonical_mutation:false,may_mint:false,may_publish:false});
export function stageFamilyPacket({objectId,version,originalLeaves,family,owner,
  semanticKey,rights='unknown',acl='unknown',rightsRef=null,aclRef=null,
  dependencies=[],capabilities=[]}={}){
 if(!valid(objectId)||!valid(owner)||!valid(semanticKey)||!FAMILIES.has(family)||!RIGHTS.has(rights)||!ACLS.has(acl)
    ||typeof version!=='string'||! /^(0|[1-9][0-9]{0,17})$/.test(version))return denied('SOURCE_IDENTITY_SCOPE_INVALID');
 if(!Array.isArray(capabilities)||capabilities.length>100||
    capabilities.some(c=>!c||!valid(c.capability_id)||!['tool','view','resolver','widget','skillset','adapter'].includes(c.kind)))
    return denied('CAPABILITY_REVIEW_INVALID');
 const env=buildReviewEnvelope({objectId,version,leaves:originalLeaves,dependencies,rightsRef,aclRef});
 if(!verifyEnvelope(env))return denied(env.reason||'SOURCE_ENVELOPE_INVALID');
 const source={source_id:objectId,revision:version,sha256:env.manifest.source.sha256,
    family,owner,abi:'read:cgx:leaf:1',semantic_key:semanticKey,rights,acl};
 const report=convergeCGXBatch({parent:'cgx:root:cognigrex',sources:[source],
   capabilities:capabilities.map(c=>({capability_id:c.capability_id,source_id:objectId,
      owner,abi:source.abi,kind:c.kind})),phases:[],aliases:[],transferred_bytes:0});
 return {schema:SCHEMA,state:report.blockers.length?'REVIEW_WITH_HOLDS':'PREMINT_REVIEW_ONLY',
  canonical_parent:'cgx:root:cognigrex',library:'LOAD.cgx',
  envelope:env,convergence:report,
  canonical_mutation:false,may_mint:false,may_publish:false,
  note:'Source identity and content hashes are derived from supplied bytes; origin, rights and issuer remain independently unverified'};
}
export function projectUniSpace(packet,{audience='owner',requestedLeaves=[],proof=null}={}){
 if(!packet||packet.schema!==SCHEMA||!verifyEnvelope(packet.envelope)||
    !packet.convergence||packet.convergence.parent!=='cgx:root:cognigrex')
    return denied('UNQUALIFIED_PACKET');
 if(audience!=='owner')return {schema:SCHEMA,state:'HOLD',reason:'PUBLIC_RELEASE_NOT_AUTHORISED',
   may_publish:false,network_transfer:false};
 const m=packet.envelope.manifest;
 const r=planHydration(packet.envelope,requestedLeaves,proof);
 return {schema:SCHEMA,state:'SOURCE_ONLY_PRIVATE_PROJECTION',audience:'owner',
  h0:{object_id:m.object_id,version:m.version,source_sha256:m.source.sha256,
    manifest_digest:packet.envelope.digest_sha256},
  h1:{dependencies:m.dependencies,leaf_count:m.leaves.length},
  h2:{evidence_stage:'REVIEW_ONLY',rights_reference_present:!!m.rights_ref,
    acl_reference_present:!!m.acl_ref,source_qualified:false},
  h3:{candidate_capability_ids:packet.convergence.capabilities.map(x=>x.capability_id),
    installed_capabilities_verified:false},
  h4:{execution:'DISABLED_AUTHORITY_HOLD',native_admitted:false, may_mint:false,may_publish:false},
  hydration:r,
  network_transfer:false,canonical_mutation:false};
}
