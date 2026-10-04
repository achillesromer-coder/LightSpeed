# Cognigrex / LightSpeed ChatGPT Plugin Suite

This directory is the installable source for nine thin selector plugins:

- Achilles
- Neo
- Athene
- Raphael
- Cognigrex
- Römer-Grex
- Eco-Grex
- EMASSC
- LightSpeed

They are selectors over the existing Cognigrex/LightSpeed architecture. They do
not create a parallel runtime, new truth store, duplicate agent, or replacement
filespace.

## Direct ChatGPT invocation

After installation and enablement, ChatGPT supports selecting an installed
plugin directly with an `@` mention. The canonical chat contract is
`plugins/chat_invocation_contract.json`.

Expected selectors:

```
@Achilles
@Neo
@Athene
@Raphael
@Cognigrex
@Römer-Grex
@Eco-Grex
@EMASSC
@LightSpeed
```

The selector establishes the requested actor/domain/system default, then enters
the shared CGX handshake. It does not transfer domain authority or create a new
agent/runtime.

## Install across ChatGPT Desktop / Codex chats

The repository exposes a marketplace at:

`.agents/plugins/marketplace.json`

Register and provision the personal plugin state with:

```powershell
powershell -ExecutionPolicy Bypass -File tools/install_cgx_chatgpt_plugins.ps1
```

The bootstrap:

1. registers `achillesromer-coder/LightSpeed` as the marketplace source pinned
   to `main`;
2. refreshes the marketplace;
3. enables all nine `plugin@cognigrex-lightspeed` IDs in
   `~/.codex/config.toml`; and
4. lists the resolved marketplace for verification.

The repository also carries `.codex/config.toml` so trusted LightSpeed project
sessions use the same nine selectors.

Restart ChatGPT Desktop after provisioning, then start a new chat before first
use. Open **Plugins > Personal > Cognigrex / LightSpeed** if you need to inspect
the installed state.

The marketplace declares the suite `INSTALLED_BY_DEFAULT`; the local client
remains the authority for installed/enabled state. Availability on web/mobile
can differ from Desktop for local/private plugins and any local execution
capability remains machine-bound.

## Invocation examples

```
@Achilles audit this result against current authority and evidence.
@Neo decompose and route this task using minimum sufficient work.
@Raphael verify the physics and reuse existing tests where valid.
@Römer-Grex /twin WatchTower
@Cognigrex /object M1 Elevated Bypass
@Eco-Grex /object Bio Blocks
@Eco-Grex assess this infrastructure component through the current ecology domain.
@LightSpeed execute only the unresolved deterministic work and return a receipt.
```

## Runtime boundary

Version 0.3.x uses the same thin selector architecture plus one shared,
validated local `lightspeed-cgx` MCP tool plane. The MCP server wraps existing
LightSpeed runtime functions and receipts; it is not a second runtime or truth
store.

Current typed tools include capability/shortcall resolution, current object
resolution, consequence preflight, cross-analysis planning, receipt access,
bounded local planning/execution, and read-only FreeCAD inspection/BOM
derivation. `cgx_resolve_object` joins the current twin lineage to its owning
CGX child domain, Operations binding, source owner and representation boundary.

The shared tool plane deliberately exposes no arbitrary shell, arbitrary Python,
arbitrary filesystem open, automatic canonical promotion or public publishing.
Heavy/local execution remains separately gated and `cgx_run_local_work`
requires explicit confirmation with `heavy=false`.
