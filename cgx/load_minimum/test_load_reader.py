#!/usr/bin/env python3
"""Synthetic negative tests only: no original carrier bytes, host or DBR access."""
import io
import json
import unittest
import warnings
import zipfile
from unittest.mock import patch

from load_reader import ENTRY, read_library, resolve


def fixture(entries, duplicate_member=False):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        payload=json.dumps({'entries':entries}).encode('utf-8')
        z.writestr(ENTRY, payload)
        if duplicate_member:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                z.writestr(ENTRY, payload)
    buf.seek(0)
    return buf


class LoadReaderSourceSafety(unittest.TestCase):
    def test_bounded_valid_reference_remains_noncanonical(self):
        source=fixture([{'ref_id':'fixture:1','name':'Synthetic reference',
                         'sources':['fixture:source']}])
        library=read_library(source)
        self.assertEqual(library['entries'][0]['sources'], ['fixture:source'])
        result=resolve(library,'fixture:1')
        self.assertEqual(result['state'],'REFERENCE_ONLY')
        self.assertIs(result['native_admission'],False)

    def test_duplicate_zip_entry_denied_before_ambiguous_selection(self):
        with self.assertRaisesRegex(ValueError,'duplicate LOAD library entry'):
            read_library(fixture([{'ref_id':'fixture:1'}],duplicate_member=True))

    def test_oversized_uncompressed_library_denied_without_large_fixture(self):
        with patch('load_reader.MAX_LIBRARY_BYTES',64):
            with self.assertRaisesRegex(ValueError,'exceeds bounded read'):
                read_library(fixture([{'ref_id':'fixture:1','name':'X'*200}]))

    def test_invalid_structure_denied(self):
        with self.assertRaisesRegex(ValueError,'invalid LOAD reference id'):
            read_library(fixture([{'name':'missing-id'}]))

    def test_duplicate_reference_id_denied(self):
        with self.assertRaisesRegex(ValueError,'ambiguous duplicate load-reference-id'):
            read_library(fixture([{'ref_id':'fixture:1'},{'ref_id':'fixture:1'}]))


if __name__=='__main__':
    unittest.main()
