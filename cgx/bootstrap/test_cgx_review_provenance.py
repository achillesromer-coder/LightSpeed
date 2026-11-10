import hashlib
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from cgxReviewProvenance import (is_source_review,source_review_disposition,
    repair_review_dispositions,SOURCE_REVIEW_DISPOSITION)

class ReviewProvenanceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.master=self.root/'master.db';self.agent=self.root/'agent.db'
  with closing(sqlite3.connect(self.master)) as db:
   db.execute('CREATE TABLE items(item_id INTEGER PRIMARY KEY,conv_id TEXT,role TEXT,text TEXT,text_sha TEXT,ctype TEXT)');db.commit()
  with closing(sqlite3.connect(self.agent)) as db:
   db.execute('CREATE TABLE items(item_id INTEGER PRIMARY KEY,conv_id TEXT,role TEXT,text TEXT,text_sha TEXT,disposition TEXT)')
   db.execute('CREATE TABLE existing_marker(k TEXT PRIMARY KEY,value TEXT)');db.execute("INSERT INTO existing_marker VALUES('marker','untouched')");db.commit()
 def tearDown(self):self.temp.cleanup()
 def add(self,iid=1,ctype='source_review',disposition='proof',agent_changes=None,master_hash=None):
  body='Source claim remains unvalidated: '+str(iid);digest=hashlib.sha256(body.encode()).hexdigest()
  with closing(sqlite3.connect(self.master)) as db:
   db.execute('INSERT INTO items VALUES(?,?,?,?,?,?)',(iid,'source:'+str(iid),'file',body,master_hash or digest,ctype));db.commit()
  row={'item_id':iid,'conv_id':'source:'+str(iid),'role':'file','text':body,'text_sha':digest,'disposition':disposition};row.update(agent_changes or {})
  with closing(sqlite3.connect(self.agent)) as db:
   db.execute('INSERT INTO items VALUES(?,?,?,?,?,?)',tuple(row[k] for k in ('item_id','conv_id','role','text','text_sha','disposition')));db.commit()
 def agent_rows(self):
  with closing(sqlite3.connect(self.agent)) as db:return db.execute('SELECT * FROM items ORDER BY item_id').fetchall()
 def test_exact_review_types_clamped_and_legacy_unchanged(self):
  for ctype in ['source_review','source_review_pointer']:
   self.assertTrue(is_source_review(ctype))
   for derived in ['proof','confirmed','native_accepted',None,{'verdict':'accept'}]:self.assertEqual(source_review_disposition(ctype,derived),SOURCE_REVIEW_DISPOSITION)
  for ctype in [None,'text','Source_Review',[],{}]:
   self.assertFalse(is_source_review(ctype));self.assertEqual(source_review_disposition(ctype,'legacy'),'legacy')
 def test_repairs_only_matching_review_rows_and_preserves_master_and_legacy(self):
  self.add(1);self.add(2,'source_review_pointer',None);self.add(3,'text','proof')
  master_before=self.master.read_bytes();before=self.agent_rows()
  r=repair_review_dispositions(self.master,self.agent)
  self.assertEqual((r['checked'],r['matched'],r['repaired']),(2,2,2))
  after=self.agent_rows()
  for a,b in zip(before,after):self.assertEqual(a[:-1],b[:-1])
  self.assertEqual([r[-1] for r in after],[SOURCE_REVIEW_DISPOSITION,SOURCE_REVIEW_DISPOSITION,'proof'])
  self.assertEqual(master_before,self.master.read_bytes());self.assertFalse(r['native_admission']);self.assertFalse(r['canonical_acceptance'])
  with closing(sqlite3.connect(self.agent)) as db:self.assertEqual(db.execute("SELECT value FROM existing_marker WHERE k='marker'").fetchone()[0],'untouched')
 def test_id_identity_and_hash_collisions_remain_untouched(self):
  self.add(1,agent_changes={'conv_id':'other-object'})
  self.add(2,agent_changes={'role':'assistant'})
  self.add(3,agent_changes={'text_sha':'a'*64})
  self.add(4,agent_changes={'text':'altered text with old hash'})
  self.add(5,agent_changes={'text_sha':'b'*64},master_hash='b'*64)
  before=self.agent_rows();r=repair_review_dispositions(self.master,self.agent)
  self.assertEqual(r['repaired'],0);self.assertEqual(r['mismatches'],5);self.assertEqual(before,self.agent_rows())
 def test_idempotent_repeat_and_bounded_continuation(self):
  for i in range(1,5):self.add(i)
  first=repair_review_dispositions(self.master,self.agent,max_rows=2)
  self.assertEqual(first['repaired'],2);self.assertTrue(first['has_more']);self.assertEqual(first['next_after_item_id'],2)
  last=repair_review_dispositions(self.master,self.agent,max_rows=2,after_item_id=first['next_after_item_id'])
  self.assertEqual(last['repaired'],2);self.assertFalse(last['has_more'])
  again=repair_review_dispositions(self.master,self.agent)
  self.assertEqual(again['repaired'],0);self.assertEqual(again['already_unvalidated'],4)
 def test_missing_databases_never_created(self):
  missing=self.root/'missing.db'
  for a,b in [(missing,self.agent),(self.master,missing)]:
   with self.assertRaisesRegex(ValueError,'EXISTING_DATABASE_REQUIRED'):repair_review_dispositions(a,b)
   self.assertFalse(missing.exists())
 def test_incomplete_identity_and_oversize_source_are_not_repaired(self):
  self.add(1);self.add(2)
  with closing(sqlite3.connect(self.master)) as db:
   db.execute('UPDATE items SET conv_id=NULL WHERE item_id=1')
   text='x'*5000;db.execute('UPDATE items SET text=?,text_sha=? WHERE item_id=2',(text,hashlib.sha256(text.encode()).hexdigest()));db.commit()
  with closing(sqlite3.connect(self.agent)) as db:
   db.execute('UPDATE items SET conv_id=NULL WHERE item_id=1')
   db.execute('UPDATE items SET text=?,text_sha=? WHERE item_id=2',(text,hashlib.sha256(text.encode()).hexdigest()));db.commit()
  before=self.agent_rows();r=repair_review_dispositions(self.master,self.agent)
  self.assertEqual(r['repaired'],0);self.assertEqual(r['mismatches'],2);self.assertEqual(before,self.agent_rows())
 def test_refuses_same_database_or_wrong_schema_and_bad_budgets(self):
  with self.assertRaisesRegex(ValueError,'MASTER_AND_AGENT_MUST_DIFFER'):repair_review_dispositions(self.master,self.master)
  bad=self.root/'bad.db'
  with closing(sqlite3.connect(bad)) as db:db.execute('CREATE TABLE other(k TEXT)');db.commit()
  before=bad.read_bytes()
  with self.assertRaisesRegex(ValueError,'EXISTING_ITEMS_SCHEMA_REQUIRED'):repair_review_dispositions(self.master,bad)
  self.assertEqual(before,bad.read_bytes())
  for kw in [{'max_rows':True},{'max_rows':0},{'max_rows':10001},{'after_item_id':-1},{'after_item_id':True}]:
   with self.assertRaises(ValueError):repair_review_dispositions(self.master,self.agent,**kw)

if __name__=='__main__':unittest.main()
