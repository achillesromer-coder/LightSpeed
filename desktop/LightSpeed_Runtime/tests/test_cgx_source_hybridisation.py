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



# Freeze the exact previously inspected legacy function, not the whole module.
# Only that function is executed; the wrapper and its GUI/main code never run.
LEGACY_KERNEL = """def mandelbrot_set(width, height, zoom, max_iter):
    \"\"\"
    Generates a Mandelbrot fractal set for a 2D projection.
    \"\"\"
    x = np.linspace(-2.0, 2.0, width) / zoom
    y = np.linspace(-2.0, 2.0, height) / zoom
    fractal = np.zeros((width, height))
    for i, x_val in enumerate(x):
        for j, y_val in enumerate(y):
            z = 0
            c = complex(x_val, y_val)
            for k in range(max_iter):
                if abs(z) > 2.0:
                    fractal[i, j] = k
                    break
                z = z * z + c
    return fractal
"""


def checked_legacy_kernel(raw):
    import ast
    import numpy as np
    assert len(raw) <= 256 * 1024
    tree = ast.parse(raw)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name == "mandelbrot_set"]
    # A subsequent assignment/import could shadow a function in a real module.
    # This checks only the extracted body with explicit dependencies.
    assert len(nodes) == 1
    assert ast.dump(nodes[0], include_attributes=False) == ast.dump(
        ast.parse(LEGACY_KERNEL).body[0], include_attributes=False)
    env = {"np": np, "__builtins__": {"enumerate": enumerate, "range": range,
                                       "abs": abs, "complex": complex}}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<reviewed-kernel>", "exec"), env)
    return env["mandelbrot_set"]


CASES = [(1,1,1.0,1), (3,3,1.0,8), (5,7,.5,16), (17,11,1.7,32),
         (32,25,4.0,64), (9,13,.125,3)]


def test_actual_legacy_kernel_reuse():
    import numpy as np
    from lightspeed_runtime.cgx_cross_analysis import mandelbrot_grid_candidate
    repo = Path(__file__).resolve().parents[3]
    axis = repo / "desktop/Desktop_Hooks/LightSpeed/Z Axis"
    paths = [axis/"Z-4_Merovingian/core/physics/raphael/fractal_expansion.py",
             axis/"Z0_TheConstruct/cosmological/fractal_expansion.py"]
    for path in paths:
        legacy = checked_legacy_kernel(path.read_bytes())
        for case in CASES:
            result = mandelbrot_grid_candidate(*case)
            assert np.array_equal(result["grid"], legacy(*case))
            assert not result["native_admitted"]


def test_shared_grid_independent_known_points_and_negative_cases():
    from lightspeed_runtime.cgx_cross_analysis import mandelbrot_grid_candidate
    assert mandelbrot_grid_candidate(3,3,1,8)["grid"] == [[1,0,1],[2,0,2],[1,2,1]]
    assert mandelbrot_grid_candidate(3,3,1,1)["grid"] == [[0,0,0]]*3
    for case in [(0,3,1,8),(True,3,1,8),(3,3,0,8),(3,3,float("nan"),8),
                 (3,3,float("inf"),8),(128,128,1,256),(3,3,1,257)]:
        with pytest.raises(CGXCrossAnalysisError):
            mandelbrot_grid_candidate(*case)
    with pytest.raises(AssertionError):
        checked_legacy_kernel(LEGACY_KERNEL.replace("z = 0", "z = 1").encode())
