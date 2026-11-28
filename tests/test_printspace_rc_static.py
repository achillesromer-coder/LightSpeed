"""Static PrintSpace private RC2 security/accessibility audit, never an owner sign-off."""
from __future__ import annotations
import hashlib
from pathlib import Path
import pytest
from scripts.package_printspace_software import build, ROOT
from scripts.audit_printspace_rc_static import audit_bytes, AuditHold, RC2_SHA256


def test_rc2_source_rebuild_matches_immutable_review_hash():
    data = build(ROOT)
    assert hashlib.sha256(data).hexdigest() == RC2_SHA256
    receipt = audit_bytes(data)
    assert receipt['state'] == 'PASS_STATIC_PRELIMINARY_REVIEW_ONLY'
    assert receipt['rc_zip_sha256'] == RC2_SHA256
    assert receipt['control_count'] == 10
    assert receipt['button_count'] == 9
    assert receipt['hard_hold_codes'] == []
    assert len(receipt['independent_review_findings']) >= 4
    assert 'DYNAMIC_STAGE_STATUS_ANNOUNCEMENT' in receipt['independent_review_findings']
    assert 'CUSTOM_PART_TREE_SPACE_KEY_ACTIVATION' in receipt['independent_review_findings']


def test_preflight_never_grants_public_native_physical_or_owner_approval():
    receipt = audit_bytes(build(ROOT))
    for flag in ('static_security_review_complete','wcag_conformance_verified',
                 'interactive_browser_uat_verified','owner_accepted',
                 'public_distribution_authorised','native_admitted','machine_authorised'):
        assert receipt[flag] is False, flag
    assert receipt['next_owner_gates'] == ['SW-03','SW-04']


@pytest.mark.parametrize('payload', [b'', b'not zip', b'PK\x03\x04'])
def test_nonrelease_bytes_hold(payload):
    with pytest.raises(AuditHold, match='IMMUTABLE_RC2_SHA256_MISMATCH'):
        audit_bytes(payload)


def test_manifest_tampering_cannot_self_attest_release():
    data = bytearray(build(ROOT))
    data[-1] ^= 0x01
    with pytest.raises(AuditHold, match='IMMUTABLE_RC2_SHA256_MISMATCH'):
        audit_bytes(bytes(data))


def test_oversized_data_holds_before_parsing():
    with pytest.raises(AuditHold, match='ARCHIVE_SIZE_OR_FORMAT'):
        audit_bytes(b'0' * (8 * 1024 * 1024 + 1))


def test_static_audit_is_reproducible_and_never_claims_w_c_a_g():
    first = audit_bytes(build(ROOT))
    second = audit_bytes(build(ROOT))
    assert first == second
    assert first['wcag_conformance_verified'] is False
    assert first['static_security_review_complete'] is False
