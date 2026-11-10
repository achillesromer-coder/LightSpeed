"""Read pending inputs from existing advisory agent stores without cursor data loss."""
import sqlite3
from contextlib import closing
from pathlib import Path

def pending_rows(source_db,review_db,limit=3):
    if type(limit) is not int or not 1<=limit<=64:raise ValueError('INVALID_PENDING_LIMIT')
    with closing(sqlite3.connect(Path(source_db).absolute().as_uri()+'?mode=ro',uri=True,timeout=10)) as db:
        db.execute('ATTACH DATABASE ? AS reviewed',(Path(review_db).absolute().as_uri()+'?mode=ro',))
        return db.execute('SELECT i.item_id,i.text FROM items i WHERE length(i.text) BETWEEN 120 AND 4000 AND NOT EXISTS (SELECT 1 FROM reviewed.proposals p WHERE p.item_id=i.item_id) ORDER BY i.item_id LIMIT ?',(limit,)).fetchall()

def pending_count(source_db,review_db):
    with closing(sqlite3.connect(Path(source_db).absolute().as_uri()+'?mode=ro',uri=True,timeout=10)) as db:
        db.execute('ATTACH DATABASE ? AS reviewed',(Path(review_db).absolute().as_uri()+'?mode=ro',))
        return db.execute('SELECT count(*) FROM items i WHERE length(i.text) BETWEEN 120 AND 4000 AND NOT EXISTS (SELECT 1 FROM reviewed.proposals p WHERE p.item_id=i.item_id)').fetchone()[0]
