"""Read pending inputs from existing advisory agent stores without cursor data loss."""
import sqlite3
from contextlib import closing
from pathlib import Path

SOURCE_REVIEW_DISPOSITION='source_review_unvalidated'

def _filter_and_order(db,source_review_only):
    if type(source_review_only) is not bool:raise ValueError('INVALID_SOURCE_REVIEW_FILTER')
    has_disposition=any(row[1]=='disposition' for row in db.execute('PRAGMA table_info(items)'))
    if source_review_only and not has_disposition:return '0','i.item_id',()
    if not has_disposition:return '1','i.item_id',()
    if source_review_only:return 'i.disposition=?','i.item_id',(SOURCE_REVIEW_DISPOSITION,)
    return '1',"CASE WHEN i.disposition='source_review_unvalidated' THEN 0 ELSE 1 END,i.item_id",()

def pending_rows(source_db,review_db,limit=3,*,source_review_only=False):
    if type(limit) is not int or not 1<=limit<=64:raise ValueError('INVALID_PENDING_LIMIT')
    if type(source_review_only) is not bool:raise ValueError('INVALID_SOURCE_REVIEW_FILTER')
    with closing(sqlite3.connect(Path(source_db).absolute().as_uri()+'?mode=ro',uri=True,timeout=10)) as db:
        db.execute('ATTACH DATABASE ? AS reviewed',(Path(review_db).absolute().as_uri()+'?mode=ro',))
        condition,order,values=_filter_and_order(db,source_review_only)
        return db.execute('SELECT i.item_id,i.text FROM items i WHERE NOT EXISTS (SELECT 1 FROM reviewed.proposals p WHERE p.item_id=i.item_id) AND '+condition+' AND length(i.text) BETWEEN 120 AND 4000 ORDER BY '+order+' LIMIT ?',(*values,limit)).fetchall()

def pending_count(source_db,review_db,*,source_review_only=False):
    if type(source_review_only) is not bool:raise ValueError('INVALID_SOURCE_REVIEW_FILTER')
    with closing(sqlite3.connect(Path(source_db).absolute().as_uri()+'?mode=ro',uri=True,timeout=10)) as db:
        db.execute('ATTACH DATABASE ? AS reviewed',(Path(review_db).absolute().as_uri()+'?mode=ro',))
        condition,_,values=_filter_and_order(db,source_review_only)
        return db.execute('SELECT count(*) FROM items i WHERE NOT EXISTS (SELECT 1 FROM reviewed.proposals p WHERE p.item_id=i.item_id) AND '+condition+' AND length(i.text) BETWEEN 120 AND 4000',values).fetchone()[0]
