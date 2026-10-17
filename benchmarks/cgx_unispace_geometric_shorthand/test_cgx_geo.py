import copy
import io
import json
import random
import struct
import unittest
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory
from cgx_geo import (CodecError,HEADER,encode_bytes,decode_bytes,inspect,
                     morton3,unmorton3,lattice,side_for,chunk_map)

class GeometricCarrierTests(unittest.TestCase):
 def test_morton_roundtrip(self):
  for x,y,z in [(0,0,0),(1,2,3),(15,0,2),(65535,65535,65535)]:
   self.assertEqual((x,y,z),unmorton3(morton3(x,y,z)))
 def test_r0_every_payload_size(self):
  r=random.Random(42)
  for n in [0,1,8,160,1024,4100,131072,210008]:
   data=r.randbytes(n)
   for layers in [1,3,15,52,128]:
    blob,stats=encode_bytes(data,layers=layers)
    restored,receipt=decode_bytes(blob)
    self.assertEqual(data,restored)
    self.assertEqual(receipt['status'],'R0_EXACT_BYTE_RECONSTRUCTION')
    self.assertEqual(stats['n_layers'],layers)
 def test_textual_semantics_never_conflated_with_bytes(self):
  data=('"x","y"\n'+'"alpha","beta"\n'*2500).encode()
  blob,stats=encode_bytes(data,layers=15,chunk_size=4096)
  self.assertTrue(stats['zlib_chunks']>0)
  self.assertEqual(decode_bytes(blob)[0],data)
  self.assertFalse(decode_bytes(blob)[1]['semantic_equivalence_verified'])
 def test_binary_high_entropy_has_raw_fallback(self):
  data=random.Random(28).randbytes(90000)
  blob,stats=encode_bytes(data,layers=3)
  self.assertEqual(stats['raw_chunks'],2)
  self.assertEqual(decode_bytes(blob)[0],data)
 def test_zero_byte_source(self):
  blob,_=encode_bytes(b'');doc=inspect(blob)
  self.assertEqual(doc['original_bytes'],0)
  self.assertEqual(doc['chunks'],[])
  self.assertEqual(decode_bytes(blob)[0],b'')
 def test_ref_rehydration_requires_matching_cache(self):
  shared=b'core-language-geometry-'*4000
  edited=shared[:10000]+b'SOME DIFFERENT DATA'+shared[10019:]
  with TemporaryDirectory() as t:
   p=Path(t)/'original.bin';p.write_bytes(shared)
   cache=chunk_map([p],4096)
   self.assertTrue(cache)
   blob,stats=encode_bytes(edited,cache=cache,chunk_size=4096,layers=15)
   self.assertGreater(stats['ref_chunks'],0)
   with self.assertRaisesRegex(CodecError,'NOT_CACHED'):decode_bytes(blob)
   self.assertEqual(decode_bytes(blob,cache=cache)[0],edited)
 def test_corruption_is_rejected(self):
  blob,_=encode_bytes(b'hello world'*10000,layers=15)
  altered=bytearray(blob);altered[-1]^=128
  with self.assertRaises(CodecError):decode_bytes(bytes(altered))
  with self.assertRaises(CodecError):decode_bytes(blob[:10])
  with self.assertRaises(CodecError):decode_bytes(blob+b'junk')
 def test_replay_reorder_and_geometry_tamper(self):
  blob,_=encode_bytes(b'q'*5000,chunk_size=1024,layers=3)
  doc=inspect(blob)
  doc['chunks'][0][0]=999
  doc['geometry_root']=__import__('hashlib').sha256(json.dumps(doc['geometry'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
  man=zlib.compress(json.dumps(doc,sort_keys=True,separators=(',',':')).encode(),9)
  forged=HEADER.pack(b'CGXS',1,len(man))+man+blob[HEADER.size+len(zlib.compress(json.dumps(inspect(blob),sort_keys=True,separators=(',',':')).encode(),9)):]
  with self.assertRaisesRegex(CodecError,'Geometry address'):decode_bytes(forged)
 def test_bounded_decode(self):
  blob,_=encode_bytes(b'A'*9000)
  with self.assertRaisesRegex(CodecError,'capacity'):decode_bytes(blob,max_output=8000)
 def test_security_and_source_ownership(self):
  blob,_=encode_bytes(b'abc')
  doc=inspect(blob)
  self.assertFalse(doc['authority_transfer']);self.assertFalse(doc['signed'])
  self.assertFalse(doc['dbr_promotion']);self.assertEqual(doc['preservation'],'R0_EXACT')
 def test_bad_filename(self):
  with self.assertRaises(CodecError):encode_bytes(b'x',filename='../secret')
  with self.assertRaises(CodecError):encode_bytes(b'x',filename=r'C:\secret')
 def test_selection_penalty_does_not_invent_savings(self):
  data=(b'row,A,B\n'*2000)
  fast,_=encode_bytes(data,chunk_size=4096)
  slow,stats=encode_bytes(data,chunk_size=4096,cpu_byte_penalty=2.)
  self.assertGreater(stats['raw_chunks'],0)
  self.assertEqual(decode_bytes(fast)[0],decode_bytes(slow)[0])

if __name__=='__main__':unittest.main()

class RootDeltaTests(unittest.TestCase):
 def test_one_key_sparse_edit(self):
  from cgx_geo import encode_delta_bytes,decode_delta_bytes
  a=bytearray(b'A'*196608);b=bytearray(a);b[90000]=66
  blob,receipt=encode_delta_bytes(bytes(a),bytes(b),layers=15)
  self.assertEqual(receipt['selection'],'ROOT_REFERENCE_SPARSE_PATCH')
  self.assertLess(len(blob),900)
  self.assertEqual(decode_delta_bytes(blob,bytes(a))[0],bytes(b))
  with self.assertRaisesRegex(CodecError,'NOT_CACHED'):decode_delta_bytes(blob,None)
  with self.assertRaisesRegex(CodecError,'CONTEXT_MISMATCH'):decode_delta_bytes(blob,b'Z'*len(a))
 def test_length_change_falls_back_full(self):
  from cgx_geo import encode_delta_bytes,decode_delta_bytes
  blob,stats=encode_delta_bytes(b'abc'*2000,b'abcd'*2000)
  self.assertIn('FULL_SOURCE_FALLBACK',stats['selection'])
  self.assertEqual(decode_delta_bytes(blob,None)[0],b'abcd'*2000)
 def test_identical_but_cache_is_still_required(self):
  from cgx_geo import encode_delta_bytes,decode_delta_bytes
  old=b'abc'*5000
  blob,stats=encode_delta_bytes(old,old)
  self.assertEqual(stats['patch_runs'],0)
  self.assertEqual(decode_delta_bytes(blob,old)[0],old)
  with self.assertRaisesRegex(CodecError,'NOT_CACHED'):decode_delta_bytes(blob,None)

class ReadLensTests(unittest.TestCase):
 def test_signatures(self):
  from read_lenses import probe
  self.assertEqual(probe(b'%PDF-1.7\n...')['read_mode'],'pdf')
  self.assertEqual(probe(b'\x89PNG\r\n\x1a\n'+bytes(4)+b'IHDR'+struct.pack('>II',1080,720))['metadata']['width'],1080)
  self.assertEqual(probe(b'\x7fELFxxxx')['metadata']['execution_authorised'],False)
  self.assertEqual(probe(b'{"a":2}')['read_mode'],'json')
  self.assertEqual(probe(b'IWAD'+struct.pack('<II',0,12))['read_mode'],'doom-wad')
 def test_no_execution_from_filename_or_zip(self):
  from read_lenses import probe
  self.assertFalse(probe(b'nonbinary text',filename='danger.exe')['application_execution_authorized'])
  import io,zipfile
  buff=io.BytesIO()
  with zipfile.ZipFile(buff,'w') as z:z.writestr('../../escape.sh','rm -rf /')
  x=probe(buff.getvalue(),'test.zip')
  self.assertEqual(x['read_mode'],'zip-container')
  self.assertFalse(x['metadata']['archive_content_extracted'])
  self.assertFalse(x['licence_or_owner_verified'])
