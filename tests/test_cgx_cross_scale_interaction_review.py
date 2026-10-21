"""Alexandria cross-scale ontology: fail-closed source, conservation and authority checks."""
from __future__ import annotations
import copy
from decimal import Decimal
import json
from pathlib import Path
import unittest

from cgx.review.cross_scale_interaction_review import (
    review_cross_scale, screen_flux_ledger, screen_passive_power, load_and_review,
)

BASE = Path(__file__).resolve().parents[1]
MODEL = BASE/"cgx"/"review"/"alexandria_cross_scale_interaction_review_20261021.json"
EXISTING = BASE/"cgx"/"domain_templates"/"cross_domain_bridge_registry.json"


def source():
    return json.loads(MODEL.read_text(encoding="utf-8")), json.loads(EXISTING.read_text(encoding="utf-8"))


class CrossScaleReviewTests(unittest.TestCase):
    def test_admits_only_source_limited_overlay_to_existing_bridge(self):
        r=load_and_review()
        self.assertEqual(r["profile_count"],12)
        self.assertEqual(r["operator_count"],5)
        self.assertEqual(r["bridge_count"],8)
        self.assertEqual(r["issues_held"],[158,161])
        for x in ("native_dbr_verified","sai_authority_granted",
                  "natural_network_verified","public_release_authorized",
                  "physical_authority_granted"):
            self.assertFalse(r[x])
        self.assertEqual(r["canonical_mutations"],0)
        self.assertEqual(r["functional_simulations"],0)

    def test_mass_and_energy_ledgers_conserve_only_declared_boundary_flows(self):
        self.assertEqual(screen_flux_ledger(incoming=12,outgoing=5,stored_delta=7,unit="kg")["status"],
                         "ACCOUNTING_IDENTITY_PASSED_SYNTHETIC_ONLY")
        self.assertEqual(screen_flux_ledger(incoming=100,outgoing=72,stored_delta=28,unit="J")["status"],
                         "ACCOUNTING_IDENTITY_PASSED_SYNTHETIC_ONLY")
        self.assertEqual(screen_flux_ledger(incoming=20,outgoing=2,stored_delta=19,unit="kg")["status"],
                         "HOLD_UNBALANCED_FLUX")

    def test_tiny_relative_rounding_can_be_explicitly_scoped_not_fabricated(self):
        r=screen_flux_ledger(incoming="1.00000000001",outgoing="0.4",stored_delta="0.6",
                             tolerance="0.000000001",unit="C")
        self.assertEqual(r["status"],"ACCOUNTING_IDENTITY_PASSED_SYNTHETIC_ONLY")
        self.assertFalse(r["empirical_validation"])

    def test_ambient_flux_never_yields_free_extra_power(self):
        good=screen_passive_power(incident_w_m2=5,area_m2=2,efficiency="0.3",claimed_harvest_w=3)
        self.assertEqual(good["available_upper_bound_w"],"3.0")
        self.assertEqual(good["status"],"BOUND_COMPATIBLE_SYNTHETIC_ONLY")
        self.assertFalse(good["usable_energy_verified"])
        bad=screen_passive_power(incident_w_m2=5,area_m2=2,efficiency="0.3",claimed_harvest_w=3.1)
        self.assertEqual(bad["status"],"HOLD_PASSIVE_ENERGY_VIOLATION")
        with self.assertRaises(ValueError):
            screen_passive_power(incident_w_m2=2,area_m2=1,efficiency=1.01,claimed_harvest_w=2)

    def test_boundary_quantities_refuse_wrong_or_unbounded_units(self):
        for v in (float("nan"),float("inf"),-1,True,None,"NaN"):
            with self.subTest(v=v),self.assertRaises(ValueError):
                screen_flux_ledger(incoming=v,outgoing=0,stored_delta=0,unit="J")
        with self.assertRaises(ValueError):
            screen_flux_ledger(incoming=3,outgoing=1,stored_delta=2,unit="W")
        with self.assertRaises(ValueError):
            screen_flux_ledger(incoming=3,outgoing=1,stored_delta=2,unit="kg",tolerance=1)

    def test_cross_scale_analogies_never_silently_merge_source_owners(self):
        obj, registry=source()
        self.assertEqual(review_cross_scale(obj,registry)["profile_count"],12)
        for edge in obj["analogies"]:
            self.assertNotEqual(edge["a"],edge["b"])
            self.assertTrue(edge["distinct"])
        bad=copy.deepcopy(obj)
        bad["cross_scale_records"][0]["object_id"]="invented:canonical"
        with self.assertRaisesRegex(ValueError,"Object_ID"):
            review_cross_scale(bad,registry)
        bad=copy.deepcopy(obj)
        bad["cross_scale_records"][0]["canonical"]=True
        with self.assertRaisesRegex(ValueError,"promoted"):
            review_cross_scale(bad,registry)

    def test_no_sai_or_natural_network_authority_from_geography_or_em_analogy(self):
        obj,registry=source()
        bad=copy.deepcopy(obj)
        bad["authority_flags"]["SAI_enabled"]=True
        with self.assertRaisesRegex(ValueError,"silently promoted"):
            review_cross_scale(bad,registry)
        bad=copy.deepcopy(obj)
        bad["authority_flags"]["verified_elf_broadband_network"]=True
        with self.assertRaisesRegex(ValueError,"silently promoted"):
            review_cross_scale(bad,registry)
        bad=copy.deepcopy(obj)
        bad["analogies"][5]["distinct"]=""
        with self.assertRaisesRegex(ValueError,"falsely equivalent"):
            review_cross_scale(bad,registry)

    def test_missing_operator_or_wrong_graph_root_not_accepted(self):
        obj,registry=source()
        bad=copy.deepcopy(obj)
        bad["operators"].pop()
        with self.assertRaisesRegex(ValueError,"operator family"):
            review_cross_scale(bad,registry)
        bad=copy.deepcopy(obj)
        bad["bridge_location"]="Cognigrex.cgx:/another-graph"
        with self.assertRaisesRegex(ValueError,"graph root"):
            review_cross_scale(bad,registry)
        wrong=copy.deepcopy(registry)
        wrong["schema"]="NEW-MASTER"
        with self.assertRaisesRegex(ValueError,"Existing"):
            review_cross_scale(obj,wrong)

    def test_physical_claims_remain_design_proposals_and_never_source_hydrated(self):
        obj,_=source()
        by_id={x["id"]:x for x in obj["cross_scale_records"]}
        for selected in ("ICE_REGOLITH_PLANETARY_COMPOSITION","APOSTLES_EM_COUNTERFIELD",
                         "ASTEROID_SPACEJUNK_CAPTURE","SAI_AU_REGION"):
            p=by_id[selected]
            self.assertFalse(p["executable"])
            self.assertFalse(p["rights_clearance"])
            self.assertIsNone(p["object_id"])
        self.assertIn("not inevitably accrete",by_id["ICE_REGOLITH_PLANETARY_COMPOSITION"]["non_equivalence"])
        self.assertIn("does not stop radiation",by_id["APOSTLES_EM_COUNTERFIELD"]["non_equivalence"])
        self.assertIn("not authenticate",by_id["SAI_AU_REGION"]["non_equivalence"])

    def test_no_profile_without_original_source_lineage_is_claimed_as_qualified(self):
        obj,registry=source()
        bad=copy.deepcopy(obj)
        bad["cross_scale_records"][4]["source_state"]="REAL_SOURCE_PROVEN"
        with self.assertRaisesRegex(ValueError,"source lineage"):
            review_cross_scale(bad,registry)
        bad=copy.deepcopy(obj)
        bad["cross_scale_records"][4]["required_qualification"]=[]
        with self.assertRaisesRegex(ValueError,"Insufficient"):
            review_cross_scale(bad,registry)



class PassiveBistaticInputReviewTests(unittest.TestCase):
    """Source-only metadata and denial paths; zero sensing or capture claims."""
    def sample(self):
        channel = {
            "channel_id": "ref-01",
            "source_locator": "synthetic://reference-channel-01",
            "center_hz": 100_000_000,
            "bandwidth_hz": 1_000_000,
            "sampling_hz": 2_500_000,
            "epoch_utc": "2026-10-21T00:00:00Z",
            "timebase_id": "synthetic-clock-01",
            "calibration_id": "unverified-calibration-reference",
            "noise_floor_dbm": -90,
        }
        surveillance = {
            **channel, "channel_id": "surveillance-02",
            "source_locator": "synthetic://surveillance-channel-02",
            "calibration_id": "unverified-calibration-surveillance",
        }
        geometry = {
            "frame_id": "synthetic-local-cartesian",
            "epoch_utc": channel["epoch_utc"],
            "tx_rx_m": 3000,
            "tx_to_hypothesis_m": 5000,
            "hypothesis_to_rx_m": 4000,
        }
        return channel, surveillance, geometry

    def review(self, a, b, g):
        from cgx.review.cross_scale_interaction_review import screen_passive_bistatic_inputs
        return screen_passive_bistatic_inputs(reference=a, surveillance=b, geometry=g)

    def test_complete_synthetic_input_is_never_detection_or_rights_proof(self):
        a,b,g=self.sample()
        v=self.review(a,b,g)
        self.assertEqual(v["status"],"SYNTHETIC_METADATA_SHAPE_COMPLETE_ONLY")
        self.assertEqual(v["holds"],[])
        self.assertEqual(v["existing_profile"],"AMBIENT_BISTATIC_RADAR")
        self.assertAlmostEqual(float(v["hypothetical_excess_path_delay_s"]),
                               6000/299792458,places=14)
        for field in ("original_source_bytes_verified","calibration_independently_verified",
                      "measured_signal_processed","target_detected_or_tracked",
                      "transmitter_activated","right_to_publish","owner_dbr_verified",
                      "sai_or_country_network_enabled"):
            self.assertIs(v[field],False,field)

    def test_no_reference_is_hold(self):
        a,b,g=self.sample()
        v=self.review(None,b,g)
        self.assertIn("MISSING_REFERENCE_CHANNEL",v["holds"])
        self.assertEqual(v["status"],"HOLD_MISSING_OR_INCOMPATIBLE_INPUTS")

    def test_no_surveillance_is_hold(self):
        a,b,g=self.sample()
        v=self.review(a,None,g)
        self.assertIn("MISSING_SURVEILLANCE_CHANNEL",v["holds"])

    def test_two_channels_must_be_independent(self):
        a,b,g=self.sample()
        b["source_locator"]=a["source_locator"]
        b["channel_id"]=a["channel_id"]
        self.assertIn("INDEPENDENT_CHANNEL_IDENTITIES_REQUIRED",self.review(a,b,g)["holds"])

    def test_same_multichannel_source_file_can_hold_distinct_stream_ids(self):
        a,b,g=self.sample()
        b["source_locator"]=a["source_locator"]
        v=self.review(a,b,g)
        self.assertEqual(v["status"],"SYNTHETIC_METADATA_SHAPE_COMPLETE_ONLY")
        self.assertFalse(v["original_source_bytes_verified"])

    def test_bad_noise_floor_is_not_calibration_evidence(self):
        a,b,g=self.sample()
        for value in (True, None, float("nan"), float("inf"), "not a reading"):
            ref=dict(a); ref["noise_floor_dbm"]=value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.review(ref,b,g)

    def test_center_bands_must_overlap(self):
        a,b,g=self.sample()
        b["center_hz"]=120_000_000
        self.assertIn("NO_SHARED_DECLARED_RF_BAND",self.review(a,b,g)["holds"])

    def test_unqualified_timebase_and_epoch_fail_closed(self):
        a,b,g=self.sample()
        b["timebase_id"]="other-clock"
        self.assertIn("COMMON_TIMEBASE_NOT_DECLARED",self.review(a,b,g)["holds"])
        b["timebase_id"]=a["timebase_id"]
        g["epoch_utc"]="2026-10-21T00:01:00Z"
        self.assertIn("GEOMETRY_EPOCH_MISMATCH",self.review(a,b,g)["holds"])

    def test_impossible_bistatic_triangle_is_rejected(self):
        a,b,g=self.sample()
        g["tx_to_hypothesis_m"]=800
        g["hypothesis_to_rx_m"]=1000
        v=self.review(a,b,g)
        self.assertIn("GEOMETRIC_TRIANGLE_INCONSISTENT",v["holds"])
        self.assertIsNone(v["hypothetical_excess_path_delay_s"])

    def test_missing_geometry_never_implies_range_or_location(self):
        a,b,_=self.sample()
        v=self.review(a,b,None)
        self.assertIn("MISSING_BISTATIC_GEOMETRY",v["holds"])
        self.assertIsNone(v["hypothetical_excess_path_delay_s"])
        self.assertFalse(v["target_detected_or_tracked"])

    def test_bandwidth_without_sufficient_sampling_flags_hold(self):
        a,b,g=self.sample()
        a["sampling_hz"]=900_000
        self.assertIn("REFERENCE_BANDWIDTH_NOT_BELOW_SAMPLE_RATE",self.review(a,b,g)["holds"])

    def test_nonfinite_and_boolean_numbers_rejected(self):
        a,b,g=self.sample()
        for value in (False, float("nan"),float("inf"), -1,0):
            a0=dict(a);a0["center_hz"]=value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.review(a0,b,g)

    def test_malformed_timestamps_and_injected_rights_rejected(self):
        a,b,g=self.sample()
        a["epoch_utc"]="2026-10-21T00:00:00"
        with self.assertRaises(ValueError):
            self.review(a,b,g)
        a,b,g=self.sample()
        a["rights_attested"]=True
        with self.assertRaisesRegex(ValueError,"Exact reference channel schema"):
            self.review(a,b,g)

    def test_unverified_claims_rejected_for_any_channel(self):
        a,b,g=self.sample()
        b["native_dbr_accepted"]=True
        with self.assertRaises(ValueError):
            self.review(a,b,g)


if __name__=="__main__":
    unittest.main()
