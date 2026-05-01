/**
 * Römer LightSpeed Shared Loader
 * @module shared-loader
 * @description
 * Central module resolution, theme token loading, error boundary, and page boot orchestrator.
 * Used by all Squarespace embeds to load repo modules dynamically with fallback UI.
 *
 * @version 2026-05-02.v1
 * @author Nathaniel Bouwer / Römer Industries
 * @license CC-BY-NC-ND-4.0
 */

/**
 * Resolves the first available module from a candidate list.
 * Attempts to fetch each candidate URL in order until one succeeds.
 * @param {string[]} candidates - Array of module URLs to attempt
 * @param {Object} config - Bootstrap config object (for logging)
 * @returns {Promise<string>} - URL of the first successfully resolved module
 * @throws {Error} if all candidates fail or array is empty
 */
async function resolveFirstAvailableModule(candidates, config) {
  if (!candidates || candidates.length === 0) {
    throw new Error("No module candidates provided to resolver.");
  }

  const errors = [];
  for (const candidate of candidates) {
    try {
      const url = candidate.includes("://") ? candidate : candidate;
      const resp = await fetch(url, { method: "HEAD", mode: "cors" });
      if (resp.ok || resp.status === 200) {
        if (config?.debug) console.log(`[LightSpeed] Resolved module: ${url}`);
        return url;
      }
    } catch (err) {
      errors.push(`${candidate}: ${err.message}`);
    }
  }

  throw new Error(`No available module candidates. Attempts: ${errors.join("; ")}`);
}

/**
 * Loads a JSON schema from a URL.
 * Used to validate page manifests, mission records, audit events, etc.
 * @param {string} schemaUrl - URL to the JSON schema
 * @returns {Promise<Object>} - Parsed JSON schema
 */
async function loadSchema(schemaUrl) {
  const resp = await fetch(schemaUrl);
  if (!resp.ok) throw new Error(`Failed to load schema from ${schemaUrl}: ${resp.statusText}`);
  return resp.json();
}

/**
 * Loads and applies theme tokens from a remote JSON file.
 * Injects CSS custom properties into :root.
 * @param {string} tokenUrl - URL to romer.tokens.json or theme-specific tokens
 * @param {string} theme - Theme name (operationsDark, missionDarkMpl, publicLight)
 * @returns {Promise<Object>} - Loaded token object
 */
async function loadAndApplyTokens(tokenUrl, theme = "operationsDark") {
  try {
    const resp = await fetch(tokenUrl);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const tokens = await resp.json();

    // Apply semantic tokens to :root
    const root = document.documentElement;
    if (tokens.semantic) {
      for (const [key, value] of Object.entries(tokens.semantic)) {
        root.style.setProperty(`--ri-${key.replace(/\./g, "-")}`, value);
      }
    }

    // Apply theme-specific overrides
    if (tokens.themes && tokens.themes[theme]) {
      for (const [key, value] of Object.entries(tokens.themes[theme])) {
        root.style.setProperty(`--ri-theme-${key}`, value);
      }
    }

    if (tokens.typography) {
      const typo = tokens.typography;
      if (typo.fontDisplay) root.style.setProperty("--ri-font-display", typo.fontDisplay);
      if (typo.fontUi) root.style.setProperty("--ri-font-ui", typo.fontUi);
      if (typo.fontMono) root.style.setProperty("--ri-font-mono", typo.fontMono);
    }

    return tokens;
  } catch (err) {
    console.warn(`[LightSpeed] Failed to load tokens from ${tokenUrl}:`, err.message);
    return {};
  }
}

/**
 * Error boundary wrapper for module loading.
 * Catches errors during dynamic import and provides diagnostic info.
 * @param {Object} params - { root, config, error }
 */
function renderErrorBoundary({ root, config, error }) {
  const errorHtml = `
    <div style="padding: 24px; color: #e8dfdc; background: linear-gradient(135deg, #090d12, #172334); border: 1px solid rgba(232,223,220,.2); border-radius: 18px; font-family: 'JetBrains Mono', monospace; font-size: 13px; line-height: 1.6;">
      <div style="color: #ff3038; font-weight: bold; margin-bottom: 12px;">⚠ LightSpeed Module Load Error</div>
      <div style="margin-bottom: 12px; color: rgba(232,223,220, .8);">${error.message || "Unknown error"}</div>
      ${config?.debug ? `<div style="color: #b7fb61; margin-top: 12px; font-size: 11px; white-space: pre-wrap; overflow-x: auto; background: rgba(0,0,0,.4); padding: 8px; border-radius: 6px;">${error.stack || "No stack trace"}</div>` : ""}
      <div style="margin-top: 12px; color: #ffdc57; font-size: 12px;">
        Fallback UI rendered. Check browser console and repo/endpoint configuration.
      </div>
    </div>
  `;
  root.innerHTML = errorHtml;
}

/**
 * Main page boot function.
 * Orchestrates config validation, token loading, module resolution, and mount.
 * @param {Object} params - { root, config }
 * @param {HTMLElement} params.root - DOM element to mount into
 * @param {Object} params.config - Bootstrap config (from Squarespace embed)
 * @returns {Promise<void>}
 */
export async function mountPage({ root, config }) {
  try {
    // Validate config
    if (!root || !(root instanceof HTMLElement)) {
      throw new Error("Invalid root: expected HTMLElement");
    }
    if (!config || typeof config !== "object") {
      throw new Error("Invalid config: expected object");
    }

    // Load tokens
    if (config.repo?.themeTokens) {
      await loadAndApplyTokens(config.repo.themeTokens, config.theme || "operationsDark");
    }

    // Resolve module
    const moduleUrl = await resolveFirstAvailableModule(config.module?.candidates || [], config);

    // Dynamic import
    const moduleExport = await import(`${moduleUrl}?v=${encodeURIComponent(config.version || "unknown")}`);

    // Find mount function (try in priority order)
    const mountFn =
      moduleExport.mountWorkspace ||
      moduleExport.mountDataspace ||
      moduleExport.mountApp ||
      moduleExport.mountPage ||
      moduleExport.bootPage ||
      moduleExport.default;

    if (typeof mountFn !== "function") {
      throw new Error(
        `No suitable mount export found in module. Expected: mountWorkspace, mountDataspace, mountApp, mountPage, or default. Got keys: ${Object.keys(moduleExport).join(", ")}`
      );
    }

    // Mount module
    await mountFn({ root, config });

    // Signal success
    window.dispatchEvent(new CustomEvent("ri:module-mounted", { detail: { config, moduleUrl } }));
  } catch (error) {
    console.error("[LightSpeed] Boot error:", error);
    renderErrorBoundary({ root, config, error });
    window.dispatchEvent(new CustomEvent("ri:module-load-failed", { detail: { error: error.message, config } }));
  }
}

// Aliases for different page types
export const mountWorkspace = mountPage;
export const mountDataspace = mountPage;
export const mountApp = mountPage;
export const bootLightspeedPage = mountPage;

// Utility exports for adapters and modules
export { loadSchema, loadAndApplyTokens, resolveFirstAvailableModule, renderErrorBoundary };

export default { mountPage, loadSchema, loadAndApplyTokens, resolveFirstAvailableModule, renderErrorBoundary };