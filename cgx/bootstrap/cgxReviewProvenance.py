"""Preserve unvalidated review provenance in existing resident source databases.

This helper does not create a database/table, change source content, invoke a
model, grant canonical authority, or start a worker. The master is attached
read-only. Repair changes only existing matching agent disposition values.
"""
from __future__ import annotations
import hashlib
import os
import re
import sqlite3
import stat
from pathlib import Path

SOURCE_REVIEW_TYPES=('source_review','source_review_pointer')
SOURCE_REVIEW_DISPOSITION='source_review_unvalidated'
MAX_REVIEW_TEXT_CHARS=4096

def is_source_review(ctype):
    """Only exact typed review labels are eligible; model wording is not authority."""
    return isinstance(ctype,str) and ctype in SOURCE_REVIEW_TYPES

def source_review_disposition(ctype,derived):
    """Clamp review input irrespective of model-derived classification.

    Existing non-review behavior is deliberately unchanged, including None.
    """
    return SOURCE_REVIEW_DISPOSITION if is_source_review(ctype) else derived

def _existing_database(path):
    path=Path(path).absolute()
    try:info=path.lstat()
    except FileNotFoundError:raise ValueError('EXISTING_DATABASE_REQUIRED') from None
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0)&0x400:
        raise ValueError('REGULAR_NONLINK_DATABASE_REQUIRED')
    return path

def _check_columns(db,schema,required):
    # schema is one of two fixed internal names, never caller input.
    columns={row[1]:row for row in db.execute('PRAGMA '+schema+'.table_info(items)')}
    if not required.issubset(columns) or columns['item_id'][5]!=1:
        raise ValueError('EXISTING_ITEMS_SCHEMA_REQUIRED')

def _content_hash_matches(text,digest):
    return (isinstance(text,str) and isinstance(digest,str) and
            re.fullmatch(r'[0-9a-f]{64}',digest) is not None and
            hashlib.sha256(text.encode('utf-8')).hexdigest()==digest)

def repair_review_dispositions(master_db,agent_db,*,max_rows=1000,after_item_id=0):
    """Repair one bounded page of exact-matching existing review inputs.

    Match item_id, conversation identity, role, declared hash and actual text
    hashes. Collisions and unverified hashes remain untouched. Only the agent
    disposition column is updated. Returned ``next_after_item_id`` supports a
    caller-owned continuation; ``has_more`` is not a completion/admission claim.
    Call after stopping relevant writers or under the existing supervisor lock.
    """
    if type(max_rows) is not int or not 1<=max_rows<=10000:
        raise ValueError('INVALID_ROW_BUDGET')
    if type(after_item_id) is not int or after_item_id<0:
        raise ValueError('INVALID_CONTINUATION')
    master=_existing_database(master_db);agent=_existing_database(agent_db)
    if os.path.samefile(master,agent):raise ValueError('MASTER_AND_AGENT_MUST_DIFFER')
    report={'schema':'CGX-SOURCE-REVIEW-PROVENANCE-REPAIR/0.1',
        'checked':0,'matched':0,'repaired':0,'already_unvalidated':0,
        'mismatches':0,'mismatch_samples':[],'has_more':False,
        'next_after_item_id':after_item_id,'source_changed':False,
        'new_database':False,'new_table':False,'native_admission':False,
        'canonical_acceptance':False,'updated_columns':['disposition']}
    db=sqlite3.connect(agent.as_uri()+'?mode=rw',uri=True,timeout=5)
    try:
        db.execute('ATTACH DATABASE ? AS review_source',(master.as_uri()+'?mode=ro',))
        _check_columns(db,'main',{'item_id','conv_id','role','text','text_sha','disposition'})
        _check_columns(db,'review_source',{'item_id','conv_id','role','text','text_sha','ctype'})
        # Reserve this agent DB for the short repair, keeping reads and changes
        # in one snapshot. The attached source remains mode=ro.
        db.execute('BEGIN IMMEDIATE')
        rows=db.execute('''SELECT m.item_id,m.conv_id,m.role,
            CASE WHEN length(m.text)<=4096 THEN m.text ELSE NULL END,m.text_sha,m.ctype,
            a.conv_id,a.role,CASE WHEN length(a.text)<=4096 THEN a.text ELSE NULL END,a.text_sha,a.disposition
            FROM review_source.items AS m JOIN main.items AS a ON a.item_id=m.item_id
            WHERE m.item_id>? AND m.ctype IN ('source_review','source_review_pointer')
            ORDER BY m.item_id LIMIT ?''',(after_item_id,max_rows+1)).fetchall()
        report['has_more']=len(rows)>max_rows
        for row in rows[:max_rows]:
            iid,mc,mr,mt,mh,ctype,ac,ar,at,ah,disposition=row
            report['checked']+=1;report['next_after_item_id']=iid
            reason=None
            if type(iid) is not int or iid<=0 or not isinstance(mc,str) or not mc or not isinstance(mr,str) or not mr:reason='SOURCE_IDENTITY_UNVERIFIED'
            elif (mc,mr)!=(ac,ar):reason='IDENTITY_MISMATCH'
            elif mh!=ah:reason='DECLARED_HASH_MISMATCH'
            elif not _content_hash_matches(mt,mh):reason='MASTER_CONTENT_HASH_UNVERIFIED'
            elif not _content_hash_matches(at,ah):reason='AGENT_CONTENT_HASH_UNVERIFIED'
            if reason:
                report['mismatches']+=1
                if len(report['mismatch_samples'])<20:report['mismatch_samples'].append({'item_id':iid,'reason':reason})
                continue
            report['matched']+=1
            required=source_review_disposition(ctype,disposition)
            if disposition==required:report['already_unvalidated']+=1
            else:
                changed=db.execute('UPDATE main.items SET disposition=? WHERE item_id=?',(required,iid)).rowcount
                if changed!=1:raise RuntimeError('REPAIR_ROW_IDENTITY_CHANGED')
                report['repaired']+=changed
        db.commit()
        return report
    except BaseException:
        db.rollback()
        raise
    finally:db.close()
