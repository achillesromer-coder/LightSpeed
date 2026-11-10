"""Read pending advisory proposals from existing stores; never accept or execute.

The caller persists ``next_lane`` in the existing Achilles meta table. Selection
does not write a cursor, task, decision, lease or receipt and invokes no model.
"""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
import sqlite3

MAX_LANES = 32
MAX_SOURCE_CHARS = 4000
MAX_PROPOSAL_CHARS = 16384


def _existing_uri(value):
    path = Path(value).absolute()
    if not path.is_file():
        raise ValueError('EXISTING_OVERSIGHT_DATABASE_REQUIRED')
    return path.as_uri() + '?mode=ro'


def pending_oversight_rows(lanes, review_db, *, after_lane=None, limit=6, per_lane=1):
    """Return exact proposal/source pairs with bounded, caller-owned rotation.

    Each lane is ``{lane, proposal_db, source_db}``. Manual Intake inputs are
    preferred within a lane. Already-reviewed ``lane:item_id`` identities and
    unsuccessful proposals are excluded. Missing source rows are never replaced
    with an empty source. These rows remain advisory, including after selection.
    """
    if type(limit) is not int or not 1 <= limit <= 64:
        raise ValueError('INVALID_OVERSIGHT_LIMIT')
    if type(per_lane) is not int or not 1 <= per_lane <= 2:
        raise ValueError('INVALID_OVERSIGHT_PER_LANE')
    if not isinstance(lanes, (list, tuple)) or len(lanes) > MAX_LANES:
        raise ValueError('INVALID_OVERSIGHT_LANES')
    names = []
    for lane in lanes:
        name = lane.get('lane') if isinstance(lane, dict) else None
        if not isinstance(name, str) or not name.strip() or len(name) > 64 or name in names:
            raise ValueError('INVALID_OR_DUPLICATE_OVERSIGHT_LANE')
        if not {'proposal_db', 'source_db'}.issubset(lane):
            raise ValueError('OVERSIGHT_DATABASE_POINTERS_REQUIRED')
        names.append(name)
    review_uri = _existing_uri(review_db)
    start = (names.index(after_lane) + 1) % len(names) if names and after_lane in names else 0
    ordered = [*lanes[start:], *lanes[:start]]
    result = []
    next_lane = after_lane if after_lane in names else None
    for lane in ordered:
        name = lane['lane']
        proposal_uri = _existing_uri(lane['proposal_db'])
        source_uri = _existing_uri(lane['source_db'])
        with closing(sqlite3.connect(proposal_uri, uri=True, timeout=1)) as db:
            db.execute('ATTACH DATABASE ? AS inputs', (source_uri,))
            db.execute('ATTACH DATABASE ? AS oversight', (review_uri,))
            selected = db.execute(
                'SELECT p.item_id,p.out,i.text FROM proposals p '
                'JOIN inputs.items i ON i.item_id=p.item_id '
                'WHERE p.ok=1 AND typeof(p.out)=\'text\' AND typeof(i.text)=\'text\' '
                'AND length(p.out) BETWEEN 1 AND ? AND length(i.text) BETWEEN 1 AND ? '
                'AND NOT EXISTS (SELECT 1 FROM oversight.reviews r WHERE r.ref=?||CAST(p.item_id AS TEXT)) '
                'ORDER BY CASE WHEN instr(i.conv_id,\'manual-intake-\')=1 THEN 0 ELSE 1 END,p.item_id '
                'LIMIT ?',
                (MAX_PROPOSAL_CHARS, MAX_SOURCE_CHARS, name + ':', min(per_lane, limit - len(result))),
            ).fetchall()
        next_lane = name
        result.extend({'lane': name, 'item_id': iid, 'proposal': proposal, 'source': source}
                      for iid, proposal, source in selected)
        if len(result) >= limit:
            break
    return {'rows': result, 'next_lane': next_lane}
