import { describe, expect, it, vi, afterEach } from "vitest";
import { privateReviewApiPath, privateReviewFileFromLegacyPath, PrivateObjectReviewSession } from "./privateObjectReview";
import { renderObjectReview, type ComponentAtlas, type ObjectReviewCatalogue } from "./objectReview";

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

const sampleManifest: ObjectReviewCatalogue = {
  schema:"test",generated_from_git:"fixture",status:"INTERNAL_REVIEW",authority:"owner",
  visual_system:{palette:{},rule:"No public source",render_plate:"svg"},
  coverage:{printable_4d_archetypes:1,macro_source_meshes:1,symbolic_core_component_stack_plates:1,physical_tests_complete:0},
  tiers:[],
  micro_review_objects:[{id:"D1",label:"Diode",role:"part",level:"micro",source:"fixture",
    render:"/review/renders/diode_review.svg",geometry_state:"UNKNOWN",
    physical_state:"NOT_RUN",review_rules:[]}],
  macro_review_objects:[{id:"M1",label:"Luke",role:"system",level:"macro",source:"fixture",
    render:"/review/renders/luke_review.svg",hero_render:"/review/renders/luke_hero.svg",
    mesh_data:"/review/mesh/luke.json",geometry_state:"DIGITAL",
    physical_state:"NOT_BUILT",review_rules:[]}],
  atlas_ref:"/data/component_geometry_atlas_public_review.json",pending_owner_layers:[],boundary:"No promotion"
};
const atlas:ComponentAtlas={schema:"test",status:"held",record_count:1,records:[{ID:"D1"}]};

describe("private CGX Objects access", () => {
  it("requires exact known paths and rejects URL escape or unapproved format", () => {
    expect(privateReviewApiPath("/data/cgx_object_review_catalogue.json"))
      .toBe("/api/v1/private-object-review/catalogue/cgx_object_review_catalogue.json");
    expect(privateReviewApiPath("/review/mesh/luke.json"))
      .toBe("/api/v1/private-object-review/mesh/luke.json");
    for (const bad of ["/review/mesh/../private.json","/review/renders/luke.json",
      "https://example.org/review/mesh/luke.json","/review/mesh/luke.json?token=secret",
      "/review/mesh/%2e%2e.json","/review/renders/luke.svg#query","/data/other.json"]) {
      expect(() => privateReviewFileFromLegacyPath(bad)).toThrow();
    }
  });
  it("renders a safe gallery: no raw static image requests or anchor links", () => {
    const html=renderObjectReview(sampleManifest,atlas,true);
    expect(html).toContain('data-private-render="/review/renders/diode_review.svg"');
    expect(html).toContain('data-private-open="/review/renders/luke_hero.svg"');
    expect(html).toContain("Interactive 3D");
    expect(html).not.toContain('src="/review/');
    expect(html).not.toContain('href="/review/');
    expect(html).not.toContain('src="/data/');
    expect(html).not.toContain('href="/data/');
    expect(html).toContain("NOT_BUILT");
  });
  it("cannot fetch private bytes without an owner session",()=>{
    expect(() => new PrivateObjectReviewSession("")).toThrow("Owner session");
  });
  it("passes owner header, no credentials, and checks exact source digest", async () => {
    const payload=new TextEncoder().encode('{"records":[],"record_count":0}');
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",payload)),
      x=>x.toString(16).padStart(2,"0")).join("");
    const fetcher=vi.fn(async (_url:string,_init:RequestInit)=>new Response(payload,{
      status:200,headers:{"Content-Type":"application/json","X-CGX-Source-SHA256":digest}
    }));
    vi.stubGlobal("fetch",fetcher);
    const session=new PrivateObjectReviewSession("owner-fake-credential","http://127.0.0.1:8765");
    const data=await session.readJson<{record_count:number}>("/data/cgx_object_review_catalogue.json");
    expect(data.record_count).toBe(0);
    const [url,init]=fetcher.mock.calls[0] as [string,RequestInit];
    expect(url).toContain("/api/v1/private-object-review/catalogue/");
    expect((init.headers as Record<string,string>)["X-LightSpeed-Session"]).toBe("owner-fake-credential");
    expect(init.credentials).toBe("omit");
    expect(init.cache).toBe("no-store");
    expect(init.redirect).toBe("error");
    session.revoke();
    await expect(session.readJson("/data/cgx_object_review_catalogue.json")).rejects.toThrow();
  });
  it("fails closed on revoked HTTP, wrong content digest or missing digest", async () => {
    const payload=new TextEncoder().encode("{}");
    let state=0;
    vi.stubGlobal("fetch",vi.fn(async()=>{
      state++;
      if (state===1) return new Response("denied",{status:403});
      return new Response(payload,{status:200,headers:{
        "Content-Type":"application/json",
        ...(state===2?{"X-CGX-Source-SHA256":"f".repeat(64)}:{})
      }});
    }));
    const session=new PrivateObjectReviewSession("owner","http://127.0.0.1:8765");
    for(let i=0;i<3;i++)await expect(session.read("/data/cgx_object_review_catalogue.json")).rejects.toThrow();
    session.revoke();
  });
  it("creates a verified temporary SVG Blob URL and revokes it on owner logout", async () => {
    const path="/review/renders/diode_review.svg";
    const payload=new TextEncoder().encode('<svg xmlns="http://www.w3.org/2000/svg"></svg>');
    const digest=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",payload)),
      x=>x.toString(16).padStart(2,"0")).join("");
    const fetcher=vi.fn(async()=>new Response(payload,{status:200,headers:{
      "Content-Type":"image/svg+xml","X-CGX-Source-SHA256":digest
    }}));
    vi.stubGlobal("fetch",fetcher);
    const create=vi.spyOn(URL,"createObjectURL").mockReturnValue("blob:owner-review-test");
    const revoke=vi.spyOn(URL,"revokeObjectURL").mockImplementation(()=>{});
    const session=new PrivateObjectReviewSession("owner","http://127.0.0.1:8765");
    expect(await session.blobUrl(path)).toBe("blob:owner-review-test");
    expect(await session.blobUrl(path)).toBe("blob:owner-review-test");
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(create).toHaveBeenCalledTimes(1);
    session.revoke();
    expect(revoke).toHaveBeenCalledExactlyOnceWith("blob:owner-review-test");
    await expect(session.blobUrl(path)).rejects.toThrow("closed");
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it("aborts in-flight private request on logout before data is hydrated", async()=>{
    let captured:AbortSignal|undefined;
    vi.stubGlobal("fetch",vi.fn(async (_url:string,init:RequestInit)=>{
      captured=init.signal as AbortSignal;
      return await new Promise<Response>((_resolve,reject)=>{
        captured?.addEventListener("abort",()=>reject(new DOMException("Aborted","AbortError")),{once:true});
      });
    }));
    const session=new PrivateObjectReviewSession("owner","http://127.0.0.1:8765");
    const result=session.read("/review/mesh/luke.json");
    session.revoke();
    await expect(result).rejects.toThrow();
    expect(captured?.aborted).toBe(true);
  });
});
