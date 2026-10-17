# Existing LS GO Site and GPT tunnel boundaries

The shipped mobile carrier now selects `existing_owner_private_ls_go_site`,
`existing_site_same_origin` and `existing_site_owner_auth`. The phone opens
`https://lightspeed-go.nathaniel-b.chatgpt.site/` and uses the existing owner
ChatGPT sign-in. No private host origin is required for that Site route.
The Android source offers that fixed Site URL directly; it never imports a URL,
credential or authority from an untrusted carrier. Legacy direct-host carriers
remain recognizable as a separate complete profile; mixed profiles are rejected.

Local GPT setup is source-verified at PR #173 commit
`91dd835850033952dda38c78fe2e701828d4a241`, superseding the earlier setup
checkpoint below. Its helper requires a real tunnel ID on configure and start,
pins the reviewed read-only MCP entrypoint on each invocation and guards its own
profile starts with a Windows mutex. A real tunnel ID, protected runtime key and
authenticated ChatGPT-web call are still required for connection acceptance.

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
