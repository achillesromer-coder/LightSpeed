"""Bounded CGX-IM L5 functional geometry; private review kernel, not a lease or mint service."""
from collections import defaultdict, deque
from fractions import Fraction
from hashlib import sha256
from itertools import permutations
import json

MAX_DEPTH = 5
MAX_INT = 10**18
OPS = frozenset(("add", "sub", "mul", "div"))
STATES = frozenset(("verified", "unverified", "revoked"))


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _det(a, b, c):
    return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])


class Geometry:
    """Exact cone subdivision fixture; no T173 shape assignments or authority inferred."""
    def __init__(self, depth=5):
        require(type(depth) is int and 1 <= depth <= MAX_DEPTH, "depth")
        self.depth = depth
        self.scale = 3**depth
        self.volumes = {}
        faces = defaultdict(list)
        def build(p, t):
            self.volumes[p] = _det(*t)
            if len(p) == depth:
                for a, b in zip(t, t[1:]+t[:1]):
                    faces[tuple(sorted((a,b)))].append((p,a,b))
                return
            a,b,c = t
            sums = tuple(sum(x) for x in zip(a,b,c))
            require(all(x%3 == 0 for x in sums), "centroid")
            g = tuple(x//3 for x in sums)
            for i, child in enumerate(((a,b,g),(b,c,g),(c,a,g))):
                build(p+str(i), child)
        s = self.scale
        build("", ((s,0,0),(0,s,0),(0,0,s)))
        self.leaves = frozenset(p for p in self.volumes if len(p)==depth)
        adjacency = defaultdict(set)
        for v in faces.values():
            require(len(v) in (1,2), "nonmanifold")
            if len(v)==2:
                (x,a,b),(y,c,d)=v
                require((a,b)==(d,c), "orientation")
                adjacency[x].add(y); adjacency[y].add(x)
        self.edges = frozenset((x,y) for x in adjacency for y in adjacency[x])
        self.adj = {x:tuple(sorted(adjacency[x])) for x in self.leaves}
        require(all(v>0 for v in self.volumes.values()), "volume")
        require(all(sum(self.volumes[p+str(i)] for i in range(3))==v for p,v in self.volumes.items() if len(p)<depth), "conservation")

    def route(self, start, end, allowed, budget=243):
        require(type(budget) is int and 1<=budget<=243, "budget")
        require(start in self.leaves and end in self.leaves, "address")
        allowed=frozenset(allowed)
        require(allowed <= self.edges, "nonincident edge")
        q=deque([(start,(start,))]); seen={start}
        while q:
            x,p=q.popleft()
            if x==end:return p
            if len(p)>=budget:continue
            for y in self.adj[x]:
                if (x,y) in allowed and y not in seen:
                    seen.add(y);q.append((y,p+(y,)))
        return None


def quantity(n, d=1, unit="1", frame="fixture", scope="fixture"):
    require(type(n) is int and type(d) is int and abs(n)<=MAX_INT and 0<d<=MAX_INT, "rational bounds")
    require(all(type(x) is str and 0<len(x)<=128 for x in (unit,frame,scope)), "quantity metadata")
    f=Fraction(n,d)
    return {"n":f.numerator,"d":f.denominator,"unit":unit,"frame":frame,"scope":scope}


def validate(q):
    require(type(q) is dict and set(q)=={"n","d","unit","frame","scope"}, "quantity schema")
    require(q==quantity(q["n"],q["d"],q["unit"],q["frame"],q["scope"]), "canonical quantity")
    return q


def calculate(op,a,b):
    require(op in OPS,"unknown operation")
    validate(a);validate(b)
    require(a["scope"]==b["scope"] and a["frame"]==b["frame"],"boundary metadata")
    require(a["unit"]==b["unit"] if op in ("add","sub") else b["unit"]=="1","units")
    x,y=Fraction(a["n"],a["d"]),Fraction(b["n"],b["d"])
    require(op!="div" or y!=0,"division by zero")
    z={"add":lambda:x+y,"sub":lambda:x-y,"mul":lambda:x*y,"div":lambda:x/y}[op]()
    return quantity(z.numerator,z.denominator,a["unit"],a["frame"],a["scope"])


def compose(geometry, inputs, steps, *, allowed, scope, budget=243):
    """Pure DAG in topological order. Allowed edges are fixture policy, NOT real grants.
    All values (including caller inputs) are bound to fixture scope; no external dispatch.
    """
    require(type(geometry) is Geometry and scope=="fixture","review scope only")
    require(type(budget) is int and 1<=budget<=243,"budget")
    require(type(inputs) is dict and 0<len(inputs)<=243 and type(steps) in (list,tuple) and 0<len(steps)<=243,"graph bounds")
    allowed=frozenset(allowed)
    require(allowed<=geometry.edges,"invalid boundary")
    known={}
    def key(x):
        require(type(x) is str and 0<len(x)<=64,"facet id")
        return x
    for k,v in inputs.items():
        key(k);require(type(v) is dict and set(v)=={"at","value"},"input schema")
        require(v["at"] in geometry.leaves and validate(v["value"])["scope"]==scope,"input boundary")
        known[k]={"at":v["at"],"value":dict(v["value"])}
    trace=[];remaining=budget
    for s in steps:
        require(type(s) is dict and set(s)=={"id","at","op","args"},"step schema")
        k=key(s["id"]);at=s["at"];args=s["args"]
        require(k not in known and at in geometry.leaves,"duplicate or missing address")
        require(type(args) in (list,tuple) and len(args)==2 and all(type(x) is str and x in known for x in args),"unresolved dependency")
        paths=[]
        for arg in args:
            require(remaining>0,"aggregate budget")
            p=geometry.route(known[arg]["at"],at,allowed,remaining)
            require(p is not None,"boundary held")
            remaining-=len(p);paths.append(list(p))
        value=calculate(s["op"],*(known[x]["value"] for x in args))
        known[k]={"at":at,"value":value}
        trace.append({"id":k,"at":at,"op":s["op"],"args":list(args),"inputs":[dict(known[x]["value"]) for x in args],"paths":paths,"value":dict(value)})
    record={"scope":scope,"initial_inputs":{k:{"at":v["at"],"value":dict(v["value"])} for k,v in inputs.items()},"trace":trace,"cost":budget-remaining}
    return {"record":record,"sha256":digest(record)}


def perspectives(ids):
    require(type(ids) in (tuple,list) and len(ids)==3 and all(type(x) is str and x for x in ids) and len(set(ids))==3,"identities")
    return {x:{"Me":x,"Myself":ids[(i+1)%3],"I":ids[(i+2)%3]} for i,x in enumerate(ids)}


def reconcile(votes):
    require(type(votes) in (tuple,list) and len(votes)==3 and all(x in ("yes","no","maybe") for x in votes),"ternary")
    return votes[0] if len(set(votes))==1 else "maybe"


def make_event(previous, seq, facet, status, value, evidence):
    require(type(seq) is int and 0<=seq<4096 and type(facet) is str and 0<len(facet)<=64,"event bounds")
    require(status in STATES and type(evidence) is str and 0<len(evidence)<=128,"event state")
    require(previous is None or (type(previous) is str and len(previous)==64),"parent")
    require((status=="verified" and type(value) is dict and validate(value)["scope"]=="fixture") or (status!="verified" and value is None),"evidence value")
    body={"seq":seq,"prev":previous,"facet":facet,"status":status,"value":dict(value) if value else None,"evidence":evidence,"scope":"fixture"}
    return {"body":body,"sha256":digest(body)}


def replay(events, expected_head):
    """Integrity and anti-truncation relative to supplied trusted head; no signature validation."""
    require(type(events) in (list,tuple) and len(events)<=4096,"history bounds")
    prev=None;state={}
    for i,e in enumerate(events):
        require(type(e) is dict and set(e)=={"body","sha256"},"event envelope")
        b=e["body"]
        require(type(b) is dict and set(b)=={"seq","prev","facet","status","value","evidence","scope"},"event schema")
        reconstructed=make_event(prev,i,b["facet"],b["status"],b["value"],b["evidence"])
        require(e==reconstructed,"history integrity")
        prev=e["sha256"]
        state[b["facet"]]={"status":b["status"],"value":dict(b["value"]) if b["value"] else None,"event":prev}
    require(prev==expected_head,"head mismatch")
    return state
