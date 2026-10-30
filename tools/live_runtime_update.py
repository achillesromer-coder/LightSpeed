"""Stage and apply a bounded Python-package update to the existing live runtime.

No service management, database writes, carrier changes or queue dispatch.
The Windows operator must stop relevant services and suspend their guard first.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).is_file() else None


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.runtime-update-')
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save(path, value):
    atomic(path, (json.dumps(value, indent=2) + '\n').encode())


def member(root, name):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts or ':' in name or '\\' in name or relative.suffix != '.py':
        raise ValueError('unsafe package member')
    root = Path(root).resolve(strict=True)
    target = root / relative
    for part in [target, *target.parents]:
        if part == root:
            break
        if part.is_symlink() or (part.exists() and getattr(part.stat(follow_symlinks=False), 'st_file_attributes', 0) & 0x400):
            raise ValueError('redirected package member')
    if not target.resolve().is_relative_to(root):
        raise ValueError('package member escapes root')
    return target


def stage(source, target, transaction, head):
    source, target, transaction = Path(source).resolve(strict=True), Path(target).resolve(strict=True), Path(transaction)
    if source == target or source.is_relative_to(target) or target.is_relative_to(source):
        raise ValueError('source and target must be separate packages')
    if transaction.resolve().is_relative_to(source) or transaction.resolve().is_relative_to(target):
        raise ValueError('transaction must be outside packages')
    files = sorted(source.rglob('*.py'))
    if not 1 <= len(files) <= 512:
        raise ValueError('package count exceeds update budget')
    transaction.mkdir(parents=True, exist_ok=False)
    (transaction / 'before').mkdir()
    (transaction / 'after').mkdir()
    rows = []
    for file in files:
        name = file.relative_to(source).as_posix()
        src, dst = member(source, name), member(target, name)
        data = src.read_bytes()
        if len(data) > 8 * 1024 * 1024 or (dst.exists() and dst.stat().st_size > 8 * 1024 * 1024):
            raise ValueError('package member exceeds byte budget')
        compile(data, name, 'exec')
        new, old = hashlib.sha256(data).hexdigest(), digest(dst)
        if new == old:
            continue
        atomic(transaction / 'after' / name, data)
        if old is not None:
            prior = dst.read_bytes()
            if hashlib.sha256(prior).hexdigest() != old:
                raise ValueError('installed file changed during backup')
            atomic(transaction / 'before' / name, prior)
        rows.append({'name': name, 'before': old, 'after': new})
    manifest = {'schema': 'lightspeed-live-package-transaction-v1', 'source': str(source),
                'target': str(target), 'head': head, 'state': 'STAGED', 'files': rows,
                'authority': 'software bytes only; no ingestion or canonical admission'}
    save(transaction / 'manifest.json', manifest)
    return manifest


def transition(transaction, *, rollback=False, idle):
    transaction = Path(transaction).resolve(strict=True)
    lock = transaction / 'transaction.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        manifest_path = transaction / 'manifest.json'
        m = json.loads(manifest_path.read_text())
        if m['state'] != ('APPLIED' if rollback else 'STAGED'):
            raise ValueError('transaction state does not permit transition')
        names = [r['name'] for r in m['files']]
        if len(names) != len(set(names)) or len(names) > 512:
            raise ValueError('invalid transaction member list')
        target = Path(m['target']).resolve(strict=True)
        expected, desired, folder = ('after', 'before', 'before') if rollback else ('before', 'after', 'after')
        for r in m['files']:
            dst = member(target, r['name'])
            if digest(dst) != r[expected]:
                raise ValueError('target drift; no files changed')
            for field in ('before', 'after'):
                if r[field] is not None and digest(member(transaction / field, r['name'])) != r[field]:
                    raise ValueError('staged or rollback bytes changed')
        idle()
        changed = []
        try:
            for r in m['files']:
                idle()
                dst = member(target, r['name'])
                if digest(dst) != r[expected]:
                    raise ValueError('target changed during update')
                if r[desired] is None:
                    dst.unlink()
                else:
                    atomic(dst, member(transaction / folder, r['name']).read_bytes())
                changed.append(r)
                if digest(dst) != r[desired]:
                    raise ValueError('installed readback mismatch')
            m['state'] = 'ROLLED_BACK' if rollback else 'APPLIED'
            save(manifest_path, m)
        except Exception:
            # Restore only files written by this attempt; never clobber later edits.
            for r in reversed(changed):
                dst = member(target, r['name'])
                if digest(dst) != r[desired]:
                    m['state'] = 'RECOVERY_REQUIRED'
                    save(manifest_path, m)
                    raise ValueError('concurrent edit prevents safe recovery')
                if r[expected] is None:
                    dst.unlink()
                else:
                    atomic(dst, member(transaction / expected, r['name']).read_bytes())
            raise
        return m
    finally:
        os.close(fd)
        lock.unlink()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True, timeout=30).strip()


def active_runtime_processes(rows, own_pid):
    """Inspect Python service owners, not shells merely mentioning a filename."""
    markers = ('run_ls_go_bridge.py', 'run_merovingian', 'ls_go_job_consumer', 'cognigrex_setup_wizard.py',
               'ensure_cognigrex_local_stack.py', 'run_cognigrex_local_stack.py', 'lightspeed\\app\\__main__.py',
               'desktop_hooks\\lightspeed\\__main__.py')
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list):
        raise ValueError('process inventory unavailable')
    return [r for r in rows if r.get('ProcessId') != own_pid
            and str(r.get('Name', '')).lower() in ('python.exe', 'pythonw.exe')
            and any(x in (r.get('CommandLine') or '').lower() for x in markers)]


def windows_idle():
    if os.name != 'nt':
        raise ValueError('live operator requires Windows')
    script = "Get-CimInstance Win32_Process | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    rows = json.loads(subprocess.check_output(['powershell.exe', '-NoProfile', '-Command', script], text=True, timeout=20))
    if active_runtime_processes(rows, os.getpid()):
        raise ValueError('live services or setup wizard still running; stop through existing controls first')
    task = subprocess.check_output(['powershell.exe', '-NoProfile', '-Command',
        "(Get-ScheduledTask -TaskName 'LightSpeed Cognigrex Local Guard' -ErrorAction Stop).State.ToString()"], text=True, timeout=20).strip()
    if task != 'Disabled':
        raise ValueError('local guard must be suspended for update window')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['stage', 'apply', 'rollback'])
    p.add_argument('--transaction', type=Path, required=True)
    p.add_argument('--confirmed', action='store_true')
    args = p.parse_args()
    repo = Path(r'D:\LightSpeed\Repositories\LightSpeed_Canonical')
    source = repo / 'desktop/LightSpeed_Runtime/lightspeed_runtime'
    target = Path(r'D:\LightSpeed\App\lightspeed_runtime')
    head = git(repo, 'rev-parse', 'HEAD')
    if git(repo, 'status', '--porcelain') or head != git(repo, 'rev-parse', 'origin/main'):
        raise ValueError('canonical checkout must be clean and match fetched main')
    if target.resolve(strict=True) != Path(r'D:\LightSpeed\Core\lightspeed_runtime').resolve(strict=True):
        raise ValueError('App/Core package identity differs')
    if args.action == 'stage':
        result = stage(source, target, args.transaction, head)
    else:
        if not args.confirmed:
            raise ValueError('explicit confirmation required')
        m = json.loads((args.transaction / 'manifest.json').read_text())
        if Path(m['target']).resolve() != target.resolve() or Path(m['source']).resolve() != source.resolve() or m['head'] != head:
            raise ValueError('transaction binding differs from canonical runtime')
        if args.action == 'apply':
            for r in m['files']:
                if digest(member(source, r['name'])) != r['after']:
                    raise ValueError('canonical source changed since staging')
        result = transition(args.transaction, rollback=args.action == 'rollback', idle=windows_idle)
    print(json.dumps({'state': result['state'], 'head': result['head'], 'files': len(result['files']),
                      'transaction': str(args.transaction), 'runtime_acceptance': False}))


if __name__ == '__main__':
    main()
