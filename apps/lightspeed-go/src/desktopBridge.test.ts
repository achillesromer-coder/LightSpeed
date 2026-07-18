import { describe, expect, it } from "vitest";
import { COMMAND_SCHEMA, createCommandEnvelope, routeInstruction } from "./desktopBridge";

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
    });
    expect(command.schema_version).toBe(COMMAND_SCHEMA);
    expect(command.oversight_floor).toBe("Achilles");
    expect(command.proof_required).toBe(true);
    expect(command.public_safe).toBe(true);
    expect(command.target_floor).toBe("Architect");
  });
});
