"""LOAD R1 source-backed selective hydration: synthetic data only, no private export."""
from __future__ import annotations
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from cgx.load_minimum.gptExportSparseHydrate import (
    R1_PARENT, R1_SCHEMA, SCHEMA, IntakeHold,
    validate_sparse_index, verify_all_originals, resolve_private_record,
)
from cgx.load_minimum.gptExportShardReview import RECORD_HASH_ALGORITHM

def blob(value):
    return json.dumps(value, separators=(",",":"), ensure_ascii=False).encode("utf-8")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def record(key):
    return {"id":key,"conversation_id":key,"mapping":{
        "shared": {"id":"shared", "parent":None,"message":None}},
        "title":"SYNTHETIC_ONLY", "payload": {"string":f"record-{key}"}}

def fixtures(directory: Path):
    rows = [[record("one"),record("two")],[record("three")]]
    names = [f"conversations-{i:03d}.json" for i in range(len(rows))]
    raw_files = [blob(row) for row in rows]
    for name, raw in zip(names, raw_files):
        (directory/name).write_bytes(raw)
    manifest=blob({"version":1,"manifest_file":"export_manifest.json",
        "export_files":[{"path":name,"size_bytes":len(raw)} for name,raw in zip(names,raw_files)],
        "logical_files":{"conversations.json":{
            "files":names,"sharded":True,"shard_count":len(names)}}})
    shards = []
    for name,raw,items in zip(names,raw_files,rows):
        records = []
        for pos,item in enumerate(items):
            canonical=json.dumps(item,sort_keys=True,separators=(",",":"),
                                 ensure_ascii=False,allow_nan=False).encode("utf-8")
            records.append({
                "ordinal":pos,"mapping_nodes":len(item["mapping"]),
                "source_native_object_id_admitted":False,
                "source_record_bytes_canonical":len(canonical),
                "source_record_sha256":sha(canonical)})
        shards.append({
            "filename":name,"R0_sha256":sha(raw),"record_count":len(items),
            "reconstruction":"ORIGINAL_R0_REQUIRED_FOR_LOSSLESS_HYDRATION",
            "source_rights":"UNRESOLVED_PRIVATE_DO_NOT_PUBLISH","records":records})
    index={
        "schema":R1_SCHEMA,"canonical_parent":R1_PARENT,
        "canonical_record_encoding":RECORD_HASH_ALGORITHM,
        "source_manifest_sha256":sha(manifest),
        "source_sha256_algorithm":"SHA-256 over original unmodified raw file bytes",
        "source_body_copied_into_index":False,
        "source_message_content_extracted":False,
        "native_mint":False,"dbr_written":False,
        "full_lossless_reconstruction_without_R0":False,
        "shards":shards,"totals":{
            "bytes":sum(map(len,raw_files)),"files":len(shards),
            "records":sum(map(len,rows)),"mapping_nodes":3}}
    return manifest,index,rows

class SparseHydrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name)
        self.manifest,self.index,self.rows=fixtures(self.directory)
    def index_bytes(self): return blob(self.index)
    def hydrate(self, **patch):
        args={"shard_name":"conversations-000.json","ordinal":0,
              "authorize_read": lambda _:True}
        args.update(patch)
        return resolve_private_record(self.manifest,self.index_bytes(),
                                      self.directory,**args)

    def test_validate_known_private_source_scoped_index(self):
        m,i=validate_sparse_index(self.manifest,self.index_bytes())
        self.assertEqual(len(m["conversation_shards"]),2)
        self.assertEqual(i["totals"]["records"],3)

    def test_compare_every_original_to_sparse_canonical_index(self):
        result=verify_all_originals(self.manifest,self.index_bytes(),self.directory)
        self.assertEqual(result["records"],3)
        self.assertEqual(result["shards"],2)
        self.assertEqual(result["mapping_nodes"],3)
        self.assertEqual(result["state"],
                         "OWNER_PRIVATE_R0_R1_CANONICAL_PARITY_VERIFIED_NOT_NATIVE")
        for prop in ("native_dbr_verified","minted","published","raw_messages_in_receipt"):
            self.assertFalse(result[prop])

    def test_selective_source_record_structural_roundtrip(self):
        original,receipt=self.hydrate()
        self.assertEqual(original,self.rows[0][0])
        self.assertEqual(receipt["source_ordinal"],0)
        self.assertEqual(receipt["canonical_root"],R1_PARENT)
        self.assertFalse(receipt["native_dbr_verified"])
        self.assertFalse(receipt["private_record_in_receipt"])
        self.assertNotIn("SYNTHETIC_ONLY",json.dumps(receipt))
        self.assertEqual(receipt["schema"],SCHEMA)

    def test_selective_other_shard_record(self):
        original,receipt=self.hydrate(shard_name="conversations-001.json",ordinal=0)
        self.assertEqual(original,self.rows[1][0])
        self.assertEqual(receipt["source_shard"],"conversations-001.json")

    def test_denied_private_host_policy(self):
        with self.assertRaises(IntakeHold):
            self.hydrate(authorize_read=lambda _:False)
    def test_policy_integer_one_not_boolean_true(self):
        with self.assertRaises(IntakeHold):
            self.hydrate(authorize_read=lambda _:1)
    def test_missing_callback_denied(self):
        with self.assertRaises(IntakeHold):
            self.hydrate(authorize_read=None)
    def test_callback_exception_fail_closed(self):
        def fail(_):raise RuntimeError("no session")
        with self.assertRaises(IntakeHold):
            self.hydrate(authorize_read=fail)
    def test_callback_runs_before_original_source_io(self):
        (self.directory/"conversations-000.json").unlink()
        with self.assertRaisesRegex(IntakeHold,"PRIVATE_HOST_POLICY_DENIED"):
            self.hydrate(authorize_read=lambda _:False)

    def test_reject_bad_root(self):
        self.index["canonical_parent"]="other"
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_new_index_schema(self):
        self.index["schema"]="PROMOTED/9"
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_wrong_canonical_encoding(self):
        self.index["canonical_record_encoding"]="orjson-v1"
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_manifest_binding(self):
        self.index["source_manifest_sha256"]="0"*64
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_shard_sequence_loss(self):
        self.index["shards"]=list(reversed(self.index["shards"]))
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_duplicate_ordinal(self):
        self.index["shards"][0]["records"][1]["ordinal"]=0
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_bool_ordinal(self):
        with self.assertRaises(IntakeHold):self.hydrate(ordinal=True)
    def test_reject_traversal_source(self):
        with self.assertRaises(IntakeHold):
            self.hydrate(shard_name="../../secrets")
    def test_reject_missing_source(self):
        (self.directory/"conversations-000.json").unlink()
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_source_symlink(self):
        target=self.directory/"source_backup.json"
        (self.directory/"conversations-000.json").rename(target)
        (self.directory/"conversations-000.json").symlink_to(target)
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_original_source_byte_drift_same_length(self):
        p=self.directory/"conversations-000.json"
        data=p.read_bytes();p.write_bytes(data.replace(b"record-one",b"record-two",1))
        self.assertEqual(len(p.read_bytes()),len(data))
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_forged_original_sha(self):
        self.index["shards"][0]["R0_sha256"]="a"*64
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_tampered_canonical_record_digest(self):
        self.index["shards"][0]["records"][0]["source_record_sha256"]="b"*64
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_incorrect_canonical_record_length(self):
        self.index["shards"][0]["records"][0]["source_record_bytes_canonical"]+=1
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_wrong_mapping_count(self):
        self.index["shards"][0]["records"][0]["mapping_nodes"]+=1
        self.index["totals"]["mapping_nodes"]+=1
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_private_source_rights_promotion(self):
        self.index["shards"][0]["source_rights"]="CLEARED_PUBLIC"
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_claimed_native_admission(self):
        self.index["shards"][0]["records"][0]["source_native_object_id_admitted"]=True
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_claimed_mint(self):
        self.index["native_mint"]=True
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_index_promoted_to_body_store(self):
        self.index["full_lossless_reconstruction_without_R0"]=True
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_embedded_message_in_sparse_row(self):
        self.index["shards"][0]["records"][0]["text"]="private message"
        with self.assertRaises(IntakeHold):self.hydrate()
    def test_reject_duplicate_json_keys_in_r1_index(self):
        raw=self.index_bytes()
        encoded=raw.replace(b'"native_mint":false',b'"native_mint":false,"native_mint":false')
        self.assertNotEqual(raw,encoded)
        with self.assertRaises(IntakeHold):
            validate_sparse_index(self.manifest,encoded)
    def test_reject_duplicate_json_keys_in_original_source(self):
        p=self.directory/"conversations-000.json"
        b=p.read_bytes()
        b=b.replace(b'"title":"SYNTHETIC_ONLY"',b'"title":"SYNTHETIC_ONLY","title":"duplicate"',1)
        p.write_bytes(b)
        self.index["shards"][0]["R0_sha256"]=sha(b)
        self.manifest=blob({**json.loads(self.manifest), "export_files":[
            {"path":"conversations-000.json","size_bytes":len(b)},
            {"path":"conversations-001.json","size_bytes":(self.directory/"conversations-001.json").stat().st_size}]})
        self.index["source_manifest_sha256"]=sha(self.manifest)
        self.index["totals"]["bytes"]=sum(x["size_bytes"] for x in json.loads(self.manifest)["export_files"])
        with self.assertRaisesRegex(IntakeHold,"DUPLICATE_JSON_OBJECT_KEY"):
            self.hydrate()
    def test_reject_all_originals_cross_shard_identity_collision(self):
        b=blob([record("one")])
        (self.directory/"conversations-001.json").write_bytes(b)
        self.index["shards"][1]["R0_sha256"]=sha(b)
        self.index["totals"]["bytes"]=len((self.directory/"conversations-000.json").read_bytes())+len(b)
        m=json.loads(self.manifest)
        m["export_files"][1]["size_bytes"]=len(b)
        self.manifest=blob(m)
        self.index["source_manifest_sha256"]=sha(self.manifest)
        with self.assertRaises(IntakeHold):
            verify_all_originals(self.manifest,self.index_bytes(),self.directory)

if __name__=="__main__":unittest.main()
