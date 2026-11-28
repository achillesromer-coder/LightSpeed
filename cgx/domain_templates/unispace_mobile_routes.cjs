'use strict';
/* Public-safe route resolver: no native bridge, enumeration, dispatch or credentials. */
const WEB=Object.freeze({chatgpt:['ChatGPT','chat','https://chatgpt.com/'],drive:['Drive','folder','https://drive.google.com/'],docs:['Docs','document','https://docs.google.com/'],sheets:['Sheets','table','https://sheets.google.com/'],github:['GitHub','code','https://github.com/'],gmail:['Gmail','mail','https://mail.google.com/'],calendar:['Calendar','calendar','https://calendar.google.com/'],canva:['Canva','design','https://www.canva.com/'],maps:['Maps','map','https://maps.google.com/']});
const FACETS=Object.freeze({filespace:'FileSpace',dataspace:'DataSpace',printspace:'PrintSpace',socialspace:'SocialSpace',profilespace:'ProfileSpace',intelligencespace:'IntelligenceSpace',earth:'Earth / ECW',orbital:'Orbital',mol:'Molecular',raphael:'Raphael',universe:'Universe',lightspeed:'LightSpeed'});
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
function route(id,available=[]){
 if(typeof id!=='string'||!Array.isArray(available))return {state:'HOLD',nativeAuthority:false};
 if(own(WEB,id)){const [label,icon,url]=WEB[id];return {id,label,icon,url,state:'HTTPS_LINK',target:'_blank',rel:'noopener noreferrer',nativeAuthority:false,installed:'UNKNOWN'};}
 if(own(FACETS,id))return {id,label:FACETS[id],icon:'facet',state:available.includes(id)?'INTERNAL_VIEW':'HOLD',nativeAuthority:false};
 return {state:'HOLD',nativeAuthority:false};
}
function list(available=[]){return [...Object.keys(WEB),...Object.keys(FACETS)].map(id=>route(id,available));}
module.exports=Object.freeze({route,list});
