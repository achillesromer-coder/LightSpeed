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

## Install across desktop/Codex chats

The repository exposes a marketplace at:

`.agents/plugins/marketplace.json`

Once this work is on `main`, register it with:

```powershell
codex plugin marketplace add achillesromer-coder/LightSpeed --ref main
codex plugin marketplace upgrade
codex plugin marketplace list
```

Or run:

```powershell
powershell -ExecutionPolicy Bypass -File tools/install_cgx_chatgpt_plugins.ps1
```

Then restart the ChatGPT desktop app. Open **Plugins**, choose
**Cognigrex / LightSpeed**, verify the nine selector plugins are installed and
enabled, and start a new chat before first use.

The marketplace declares the suite `INSTALLED_BY_DEFAULT`; the client remains
the authority for local installation/enabled state.

## Invocation examples

```
@Achilles audit this result against current authority and evidence.
@Neo decompose and route this task using minimum sufficient work.
@Raphael verify the physics and reuse existing tests where valid.
@Römer-Grex resolve the current Mark V context.
@Eco-Grex assess this infrastructure component through the current ecology domain.
@LightSpeed execute only the unresolved deterministic work and return a receipt.
```

## Runtime boundary

Version 0.2.0 is intentionally **skills-only**. It can orchestrate currently
available ChatGPT/Codex tools and connected plugins through its workflow skills,
but it does not fabricate a local MCP endpoint. Heavy/local LS execution remains
behind the existing LightSpeed runtime until a verified typed transport is
registered.

That later transport must wrap existing LightSpeed functions and receipts; it
must not expose an arbitrary shell executor or create a second runtime.
