export type CgxLens="neo"|"athene"|"achilles"|"alexandria";
export type CgxTheme="orbit"|"forest"|"blueprint"|"dawn";
export const LENSES:Record<CgxLens,string>={
 neo:"Neo · Römer-Grex",athene:"Athene · Eco-Grex",
 achilles:"Achilles · Cognigrex",alexandria:"Alexandria · Evidence"
};
export const THEMES:CgxTheme[]=["orbit","forest","blueprint","dawn"];
const configured=String(import.meta.env.VITE_LIGHTSPEED_VISITOR_API_ORIGIN||"").trim();
export const visitorOrigin=(()=>{
 if(!configured)return window.location.origin;
 const parsed=new URL(configured);
 if(parsed.protocol!=="https:"||parsed.username||parsed.password||parsed.pathname!=="/"||parsed.search||parsed.hash)
   throw new Error("Visitor remote API must be an HTTPS origin");
 return parsed.origin;
})();
let session="";
export const setVisitorSession=(value:string):void=>{session=value;};
export async function visitorRequest<T>(endpoint:string,data?:unknown):Promise<T>{
 if(!/^\/api\/v1\/visitor\/[a-z-]+$/.test(endpoint))throw Error("Unapproved visitor path");
 const headers:Record<string,string>={"Accept":"application/json"};
 if(data!==undefined)headers["Content-Type"]="application/json";
 if(session)headers["X-LightSpeed-Visitor-Session"]=session;
 const response=await fetch(visitorOrigin+endpoint,{method:data===undefined?"GET":"POST",headers,
   credentials:"omit",cache:"no-store",body:data===undefined?undefined:JSON.stringify(data)});
 const result=await response.json().catch(()=>({detail:"Unparseable response"}));
 if(!response.ok)throw Error(String(result.detail||"Service unavailable"));
 return result as T;
}
