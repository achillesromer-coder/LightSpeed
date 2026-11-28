"""PrintSpace private RC packaging regression; all rights/native/device gates remain denied."""
from __future__ import annotations

import io
import json
import shutil
import zipfile
from pathlib import Path

import pytest

from scripts.package_printspace_software import (
    ASSETS, MANIFEST, ROOT, SCHEMA, VERSION, ZIP_NAME,
    ReleaseHold, build, verify, write_release,
)


def archive_members(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {n: z.read(n) for n in z.namelist()}


def rewrite(data: bytes, mutate) -> bytes:
    members = archive_members(data)
    mutate(members)
    from scripts.package_printspace_software import _zip
    return _zip(members)


def private_copy(tmp_path: Path) -> Path:
    root = tmp_path / "mock-git-root"
    for source in ASSETS:
        src = ROOT / source
        dst = root / source
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return root


def test_two_deterministic_rebuilds_are_identical_even_across_source_roots(tmp_path):
    a = build(ROOT)
    b = build(private_copy(tmp_path))
    assert a == b
    proof = verify(a)
    assert proof["state"] == "PASS_PRIVATE_RC_INTEGRITY_ONLY"
    assert proof["file_count"] == len(ASSETS) + 3
    assert proof["public_distribution_approved"] is False
    assert proof["physical_machine_authorised"] is False
    assert proof["native_admitted"] is False


def test_rebuild_disk_readback_and_sidecar(tmp_path):
    a = write_release(ROOT, tmp_path)
    b = write_release(ROOT, tmp_path, check=True)
    assert a == b
    archive = tmp_path / ZIP_NAME
    assert archive.is_file()
    assert verify(archive.read_bytes(), sidecar=(tmp_path / (ZIP_NAME + ".sha256")).read_text(), filename=ZIP_NAME)["state"] == "PASS_PRIVATE_RC_INTEGRITY_ONLY"
    (tmp_path / (ZIP_NAME + ".sha256")).write_text("0" * 64 + "  " + ZIP_NAME + "\n")
    with pytest.raises(ReleaseHold, match="REPRODUCIBLE_RELEASE_RC_DRIFT"):
        write_release(ROOT, tmp_path, check=True)


def test_all_release_members_explicit_no_private_keys_or_binaries():
    members = archive_members(build(ROOT))
    assert set(members) == set(ASSETS.values()) | {MANIFEST, "README-START-HERE.md", "RELEASE-GATES.md"}
    assert all(not name.endswith((".py", ".mjs", ".exe", ".wasm", ".so", ".dll", ".pem")) for name in members)
    assert members["PrintSpace.Studio.offline.html"].startswith(b"<!doctype html>")
    doc = json.loads(members[MANIFEST])
    assert doc["schema"] == SCHEMA and doc["version"] == VERSION
    assert doc["distribution_scope"] == "OWNER_PRIVATE_EVALUATION_ONLY"
    assert doc["independent_signing_attestation"] is False
    assert all(v is False for v in doc["safety_flags"].values())
    assert "native" in members["RELEASE-GATES.md"].decode().lower()


def test_archive_content_change_is_rejected_even_when_zip_crc_rewritten():
    modified = rewrite(build(ROOT), lambda m: m.__setitem__("data/cgx-80-facet-bundle.json", m["data/cgx-80-facet-bundle.json"] + b" "))
    with pytest.raises(ReleaseHold, match="SOURCE_ASSET_INTEGRITY"):
        verify(modified)


def test_public_release_authority_forgery_rejected():
    def alter(m):
        doc = json.loads(m[MANIFEST])
        doc["software_release_ready_for_public"] = True
        m[MANIFEST] = (json.dumps(doc, sort_keys=True, indent=2) + "\n").encode()
    with pytest.raises(ReleaseHold, match="MANIFEST_AUTHORITY_ESCALATION"):
        verify(rewrite(build(ROOT), alter))


def test_false_native_db_receipt_in_source_h0_rejected(tmp_path):
    root = private_copy(tmp_path)
    path = root / "cgx/manufacturing/printspace_cgx_h0_v0_1.json"
    doc = json.loads(path.read_text())
    doc["native_admitted"] = True
    path.write_text(json.dumps(doc))
    with pytest.raises(ReleaseHold, match="LOAD_H0_SOURCE_REPLAY"):
        build(root)


def test_privileged_catalogue_change_denied_before_packaging(tmp_path):
    root = private_copy(tmp_path)
    path = root / "cgx/manufacturing/printspace_virtual_factory_catalog_v0_1.json"
    doc = json.loads(path.read_text())
    doc["attestations"]["software_release_approved"] = True
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="AUTHORITY_ESCALATION"):
        build(root)


def test_mutated_source_catalogue_not_masked_by_manifest(tmp_path):
    root = private_copy(tmp_path)
    path = root / "cgx/manufacturing/printspace_virtual_factory_catalog_v0_1.json"
    doc = json.loads(path.read_text())
    doc["catalogue_id"] += "-ALTERED"
    path.write_text(json.dumps(doc))
    with pytest.raises(ReleaseHold, match="CGX_SOURCE_REPLAY_OR_CATALOGUE_HASH_MISMATCH"):
        build(root)


def test_static_html_remote_dependency_denied(tmp_path):
    root = private_copy(tmp_path)
    path = root / "cgx/manufacturing/printspace_studio_v0_1.html"
    path.write_text(path.read_text() + "<script src='https://example.org/inject.js'></script>")
    with pytest.raises(ReleaseHold, match="REMOTE_DEPENDENCY_IN_OFFLINE_STUDIO"):
        build(root)


def test_missing_source_denied(tmp_path):
    root = private_copy(tmp_path)
    (root / "cgx/manufacturing/printspace_cgx_bundle_v0_1.json").unlink()
    with pytest.raises(ReleaseHold, match="MISSING_OR_UNSAFE_SOURCE"):
        build(root)


def test_release_zip_traversal_and_duplicate_member_denied():
    payload = build(ROOT)
    evil = rewrite(payload, lambda m: m.__setitem__("../../payload.txt", b"unsafe"))
    with pytest.raises(ReleaseHold, match="UNSAFE_ARCHIVE_MEMBER_PATH"):
        verify(evil)
    with zipfile.ZipFile(io.BytesIO(payload)) as original:
        zbytes = io.BytesIO()
        with zipfile.ZipFile(zbytes, "w") as w:
            for name in original.namelist():
                w.writestr(name, original.read(name))
            w.writestr("README-START-HERE.md", b"duplicate")
        with pytest.raises(ReleaseHold, match="DUPLICATE_OR_MISSING_ARCHIVE_MEMBERS"):
            verify(zbytes.getvalue())


def test_wrong_external_sha256_sidecar_denied():
    with pytest.raises(ReleaseHold, match="UNMATCHED_ARCHIVE_SHA256_SIDECAR"):
        verify(build(ROOT), sidecar="0" * 64 + "  " + ZIP_NAME + "\n", filename=ZIP_NAME)


def test_non_archive_input_denied():
    with pytest.raises(ReleaseHold, match="CORRUPT_OR_INVALID_RELEASE_ARCHIVE"):
        verify(b"not a zip")


def test_no_release_time_or_owner_credential_depends_on_execution_date():
    a, b = archive_members(build(ROOT)), archive_members(build(ROOT))
    assert a[MANIFEST] == b[MANIFEST]
    manifest = json.loads(a[MANIFEST]);assert "built_at" not in manifest
    assert manifest["source_reference"]["symbolic_facets"] == 80
    assert manifest["source_reference"]["sample_products"] == 3


def test_rc2_reuses_one_offline_studio_with_five_view_contexts():
    assert VERSION == '0.1.0-rc.2'
    members=archive_members(build(ROOT))
    html=members['PrintSpace.Studio.offline.html'].decode('utf-8')
    assert html.count('id="space"') == 1
    for facet in ('file_space','data_space','print_space',
                  'intelligence_space','social_space'):
        assert f'value="{facet}"' in html
    assert 'Cognigrex.cgx' in html and 'Romer.cgx' in html
    assert 'native_ternary_encoded:false' in html
    assert 't173_mesh_admitted:false' in html
    doc=json.loads(members['data/load-lite-h0.json'])
    assert doc['root_namespace']=='cgx://romer.industries/romer/printspace/'
    assert doc['native_admitted'] is False and doc['source_bytes_hydrated'] == 0
    assert all(v is False for v in json.loads(members[MANIFEST])['safety_flags'].values())
