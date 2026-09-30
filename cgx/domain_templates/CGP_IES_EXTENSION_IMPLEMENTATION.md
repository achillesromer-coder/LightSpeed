# CGP-IES shared extension — functional implementation

**Owner path target:** `Cognigrex.cgx:/extensions/cgp-ies`  
**Child rule:** reference/bind; do not copy the policy body into each agent or child domain.  
**Status:** source blueprint and resolver implemented in LightSpeed; parent-carrier hydration remains a separate Recovery-carrier mutation/verification step.

## Runtime contract

The resolver returns one mode:

`OFF < OBSERVE < ADVISE < GATE < ENFORCE_SAFETY`

`ENFORCE_SAFETY` is deliberately narrow: it can only enforce already-declared safety, authority, replication, containment, stop and life/ecology-preservation constraints. It is not permission for a model to become a sovereign moral optimiser.

## Child binding

Generated child carriers receive `extensions/bindings.json` containing the parent source path, default mode and fail-closed behaviour. The policy payload remains parent-owned.

## Fail behaviour

- low-consequence read/analysis with missing extension source: continue with an explicit unavailable receipt;
- consequential execution with missing or integrity-mismatched source: `HOLD`;
- unknown affected party: preserve uncertainty and favour reversibility; do not convert uncertainty into automatic prohibition;
- conflicting lenses: preserve dissent and compare admissible options rather than collapsing to a single moral score.

## Verification

```bash
python scripts/validate_cgp_ies_extension.py
python scripts/validate_cgx_domain_templates.py
python scripts/resolve_cgx_extensions.py --domain romer --execution-depth execute --cascade-class C3 --tags resource-extraction,autonomous-fleet
```

The `.cgx` domain-child builder consumes the binding after the template gate passes.
