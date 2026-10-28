// Source-only cross-family relation grammar preflight. No Object_ID mint, DBR write or owner approval.
export function inspectRelationGrammar(domainRegistry, sharedQualifier) {
  if (!domainRegistry || typeof domainRegistry !== 'object' || !domainRegistry.families || typeof domainRegistry.families !== 'object' || Array.isArray(domainRegistry.families)) {
    throw new TypeError('INVALID_DOMAIN_RELATION_REGISTRY');
  }
  if (!sharedQualifier || typeof sharedQualifier.schema !== 'string') {
    throw new TypeError('INVALID_SHARED_RELATION_CONTRACT');
  }
  const occurrences = new Map();
  for (const [family, entries] of Object.entries(domainRegistry.families)) {
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
    status: issues.length ? 'HOLD' : 'SOURCE_CONTRACT_CHECK_ONLY',
    issues,
    relation_declarations: [...occurrences.values()].reduce((n, group) => n + group.length, 0),
    distinct_lexical_ids: occurrences.size,
    qualified_object_id: null,
    native_admitted: false,
    dbr_readback_verified: false,
    authority_transferred: false
  };
}
