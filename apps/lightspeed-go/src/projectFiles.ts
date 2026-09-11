import type {
  ProjectFileOpenResult,
  ProjectFilesResponse,
  ProjectRecord,
} from "./desktopBridge";
import { escapeHtml } from "./neoExchange";

export type ProjectBrowseHandler = (
  projectId: string,
  button: HTMLButtonElement,
) => void | Promise<void>;
export type ProjectFileOpenHandler = (
  projectId: string,
  relativePath: string,
  button: HTMLButtonElement,
) => void | Promise<void>;

const formatBytes = (value?: number): string => {
  const bytes = Number(value || 0);
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
};

export const renderProjectCards = (projects: ProjectRecord[]): string => {
  if (!projects.length) {
    return `<p class="muted">No project folders were found in the configured roots.</p>`;
  }
  return projects.slice(0, 30).map((project) => `
    <article class="task-card project-card" data-project-card="${escapeHtml(project.project_id)}">
      <div class="project-summary">
        <strong>${escapeHtml(project.name)}</strong>
        <span>${escapeHtml(project.condition || "unknown")} · ${escapeHtml(project.authority || "reference")} · ${project.file_count || 0} files</span>
        <small>${formatBytes(project.size_bytes)}${project.scan_truncated ? " · bounded scan" : ""}</small>
      </div>
      <div class="task-actions">
        <button type="button" data-project-files="${escapeHtml(project.project_id)}" aria-expanded="false">Files</button>
      </div>
      <div class="project-files" aria-live="polite" hidden></div>
    </article>
  `).join("");
};

export const renderProjectFiles = (response: ProjectFilesResponse): string => {
  const summary = response.summary;
  const boundary = `<p class="project-file-boundary">${escapeHtml(response.boundary)}</p>`;
  if (!response.files.length) {
    const message = response.state === "restricted"
      ? "No files are visible; credential-like or excluded runtime files are withheld."
      : "This registered project currently has no visible files.";
    return `<div class="project-files-head"><strong>Files</strong><small>${escapeHtml(response.project.authority || "reference")} authority</small></div><p class="muted">${message}</p>${boundary}`;
  }
  const rows = response.files.map((file) => `
    <article class="project-file-row">
      <div><strong>${escapeHtml(file.relative_path)}</strong><small>${escapeHtml(file.mime_type)} · ${formatBytes(file.size_bytes)}</small></div>
      <button type="button" data-project-file="${escapeHtml(file.relative_path)}" data-project-id="${escapeHtml(response.project.project_id)}">Open</button>
    </article>
  `).join("");
  const bounded = summary.scan_truncated ? " · bounded result" : "";
  return `
    <div class="project-files-head"><strong>Files</strong><small>${summary.visible_file_count} visible · ${summary.blocked_file_count} withheld${bounded}</small></div>
    <div class="project-file-list">${rows}</div>
    <div class="project-file-result" aria-live="polite"></div>
    ${boundary}
  `;
};

export const renderProjectFilesError = (message: string): string => `
  <div class="project-files-head"><strong>Files unavailable</strong></div>
  <p class="result" data-tone="bad">${escapeHtml(message)}</p>
`;

export const renderProjectFileOpenResult = (result: ProjectFileOpenResult): string => {
  const preview = result.preview;
  let content = `<p class="muted">Metadata only. Binary or non-UTF-8 content is not transferred into LS GO.</p>`;
  if (preview.state === "empty") {
    content = `<p class="muted">The file is empty.</p>`;
  } else if (preview.state === "available") {
    content = `<pre>${escapeHtml(preview.text || "")}</pre>${preview.truncated ? `<small class="muted">Preview truncated at the governed byte limit.</small>` : ""}`;
  }
  return `
    <section class="project-file-preview">
      <div class="project-files-head"><strong>${escapeHtml(result.file.relative_path)}</strong><small>${escapeHtml(result.file.mime_type)} · ${formatBytes(result.file.size_bytes)}</small></div>
      ${content}
      <p class="project-file-boundary">${escapeHtml(result.boundary)}</p>
    </section>
  `;
};

export const bindProjectBrowseButtons = (
  mount: HTMLElement,
  handler: ProjectBrowseHandler,
): void => {
  mount.querySelectorAll<HTMLButtonElement>("[data-project-files]").forEach((button) => {
    button.addEventListener("click", () => {
      const projectId = button.dataset.projectFiles || "";
      if (projectId) void handler(projectId, button);
    });
  });
};

export const bindProjectFileOpenButtons = (
  mount: HTMLElement,
  handler: ProjectFileOpenHandler,
): void => {
  mount.querySelectorAll<HTMLButtonElement>("[data-project-file][data-project-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const projectId = button.dataset.projectId || "";
      const relativePath = button.dataset.projectFile || "";
      if (projectId && relativePath) void handler(projectId, relativePath, button);
    });
  });
};
