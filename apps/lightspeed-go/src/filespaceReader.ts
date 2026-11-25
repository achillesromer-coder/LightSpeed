import template from "../../../UniSpace/FileSpace.html?raw";
import stylesheet from "../../../UniSpace/unispace.css?raw";
import script from "../../../UniSpace/filespace.js?raw";

export function readerDocument(): string {
  const doc = new DOMParser().parseFromString(template, "text/html");
  doc.querySelector("header")?.remove();
  doc.querySelector("footer a")?.remove();
  doc.querySelector("link[rel=stylesheet]")?.remove();
  const style = doc.createElement("style");
  style.textContent = stylesheet;
  doc.head.append(style);
  const policy = doc.createElement("meta");
  policy.httpEquiv = "Content-Security-Policy";
  policy.content = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'";
  doc.head.prepend(policy);
  const digest = import.meta.env.VITE_UNISPACE_REVIEW_SHA256;
  const size = Number(import.meta.env.VITE_UNISPACE_REVIEW_BYTES);
  if (/^[0-9a-f]{64}$/.test(digest ?? "") && Number.isSafeInteger(size) && size > 0 && size <= 16*1024*1024) {
    const main = doc.querySelector("main")!;
    main.dataset.librarySha = digest;
    main.dataset.librarySize = String(size);
  }
  doc.querySelector("script[src]")?.remove();
  const reader = doc.createElement("script");
  reader.textContent = script;
  doc.body.append(reader);
  return "<!doctype html>" + doc.documentElement.outerHTML;
}
