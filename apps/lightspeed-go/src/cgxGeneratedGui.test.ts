import { describe, expect, it } from "vitest";
import source from "../../../docs/architecture/CGX_UNISPACE_GO_FIVE_FACET_INTERFACE_20261122.json?raw";
import {
  compileCgxGeneratedGui, renderCgxGeneratedGuiMarkup,
  CgxInterfaceHold, CGX_GENERATED_GUI_ROOT,
} from "./cgxGeneratedGui";

const fixture = (): any => JSON.parse(source);
const reject = (change: (body: any) => void, code?: string): void => {
  const input = fixture();
  change(input);
  expect(() => compileCgxGeneratedGui(input)).toThrow(CgxInterfaceHold);
  if (code) expect(() => compileCgxGeneratedGui(input)).toThrow(code);
};

describe("Generated CGX FileSpace GUI compiler, not native admission", () => {
  it("compiles exactly the existing owner-reviewed Interface Studio candidate", () => {
    const plan = compileCgxGeneratedGui(source);
    expect(plan.parent).toBe(CGX_GENERATED_GUI_ROOT);
    expect(plan.panels.map((p) => p.facet)).toEqual([
      "file_space", "data_space", "social_space", "print_space", "intelligence_space",
    ]);
    expect(plan.panels.map((p) => p.workspace)).toEqual([
      "filespace", "sources", "activity", "objects", "command",
    ]);
    expect(plan.state).toBe("SOURCE_PROJECTION_ONLY");
    expect(plan.nativeAdmitted).toBe(false);
    expect(plan.hostAuthenticated).toBe(false);
    expect(plan.publicPublished).toBe(false);
    expect(plan.privateBytesIncluded).toBe(false);
    expect(plan.handlersBound).toBe(false);
    expect(Object.isFrozen(plan)).toBe(true);
    expect(Object.isFrozen(plan.panels)).toBe(true);
  });
  it("outputs five accessible generated facet tabs and bounded source cards", () => {
    const markup = renderCgxGeneratedGuiMarkup(compileCgxGeneratedGui(source));
    expect(markup.match(/role="tab"/g)).toHaveLength(5);
    expect(markup).toContain('data-cgx-gui-open="filespace"');
    expect(markup).toContain("native admission");
    expect(markup).not.toContain("<script");
    expect(markup).not.toContain("fetch(");
    expect(markup).not.toContain("mint");
  });
  it("renders a different selected facet without changing underlying rights", () => {
    const plan = compileCgxGeneratedGui(source);
    const markup = renderCgxGeneratedGuiMarkup(plan, "view-3");
    expect(markup).toContain('data-cgx-gui-open="objects"');
    expect(markup).toContain("PrintSpace");
    expect(markup).not.toContain('data-cgx-gui-open="filespace"');
    expect(plan.nativeAdmitted).toBe(false);
  });
  it("defaults unknown selected view to bounded first layout", () => {
    const plan = compileCgxGeneratedGui(source);
    expect(renderCgxGeneratedGuiMarkup(plan, "__proto__")).toContain('data-cgx-gui-open="filespace"');
  });
  it("rejects raw malformed JSON and oversized source", () => {
    expect(() => compileCgxGeneratedGui("{bad")).toThrow("CGX_GUI_INVALID_JSON");
    expect(() => compileCgxGeneratedGui("x".repeat(32769))).toThrow("CGX_GUI_SOURCE_SIZE_HOLD");
  });
  it("requires exactly one canonical root and wrapper", () => {
    reject((x) => { x.design.parent = "cgx:root:competitor"; }, "CGX_GUI_CANONICAL_IDENTITY_HOLD");
    reject((x) => { x.design.schema = "cgx.unispace.interface/2"; }, "CGX_GUI_CANONICAL_IDENTITY_HOLD");
    reject((x) => { x.source_bytes = "SECRET"; }, "CGX_GUI_WRAPPER_HOLD");
  });
  it("denies privileged, unexpected controls and links", () => {
    reject((x) => { x.design.body.children[0].action = "publish"; }, "CGX_GUI_UNSUPPORTED_CONTROL_HOLD");
    reject((x) => { x.design.body.children[0].url = "https://secret.invalid"; });
    reject((x) => { x.design.body.children[0].type = "execute"; });
  });
  it("denies private data projections with wrong facet/dataset binding", () => {
    reject((x) => { x.design.body.children[0].dataset = "records"; }, "CGX_GUI_FACET_DATASET_MISMATCH");
    reject((x) => { x.design.body.children[0].facet = "private_space"; }, "CGX_GUI_COLLECTION_SHAPE_HOLD");
    reject((x) => { x.design.body.children[0].facet = ""; }, "CGX_GUI_UNSCOPED_PRIVATE_DATASET_HOLD");
  });
  it("rejects duplicate collection identities and dangerous IDs", () => {
    reject((x) => { x.design.body.children[1].id = x.design.body.children[0].id; }, "CGX_GUI_NODE_ID_OR_LABEL_HOLD");
    reject((x) => { x.design.body.children[0].id = "x\" onclick=\"alert(1)"; }, "CGX_GUI_NODE_ID_OR_LABEL_HOLD");
  });
  it("fails closed on empty, excessive and recursive group depth", () => {
    reject((x) => { x.design.body.children = []; }, "CGX_GUI_GROUP_SHAPE_HOLD");
    reject((x) => { x.design.body.children = Array.from({length:17}, () => ({ ...x.design.body.children[0] })); }, "CGX_GUI_GROUP_SHAPE_HOLD");
  });
  it("handles nested fractal groups with stable source-scoped panels", () => {
    const x = fixture();
    const first = x.design.body.children.shift();
    x.design.body.children.unshift({
      id:"group-file",type:"group",title:"FileSpace stack",layout:"grid",children:[first]
    });
    const plan = compileCgxGeneratedGui(x);
    expect(plan.panels[0].path).toEqual([x.design.body.title,"FileSpace stack"]);
    expect(plan.panels).toHaveLength(5);
  });
  it("rejects unlimited hydration and nonfinite limits", () => {
    reject((x) => { x.design.body.children[0].limit = 999999; }, "CGX_GUI_COLLECTION_SHAPE_HOLD");
    reject((x) => { x.design.body.children[0].limit = "18"; }, "CGX_GUI_COLLECTION_SHAPE_HOLD");
    reject((x) => { x.design.body.children[0].limit = NaN; }, "CGX_GUI_COLLECTION_SHAPE_HOLD");
  });
  it("rejects runtime script/protocol labels", () => {
    reject((x) => { x.design.title = "<svg onload=alert(1)>"; }, "CGX_GUI_CANONICAL_IDENTITY_HOLD");
    reject((x) => { x.design.body.children[0].query = "https://host/private"; }, "CGX_GUI_COLLECTION_SHAPE_HOLD");
  });
  it("accepts a generic unscoped workspace card without a new root", () => {
    const x = fixture();
    x.design.body.children.push({
      id:"view-7",type:"collection",title:"Card stack",
      dataset:"stacks",facet:"",kind:"",status:"",query:"",
      layout:"rows",limit:12
    });
    const plan = compileCgxGeneratedGui(x);
    expect(plan.panels[plan.panels.length - 1]?.workspace).toBeNull();
    expect(plan.panels).toHaveLength(6);
    expect(plan.parent).toBe(CGX_GENERATED_GUI_ROOT);
  });
  it("does not convert user-editable evidence status into native authority", () => {
    const x = fixture();
    x.design.body.children[0].status = "owner approved";
    const plan = compileCgxGeneratedGui(x);
    expect(plan.panels[0].status).toBe("owner approved");
    expect(plan.nativeAdmitted).toBe(false);
    expect(plan.publicPublished).toBe(false);
  });
  it("renders labels as escaped text, not trusted HTML", () => {
    const plan = compileCgxGeneratedGui(source);
    const markup = renderCgxGeneratedGuiMarkup(plan);
    expect(markup).toContain("Source-review only");
    expect(markup).not.toContain("contenteditable");
    expect(markup).not.toContain("<iframe");
    expect(markup).not.toContain("onerror=");
  });
});
