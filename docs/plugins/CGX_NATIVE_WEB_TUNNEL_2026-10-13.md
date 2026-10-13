# CGX native web handshake — private stdio transport

This is an **additive exposure profile** for the already installed/checked-in
`lightspeed-cgx-tools` stdio MCP tool server. It is **not** a second runtime,
FileSpace authority, Grex, automation, public listener, third-party remote desktop,
or permission to run arbitrary shell or commit repository changes.

## Owner-approved access path

`ChatGPT web / LS GO operator -> authenticated MCP app -> OpenAI Secure MCP Tunnel -> BouwerBase existing stdio MCP server -> existing CGX/LightSpeed bridge`.

OpenAI's Secure MCP Tunnel supports a private stdio command and outbound-only
HTTPS. It needs a tunnel ID from Platform, a runtime credential stored outside
source control, a permitted ChatGPT workspace/app connection and a locally
running `tunnel-client`. This does not expose port 8765, 4173, file contents,
private catalogues or physical devices on the internet.

The existing MCP server offers a deliberately separate exposure profile:

- Normal local `node server.mjs`: existing local MCP tool surface, unchanged.
- Set `CGX_MCP_EXPOSURE=web-readonly` before starting `node server.mjs`:
  only `cgx_web_handshake` is advertised; the other registered tools do not
  appear in `tools/list`. The handshake probes only the public-safe local
  CGX bootstrap candidate, returns a fixed redacted schema, and never grants
  source roots, credentials, receipts, device identity, lease, Git writes or
  consumer/job execution.
- `CGX_MCP_EXPOSURE` is a startup mode, NOT an authentication switch or a
  replacement for owner session, scopes, source/installed parity or device keys.

### Existing checkout test

From the authorised checkout, after verifying it is the intended reviewed
branch, install dependencies from the existing lockfile and run:

```powershell
Set-Location desktop/LightSpeed_Runtime/mcp/cgx_tools
npm ci --ignore-scripts
npm run test:web
```

Do not treat source CI as installed-host or tunnel proof.

### Owner-run private connection

1. On BouwerBase, identify the installed runtime, trusted worktree, Node binary
   and exact `server.mjs` SHA; do not open protected Documents or run an
   unknown online package.
2. Provision an official OpenAI Secure MCP Tunnel with the appropriate workspace,
   Platform permissions and credential injection in a secure local secret store.
   Keep keys out of Git, launch arguments, receipts, chats and logs.
3. Configure the tunnel's **stdio** target to execute
   `node <verified-absolute-tools/run_cgx_web_readonly_mcp.mjs>`. This exact
   wrapper forces `CGX_MCP_EXPOSURE=web-readonly` before loading the existing
   `server.mjs`, even if the caller's environment requests `local`.
   **Do not** point the tunnel directly at `server.mjs` (which retains the
   original local-tools default for already installed Codex sessions).
   The `tunnel-client` profile should never invoke a general shell on request;
   it simply launches this reviewed MCP wrapper.
4. Run `tunnel-client doctor` using its actual configured profile; run and
   confirm tunnel-client in the host's existing managed service environment.
   Do **not** register a second worker, open firewall ports or start a parallel
   LightSpeed bridge on 8765.
5. In ChatGPT **web**, create/connect the MCP app using the selected private
   tunnel. Verify **exactly one** `cgx_web_handshake` tool is exposed, and
   that its response keeps
   `owner_session_verified=false`,
   `consumer_receipt_verified=false`,
   `canonical_write_authorized=false`,
   `git_commit_authorized=false`.
6. Test invalid/expired session, disconnected host, tampered advertisement,
   tool-list mutation, replay, revoked pairing and protected-source isolation
   before considering expanded private tools.

Official tunnel-client quickstart and access requirements:
https://developers.openai.com/api/docs/guides/secure-mcp-tunnels

## BouwerBase guided PowerShell setup

Download the trusted Windows `tunnel-client` binary using the link in
[OpenAI Platform tunnel settings](https://platform.openai.com/settings/organization/tunnels)
or the official [openai/tunnel-client latest release](https://github.com/openai/tunnel-client/releases/latest).
Do not download an unverified binary from a chat, mirrored website or a random
third-party package. Make `tunnel-client` available on PATH or pass
`-TunnelClientPath <reviewed absolute executable path>`.

Keep the checked-out repository in an **existing dedicated review worktree**;
do not run this against the live `D:\LightSpeed\App` tree or recreate
`Cognigrex.cgx`. Fetch PR #173 into that worktree through the owner's
existing GitHub Desktop/Git workflow. Ensure its branch has the exact reviewed
and CI-approved commit; a later concurrent PR update requires fresh review
and a new `-ApprovedHeadSha` value.

Run in PowerShell from the reviewed **repository root**:

```powershell
# Read-only; no tunnel config, process start, or npm install.
.\tools\setup_cgx_web_tunnel.ps1

# After creating a tunnel in Platform and copying its REAL tunnel ID:
$approved = "<paste exact reviewed PR173 HEAD SHA, 40 hex digits>"
$tunnelId = "<paste actual tunnel_... ID>"
.\tools\setup_cgx_web_tunnel.ps1 -Configure -TunnelId $tunnelId -ApprovedHeadSha $approved

# This checks the local read-only tool boundary again and runs only tunnel-client.
.\tools\setup_cgx_web_tunnel.ps1 -Start -ApprovedHeadSha $approved
```

The setup validates canonical Git origin/clean branch/exact SHA, uses the
repository's existing `package-lock.json` with `npm ci --ignore-scripts`,
runs the web-only MCP negative-privilege test, and calls the official
`tunnel-client init --sample sample_mcp_stdio_local ... --mcp-command`
and `doctor` commands. It does not install an OS service, copy keys to Git,
start the LightSpeed bridge/Smith consumer, or grant file/commit permission.
Only `-Start` invokes the long-running tunnel process. The runtime API key
is requested with hidden input if `CONTROL_PLANE_API_KEY` was not already
provided in the current PowerShell process.

In ChatGPT web select **Plugins → + → Add custom MCP server → Tunnel**,
choose the tunnel, complete the connection review and create the plugin.
This needs an approved ChatGPT workspace and the tunnel's Platform
**Tunnels Read + Use** access. The explicit expected MCP tool list is exactly
`cgx_web_handshake`. Calling it must show no authenticated owner/Smith/commit
claim. A healthy bootstrap candidate is only a diagnostic.

If any test fails, keep the existing local service running without changes,
inspect the error, and do not reconnect through an unreviewed HTTP or shell
fallback. The private tunnel can be stopped with Ctrl+C. To remove access,
disconnect the custom MCP plugin and revoke the tunnel/key through Platform
settings. The setup does not touch Desktop Commander.

## Native write/commit gateway — outstanding owner gate

The target is a **separate tool action** on this same MCP server and same local
Smith/Neo queue, not arbitrary remote shell: `cgx_request_scoped_commit` may
eventually accept a reviewed `source_ref`, `expected_base_sha`, `branch`,
`allowed_paths`, `diff_hash`, `owner_decision_ref` and `lease_id`.
The server must validate an actual owner-authenticated identity and
single-use scoped lease **locally**, refuse protected paths and direct main
push, store approved work in the existing worktree/DB queue, and return a
signed exact-result DBR with Git branch/commit/remote-readback before it can
claim completion. The browser/client cannot mint or self-approve a lease or
change a source root. The same acceptance holds for LS Mobile and other
registered nodes. **This capability is NOT enabled by the read-only profile.**

Use the existing GitHub provider connector for reviewed cloud source commits
while local admission remains held. Git source/PR history is backup for source,
not for SQLite state, secret keys, original CAD, private corpus or host backup.
Local state is preserved by its existing controlled encrypted/snapshotted
backup/restore policy, with explicit hash receipts.

## Third-party displacement

- **Remote Desktop Commander**: optional recovery/inspection provider, not
  normal transport, identity, scheduler or dependency.
- **Slack**: optional externally requested people/team integration only.
  CGX domain agent coordination uses existing typed messages, task IDs, DBR
  and LS GO review surface; no Slack message is evidence of an executed job.
- **GitHub / Drive**: remain reviewed source/durable evidence providers; use
  adapters and receipts, not a duplicate local Git master or silent file sync.
- **All client surfaces**: ChatGPT web (if custom MCP/tunnel supported by
  account), LS GO, LS Mobile, Desktop, API use one CGX capability/authority
  contract; no interface gains powers from its visual appearance.

## Stop conditions

If a tunnel is inaccessible, connected to the wrong workspace, its tool set
contains any unreviewed local/writer tool, a credential leaks, the local source
does not match reviewed SHA, or the existing consumer lock/queue is stale:
**HOLD**. Do not bypass with a public port, unrestricted file access, arbitrary
shell, second OS user, or alternate provider credential. Native authorization,
lease, receipt and installed proof must be separately demonstrated.
