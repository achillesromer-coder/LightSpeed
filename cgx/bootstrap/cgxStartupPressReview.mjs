#!/usr/bin/env node
/**
 * One CGX startup + first-spaces Press review from EXISTING contracts.
 * No duplicate root, automatic mint, source deletion, deploy or native signer.
 */
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
import {planCGXSetup} from './unifiedBootstrap.mjs';
import {planFirstSpacesReview} from '../../apps/lightspeed-go/src/cgxFirstSpacesReviewModel.mjs';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const SOURCE='cgx/domain_templates/achilles_file_space_launch_review_contract.json';
const PHASE_IDS=['file_space','unispace_file_space_control','data_space','print_space'];
const PHASE_DEPS=[[],['file_space:ACCEPTED'],
 ['file_space:LANDED_AND_ACCEPTED','unispace_file_space_control:TESTED'],
 ['file_space:LANDED_AND_ACCEPTED','data_space:TESTED']];
const PHASE_STATES=['PRIVATE_R1_CANDIDATE_NOT_ACCEPTED',
 'REVIEW_STAGE_BLOCKED_BY_FILESPACE_AND_R3','NOT_ACTIVATED','DESIGN_ONLY_NOT_ENABLED'];
export const SCHEMA='CGX-STARTUP-LOAD-PREMINT-PRESS-REVIEW/0.1';
const ROOT_KEY='family.cognigrex';
const FAMILIES=['Cognigrex.cgx','Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx'];
const hold=reason=>({schema:SCHEMA,state:'HOLD',reason,
  minted:false,signed:false,source_deleted:false,deployed:false,canonical_mutation:false});
export function planStartupPressReview({contract,layout='lattice',order=null,focus='facet.load',decisions={}}={}){
 if(!contract||contract.schema!=='CGX-ACHILLES-FILESPACE-FIRST-REVIEW-CONTRACT/0.1'||
    contract.state!=='REVIEW_ONLY_UNMINTED'||contract.canonical_parent!=='cgx:root:cognigrex'||
    contract.canonical_objects_minted!==0||!Array.isArray(contract.phase_order)||
    contract.phase_order.length!==PHASE_IDS.length||
    contract.phase_order.some((phase,i)=>phase?.id!==PHASE_IDS[i]||
     phase?.state!==PHASE_STATES[i]||!Array.isArray(phase.dependency)||
     JSON.stringify(phase.dependency)!==JSON.stringify(PHASE_DEPS[i])))
  return hold('UNQUALIFIED_FIRST_SPACE_SOURCE_CONTRACT');
 const lattice=planFirstSpacesReview({layout,order,focus,decisions});
 if(lattice.state!=='SOURCE_REVIEW_ONLY')return hold('INVALID_LATTICE_REVIEW');
 const keys=new Set(lattice.nodes.map(n=>n.key));
 if(keys.size!==lattice.nodes.length||!keys.has(ROOT_KEY)||
    lattice.edges.some(edge=>!keys.has(edge.from)||!keys.has(edge.to)))
  return hold('MISSING_OR_DUPLICATE_TOPOLOGICAL_OBJECT');
 // A visual drag reorder cannot create a dependency cycle, override parentage
 // or change the actual conservative Press sequence.
 const minted=new Set();
 for(const key of lattice.mint_sequence){
  const n=lattice.nodes.find(x=>x.key===key);
  if(!n||n.requires.some(k=>!minted.has(k))||(n.parent&&!minted.has(n.parent)))
   return hold('PRESS_DEPENDENCY_DAG_UNRESOLVED');
  minted.add(key);
 }
 const setup=FAMILIES.map(family=>planCGXSetup({family,mode:'first-run',
  device:'desktop',intent:'plan',observed:{}}));
 if(setup.some(p=>p.state!=='REVIEW_ONLY'||p.canonical_accepted!==false||
    p.library?.name!=='LOAD.cgx'||p.library?.bind!=='EXISTING_IDENTITY_ONLY'||
    p.ls_go?.enabled!==false||p.published!==false))
  return hold('BOOTSTRAP_SOURCE_AUTHORITY_MISMATCH');
 const blocked=[...new Set(setup.flatMap(x=>x.blockers))];
 const candidates=lattice.mint_sequence.map((key,index)=>{
  const node=lattice.nodes.find(x=>x.key===key);
  const familyOrResolver=['canonical-parent','resolver-facet','grex-family','nested-grex'].includes(node.kind);
  return {sequence:index+1,candidate_key:key,
   label:node.label,kind:node.kind,parent_candidate_key:node.parent,
   dependency_keys:node.requires,geometric_role:node.role,
   mint_scope:familyOrResolver?'CANONICAL_TYPE_OR_FACET':'FUNCTIONAL_SPACE_VIEW_NOT_SEPARATELY_MINTED',
   design_review_state:node.review_stage,
   source_digest:null,source_rights:'UNVERIFIED',asset_manifest_digest:null,
   signed_object_id:null,native_mint_intent:null,founder_signoff_verified:false,
   eligible_for_native_mint:false,actual_minted:false};
 });
 return {schema:SCHEMA,state:'STARTUP_SOURCE_REVIEW_READY_NOT_NATIVE',
  canonical_parent:'cgx:root:cognigrex',resolver:'LOAD.cgx',
  first_run:'EXISTING_UNIFIED_BOOTSTRAP_REVIEW_ONLY',
  bootstrap_family_count:setup.length,
  bootstrap_blockers:blocked,
  lattice:{schema:lattice.schema,layout:lattice.layout,focus:lattice.focus,
   nodes:lattice.nodes,edges:lattice.edges,visual_order:lattice.order},
  press:{candidates,canonical_type_candidates:candidates.filter(x=>x.mint_scope==='CANONICAL_TYPE_OR_FACET').length,
   native_mint_intents_created:0,founder_review:'DESIGN_APPROVAL_NOT_NATIVE_SIGNOFF'},
  first_spaces:contract.phase_order.map((x,i)=>({order:i+1,id:x.id,
   source_stage:x.state,dependencies:x.dependency,
   installed:false,native_accepted:false})),
  product_surfaces:{unispace:'SEPARATE_USER_PRODUCT_NOT_MINT_ISSUER',
   lightspeed:'GREX_EXECUTION_NOT_SECOND_ROOT',
   ccc:'CAPABILITY_ROUTE_WITH_PER_TOOL_AUTHORITY',
   filespace:'R0_SOURCE_CARRIER_RETAINED',
   dataspace:'TYPED_ASSERTIONS_HOLD_PENDING_DBR',
   printspace:'GEOMETRY_AND_PHYSICS_EVIDENCE_HOLD'},
  pending_acceptance_edges:[
   {from:'CGX startup',to:'canonical parent',requires:'signed RootAuthority + exact native Object_ID',accepted:false},
   {from:'LOAD',to:'FileSpace',requires:'qualified source rights + R0 hash roundtrip + owner ACL',accepted:false},
   {from:'FileSpace',to:'UniSpace control',requires:'private route and current session ACL + R3 presentation negatives',accepted:false},
   {from:'FileSpace',to:'DataSpace',requires:'typed claims + independently accepted DBR',accepted:false},
   {from:'DataSpace',to:'PrintSpace',requires:'geometry source, units, frame and physics acceptance',accepted:false},
   {from:'CCC',to:'LightSpeed/LS',requires:'installed capability + lease/consumer receipt + singleton owner',accepted:false},
   {from:'Press review',to:'native mint',requires:'founder native signoff + issuer + asset availability/revocation verification',accepted:false},
   {from:'native mint',to:'public UniSpace release',requires:'host HTTP privacy #158 + publication rights + distinct-node acceptance #161',accepted:false}
  ],
  approval_gates:{rights:'HOLD',root_authority:'HOLD',independent_two_node_dbr:'HOLD',
   signed_issuer:'HOLD',live_mint:'HOLD',publish:'HOLD',source_delete:'HOLD'},
  review_controls:{rearrange:'VISUAL_EPHEMERAL_ONLY',facets:'SOURCE_REVIEW_ONLY',
   founder_decisions:'DESIGN_REVIEW_ONLY_NO_PERSISTED_SIGNOFF'},
  source_originals_preserved:true,canonical_mutation:false,
  native_minted:false,signed:false,source_deleted:false,deployed:false};
}
export function buildHostStartupPressReceipt(){
 const bytes=execFileSync('git',['show',':'+SOURCE],{cwd:ROOT,maxBuffer:2*1024*1024});
 const contract=JSON.parse(bytes.toString('utf8'));
 const result=planStartupPressReview({contract});
 if(result.state!=='STARTUP_SOURCE_REVIEW_READY_NOT_NATIVE')return result;
 const head=execFileSync('git',['rev-parse','HEAD'],{cwd:ROOT,encoding:'utf8'}).trim();
 return {...result,source_contract:{git_path:SOURCE,
   sha256:createHash('sha256').update(bytes).digest('hex'),
   git_head:head,indexed_git_blob_verified:true},
   evidence_class:'AUTHENTICATED_LOCAL_GIT_INDEX_REVIEW_NOT_NATIVE_ISSUER'};
}
if(process.argv[1]&&/(?:^|[\\/])cgxStartupPressReview\.mjs$/i.test(process.argv[1])){
 if(process.argv.length!==3||process.argv[2]!=='--review'){
  process.stderr.write('SOURCE_ONLY_USE_--review\n');process.exitCode=2;
 }else{
  const receipt=buildHostStartupPressReceipt();
  process.stdout.write(JSON.stringify(receipt,null,2)+'\n');
  if(receipt.state!=='STARTUP_SOURCE_REVIEW_READY_NOT_NATIVE')process.exitCode=2;
 }
}
