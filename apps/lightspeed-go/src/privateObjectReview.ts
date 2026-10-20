/* Private CGX review reads: no public/ URLs, no URL tokens, no persistent cache. */
import { DEFAULT_DESKTOP_ORIGIN, DesktopRequestError } from "./desktopBridge";

const SHA256 = /^[0-9a-f]{64}$/i;
const NAME = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;
const LIMIT = 4 * 1024 * 1024;

export type PrivateReviewKind = "catalogue" | "atlas" | "renders" | "mesh";
export type PrivateReviewFile = { kind: PrivateReviewKind; name: string };

export const privateReviewFileFromLegacyPath = (raw: string): PrivateReviewFile => {
  if (typeof raw !== "string" || raw.length > 256 || raw.includes("?") || raw.includes("#") || raw.includes("%")) {
    throw new Error("Private review filename is not a trusted static path");
  }
  if (raw === "/data/cgx_object_review_catalogue.json") {
    return { kind: "catalogue", name: "cgx_object_review_catalogue.json" };
  }
  if (raw === "/data/component_geometry_atlas_public_review.json") {
    return { kind: "atlas", name: "component_geometry_atlas_public_review.json" };
  }
  const match = /^\/review\/(renders|mesh)\/([^/]+)$/.exec(raw);
  if (!match) throw new Error("Review media is not an allowed private asset");
  const kind = match[1] as "renders" | "mesh";
  const name = match[2];
  if (!NAME.test(name) || name === "." || name === ".." ||
      !(kind === "renders" ? name.endsWith(".svg") : name.endsWith(".json"))) {
    throw new Error("Private review asset name rejected");
  }
  return { kind, name };
};
export const privateReviewApiPath = (sourcePath: string): string => {
  const { kind, name } = privateReviewFileFromLegacyPath(sourcePath);
  return "/api/v1/private-object-review/" + encodeURIComponent(kind) + "/" + encodeURIComponent(name);
};

export class PrivateObjectReviewSession {
  private active = true;
  private readonly requests = new Set<AbortController>();
  private readonly blobUrls = new Set<string>();
  private readonly blobPromises = new Map<string, Promise<string>>();
  private readonly ownerSession: string;
  private readonly origin: string;
  constructor(ownerSession: string, origin = DEFAULT_DESKTOP_ORIGIN) {
    if (!ownerSession || ownerSession.length > 256) throw new Error("Owner session is required");
    this.ownerSession = ownerSession;
    this.origin = origin;
  }
  get isActive(): boolean { return this.active; }
  revoke(): void {
    this.active = false;
    this.requests.forEach((item) => item.abort());
    this.requests.clear();
    for (const url of this.blobUrls) URL.revokeObjectURL(url);
    this.blobUrls.clear();
    this.blobPromises.clear();
  }
  async read(sourcePath: string, outerSignal?: AbortSignal): Promise<Uint8Array> {
    if (!this.active) throw new Error("Owner review session closed");
    const { kind } = privateReviewFileFromLegacyPath(sourcePath);
    const controller = new AbortController();
    this.requests.add(controller);
    const signal = controller.signal;
    const cancel = (): void => controller.abort();
    if (outerSignal?.aborted) controller.abort();
    outerSignal?.addEventListener("abort", cancel, { once: true });
    try {
      const response = await fetch(this.origin + privateReviewApiPath(sourcePath), {
        method: "GET", cache: "no-store", mode: "cors", credentials: "omit",
        redirect: "error", signal, headers: { "X-LightSpeed-Session": this.ownerSession },
      });
      if (!response.ok) throw new DesktopRequestError(response.status, "Private asset unavailable or owner session denied");
      if (response.type === "opaque" || response.type === "opaqueredirect") {
        throw new Error("Private asset response must be authenticated and readable");
      }
      const mime = response.headers.get("Content-Type")?.split(";")[0].toLowerCase();
      const expected = kind === "renders" ? "image/svg+xml" : "application/json";
      if (mime !== expected) throw new Error("Private review asset media type mismatch");
      const declared = Number(response.headers.get("Content-Length") || "0");
      if (!Number.isFinite(declared) || declared > LIMIT) throw new Error("Private asset size limit exceeded");
      const bytes = new Uint8Array(await response.arrayBuffer());
      if (bytes.byteLength > LIMIT || !this.active || signal.aborted) throw new Error("Private review read invalidated");
      const pin = response.headers.get("X-CGX-Source-SHA256") || "";
      if (!SHA256.test(pin) || !globalThis.crypto?.subtle) throw new Error("Missing verifiable private source digest");
      const received = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
      const digest = Array.from(received, (x) => x.toString(16).padStart(2, "0")).join("");
      if (digest !== pin.toLowerCase() || !this.active) throw new Error("Private asset source digest mismatch");
      return bytes;
    } finally {
      outerSignal?.removeEventListener("abort", cancel);
      this.requests.delete(controller);
    }
  }
  async readJson<T>(sourcePath: string, signal?: AbortSignal): Promise<T> {
    const kind = privateReviewFileFromLegacyPath(sourcePath).kind;
    if (kind === "renders") throw new Error("Review render is not JSON");
    const bytes = await this.read(sourcePath, signal);
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)) as T;
  }
  blobUrl(sourcePath: string): Promise<string> {
    if (!this.active) return Promise.reject(Error("Owner review session closed"));
    const kind = privateReviewFileFromLegacyPath(sourcePath).kind;
    if (kind !== "renders") return Promise.reject(Error("Only SVG thumbnails may be exposed as Blob URLs"));
    const cached = this.blobPromises.get(sourcePath);
    if (cached) return cached;
    const promise = this.read(sourcePath).then((bytes) => {
      if (!this.active) throw new Error("Owner review session closed");
      const isolated = new Uint8Array(bytes.byteLength);
      isolated.set(bytes);
      const url = URL.createObjectURL(new Blob([isolated.buffer], { type: "image/svg+xml" }));
      if (!this.active) { URL.revokeObjectURL(url); throw new Error("Owner review session closed"); }
      this.blobUrls.add(url);
      return url;
    });
    this.blobPromises.set(sourcePath, promise);
    promise.catch(() => { if (this.blobPromises.get(sourcePath) === promise) this.blobPromises.delete(sourcePath); });
    return promise;
  }
}

export const bindPrivateReviewMedia = (root: HTMLElement, session: PrivateObjectReviewSession): (() => void) => {
  let observer: IntersectionObserver | null = null;
  let disposed = false;
  const expand = async (image: HTMLImageElement): Promise<void> => {
    const path = image.dataset.privateRender || "";
    try {
      const url = await session.blobUrl(path);
      if (session.isActive && !disposed && image.isConnected) image.src = url;
    } catch {
      image.alt = "Owner review media unavailable or session denied";
    }
  };
  const images = [...root.querySelectorAll<HTMLImageElement>("img[data-private-render]")];
  if (typeof IntersectionObserver !== "undefined") {
    observer = new IntersectionObserver((records) => records.forEach((record) => {
      if (!record.isIntersecting || !observer) return;
      observer.unobserve(record.target);
      void expand(record.target as HTMLImageElement);
    }), { rootMargin: "200px" });
    images.forEach((img) => observer?.observe(img));
  } else {
    // Old browsers receive no automatic media fetches. Owner may still open a plate.
  }
  const actions = [...root.querySelectorAll<HTMLButtonElement>("button[data-private-open]")];
  let dialog: HTMLDialogElement | null = null;
  for (const button of actions) button.addEventListener("click", async () => {
    if (disposed || !session.isActive) return;
    button.disabled = true;
    try {
      const url = await session.blobUrl(button.dataset.privateOpen || "");
      if (disposed || !session.isActive) return;
      if (!dialog) {
        dialog = document.createElement("dialog");
        dialog.setAttribute("aria-label", "Private CGX engineering plate");
        dialog.innerHTML = '<button type="button" aria-label="Close plate">Close</button><img alt="Private source-qualified CGX review plate" style="max-width:min(94vw,1200px);max-height:85vh;display:block"/>';
        dialog.querySelector("button")?.addEventListener("click", () => dialog?.close());
        root.appendChild(dialog);
      }
      const target = dialog.querySelector("img");
      if (target) target.src = url;
      if (!dialog.open) dialog.showModal();
    } catch {
      button.textContent = "Private media unavailable";
    } finally {
      if (!disposed) button.disabled = false;
    }
  });
  return () => {
    disposed = true;
    observer?.disconnect();
    dialog?.close();
    dialog?.remove();
    images.forEach((img) => img.removeAttribute("src"));
    session.revoke();
  };
};
