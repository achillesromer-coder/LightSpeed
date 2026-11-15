import hashlib
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from cgxResidentOversightQueue import pending_oversight_rows


class ResidentOversightQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.review = self.root / 'achilles.db'
        with closing(sqlite3.connect(self.review)) as db, db:
            db.execute('CREATE TABLE reviews(ref TEXT PRIMARY KEY,out TEXT)')

    def tearDown(self):
        self.tmp.cleanup()

    def lane(self, name, rows):
        source, proposals = self.root / (name + '-source.db'), self.root / (name + '-home.db')
        with closing(sqlite3.connect(source)) as db, db:
            db.execute('CREATE TABLE items(item_id INTEGER PRIMARY KEY,conv_id TEXT,text TEXT)')
            db.executemany('INSERT INTO items VALUES(?,?,?)', [(iid, cid, text) for iid, cid, text, ok in rows])
        with closing(sqlite3.connect(proposals)) as db, db:
            db.execute('CREATE TABLE proposals(item_id INTEGER PRIMARY KEY,out TEXT,ok INTEGER)')
            db.executemany('INSERT INTO proposals VALUES(?,?,?)', [(iid, 'proposal:' + str(iid), ok) for iid, cid, text, ok in rows])
        return {'lane': name, 'source_db': source, 'proposal_db': proposals}

    def test_reviewed_latest_does_not_hide_older_and_late_low_ids(self):
        lane = self.lane('Raphael', [(90, 'legacy', 'source90', 1), (100, 'legacy', 'source100', 1)])
        with closing(sqlite3.connect(self.review)) as db, db:
            db.executemany('INSERT INTO reviews VALUES(?,?)', [('Raphael:90', 'hold'), ('Raphael:100', 'hold')])
        with closing(sqlite3.connect(lane['source_db'])) as db, db:
            db.execute('INSERT INTO items VALUES(2,?,?)', ('manual-intake-text:hash', 'exact late source'))
        with closing(sqlite3.connect(lane['proposal_db'])) as db, db:
            db.execute('INSERT INTO proposals VALUES(2,?,1)', ('exact late proposal',))
        selected = pending_oversight_rows([lane], self.review)
        self.assertEqual(selected['rows'], [{'lane': 'Raphael', 'item_id': 2, 'proposal': 'exact late proposal', 'source': 'exact late source'}])
        self.assertEqual(selected['next_lane'], 'Raphael')

    def test_manual_inputs_preferred_only_successful_exact_sources_returned(self):
        lane = self.lane('Oracle', [(1, 'legacy', 'old source', 1), (3, 'manual-intake-pointer:h', 'manual source', 1), (4, 'manual-intake-text:h', 'failed source', 0)])
        with closing(sqlite3.connect(lane['proposal_db'])) as db, db:
            db.execute('INSERT INTO proposals VALUES(2,?,1)', ('orphan without source',))
        result = pending_oversight_rows([lane], self.review, per_lane=2)
        self.assertEqual([r['item_id'] for r in result['rows']], [3, 1])
        self.assertTrue(all(set(r) == {'lane', 'item_id', 'proposal', 'source'} for r in result['rows']))

    def test_caller_rotation_is_fair_across_multiple_lanes(self):
        lanes = [self.lane(name, [(1, 'manual-intake-text:h', name + ' source', 1)]) for name in ['Oracle', 'Raphael', 'Smith']]
        after, served = None, []
        for _ in range(3):
            result = pending_oversight_rows(lanes, self.review, after_lane=after, limit=1)
            served.append(result['rows'][0]['lane'])
            after = result['next_lane']
        self.assertEqual(served, ['Oracle', 'Raphael', 'Smith'])

    def test_read_only_no_databases_created_or_acceptance_written(self):
        lane = self.lane('Neo', [(1, 'manual-intake-text:h', 'source', 1)])
        paths = [self.review, lane['source_db'], lane['proposal_db']]
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        pending_oversight_rows([lane], self.review)
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
        missing = self.root / 'missing.db'
        with self.assertRaisesRegex(ValueError, 'EXISTING_OVERSIGHT_DATABASE_REQUIRED'):
            pending_oversight_rows([lane], missing)
        self.assertFalse(missing.exists())
        with self.assertRaisesRegex(ValueError, 'EXISTING_OVERSIGHT_DATABASE_REQUIRED'):
            pending_oversight_rows([{**lane, 'source_db': missing}], self.review)
        self.assertFalse(missing.exists())
        with closing(sqlite3.connect(self.review)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM reviews').fetchone()[0], 0)

    def test_bounds_and_duplicate_lanes_rejected(self):
        lane = self.lane('Oracle', [(1, 'legacy', 'source', 1)])
        for opts in [{'limit': 0}, {'limit': True}, {'per_lane': 3}]:
            with self.assertRaises(ValueError):
                pending_oversight_rows([lane], self.review, **opts)
        with self.assertRaisesRegex(ValueError, 'INVALID_OR_DUPLICATE_OVERSIGHT_LANE'):
            pending_oversight_rows([lane, lane], self.review)


if __name__ == '__main__':
    unittest.main()
