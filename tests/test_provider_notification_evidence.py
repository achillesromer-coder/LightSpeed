from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("provider_classifier", ROOT/"scripts"/"classify_provider_notification.py")
mod=importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)

class ProviderNotificationEvidenceTests(unittest.TestCase):
    def test_stale_failure_is_superseded_by_later_pass(self):
        r=mod.classify({
            "provider":"github","event_type":"WORKFLOW_FAILURE","provider_event_id_or_run_id":1,
            "head_or_revision":"abc","provider_readback":{"later_success":True,"verified":True},
            "mail_message_id":"private"
        })
        self.assertEqual(r["disposition"],"SUPERSEDED_BY_NEWER_PASS")
        self.assertFalse(r["private_fields_emitted_publicly"])
        self.assertNotIn("mail_message_id",r["public_projection"])

    def test_live_failure_stays_active(self):
        r=mod.classify({
            "provider":"github","event_type":"WORKFLOW_FAILURE",
            "provider_readback":{"current_failed":True,"verified":True}
        })
        self.assertEqual(r["disposition"],"PROVIDER_CONFIRMED_ACTIVE")

    def test_merge_requires_readback(self):
        r=mod.classify({"provider":"github","event_type":"MERGE_OR_CLOSE"})
        self.assertEqual(r["disposition"],"OBSERVED_UNVERIFIED")
        r=mod.classify({
            "provider":"github","event_type":"MERGE_OR_CLOSE",
            "provider_readback":{"verified":True,"state":"merged"}
        })
        self.assertEqual(r["disposition"],"PROVIDER_CONFIRMED_RESOLVED")

    def test_security_event_requires_human_authorization(self):
        r=mod.classify({"provider":"google","event_type":"CONNECTOR_SECURITY","human_authorized":False})
        self.assertEqual(r["disposition"],"SECURITY_REVIEW_REQUIRED")
        r=mod.classify({"provider":"google","event_type":"CONNECTOR_SECURITY","human_authorized":True})
        self.assertEqual(r["disposition"],"AUTHORIZED_SECURITY_EVENT")

    def test_permission_or_quota_uses_live_service_state(self):
        r=mod.classify({"provider":"drive","event_type":"PERMISSION_OR_QUOTA","provider_readback":{"healthy":True}})
        self.assertEqual(r["disposition"],"PROVIDER_CONFIRMED_RESOLVED")

if __name__=="__main__":
    unittest.main()
