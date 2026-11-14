from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.cgx_cross_analysis import source_hybridisation_candidates, CGXCrossAnalysisError

def test_duplicates_and_variants_preserve_occurrences():
    x=b"def f(x): return x+1"
    y=b"# wrapper\ndef f(x): return x+1"
    z=b"def f(x): return x-1"
    sources={"raphael":x,"ls":x,"wrapper":y,"variant":z}
    r=source_hybridisation_candidates(sources)
    assert r==source_hybridisation_candidates(dict(reversed(list(sources.items()))))
    assert r["distinct_payload_count"]==3
    assert r["exact_payload_groups"][0]["occurrences"]==["ls","raphael"]
    assert len(r["function_candidates"][0]["syntax_variants"])==2
    assert not r["semantic_equivalence_proven"] and not r["native_admitted"]

def test_context_and_duplicate_definitions_not_discarded():
    r=source_hybridisation_candidates({"a":b"v=1\ndef f(): return v\ndef f(): return v","b":b"v=2\ndef f(): return v"})
    c=r["function_candidates"][0]
    assert len(c["syntax_variants"][0]["occurrences"])==3
    assert "dependency_binding" in c["requires"]
    assert not r["execution_performed"]

def test_invalid_source_and_budget():
    r=source_hybridisation_candidates({"invalid":b"def :","never_run":b"raise RuntimeError('must not execute')"})
    assert r["unparsed_sources"]==["invalid"]
    with pytest.raises(CGXCrossAnalysisError): source_hybridisation_candidates({"a":b"x"*(5*1024*1024+1)})
    with pytest.raises(CGXCrossAnalysisError): source_hybridisation_candidates({"a":"not bytes"})
