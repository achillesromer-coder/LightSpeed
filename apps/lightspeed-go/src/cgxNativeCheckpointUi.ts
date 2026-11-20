import {
  checkpointSelectable,
  revokeCgxCheckpoint,
  writeCgxCheckpoint,
  type CgxDynamicSurface,
} from "./desktopBridge";
import { escapeHtml } from "./neoExchange";

/** The host registry supplies all choices. This is one adjunct to the existing System view. */
export const checkpointUiProjection = (surface: CgxDynamicSurface) => {
  const choices = checkpointSelectable(surface);
  return {
    revision: surface.source_view_sha256,
    roles: choices.roles.map(({ id, floor }) => ({ id, label: floor })),
    routes: choices.routes.map(({ id }) => ({ id, label: id })),
    canStage: choices.roles.length > 0 && choices.routes.length > 0 &&
      surface.native_mint_authorized === false &&
      surface.execution_authorized === false,
    permission: "owner_session_private_review_only",
  };
};

export function mountCgxNativeCheckpointUi(
  host: HTMLElement,
  surface: CgxDynamicSurface,
  ownerSession: string,
  isCurrentOwnerSession: () => boolean,
): void {
  const catalogue = checkpointUiProjection(surface);
  const roleOptions = catalogue.roles.map((role) =>
    '<option value="' + escapeHtml(role.id) + '">' + escapeHtml(role.label) + '</option>',
  ).join("");
  const routeOptions = catalogue.routes.map((route) =>
    '<option value="' + escapeHtml(route.id) + '">' + escapeHtml(route.label) + '</option>',
  ).join("");
  const holder = document.createElement("details");
  holder.innerHTML =
    '<summary>Canonical Cognigrex persistence · review checkpoint</summary>' +
    '<p class="muted">Task-bound metadata only in the existing FileSpace/DataSpace operational ledger. ' +
    'This does not dispatch an agent, train weights, mint CGX, or grant source access.</p>' +
    '<form class="form-grid" id="cgx-native-checkpoint-form">' +
    '<label class="field"><span>Existing task ID</span><input name="task" required maxlength="128" pattern="[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}" placeholder="task-001"></label>' +
    '<label class="field"><span>Run ID</span><input name="run" required maxlength="128" pattern="[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}" placeholder="run-001"></label>' +
    '<label class="field"><span>Specialist lane</span><select name="role" required>' + roleOptions + '</select></label>' +
    '<label class="field"><span>Read-only capability</span><select name="route" required>' + routeOptions + '</select></label>' +
    '<label class="field"><span>CPU planning ceiling</span><input name="cpu" type="number" min="1" max="4" value="1" required></label>' +
    '<label class="field"><span>Memory planning ceiling (MiB)</span><input name="memory" type="number" min="64" max="1024" value="128" required></label>' +
    '<label class="field"><span>Maximum jobs</span><input name="jobs" type="number" min="1" max="16" value="2" required></label>' +
    '<label class="field"><span>TTL (seconds)</span><input name="ttl" type="number" min="60" max="3600" value="900" required></label>' +
    '<button type="submit"' + (catalogue.canStage ? "" : " disabled") + '>Record private checkpoint</button>' +
    '<button type="button" id="cgx-native-revoke" hidden>Revoke checkpoint</button>' +
    '</form><p id="cgx-native-result" class="muted" role="status">No checkpoint recorded.</p>';
  host.appendChild(holder);
  const form = holder.querySelector<HTMLFormElement>("form");
  const status = holder.querySelector<HTMLElement>("#cgx-native-result");
  const revokeButton = holder.querySelector<HTMLButtonElement>("#cgx-native-revoke");
  if (!form || !status || !revokeButton) return;
  const field = (name: string) => form.elements.namedItem(name) as HTMLInputElement | HTMLSelectElement | null;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!isCurrentOwnerSession() || !catalogue.canStage) return;
    const task = field("task")?.value.trim() || "";
    const run = field("run")?.value.trim() || "";
    const role = field("role")?.value || "";
    const route = field("route")?.value || "";
    if (!task || !run || !role || !route) return;
    status.textContent = "Validating owner authority and canonical source revision…";
    try {
      const receipt = await writeCgxCheckpoint({
        selector: "LightSpeed",
        task_id: task,
        run_id: run,
        expected_view_sha256: catalogue.revision,
        role_ids: [role],
        route_ids: [route],
        cpu_threads: Number(field("cpu")?.value),
        memory_mib: Number(field("memory")?.value),
        max_jobs: Number(field("jobs")?.value),
        ttl_seconds: Number(field("ttl")?.value),
      }, ownerSession);
      if (!isCurrentOwnerSession() || !status.isConnected) return;
      status.textContent = receipt.state + " · readback " +
        String(receipt.exact_readback_verified) + " · expires " +
        receipt.expires_utc + " · execution/mint held";
      revokeButton.hidden = receipt.state !== "REVIEW_ONLY";
      revokeButton.onclick = async () => {
        if (!isCurrentOwnerSession()) return;
        status.textContent = "Submitting bounded revocation…";
        try {
          const revoked = await revokeCgxCheckpoint(
            task, run, receipt.candidate_sha256, ownerSession,
          );
          if (!isCurrentOwnerSession() || !status.isConnected) return;
          status.textContent = revoked.state + " · readback " +
            String(revoked.exact_readback_verified);
          revokeButton.hidden = true;
        } catch (error) {
          if (isCurrentOwnerSession() && status.isConnected) {
            status.textContent = error instanceof Error ? error.message : "Revocation held";
          }
        }
      };
    } catch (error) {
      if (isCurrentOwnerSession() && status.isConnected) {
        status.textContent = error instanceof Error ? error.message :
          "Native persistence deployment or authority is held";
      }
    }
  });
}
