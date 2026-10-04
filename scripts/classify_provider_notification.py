#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "cgx" / "domain_templates" / "provider_notification_evidence_contract.json"

PRIVATE_KEYS = {"account_email","mail_message_id","mail_thread_id","display_url","security_link","full_email_body"}

def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

def classify(event: dict[str, Any]) -> dict[str, Any]:
    event_type=str(event.get("event_type") or "").upper()
    readback=event.get("provider_readback") or {}
    disposition="OBSERVED_UNVERIFIED"
    reasons=[]

    if event_type=="WORKFLOW_FAILURE":
        if readback.get("later_success") is True or readback.get("same_head_success") is True:
            disposition="SUPERSEDED_BY_NEWER_PASS"
            reasons.append("later-provider-success")
        elif readback.get("current_failed") is True:
            disposition="PROVIDER_CONFIRMED_ACTIVE"
            reasons.append("live-provider-still-failed")
        else:
            reasons.append("failure-notification-awaiting-provider-readback")
    elif event_type=="WORKFLOW_SUCCESS":
        if readback.get("verified") is True:
            disposition="PROVIDER_CONFIRMED_RESOLVED"
            reasons.append("provider-success-readback")
        else:
            reasons.append("success-notification-awaiting-provider-readback")
    elif event_type=="MERGE_OR_CLOSE":
        if readback.get("verified") is True and readback.get("state") in {"merged","closed","success"}:
            disposition="PROVIDER_CONFIRMED_RESOLVED"
            reasons.append("provider-state-confirmed")
        else:
            reasons.append("merge-close-notification-awaiting-provider-readback")
    elif event_type=="PERMISSION_OR_QUOTA":
        if readback.get("healthy") is True:
            disposition="PROVIDER_CONFIRMED_RESOLVED"
            reasons.append("service-healthy")
        elif readback.get("blocked") is True:
            disposition="PROVIDER_CONFIRMED_ACTIVE"
            reasons.append("service-still-blocked")
        else:
            reasons.append("permission-quota-awaiting-live-check")
    elif event_type=="CONNECTOR_SECURITY":
        if event.get("human_authorized") is True:
            disposition="AUTHORIZED_SECURITY_EVENT"
            reasons.append("user-authorized")
        else:
            disposition="SECURITY_REVIEW_REQUIRED"
            reasons.append("authorization-not-confirmed")
    elif event_type=="INFORMATIONAL":
        disposition="INFORMATIONAL"
        reasons.append("informational")
    else:
        reasons.append("unknown-event-type")

    public_projection={}
    for key in ("provider","resource_class","event_type","provider_event_id_or_run_id","head_or_revision","observed_at"):
        if key in event:
            public_projection[key]=event[key]
    public_projection["disposition"]=disposition
    if readback:
        public_projection["provider_readback_state"]={
            k:v for k,v in readback.items()
            if k in {"verified","state","status","conclusion","head_or_revision","later_success","same_head_success","current_failed","healthy","blocked"}
        }

    restricted_present=sorted(k for k in PRIVATE_KEYS if k in event and event.get(k) not in (None,""))
    return {
        "schema":"CGX-PROVIDER-NOTIFICATION-RECEIPT/0.1",
        "disposition":disposition,
        "reasons":reasons,
        "evidence_ceiling":"LIVE_PROVIDER_READBACK" if readback else "SECONDARY_NOTIFICATION",
        "canonical_effect":load_contract()["cgx_effect"].get(disposition),
        "public_projection":public_projection,
        "restricted_fields_present":restricted_present,
        "private_fields_emitted_publicly":False
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("event_json",type=Path)
    args=ap.parse_args()
    event=json.loads(args.event_json.read_text(encoding="utf-8"))
    print(json.dumps(classify(event),indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
