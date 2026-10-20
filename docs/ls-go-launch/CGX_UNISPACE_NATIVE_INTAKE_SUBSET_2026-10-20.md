# CGX / UniSpace — Native intake projection source convergence
**20 October 2026 · Stacked draft source candidate · no runtime deployment or canon promotion**

## Integration history and scope
- **Stack:** #182 (source families) → #184 (Object_ID identity and library coverage) → #185 (selective R0 byte carrier) → this source-only intake stage (proposed next #186).
- **Source owner:** existing draft PR #173, `cgx/dataspace-rolling-observer-facet-20261012`, head `03448282109278aef1f2745086b5176cdb615159`.
- **Carried EXACT upstream source:** `cgx/domain_templates/unispace_intake_mapping_contract.json`, `desktop/LightSpeed_Runtime/lightspeed_runtime/cgx_intake_projection.py`, `desktop/LightSpeed_Runtime/tests/test_cgx_intake_projection.py`. Their Git blobs are in `cgx/review/native_intake_subset_fold_20261020.json`.
- **Native manifest compatibility:** retain all 733 existing `desktop/source-manifest.json` records (including the independently accepted #177 resolver digest), append only those 2 newly staged PR #173 desktop files, and verify manifest SHA/byte parity. Do not copy the entire divergent PR #173 desktop manifest.
- **Does not fold:** rolling Psi/N-node executor modifications, `node_exchange.py` runtime extension, `ls_go_job_consumer.py`, native source-intake executor, MCP tunnel, local floor/Ollama resource execution, restricted Alexandria public skeleton, job queue or new scheduled agent. Those require separate source conflict/test and owner proof gates.

## What this code actually implements
1. `project_intake(bytes, source_metadata)` validates bounded local exact SHA-256 source bytes with declared provider/revision/owner/licence/visibility, and recognises bounded JSON and CSV structure only.
2. Source owner supplied typed attributes remain explicitly `SOURCE_ASSERTION_UNVERIFIED`; file names do not determine semantic owner. The source record does **not** allocate Object_ID or promote DBR.
3. `project_native_envelope_candidate` cross-checks the *existing native source-intake envelope* against original local bytes. No local byte match attests cloud provider ACL/revision.
4. `plan_native_r1_review` requests a registered, type-exact adapter and cannot self-certify R1 fidelity; specialised types return HOLD where appropriate.
5. `plan_two_node_exchange` invokes the already present `lightspeed_runtime.node_exchange.build_transfer_envelope_from_manifest` and returns `HOLD_AUTHENTICATED_PEER_ADMISSION`. Strings like `authenticated:true` in caller input are **not** actual peer admission.
6. `project_public_preview` allows descriptive text only when source metadata permits; it never publishes source bytes, hashes, private source locator or user data.

## Tested cross-family demonstration
A synthetic CSV fixture flows from existing native `source_intake.build_source_envelope` → #173 intake candidate → existing #185 candidate byte-carrier R0 reconstruction. It returns exact original SHA-256 and keeps public, permission, peer and DBR claims FALSE/HOLD. No network traffic, source owner authentication or external cloud readback occurred.

## Integration against existing capability catalogue
- Existing 33 file-type registry, 19 first-file mappings and 34 semantic lenses are referenced by #184's read-only coverage, not duplicated by the intake map.
- `cgx_intake_projection` recognises a bounded subset only; do not market it as complete native 33-type conversion.
- R0 reconstruction proof is distinct from R1 reversible semantic fidelity and R2/R3 interpretations.
- Existing #180 keyed package grant/rights review stays separate from local source envelope; a shareable digest is not a licence or authenticated grant.
- #181 physical composition remains a source/geometry planning engine, not automatic qualified physical product.

## Owner and release gates
#158 private/public static asset boundary, #161 independently authenticated FileSpace/DataSpace two-node acceptance, signed source/State_Root/DBR receipts, CAS/replay/leases, provider revision rights, resource-safe host/runtime installation and physical qualification remain OPEN. Tests are offline/synthetic only. No direct publishing, live peer, host C:/D:, Drive canonical write, private source replication, executable arbitrary intake or funding action.

## Next safe fold
Review #173's *rolling observer / scatter-gather* contract and tests as a **separate, opt-in read-only facet**, evaluate conflicts with existing node_exchange and owner semantics, and only then stage minimal independently proven code. The broader node-exchange replacement, native job consumers and web/MCP tunnel must not be brought over blindly.
