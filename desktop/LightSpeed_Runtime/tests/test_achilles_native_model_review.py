import copy,itertools,unittest
from fractions import Fraction
from lightspeed_runtime.achilles.native_geometry import Geometry,quantity
from lightspeed_runtime.achilles.native_methods import discover
from lightspeed_runtime.achilles.native_model_review import build_model,verify_model,transition,resolve_history,run_active,release_review

def q(x):
    x=Fraction(x);return quantity(x.numerator,x.denominator,"kg")
def method(m,b):
    def cases(keys):return [{"x":q(x),"y":q(m*x+b)} for x in keys]
    return discover(cases([-64,0,64]),cases([-32,1,32]))
def genesis(model):
    h=model["sha256"];e=transition(model["model"]["identity"],0,None,h,"propose")
    return [e],e["sha256"],{h:model}

class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Geometry();cls.at=min(cls.g.leaves)
        cls.methods={k:method(*k) for k in itertools.product([-2,-1,0,1,2],[-1,0,1])}
    def run_case(self,a,b,x):
        stages=[self.methods[a],self.methods[b]]
        m=build_model("fixture-model",stages)
        e,h,store=genesis(m)
        r=run_active(e,h,store,q(x),self.g,self.at,allowed=self.g.edges)
        self.assertEqual(r["record"]["result"],q(b[0]*(a[0]*x+a[1])+b[1]))
        self.assertEqual(r["record"]["cost"],8)
        self.assertEqual(r,run_active(e,h,store,q(x),self.g,self.at,allowed=self.g.edges))
        self.assertEqual(len(m["model"]["methods"]),len(set(m["model"]["pipeline"])))
        self.assertFalse(r["record"]["execution_authorized"])
    def test_history_and_release(self):
        a=build_model("fixture-model",[self.methods[(1,0)]])
        b=build_model("fixture-model",[self.methods[(2,0)]])
        e,h,store=genesis(a);store[b["sha256"]]=b
        e.append(transition("fixture-model",1,h,b["sha256"],"supersede"));h=e[-1]["sha256"]
        self.assertEqual(resolve_history(e,h,store)["active"],b["sha256"])
        review=release_review(e,h,store)["review"]
        self.assertEqual(len(review["floors"]),8)
        self.assertFalse(review["publication_authorized"])
        for stale in (e[:1],list(reversed(e))):
            with self.assertRaises(ValueError):resolve_history(stale,h,store)
        e.append(transition("fixture-model",2,h,b["sha256"],"revoke"));h=e[-1]["sha256"]
        self.assertIsNone(resolve_history(e,h,store)["active"])
        with self.assertRaises(ValueError):release_review(e,h,store)
        with self.assertRaises(ValueError):run_active(e,h,store,q(1),self.g,self.at,allowed=self.g.edges)
        e.append(transition("fixture-model",3,h,a["sha256"],"supersede"))
        with self.assertRaises(ValueError):resolve_history(e,e[-1]["sha256"],store)
    def test_tamper_budget_and_identity(self):
        a=build_model("fixture-model",[self.methods[(1,0)]]*2)
        e,h,store=genesis(a)
        with self.assertRaises(ValueError):run_active(e,h,store,q(1),self.g,self.at,allowed=self.g.edges,budget=7)
        with self.assertRaises(ValueError):run_active(e,h,store,q(65),self.g,self.at,allowed=self.g.edges)
        bad=copy.deepcopy(a);bad["model"]["execution_authorized"]=True
        with self.assertRaises(ValueError):verify_model(bad)
        wrong=transition("other",0,None,a["sha256"],"propose")
        with self.assertRaises(ValueError):resolve_history([wrong],wrong["sha256"],store)
        bad=copy.deepcopy(a);bad["model"]["methods"]["0"*64]=self.methods[(1,0)]
        with self.assertRaises(ValueError):verify_model(bad)
def make(a,b,x):
    def test(self):self.run_case(a,b,x)
    return test
keys=list(itertools.product([-2,-1,0,1,2],[-1,0,1]))
for i,(a,b,x) in enumerate(itertools.product(keys,keys,[-3,2])):
    setattr(ModelTests,"test_composition_"+str(i),make(a,b,x))
