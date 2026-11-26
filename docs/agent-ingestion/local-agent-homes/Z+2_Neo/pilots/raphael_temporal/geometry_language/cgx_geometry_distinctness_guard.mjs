/** Evidence boundary for Raphael T173 research roles: pure, review-only. */
export class GeometryEvidenceError extends Error {}
const isOverlay = (e) => e.class === 'FUNCTIONAL_OVERLAY_NOT_DISTINCT_SOLID';
const isAlias = (e) => e.class === 'PROVISIONAL_ALIAS_NOT_DISTINCT_SOLID';
export function classifyGeometryClaim(slot, registry, claim) {
  if (typeof slot !== 'string' || !/^T173:\d{3}$/.test(slot)) throw new GeometryEvidenceError('Malformed geometry role');
  const index = Number(slot.slice(5));
  if (index === 174) throw new GeometryEvidenceError('T173:174 is a null sentinel');
  if (!Array.isArray(registry?.slots) || registry.slots.length !== 173 || !(index>=1 && index<=173)) throw new GeometryEvidenceError('Invalid or missing role registry');
  const e = registry.slots[index-1];
  if (e?.slot !== slot || e.native_admitted !== false) throw new GeometryEvidenceError('Role identity/authority mismatch');
  if (!['boundary_faces', 'functional_channels', 'distinct_solid', 'reference_mesh'].includes(claim)) throw new GeometryEvidenceError('Unrecognised claim type');
  if (isOverlay(e)) {
    return {schema:'cgx.geometry.claim/0.1',slot,claim,base_mesh_ref:e.mesh_ref,verdict:claim==='functional_channels'?'SOURCE_ROLE_LABEL_ONLY':'NOT_ESTABLISHED',
      assertion_allowed:false,requires:['original_face_cycles','intrinsic_chirality_proof','independent_equivalence_test'],native_admitted:false};
  }
  if (isAlias(e)) {
    return {schema:'cgx.geometry.claim/0.1',slot,claim,base_mesh_ref:e.mesh_ref,verdict:'J72_REFERENCE_ALIAS_PENDING_DISTINCTNESS',
      assertion_allowed:false,requires:['independent_noncongruent_mesh','explicit_cap_reattachment','source_rights'],native_admitted:false};
  }
  return {schema:'cgx.geometry.claim/0.1',slot,claim,base_mesh_ref:e.mesh_ref,verdict:'UNQUALIFIED_NO_AUTOMATIC_PROMOTION',assertion_allowed:false,native_admitted:false};
}
export function planCapGyration(slot,angleDegrees,registry) {
  const verdict=classifyGeometryClaim(slot,registry,'distinct_solid');
  if (!isAlias(registry.slots[136]) || slot!=='T173:137') throw new GeometryEvidenceError('Cap plan only for held role T173:137');
  if (angleDegrees!==36 && angleDegrees!==-36) throw new GeometryEvidenceError('Only history-grounded +/-36 degree candidate');
  return {schema:'cgx.geometry.ast/0.1',kind:'research_cap_gyration_plan',slot,base_mesh_ref:verdict.base_mesh_ref,
    transform:{axis:'DERIVE_FROM_VERIFIED_CAP',angle_degrees:angleDegrees,rim:'REATTACH_BY_BIJECTIVE_DECAGON_PERMUTATION'},
    source_rights_required:true,exact_geometry_source_required:true,distinctness_proven:false,
    status:'DRY_RUN_REVIEW_ONLY',effects_performed:false,authority_transfer:false};
}
