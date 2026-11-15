"""Time-bounded, source-only import smoke for private UOS integration ZIP.
Never starts an agent, service, issuer, scanner or external network client.
Import success does not establish native UOS runtime or public release.
"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from package_unispace_uos_integration import verify_uos_archive
MODULES=("lightspeed_runtime.contracts",
         "lightspeed_runtime.bridge_health",
         "lightspeed_runtime.cgx_capability_registry")
ISOLATED_CODE=r'''
import importlib,json,sys
archive=sys.argv[1].replace("\\","/").lower()
sys.path.insert(0,sys.argv[1]+"/native")
results=[]
for name in ("lightspeed_runtime.contracts",
 "lightspeed_runtime.bridge_health",
 "lightspeed_runtime.cgx_capability_registry"):
 try:
  mod=importlib.import_module(name)
  origin=str(getattr(mod,"__file__","")).replace("\\","/").lower()
  results.append({"module":name,"imported_from_package":
    origin.startswith(archive+"/native/"),
    "failure":None if origin.startswith(archive+"/native/") else "ORIGIN_MISMATCH"})
 except Exception as exc:
  results.append({"module":name,"imported_from_package":False,
                  "failure":type(exc).__name__+":"+str(exc)[:100]})
print(json.dumps(results))
'''
def probe(path:Path,timeout_s:float=12):
    verify_uos_archive(path)
    state="HOLD_RUNTIME_IMPORT"
    results=[]
    try:
        run=subprocess.run([sys.executable,"-I","-B","-c",ISOLATED_CODE,
                            str(path.resolve())],capture_output=True,text=True,
                           timeout=timeout_s,check=False)
        if run.returncode==0:
            results=json.loads(run.stdout)
            if len(results)==len(MODULES) and all(
                item["imported_from_package"] for item in results):
                state="PASS_SOURCE_IMPORT_ONLY"
        else:results=[{"failure":"IMPORT_SUBPROCESS_FAILED"}]
    except subprocess.TimeoutExpired:
        results=[{"failure":"IMPORT_TIMEOUT_BOUNDED"}]
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):
        results=[{"failure":"INVALID_IMPORT_RESULT"}]
    return {"schema":"UOS-PRIVATE-NATIVE-IMPORT-SMOKE/0.1",
            "state":state,"modules":results,
            "native_runtime_accepted":False,
            "installed":False,"issuer_accepted":False,
            "public_release_ready":False}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,required=True)
    a=parser.parse_args()
    result=probe(a.archive)
    print(json.dumps(result,sort_keys=True))
    if result["state"]!="PASS_SOURCE_IMPORT_ONLY":sys.exit(2)
