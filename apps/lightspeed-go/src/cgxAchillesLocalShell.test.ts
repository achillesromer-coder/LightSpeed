import { describe, expect, it } from "vitest";
import {
  ACHILLES_LOCAL_FACETS, ACHILLES_LOCAL_ROOT,
  ACHILLES_LOCAL_SHELL_SCHEMA, ACHILLES_LOCAL_SHELL_URL,
  ACHILLES_DESKTOP_BRIDGE_BASELINE, planAchillesLocalShell,
  resolveAchillesLocalShellUrl,
} from "./cgxAchillesLocalShell";

describe("Existing Achilles 8772 local supervisor boundary", () => {
  it("uses the observed loopback endpoint only", () => {
    expect(resolveAchillesLocalShellUrl("http://127.0.0.1:8772/")).toBe(ACHILLES_LOCAL_SHELL_URL);
    expect(resolveAchillesLocalShellUrl("http://127.0.0.1:8772")).toBe(ACHILLES_LOCAL_SHELL_URL);
  });
  it("keeps Achilles 8772 distinct from Desktop 8765", () => {
    expect(ACHILLES_DESKTOP_BRIDGE_BASELINE).toBe("http://127.0.0.1:8765");
    expect(ACHILLES_LOCAL_SHELL_URL).not.toBe(ACHILLES_DESKTOP_BRIDGE_BASELINE);
  });
  it("rejects remote host attempts and alternate host aliases", () => {
    for(const bad of ["https://example.com:8772/","http://example.com:8772/",
      "http://localhost:8772/","http://127.0.0.2:8772/",
      "http://192.168.1.7:8772/","http://[::1]:8772/"]) {
      expect(() => resolveAchillesLocalShellUrl(bad)).toThrow("ACHILLES_LOCAL_EXACT_ORIGIN_REQUIRED");
    }
  });
  it("rejects credentials, query parameters, fragment and path escalation", () => {
    for(const bad of ["http://user:pw@127.0.0.1:8772/",
      "http://127.0.0.1:8772/health", "http://127.0.0.1:8772/api",
      "http://127.0.0.1:8772/?action=stop", "http://127.0.0.1:8772/#execute",
      "http://127.0.0.1:8773/", "https://127.0.0.1:8772/"]) {
      expect(() => resolveAchillesLocalShellUrl(bad)).toThrow("ACHILLES_LOCAL_EXACT_ORIGIN_REQUIRED");
    }
  });
  it("rejects malformed input and nonstring values", () => {
    for(const bad of ["", "/relative", "not-a-url", null, undefined, 8772, {}, "x".repeat(70)]) {
      expect(() => resolveAchillesLocalShellUrl(bad)).toThrow("ACHILLES_LOCAL_EXACT_ORIGIN_REQUIRED");
    }
  });
  it("keeps precisely one existing canonical root", () => {
    const plan = planAchillesLocalShell();
    expect(plan.parent).toBe(ACHILLES_LOCAL_ROOT);
    expect(plan.schema).toBe(ACHILLES_LOCAL_SHELL_SCHEMA);
    expect(plan.parent).toBe("cgx:root:cognigrex");
  });
  it("has six observed capability categories without a new data store", () => {
    expect(ACHILLES_LOCAL_FACETS.map(x=>x.id)).toEqual([
      "agent_runtime", "cpu_policy", "failure_policy", "llm_sorter", "loaded_models", "operator_notes",
    ]);
    expect(planAchillesLocalShell().facets).toBe(ACHILLES_LOCAL_FACETS);
  });
  it("preserves evidence: root 200 is historical, health route 404", () => {
    const obs = planAchillesLocalShell().observation;
    expect(obs.rootHttp).toBe(200);
    expect(obs.rootTitle).toBe("Achilles shell");
    expect(obs.healthRouteHttp).toBe(404);
    expect(obs.currentBrowserStatus).toBe("NOT_VERIFIED");
    expect(obs.date).toBe("2026-11-23");
  });
  it("does not invent live model counts or CPU current values", () => {
    const p = planAchillesLocalShell();
    expect(JSON.stringify(p)).not.toMatch(/"currentCpu"|"activeModelCount"|"agentCount"|"liveHealthy"/);
  });
  it("does not expose native authority or transport control", () => {
    const p = planAchillesLocalShell();
    for(const k of ["nativeAdmitted","peerDbrVerified","publicReleased",
      "hostAuthVerified","controlsBound","networkRequestsFromPage","privateHydration"] as const)
      expect(p[k]).toBe(false);
    expect(p.localOnly).toBe(true);
  });
  it("freezes observations and all declared capability metadata", () => {
    const p = planAchillesLocalShell();
    expect(Object.isFrozen(p)).toBe(true);
    expect(Object.isFrozen(p.observation)).toBe(true);
    expect(Object.isFrozen(p.facets)).toBe(true);
    p.facets.forEach(x=>expect(Object.isFrozen(x)).toBe(true));
  });
  it("does not promote the agent UI controls into UniSpace actions", () => {
    expect(ACHILLES_LOCAL_FACETS.every(x=>x.state==="OBSERVED_UI_CONTROL_NOT_CONNECTED")).toBe(true);
    expect(ACHILLES_LOCAL_FACETS.find(x=>x.id==="agent_runtime")?.boundary).toMatch(/not exposed/);
  });
  it("discloses resource control without initiating settings changes", () => {
    expect(ACHILLES_LOCAL_FACETS.find(x=>x.id==="cpu_policy")?.observed).toContain("10–100");
    expect(ACHILLES_LOCAL_FACETS.find(x=>x.id==="cpu_policy")?.boundary).toContain("No CPU setting");
  });
  it("marks loaded models and notes as private or unverified", () => {
    expect(ACHILLES_LOCAL_FACETS.find(x=>x.id==="loaded_models")?.boundary).toContain("No weights");
    expect(ACHILLES_LOCAL_FACETS.find(x=>x.id==="operator_notes")?.boundary).toContain("No notes");
  });
  it("retains the original local operator page instead of shadowing it", () => {
    const p = planAchillesLocalShell();
    expect(p.endpoint).toBe("http://127.0.0.1:8772/");
    expect(p.controlsBound).toBe(false);
  });
});
