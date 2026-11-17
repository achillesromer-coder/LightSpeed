# CGX family — per-occurrence content permission correction

**Release status:** SOURCE-REVIEW ONLY. Not a native authority, a signature, a model update, or a machine deployment.

## Defect and correction

Previously, two different specialist source occurrences could share a SHA-256 blob and its lexical index. A hash-only (`--metadata-only`) occurrence under another specialist was then sufficient to expose the existing text or restore bytes, even though the second specialist never fully ingested that content.

The existing `source_occurrence` table now carries `content_granted` (Boolean 0/1), representing evidence of the **same specialist** explicitly performing a full source intake under a selected root. Search results, source restoration, and source-grounded learning proposals use role-filtered **full-content** occurrences; hash-only records retain their source identity, length, and review receipt but do not grant a text read. A later authorised full intake of the same source SHA and path upgrades the occurrence without duplicating the blob or losing its previous SHA history.

This is a local review filter only: the process can be launched with any role label and does **not** authenticate the caller. Windows ACLs, owner-selected intake roots, signed issuer and revocation, and full LOAD remain mandatory gates before native or distributed execution.

## Migration and consequences

Existing databases predate this field. Their prior occurrence-level grants cannot be inferred with confidence, so migration adds `content_granted=0`. It **does not delete source bytes, alter content SHA identities or change historical event receipts**. Content remains available only through the existing owner-level review store's explicit export; a specialist must re-ingest its original source with `store_bytes=True` and the approved root to receive a scoped grant. Missing originals must be marked unresolved; do not auto-grant access on migrated records merely because a global blob exists.

Full intake is not the same as public rights clearance, model-weight training, native CGX admission, evidence of a physical phenomenon, or an approved peer transport.

## Acceptance

- Existing source tests `test_family.py`, `test_occurrence_admission.py`, `test_specialist_scope.py`, `test_metadata_atomic.py` continue passing.
- `test_content_grant.py` verifies cross-specialist hash-only denial, byte restoration denial, review-proposal denial, idempotent metadata observations, restart persistence, explicit full rehydration, and fail-closed legacy migration.
- No remote or Windows host was accessed; no canonical branch merge or actual browser/Windows deployment is asserted.

## How to run

```bash
python test_occurrence_admission.py
python test_specialist_scope.py
python test_metadata_atomic.py
python test_content_grant.py
```

This delta is applied to the **existing** `cgx/review/persistence_family` source tree. It neither creates a new canonical family nor replaces the private research archive.
