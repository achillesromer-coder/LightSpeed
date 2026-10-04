import { afterEach, describe, expect, it, vi } from "vitest";
import { commandSubmissionIsUncertain, DesktopRequestError, createSourceIntakeCommand, stageDesktopSource, submitSourceIntakeCommand, readPendingCommands, type StagedSource } from "./desktopBridge";

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
  it("saves identity before dispatch and reuses it after a lost response", async () => {
    let stored = "[]";
    vi.stubGlobal("window", { setTimeout, clearTimeout });
    vi.stubGlobal("localStorage", { getItem: () => stored, setItem: (_key: string, value: string) => { stored = value; } });
    const command = createSourceIntakeCommand(source, authority);
    const fetcher = vi.fn().mockImplementation(async () => {
      expect(readPendingCommands()[0]).toEqual(command);
      throw new TypeError("reply lost");
    });
    vi.stubGlobal("fetch", fetcher);
    await expect(submitSourceIntakeCommand(command)).rejects.toThrow("reply lost");
    expect(readPendingCommands()).toEqual([command]);
    fetcher.mockResolvedValue({ ok: true, json: async () => ({ command_id: command.command_id, state: "queued" }) });
    await submitSourceIntakeCommand(readPendingCommands()[0]);
    expect(fetcher.mock.calls[0][1].body).toBe(fetcher.mock.calls[1][1].body);
    expect(readPendingCommands()).toEqual([]);
  });
  it("does not dispatch when command identity cannot be saved", async () => {
    vi.stubGlobal("localStorage", { getItem: () => "[]", setItem: () => { throw new Error("storage full"); } });
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    await expect(submitSourceIntakeCommand(createSourceIntakeCommand(source, authority))).rejects.toThrow("storage full");
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("retains command identity when a server failure could follow a queue write", () => {
    expect(commandSubmissionIsUncertain(new DesktopRequestError(500, "server failed"))).toBe(true);
    expect(commandSubmissionIsUncertain(new DesktopRequestError(504, "gateway timeout"))).toBe(true);
    expect(commandSubmissionIsUncertain(new DesktopRequestError(408, "request timeout"))).toBe(true);
    expect(commandSubmissionIsUncertain(new TypeError("network error"))).toBe(true);
    expect(commandSubmissionIsUncertain(new DesktopRequestError(403, "held"))).toBe(false);
    expect(commandSubmissionIsUncertain(new DesktopRequestError(400, "invalid"))).toBe(false);
  });
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
