import io
import json
import random
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from cgx_geo import h
from node_exchange_r0_adapter import (
    BridgeError,candidate,reconstruct,native_node_transfer_plan,unzip_one
)

def native(data,revision="fixture-r1"):
    return {"object_id":"CGX-FIXTURE/A","native_provider":"fixture",
        "native_source_ref":"fixture://sourceA","native_revision":revision,
        "owner_ref":"fixture-owner","source_sha256":h(data)}

class R0FileSpaceBridgeTests(unittest.TestCase):
    def test_unverified_provider_claim_never_grants_rights(self):
        data=b"small";meta=native(data);meta["acl_attested"]=True
        packet,plan=candidate(data,native=meta)
        self.assertFalse(plan["acl_attested"])
        self.assertFalse(plan["lease_validated"])
        self.assertFalse(plan["canonical_promotion_authorized"])
        self.assertEqual(reconstruct(packet,plan)[0],data)
    def test_native_revision_required(self):
        data=b"abc";meta=native(data);del meta["native_revision"]
        with self.assertRaisesRegex(BridgeError,"SOURCE_IDENTITY_MISSING"):
            candidate(data,native=meta)
    def test_native_hash_mismatch(self):
        with self.assertRaisesRegex(BridgeError,"SOURCE_READBACK_MISMATCH"):
            candidate(b"changed",native=native(b"old"))
    def test_cold_zip_wins_for_structured_text(self):
        data=(b"table,id=123,kind=map\n"*8000)
        packet,plan=candidate(data,native=native(data))
        self.assertEqual(plan["mode"],"zip-deflate")
        self.assertEqual(reconstruct(packet,plan)[0],data)
    def test_cold_raw_wins_for_high_entropy(self):
        data=random.Random(777).randbytes(65536)
        packet,plan=candidate(data,native=native(data))
        self.assertEqual(plan["mode"],"raw")
        self.assertEqual(reconstruct(packet,plan)[0],data)
    def test_warm_identical_zero_data_requires_prior(self):
        data=b"shared-static-content"*1000
        packet,plan=candidate(data,native=native(data),baseline=data,receiver_claimed_root=h(data))
        self.assertEqual(plan["mode"],"no-change");self.assertEqual(packet,b"")
        with self.assertRaisesRegex(BridgeError,"NOT_CACHED"):reconstruct(packet,plan)
        self.assertEqual(reconstruct(packet,plan,prior=data)[0],data)
    def test_warm_one_byte_root_patch_less_than_zip(self):
        data=random.Random(52).randbytes(100000)
        updated=bytearray(data);updated[53000]^=1;updated=bytes(updated)
        packet,plan=candidate(updated,native=native(updated),baseline=data,receiver_claimed_root=h(data))
        self.assertEqual(plan["mode"],"cgxs-root-delta")
        self.assertLess(len(packet),850)
        self.assertEqual(reconstruct(packet,plan,prior=data)[0],updated)
        with self.assertRaisesRegex(BridgeError,"NOT_CACHED"):reconstruct(packet,plan)
        with self.assertRaisesRegex(BridgeError,"CONTEXT_MISMATCH"):
            reconstruct(packet,plan,prior=b"?"*len(data))
    def test_wrong_cached_claim_rejected(self):
        data=b"x"
        with self.assertRaisesRegex(BridgeError,"CONTEXT_MISMATCH"):
            candidate(data,native=native(data),baseline=b"y",receiver_claimed_root="a"*64)
    def test_payload_corruption_fails(self):
        data=b"rows\n"*800
        packet,plan=candidate(data,native=native(data))
        changed=bytearray(packet);changed[-1]^=1
        with self.assertRaisesRegex(BridgeError,"CARRIER_HASH_MISMATCH"):
            reconstruct(bytes(changed),plan)
    def test_decode_output_bound(self):
        data=b"many"*2000
        packet,plan=candidate(data,native=native(data))
        with self.assertRaisesRegex(BridgeError,"OUTPUT_BOUND"):
            reconstruct(packet,plan,max_output=600)
    def test_zip_slip_unsafe_archive_rejected_before_extraction(self):
        b=io.BytesIO()
        with zipfile.ZipFile(b,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("payload.bin",b"test")
            z.writestr("../evil.dat",b"data")
        with self.assertRaisesRegex(BridgeError,"ZIP_LAYOUT_UNSUPPORTED"):
            unzip_one(b.getvalue(),10000)
    def test_real_existing_native_node_exchange_envelope_is_plan_only(self):
        data=b"bound-r0-byte-source"*1200
        packet,plan=candidate(data,native=native(data))
        with tempfile.TemporaryDirectory() as root:
            carrier=Path(root)/"carrier.dat";carrier.write_bytes(packet)
            result=native_node_transfer_plan(staged_carrier=carrier,plan=plan,
                 source_node_id="SOURCE-FIXTURE",target_node_id="RECEIVER-FIXTURE",
                 source_root_id="SOURCE-ROOT",target_root_id="RECEIVER-ROOT")
            self.assertEqual(result["status"],"NATIVE_NODE_EXCHANGE_ENVELOPE_PLANNED")
            env=result["envelope"]
            self.assertEqual(env["schema_version"],"cgx-node-transfer-envelope-v1")
            self.assertEqual(env["source_sha256"],h(packet))
            self.assertEqual(result["original_source_sha256"],h(data))
            self.assertFalse(result["lease_validated"])
            self.assertFalse(result["peer_transport_verified"])
            self.assertFalse(env["canonical_promotion_authorized"])
    def test_no_change_native_plan_never_queues_empty_transfer(self):
        data=b"unchanged"
        packet,plan=candidate(data,native=native(data),baseline=data,receiver_claimed_root=h(data))
        with tempfile.TemporaryDirectory() as root:
            carrier=Path(root)/"no-op.dat";carrier.write_bytes(packet)
            result=native_node_transfer_plan(staged_carrier=carrier,plan=plan,
                 source_node_id="A",target_node_id="B",
                 source_root_id="A-ROOT",target_root_id="B-ROOT")
            self.assertEqual(result["status"],"NO_PAYLOAD_PLAN")
            self.assertIsNone(result["envelope"])
            self.assertEqual(result["requires_receiver_prior"],h(data))
if __name__=="__main__":
    unittest.main()
