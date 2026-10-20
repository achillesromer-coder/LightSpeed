"""CGX native intake subset: exact lineage, FileSpace + DataSpace + R0 boundary.

These tests do not enrol a node, perform a network exchange, publish content,
write to a provider or grant canonical approval.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
DESKTOP=ROOT/"desktop/LightSpeed_Runtime"
BENCH=ROOT/"benchmarks/cgx_unispace_geometric_shorthand"
for p in (str(DESKTOP),str(BENCH)):
    if p not in sys.path: sys.path.insert(0,p)

from lightspeed_runtime.cgx_intake_projection import (
    project_intake, project_native_envelope_candidate,
    plan_two_node_exchange, project_public_preview, IntakeError
)
from lightspeed_runtime.source_intake import build_source_envelope
from node_exchange_r0_adapter import candidate, reconstruct

MANIFEST=ROOT/"cgx/review/native_intake_subset_fold_20261020.json"
META={
    "provider":"unit-test-provider",
    "provider_file_id":"f-abc",
    "provider_revision":"r-1",
    "source_name":"evidence.csv",
    "source_ref":"local-test://source-abc",
    "owner_domain":"eco",
    "licence":"NOT_RIGHTS_CLEARED",
    "visibility":"INTERNAL_ONLY"
}

class NativeIntakeSubsetFoldTests(unittest.TestCase):
    def test_exact_three_source_blobs(self):
        manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_pr"],173)
        self.assertEqual(len(manifest["carried_source_files"]),3)
        for x in manifest["carried_source_files"]:
            raw=(ROOT/x["path"]).read_bytes()
            blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
            self.assertEqual(blob,x["git_blob_sha1"],x["path"])

    def test_existing_file_space_source_envelope_and_candidate_preserve_exact_bytes(self):
        data=b"item,unit,value\ncapacity,kg,unknown\n"
        env=build_source_envelope(source_name=META["source_name"],data=data,
                                  source_ref=META["source_ref"],release_class="Internal")
        rec=project_native_envelope_candidate(data,env,META)
        self.assertEqual(rec["identity"]["source_sha256"],hashlib.sha256(data).hexdigest())
        self.assertEqual(rec["identity"]["source_size_bytes"],len(data))
        self.assertEqual(rec["gates"]["canonical_dbr_commit"],"HOLD")
        self.assertFalse(rec["public_publish_authorized"])
        self.assertFalse(rec["canonical_promotion_authorized"])
        self.assertEqual(rec["native_envelope_binding"]["provider_revision_verified"],False)

    def test_two_node_is_plan_even_when_untrusted_client_claims_authenticated(self):
        data=b"tiny-private"
        record=project_intake(data,META)
        desktop={"node_id":"A","root_id":"A-ROOT","device_kind":"desktop_host","authenticated":True}
        phone={"node_id":"B","root_id":"B-ROOT","device_kind":"mobile_touch","authenticated":True}
        packet=plan_two_node_exchange(record,desktop,phone)
        self.assertEqual(packet["state"],"HOLD_AUTHENTICATED_PEER_ADMISSION")
        self.assertFalse(packet["peer_transport_verified"])
        self.assertFalse(packet["authenticated"])
        self.assertFalse(packet["signed"])
        self.assertEqual(packet["transfer_envelope"]["source_sha256"],hashlib.sha256(data).hexdigest())

    def test_exact_r0_reconstruction_does_not_grant_publishing_or_licensing(self):
        data=b"csv,registered?\nno,rights unknown\n"*150
        rec=project_intake(data,META)
        original=rec["identity"]
        native={
            "object_id":"CGX-FIXTURE/INTAKE",
            "native_provider":META["provider"],
            "native_source_ref":META["source_ref"],
            "native_revision":META["provider_revision"],
            "owner_ref":"test-owner",
            "source_sha256":original["source_sha256"]
        }
        bytes_carrier,plan=candidate(data,native=native)
        restored,receipt=reconstruct(bytes_carrier,plan)
        self.assertEqual(restored,data)
        self.assertEqual(receipt["source_sha256"],original["source_sha256"])
        self.assertFalse(receipt["peer_transport_verified"])
        self.assertFalse(receipt["canonical_promotion_authorized"])
        self.assertFalse(plan["public_publish_authorized"])

    def test_private_title_and_source_ref_are_not_projected_public(self):
        rec=project_intake(b"private",META)
        result=project_public_preview(rec,{"title":"INTERNAL-SOURCE-SECRET","summary":"SENSITIVE"})
        self.assertEqual(result["state"],"HOLD_NOT_PUBLIC_SAFE")
        self.assertNotIn("INTERNAL-SOURCE-SECRET",json.dumps(result))
        self.assertNotIn(META["source_ref"],json.dumps(result))

    def test_cannot_make_private_native_source_public_by_relabelling(self):
        data=b"private source"
        env=build_source_envelope(source_name=META["source_name"],data=data,
                                  source_ref=META["source_ref"],release_class="Internal")
        with self.assertRaises(IntakeError):
            project_native_envelope_candidate(data,env,{**META,"visibility":"PUBLIC_SAFE"})

if __name__=="__main__":
    unittest.main()
