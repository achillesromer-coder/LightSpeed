import itertools,unittest,copy
from fractions import Fraction
from lightspeed_runtime.achilles.native_geometry import Geometry,quantity
from lightspeed_runtime.achilles.native_methods import discover
from lightspeed_runtime.achilles.native_model_review import build_model,transition,run_active
from lightspeed_runtime.achilles.native_semantic_review import describe,compare

def q(x,unit="kg"):
    f=Fraction(x);return quantity(f.numerator,f.denominator,unit)
def method(a,b,keys=(-16,-8,-4,0,4,8),unit="kg"):
    def case(x):return {"x":q(x,unit),"y":q(a*x+b,unit)}
    return discover([case(x) for x in keys[:3]],[case(x) for x in keys[3:]])
class SemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Geometry();cls.at=min(cls.g.leaves)
        cls.m={k:method(*k) for k in itertools.product([-2,-1,0,1,2],[-1,0,1])}
    def test_boundaries(self):
        a=build_model("A",[method(1,0)])
        b=build_model("B",[method(1,0,(-12,-6,-3,0,3,6))])
        r=compare(a,b)["review"]
        self.assertEqual(r["status"],"SAME_AFFINE_LAW_ON_OVERLAP")
        self.assertNotEqual(r["left"]["method_revisions"],r["right"]["method_revisions"])
        self.assertEqual(r["overlap"],[[-12,1],[6,1]])
        self.assertFalse(r["evidence_merge"])
        self.assertFalse(r["permission_inheritance"])
        for keys,unit,status in (((20,21,22,23,24,25),"kg","HOLD_DISJOINT"),((-8,-6,-4,0,4,8),"m","HOLD_BOUNDARY")):
            other=build_model("B",[method(1,0,keys,unit)])
            self.assertEqual(compare(a,other)["review"]["status"],status)
        # Constant pipeline with an impossible successor envelope.
        with self.assertRaises(ValueError):describe(build_model("X",[method(0,40),method(1,0)]))
        bad=copy.deepcopy(a);bad["model"]["execution_authorized"]=True
        with self.assertRaises(ValueError):describe(bad)
    def test_point_only(self):
        a=build_model("A",[method(1,0,(-5,-4,-3,-2,-1,0))])
        b=build_model("B",[method(2,0,(0,1,2,3,4,5))])
        self.assertEqual(compare(a,b)["review"]["status"],"POINT_AGREEMENT_ONLY")
    def check_pair(self,s,t,x):
        m=build_model("A",[self.m[s],self.m[t]])
        a,b=t[0]*s[0],t[0]*s[1]+t[1]
        equivalent=build_model("B",[method(a,b)])
        d=describe(m)["review"]
        self.assertEqual((d["law"]["a"],d["law"]["b"]),([a,1],[b,1]))
        c=compare(m,equivalent)["review"]
        self.assertEqual(c["status"],"SAME_AFFINE_LAW_ON_OVERLAP")
        self.assertFalse(c["execution_authorized"])
        lo,hi=map(lambda v:Fraction(*v),d["input_envelope"])
        self.assertTrue(lo<=x<=hi)
        event=transition("A",0,None,m["sha256"],"propose")
        output=run_active([event],event["sha256"],{m["sha256"]:m},q(x),self.g,self.at,allowed=self.g.edges)
        self.assertEqual(output["record"]["result"],q(a*x+b))
def make(s,t,x):
    def test(self):self.check_pair(s,t,x)
    return test
keys=list(itertools.product([-2,-1,0,1,2],[-1,0,1]))
for i,(s,t,x) in enumerate(itertools.product(keys,keys,[-2,2])):
    setattr(SemanticTests,"test_equivalence_"+str(i),make(s,t,x))
