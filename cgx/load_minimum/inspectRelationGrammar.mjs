// Source-only cross-family relation grammar preflight. No Object_ID mint, DBR write or owner approval.
export function inspectRelationGrammar(domainRegistry, sharedQualifier) {
  if (!domainRegistry || typeof domainRegistry !== 'object' || Array.isArray(domainRegistry)) {
    throw new TypeError('INVALID_DOMAIN_RELATION_REGISTRY');
  }
  // EMASSC/LS declares three typed groups at the root rather than under "families".
  // Do not interpret host_local_noncanonical entries as shared relation types.
  const groups = domainRegistry.schema === 'CGX-EMASSC-LS-RELATION-REGISTRY/0.2'
    ? Object.fromEntries(['emassc', 'lightspeed', 'bridge'].map(key => [key, domainRegistry[key]]))
    : domainRegistry.families;
  if (!groups || typeof groups !== 'object' || Array.isArray(groups)) {
    throw new TypeError('INVALID_DOMAIN_RELATION_REGISTRY');
  }
  if (!sharedQualifier || typeof sharedQualifier.schema !== 'string') {
    throw new TypeError('INVALID_SHARED_RELATION_CONTRACT');
  }
  const occurrences = new Map();
  for (const [family, entries] of Object.entries(groups)) {
    if (!Array.isArray(entries)) throw new TypeError('INVALID_RELATION_FAMILY');
    for (const entry of entries) {
      if (!entry || typeof entry.id !== 'string' || !/^[A-Z][A-Z0-9_]*$/.test(entry.id)) {
        throw new TypeError('INVALID_RELATION_TYPE');
      }
      const group = occurrences.get(entry.id) ?? [];
      group.push({family, source_relation_id: entry.id});
      occurrences.set(entry.id, group);
    }
  }
  // Shared vocabulary reuse is a crosswalk candidate, never an identity merge.
  // A shared type may intentionally be reused with domain-specific qualifiers;
  // owner/rights/source/version and authenticated DBR proof are outside this preflight.
  const sharedTypes = sharedQualifier.shared_relation_types;
  if (!sharedTypes || typeof sharedTypes !== 'object' || Array.isArray(sharedTypes)) {
    throw new TypeError('INVALID_SHARED_RELATION_TYPES');
  }
  const sharedOccurrences = new Map();
  for (const [sharedFamily, entries] of Object.entries(sharedTypes)) {
    if (!Array.isArray(entries)) throw new TypeError('INVALID_SHARED_RELATION_FAMILY');
    for (const entry of entries) {
      if (!entry || typeof entry.id !== 'string' || !/^[A-Z][A-Z0-9_]*$/.test(entry.id)) {
        throw new TypeError('INVALID_SHARED_RELATION_TYPE');
      }
      const families = sharedOccurrences.get(entry.id) ?? [];
      families.push(sharedFamily);
      sharedOccurrences.set(entry.id, families);
    }
  }
  const crosswalk_candidates = [];
  for (const [id, declarations] of occurrences) {
    for (const sharedFamily of sharedOccurrences.get(id) ?? []) {
      for (const declaration of declarations) {
        crosswalk_candidates.push({
          relation_id: id,
          domain_family: declaration.family,
          shared_family: sharedFamily,
          classification: 'UNRESOLVED_SHARED_TYPE_REUSE',
          qualified_object_id: null,
          owner_qualified: false,
          native_admitted: false
        });
      }
    }
  }
  const issues = [];
  if (domainRegistry.extends !== sharedQualifier.schema) {
    issues.push({
      code: 'RELATION_SCHEMA_COMPATIBILITY_HOLD',
      declared_extends: domainRegistry.extends ?? null,
      available_contract: sharedQualifier.schema
    });
  }
  for (const [id, declarations] of occurrences) {
    if (declarations.length > 1) {
      issues.push({
        code: 'RELATION_TYPE_NAMESPACE_AMBIGUITY',
        relation_id: id,
        source_declarations: declarations
      });
    }
  }
  return {
    stage: 'SOURCE_REVIEW_ONLY',
    // Unresolved lexical reuse is a separate owner/identity gate even if both schemas parse cleanly.
    status: (issues.length || crosswalk_candidates.length) ? 'HOLD' : 'SOURCE_CONTRACT_CHECK_ONLY',
    unresolved_crosswalk_count: crosswalk_candidates.length,
    issues,
    crosswalk_candidates,
    relation_declarations: [...occurrences.values()].reduce((n, group) => n + group.length, 0),
    distinct_lexical_ids: occurrences.size,
    qualified_object_id: null,
    native_admitted: false,
    dbr_readback_verified: false,
    authority_transferred: false
  };
}
