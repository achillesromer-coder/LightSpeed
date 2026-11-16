# Eco.cgx spatial-coordinate review — 2026-11-07

Status: SOURCE-ONLY REVIEW; no native admission, public release or ecological observation claim.

Source: `cgx/domain_templates/eco_digital_mint_boundary.mjs` in draft PR #207, head `926496af0c3829a576c3d346b2a26a44578e9af0` at inspection. Its `spatialText` heuristic detects decimal pairs, WKT POINT and coordinate query keys but has no explicit degrees/minutes/seconds (DMS) textual pattern.

Bounded negative-test proposal: pass a synthetic `EcoObservation` record containing a nested string such as `27°28'12"S 153°01'36"E`, with otherwise source-scoped non-observed fixture fields, to `reviewEcoObservationShowcase`. Expected privacy guard: `RAW_SPATIAL_COORDINATES_NOT_ACCEPTED_IN_SOURCE_ONLY_BRIDGE` or a conservative review-limit flag. No actual specimen or site coordinates are included here. Test has NOT been executed in this note.

Risk: a DMS coordinate string may evade the current heuristic. This is a suspected false negative, not proof of exploitable disclosure or a passed test. Keep public export prohibited independently of heuristic result. Next code change, if reproduced: add bounded DMS recognition in the existing module and a synthetic regression fixture in its existing test, then run Node CI and read back exact blob/commit. Do not treat a clean heuristic as rights/ACL approval.

Owner: Athene / Eco.cgx. Parent Cognigrex.cgx; #158, #161 and #209 HOLD. No original Drive workbook, wildlife record, private geolocation, licence or measured ecological outcome is copied into this note.
