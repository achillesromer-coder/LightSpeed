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


if __name__ == '__main__':
    print(json.dumps(verify(ROOT / 'UniSpace'), indent=2))
