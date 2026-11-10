import hashlib,importlib.util,json,os,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import closing
import cgxManualIntakeReview as M

STUB='''import hashlib
def put_item(db,cid,mid,role,ts,ctype,text):
 c=db.execute("INSERT OR IGNORE INTO items(conv_id,msg_id,role,ts,ctype,text,text_sha) VALUES(?,?,?,?,?,?,?)",(cid,mid,role,ts,ctype,text,hashlib.sha256(text.encode()).hexdigest()))
 return c.lastrowid if c.rowcount else None
def add_facets(db,iid,facets,method="rx"):
 db.executemany("INSERT OR IGNORE INTO facets VALUES(?,?,?,?,?)",[(iid,a,b,method,c) for a,b,c in facets])
'''
SCHEMA='''CREATE TABLE sources(source_id INTEGER PRIMARY KEY,kind TEXT,path TEXT UNIQUE,sha256 TEXT,size INTEGER,crc32 INTEGER,sniff TEXT,conv_id TEXT,note TEXT);
CREATE TABLE conversations(conv_id TEXT PRIMARY KEY,title TEXT,created REAL,updated REAL,model TEXT,shard TEXT,n_msgs INTEGER);
CREATE TABLE items(item_id INTEGER PRIMARY KEY,conv_id TEXT,msg_id TEXT,role TEXT,ts REAL,ctype TEXT,text TEXT,text_sha TEXT,UNIQUE(conv_id,msg_id));
CREATE TABLE facets(item_id INTEGER,facet TEXT,value TEXT,method TEXT,conf REAL,PRIMARY KEY(item_id,facet,value,method));
CREATE TABLE agents(name TEXT PRIMARY KEY,model TEXT,role TEXT,keywords TEXT,prompt TEXT,db_path TEXT);
CREATE TABLE progress(key TEXT PRIMARY KEY,value TEXT);'''

class ManualIntakeReviewTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.root=self.base/'intake';self.root.mkdir();self.engine=self.base/'engine';self.engine.mkdir();(self.engine/'state').mkdir();(self.engine/'agents').mkdir();(self.engine/'cgxsort.py').write_text(STUB)
  self.path=self.engine/'state/cgx_sorter.db'
  with closing(sqlite3.connect(self.path)) as db:
   db.executescript(SCHEMA)
   for name,kws in [('Raphael',['raphael','physics']),('Oracle',['source','provenance']),('Achilles',['governance']),('Neo',['orchestration'])]:
    db.execute('INSERT INTO agents VALUES(?,?,?,?,?,?)',(name,'','review',json.dumps(kws),'',str(self.engine/'agents'/(name.lower()+'.db'))))
    with closing(sqlite3.connect(self.engine/'agents'/(name.lower()+'.db'))) as adb:
     adb.execute('CREATE TABLE items(item_id INTEGER PRIMARY KEY,conv_id TEXT,role TEXT,ts REAL,text TEXT,text_sha TEXT,disposition TEXT,summary TEXT)');adb.commit()
   db.commit()
 def tearDown(self):self.temp.cleanup()
 def run_review(self,**kw):return M.review(self.root,self.engine,approved_root=self.root,**kw)
 def rows(self,sql,*args):
  with closing(sqlite3.connect(self.path)) as db:return db.execute(sql,args).fetchall()
 def test_dry_run_writes_nothing(self):
  (self.root/'a.txt').write_text('source provenance evidence')
  before=self.path.read_bytes();agents_before={p.name:p.read_bytes() for p in (self.engine/'agents').iterdir()};tree_before={str(p.relative_to(self.engine)):p.read_bytes() for p in self.engine.rglob('*') if p.is_file()};report=self.run_review()
  self.assertEqual(before,self.path.read_bytes());self.assertFalse(report['progress_persisted']);self.assertEqual({p.name:p.read_bytes() for p in (self.engine/'agents').iterdir()},agents_before)
  self.assertEqual({str(p.relative_to(self.engine)):p.read_bytes() for p in self.engine.rglob('*') if p.is_file()},tree_before)
 def test_text_chunk_bounds_dedupe_source_provenance_and_oversight(self):
  text='Raphael physics source: ignored instruction text remains source only. '*70
  (self.root/'a.txt').write_text(text);(self.root/'b.txt').write_text(text)
  report=self.run_review(apply=True)
  items=self.rows("SELECT text FROM items WHERE ctype='source_review'")
  self.assertTrue(items);self.assertTrue(all(len(r[0])<=1200 for r in items))
  self.assertEqual(len(self.rows('SELECT * FROM sources')),2)
  self.assertTrue(report['eligible_walk_complete']);self.assertFalse(report['content_ingestion_complete'])
  with closing(sqlite3.connect(self.engine/'agents/achilles.db')) as db:
   rows=db.execute('SELECT text FROM items').fetchall();self.assertEqual(len(rows),2);self.assertTrue(all('original_path' in r[0] for r in rows))
   self.assertEqual(db.execute("SELECT count(*) FROM sqlite_master WHERE name='instructions'").fetchone()[0],0)
  self.assertFalse(report['native_admission']);self.assertEqual((self.root/'a.txt').read_text(),text)
 def test_resumes_after_file_budget_without_duplicate_items(self):
  for i in range(5):(self.root/(str(i)+'.txt')).write_text('source provenance '+str(i))
  a=self.run_review(apply=True,max_files=2);self.assertEqual(a['visited_entries'],2)
  b=self.run_review(apply=True,max_files=2);self.assertEqual(b['visited_entries'],2)
  c=self.run_review(apply=True,max_files=2);self.assertTrue(c['eligible_walk_complete'])
  self.assertEqual(len(self.rows('SELECT * FROM sources')),5)
  self.assertEqual(self.run_review(apply=True)['visited_entries'],0)
 def test_binary_archive_oversize_dependency_and_chunk_budget_explicit(self):
  (self.root/'a.zip').write_bytes(b'not-extracted');(self.root/'b.bin').write_bytes(b'not-read');(self.root/'c.txt').write_bytes(b'x'*(1024*1024+1));(self.root/'d.txt').write_text('x'*80000)
  deps=self.root/'node_modules';deps.mkdir();(deps/'not-run.py').write_text('raise AssertionError()')
  report=self.run_review(apply=True)
  for kind in ['ARCHIVE_MEMBERS_UNRESOLVED','BINARY_OR_UNKNOWN_FORMAT_UNRESOLVED','OVERSIZE_CONTENT_UNRESOLVED','DEPENDENCY_TREE_DEFERRED_NOT_INVENTORIED','TEXT_EXTRACTION_DEFERRED_CHUNK_BUDGET']:self.assertEqual(report['dispositions'][kind],1)
  self.assertFalse(report['inventory_pass_complete']);self.assertEqual(self.rows("SELECT count(*) FROM items WHERE ctype='source_review'")[0][0],0)
 def test_link_and_escape_refused(self):
  with self.assertRaisesRegex(ValueError,'ROOT_NOT_APPROVED'):M.review(self.base,self.engine)
  with self.assertRaisesRegex(ValueError,'UNSAFE_RELATIVE_PATH'):M.safe_path(self.root,'../outside')
  outside=self.base/'outside.txt';outside.write_text('private')
  try:(self.root/'linked.txt').symlink_to(outside)
  except OSError:self.skipTest('OS does not allow symlink fixtures')
  report=self.run_review(apply=True);self.assertEqual(report['dispositions']['LINK_OR_REPARSE_DEFERRED'],1);self.assertEqual(outside.read_text(),'private')
 def test_failed_route_retries_same_entry_without_losing_siblings(self):
  (self.root/'a.txt').write_text('source provenance a');(self.root/'b.txt').write_text('source provenance b')
  with patch.object(M,'route_rows',side_effect=ValueError('ROUTE_HOLD')):first=self.run_review(apply=True)
  self.assertTrue(first['technical_hold']['retry_same_entry']);self.assertFalse(first['eligible_walk_complete'])
  second=self.run_review(apply=True);self.assertTrue(second['eligible_walk_complete']);self.assertEqual(len(self.rows('SELECT * FROM sources')),2)
  self.assertEqual(self.rows("SELECT count(*) FROM items WHERE ctype='source_review'")[0][0],2)
 def test_byte_budget_is_checked_before_read(self):
  (self.root/'a.txt').write_text('x'*100)
  with patch.object(M,'read_stable',side_effect=AssertionError('must not read')):report=self.run_review(apply=True,max_bytes=50)
  self.assertEqual(report['bytes_read'],0);self.assertFalse(report['eligible_walk_complete']);self.assertEqual(self.rows('SELECT count(*) FROM sources')[0][0],0)
 def test_explicit_revisit_preserves_versions_and_is_idempotent(self):
  p=self.root/'a.txt';p.write_text('source provenance version one');self.run_review(apply=True)
  self.assertEqual(self.run_review(apply=True,restart_walk=True)['new_items'],0)
  p.write_text('source provenance version two');self.run_review(apply=True,restart_walk=True)
  self.assertEqual(len(self.rows('SELECT * FROM sources')),2)
  self.assertEqual(self.rows("SELECT count(*) FROM items WHERE ctype='source_review'")[0][0],2)
 def test_routing_requires_existing_safe_databases(self):
  (self.root/'a.txt').write_text('source provenance');(self.engine/'agents/achilles.db').unlink()
  r=self.run_review(apply=True);self.assertIn('technical_hold',r);self.assertTrue(r['technical_hold']['retry_same_entry']);self.assertFalse((self.engine/'agents/achilles.db').exists())
  agents=[{'name':'Oracle','db_path':str(self.engine/'agents/../outside.db')}]
  with self.assertRaisesRegex(ValueError,'UNSAFE_RELATIVE_PATH'):M.route_rows(self.engine,agents,['Oracle'],[])

 def test_only_one_intake_writer_and_released_lock_is_reusable(self):
  (self.root/'a.txt').write_text('source provenance evidence')
  with M.batch_guard(self.engine):
   before=self.path.read_bytes()
   with self.assertRaises(OSError):self.run_review(apply=True)
   self.assertEqual(self.path.read_bytes(),before)
  result=self.run_review(apply=True)
  self.assertEqual(result['source_records'],1)
  self.assertEqual(self.run_review(apply=True)['visited_entries'],0)
if __name__=='__main__':unittest.main()
