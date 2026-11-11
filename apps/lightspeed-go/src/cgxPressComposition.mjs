/** Declarative composition of local source facets. No executable handler or authority. */
export const SCHEMA='CGX-PRESS-COMPOSITION-REVIEW/0.1';
export const KINDS=['image','object','background','information','table','contract'];
export const MAX_BYTES=8*1024*1024;
const encoder=new TextEncoder();
const digest=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
const canon=x=>JSON.stringify(x,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])):v);
const exact=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).sort().join('|')===[...keys].sort().join('|');
const nameSafe=s=>typeof s==='string'&&s.length>0&&s.length<=180&&!/[\x00-\x1f/\\]/.test(s);
export function emptyComposition(){return {schema:SCHEMA,parent_ref:'Cognigrex.cgx',object_ref:'',title:'Untitled composition',catalogue:'',contract_type:'',notes:'',load_plan:null,assets:[],layers:[],native_mint:false,public_release:false,automatic_execution:false};}
export function suggestedKind(name,mime){return mime.startsWith('image/')?'image':/contract/i.test(name)?'contract':/\.csv$/i.test(name)?'table':/\.(txt|md)$/i.test(name)?'information':'object';}
export async function sourceAsset(name,mime,bytes){
 if(!nameSafe(name)||!(bytes instanceof Uint8Array)||!bytes.length||bytes.length>3*1024*1024)throw Error('Choose a named source file between 1 byte and 3 MiB.');
 let base64='';for(let i=0;i<bytes.length;i+=8192)base64+=String.fromCharCode(...bytes.subarray(i,i+8192));
 const hash=await digest(bytes);
 // Only raster signatures receive an image renderer; SVG/HTML/scripts remain inert references.
 const raster=bytes[0]===137&&bytes[1]===80&&bytes[2]===78&&bytes[3]===71?'image/png':bytes[0]===255&&bytes[1]===216?'image/jpeg':String.fromCharCode(...bytes.slice(0,6)).startsWith('GIF8')?'image/gif':String.fromCharCode(...bytes.slice(0,4))==='RIFF'&&String.fromCharCode(...bytes.slice(8,12))==='WEBP'?'image/webp':null;
 const text=/\.(txt|md|csv|json)$/i.test(name)&&bytes.length<=256*1024?new TextDecoder('utf-8',{fatal:true}).decode(bytes).slice(0,16000):'';
 return {id:hash,name,mime:raster||'application/octet-stream',size:bytes.length,base64:btoa(base64),text,handler:raster?'raster-preview':text?(/\.csv$/i.test(name)?'table-preview':/contract/i.test(name)?'contract-inspection':'text-inspection'):'reference-only',rights:'unverified'};
}
export function addAsset(composition,asset){
 const found=composition.assets.find(a=>a.id===asset.id);if(found)return {composition,duplicate:true,asset:found};
 if(composition.assets.length>=96)throw Error('This composition is limited to 96 distinct local sources.');
 if(composition.assets.reduce((n,a)=>n+a.size,0)+asset.size>MAX_BYTES)throw Error('This local composition is limited to 8 MiB of original source bytes.');
 return {composition:{...composition,assets:[...composition.assets,asset]},duplicate:false,asset};
}
export function addLayer(c,kind,assetId=null){
 if(!KINDS.includes(kind)||c.layers.length>=48||assetId&&!c.assets.some(a=>a.id===assetId))throw Error('Invalid layer or source reference.');
 const index=c.layers.reduce((n,l)=>Math.max(n,Number(l.id.slice(6))||0),0)+1;
 const asset=c.assets.find(a=>a.id===assetId);
 const layer={id:'layer-'+index,kind,name:asset?.name||kind,asset_id:assetId,parent_id:null,visible:true,x:kind==='background'?0:12,y:kind==='background'?0:12,width:kind==='background'?100:76,height:kind==='background'?100:60,opacity:100,color:kind==='background'?'#102536':'#eaf2f3',text:asset?.text?.slice(0,16000)||'',source_ref:'',rights:'unverified'};
 return {...c,layers:kind==='background'?[layer,...c.layers]:[...c.layers,layer]};
}
export function updateLayer(c,id,patch){
 const layer=c.layers.find(l=>l.id===id);if(!layer)throw Error('Layer not found.');
 const next={...layer,...patch};
 for(const k of ['x','y','width','height','opacity'])if(!Number.isFinite(next[k])||next[k]<0||next[k]>100||(['width','height'].includes(k)&&next[k]<5))throw Error('Layer dimensions must remain within 0–100% (minimum size 5%).');
 if(next.x+next.width>100.001||next.y+next.height>100.001)throw Error('Keep the layer inside the surface.');
 if(!/^#[0-9a-f]{6}$/i.test(next.color)||typeof next.text!=='string'||next.text.length>16000||typeof next.name!=='string'||next.name.length>180||typeof next.source_ref!=='string'||next.source_ref.length>500)throw Error('Invalid layer information.');
 if(next.rights!=='unverified'||!KINDS.includes(next.kind)||next.asset_id!==layer.asset_id||next.id!==id||typeof next.visible!=='boolean')throw Error('Source identity and rights cannot be changed through presentation.');
 if(next.parent_id!==null&&!c.layers.some(l=>l.id===next.parent_id))throw Error('Unknown layer parent.');
 const all=c.layers.map(l=>l.id===id?next:l);let at=next;const seen=new Set();
 while(at){if(seen.has(at.id))throw Error('Layer hierarchy cycle.');seen.add(at.id);at=all.find(l=>l.id===at.parent_id);}
 return {...c,layers:all};
}
export function moveLayer(c,id,offset){const layers=[...c.layers];const i=layers.findIndex(l=>l.id===id);if(i<0)return c;const j=Math.max(0,Math.min(layers.length-1,i+offset));layers.splice(j,0,layers.splice(i,1)[0]);return {...c,layers};}
export function parseCsv(text){
 const rows=[];let row=[],value='',quoted=false;
 for(let i=0;i<text.length;i++){const ch=text[i];if(ch==='"'){if(quoted&&text[i+1]==='"'){value+='"';i++;}else quoted=!quoted;}
 else if(!quoted&&(ch===','||ch==='\n')){row.push(value);value='';if(ch==='\n'){rows.push(row);row=[];}}else if(ch!=='\r')value+=ch;
 if(rows.length>200||row.length>40)throw Error('Table preview supports up to 200 rows and 40 columns.');}
 if(quoted)throw Error('Unclosed CSV quotation.');row.push(value);if(row.some(Boolean))rows.push(row);return rows;
}
export async function exportComposition(c){await validate(c);const body={...c};return {...body,composition_sha256:await digest(encoder.encode(canon(body)))};}
async function validate(c){
 if(!exact(c,Object.keys(emptyComposition()))||c.schema!==SCHEMA||c.parent_ref!=='Cognigrex.cgx'||typeof c.object_ref!=='string'||c.object_ref.length>500||typeof c.title!=='string'||c.title.length>180||c.native_mint!==false||c.public_release!==false||c.automatic_execution!==false||!Array.isArray(c.assets)||!Array.isArray(c.layers)||c.layers.length>48||c.assets.length>96)throw Error('Invalid composition identity or authority boundary.');
 for(const key of ['catalogue','contract_type','notes'])if(typeof c[key]!=='string'||c[key].length>(key==='notes'?4000:180))throw Error('Invalid catalogue details.');
 if(c.load_plan!==null&&(!exact(c.load_plan,['plan_sha256','references','batches','mint_ready'])||!/^[a-f0-9]{64}$/.test(c.load_plan.plan_sha256)||!Number.isInteger(c.load_plan.references)||c.load_plan.references<1||c.load_plan.references>2500||!Number.isInteger(c.load_plan.batches)||c.load_plan.batches<1||c.load_plan.batches>2500||c.load_plan.mint_ready!==0))throw Error('Invalid unsigned LOAD plan binding.');
 let size=0;const ids=new Set();
 for(const a of c.assets){if(!exact(a,['id','name','mime','size','base64','text','handler','rights'])||!nameSafe(a.name)||typeof a.base64!=='string'||a.base64.length>4*1024*1024||ids.has(a.id))throw Error('Invalid source asset.');
 const bytes=Uint8Array.from(atob(a.base64),ch=>ch.charCodeAt(0));const verified=await sourceAsset(a.name,a.mime,bytes);
 if(canon(a)!==canon(verified))throw Error('Source bytes or derived handler differ from the manifest.');ids.add(a.id);size+=a.size;}
 if(size>MAX_BYTES)throw Error('Composition size limit.');
 const layerIds=new Set();for(const l of c.layers){if(!exact(l,['id','kind','name','asset_id','parent_id','visible','x','y','width','height','opacity','color','text','source_ref','rights'])||!/^layer-[1-9]\d*$/.test(l.id)||layerIds.has(l.id)||l.asset_id!==null&&!ids.has(l.asset_id))throw Error('Invalid layer identity.');layerIds.add(l.id);updateLayer(c,l.id,{});}
 return true;
}
export async function restoreComposition(text){if(typeof text!=='string'||text.length>16*1024*1024)throw Error('Composition file too large.');const data=JSON.parse(text);if(!Object.hasOwn(data,'composition_sha256'))throw Error('Missing composition digest.');const {composition_sha256,...body}=data;await validate(body);if(await digest(encoder.encode(canon(body)))!==composition_sha256)throw Error('Composition digest mismatch.');return body;}
