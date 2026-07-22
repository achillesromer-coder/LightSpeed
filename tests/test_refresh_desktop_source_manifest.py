from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "refresh_desktop_source_manifest.py"
SPEC = importlib.util.spec_from_file_location("refresh_desktop_source_manifest", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_sha256_is_portable_across_windows_and_posix_newlines(tmp_path):
    windows_file = tmp_path / "windows.txt"
    posix_file = tmp_path / "posix.txt"
    windows_file.write_bytes(b"alpha\r\nbeta\r\n")
    posix_file.write_bytes(b"alpha\nbeta\n")

    expected = hashlib.sha256(b"alpha\nbeta\n").hexdigest()
    assert MODULE.sha256(windows_file) == expected
    assert MODULE.sha256(posix_file) == expected
    assert MODULE.portable_content(windows_file) == MODULE.portable_content(posix_file)
