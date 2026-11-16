# Athene / Eco.cgx — EcoX Ocean Restoration source qualification (2026-10-31)

**Scope:** source-only, reversible R1 cross-reference; NOT a native CGX Object_ID, DBR admission, executable marine model, physical deployment, or public ecological outcome. Keep the single Cognigrex.cgx parent and the Eco.cgx child. This note is a review record, not authority to integrate into Romer.cgx.

## Public original-source references

- Original project repository: `NCNBOUWER/Raphael`, draft PR [#4](https://github.com/NCNBOUWER/Raphael/pull/4), head `0bf6b0fb9713e6795df5ee71afc636b6de045248` when inspected 2026-10-31; 26 changed files, 28 commits, unmerged. This is the historical EcoX project source, not a CGX native installation.
- [Twin manifest](https://github.com/NCNBOUWER/Raphael/blob/0bf6b0fb9713e6795df5ee71afc636b6de045248/EcoX/Ocean_Restoration/v1_1/manifest/twin_manifest.json), Git blob `c7ff9798f41b4632b7de8ace46462aded50b415c`: historical project ID `ECOX-OPC-0001`, twin ID `ECOX-OPC-DTS-0001`, `integration_state=pending`. These are **source-authored IDs**, not minted CGX Object_IDs.
- [Workbook source map](https://github.com/NCNBOUWER/Raphael/blob/0bf6b0fb9713e6795df5ee71afc636b6de045248/EcoX/Ocean_Restoration/v1_1/data/workbook_sources.md), Git blob `018e11e8c54fce3b107cbe6426c7d7e738d744da`: claims XLSX v1.1 SHA-256 `ae09e73d11e162ae040632d2e5375445df5e44ab83e02eaf13d5fff608fd681f`, 61 sheets, 60 routes. **Source-asserted only**: original XLSX bytes were not fetched/rehashed in this review.
- [Acceptance gate register](https://github.com/NCNBOUWER/Raphael/blob/0bf6b0fb9713e6795df5ee71afc636b6de045248/EcoX/Ocean_Restoration/v1_1/release/acceptance_gates.md), Git blob `3027b013483c530baa1ffa4f548503208ff91ce1`: GATE-002 marked Pass **in the historical register**, GATE-003 open, GATE-004/005/006/009 open, and GATE-012 blocked. No contemporary independent acceptance or DBR receipt was provided.
- [Claim register](https://github.com/NCNBOUWER/Raphael/blob/0bf6b0fb9713e6795df5ee71afc636b6de045248/EcoX/Ocean_Restoration/v1_1/evidence/claims_register.md), Git blob `faef148f5423c69f8b6494a06364aaf97ecfc974`: CLM-008 explicitly treats clusters as simulated; CLM-009 (432 Hz marine safety), CLM-010 (open-water cancellation), CLM-011 (automatic filament suitability), CLM-012 (recovered-plastic reef habitat) are unverified/blocked. These are not ecological observations.

## Private-provider review boundary

A separate authenticated Drive read on 2026-10-31 located the historical project control index and examined its associated canonical-workbook folder. The control index is dated 2026-07-19 and describes a workbook publication pending; the queried folder contained no files. The **private Drive IDs, permissions and raw content are deliberately excluded** from this public review note. The source-age and folder listing do not prove the original binary was never created, nor that no copy exists elsewhere. No original XLSX bytes or hash-equivalence receipt were obtained.

## Candidate FileSpace/semantic mapping and falsifiers

- **R0:** preserve each distinct historical original, public Git manifest and private Drive control index separately. Historical aliases and project IDs are not merged by title.
- **R1:** `Eco.cgx / EcoX-Ocean-Restoration / project-source-candidate`; evidence classes `source_asserted` for workbook/gates and `simulated` for cluster scenarios. No species, specimen, observation, ocean-site geometry, field measurement, licence or stewardship permission is inferred.
- **R2 / geomatrix / Frontier-Resolve:** HOLD. Require authenticated original workbook bytes, matching digest and revision, source licence, validated model/CRS/units/time, ecological safety evidence, and independent review before typed spatial or temporal relationships can be accepted.
- **Negative gates:** missing original XLSX must not pass checksum equivalence; GATE-002 historical pass must not imply GATE-012 acceptance; candidate operators must not be described as partners; illustrative clusters must not become observed plastic distributions; speculative acoustics/materials/reef claims must not become measured impacts.
- **Native/operational/public:** NOT ADMITTED; no DBR/root/host handshake, operator control, publication approval, or field outcome. Issues #158, #161, #209 remain HOLD.

**Next:** obtain the exact original XLSX in an authorised private provider boundary (if present), independently hash and reconcile it with the source-asserted digest; otherwise retain a stable missing-binary blocker. No new root, scheduler, production merge, external outreach or permission change.
