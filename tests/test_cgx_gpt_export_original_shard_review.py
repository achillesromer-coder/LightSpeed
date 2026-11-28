"""Synthetic only: original owner-private exports are never included in Git/CI."""
import json
import tempfile
import unittest
from pathlib import Path
from cgx.load_minimum.gptExportShardReview import inspect_raw_shard,inspect_originals,IntakeHold,RECORD_HASH_ALGORITHM

def example(one="x"):
    return [{"id":one,"conversation_id":one,
             "mapping":{one:{"id":one,"parent":None,"message":None}},
             "title":"PRIVATE_TEST_ONLY"}]

def raw(obj):
    return json.dumps(obj,separators=(",",":"),ensure_ascii=False).encode("utf-8")

def declaration(blob,name="conversations-000.json"):
    return {"path":name,"declared_size_bytes":len(blob)}

def manifest(names,sizes):
    return raw({"version":1,"manifest_file":"export_manifest.json",
       "export_files":[{"path":p,"size_bytes":n} for p,n in zip(names,sizes)],
       "logical_files":{"conversations.json":{
           "files":names,"sharded":True,"shard_count":len(names)}}})

class OriginalShardReviewTests(unittest.TestCase):
    def test_canonical_algorithm_is_explicit_and_versioned(self):
        b=raw(example())
        row,_,_=inspect_raw_shard(b,declaration(b))
        self.assertEqual(RECORD_HASH_ALGORITHM,
                         "PYTHON_JSON_SORT_KEYS_COMPACT_UTF8_ALLOW_NAN_FALSE/1")
        self.assertEqual(row["canonical_record_hash_algorithm"],RECORD_HASH_ALGORITHM)
        self.assertEqual(row["node_identity_scope"],
                         "SHARD_FILENAME_PLUS_RECORD_ORDINAL_PLUS_NODE_KEY")

    def test_repeat_mapping_node_keys_are_source_scoped_not_deduplicated(self):
        recs=[
          {"id":"one","conversation_id":"one",
           "mapping":{"shared":{"id":"shared","message":None,"parent":None}}},
          {"id":"two","conversation_id":"two",
           "mapping":{"shared":{"id":"shared","message":None,"parent":None}}}
        ]
        b=raw(recs)
        item,record_ids,conversation_ids=inspect_raw_shard(b,declaration(b))
        self.assertEqual(item["records"],2)
        self.assertEqual(item["mapping_nodes"],2)
        self.assertEqual(len(record_ids),2)
        self.assertEqual(len(conversation_ids),2)
        self.assertFalse(item["native_dbr"])

    def test_valid_shard_is_private_non_native(self):
        b=raw(example())
        x,ids,convs=inspect_raw_shard(b,declaration(b))
        self.assertEqual(x["records"],1)
        self.assertEqual(x["mapping_nodes"],1)
        self.assertEqual(len(ids),1);self.assertEqual(len(convs),1)
        self.assertFalse(x["native_dbr"])
        self.assertFalse(x["source_body_in_receipt"])
        self.assertNotIn("title",json.dumps(x))
    def test_invalid_shard_path_held(self):
        b=raw(example())
        with self.assertRaises(IntakeHold):
            inspect_raw_shard(b,declaration(b,"../private.json"))
    def test_changed_raw_size_held(self):
        b=raw(example())
        with self.assertRaises(IntakeHold):
            inspect_raw_shard(b+b" ",declaration(b))
    def test_boolean_declared_size_held(self):
        with self.assertRaises(IntakeHold):
            inspect_raw_shard(b"x",{"path":"conversations-000.json","declared_size_bytes":True})
    def test_bad_json_held(self):
        b=b"{bad"
        with self.assertRaises(IntakeHold): inspect_raw_shard(b,declaration(b))
    def test_nonfinite_json_held(self):
        b=b'[{"id":"a","conversation_id":"a","mapping":{},"x":NaN}]'
        with self.assertRaises(IntakeHold): inspect_raw_shard(b,declaration(b))
    def test_array_root_required(self):
        b=b"{}"
        with self.assertRaises(IntakeHold): inspect_raw_shard(b,declaration(b))
    def test_empty_array_held(self):
        b=b"[]"
        with self.assertRaises(IntakeHold): inspect_raw_shard(b,declaration(b))
    def test_record_type_held(self):
        b=raw([7])
        with self.assertRaises(IntakeHold): inspect_raw_shard(b,declaration(b))
    def test_identity_required(self):
        b=raw([{"id":"a","mapping":{}}])
        with self.assertRaises(IntakeHold): inspect_raw_shard(b,declaration(b))
    def test_intra_shard_duplicate_denied(self):
        b=raw(example()+example())
        with self.assertRaises(IntakeHold): inspect_raw_shard(b,declaration(b))
    def test_mapping_dictionary_required(self):
        b=raw([{"id":"a","conversation_id":"a","mapping":[]}])
        with self.assertRaises(IntakeHold): inspect_raw_shard(b,declaration(b))
    def test_semantic_key_order_digest_is_stable(self):
        a=raw([{"id":"a","conversation_id":"a","mapping":{},"z":3}])
        b=raw([{"z":3,"mapping":{},"conversation_id":"a","id":"a"}])
        x=inspect_raw_shard(a,declaration(a))[0]
        y=inspect_raw_shard(b,declaration(b))[0]
        self.assertEqual(x["record_index"][0]["canonical_sha256"],
                         y["record_index"][0]["canonical_sha256"])
        self.assertNotEqual(x["original_sha256"],y["original_sha256"])
    def test_two_shard_source_passes_without_any_promotion(self):
        a=raw(example("first"));b=raw(example("second"))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            (path/"conversations-000.json").write_bytes(a)
            (path/"conversations-001.json").write_bytes(b)
            z=inspect_originals(manifest(["conversations-000.json","conversations-001.json"],
                                         [len(a),len(b)]),path)
            self.assertEqual(z["shard_count"],2)
            self.assertEqual(z["records"],2)
            self.assertEqual(z["root"],"cgx:root:cognigrex")
            for key in ("public_published","model_trained","canonical_write","mint",
                        "dbr_verified","node_restore_verified","owner_rights_accepted"):
                self.assertFalse(z[key])
    def test_duplicate_between_shards_held(self):
        a=raw(example());b=raw(example())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            (path/"conversations-000.json").write_bytes(a)
            (path/"conversations-001.json").write_bytes(b)
            with self.assertRaises(IntakeHold):
                inspect_originals(manifest(["conversations-000.json","conversations-001.json"],
                                           [len(a),len(b)]),path)
    def test_missing_shard_held(self):
        a=raw(example())
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(IntakeHold):
                inspect_originals(manifest(["conversations-000.json"],[len(a)]),Path(td))
    def test_symlink_shard_held(self):
        a=raw(example())
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/"real.json").write_bytes(a)
            (p/"conversations-000.json").symlink_to(p/"real.json")
            with self.assertRaises(IntakeHold):
                inspect_originals(manifest(["conversations-000.json"],[len(a)]),p)

if __name__=="__main__":unittest.main()
