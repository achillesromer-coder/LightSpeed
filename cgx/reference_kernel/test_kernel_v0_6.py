from pathlib import Path
import importlib.util, sys, tempfile, shutil, json
K=Path(__file__).resolve().parents[1]/'runtime/python/cgx_kernel.py'
spec=importlib.util.spec_from_file_location('cgx_kernel_v06',K)
mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
with tempfile.TemporaryDirectory() as td:
    td=Path(td); base=td/'base'; mod.create_empty(base,'Peer Sync Test')
    src=td/'data.json'; src.write_text('{"a":1,"b":1}\n'); imp=mod.do_import(base,src,'data.json'); target=imp['destination']
    A=td/'A'; B=td/'B'; shutil.copytree(base,A); shutil.copytree(base,B)
    def edit(root,obj,label):
        def op(): (root/target).write_text(json.dumps(obj,separators=(',',':'))+'\n')
        return mod.mutate(root,label,label,op)
    edit(A,{'a':2,'b':1},'A-edit'); edit(B,{'a':1,'b':3},'B-edit')
    st=mod.peer_status(A,B); assert st['compatible'] and st['relation']=='diverged',st
    s1=mod.peer_sync(A,B,'sync-b-into-a'); assert s1['synced'] and json.loads((A/target).read_text())=={'a':2,'b':3}
    s2=mod.peer_sync(B,A,'sync-a-into-b'); assert s2['synced'] and json.loads((B/target).read_text())=={'a':2,'b':3}
    assert mod.compute_content_root(A)[0]==mod.compute_content_root(B)[0]
    assert mod.verify(A)['ok'] and mod.verify(B)['ok']
    C=td/'C'; mod.create_empty(C,'Other Object'); bad=mod.peer_status(A,C)
    assert bad['compatible'] is False and bad['reason']=='object-id-mismatch'
print('PASS v0.6 peer-sync/convergence')
