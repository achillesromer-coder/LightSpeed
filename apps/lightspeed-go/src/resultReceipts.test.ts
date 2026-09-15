import { describe, expect, it } from "vitest";
import type {
  LocalResultOpenResponse,
  LocalResultsResponse,
} from "./desktopBridge";
import {
  bindResultReceiptButtons,
  renderResultReceiptOpen,
  renderResultReceipts,
  renderResultReceiptsError,
} from "./resultReceipts";


const listing: LocalResultsResponse = {
  schema_version: "lightspeed-local-results-index-v1",
  state: "available",
  results: [{
    result_id: "LSGO-RESULT-001",
    command_id: "LSGO-TASK-001",
    task_id: 490,
    job_id: 490026,
    status: "completed",
    action_type: "rfs_emff_sweep",
    target_floor: "TheConstruct",
    created_utc: "2026-08-24T19:22:34+10:00",
    completed_utc: "2026-08-24T19:22:35+10:00",
    public_safe_state: "true",
    proof_required_state: "true",
    public_publish_authorized: false,
    drive_write_executed: false,
    size_bytes: 4189,
    modified_utc: "2026-08-24T09:22:35Z",
    sha256: "abc123",
  }],
  summary: {
    visible_result_count: 1,
    invalid_file_count: 0,
    scanned_file_count: 1,
    limit: 50,
    truncated: false,
    status_counts: { completed: 1 },
  },
  boundary: "Fixed receipt metadata only.",
};

type FakeButton = {
  dataset: Record<string, string>;
  disabled: boolean;
  addEventListener: (name: string, listener: () => void) => void;
  click: () => void;
};

const fakeButton = (dataset: Record<string, string>, disabled = false): FakeButton => {
  let listener: () => void = () => undefined;
  return {
    dataset,
    disabled,
    addEventListener: (_name, next) => { listener = next; },
    click: () => listener(),
  };
};

const fakeMount = (buttons: FakeButton[]): HTMLElement => ({
  querySelectorAll: () => buttons,
}) as unknown as HTMLElement;

describe("LightSpeed Go fixed local results", () => {
  it("renders bounded path-free metadata and fails closed when auth is unavailable", () => {
    const html = renderResultReceipts(listing, false);
    expect(html).toContain("LSGO-RESULT-001");
    expect(html).toContain("completed · rfs_emff_sweep · TheConstruct");
    expect(html).toContain("Content inspection is held");
    expect(html).toContain("disabled");
    expect(html).not.toContain("receipt_path");
    expect(html).not.toContain("shell_root");
  });

  it("binds an enabled receipt button to its exact result identity", () => {
    const enabled = fakeButton({ resultReceipt: "LSGO-RESULT-001" });
    const disabled = fakeButton({ resultReceipt: "LSGO-RESULT-HELD" }, true);
    const calls: string[] = [];
    bindResultReceiptButtons(
      fakeMount([enabled, disabled]),
      (resultId) => { calls.push(resultId); },
    );
    enabled.click();
    disabled.click();
    expect(calls).toEqual(["LSGO-RESULT-001"]);
  });

  it("escapes every value in the owner-confirmed unredacted receipt", () => {
    const opened: LocalResultOpenResponse = {
      schema_version: "lightspeed-local-result-open-v1",
      state: "opened_read_only",
      identity: {
        result_id: "LSGO-RESULT-<unsafe>",
        size_bytes: 80,
        modified_utc: "2026-08-24T09:22:35Z",
        sha256: "abc<123>",
      },
      result: {
        summary: '<script data-test="no">unsafe</script>',
        receipt_path: "D:\\private\\receipt.json",
      },
      source_mutated: false,
      boundary: "Owner-confirmed <read-only> receipt.",
    };
    const html = renderResultReceiptOpen(opened);
    expect(html).toContain("LSGO-RESULT-&lt;unsafe&gt;");
    expect(html).toContain("&lt;script data-test=\\&quot;no\\&quot;&gt;");
    expect(html).toContain("Owner-confirmed &lt;read-only&gt; receipt.");
    expect(html).not.toContain("<script");
  });

  it("escapes bridge errors", () => {
    const html = renderResultReceiptsError("Desktop returned <held>");
    expect(html).toContain("&lt;held&gt;");
    expect(html).not.toContain("<held>");
  });
});
