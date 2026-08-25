import type {
  LocalResultOpenResponse,
  LocalResultsResponse,
  ResultReceiptMetadata,
} from "./desktopBridge";
import { escapeHtml } from "./neoExchange";


export type ResultReceiptOpenHandler = (
  resultId: string,
  button: HTMLButtonElement,
) => void | Promise<void>;

const formatBytes = (value: number): string => {
  const bytes = Number(value || 0);
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
};

const displayStatus = (receipt: ResultReceiptMetadata): string => {
  const status = String(receipt.status || "unknown").toLowerCase();
  if (["complete", "completed", "pass", "passed"].includes(status)) return "good";
  if (["blocked", "failed", "error"].includes(status)) return "bad";
  return "warn";
};

export const renderResultReceipts = (
  response: LocalResultsResponse,
  ownerConfirmationConfigured: boolean,
): string => {
  const summary = response.summary;
  const boundary = `<p class="result-receipt-boundary">${escapeHtml(response.boundary)}</p>`;
  const hold = ownerConfirmationConfigured
    ? "Exact receipt content requires the local owner-confirmation token."
    : "Content inspection is held because the local owner-confirmation token is not configured.";
  if (!response.results.length) {
    const message = response.state === "restricted"
      ? "No eligible fixed receipts are visible; invalid receipt objects remain withheld."
      : "No fixed local result receipts have been written yet.";
    return `<p class="muted">${message}</p><p class="result-receipt-auth">${hold}</p>${boundary}`;
  }
  const rows = response.results.map((receipt) => {
    const action = receipt.action_type || "untyped";
    const floor = receipt.target_floor || "floor unknown";
    const completed = receipt.completed_utc || receipt.created_utc || receipt.modified_utc;
    const ids = [
      receipt.task_id == null ? null : `Task ${receipt.task_id}`,
      receipt.job_id == null ? null : `Job ${receipt.job_id}`,
      receipt.command_id || null,
    ].filter(Boolean).join(" · ");
    const disabled = ownerConfirmationConfigured ? "" : " disabled aria-disabled=\"true\"";
    return `
      <article class="task-card result-receipt-card" data-result-state="${displayStatus(receipt)}">
        <div>
          <strong>${escapeHtml(receipt.result_id)}</strong>
          <span>${escapeHtml(receipt.status)} · ${escapeHtml(action)} · ${escapeHtml(floor)}</span>
          <small>${escapeHtml(ids || "No task/job identity")} · ${escapeHtml(completed || "time unavailable")} · ${formatBytes(receipt.size_bytes)}</small>
        </div>
        <div class="task-actions">
          <button type="button" data-result-receipt="${escapeHtml(receipt.result_id)}"${disabled}>Inspect receipt</button>
        </div>
      </article>
    `;
  }).join("");
  const bounded = summary.truncated ? " · bounded index" : "";
  return `
    <div class="result-receipt-summary"><span>${summary.visible_result_count} visible${bounded}</span><span>${summary.invalid_file_count} invalid withheld</span></div>
    <div class="result-receipt-list">${rows}</div>
    <div class="result-receipt-detail" aria-live="polite"></div>
    <p class="result-receipt-auth">${escapeHtml(hold)}</p>
    ${boundary}
  `;
};

export const renderResultReceiptOpen = (response: LocalResultOpenResponse): string => {
  const content = JSON.stringify(response.result, null, 2);
  return `
    <section class="result-receipt-preview">
      <div class="result-receipt-preview-head">
        <strong>${escapeHtml(response.identity.result_id)}</strong>
        <small>${formatBytes(response.identity.size_bytes)} · SHA-256 ${escapeHtml(response.identity.sha256)}</small>
      </div>
      <pre>${escapeHtml(content)}</pre>
      <p class="result-receipt-boundary">${escapeHtml(response.boundary)}</p>
    </section>
  `;
};

export const renderResultReceiptsError = (message: string): string => `
  <p class="result" data-tone="bad">${escapeHtml(message)}</p>
`;

export const bindResultReceiptButtons = (
  mount: HTMLElement,
  handler: ResultReceiptOpenHandler,
): void => {
  mount.querySelectorAll<HTMLButtonElement>("[data-result-receipt]").forEach((button) => {
    button.addEventListener("click", () => {
      const resultId = button.dataset.resultReceipt || "";
      if (resultId && !button.disabled) void handler(resultId, button);
    });
  });
};
