export type MeshReviewGeometry = {
  schema: string;
  id: string;
  source: string;
  source_sha256: string;
  state: string;
  units: string;
  bounds: { min: number[]; max: number[]; extents: number[] };
  vertices: number[][];
  faces: number[][];
};

type MeshViewerOptions = {
  url: string;
  label: string;
  source: string;
  sourceHash?: string;
  physicalState: string;
};

const esc = (value: string): string => value
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

const cross = (a:number[], b:number[]):number[] => [
  a[1]*b[2]-a[2]*b[1],
  a[2]*b[0]-a[0]*b[2],
  a[0]*b[1]-a[1]*b[0],
];
const sub = (a:number[], b:number[]):number[] => [a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const length = (a:number[]):number => Math.hypot(a[0],a[1],a[2]) || 1;
const unit = (a:number[]):number[] => { const n=length(a); return [a[0]/n,a[1]/n,a[2]/n]; };
const dot = (a:number[],b:number[]):number => a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const clamp=(v:number,lo=0,hi=1):number=>Math.max(lo,Math.min(hi,v));

const rotate=(p:number[],elev:number,azim:number):number[]=>{
  const e=elev*Math.PI/180,a=azim*Math.PI/180;
  const x=p[0]*Math.cos(a)-p[1]*Math.sin(a);
  const y=p[0]*Math.sin(a)+p[1]*Math.cos(a);
  const z=p[2];
  return [x,y*Math.cos(e)-z*Math.sin(e),y*Math.sin(e)+z*Math.cos(e)];
};

const mix=(a:number[],b:number[],t:number):number[] => a.map((v,i)=>Math.round(v+(b[i]-v)*t));
const cssRgb=(v:number[]):string => `rgb(${v[0]},${v[1]},${v[2]})`;

const renderMesh = (
  canvas: HTMLCanvasElement,
  mesh: MeshReviewGeometry,
  state: { elev:number; azim:number; zoom:number },
): void => {
  const ctx=canvas.getContext("2d");
  if(!ctx) return;
  const dpr=Math.min(window.devicePixelRatio || 1,2);
  const cssW=Math.max(canvas.clientWidth,320), cssH=Math.max(canvas.clientHeight,320);
  const pxW=Math.round(cssW*dpr),pxH=Math.round(cssH*dpr);
  if(canvas.width!==pxW || canvas.height!==pxH){canvas.width=pxW;canvas.height=pxH;}
  ctx.setTransform(dpr,0,0,dpr,0,0);
  const w=cssW,h=cssH;
  ctx.clearRect(0,0,w,h);

  const grad=ctx.createRadialGradient(w*.58,h*.42,20,w*.55,h*.45,Math.max(w,h)*.75);
  grad.addColorStop(0,"#173033");grad.addColorStop(.55,"#0c191b");grad.addColorStop(1,"#050a0b");
  ctx.fillStyle=grad;ctx.fillRect(0,0,w,h);
  ctx.strokeStyle="rgba(41,64,67,.25)";ctx.lineWidth=1;
  const grid=48;
  for(let x=0;x<w;x+=grid){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke();}
  for(let y=0;y<h;y+=grid){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}

  const rv=mesh.vertices.map((p)=>rotate(p,state.elev,state.azim));
  let minx=Infinity,maxx=-Infinity,miny=Infinity,maxy=-Infinity,minz=Infinity,maxz=-Infinity;
  for(const p of rv){minx=Math.min(minx,p[0]);maxx=Math.max(maxx,p[0]);miny=Math.min(miny,p[1]);maxy=Math.max(maxy,p[1]);minz=Math.min(minz,p[2]);maxz=Math.max(maxz,p[2]);}
  const dx=Math.max(maxx-minx,1e-9),dy=Math.max(maxy-miny,1e-9),dz=Math.max(maxz-minz,1e-9);
  const scale=Math.min((w*.78)/dx,(h*.72)/dy)*state.zoom;
  const cx=w*.53,cy=h*.53,cam=Math.max(dx,dy,dz)*7.5;
  const pts=rv.map((p)=>{
    const z=p[2]-(minz+maxz)/2;
    const persp=cam/(cam-z);
    return [cx+(p[0]-(minx+maxx)/2)*scale*persp,cy-(p[1]-(miny+maxy)/2)*scale*persp,p[2]];
  });

  const key=unit([-0.45,-0.35,0.82]),fill=unit([0.6,-0.2,0.5]),rim=unit([0.25,0.8,0.5]);
  const faces=mesh.faces.map((t)=>{
    const A=rv[t[0]],B=rv[t[1]],C=rv[t[2]];
    const n=unit(cross(sub(B,A),sub(C,A)));
    const z=(A[2]+B[2]+C[2])/3;
    let intensity=.16+.58*Math.abs(dot(n,key))+.16*Math.abs(dot(n,fill))+.1*Math.abs(dot(n,rim));
    return {t,z,intensity:clamp(intensity,.12,1)};
  }).sort((a,b)=>a.z-b.z);

  ctx.save();
  ctx.shadowColor="rgba(0,0,0,.4)";ctx.shadowBlur=24;
  ctx.fillStyle="rgba(0,0,0,.3)";
  ctx.beginPath();ctx.ellipse(cx,h*.82,Math.min(w*.27,380)*state.zoom,Math.max(20,h*.035)*state.zoom,0,0,Math.PI*2);ctx.fill();
  ctx.restore();

  const dark=[17,38,41],light=[92,222,214],gold=[200,164,88];
  const step=Math.max(1,Math.ceil(faces.length/9000));
  for(let i=0;i<faces.length;i+=step){
    const {t,intensity}=faces[i],A=pts[t[0]],B=pts[t[1]],C=pts[t[2]];
    let color=mix(dark,light,intensity);
    if(intensity>.82) color=mix(color,gold,.12);
    ctx.beginPath();ctx.moveTo(A[0],A[1]);ctx.lineTo(B[0],B[1]);ctx.lineTo(C[0],C[1]);ctx.closePath();
    ctx.fillStyle=cssRgb(color);ctx.fill();
    ctx.strokeStyle="rgba(120,227,221,.15)";ctx.lineWidth=.55;ctx.stroke();
  }

  ctx.fillStyle="#aab9b8";ctx.font="12px ui-monospace, SFMono-Regular, Consolas, monospace";
  ctx.fillText(`az ${state.azim.toFixed(0)}° · el ${state.elev.toFixed(0)}° · zoom ${state.zoom.toFixed(2)}×`,16,h-18);
};

const modalMarkup=():string=>`
  <div class="mesh-viewer-dialog" role="dialog" aria-modal="true" aria-label="Interactive source mesh review">
    <div class="mesh-viewer-head">
      <div><p class="eyebrow">source-hashed interactive geometry</p><h3 data-mesh-title>Object</h3></div>
      <button type="button" class="mesh-viewer-close" aria-label="Close interactive mesh">×</button>
    </div>
    <div class="mesh-viewer-canvas-wrap"><canvas class="mesh-viewer-canvas"></canvas></div>
    <div class="mesh-viewer-foot">
      <div><strong data-mesh-state>REVIEW ONLY</strong><small data-mesh-source></small><small data-mesh-hash></small></div>
      <div class="mesh-viewer-help">Drag to orbit · wheel to zoom · double-click to reset</div>
    </div>
  </div>`;

let modal:HTMLElement | null=null;
let abort:AbortController | null=null;

const ensureModal=():HTMLElement=>{
  if(modal) return modal;
  modal=document.createElement("div");
  modal.className="mesh-viewer-modal";
  modal.hidden=true;
  modal.innerHTML=modalMarkup();
  document.body.append(modal);
  const close=():void=>{ if(!modal) return; modal.hidden=true; abort?.abort(); abort=null; document.body.classList.remove("mesh-viewer-open"); };
  modal.querySelector(".mesh-viewer-close")?.addEventListener("click",close);
  modal.addEventListener("click",(event)=>{if(event.target===modal) close();});
  window.addEventListener("keydown",(event)=>{if(event.key==="Escape" && modal && !modal.hidden) close();});
  return modal;
};

export const openMeshViewer=async(options:MeshViewerOptions):Promise<void>=>{
  const host=ensureModal();
  abort?.abort();abort=new AbortController();
  host.hidden=false;document.body.classList.add("mesh-viewer-open");
  const title=host.querySelector<HTMLElement>("[data-mesh-title]");
  const stateEl=host.querySelector<HTMLElement>("[data-mesh-state]");
  const source=host.querySelector<HTMLElement>("[data-mesh-source]");
  const hash=host.querySelector<HTMLElement>("[data-mesh-hash]");
  const canvas=host.querySelector<HTMLCanvasElement>(".mesh-viewer-canvas");
  if(!canvas) return;
  if(title) title.textContent=options.label;
  if(stateEl) stateEl.textContent=options.physicalState;
  if(source) source.textContent=options.source;
  if(hash) hash.textContent=options.sourceHash ? `source SHA-256 ${options.sourceHash}` : "source hash in mesh payload";
  const ctx=canvas.getContext("2d");if(ctx){ctx.fillStyle="#071011";ctx.fillRect(0,0,canvas.width,canvas.height);}

  let mesh:MeshReviewGeometry;
  try{
    const response=await fetch(options.url,{cache:"no-store",signal:abort.signal});
    if(!response.ok) throw new Error(`mesh payload HTTP ${response.status}`);
    mesh=await response.json() as MeshReviewGeometry;
  }catch(error){
    if((error as Error).name==="AbortError") return;
    if(ctx){ctx.fillStyle="#e27e7e";ctx.font="16px sans-serif";ctx.fillText("Interactive mesh unavailable.",20,36);}
    return;
  }

  const state={elev:22,azim:-38,zoom:1};
  let dragging=false,lastX=0,lastY=0,frame=0;
  const draw=():void=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>renderMesh(canvas,mesh,state));};
  const reset=():void=>{state.elev=22;state.azim=-38;state.zoom=1;draw();};
  const onDown=(event:PointerEvent):void=>{dragging=true;lastX=event.clientX;lastY=event.clientY;canvas.setPointerCapture(event.pointerId);};
  const onMove=(event:PointerEvent):void=>{
    if(!dragging) return;
    const dx=event.clientX-lastX,dy=event.clientY-lastY;lastX=event.clientX;lastY=event.clientY;
    state.azim+=dx*.35;state.elev=Math.max(-85,Math.min(85,state.elev+dy*.28));draw();
  };
  const onUp=():void=>{dragging=false;};
  const onWheel=(event:WheelEvent):void=>{event.preventDefault();state.zoom=Math.max(.35,Math.min(4,state.zoom*Math.exp(-event.deltaY*.001)));draw();};
  canvas.onpointerdown=onDown;canvas.onpointermove=onMove;canvas.onpointerup=onUp;canvas.onpointercancel=onUp;canvas.onwheel=onWheel;canvas.ondblclick=reset;
  new ResizeObserver(draw).observe(canvas);
  draw();
};

export const meshViewerButtonMarkup=(options:MeshViewerOptions):string=>`
  <button type="button" class="button-secondary mesh-viewer-trigger"
    data-mesh-url="${esc(options.url)}"
    data-mesh-label="${esc(options.label)}"
    data-mesh-source="${esc(options.source)}"
    data-mesh-hash="${esc(options.sourceHash || "")}"
    data-mesh-state="${esc(options.physicalState)}">Interactive 3D</button>`;

export const bindMeshViewerTriggers=(root:HTMLElement):void=>{
  root.querySelectorAll<HTMLButtonElement>(".mesh-viewer-trigger").forEach((button)=>{
    button.addEventListener("click",()=>void openMeshViewer({
      url:button.dataset.meshUrl || "",
      label:button.dataset.meshLabel || "Object",
      source:button.dataset.meshSource || "",
      sourceHash:button.dataset.meshHash || "",
      physicalState:button.dataset.meshState || "REVIEW ONLY",
    }));
  });
};
