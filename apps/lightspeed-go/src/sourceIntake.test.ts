import { afterEach, describe, expect, it, vi } from "vitest";
import { createSourceIntakeCommand, stageDesktopSource, type StagedSource } from "./desktopBridge";

const source: StagedSource = {
  state: "staged", source_name: "original.txt", source_path: "D:/sources/original.txt",
  source_sha256: "a".repeat(64), byte_length: 3, queue_dispatched: false, canonical_mutation: false,
};
const authority = {
  canonical_gate_id: "gate", owner_decision_ref: "owner", core_acceptance_ref: "core",
  approval_or_hold_state: "approved", authorised_scope: "Neo private local queue",
  prohibited_scope: "canonical mutation",
};
afterEach(() => vi.unstubAllGlobals());

describe("native source intake", () => {
  it("binds extraction to source identity and preserves authority gates", () => {
    const command = createSourceIntakeCommand(source, authority);
    expect(command.target_floor).toBe("Neo");
    expect(command.execution_mode).toBe("queue");
    expect(command.action_type).toBe("source_preserving_intake");
    expect(command.action_payload).toEqual({ source_path: source.source_path, source_sha256: source.source_sha256 });
    expect(command.oversight_floor).toBe("Achilles");
    expect(() => createSourceIntakeCommand(source, null)).toThrow("authority");
    expect(() => createSourceIntakeCommand(source, { ...authority, approval_or_hold_state: "held" })).toThrow("held");
  });
  it("requires sign-in and bounds size before reading or sending bytes", async () => {
    const read = vi.fn();
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    const file = { size: 64 * 1024 * 1024 + 1, arrayBuffer: read } as unknown as File;
    await expect(stageDesktopSource(file, "")).rejects.toThrow("sign-in");
    await expect(stageDesktopSource(file, "session")).rejects.toThrow("64 MiB");
    expect(read).not.toHaveBeenCalled();
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("uploads exact bytes with owner authentication and rejects a mismatched receipt", async () => {
    vi.stubGlobal("window", { setTimeout, clearTimeout });
    const file = new File(["abc"], "original.txt");
    const hash = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    const receipt = { ...source, source_sha256: hash };
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => receipt });
    vi.stubGlobal("fetch", fetcher);
    expect(await stageDesktopSource(file, "session")).toEqual(receipt);
    const [url, init] = fetcher.mock.calls[0];
    expect(url).toContain(`source_sha256=${hash}`);
    expect(init.headers["X-LightSpeed-Session"]).toBe("session");
    expect(new TextDecoder().decode(init.body)).toBe("abc");
    fetcher.mockResolvedValue({ ok: true, json: async () => ({ ...receipt, source_name: "other.txt" }) });
    await expect(stageDesktopSource(file, "session")).rejects.toThrow("did not match");
    expect(fetcher.mock.calls.every(([url]) => String(url).includes("source-intake/stage"))).toBe(true);
  });
});
