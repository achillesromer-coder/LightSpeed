"""Synthetic regression for the native CGX-IM review kernel."""
import copy
import itertools
import unittest
from fractions import Fraction
from lightspeed_runtime.achilles.native_geometry import Geometry, quantity, calculate, compose, perspectives, reconcile, make_event, replay

class NativeGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Geometry()
        cls.start=min(cls.g.leaves)
        cls.end=max(cls.g.leaves)

    def test_counts(self):
        self.assertEqual((len(self.g.volumes),len(self.g.leaves),len(self.g.edges)),(364,243,726))

    def test_composition(self):
        a=self.start;b=self.g.adj[a][0]
        data={"a":{"at":a,"value":quantity(2,3,"m")},"b":{"at":b,"value":quantity(1,6,"m")},"c":{"at":b,"value":quantity(3)}}
        steps=[{"id":"sum","at":b,"op":"add","args":["a","b"]},{"id":"scaled","at":b,"op":"mul","args":["sum","c"]}]
        r=compose(self.g,data,steps,allowed=self.g.edges,scope="fixture")
        self.assertEqual(r["record"]["trace"][-1]["value"],quantity(5,2,"m"))
        self.assertEqual(r,compose(self.g,data,steps,allowed=self.g.edges,scope="fixture"))
        for changes in ({"budget":1},{"scope":"production"},{"allowed":set()}):
            kwargs={"allowed":self.g.edges,"scope":"fixture"}|changes
            with self.assertRaises(ValueError):compose(self.g,data,steps,**kwargs)
        for step in (steps[1],steps[0]|{"id":"a"},steps[0]|{"op":"shell"}):
            with self.assertRaises(ValueError):compose(self.g,data,[step],allowed=self.g.edges,scope="fixture")

    def test_history(self):
        a=make_event(None,0,"x","verified",quantity(1),"fixture-a")
        b=make_event(a["sha256"],1,"x","unverified",None,"fixture-b")
        c=make_event(b["sha256"],2,"x","verified",quantity(2),"fixture-c")
        d=make_event(c["sha256"],3,"x","revoked",None,"fixture-d")
        self.assertIsNone(replay([a,b],b["sha256"])["x"]["value"])
        self.assertEqual(replay([a,b,c],c["sha256"])["x"]["value"],quantity(2))
        self.assertIsNone(replay([a,b,c,d],d["sha256"])["x"]["value"])
        for seq in ([a,b,c],[b,a,c,d],[]):
            with self.assertRaises(ValueError):replay(seq,d["sha256"])
        tampered=copy.deepcopy([a,b,c,d]);tampered[0]["body"]["value"]["n"]=9
        with self.assertRaises(ValueError):replay(tampered,d["sha256"])

    def test_limits(self):
        for d in (0,6,True):
            with self.assertRaises(ValueError):Geometry(d)
        with self.assertRaises(ValueError):self.g.route("174",self.end,self.g.edges)
        with self.assertRaises(ValueError):self.g.route(self.start,self.end,[(self.start,self.end)])
        self.assertIsNone(self.g.route(self.start,self.end,self.g.edges,1))
        for b in (quantity(1,unit="kg"),quantity(1,frame="other"),quantity(1,scope="other")):
            with self.assertRaises(ValueError):calculate("add",quantity(1,unit="m"),b)
        with self.assertRaises(ValueError):calculate("div",quantity(1),quantity(0))
        with self.assertRaises(ValueError):calculate("mul",quantity(10**18),quantity(10**18))

    def test_reciprocity(self):
        ids=("A1","A2","A3")
        views=perspectives(ids)
        for offset in range(3):
            self.assertEqual(views,perspectives(ids[offset:]+ids[:offset]))
        self.assertEqual({k:v["Me"] for k,v in views.items()},dict(zip(ids,ids)))

# Independent discoverable test cases, not counted subassertions or claimed feature implementations.
def route_case(target):
    def test(self):
        p=self.g.route(self.start,target,self.g.edges)
        self.assertIsNotNone(p)
        self.assertEqual((p[0],p[-1]),(self.start,target))
        self.assertTrue(all(e in self.g.edges for e in zip(p,p[1:])))
    return test

def volume_case(target):
    def test(self):
        self.assertEqual(Fraction(self.g.volumes[target],6*self.g.scale**3),Fraction(1,6*243))
    return test

def direction_case(a,b):
    def test(self):
        self.assertEqual(self.g.route(a,b,{(a,b)}),(a,b))
        self.assertIsNone(self.g.route(b,a,{(a,b)}))
    return test

def ternary_case(votes):
    def test(self):
        expected=votes[0] if len(set(votes))==1 else "maybe"
        self.assertTrue(all(reconcile(p)==expected for p in itertools.permutations(votes)))
    return test

g=Geometry()
for leaf in sorted(g.leaves):
    setattr(NativeGeometryTests,"test_path_"+leaf,route_case(leaf))
    setattr(NativeGeometryTests,"test_volume_"+leaf,volume_case(leaf))
for a,b in sorted(g.edges):
    if a<b:setattr(NativeGeometryTests,"test_direction_"+a+"_"+b,direction_case(a,b))
for i,votes in enumerate(itertools.product(("yes","no","maybe"),repeat=3)):
    setattr(NativeGeometryTests,"test_ternary_"+str(i),ternary_case(votes))
