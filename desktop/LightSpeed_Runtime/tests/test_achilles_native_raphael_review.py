import unittest
from lightspeed_runtime.achilles.native_raphael_review import source_review,resolve_review

class RaphaelReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.env=source_review();cls.sha=cls.env["sha256"]
    def review(self,**change):
        args={"atlas_id":"CGA-C-001","kernel_id":"T1K-005","search_id":"RGS-000","task_id":"fixture-task",
              "scope_revision":"fixture-acl","max_bytes":65536,"authorise":lambda *a:True}|change
        return resolve_review(self.sha,**args)
    def test_source_counts(self):
        b=self.env["review"]
        self.assertEqual((b["atlas_count"],len(b["kernel_refs"]),len(b["search_refs"])),(411,20,61))
        self.assertTrue(b["local_online_projection_byte_equal"])
        self.assertEqual(b["solver_route_id"],"science.rfs_emff_sweep")
        self.assertFalse(b["execution_authorized"])
    def test_hydration(self):
        r=self.review()["review"]
        self.assertEqual(r["rows"]["atlas"]["ID"],"CGA-C-001")
        self.assertEqual(r["rows"]["kernel"]["kernel_id"],"T1K-005")
        self.assertEqual(r["rows"]["search"]["ID"],"RGS-000")
        self.assertEqual(r["relationship_state"],"CALLER_PROPOSED_NOT_VALIDATED")
        self.assertFalse(r["physical_inference_authorized"])
    def test_permission_and_revocation(self):
        for deny in ("atlas","kernel","search"):
            with self.assertRaises(PermissionError):self.review(authorise=lambda t,k,*a:k!=deny)
        calls=[]
        def revoke(*a):
            calls.append(a);return len(calls)<6
        with self.assertRaises(PermissionError):self.review(authorise=revoke)
    def test_bad_source_and_request(self):
        for changes in ({"kernel_id":"T1K-999"},{"search_id":"RGS-999"},{"max_bytes":1},{"atlas_id":"174"}):
            with self.assertRaises((ValueError,RuntimeError)):self.review(**changes)
        with self.assertRaises(ValueError):resolve_review("0"*64,atlas_id="CGA-C-001",kernel_id="T1K-005",
                search_id="RGS-000",task_id="fixture",scope_revision="r1",max_bytes=65536,authorise=lambda *a:True)
