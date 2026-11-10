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
if __name__=='__main__':unittest.main()
