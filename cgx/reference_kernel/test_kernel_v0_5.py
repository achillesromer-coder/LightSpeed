from pathlib import Path
import importlib.util, json, tempfile, shutil, sys

KERNEL = Path(__file__).resolve().parents[1] / 'runtime/python/cgx_kernel.py'
spec = importlib.util.spec_from_file_location('cgx_kernel_v05', KERNEL)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

results = {}
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    root = td/'root'
    mod.create_empty(root, 'v0.5 test')
    p1 = td/'local_provider.json'
    p1.write_text(json.dumps({'id':'local-solver','capabilities':['solve.trajectory'],'connection_types':['local-ipc'],'trust':0.95,'latency_ms':2,'egress_multiplier':0,'compute_cost':1,'privacy_penalty':0,'semantic_distance':0,'authority_penalty':0,'permissions':['execute'],'locator':'ipc://solver'}))
    p2 = td/'remote_provider.json'
    p2.write_text(json.dumps({'id':'remote-solver','capabilities':['solve.trajectory'],'connection_types':['https'],'trust':0.99,'latency_ms':80,'egress_multiplier':1,'compute_cost':0.2,'privacy_penalty':0.4,'semantic_distance':0,'authority_penalty':0,'permissions':['execute'],'locator':'https://example.invalid/solve'}))
    mod.provider_add(root, json.loads(p1.read_text())); mod.provider_add(root, json.loads(p2.read_text()))
    route = mod.provider_route(root, 'solve.trajectory', data_bytes=5_000_000, min_trust=0.9)
    assert route['selected']['id'] == 'local-solver', route
    child = td/'child'; mod.create_empty(child, 'Tracked Child')
    add = mod.child_add(root, child, 'tracked', 'TRACK'); old_state = add['child']['state_id']
    mod.dependency_add(child, 'report', 'source'); refreshed = mod.child_refresh(root, 'tracked')
    assert refreshed['changed'] is True and refreshed['child']['object_id'] == add['child']['object_id'] and refreshed['child']['state_id'] != old_state
    src = td/'data.json'; src.write_text('{"a":1,"b":1}\n'); imp = mod.do_import(root, src, 'data.json'); target = imp['destination']
    mod.branch_create(root, 'alice'); prop = td/'alice.json'; prop.write_text('{"a":2,"b":1}\n'); mod.branch_set(root, 'alice', prop, target)
    def change_current(): (root/target).write_text('{"a":1,"b":3}\n')
    mod.mutate(root, 'test_current_edit', 'change b on current', change_current)
    merged = mod.branch_merge(root, 'alice'); assert merged['merged'] is True and json.loads((root/target).read_text()) == {'a':2,'b':3}
    mod.branch_create(root, 'bob'); prop2 = td/'bob.json'; prop2.write_text('{"a":5,"b":3}\n'); mod.branch_set(root, 'bob', prop2, target)
    def change_same(): (root/target).write_text('{"a":7,"b":3}\n')
    mod.mutate(root, 'test_conflict_edit', 'change same key', change_same)
    conflict = mod.branch_merge(root, 'bob'); assert conflict['merged'] is False and conflict['conflicts']
    ver = mod.verify(root); assert ver['ok'], ver
print('PASS v0.5 provider/TRACK/semantic-merge')
