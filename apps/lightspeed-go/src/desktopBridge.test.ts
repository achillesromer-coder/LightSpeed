import { describe, expect, it } from "vitest";
import { COMMAND_SCHEMA, createCommandEnvelope, routeInstruction } from "./desktopBridge";

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
    expect(command.target_floor).toBe("Architect");
    expect(command.canonical_gate_id).toBe("gate-soft-launch");
    expect(command.requested_scope).toBe("Architect private local review queue");
  });

  it("fails closed when the Desktop authority contract is unavailable", () => {
    expect(() => createCommandEnvelope({ instruction: "Run a bounded health check" })).toThrow(
      "Desktop authority contract is not available",
    );
  });
});
