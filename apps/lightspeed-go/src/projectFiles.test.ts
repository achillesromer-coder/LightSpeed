import { describe, expect, it } from "vitest";
import type { ProjectFileOpenResult, ProjectFilesResponse, ProjectRecord } from "./desktopBridge";
import {
  bindProjectBrowseButtons,
  bindProjectFileOpenButtons,
  renderProjectCards,
  renderProjectFileOpenResult,
  renderProjectFiles,
  renderProjectFilesError,
} from "./projectFiles";

const project: ProjectRecord = {
  project_id: "project-alpha-a1b2c3d4",
  name: "Project Alpha",
  path: "not-rendered",
  authority: "canonical",
  condition: "active",
  file_count: 2,
  size_bytes: 42,
};

const listing: ProjectFilesResponse = {
  schema_version: "lightspeed-project-files-v1",
  state: "available",
  project,
  files: [{
    relative_path: "results/sweep.json",
    name: "sweep.json",
    extension: ".json",
    mime_type: "application/json",
    kind: "text",
    size_bytes: 42,
    preview_supported: true,
  }],
  summary: {
    visible_file_count: 1,
    blocked_file_count: 1,
    skipped_file_count: 0,
    scanned_file_count: 2,
    scan_truncated: false,
    limit: 200,
  },
  boundary: "Read-only project-relative metadata.",
};

type FakeButton = {
  dataset: Record<string, string>;
  addEventListener: (name: string, listener: () => void) => void;
  click: () => void;
};

const fakeButton = (dataset: Record<string, string>): FakeButton => {
  let listener: () => void = () => undefined;
  return {
    dataset,
    addEventListener: (_name, next) => { listener = next; },
    click: () => listener(),
  };
};

const fakeMount = (buttons: FakeButton[]): HTMLElement => ({
  querySelectorAll: () => buttons,
}) as unknown as HTMLElement;

describe("LightSpeed Go project file browser", () => {
  it("renders and binds a project file action without exposing the project path", () => {
    const html = renderProjectCards([project]);
    expect(html).toContain('data-project-files="project-alpha-a1b2c3d4"');
    expect(html).toContain(">Files</button>");
    expect(html).not.toContain("not-rendered");

    const button = fakeButton({ projectFiles: project.project_id });
    const calls: string[] = [];
    bindProjectBrowseButtons(fakeMount([button]), (projectId) => { calls.push(projectId); });
    button.click();
    expect(calls).toEqual([project.project_id]);
  });

  it("binds file-open clicks to the exact project-relative file", () => {
    const html = renderProjectFiles(listing);
    expect(html).toContain('data-project-file="results/sweep.json"');
    expect(html).toContain("1 withheld");

    const button = fakeButton({
      projectId: project.project_id,
      projectFile: "results/sweep.json",
    });
    const calls: string[][] = [];
    bindProjectFileOpenButtons(
      fakeMount([button]),
      (projectId, relativePath) => { calls.push([projectId, relativePath]); },
    );
    button.click();
    expect(calls).toEqual([[project.project_id, "results/sweep.json"]]);
  });

  it("renders explicit empty, restricted and error states", () => {
    const empty = renderProjectFiles({ ...listing, state: "empty", files: [] });
    const restricted = renderProjectFiles({ ...listing, state: "restricted", files: [] });
    const error = renderProjectFilesError("Desktop returned HTTP 503 <held>");
    expect(empty).toContain("currently has no visible files");
    expect(restricted).toContain("credential-like or excluded runtime files are withheld");
    expect(error).toContain("Files unavailable");
    expect(error).toContain("&lt;held&gt;");
  });

  it("escapes a bounded preview and labels the read-only result", () => {
    const result: ProjectFileOpenResult = {
      schema_version: "lightspeed-project-file-open-result-v1",
      state: "opened_read_only",
      project,
      file: listing.files[0],
      preview: {
        state: "available",
        encoding: "utf-8",
        truncated: false,
        text: '<script data-test="no">unsafe</script>',
      },
      source_mutated: false,
      boundary: "Read-only bounded preview.",
    };
    const html = renderProjectFileOpenResult(result);
    expect(html).toContain("&lt;script data-test=&quot;no&quot;&gt;");
    expect(html).not.toContain("<script");
    expect(html).toContain("Read-only bounded preview.");
  });
});
