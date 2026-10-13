# Existing LS GO Site and GPT tunnel boundaries

LS GO is the existing owner-private mobile/web control surface. Its same-origin
Site exchange stores bounded host reports and untrusted owner intents in the
existing `sync_cycles` table. It does not start a worker, issue a lease, accept a
local execution command or grant device authority. The local `site_link.py`
adapter performs one outbound status upload and independent hash readback;
it neither persists its Sites credential nor introduces a scheduler.

The separate OpenAI Secure MCP Tunnel uses the PR #173 read-only profile of the
existing LightSpeed MCP server. Its initial exported tool is exactly
`cgx_web_handshake`. It must not consume LS GO intents or dispatch a second
Smith worker. Runtime access uses a dedicated Platform credential, distinct
from Sites service access. The tunnel is not a mobile HTTP origin.

Any future execution must enter the existing owner/session/lease/Smith queue
and preserve command identity, durable acceptance and DBR result readback.
Site transport staging, a host report and an MCP handshake do not satisfy those
execution gates. Git and Drive retain their assigned code and evidence roles.

Observed 2026-10-13: existing LS GO Site v12 deployed privately from source
`00d4541794822a38350bf5da363a6caf59309521`; one real BouwerBase status upload
and independent readback verified. Reports expire after five minutes. No
continuous exchange or phone enrollment is asserted by that one-shot result.
The PR #173 exact commit `7eb4a77649f5f03a374063d49b755ec0ca465a54`
passed local diagnostic and read-only MCP tests. Tunnel provisioning, runtime
credential approval and authenticated remote acceptance remain separate gates.

PrintSpace / Raphael is an independent product/source lane. Its cited source
test results and illustrative geometry do not authorize device actuation,
physical manufacture or either transport's execution capabilities.
