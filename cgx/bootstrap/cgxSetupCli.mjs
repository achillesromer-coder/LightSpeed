#!/usr/bin/env node
/**
 * CGX smart setup: read-only orientation / non-mutating preflight.
 * Does not install, authenticate, upload, connect to networks, bind live FileSpaces,
 * set a real LS GO toggle, or save any secrets. Real provider proof comes from
 * the separate native authenticated host, not from CLI argument flags.
 */
import {planCGXSetup,planOngoingSetup} from './unifiedBootstrap.mjs';
const supported=new Set(['--family','--mode','--profile','--device','--ls-go','--got','--offline','--help']);
function parse(argv){
 const x={};
 for(let i=0;i<argv.length;i++){
  const [k,v]=argv[i].split('=',2);
  if(!supported.has(k))throw Error('UNKNOWN_OPTION:'+k);
  if(k==='--help')return {help:true};
  if(['--ls-go','--got','--offline'].includes(k)){
   const actual=v??'true';
   if(!['true','false'].includes(actual))throw Error('INVALID_BOOLEAN:'+k);
   x[k.slice(2)]=actual==='true';
  } else{
   const value=v??argv[++i];
   if(!value||value.startsWith('--'))throw Error('MISSING_OPTION_VALUE:'+k);
   x[k.slice(2)]=value;
  }
 }
 return x;
}
try{
 const args=parse(process.argv.slice(2));
 if(args.help){
  process.stdout.write('CGX/LS smart setup — review preflight, not an installer.\n');
  process.stdout.write('node cgx/bootstrap/cgxSetupCli.mjs --family Romer.cgx --mode first-run --device desktop --profile core --ls-go=true\n');
 }else{
  const plan=planCGXSetup({family:args.family,mode:args.mode??'first-run',device:args.device??'desktop',
   profile:args.profile??'core',lsGORequested:args['ls-go']===true,gotRequested:args.got===true,
   offlinePreferred:args.offline!==false});
  if(plan.state==='DENIED')process.exitCode=2;
  process.stdout.write(JSON.stringify({
   issued_by:'CGX_REVIEW_CLI_NO_NATIVE_PROOF',setup:plan,
   ongoing:plan.state!=='DENIED'?planOngoingSetup({family:plan.family,current:{},changes:[]}):null
  },null,2)+'\n');
 }
}catch(e){
 process.stderr.write(JSON.stringify({error:'SETUP_CLI_REJECTED',reason:String(e.message??e)})+'\n');
 process.exitCode=2;
}
