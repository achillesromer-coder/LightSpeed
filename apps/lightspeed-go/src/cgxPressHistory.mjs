/** Bounded view history; source asset bytes are shared by reference, never cloned. */
const frame=c=>({...c,assets:[...c.assets],layers:c.layers.map(l=>({...l})),load_plan:c.load_plan?{...c.load_plan}:null});
const signature=c=>JSON.stringify({...c,assets:c.assets.map(a=>a.id)});
export function createPressHistory(initial,limit=60){
 let current=frame(initial),past=[],future=[];
 const trim=()=>{
  while(past.length>limit)past.shift();
  const size=()=>{const ids=new Map();for(const c of [...past,current,...future])for(const a of c.assets)ids.set(a.id,a.size);return [...ids.values()].reduce((n,v)=>n+v,0);};
  while(past.length&&size()>32*1024*1024)past.shift();
 };
 return {
  record(c){if(signature(c)===signature(current))return;past.push(current);current=frame(c);future=[];trim();},
  undo(){if(past.length){future.push(current);current=past.pop();}return frame(current);},
  redo(){if(future.length){past.push(current);current=future.pop();}return frame(current);},
  get canUndo(){return past.length>0;},get canRedo(){return future.length>0;},
  get depth(){return past.length;}
 };
}
