import sqlite3,tempfile,unittest
from contextlib import closing
from pathlib import Path
from cgxResidentReviewQueue import pending_rows,pending_count

class PendingReviewTests(unittest.TestCase):
 def test_late_low_id_route_is_reviewed_without_resetting_cursor(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'source.db';home=Path(tmp)/'home.db'
   with closing(sqlite3.connect(source)) as db,db:
    db.execute('CREATE TABLE items(item_id INTEGER PRIMARY KEY,text TEXT)')
    db.executemany('INSERT INTO items VALUES(?,?)',[(2,'a'*200),(90,'b'*200),(100,'c'*200),(101,'x')])
   with closing(sqlite3.connect(home)) as db,db:
    db.execute('CREATE TABLE proposals(item_id INTEGER PRIMARY KEY,ok INTEGER)')
    db.executemany('INSERT INTO proposals VALUES(?,?)',[(90,1),(100,0)])
   self.assertEqual(pending_rows(source,home),[(2,'a'*200)])
   self.assertEqual(pending_count(source,home),1)
   with closing(sqlite3.connect(home)) as db,db:db.execute('INSERT INTO proposals VALUES(2,1)')
   self.assertEqual(pending_rows(source,home),[])
   self.assertEqual(pending_count(source,home),0)
   # Failed prior proposals remain failed, not silently retried or accepted.
   with closing(sqlite3.connect(home)) as db:self.assertEqual(db.execute('SELECT ok FROM proposals WHERE item_id=100').fetchone()[0],0)
 def test_missing_review_database_is_not_created(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'s.db';home=Path(tmp)/'absent.db'
   with closing(sqlite3.connect(source)) as db,db:db.execute('CREATE TABLE items(item_id INTEGER,text TEXT)')
   with self.assertRaises(sqlite3.OperationalError):pending_rows(source,home)
   self.assertFalse(home.exists())
 def test_invalid_limit_is_rejected(self):
  with self.assertRaises(ValueError):pending_rows('a','b',0)
 def test_manual_inputs_precede_old_backlog_and_achilles_can_filter_own_pointers(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'source.db';home=Path(tmp)/'home.db'
   with closing(sqlite3.connect(source)) as db,db:
    db.execute('CREATE TABLE items(item_id INTEGER PRIMARY KEY,text TEXT,disposition TEXT)')
    db.executemany('INSERT INTO items VALUES(?,?,?)',[(1,'history'*30,None),(2,'older'*40,'legacy'),(100,'manual-a'*30,'source_review_unvalidated'),(101,'manual-b'*30,'source_review_unvalidated'),(102,'failed'*40,'source_review_unvalidated'),(103,'done'*50,'source_review_unvalidated'),(104,'tiny','source_review_unvalidated')])
   with closing(sqlite3.connect(home)) as db,db:
    db.execute('CREATE TABLE proposals(item_id INTEGER PRIMARY KEY,ok INTEGER)')
    db.executemany('INSERT INTO proposals VALUES(?,?)',[(102,0),(103,1)])
   self.assertEqual([i for i,_ in pending_rows(source,home,3)],[100,101,1])
   self.assertEqual([i for i,_ in pending_rows(source,home,3,source_review_only=True)],[100,101])
   self.assertEqual(pending_count(source,home),4)
   self.assertEqual(pending_count(source,home,source_review_only=True),2)
   # Once manual input is reviewed, old low IDs remain eligible; no cursor reset.
   with closing(sqlite3.connect(home)) as db,db:db.executemany('INSERT INTO proposals VALUES(?,1)',[(100,),(101,)])
   self.assertEqual([i for i,_ in pending_rows(source,home)],[1,2])
   self.assertEqual(pending_rows(source,home,source_review_only=True),[])
 def test_legacy_schema_cannot_be_mislabelled_as_manual_input(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'source.db';home=Path(tmp)/'home.db'
   with closing(sqlite3.connect(source)) as db,db:
    db.execute('CREATE TABLE items(item_id INTEGER PRIMARY KEY,text TEXT)');db.execute('INSERT INTO items VALUES(1,?)',('legacy'*30,))
   with closing(sqlite3.connect(home)) as db,db:db.execute('CREATE TABLE proposals(item_id INTEGER PRIMARY KEY,ok INTEGER)')
   self.assertEqual([i for i,_ in pending_rows(source,home)],[1])
   self.assertEqual(pending_rows(source,home,source_review_only=True),[])
   self.assertEqual(pending_count(source,home,source_review_only=True),0)
 def test_source_only_option_rejects_truthy_nonbooleans(self):
  with self.assertRaisesRegex(ValueError,'INVALID_SOURCE_REVIEW_FILTER'):pending_rows('a','b',source_review_only='true')
  with self.assertRaisesRegex(ValueError,'INVALID_SOURCE_REVIEW_FILTER'):pending_count('a','b',source_review_only=1)
if __name__=='__main__':unittest.main()
