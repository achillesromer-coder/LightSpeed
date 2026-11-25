#!/usr/bin/env python3
"""Review-only deduplication of overlapping GitHub PR file-path footprints.

Overlapping paths need independent source diff and regression proof; a common
filename is NOT a shared blob, semantic equivalence, permission to squash or a
reason to delete any historical parent file.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import PurePosixPath, Path
from itertools import combinations

SCHEMA = "CGX-UNISPACE-CHANGED-PATH-OVERLAP/0.1"
OUT_SCHEMA = "CGX-UNISPACE-OVERLAP-REVIEW-PLAN/0.1"
ROOT = "cgx:root:cognigrex"
REPO = "achillesromer-coder/LightSpeed"

class OverlapHold(ValueError):
    """Unsafe, incomplete or mutated source-diff reference."""

def path_ok(p):
    if not isinstance(p, str) or not p or len(p) > 400 or '\\' in p or p.startswith('/'):
        return False
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in p):
        return False
    parts = PurePosixPath(p).parts
    return '..' not in parts and '.' not in parts and '//' not in p

def classification(path):
    if '/dist/' in '/' + path or path.startswith('apps/lightspeed-go/dist/'):
        return 'GENERATED_BUILD_REPRODUCE_FROM_VERIFIED_SOURCE'
    if path.endswith(('.ts', '.tsx', '.js', '.mjs', '.py', '.json')):
        return 'SOURCE_THREE_WAY_DIFF_AND_SEMANTIC_REGRESSION'
    if path.endswith(('.yml', '.yaml')):
        return 'WORKFLOW_PERMISSIONS_AND_TRIGGER_REVIEW'
    if path.endswith(('.test', '.md', '.html', '.css')):
        return 'REVIEW_AND_REGENERATE_PROJECTION_IF_NEEDED'
    return 'HOLD_REQUIRES_SOURCE_AND_RIGHTS_COMPARISON'

def review_overlap(source):
    if (not isinstance(source, dict) or source.get('schema') != SCHEMA
            or source.get('canonical_root') != ROOT or source.get('repository') != REPO
            or source.get('status') != 'REVIEW_ONLY'):
        raise OverlapHold('unknown source, scope or canonical root')
    if any(source.get('authority', {}).get(field) is not False for field in
           ('merge','archive_delete','native_dbr','public_release','model_train')):
        raise OverlapHold('path metadata cannot grant authority')
    prs = source.get('source_pull_requests')
    if not isinstance(prs, list) or len(prs) > 30:
        raise OverlapHold('unbounded or unavailable PR list')
    paths_by_pr = {}
    for pr in prs:
        if not isinstance(pr, dict) or not isinstance(pr.get('pr'), int):
            raise OverlapHold('bad PR identity')
        number = pr['pr']
        if number <= 0 or number in paths_by_pr:
            raise OverlapHold('duplicate PR')
        if not isinstance(pr.get('head_sha'), str) or len(pr['head_sha']) != 40 or any(
                ch not in '0123456789abcdef' for ch in pr['head_sha']):
            raise OverlapHold('invalid pinned head')
        paths = pr.get('paths')
        if not isinstance(paths, list) or len(paths) > 500 or any(not path_ok(p) for p in paths):
            raise OverlapHold('unsafe source diff')
        if len(set(paths)) != len(paths):
            raise OverlapHold('same PR path duplicated')
        if pr.get('compare_status') not in ('ahead', 'diverged', 'identical'):
            raise OverlapHold('unverified compare status')
        paths_by_pr[number] = set(paths)
    computed_pairs = []
    all_shared = set()
    for a, b in combinations(sorted(paths_by_pr), 2):
        shared = sorted(paths_by_pr[a] & paths_by_pr[b])
        if shared:
            all_shared.update(shared)
            computed_pairs.append({
                'a': a, 'b': b, 'shared_paths': shared,
                'review_class': 'SOURCE_PATH_OVERLAP_NO_SEMANTIC_EQUIVALENCE'
            })
    original_pairs = source.get('overlapping_pairs')
    if not isinstance(original_pairs, list) or original_pairs != computed_pairs:
        raise OverlapHold('overlap evidence does not match pinned path lists')
    groups = {}
    for p in sorted(all_shared):
        owners = sorted(n for n, files in paths_by_pr.items() if p in files)
        groups[p] = {'path': p, 'branches': owners, 'action': classification(p),
                     'byte_equal': 'NOT_EVALUATED', 'semantic_equal': 'NOT_EVALUATED',
                     'promotable': False, 'delete_eligible': False}
    out = {
        'schema': OUT_SCHEMA, 'canonical_root': ROOT, 'review_status': 'OPEN_HOLDS',
        'source_pr_count': len(prs), 'overlap_pair_count': len(computed_pairs),
        'unique_overlapping_paths': len(groups), 'path_review': list(groups.values()),
        'closed_pr_source_fidelity_rule': 'PR235_REQUIRES_DIFF_NOT_BLIND_RESTORE',
        'source_bytes_inspected': False, 'semantic_equivalence_claimed': False,
        'merge_performed': False, 'archive_deleted': False, 'native_dbr_performed': False,
        'public_release_performed': False, 'new_root_created': False,
        'next_gate': 'INDEPENDENT_CONFLICT_RESOLUTION_AND_EXACT_HEAD_REGRESSIONS',
    }
    out['review_sha256'] = hashlib.sha256(json.dumps(
        out, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')).hexdigest()
    return out

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    if args.source.stat().st_size > 250000:
        raise OverlapHold('unbounded source file')
    print(json.dumps(review_overlap(json.loads(args.source.read_text('utf-8'))),
                     indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
