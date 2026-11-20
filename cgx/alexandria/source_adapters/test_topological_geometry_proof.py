import unittest
from topological_geometry_proof import regular_dodecahedron_topology, solve_regular_polyhedron_incidence

class TestTopology(unittest.TestCase):
    def test_exact_dodecahedron_integer_derivation(self):
        result = regular_dodecahedron_topology()
        self.assertEqual(result["derived"],
            {"faces": 12, "edges": 30, "vertices": 20, "euler_characteristic": 2})
    def test_incidence_relations(self):
        p=regular_dodecahedron_topology()
        x=p["derived"]
        self.assertEqual(5*x["faces"],2*x["edges"])
        self.assertEqual(3*x["vertices"],2*x["edges"])
        self.assertEqual(x["vertices"]-x["edges"]+x["faces"],2)
    def test_not_a_source_admission_or_physical_geometry(self):
        r=regular_dodecahedron_topology()
        self.assertIsNone(r["native_cgx_object_id"])
        self.assertFalse(r["euclidean_coordinates_derived"])
        self.assertFalse(r["scientific_measurement"])
        self.assertFalse(r["dbr_readback"])
    def test_noninteger_input_rejected(self):
        with self.assertRaises(ValueError):
            solve_regular_polyhedron_incidence(faces=12.0, edges_per_face=5,
                                              faces_meeting_at_vertex=3)
    def test_nonregular_invalid_geometry_rejected(self):
        with self.assertRaises(ValueError):
            solve_regular_polyhedron_incidence(faces=12, edges_per_face=4,
                                              faces_meeting_at_vertex=3)
    def test_icosahedron_as_distinct_mathematical_family(self):
        r=solve_regular_polyhedron_incidence(faces=20, edges_per_face=3,
                                             faces_meeting_at_vertex=5)
        self.assertEqual(r["derived"],{"faces":20,"edges":30,"vertices":12,"euler_characteristic":2})

if __name__=="__main__":
    unittest.main()
