"""Pure source-only candidate fixture; no owner source, network, GPU or CGX writes."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess

MODULE = Path(__file__).resolve().parents[1] / "cgx" / "review" / "video_r0_intake_candidate.py"
spec = importlib.util.spec_from_file_location("video_r0", MODULE)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class MediaR0Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.video = self.root / "synthetic.mkv"
        self.payload = b"synthetic-no-real-footage" * 101
        self.video.write_bytes(self.payload)
        self.digest = hashlib.sha256(self.payload).hexdigest()
        self.r0 = v.verify_owner_local_source(self.video, self.root, self.digest, len(self.payload))
        self.probe = {"streams": [{"index": 0, "codec_type":"video", "codec_name":"rawvideo", "width": 320,"height":180,"pix_fmt":"yuv420p", "avg_frame_rate":"30/1", "nb_frames":"48"}]}

    def test_stream_hash_exact(self): self.assertEqual(self.r0['sha256'], self.digest)
    def test_reject_corrupt_hash(self):
        with self.assertRaises(v.SourceHeld): v.verify_owner_local_source(self.video, self.root, 'a'*64, len(self.payload))
    def test_reject_size_mismatch(self):
        with self.assertRaises(v.SourceHeld): v.verify_owner_local_source(self.video, self.root, self.digest, 42)
    def test_reject_unapproved_root(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(v.SourceHeld): v.verify_owner_local_source(self.video, d, self.digest, len(self.payload))
    def test_reject_symlink(self):
        link = self.root / 'alias.mkv'
        try: link.symlink_to(self.video)
        except (OSError, NotImplementedError): self.skipTest('symlink unavailable')
        with self.assertRaises(v.SourceHeld): v.verify_owner_local_source(link, self.root, self.digest, len(self.payload))
    def test_reject_unsupported_suffix(self):
        bad=self.root/'x.txt'; bad.write_bytes(self.payload)
        with self.assertRaises(v.SourceHeld): v.verify_owner_local_source(bad,self.root,self.digest,len(self.payload))
    def test_metadata_no_promotion(self):
        out=v.prepare_video_candidate(self.r0,self.probe,claimed_layout="SIDE_BY_SIDE")
        for field in ['native_r1_admitted','compression_ratio_measured','canonical_promotion_authorized','public_publish_authorized','pixel_exact_reconstruction_verified']:
            self.assertFalse(out[field])
        self.assertEqual(out['tracks'][0]['width'],320)
    def test_declared_layout_not_evidence(self):
        self.assertEqual(v.prepare_video_candidate(self.r0,self.probe,claimed_layout="SIDE_BY_SIDE")['layout_state'], 'UNVERIFIED_OWNER_DECLARATION')
    def test_unknown_layout_stays_unknown(self):
        self.assertEqual(v.prepare_video_candidate(self.r0,self.probe)['layout_state'],'UNKNOWN')
    def test_multi_video_flags(self):
        self.probe['streams'].append({**self.probe['streams'][0],"index":1})
        self.assertIn('MULTI_TRACK_REQUIRES_PER_TRACK_PROCESSING',v.prepare_video_candidate(self.r0,self.probe)['holds'])
    def test_ffprobe_source_gate(self):
        with self.assertRaises(v.SourceHeld):
            v.bounded_ffprobe(self.video,approved_root=self.root,
                              expected_sha256='0'*64,expected_size=len(self.payload))
    def test_ffprobe_mock_success(self):
        payload=b'{"streams":[{"codec_type":"video","width":1,"height":1}]}'
        with patch.object(v.subprocess,'run',return_value=subprocess.CompletedProcess([],0,payload,b'')) as run:
            out=v.bounded_ffprobe(self.video,approved_root=self.root,
                     expected_sha256=self.digest,expected_size=len(self.payload))
        self.assertEqual(out['streams'][0]['width'],1)
        self.assertNotIn('shell',run.call_args.kwargs)
    def test_ffprobe_rejects_bogus_json(self):
        with patch.object(v.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'{',b'')):
            with self.assertRaises(v.SourceHeld):
                v.bounded_ffprobe(self.video,approved_root=self.root,
                        expected_sha256=self.digest,expected_size=len(self.payload))
    def test_10bit_flags(self):
        self.probe['streams'][0]['pix_fmt']='yuv420p10le'
        self.assertIn('HIGH_BIT_DEPTH_REQUIRES_QUALIFIED_PROFILE',v.prepare_video_candidate(self.r0,self.probe)['holds'])
    def test_zero_geometry_rejected(self):
        self.probe['streams'][0]['width']=0
        with self.assertRaises(v.SourceHeld):v.prepare_video_candidate(self.r0,self.probe)
    def test_unverified_r0_rejected(self):
        self.r0['state']='SUPPOSED'
        with self.assertRaises(v.SourceHeld):v.prepare_video_candidate(self.r0,self.probe)
    def test_malformed_digest_rejected(self):
        self.r0['sha256']='?'*64
        with self.assertRaises(v.SourceHeld):v.prepare_video_candidate(self.r0,self.probe)
    def test_compression_measurement_not_assumed_lossless(self):
        rec=v.measured_ratio(1000,100)
        self.assertEqual(rec['ratio'],10)
        self.assertFalse(rec['exact_original_byte_reconstruction_verified'])
    def test_exact_byte_hash_requires_both(self):
        rec=v.measured_ratio(1000,500,original_sha256=self.digest,reconstructed_sha256=self.digest)
        self.assertTrue(rec['reported_source_and_reconstruction_hashes_match'])
        self.assertFalse(rec['exact_original_byte_reconstruction_verified'])
        self.assertFalse(rec['pixel_exact_reconstruction_verified'])
    def test_reject_zero_compression_sizes(self):
        with self.assertRaises(v.SourceHeld):v.measured_ratio(1000,0)
    def test_unmeasured_132gb_not_present(self):
        self.assertNotIn('132',str(v.prepare_video_candidate(self.r0,self.probe)))

if __name__=='__main__': unittest.main()