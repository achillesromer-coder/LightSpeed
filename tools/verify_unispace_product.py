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
    def facet(v): return type(v) is int and 1<=v<=173
    values=tuple(admitted_facets)
    if any(not facet(v) for v in values): raise ValueError('Reserved or invalid facet')
    valid=set(values)
    def member(v): return facet(v) and v in valid
    if not member(parent) or (neighbor is not None and not member(neighbor)) or direction not in ('next','previous'): raise ValueError('Invalid context')
    out=set()
    for rule in rules:
        if not isinstance(rule,(tuple,list)) or len(rule)!=3: raise ValueError('Invalid rule shape')
        p,a,b=rule
        if not member(p) or any(v is not None and not member(v) for v in (a,b)) or (a is None and b is None): raise ValueError('Unadmitted rule')
        match,option=(a,b) if direction=='next' else (b,a)
        if p==parent and match==neighbor: out.add(option)
    return tuple(sorted(out,key=lambda x:-1 if x is None else x))


def exact_convex_mesh_review(vertices, faces):
    """Bounded integer convex-polyhedron review. Strict outward face ordering.
    No T173 mapping, licence, catalogue admission, or physical hypothesis proof.
    Coplanar split faces and non-convex meshes are not supported.
    """
    if (type(vertices) is not list or not 4<=len(vertices)<=256 or
        any(type(v) not in (list,tuple) or len(v)!=3 or
            any(type(x) is not int or abs(x)>1000000 for x in v) for v in vertices)):
        raise ValueError("Invalid integer vertex coordinates")
    points=[tuple(v) for v in vertices]
    if len(set(points))!=len(points):raise ValueError("Duplicate vertex")
    if type(faces) is not list or not 4<=len(faces)<=512:
        raise ValueError("Invalid face count")
    def sub(a,b):return tuple(x-y for x,y in zip(a,b))
    def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
    def dot(a,b):return sum(x*y for x,y in zip(a,b))
    edges={};used=set();volume6=0;face_keys=set()
    for face in faces:
        if (type(face) not in (list,tuple) or not 3<=len(face)<=64 or
            any(type(i) is not int or not 0<=i<len(points) for i in face) or len(set(face))!=len(face)):
            raise ValueError("Invalid index incidence")
        key=frozenset(face)
        if key in face_keys:raise ValueError("Duplicate face")
        face_keys.add(key);used.update(face)
        a=points[face[0]]
        normal=cross(sub(points[face[1]],a),sub(points[face[2]],a))
        if normal==(0,0,0):raise ValueError("Degenerate face")
        for i,v in enumerate(points):
            side=dot(normal,sub(v,a))
            if (i in key and side!=0) or (i not in key and side>=0):
                raise ValueError("Nonplanar, inward or non-supporting face")
        for j,i in enumerate(face):
            k=face[(j+1)%len(face)]
            direction=sub(points[k],points[i])
            for q in face:
                if q not in (i,k) and dot(normal,cross(direction,sub(points[q],points[i])))<=0:
                    raise ValueError("Nonconvex or unordered face loop")
            edge=tuple(sorted((i,k)))
            edges.setdefault(edge,[]).append((i,k))
        for j in range(1,len(face)-1):
            volume6+=dot(a,cross(points[face[j]],points[face[j+1]]))
    if len(used)!=len(points) or any(len(v)!=2 or v[0]!=v[1][::-1] for v in edges.values()):
        raise ValueError("Open or inconsistent edge incidence")
    reached={0};front=[0];neighbors={i:set() for i in used}
    for a,b in edges:neighbors[a].add(b);neighbors[b].add(a)
    while front:
        for q in neighbors[front.pop()]-reached:reached.add(q);front.append(q)
    if reached!=used or len(points)-len(edges)+len(faces)!=2 or volume6<=0:
        raise ValueError("Invalid connected closed volume")
    return {"vertices":len(points),"edges":len(edges),"faces":len(faces),
            "euler":2,"six_times_volume":volume6,"coordinate_units":"input_units",
            "exact_integer_review":True,"t173_catalogue_admitted":False}


if __name__ == '__main__':
    print(json.dumps(verify(ROOT / 'UniSpace'), indent=2))
