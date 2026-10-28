#!/usr/bin/env python3
"""Read-only portable LOAD.cgx source-reference inspector; never executes remote code."""
import argparse, json, zipfile
from pathlib import Path

ENTRY='library/one_of_one.json'
def read_library(carrier):
    with zipfile.ZipFile(carrier) as z: lib=json.loads(z.read(ENTRY))
    ids=[e['ref_id'] for e in lib['entries']]
    if len(ids)!=len(set(ids)): raise ValueError('ambiguous duplicate load-reference-id')
    return lib

def resolve(lib,term):
    m=[e for e in lib['entries'] if term==e['ref_id'] or term==e['name'] or term in e.get('aliases',[])]
    return {'state':'REFERENCE_ONLY','entry':m[0],'native_admission':False} if len(m)==1 else {'state':'AMBIGUOUS' if m else 'NOT_FOUND','matches':[e['ref_id'] for e in m]}

def hydrate(lib,term,level=0):
    res=resolve(lib,term)
    if res['state']!='REFERENCE_ONLY':return res
    e=res['entry'];out={'state':'REFERENCE_ONLY','ref_id':e['ref_id'],'name':e['name'],'object_id':e.get('object_id'),'level':level}
    if level>=1:out['edges']=e.get('edges',[])
    if level>=2:out.update(sources=e.get('sources',[]),evidence=e.get('evidence_state','UNKNOWN'))
    if level>=3:out['capability']=e.get('capability',{'status':'NOT_INSTALLED'})
    if level>=4:out['execute']='DENIED_NO_AUTHENTICATED_DBR'
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--carrier',type=Path,required=True)
    s=p.add_subparsers(dest='action',required=True)
    s.add_parser('inspect');s.add_parser('coverage')
    for name in ('search','resolve','walk','hydrate'):
        q=s.add_parser(name);q.add_argument('term')
        if name=='hydrate':q.add_argument('--level',type=int,choices=range(5),default=0)
        if name=='walk':q.add_argument('--depth',type=int,choices=range(5),default=2)
    a=p.parse_args();lib=read_library(a.carrier)
    if a.action=='inspect':r={'file_space':'LOAD.cgx','references':len(lib['entries']),'status':'SOURCE_REVIEW_ONLY','native_absorbed':0}
    elif a.action=='coverage':r={'references':len(lib['entries']),'native_absorbed':0,'external_corpus_complete':False}
    elif a.action=='resolve':r=resolve(lib,a.term)
    elif a.action=='hydrate':r=hydrate(lib,a.term,a.level)
    elif a.action=='search':r={'matches':[e['name'] for e in lib['entries'] if a.term.casefold() in (e['name']+' '+(' '.join(e.get('aliases',[])))).casefold()]}
    else:
        x=resolve(lib,a.term)
        if x['state']!='REFERENCE_ONLY':r=x
        else:
            visited=set()
            def rec(e,d):
                if e['ref_id'] in visited:return {'ref_id':e['ref_id'],'shared_reference':True}
                visited.add(e['ref_id']);return {'ref_id':e['ref_id'],'name':e['name'],'children':[rec(child,d-1) if d else {'ref_id':child['ref_id'],'unhydrated':True} for name in e.get('edges',[]) for child in lib['entries'] if child['name']==name]}
            r=rec(x['entry'],a.depth)
    print(json.dumps(r,sort_keys=True,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
