import copy,itertools,unittest
from fractions import Fraction
from lightspeed_runtime.achilles.native_geometry import Geometry,quantity
from lightspeed_runtime.achilles.native_methods import discover
from lightspeed_runtime.achilles.native_model_review import build_model,transition,run_active,run_batch_review

def q(x):
    x=Fraction(x);return quantity(x.numerator,x.denominator,"kg")
def method(a,b):
    def c(keys):return [{"x":q(x),"y":q(a*x+b)} for x in keys]
    return discover(c([-64,0,64]),c([-32,1,32]))
class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Geometry();cls.at=min(cls.g.leaves)
        cls.m=build_model("batch-fixture",[method(2,1),method(-1,3)])
        cls.h=cls.m["sha256"];cls.events=[transition("batch-fixture",0,None,cls.h,"propose")]
        cls.head=cls.events[0]["sha256"];cls.store={cls.h:cls.m}
    def batch(self,x,**changes):
        args={"allowed":self.g.edges,"current_head":lambda:self.head}|changes
        return run_batch_review(self.events,self.head,self.store,x,self.g,self.at,**args)
    def test_parity(self):
        xs=[q(Fraction(i,13)) for i in range(-150,151)]
        out,receipt=self.batch(xs)
        self.assertEqual(out,[run_active(self.events,self.head,self.store,x,self.g,self.at,allowed=self.g.edges) for x in xs])
        self.assertEqual(receipt["receipt"]["cost"],8*len(xs))
        self.assertFalse(receipt["receipt"]["execution_authorized"])
    def test_head_change(self):
        calls=[]
        def status():
            calls.append(1);return self.head if len(calls)<=4 else "0"*64
        with self.assertRaises(ValueError):self.batch([q(1),q(2),q(3)],current_head=status)
        with self.assertRaises(ValueError):self.batch([q(1)],current_head=lambda:"0"*64)
    def test_budget(self):
        for opt in ({"per_input_budget":7},{"total_budget":15},{"total_budget":True},{"per_input_budget":244}):
            with self.assertRaises(ValueError):self.batch([q(1),q(2)],**opt)
        out,r=self.batch([q(1),q(2)],total_budget=16)
        self.assertEqual(r["receipt"]["cost"],16)
    def test_inputs(self):
        for xs in ([],[q(1)]*513,[q(100)],[quantity(1,unit="m")]):
            with self.assertRaises(ValueError):self.batch(xs)
    def test_snapshot(self):
        data=copy.deepcopy(self.store)
        def reader():
            return self.head
        data[self.h]["model"]["methods"][next(iter(data[self.h]["model"]["methods"]))]["method"]["offset"]["n"]=99
        with self.assertRaises(ValueError):
            run_batch_review(self.events,self.head,data,[q(1)],self.g,self.at,allowed=self.g.edges,current_head=reader)
    def test_geometry_mutation(self):
        g=Geometry();g.adj[self.at]=()
        with self.assertRaises(ValueError):
            run_batch_review(self.events,self.head,self.store,[q(1)],g,self.at,allowed=self.g.edges,current_head=lambda:self.head)
    def test_revoked(self):
        ev=self.events+[transition("batch-fixture",1,self.head,self.h,"revoke")]
        with self.assertRaises(ValueError):
            run_batch_review(ev,ev[-1]["sha256"],self.store,[q(1)],self.g,self.at,allowed=self.g.edges,current_head=lambda:ev[-1]["sha256"])
