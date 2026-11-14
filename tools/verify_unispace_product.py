"""Verify the published product snapshot without extraction or code execution."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def verify(folder: Path) -> dict:
    contract = json.loads((folder / 'product.json').read_text(encoding='utf-8'))
    if contract['carrier'] != 'CGX.cgx':
        raise ValueError('Unexpected carrier path')
    path = folder / 'CGX.cgx'
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('Carrier byte budget exceeded')
    raw = path.read_bytes()
    if len(raw) != contract['bytes'] or hashlib.sha256(raw).hexdigest() != contract['sha256']:
        raise ValueError('Carrier hash or size mismatch')
    # Read the exact hashed snapshot, not a second potentially changed file.
    import io
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        names = [i.filename for i in members]
        if len(names) != len(set(names)) or len(names) > 5000:
            raise ValueError('Duplicate members or member budget exceeded')
        if sum(i.file_size for i in members) > 32 * 1024 * 1024:
            raise ValueError('Expanded byte budget exceeded')
        for name in names:
            if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe archive member path')
        if archive.testzip() is not None:
            raise ValueError('Archive integrity failure')
        boot = json.loads(archive.read('cgx/bootstrap.json'))
        manifest = json.loads(archive.read('cgx/manifest.json'))
        if boot['state_id'] != contract['state_id'] or manifest['state_id'] != contract['state_id']:
            raise ValueError('Carrier state mismatch')
        entries = manifest['files']
        if len(entries) != contract['tracked_files'] or len({e['path'] for e in entries}) != len(entries):
            raise ValueError('Tracked member count mismatch')
        for entry in entries:
            data = archive.read(entry['path'])
            if len(data) != entry['size_bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError('Tracked member hash or size mismatch')
    return {'status': 'PASS', 'sha256': contract['sha256'], 'state_id': boot['state_id'],
            'tracked_files': len(entries), 'archive_members': len(names), 'embedded_code_executed': False}


def nested_reference_index(entries, topology):
    """Experimental review index over existing CGX paths and topology; not a DBR."""
    nodes = {n['path']: n for n in topology}
    if len(nodes) != len(topology) or len({e['path'] for e in entries}) != len(entries):
        raise ValueError('Duplicate path')
    root = {'children': {}}
    for e in sorted(entries, key=lambda x: x['path']):
        path = e['path']; p = PurePosixPath(path)
        if not p.parts or str(p) != path or p.is_absolute() or '..' in p.parts or chr(92) in path or ':' in path:
            raise ValueError('Unsafe path')
        t = nodes.get(path)
        if t is None or t['sha256'] != e['sha256'] or t['bytes'] != e['size_bytes']:
            raise ValueError('Topology mismatch')
        cur = root
        for part in p.parts:
            if 'leaf' in cur: raise ValueError('Path collision')
            cur = cur['children'].setdefault(part, {'children': {}})
        if cur['children']: raise ValueError('Path collision')
        cur['leaf'] = {'path':path,'sha256':e['sha256'],'size_bytes':e['size_bytes'],'semantic_path':t['semantic_path'],'cell':t['cell']}
    def seal(n):
        children = {k:seal(v) for k,v in sorted(n['children'].items())}
        n['review_sha256'] = hashlib.sha256(json.dumps({'leaf':n.get('leaf'),'children':children},sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return n['review_sha256']
    seal(root)
    return root


def hydrate_nested(archive, root, prefix, *, allowed_paths, max_bytes):
    """Explicit caller-supplied scope; does not itself authenticate permissions."""
    node = root
    for part in prefix: node = node['children'][part]
    def walk(n):
        if 'leaf' in n: yield n['leaf']
        for child in n['children'].values(): yield from walk(child)
    leaves = list(walk(node))
    if any(x['path'] not in allowed_paths for x in leaves): raise PermissionError('Scope denied')
    if type(max_bytes) is not int or max_bytes < 0 or sum(x['size_bytes'] for x in leaves)>max_bytes: raise ValueError('Budget exceeded')
    result = {}
    for x in leaves:
        info = archive.getinfo(x['path'])
        if info.file_size != x['size_bytes']: raise ValueError('Size mismatch')
        raw = archive.read(info)
        if len(raw)!=x['size_bytes'] or hashlib.sha256(raw).hexdigest()!=x['sha256']: raise ValueError('Hash mismatch')
        result[x['path']]=raw
    return result


def facet_transition_options(rules, admitted_facets, *, parent, neighbor, direction='next'):
    """Explicit parent/previous/next rule table; no claim of validated T173 mapping."""
    valid=set(admitted_facets)
    if any(type(v) is not int or not 1<=v<=173 for v in valid): raise ValueError('Reserved or invalid facet')
    if parent not in valid or (neighbor is not None and neighbor not in valid) or direction not in ('next','previous'): raise ValueError('Invalid context')
    out=set()
    for p,a,b in rules:
        if p not in valid or any(v is not None and v not in valid for v in (a,b)) or (a is None and b is None): raise ValueError('Unadmitted rule')
        match,option=(a,b) if direction=='next' else (b,a)
        if p==parent and match==neighbor: out.add(option)
    return tuple(sorted(out,key=lambda x:-1 if x is None else x))


if __name__ == '__main__':
    print(json.dumps(verify(ROOT / 'UniSpace'), indent=2))
