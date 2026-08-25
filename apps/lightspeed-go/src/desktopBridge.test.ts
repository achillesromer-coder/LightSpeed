import { describe, expect, it } from "vitest";
import {
  COMMAND_SCHEMA,
  createCommandEnvelope,
  projectFileApiPath,
  resultReceiptApiPath,
  reviewDecisionOutcomeMessage,
  routeInstruction,
} from "./desktopBridge";

const authorityContract = {
  canonical_gate_id: "gate-soft-launch",
  owner_decision_ref: "owner-decision-1",
  core_acceptance_ref: "core-acceptance-1",
  approval_or_hold_state: "operator_approved",
  authorised_scope: "all floors; private local review queue",
  prohibited_scope: "public publish; destructive filesystem operations",
};

describe("LS GO desktop command routing", () => {
  it("routes implementation work to Smith", () => {
    expect(routeInstruction("Update the Git branch, run the build and return a commit receipt")).toBe("Smith");
  });

  it("routes evidence work to Oracle", () => {
    expect(routeInstruction("Read the Drive workbook and reconcile the source evidence")).toBe("Oracle");
  });

  it("retains Achilles oversight in every envelope", () => {
    const command = createCommandEnvelope({
      instruction: "Prepare a reviewed mission architecture update",
      priority: "high",
      executionMode: "review",
      authorityContract,
    });
    expect(command.schema_version).toBe(COMMAND_SCHEMA);
    expect(command.oversight_floor).toBe("Achilles");
    expect(command.proof_required).toBe(true);
    expect(command.public_safe).toBe(true);
    expect(command.action_type).toBe("cognigrex_workflow");
    expect(command.target_floor).toBe("Architect");
    expect(command.canonical_gate_id).toBe("gate-soft-launch");
    expect(command.requested_scope).toBe("Architect private local review queue");
  });

  it("fails closed when the Desktop authority contract is unavailable", () => {
    expect(() => createCommandEnvelope({ instruction: "Run a bounded health check" })).toThrow(
      "Desktop authority contract is not available",
    );
  });

  it("encodes project file routes segment-by-segment", () => {
    expect(projectFileApiPath("project alpha", "results/a file.json")).toBe(
      "/api/v1/projects/project%20alpha/files/results/a%20file.json",
    );
  });

  it("encodes a result identity as one fixed route segment", () => {
    expect(resultReceiptApiPath()).toBe("/api/v1/results");
    expect(resultReceiptApiPath("LSGO RESULT/held")).toBe(
      "/api/v1/results/LSGO%20RESULT%2Fheld",
    );
  });

  it("distinguishes local outbox staging from an owner-approved Drive write", () => {
    const pending = reviewDecisionOutcomeMessage("review-1", "approve", {
      accepted: true,
      receipt: { drive_writeback_mode: "local_outbox_pending_drive_sync" },
    });
    const drive = reviewDecisionOutcomeMessage("review-2", "hold", {
      accepted: true,
      receipt: { drive_writeback_mode: "owner_approved_exact_drive_target" },
    });
    expect(pending).toContain("Local outbox receipt staged; Drive sync remains pending");
    expect(pending).not.toContain("Drive decision receipt written");
    expect(drive).toContain("Owner-approved Drive decision receipt written");
  });
});
