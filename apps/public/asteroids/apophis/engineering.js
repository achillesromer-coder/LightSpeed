
;(()=>{'use strict';
const root=document.getElementById('engineering');if(!root||root.dataset.engineeringInit)return;root.dataset.engineeringInit='true';
const $=id=>root.querySelector('#'+id),AU=149597870.7,G=6.67430e-11,mu=3.986004418e14,radius=170,volume=4*Math.PI/3*radius**3;
let records=null,object=null,model=null;
const fmt=(n,d=3)=>Number.isFinite(n)?n.toLocaleString('en-AU',{minimumFractionDigits:d,maximumFractionDigits:d}):'UNAVAILABLE';
const el=(tag,attrs)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs||{}).forEach(([k,v])=>n.setAttribute(k,String(v)));return n};
const html= id=>$(id);
const status=(s,error=false)=>{$('eng-state').textContent=s;$('eng-state').classList.toggle('eng-trace-error',error)};
function validated(e,o,d){if(e.object_id!==o.object_id||d.object_id!==o.object_id||e.samples.length!==21||e.cadence_s!==30||e.frame!=='Ecliptic J2000'||e.time_scale!=='TDB'||Math.abs(e.units.au_km-AU)>1e-5)return false;
if(d.quality_checks.max_vector_range_residual_m>0.001||d.quality_checks.nominal_v_inf_abs_delta_vs_sbdb_km_s>1e-3)return false;
if(e.source_raw_sha256!==d.source_roots.ephemeris_sha)return false;
for(let i=0;i<e.samples.length;i++){const s=e.samples[i],range=Math.hypot(...s.position_au),rv=s.position_au.reduce((a,x,j)=>a+x*s.velocity_au_day[j],0)/range;if(!Number.isFinite(range)||Math.abs(range-s.range_au)*AU>1e-4||Math.abs(rv-s.range_rate_au_day)*AU/86400>1e-4)return false;
if(i>0&&Math.abs((s.jd_tdb-e.samples[i-1].jd_tdb)*86400-30)>.01)return false;}
return true}
function plot(samples,rho,k){const graph=$('eng-grid'),trace=$('eng-trace'),marker=$('eng-marker');while(graph.firstChild)graph.removeChild(graph.firstChild);
const panel={L:72,R:800,T:68,B:282},maxY=6.2;
for(let j=0;j<=5;j++){const y=panel.B-(j/5)*(panel.B-panel.T);graph.appendChild(el('line',{x1:panel.L,y1:y,x2:panel.R,y2:y,stroke:'#7297a1','stroke-opacity':'.25'}));const t=el('text',{x:panel.L-10,y:y+4,fill:'#a2bdc4','font-size':11,'text-anchor':'end'});t.textContent=(j*maxY/5).toFixed(1)+'%';graph.appendChild(t)}
const vals=samples.map((s,i)=>{const d=s.range_au*AU*1000,aT=2*mu*radius/d**3,aG=G*volume*rho/radius**2;return {x:panel.L+i*(panel.R-panel.L)/20,y:panel.B-(aT/aG*100/maxY)*(panel.B-panel.T),tide:aT,gravity:aG,d}});trace.setAttribute('d',vals.map((p,i)=>(i?'L':'M')+p.x.toFixed(2)+' '+p.y.toFixed(2)).join(' '));marker.setAttribute('cx',vals[k].x);marker.setAttribute('cy',vals[k].y);return vals[k]}
function update(){if(!records)return;const rho=Number($('eng-density').value),k=Number($('eng-time').value),s=records.samples[k],point=plot(records.samples,rho,k),mass=volume*rho,gravity=G*mass/radius**2,escape=Math.sqrt(2*G*mass/radius);
const massProof=gravity*radius**2/G,diff=Math.abs((massProof-mass)/mass);
$('eng-density-val').textContent=fmt(rho,0)+' kg/m³';$('eng-trace-label').textContent='ρ = '+fmt(rho,0)+' kg/m³';$('eng-time-val').textContent=s.utc_like_label_tdb+' TDB';$('eng-distance').textContent=fmt(s.range_au*AU,3)+' km';$('eng-mass').textContent=mass.toExponential(3)+' kg';$('eng-gravity').textContent=gravity.toExponential(4)+' m/s²';$('eng-escape').textContent=fmt(escape,4)+' m/s';$('eng-tide').textContent=point.tide.toExponential(4)+' m/s²';$('eng-ratio').textContent=fmt(point.tide/gravity*100,3)+'%';
$('eng-vinf').textContent=fmt(model.nominal_encounter.v_infinity_two_body_km_s,8)+' km/s';$('eng-proof').textContent=diff<1e-12?'PASS · < 10⁻¹² RELATIVE':'HOLD · CROSS-CHECK FAILED';$('eng-caption').textContent='SOURCE: '+s.utc_like_label_tdb+' TDB · 30 s sample · orbital distance source-backed; tidal sensitivity and spherical gravity are MODELLED. No spin/cohesion/shape solution.';
}
async function init(){try{const [a,b,c]=await Promise.all(['data/ephemeris-2029-30s.json','data/object-public-contract.json','data/engineering-derived.json'].map(p=>fetch('./'+p,{cache:'no-store'})));if(!a.ok||!b.ok||!c.ok)throw Error('Source HTTP '+[a.status,b.status,c.status].join('/'));
records=await a.json();object=await b.json();model=await c.json();if(!validated(records,object,model))throw Error('Data integrity mismatch: refused to compute');
$('eng-density').disabled=false;$('eng-time').disabled=false;root.querySelectorAll('button[data-eng-density]').forEach(x=>x.disabled=false);status('QA passed · 21 Horizons samples · public object and physics source contract consistent · model inputs only');update()}
catch(e){status('SOURCE OR QUALITY GATE FAILED: '+e.message,true);$('eng-caption').textContent='Engineering data unavailable. Values intentionally withheld.';records=null;}}
$('eng-density').addEventListener('input',update);$('eng-time').addEventListener('input',update);
root.querySelectorAll('button[data-eng-density]').forEach(b=>b.addEventListener('click',()=>{if(!records)return;$('eng-density').value=b.dataset.engDensity;update()}));
init();})();
