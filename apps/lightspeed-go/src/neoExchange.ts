export const EXCHANGE_SCHEMA = "lightspeed-neo-exchange-v1";

const PRIORITIES = ["critical", "high", "normal", "low"] as const;
const STATUSES = ["queued", "active", "review", "blocked", "complete"] as const;
const EXTENSION_KEYS = ["icon", "age_label"] as const;

export type QueuePriority = (typeof PRIORITIES)[number];
export type QueueStatus = (typeof STATUSES)[number];

export interface PublicQueueRecord {
  id: string;
  title: string;
  priority: QueuePriority;
  status: QueueStatus;
  source: string;
  target: string;
  created_utc: string;
  extensions: Record<string, string>;
  notes: string;
}

export interface NeoExchange {
  schema_version: typeof EXCHANGE_SCHEMA;
  generated_at_utc: string;
  queue: PublicQueueRecord[];
}

export interface ExchangeSummary {
  total: number;
  critical: number;
  active: number;
  complete: number;
}

type UnknownRecord = Record<string, unknown>;

const isRecord = (value: unknown): value is UnknownRecord =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const boundedString = (
  value: unknown,
  fallback: string,
  maximumLength: number,
): string => {
  if (typeof value !== "string") return fallback;
  const normalized = value.replace(/\s+/g, " ").trim();
  return normalized ? normalized.slice(0, maximumLength) : fallback;
};

const requiredString = (
  value: unknown,
  field: "id" | "title",
  maximumLength: number,
): string => {
  const normalized = boundedString(value, "", maximumLength);
  if (!normalized) throw new TypeError(`queue record ${field} is required`);
  return normalized;
};

const enumValue = <T extends string>(
  value: unknown,
  allowed: readonly T[],
  fallback: T,
): T => (typeof value === "string" && allowed.includes(value as T) ? (value as T) : fallback);

const normalizeExtensions = (value: unknown): Record<string, string> => {
  if (!isRecord(value)) return {};
  return Object.fromEntries(
    EXTENSION_KEYS.flatMap((key) => {
      const normalized = boundedString(value[key], "", 48);
      return normalized ? [[key, normalized]] : [];
    }),
  );
};

export const normalizeQueueRecord = (value: unknown): PublicQueueRecord => {
  if (!isRecord(value)) throw new TypeError("queue record must be an object");
  return {
    id: requiredString(value.id, "id", 80),
    title: requiredString(value.title, "title", 160),
    priority: enumValue(value.priority, PRIORITIES, "normal"),
    status: enumValue(value.status, STATUSES, "queued"),
    source: boundedString(value.source, "GO Gate", 48),
    target: boundedString(value.target, "Neo", 48),
    created_utc: boundedString(value.created_utc, "", 32),
    extensions: normalizeExtensions(value.extensions),
    notes: boundedString(value.notes, "", 240),
  };
};

export const normalizeExchange = (value: unknown): NeoExchange => {
  if (!isRecord(value)) throw new TypeError("Neo exchange must be an object");
  const queue = Array.isArray(value.queue) ? value.queue.map(normalizeQueueRecord) : [];
  return {
    schema_version: EXCHANGE_SCHEMA,
    generated_at_utc: boundedString(value.generated_at_utc, "", 32),
    queue,
  };
};

export const summarizeExchange = (exchange: NeoExchange): ExchangeSummary => ({
  total: exchange.queue.length,
  critical: exchange.queue.filter((record) => record.priority === "critical").length,
  active: exchange.queue.filter((record) => record.status !== "complete").length,
  complete: exchange.queue.filter((record) => record.status === "complete").length,
});

export const escapeHtml = (value: string): string =>
  value.replace(
    /[&<>"']/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
      })[character] ?? character,
  );

export const loadNeoExchange = async (
  readProjection: () => Promise<unknown>,
): Promise<NeoExchange> => {
  try {
    return normalizeExchange(await readProjection());
  } catch {
    return normalizeExchange({});
  }
};

const queueTone = (record: PublicQueueRecord): string => {
  if (record.status === "blocked") return "blocked";
  if (record.status === "complete") return "pass";
  if (record.priority === "critical" || record.priority === "high") return "warn";
  return "ready";
};

export const renderExchangePanel = (exchange: NeoExchange): string => {
  const summary = summarizeExchange(exchange);
  const rows = exchange.queue.length
    ? exchange.queue
        .map(
          (record) => `
            <li class="status-row ${queueTone(record)}">
              <div>
                <strong>${escapeHtml(record.title)}</strong>
                <span>${escapeHtml(record.source)} to ${escapeHtml(record.target)} · ${escapeHtml(record.id)}</span>
                ${record.notes ? `<small>${escapeHtml(record.notes)}</small>` : ""}
              </div>
              <em>${escapeHtml(record.status)}</em>
            </li>
          `,
        )
        .join("")
    : `
      <li class="status-row ready">
        <div>
          <strong>Routed queue clear</strong>
          <span>No GO-accepted Neo actions are waiting.</span>
        </div>
        <em>ready</em>
      </li>
    `;
  return `
    <div class="exchange-summary" aria-label="GO-gated Neo routing summary">
      <span><strong>${summary.total}</strong> total</span>
      <span aria-label="${summary.active} active"><strong>${summary.active}</strong> active</span>
      <span><strong>${summary.critical}</strong> critical</span>
      <span><strong>${summary.complete}</strong> complete</span>
    </div>
    <ul class="status-list exchange-list">${rows}</ul>
  `;
};
