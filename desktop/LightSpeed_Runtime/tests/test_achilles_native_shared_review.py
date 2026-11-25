import copy,io,itertools,unittest,zipfile
from lightspeed_runtime.achilles.native_geometry import quantity,digest
from lightspeed_runtime.achilles.native_methods import discover
from lightspeed_runtime.achilles.native_model_review import build_model
from lightspeed_runtime.achilles.native_shared_review import pack_models,hydrate_candidate,occurrence

def method(m,b):
    def cases(xs):return [{"x":quantity(x),"y":quantity(m*x+b)} for x in xs]
    return discover(cases([-8,0,8]),cases([-4,1,4]))
def carrier(records):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w") as z:
        e=pack_models(z,records,task_id="fixture-task",source_revision="fixture-r1")
    return stream.getvalue(),e
def restore(raw,e,domain,candidate,auth=lambda *a:True,**changes):
    args={"domain":domain,"identity":candidate["model"]["identity"],"revision":candidate["sha256"],
          "task_id":"fixture-task","source_revision":"fixture-r1","scope_revision":"fixture-acl",
          "max_bytes":1024*1024,"authorise":auth}|changes
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        return hydrate_candidate(z,e,e["sha256"],**args)

class SharedReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=method(1,0);cls.b=method(2,1)
        cls.x=build_model("A",[cls.a,cls.b,cls.a]);cls.y=build_model("B",[cls.a])
        cls.domains=("Romer","Eco","EMASSC","LightSpeed")
        cls.records=[{"domain":d,"candidate":m} for d,m in itertools.product(cls.domains,(cls.x,cls.y))]
        cls.raw,cls.e=carrier(cls.records)
    def test_shared_payloads(self):
        b=self.e["review"]
        self.assertEqual((b["method_occurrences"],b["unique_methods"]),(12,2))
        entries=b["collection"]["entries"]
        for h in (self.a["sha256"],self.b["sha256"]):
            keys=[v["methods"][h] for v in b["index"].values() if h in v["methods"]]
            self.assertEqual(len({entries[k]["root"] for k in keys}),1)
            self.assertEqual(len(keys),len(set(keys)))
        with zipfile.ZipFile(io.BytesIO(self.raw)) as z:
            self.assertEqual(len(z.namelist()),len(set(z.namelist())))
    def test_permission_not_inherited(self):
        row=self.e["review"]["index"][occurrence("Romer","A",self.x["sha256"])]
        allowed={row["header"],*row["methods"].values()}
        auth=lambda task,k,*a:k in allowed
        r,stats=restore(self.raw,self.e,"Romer",self.x,auth)
        self.assertEqual(r,self.x)
        self.assertFalse(stats["active_status_verified"])
        for domain,m in (("Eco",self.x),("Romer",self.y)):
            with self.assertRaises(PermissionError):restore(self.raw,self.e,domain,m,auth)
        with self.assertRaises(PermissionError):restore(self.raw,self.e,"Romer",self.x,lambda task,k,*a:k==row["header"])
        calls=[]
        def revoke(*a):
            calls.append(a)
            return len(calls)<=len(allowed)
        with self.assertRaises(PermissionError):restore(self.raw,self.e,"Romer",self.x,revoke)
    def test_revision_budget_scope(self):
        for change in ({"revision":"0"*64},{"source_revision":"wrong"},{"max_bytes":1},{"identity":"other"}):
            with self.assertRaises((RuntimeError,ValueError)):restore(self.raw,self.e,"Romer",self.x,**change)
        bad=copy.deepcopy(self.e);bad["review"]["native_admitted"]=True
        with self.assertRaises(ValueError):restore(self.raw,bad,"Romer",self.x)
        bad=copy.deepcopy(self.e);row=bad["review"]["index"][occurrence("Romer","A",self.x["sha256"])]
        other=bad["review"]["index"][occurrence("Eco","A",self.x["sha256"])]
        row["methods"]=other["methods"];bad["sha256"]=digest(bad["review"])
        with self.assertRaises(ValueError):restore(self.raw,bad,"Romer",self.x)
    def test_duplicate_and_reorder(self):
        with self.assertRaises(ValueError):carrier([self.records[0]]*2)
        raw,e=carrier(list(reversed(self.records)))
        self.assertEqual(e,self.e);self.assertEqual(raw,self.raw)

def make(domain,which):
    def test(self):
        m=getattr(self,which)
        restored,receipt=restore(self.raw,self.e,domain,m)
        self.assertEqual(restored,m)
        self.assertFalse(receipt["execution_authorized"])
        self.assertEqual(receipt["occurrence"],occurrence(domain,m["model"]["identity"],m["sha256"]))
    return test
for d,m in itertools.product(("Romer","Eco","EMASSC","LightSpeed"),("x","y")):
    setattr(SharedReviewTests,"test_restore_"+d+"_"+m,make(d,m))
