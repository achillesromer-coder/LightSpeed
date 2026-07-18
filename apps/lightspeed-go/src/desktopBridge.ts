export const COMMAND_SCHEMA = "lightspeed-go-command-v1";
export const DEFAULT_DESKTOP_ORIGIN = "http://127.0.0.1:8765";

export const FLOORS = [
  "Achilles",
  "Neo",
  "Architect",
  "TheConstruct",
  "Morpheus",
  "Oracle",
  "Smith",
  "Merovingian",
  "Trinity",
] as const;

export type Floor = (typeof FLOORS)[number];
export type Priority = "critical" | "high" | "normal" | "low";
export type ExecutionMode = "review" | "queue";

export interface CommandEnvelope {
  schema_version: typeof COMMAND_SCHEMA;
  command_id: string;
  created_utc: string;
  source: "LS GO";
  title: string;
  instruction: string;
  target_floor: Floor;
  oversight_floor: "Achilles";
  priority: Priority;
  execution_mode: ExecutionMode;
  proof_required: true;
  public_safe: true;
}

export interface CommandInput {
  title?: string;
  instruction: string;
  targetFloor?: Floor;
  priority?: Priority;
  executionMode?: ExecutionMode;
}

export interface DesktopStatus {
  ok: boolean;
  time_utc?: string;
  auth?: { configured?: boolean };
  services?: { db?: boolean; storage?: boolean };
}

export interface CommandReceipt {
  accepted: boolean;
  task_id?: number;
  job?: Record<string, unknown>;
  command_id?: string;
  state?: string;
  detail?: string;
}

const normalize = (value: string, maximum: number): string =>
  value.replace(/\s+/g, " ").trim().slice(0, maximum);

export const routeInstruction = (instruction: string): Floor => {
  const text = instruction.toLowerCase();
  if (/\b(ui|site|web|design|visual|layout|canva|accessibility)\b/.test(text)) return "Trinity";
  if (/\b(git|github|code|build|commit|branch|deploy|schema|api|runtime)\b/.test(text)) return "Smith";
  if (/\b(source|evidence|research|data|document|drive|sheet|workbook|citation)\b/.test(text)) return "Oracle";
  if (/\b(proof|claim|verify|conflict|confidence|audit)\b/.test(text)) return "Morpheus";
  if (/\b(simulate|simulation|model|gmat|trajectory|twin|physics)\b/.test(text)) return "TheConstruct";
  if (/\b(plan|mission|architecture|dependency|roadmap|system)\b/.test(text)) return "Architect";
  if (/\b(health|status|diagnostic|failure|error|monitor)\b/.test(text)) return "Merovingian";
  if (/\b(coordinate|queue|handoff|agent|task|execute|run)\b/.test(text)) return "Neo";
  return "Achilles";
};

export const createCommandEnvelope = (input: CommandInput): CommandEnvelope => {
  const instruction = normalize(input.instruction, 4000);
  if (!instruction) throw new TypeError("instruction is required");
  const created = new Date().toISOString();
  const entropy = Math.random().toString(36).slice(2, 8).toUpperCase();
  const targetFloor = input.targetFloor ?? routeInstruction(instruction);
  return {
    schema_version: COMMAND_SCHEMA,
    command_id: `LSGO-${created.replace(/\D/g, "").slice(0, 14)}-${entropy}`,
    created_utc: created,
    source: "LS GO",
    title: normalize(input.title || instruction, 160),
    instruction,
    target_floor: targetFloor,
    oversight_floor: "Achilles",
    priority: input.priority ?? "normal",
    execution_mode: input.executionMode ?? "review",
    proof_required: true,
    public_safe: true,
  };
};

const withTimeout = async <T>(url: string, init: RequestInit, timeoutMs = 3500): Promise<T> => {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal, cache: "no-store" });
    if (!response.ok) throw new Error(`Desktop returned HTTP ${response.status}`);
    return (await response.json()) as T;
  } finally {
    window.clearTimeout(timer);
  }
};

export const readDesktopStatus = (origin = DEFAULT_DESKTOP_ORIGIN): Promise<DesktopStatus> =>
  withTimeout<DesktopStatus>(`${origin}/api/v1/status`, { method: "GET" });

export const submitDesktopCommand = (
  command: CommandEnvelope,
  origin = DEFAULT_DESKTOP_ORIGIN,
): Promise<CommandReceipt> =>
  withTimeout<CommandReceipt>(`${origin}/api/v1/ls-go/commands`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(command),
  }, 7000);

export const listDesktopTasks = async (origin = DEFAULT_DESKTOP_ORIGIN): Promise<Record<string, unknown>[]> => {
  const response = await withTimeout<{ tasks?: Record<string, unknown>[] }>(
    `${origin}/api/v1/tasks?limit=12`,
    { method: "GET" },
  );
  return Array.isArray(response.tasks) ? response.tasks : [];
};

const STORAGE_KEY = "lightspeed-go-pending-commands-v1";

export const readPendingCommands = (): CommandEnvelope[] => {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]") as unknown;
    return Array.isArray(value) ? (value as CommandEnvelope[]) : [];
  } catch {
    return [];
  }
};

export const storePendingCommand = (command: CommandEnvelope): CommandEnvelope[] => {
  const current = readPendingCommands().filter((item) => item.command_id !== command.command_id);
  const next = [command, ...current].slice(0, 30);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
};

export const removePendingCommand = (commandId: string): CommandEnvelope[] => {
  const next = readPendingCommands().filter((item) => item.command_id !== commandId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
};

export const downloadCommand = (command: CommandEnvelope): void => {
  const blob = new Blob([JSON.stringify(command, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${command.command_id}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
};
