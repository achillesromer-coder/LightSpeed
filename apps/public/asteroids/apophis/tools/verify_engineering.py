#!/usr/bin/env python3
"""Reproduce Apophis public engineering projection QA with Python 3 stdlib.

Run: python3 apps/public/asteroids/apophis/tools/verify_engineering.py
No network, no hidden credentials, no writes to source files.
"""
from __future__ import annotations
import json, math, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(name): return json.loads((ROOT/"data"/name).read_text(encoding="utf-8"))
def close(x,y,atol=0.,rtol=1.e-9):
    return math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,abs_tol=atol,rel_tol=rtol)
def check(cond,message):
    if not cond: raise AssertionError(message)
def main():
    e=read("ephemeris-2029-30s.json")
    o=read("object-public-contract.json")
    a=read("engineering-derived.json")
    check(e["object_id"]==o["object_id"]==a["object_id"]=="JPL:SBDB:99942","Object identity mismatch")
    check(len(e["samples"])==len(a["timeseries"])==21,"Expected 21 source samples")
    check(e["cadence_s"]==30 and e["frame"]=="Ecliptic J2000" and e["time_scale"]=="TDB","Time/frame contract")
    check(e["source_raw_sha256"]==a["source_roots"]["ephemeris_sha"],"Raw source hash mismatch")
    AU=e["units"]["au_km"]*1000.0
    G=a["constants"]["gravitational_constant_m3_kg_s2"]
    mu=a["constants"]["earth_mu_m3_s2"]
    R=o["master"]["mean_diameter_m"]/2
    volume=(4.0/3.0)*math.pi*R**3
    check(close(volume,o["proxy"]["classification_volume_m3"],atol=.01,rtol=0),"Workbook sphere volume inconsistent")
    check(close(volume,a["spherical_geometry"]["equivalent_volume_m3"],rtol=1e-14),"Derived sphere volume inconsistent")
    rho=2700
    M=volume*rho
    check(close(M,o["proxy"]["classification_mass_kg"],atol=1.,rtol=0),"Workbook mass proxy mismatch")
    sg=G*M/R**2
    tide_sweep=[]
    largest_residual=0.0
    for i,(s,t) in enumerate(zip(e["samples"],a["timeseries"])):
        d=s["range_au"]*AU
        x=[v*AU for v in s["position_au"]]
        v=[w*AU/86400 for w in s["velocity_au_day"]]
        dr=math.sqrt(sum(q*q for q in x))-d
        largest_residual=max(largest_residual,abs(dr))
        rv=sum(x[j]*v[j] for j in range(3))/d
        check(close(rv,s["range_rate_au_day"]*AU/86400,atol=1e-10,rtol=0),"Radial velocity at sample "+str(i))
        check(close(d/1000,t["range_km"],atol=1e-6,rtol=0),"Range at sample "+str(i))
        tide=2*mu*R/d**3
        check(close(tide,t["tidal_acceleration_per_half_span_m_s2"],rtol=1e-12),"Tidal gradient at sample "+str(i))
        check(close(tide/sg,t["tidal_to_spherical_self_gravity_at_2700"],rtol=1e-12),"Tidal ratio at sample "+str(i))
        tide_sweep.append(tide/sg)
        if i: check(close((s["jd_tdb"]-e["samples"][i-1]["jd_tdb"])*86400,30,atol=.001,rtol=0),"Cadence error "+str(i))
    check(largest_residual<1e-4,"Vector range residual > 0.1 mm")
    check(tide_sweep.index(max(tide_sweep))==12,"Peak sample not at expected index")
    for r in a["density_sweep"]:
        rho=r["bulk_density_kg_m3"]; m=volume*rho
        g=G*m/R**2; v=math.sqrt(2*G*m/R)
        check(close(m,r["sphere_mass_kg"],rtol=1e-12),"Sweep mass")
        check(close(g,r["sphere_surface_g_m_s2"],rtol=1e-12),"Sweep gravity")
        check(close(v,r["sphere_escape_speed_m_s"],rtol=1e-12),"Sweep escape")
        check(close(2*mu*R/((o["encounter"]["nominal_distance_au"]*AU)**3*g),r["tide_g_ratio_at_nominal_tca"],rtol=1e-12),"Sweep tide ratio")
    d=o["encounter"]["nominal_distance_au"]*AU
    vel=o["encounter"]["relative_speed_km_s"]*1000
    vi=math.sqrt(vel*vel-2*mu/d)/1000
    check(close(vi,a["nominal_encounter"]["v_infinity_two_body_km_s"],atol=1e-9,rtol=0),"Two-body invariant")
    check(abs(vi-a["nominal_encounter"]["source_v_infinity_km_s"])<1e-5,"Mismatch to SBDB v_inf")
    check(o["master"]["measured_bulk_density_kg_m3"] is None,"Measured density must remain unknown")
    check(o["shape"]["interior_observations"] is False,"Internal structure should remain unknown")
    print(json.dumps({"status":"PASS","samples":len(e["samples"]),"max_range_norm_residual_m":largest_residual,"sphere_volume_m3":volume,"mass_proxy_2700_kg":M,"self_g_2700_m_s2":sg,"max_tide_ratio_2700_percent":100*max(tide_sweep),"v_infinity_two_body_km_s":vi,"note":"Analytical parameter sensitivity only; no surface/failure/interior prediction."},indent=2))
if __name__=="__main__":
    try: main()
    except Exception as exc:
        print("FAIL:",str(exc),file=sys.stderr)
        sys.exit(1)
