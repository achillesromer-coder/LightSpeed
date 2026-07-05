import { describe, expect, it } from "vitest";

import {
  escapeHtml,
  loadNeoExchange,
  normalizeExchange,
  normalizeQueueRecord,
  renderExchangePanel,
  summarizeExchange,
} from "./neoExchange";


describe("normalizeQueueRecord", () => {
  it("accepts minimal and extended queue records", () => {
    expect(normalizeQueueRecord({ id: "T-1", title: "Review" }).id).toBe("T-1");
    expect(
      normalizeQueueRecord({
        id: "T-2",
        title: "Publish",
        priority: "critical",
        extensions: { icon: "warning" },
        notes: "Owner review required",
      }).extensions.icon,
    ).toBe("warning");
  });

  it("drops private payload, path, URL, and credential fields", () => {
    const record = normalizeQueueRecord({
      id: "T-3",
      title: "Bounded handoff",
      drive_url: "https://drive.google.com/private",
      local_path: "C:\\private\\artifact.json",
      payload: { private: true },
      token: "secret-token",
    });

    expect(record).toEqual({
      id: "T-3",
      title: "Bounded handoff",
      priority: "normal",
      status: "queued",
      source: "Neo",
      target: "Review",
      created_utc: "",
      extensions: {},
      notes: "",
    });
  });

  it("rejects records without a stable id or title", () => {
    expect(() => normalizeQueueRecord({ title: "No ID" })).toThrow("id");
    expect(() => normalizeQueueRecord({ id: "T-4" })).toThrow("title");
  });

  it("escapes queue content before HTML rendering", () => {
    expect(escapeHtml(`<img src=x onerror="alert(1)">`)).toBe(
      "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;",
    );
  });
});


describe("normalizeExchange", () => {
  it("normalizes the public queue and derives bounded counts", () => {
    const exchange = normalizeExchange({
      schema_version: "lightspeed-neo-exchange-v1",
      generated_at_utc: "2026-07-05T00:00:00Z",
      queue: [
        { id: "T-5", title: "Critical review", priority: "critical" },
        { id: "T-6", title: "Completed proof", status: "complete" },
      ],
    });

    expect(summarizeExchange(exchange)).toEqual({
      total: 2,
      critical: 1,
      active: 1,
      complete: 1,
    });
  });

  it("returns an empty bounded exchange when the public projection is unavailable", async () => {
    const exchange = await loadNeoExchange(async () => {
      throw new Error("offline");
    });

    expect(exchange.queue).toEqual([]);
    expect(exchange.schema_version).toBe("lightspeed-neo-exchange-v1");
  });

  it("renders escaped queue content and summary counts", () => {
    const exchange = normalizeExchange({
      queue: [
        {
          id: "T-7",
          title: `<img src=x onerror="alert(1)">`,
          status: "active",
        },
      ],
    });

    const html = renderExchangePanel(exchange);

    expect(html).toContain("1 active");
    expect(html).toContain("&lt;img src=x");
    expect(html).not.toContain("<img src=x");
  });
});
