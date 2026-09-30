# CGP-IES shared extension — functional implementation

**Owner path target:** `Cognigrex.cgx:/extensions/cgp-ies`  
**Child rule:** reference/bind; do not copy the policy body into each agent or child domain.  
**Status:** PRE_CANONICAL functional source + runtime integration; parent Recovery promotion is intentionally held behind owner/governance review.

## Source-owned component set

The parent extension is decomposed so children hydrate only the pieces needed for the current task:

- `custodial_extension_registry.json` — toggle modes, escalation and failure behaviour.
- `cgp_ies_policy_pack.json` — shared custodial principles, lifecycle, contact, succession and protective-perpetuity policy.
- `cgp_ies_terminology_map.json` — neutral inter-special terminology and epistemic vocabulary.
- `cgp_ies_domain_adapter_registry.json` — Romer / Eco / EMASSC / LightSpeed applicability and required checks.
- `cgp_ies_decision_receipt_schema.json` — structured affected-party, agency, representation, ceiling, dissent and inheritance receipt.
- `cgp_ies_fixture_scenarios.json` — regression scenarios.
- `cgp_ies_owner_confirmation_values.json` — unresolved values that cannot become canonical by code generation.
- `cgp_ies_parent_extension_manifest.json` — exact S91-seeded parent candidate install contract.

## Runtime contract

The resolver returns one mode:

`OFF < OBSERVE < ADVISE < GATE < ENFORCE_SAFETY`

`ENFORCE_SAFETY` is deliberately narrow: it can only enforce already-declared safety, authority, replication, containment, stop and life/ecology-preservation constraints. It is not permission for a model to become a sovereign moral optimiser.

### Source-driven rule

Runtime code MUST NOT duplicate the policy's hard-predicate list. `resolve_cgx_extensions.py` reads the parent policy and domain adapter; `cgx_custodial_preflight.py` consumes that resolution. If the source contract is absent at a consequential gate, the action holds rather than silently falling back to hard-coded doctrine.

## Child binding

Generated child carriers receive `extensions/bindings.json` containing:

- parent source path;
- default and allowed modes;
- terminology reference;
- domain-adapter reference;
- decision-receipt-schema reference;
- policy reference;
- failure behaviour;
- source-integrity requirement.

The policy payload remains parent-owned. Nested children may inherit an applicable mode, but cannot weaken a required `GATE` or `ENFORCE_SAFETY` escalation.

## Domain adapters

- **Romer.cgx:** growth, resource extraction, missions, autonomous fleets, planetary defence, trajectories, pristine worlds, habitat translocation, hazardous material.
- **Eco.cgx:** ecological intervention, life impact, biosecurity, communication, translocation, welfare, restoration and unknown life.
- **EMASSC.cgx:** evidence, Raphael/model boundary, standards, biosignatures/technosignatures, scientific and public claims.
- **LS.cgx:** execution leases, replication, stop/containment, life support, hazard control, communication/civilisation loss, successor restart and possible artificial moral patients.

## Fail behaviour

- low-consequence read/analysis with missing extension source: continue with an explicit unavailable receipt;
- consequential execution with missing or integrity-mismatched source: `HOLD`;
- unknown affected party: preserve uncertainty and favour reversibility; do not convert uncertainty into automatic prohibition;
- unresolved representation: keep `UNREPRESENTED/UNKNOWN`; do not infer mandate from competence or ownership;
- conflicting lenses: preserve dissent and compare admissible options rather than collapsing to a single moral score;
- successor context unknown: hold productive restart while independently justified protective MVSL may remain.

## Parent candidate

`scripts/build_cgp_ies_parent_candidate.py` accepts only the exact promoted S91/v1.61 Recovery seed. It:

1. verifies exact SHA-256 and S91 roots;
2. verifies the seed with the CGX kernel;
3. installs the parent-owned extension components;
4. advances state through a DBR-tracked kernel mutation;
5. packs a NEW candidate carrier;
6. reopens and verifies it;
7. returns a candidate receipt.

It refuses in-place Recovery overwrite and labels the result `PRE_CANONICAL`. It does **not** promote the result to Recovery.

## Verification

```bash
python scripts/validate_cgp_ies_extension.py
python scripts/validate_cgx_domain_templates.py
python -m py_compile scripts/build_cgp_ies_parent_candidate.py
python scripts/resolve_cgx_extensions.py --domain romer --execution-depth execute --cascade-class C3 --tags resource-extraction,autonomous-fleet
python scripts/resolve_cgx_extensions.py --domain emassc --execution-depth inspect --cascade-class C1 --tags technosignature,external-contact
```

The parent candidate is built only after owner values are reviewed. Child regeneration follows only after a candidate is independently audited and explicitly promoted as the next Recovery authority.

## Authority boundary

This extension is a reasoning/safety/governance capability. Loading it cannot create ownership, representation, certification, moral sovereignty, risk acceptance or execution authority. Those remain explicit upstream/downstream authorities and leases.
