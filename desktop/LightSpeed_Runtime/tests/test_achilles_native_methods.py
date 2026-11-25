import copy,itertools,unittest
from fractions import Fraction
from lightspeed_runtime.achilles.native_geometry import Geometry,quantity
from lightspeed_runtime.achilles.native_methods import discover,apply,existing_context
from lightspeed_runtime.cgx_capability_registry import capability_interop_review

def q(x,unit="kg"):
    x=Fraction(x);return quantity(x.numerator,x.denominator,unit)
def cases(m,b,keys):
    return [{"x":q(x),"y":q(m*x+b)} for x in keys]

class NativeMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Geometry();cls.at=min(cls.g.leaves)
    def run_case(self,m,b,x):
        a=discover(cases(m,b,[-4,0,4]),cases(m,b,[-3,1,3]))
        self.assertEqual(a,discover(cases(m,b,[4,-4,0]),cases(m,b,[3,-3,1])))
        r=apply(a,a["sha256"],q(x),self.g,self.at,allowed=self.g.edges)
        self.assertEqual(r["record"]["result"],q(m*x+b))
        self.assertFalse(r["record"]["execution_authorized"])
    def test_invalid(self):
        train=cases(2,1,[-4,0,4]); hold=cases(2,1,[-3,1,3])
        a=discover(train,hold)
        for bad in ([*hold[:2],{"x":q(0),"y":q(1)}],
                    [*hold[:2],{"x":q(3),"y":q(100)}],
                    [*hold[:2],{"x":q(3,"m"),"y":q(7,"m")}]):
            with self.assertRaises(ValueError):discover(train,bad)
        with self.assertRaises(ValueError):discover(train[:2],hold)
        for x,head,budget in ((q(5),a["sha256"],243),(q(0),"0"*64,243),
                              (q(0,"m"),a["sha256"],243),(q(0),a["sha256"],3)):
            with self.assertRaises(ValueError):apply(a,head,x,self.g,self.at,allowed=self.g.edges,budget=budget)
        b=copy.deepcopy(a);b["method"]["offset"]["n"]=5
        with self.assertRaises(ValueError):apply(b,a["sha256"],q(0),self.g,self.at,allowed=self.g.edges)
    def test_registry_reference(self):
        view=capability_interop_review("Achilles")
        ref=sorted(view["references"])[0]
        out=existing_context("Achilles","native-method-review",ref)
        self.assertIn(ref,out["references"])
        self.assertFalse(out["execution_authorized"])
        self.assertFalse(out["native_admitted"])
        with self.assertRaises(Exception):existing_context("Achilles","native-method-review","unknown:fixture")
def make(m,b,x):
    def test(self):self.run_case(m,b,x)
    return test
for i,(m,b,x) in enumerate(itertools.product([Fraction(-3),Fraction(-1,2),Fraction(0),Fraction(1,3),Fraction(2),Fraction(3),Fraction(5,2)],range(-3,4),[Fraction(-7,2),Fraction(-2),Fraction(-1,2),Fraction(0),Fraction(1,2),Fraction(2),Fraction(7,2)])):
    setattr(NativeMethodTests,"test_transfer_"+str(i),make(m,b,x))
