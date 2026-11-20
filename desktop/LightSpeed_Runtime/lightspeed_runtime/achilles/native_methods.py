"""Evidence-bound affine method discovery for the existing CGX-IM review kernel.
Only synthetic, exact rational, same-unit quantities; never promotes or executes external routes.
"""
from fractions import Fraction
from lightspeed_runtime.achilles.native_geometry import (
    Geometry, calculate, compose, digest, quantity, require, validate,
)
from lightspeed_runtime.cgx_capability_registry import (
    capability_interop_review, compose_capability_review,
)

SCHEMA = "CGX-IM-AFFINE-METHOD-REVIEW/0.1"
MAX_CASES = 64


def existing_context(selector, task_id, reference):
    """Reuse canonical registry metadata; returned reference grants no execution."""
    view = capability_interop_review(selector)
    return compose_capability_review(selector, task_id=task_id,
        expected_view_sha256=view["view_sha256"], references=[reference])


def _q(f, unit, frame):
    return quantity(f.numerator, f.denominator, unit, frame, "fixture")


def _fraction(q):
    return Fraction(q["n"], q["d"])


def _case(c, unit, frame):
    require(type(c) is dict and set(c)=={"x","y"}, "case shape")
    for q in c.values():
        validate(q)
        require((q["unit"],q["frame"],q["scope"])==(unit,frame,"fixture"), "case boundary")
    return _fraction(c["x"]), _fraction(c["y"])


def discover(training, holdout):
    """Hypothesize an affine law from exact examples, check disjoint supplied cases.
    Neither holdout independence nor real-world truth is established by this function.
    """
    require(type(training) is list and type(holdout) is list and
            3<=len(training)<=MAX_CASES and 3<=len(holdout)<=MAX_CASES, "case bounds")
    require(type(training[0]) is dict and "x" in training[0],"first case")
    q=validate(training[0]["x"]); unit=q["unit"]; frame=q["frame"]
    train=[_case(c,unit,frame) for c in training]
    test=[_case(c,unit,frame) for c in holdout]
    keys=[x for x,y in train+test]
    require(len(set(keys))==len(keys),"repeated or leaked input")
    train.sort();test.sort()
    x0,y0=train[0];x1,y1=train[1]
    slope=(y1-y0)/(x1-x0);offset=y0-slope*x0
    require(all(slope*x+offset==y for x,y in train),"training contradiction")
    require(all(slope*x+offset==y for x,y in test),"holdout contradiction")
    # No extrapolation beyond tested range. Interior gaps are not a proof of validity.
    lo,hi=min(keys),max(keys)
    body={"schema":SCHEMA,"scope":"fixture","unit":unit,"frame":frame,
          "slope":_q(slope,"1",frame),"offset":_q(offset,unit,frame),
          "domain":[_q(lo,unit,frame),_q(hi,unit,frame)],
          "training":[{"x":_q(x,unit,frame),"y":_q(y,unit,frame)} for x,y in train],
          "holdout":[{"x":_q(x,unit,frame),"y":_q(y,unit,frame)} for x,y in test],
          "review_state":"supported_on_supplied_fixture_cases_only",
          "native_admitted":False,"execution_authorized":False}
    return {"method":body,"sha256":digest(body)}


def apply(envelope, expected_sha256, x, geometry, at, *, allowed, budget=243):
    require(type(envelope) is dict and set(envelope)=={"method","sha256"},"method envelope")
    body=envelope["method"]
    require(type(body) is dict and body.get("schema")==SCHEMA,"method schema")
    # Validate canonical content and independently recompute candidate from its bounded cases.
    rebuilt=discover(body["training"],body["holdout"])
    require(rebuilt==envelope and rebuilt["sha256"]==expected_sha256,"method revision")
    return _apply_verified(body,expected_sha256,x,geometry,at,allowed=allowed,budget=budget)


def _apply_verified(body, expected_sha256, x, geometry, at, *, allowed, budget):
    """Internal helper only: body must come from already verified private snapshot."""
    validate(x);require((x["unit"],x["frame"],x["scope"])==(body["unit"],body["frame"],"fixture"),"input boundary")
    lo,hi=map(_fraction,body["domain"]); require(lo<=_fraction(x)<=hi,"outside tested envelope")
    report=compose(geometry,{"x":{"at":at,"value":x},"slope":{"at":at,"value":body["slope"]},
        "offset":{"at":at,"value":body["offset"]}},
        [{"id":"scaled","at":at,"op":"mul","args":["x","slope"]},
         {"id":"result","at":at,"op":"add","args":["scaled","offset"]}],
        allowed=allowed,scope="fixture",budget=budget)
    result={"method_sha256":expected_sha256,"result":report["record"]["trace"][-1]["value"],
            "trace":report,"native_admitted":False,"execution_authorized":False}
    return {"record":result,"sha256":digest(result)}
