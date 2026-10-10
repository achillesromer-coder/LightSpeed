import type { ComponentAtlasRecord } from "./objectReview";

const esc=(value:string):string=>value
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
  .replace(/"/g,"&quot;").replace(/'/g,"&apos;");

const lines=(value:string|undefined,max=58,limit=5):string[]=>{
  const text=(value || "UNRESOLVED").replace(/\s+/g," ").trim();
  const words=text.split(" "); const out:string[]=[]; let line="";
  for(const word of words){
    const next=(line+" "+word).trim();
    if(next.length>max && line){out.push(line);line=word;} else line=next;
    if(out.length>=limit) break;
  }
  if(out.length<limit && line) out.push(line);
  return out.slice(0,limit);
};

const textBlock=(x:number,y:number,label:string,value:string|undefined,width=58):string=>{
  const body=lines(value,width,4);
  return `<g transform="translate(${x} ${y})"><text class="kicker" x="0" y="0">${esc(label)}</text>${body.map((line,i)=>`<text class="body" x="0" y="${54+i*44}">${esc(line)}</text>`).join("")}</g>`;
};

const motif=(record:ComponentAtlasRecord):string=>{
  const key=[record.Domain,record.Family,record["Component Archetype"],record["Primary Physics"]].filter(Boolean).join(" ").toLowerCase();
  if(key.includes("diode")||key.includes("semiconductor")){
    return `<g class="motif"><rect x="1330" y="650" width="1180" height="700" rx="80" class="shell"/><path d="M1550 1000h310l220-180v360l-220-180h-310M2080 820v360M2080 1000h290" class="active"/><circle cx="1550" cy="1000" r="34" class="port"/><circle cx="2370" cy="1000" r="34" class="port"/></g>`;
  }
  if(key.includes("resistor")||key.includes("resistive")){
    return `<g class="motif"><path d="M1450 1000h180l90-150 130 300 130-300 130 300 130-300 130 300 90-150h180" class="active"/><rect x="1330" y="710" width="1180" height="580" rx="80" class="shell"/></g>`;
  }
  if(key.includes("capacitor")||key.includes("capacitive")||key.includes("dielectric")){
    return `<g class="motif"><rect x="1540" y="720" width="180" height="560" rx="25" class="active fill"/><rect x="2120" y="720" width="180" height="560" rx="25" class="active fill"/><rect x="1780" y="760" width="280" height="480" rx="35" class="dielectric"/><path d="M1380 1000h160M2300 1000h160" class="active"/></g>`;
  }
  if(key.includes("inductor")||key.includes("coil")||key.includes("solenoid")||key.includes("magnetic")){
    return `<g class="motif"><path d="M1370 1000h170c0-170 230-170 230 0s230 170 230 0 230-170 230 0 230 170 230 0h160" class="active"/><rect x="1500" y="690" width="850" height="620" rx="150" class="shell"/></g>`;
  }
  if(key.includes("rf")||key.includes("antenna")||key.includes("resonator")){
    return `<g class="motif"><ellipse cx="1920" cy="1000" rx="650" ry="390" class="active"/><ellipse cx="1920" cy="1000" rx="450" ry="250" class="shell"/><path d="M1920 1390v210M1920 1600h430" class="active"/><path d="M1550 1000c180-180 560-180 740 0M1610 1110c150-120 470-120 620 0" class="field"/></g>`;
  }
  if(key.includes("fluid")||key.includes("channel")||key.includes("valve")||key.includes("pump")){
    return `<g class="motif"><rect x="1350" y="730" width="1140" height="540" rx="160" class="shell"/><path d="M1450 1000h330c90 0 120-170 210-170s120 340 210 340 120-170 210-170h160" class="fluid"/><circle cx="1920" cy="1000" r="120" class="active"/></g>`;
  }
  if(key.includes("optical")||key.includes("photon")||key.includes("laser")||key.includes("led")){
    return `<g class="motif"><rect x="1400" y="800" width="1040" height="400" rx="80" class="shell"/><path d="M1470 1000c220-260 420 260 640 0s420 260 640 0" class="optical"/><path d="M1560 780l-90-170M1710 800l-20-190M2280 800l100-170" class="field"/></g>`;
  }
  if(key.includes("mechanical")||key.includes("structure")||key.includes("frame")||key.includes("lattice")){
    return `<g class="motif"><rect x="1390" y="720" width="1060" height="560" rx="50" class="shell"/><path d="M1390 720l1060 560M2450 720L1390 1280M1390 1000h1060M1920 720v560" class="active"/></g>`;
  }
  if(key.includes("energy")||key.includes("battery")||key.includes("electrochemical")){
    return `<g class="motif"><rect x="1460" y="720" width="920" height="560" rx="70" class="shell"/><rect x="1550" y="810" width="180" height="380" class="active fill"/><rect x="1810" y="810" width="220" height="380" class="dielectric"/><rect x="2110" y="810" width="180" height="380" class="active fill"/><path d="M2290 880h180v240h-180" class="active"/></g>`;
  }
  return `<g class="motif"><rect x="1390" y="720" width="1060" height="560" rx="90" class="shell"/><circle cx="1920" cy="1000" r="250" class="active"/><path d="M1390 1000h280M2170 1000h280M1920 720v180M1920 1100v180" class="field"/></g>`;
};

export const componentPlateSvg=(record:ComponentAtlasRecord):string=>`<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160">
<defs>
  <radialGradient id="bg" cx="56%" cy="43%" r="80%"><stop offset="0" stop-color="#173033"/><stop offset=".55" stop-color="#0c191b"/><stop offset="1" stop-color="#050a0b"/></radialGradient>
  <filter id="glow"><feGaussianBlur stdDeviation="12" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<style>
  .title{font:700 92px Inter,Segoe UI,sans-serif;fill:#f2ede7;letter-spacing:-2px}.sub{font:500 36px Inter,Segoe UI,sans-serif;fill:#aab9b8}.kicker{font:700 24px Inter,Segoe UI,sans-serif;fill:#55d6cf;letter-spacing:3px}.body{font:500 30px Inter,Segoe UI,sans-serif;fill:#f2ede7}.mono{font:500 27px ui-monospace,SFMono-Regular,Consolas,monospace;fill:#aab9b8}.active{fill:none;stroke:#55d6cf;stroke-width:26;stroke-linecap:round;stroke-linejoin:round}.fill{fill:#123a3b;stroke:#55d6cf}.shell{fill:#0f1b1c;stroke:#294043;stroke-width:12}.dielectric{fill:#c8a45822;stroke:#c8a458;stroke-width:16}.field{fill:none;stroke:#c8a458;stroke-width:13;stroke-dasharray:26 22}.fluid{fill:none;stroke:#76d39b;stroke-width:30;stroke-linecap:round}.optical{fill:none;stroke:#e9d28d;stroke-width:22;filter:url(#glow)}.port{fill:#071011;stroke:#c8a458;stroke-width:16}.warn{font:700 24px Inter,Segoe UI,sans-serif;fill:#e27e7e;letter-spacing:2px}
</style>
<rect width="3840" height="2160" fill="url(#bg)"/>
<g opacity=".22" stroke="#294043" stroke-width="2">${Array.from({length:25},(_,i)=>`<path d="M${i*160} 0v2160"/>`).join("")}${Array.from({length:15},(_,i)=>`<path d="M0 ${i*160}h3840"/>`).join("")}</g>
<text x="180" y="180" class="kicker">RÖMER / COGNIGREX · CGX COMPONENT REVIEW</text>
<text x="180" y="305" class="title">${esc(record["Component Archetype"] || record.ID)}</text>
<text x="180" y="380" class="sub">${esc(record.ID)} · ${esc(record.Domain || "UNRESOLVED DOMAIN")} · ${esc(record.Family || "UNRESOLVED FAMILY")}</text>
<text x="3660" y="180" text-anchor="end" class="warn">SYMBOLIC 4K PLATE · NOT RELEASED GEOMETRY</text>
${motif(record)}
<g transform="translate(180 540)">
  ${textBlock(0,0,"PRIMARY FUNCTION",record["Primary Function"],50)}
  ${textBlock(0,330,"BUILD CLASS / ROUTE",`${record["Current CGX Build Class"] || ""} · ${record["Current Manufacturing Route"] || ""}`,50)}
  ${textBlock(0,660,"BASELINE GEOMETRY",record["Baseline Geometry"],50)}
  ${textBlock(0,990,"GEOMETRIC PARAMETERS",record["Geometric Parameters"],50)}
</g>
<g transform="translate(2720 540)">
  ${textBlock(0,0,"PHYSICS / MODEL",`${record["Primary Physics"] || ""} · ${record["Baseline Model / Equation"] || ""}`,47)}
  ${textBlock(0,330,"MATERIAL STACK",record["Typical Material Stack"],47)}
  ${textBlock(0,660,"INTERFACES / 4D",`${record["Ports / Interfaces"] || ""} · ${record["4D Fields"] || ""}`,47)}
  ${textBlock(0,990,"TEST / FAILURE",`${record["Acceptance Tests"] || ""} · ${record["Failure Modes"] || ""}`,47)}
</g>
<rect x="180" y="1960" width="3480" height="90" rx="24" fill="#0f1b1c" stroke="#294043" stroke-width="4"/>
<text x="225" y="2018" class="mono">EVIDENCE: ${esc(record["Evidence State"] || "UNRESOLVED")} · AUTHORITY: ${esc(record["Source Authority Class"] || "UNRESOLVED")} · SCALE: ${esc(record["Scale Band"] || "UNRESOLVED")}</text>
<text x="225" y="2085" class="mono">Visual form is corpus-derived symbolic topology. Exact CGXI/source/lot/geometry/process/tool/calibration/test evidence governs realization.</text>
</svg>`;

export const openComponentPlate=(record:ComponentAtlasRecord):void=>{
  const svg=componentPlateSvg(record);
  const blob=new Blob([svg],{type:"image/svg+xml"});
  const url=URL.createObjectURL(blob);
  const win=window.open(url,"_blank","noopener,noreferrer");
  if(!win) URL.revokeObjectURL(url);
  else window.setTimeout(()=>URL.revokeObjectURL(url),60_000);
};

export const componentPlateButtonMarkup=(id:string):string=>
  `<button type="button" class="button-secondary component-plate-trigger" data-component-id="${esc(id)}">4K symbolic</button>`;

export const bindComponentPlateTriggers=(root:HTMLElement,records:ComponentAtlasRecord[]):void=>{
  const byId=new Map(records.map((record)=>[record.ID,record]));
  root.querySelectorAll<HTMLButtonElement>(".component-plate-trigger").forEach((button)=>{
    button.addEventListener("click",()=>{
      const record=byId.get(button.dataset.componentId || "");
      if(record) openComponentPlate(record);
    });
  });
};
