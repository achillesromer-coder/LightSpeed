/** Presentation-only preferences: never jurisdiction, identity, consent or mint authority. */
export const PROFILE_SCHEMA='UNISPACE-PRESENTATION-PREFERENCES/0.1';
const defaults=Object.freeze({locale:'en',region:'unspecified',hue:205,background:'midnight',density:'comfortable',motion:'reduced'});
const keys=Object.keys(defaults);
export function presentationPreferences(value={}){
 if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!keys.includes(k)))throw new TypeError('INVALID_PRESENTATION_FIELDS');
 const p={...defaults,...value};
 if(typeof p.locale!=='string'||p.locale.length>35)throw new TypeError('INVALID_LOCALE');
 try {p.locale=Intl.getCanonicalLocales(p.locale)[0];if(!p.locale)throw 0;}catch{throw new TypeError('INVALID_LOCALE');}
 if(typeof p.region!=='string'||! /^(?:unspecified|[A-Z]{2})$/.test(p.region))throw new TypeError('INVALID_REGION');
 if(!Number.isInteger(p.hue)||p.hue<0||p.hue>359)throw new TypeError('INVALID_HUE');
 if(!['midnight','slate','paper'].includes(p.background)||!['comfortable','compact'].includes(p.density)||!['reduced','system'].includes(p.motion))throw new TypeError('INVALID_PRESENTATION_CHOICE');
 return Object.freeze(p);
}
export function presentationStyle(value={}){
 const p=presentationPreferences(value);
 const light=p.background==='paper', slate=p.background==='slate';
 return {preferences:p,background:light?'#f5f4ef':slate?'#18232e':'#081420',foreground:light?'#142330':'#edf3f6',
  accent:'hsl('+p.hue+' 55% '+(light?'32%':'76%')+')',gap:p.density==='compact'?'6px':'14px',
  region_scope:'DISPLAY_CONTEXT_ONLY_NOT_LOCATION_OR_LEGAL_AUTHORITY'};
}
