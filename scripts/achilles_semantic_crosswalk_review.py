#!/usr/bin/env python3
"""Private CGX R1 -> candidate R2 longitudinal source-relationship crosswalk.

No original-message content is exported; no self-acceptance, native DBR,
training, source move or public access. All relationships are lexical or
ancestry-based discovery candidates requiring independent review.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import argparse, datetime as dt, hashlib, itertools, json, pathlib, sqlite3

SCHEMA = "CGX-ACHILLES-HISTORICAL-CROSSWALK/0.1"


def candidate_crosswalk(db_path: pathlib.Path) -> dict:
    if not db_path.is_file() or db_path.is_symlink():
        raise ValueError("PRIVATE_R1_DB_MISSING")
    db = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    db.execute("PRAGMA query_only=ON")
    try:
        shards = db.execute(
            "SELECT name,sha256,bytes,state FROM shard ORDER BY name").fetchall()
        if len(shards) != 12 or any(x[3] != "VERIFIED_R1_COMMITTED" for x in shards):
            raise ValueError("SOURCE_COVERAGE_INCOMPLETE")
        family_stats = defaultdict(lambda: {"user_messages": 0, "assistant_messages": 0,
                                            "user_words": 0, "assistant_words": 0,
                                            "first_user_at": None, "last_user_at": None,
                                            "first_user_ref": None, "last_user_ref": None,
                                            "first_assistant_at": None,
                                            "last_assistant_at": None})
        msg_families = defaultdict(set)
        for mid, family, score, role, words, stamp in db.execute(
            "SELECT f.message_id,f.family,f.score,m.role,m.words,m.created "
            "FROM family_candidate f JOIN message m ON m.id=f.message_id"):
            msg_families[mid].add(family)
            stats = family_stats[family]
            label = "user" if role == "user" else "assistant"
            stats[label + "_messages"] += 1
            stats[label + "_words"] += words
            if stamp is not None:
                for side in ("first", "last"):
                    key = side + "_" + label + "_at"
                    if stats[key] is None or (stamp < stats[key] if side == "first" else stamp > stats[key]):
                        stats[key] = stamp
                        if label == "user":
                            stats[side + "_user_ref"] = mid
        overlap = Counter()
        for families in msg_families.values():
            for a,b in itertools.combinations(sorted(families),2):
                overlap[(a,b)] += 1
        conversation_pairs = Counter()
        paired = 0
        distinct_owner = set()
        for prompt_id, response_id in db.execute(
            "SELECT prompt_id,response_id FROM prompt_response"):
            paired += 1
            pf, rf = msg_families.get(prompt_id,set()), msg_families.get(response_id,set())
            if pf:
                distinct_owner.add(prompt_id)
            for a in pf:
                for b in rf:
                    conversation_pairs[(a,b)] += 1
        by_year = defaultdict(lambda: {"user_messages": 0, "assistant_messages": 0,
                                       "user_words": 0, "assistant_words": 0})
        for year, role, count, words in db.execute(
            "SELECT strftime('%Y',datetime(created,'unixepoch')),role,"
            "count(*),coalesce(sum(words),0) FROM message "
            "WHERE role IN ('user','assistant') GROUP BY 1,2"):
            if not year or year not in {"2022","2023","2024","2025","2026"}:
                continue
            label = "user" if role == "user" else "assistant"
            by_year[year][label + "_messages"] = count
            by_year[year][label + "_words"] = words
        def date(ts):
            return dt.datetime.fromtimestamp(float(ts),dt.timezone.utc).isoformat() if ts is not None else None
        return {
            "schema": SCHEMA,
            "stage": "PRIVATE_CANDIDATE_R2_DISCOVERY_NOT_ACCEPTED",
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source_shards": [{"file":n,"sha256":h,"bytes":b} for n,h,b,_ in shards],
            "conversations": db.execute("SELECT count(*) FROM conversation").fetchone()[0],
            "unique_messages": db.execute("SELECT count(*) FROM message").fetchone()[0],
            "prompt_response_links": paired,
            "unique_user_prompt_refs_with_family": len(distinct_owner),
            "annual_visible_text": {k:by_year[k] for k in sorted(by_year)},
            "family_counts": {
                f: {**{k:v for k,v in stats.items() if not k.endswith("_at")},
                    **{k:date(v) for k,v in stats.items() if k.endswith("_at")}}
                for f,stats in sorted(family_stats.items())
            },
            "lexical_family_intersections": [
                {"a":a,"b":b,"shared_message_count":n,"state":"LEXICAL_CANDIDATE"}
                for (a,b),n in overlap.most_common(65)],
            "user_to_assistant_family_relations": [
                {"user_family":a,"assistant_family":b,"prompt_response_link_count":n,
                 "state":"ROLE_DISTINCT_ANCESTRY_CANDIDATE"}
                for (a,b),n in conversation_pairs.most_common(100)],
            "method": {
                "family_membership": "Keyword occurrence scores from the existing private R1 ingestor; not an ontology or authority source",
                "relations": "Exact message-id parent-child ancestor chains and family keyword overlaps; not inferred private thoughts",
                "date": "Original explicit Unix timestamps when available, not publication/verification time",
                "truth": "Owner requests, assistant claims, and real provider execution are never conflated",
                "substantive_acceptance": False, "native_mint": False,
                "free_source_training": "NOT_STARTED_NOT_AUTHORISED_BY_INGESTION"
            }
        }
    finally:
        db.close()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True, type=pathlib.Path)
    p.add_argument("--output", required=True, type=pathlib.Path)
    args = p.parse_args()
    if not args.output.parent.is_dir() or args.output.exists() or args.output.resolve().parent != args.db.resolve().parent:
        raise ValueError("OUTPUT_PRIVATE_PATH_OR_IDEMPOTENCY_HOLD")
    output = candidate_crosswalk(args.db)
    temp = args.output.with_suffix(args.output.suffix+".tmp")
    temp.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    temp.replace(args.output)
    print(json.dumps({"schema":SCHEMA,"state":output["stage"],
                      "family_count":len(output["family_counts"]),
                      "lexical_intersections":len(output["lexical_family_intersections"]),
                      "prompt_response_links":output["prompt_response_links"],
                      "output":str(args.output),"native_mint":False}))


if __name__=="__main__":
    main()
