"""Bounded affine semantic equivalence; evidence and permissions are never deduplicated.
Uses existing candidate verifier. Pure review metadata, not an execution or mint path.
"""
from fractions import Fraction
from lightspeed_runtime.achilles.native_geometry import digest, quantity, require
from lightspeed_runtime.achilles.native_model_review import verify_model

def _f(q):
    return Fraction(q["n"],q["d"])

def _pair(f):
    return [f.numerator,f.denominator]

def describe(envelope):
    """Exact affine composition and preimage of every tested stage envelope.
    A mathematical relation, not a proof of empirical applicability or runtime equivalence.
    """
    verified=verify_model(envelope)
    body=verified["model"]
    a,b=Fraction(1),Fraction(0)
    lower=upper=None
    unit=frame=None
    traces=[]
    for h in body["pipeline"]:
        m=body["methods"][h]["method"]
        if unit is None:unit,frame=m["unit"],m["frame"]
        require((unit,frame)==(m["unit"],m["frame"]),"incompatible pipeline boundaries")
        lo,hi=map(_f,m["domain"])
        if a==0:
            require(lo<=b<=hi,"empty tested envelope")
        else:
            p,q=sorted(((lo-b)/a,(hi-b)/a))
            lower=p if lower is None else max(lower,p)
            upper=q if upper is None else min(upper,q)
            require(lower<=upper,"empty tested envelope")
        slope,offset=_f(m["slope"]),_f(m["offset"])
        a,b=slope*a,slope*b+offset
        # Bound symbolic coefficient growth; neither endpoint implies capacity to execute.
        require(max(abs(a.numerator),a.denominator,abs(b.numerator),b.denominator).bit_length()<=256,"semantic coefficient bound")
        traces.append(h)
    require(lower is not None and upper is not None,"missing tested envelope")
    require(max(abs(lower.numerator),lower.denominator,abs(upper.numerator),upper.denominator).bit_length()<=256,"semantic envelope bound")
    law={"family":"affine","unit":unit,"frame":frame,"scope":"fixture","a":_pair(a),"b":_pair(b)}
    result={"schema":"CGX-IM-AFFINE-SEMANTIC-REVIEW/0.1","identity":body["identity"],
            "candidate_sha256":verified["sha256"],"law":law,"law_sha256":digest(law),
            "input_envelope":[_pair(lower),_pair(upper)],"method_revisions":traces,
            "native_admitted":False,"execution_authorized":False}
    return {"review":result,"sha256":digest(result)}

def compare(left,right):
    l,r=(describe(x)["review"] for x in (left,right))
    ll,rr=l["law"],r["law"]
    compatible=all(ll[k]==rr[k] for k in ("family","unit","frame","scope"))
    lo=max(Fraction(*l["input_envelope"][0]),Fraction(*r["input_envelope"][0]))
    hi=min(Fraction(*l["input_envelope"][1]),Fraction(*r["input_envelope"][1]))
    overlap=compatible and lo<=hi
    same_law=compatible and ll==rr
    if not compatible:status="HOLD_BOUNDARY"
    elif not overlap:status="HOLD_DISJOINT"
    elif same_law:status="SAME_AFFINE_LAW_ON_OVERLAP"
    elif lo==hi and Fraction(*ll["a"])*lo+Fraction(*ll["b"])==Fraction(*rr["a"])*lo+Fraction(*rr["b"]):
        status="POINT_AGREEMENT_ONLY"
    else:status="DIFFERENT_LAW"
    result={"status":status,"left":l,"right":r,
            "overlap":[_pair(lo),_pair(hi)] if overlap else None,
            "shared_law_sha256":l["law_sha256"] if same_law else None,
            "evidence_merge":False,"permission_inheritance":False,"execution_authorized":False,
            "native_admitted":False}
    return {"review":result,"sha256":digest(result)}
