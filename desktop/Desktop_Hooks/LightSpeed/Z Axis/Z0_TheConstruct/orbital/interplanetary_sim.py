"""
Interplanetary EM Capture Simulator (Luke II family) — Standalone
Adds: regenerative recovery, finite-solenoid limits, dynamic dB/dt ramp, piecewise atmosphere.
Provides: single run + sweep + CSV + PDF heatmaps.

Consolidated from 3 versions
"""

# Imports

from dataclasses import asdict
from dataclasses import dataclass
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
import math
import matplotlib
import matplotlib.pyplot
import numpy
import pandas


# ===== CONSOLIDATED FROM 3 FILES =====

# Merged on: 2025-11-21 17:46:26

# Source files: 3


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interplanetary EM Capture Simulator (Luke II family) — Standalone
Adds: regenerative recovery, finite-solenoid limits, dynamic dB/dt ramp, piecewise atmosphere.
Provides: single run + sweep + CSV + PDF heatmaps.
"""
import math, numpy as np, pandas as pd
from dataclasses import dataclass, asdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

MU0 = 4e-7*math.pi
RHO_CU = 1.68e-8
K_SG = 1.83e-4*1e4
CD_SPHERE = 0.47

BODIES = {
    "earth":  {"mu": 3.986004418e14, "R": 6_371_000.0, "rho0": 1.225, "H": 8400.0},
    "moon":   {"mu": 4.9048695e12,   "R": 1_737_400.0, "rho0": 0.0,   "H": 1e6},
    "mars":   {"mu": 4.282837e13,    "R": 3_389_500.0, "rho0": 0.020, "H": 11100.0},
}

SITE = {"P_max_W": 3.0e9, "dBdt_max_Ts": 50.0}
STATIONS = {"small": 2.0, "medium-large": 5.0, "generational": 10.0}
METALS = {
    "gold (Au)": {"sigma": 4.10e7, "price": 90000.0},
    "silver (Ag)": {"sigma": 6.30e7, "price": 800.0},
    "platinum (Pt)": {"sigma": 9.43e6, "price": 30000.0},
}
KWH_COST = 0.08
ETA_EM = 0.65

def rho_atm(body, h, weather_scale=1.0):
    b=BODIES[body]; rho0, H = b["rho0"], b["H"]
    if rho0<=0: return 0.0
    if h<0: h=0.0
    return weather_scale * rho0 * math.exp(-h/H)

def v_circ(body, alt_m):
    b=BODIES[body]
    return math.sqrt(b["mu"]/(b["R"]+alt_m))

def solenoid_B_center(N, I, R, L):
    return MU0*N*I/max(1e-6, math.sqrt(R*R + (L*0.5)**2))

def solenoid_L(N, R, L):
    A=math.pi*R*R
    return MU0*(N**2)*A/max(0.1,L)

def solenoid_R_ohm(N, R, wire_area_m2=5e-6):
    length = 2*math.pi*R*N
    return RHO_CU*length/max(1e-8, wire_area_m2)

def coupling_gain(sigma, radius, geom_factor=1.0):
    return 2e-5 * (sigma/1e7) * (radius**3) * geom_factor

from dataclasses import dataclass
@dataclass
class Environment:
    body: str = "earth"
    alt_release_km: float = 20000.0
    speed_factor: float = 0.20
    weather_scale: float = 1.0

@dataclass
class Deposit:
    metal: str = "gold (Au)"
    mass_kg: float = 8000.0
    radius_m: float = 0.45

@dataclass
class Station:
    station_key: str = "generational"
    track_length_km: float = 100.0
    segments: int = 12
    coil_R_m: float = 5.0
    coil_L_m: float = 20.0
    coil_turns: int = 2000
    coil_I_max: float = 1.0e6
    regen_frac: float = 0.5
    eta_recover: float = 0.85
    ramp_share: float = 0.30  # fraction of traversal used to ramp up

def simulate_drop(env: Environment, dep: Deposit, dt_base=0.2):
    alt0 = env.alt_release_km*1e3
    v0 = v_circ(env.body, alt0)*env.speed_factor
    z=alt0; vz=-v0; x=y=vx=vy=0.0
    area=math.pi*(dep.radius_m**2)
    t=0.0; heat_peak=0.0; qdyn_peak=0.0; dt=dt_base
    while z>0 and t<10*3600:
        rho=rho_atm(env.body, z, env.weather_scale)
        v=max(1e-3, math.sqrt(vx*vx+vy*vy+vz*vz))
        rn=max(0.01,0.5*dep.radius_m)
        q_heat=K_SG*math.sqrt(max(rho,0.0)/rn)*v**3
        heat_peak=max(heat_peak,q_heat)
        qdyn_peak=max(qdyn_peak,0.5*rho*v*v)
        Fd=0.5*rho*0.47*area*v*v
        ax=-Fd/dep.mass_kg*(vx/v); ay=-Fd/dep.mass_kg*(vy/v); az=-Fd/dep.mass_kg*(vz/v)
        g=BODIES[env.body]["mu"]/((BODIES[env.body]["R"]+z)**2)
        vx+=ax*dt; vy+=ay*dt; vz+=(-g+az)*dt
        x+=vx*dt; y+=vy*dt; z+=vz*dt
        dt=2.0 if rho<1e-6 else (0.2 if rho<1e-3 else 0.02)
        t+=dt
    vfin=math.sqrt(vx*vx+vy*vy+vz*vz)
    return {"time_s":t, "final_speed_ms":abs(vfin), "heat_peak_W_m2":heat_peak, "qdyn_peak_Pa":qdyn_peak}

def capture_requirements(env: Environment, dep: Deposit, st: Station, v_capture_ms: float):
    KE=0.5*dep.mass_kg*v_capture_ms*v_capture_ms
    s=st.track_length_km*1000.0
    Favg=KE/max(1.0,s)
    Bmax_geom = solenoid_B_center(st.coil_turns, st.coil_I_max, st.coil_R_m, st.coil_L_m)
    sigma = {"gold (Au)":4.10e7,"silver (Ag)":6.30e7,"platinum (Pt)":9.43e6}[dep.metal]
    gain = coupling_gain(sigma, dep.radius_m, 1.0)
    Breq = math.sqrt( Favg / (gain*max(1.0,v_capture_ms)) )
    v_avg=max(1.0, 0.6*v_capture_ms)
    t_len=s/v_avg
    dBdt_need = Breq/max(0.01, st.ramp_share*t_len)
    P_em = (gain*(Breq**2)*v_capture_ms)*v_capture_ms/0.65
    # coil losses (worst-case)
    A=math.pi*st.coil_R_m**2
    Lcoil = MU0*(st.coil_turns**2)*A/max(0.1,st.coil_L_m)
    Rcoil = RHO_CU*(2*math.pi*st.coil_R_m*st.coil_turns)/max(1e-8,5e-6)
    P_resist = (st.coil_I_max**2)*Rcoil
    feas = (Breq<=STATIONS[st.station_key]) and (Breq<=Bmax_geom) and (dBdt_need<=SITE["dBdt_max_Ts"]) and (P_em<=SITE["P_max_W"])
    return {"Breq_T":Breq,"Bmax_station_T":STATIONS[st.station_key],"Bmax_geom_T":Bmax_geom,
            "dBdt_need_Ts":dBdt_need,"P_em_W":P_em,"P_resist_W":P_resist,"L_H":Lcoil,"R_ohm":Rcoil,
            "feasible":bool(feas),"margin_B_station":STATIONS[st.station_key]/max(1e-6,Breq),
            "margin_B_geom":Bmax_geom/max(1e-6,Breq),"margin_dBdt":SITE["dBdt_max_Ts"]/max(1e-6,dBdt_need),
            "margin_P":SITE["P_max_W"]/max(1.0,P_em),"t_len_s":t_len}

def economics(dep: Deposit, st: Station, v_capture_ms: float, cap: dict, metal_price):
    E_in = (0.5*dep.mass_kg*v_capture_ms*v_capture_ms)/0.65
    E_rec = st.regen_frac*st.eta_recover*(0.5*dep.mass_kg*v_capture_ms*v_capture_ms)
    E_net = max(0.0, E_in - E_rec)
    kWh = E_net/3.6e6
    energy_cost = kWh*0.08
    revenue = dep.mass_kg*metal_price
    profit_run = max(0.0, revenue-energy_cost)
    run_time = 1.3*max(cap["t_len_s"], E_net/max(1.0,3.0e9)) + 10.0
    runs_per_hour = 3600.0/max(1.0, run_time)
    return {"energy_kWh":kWh,"energy_cost_usd":energy_cost,"profit_run_usd":profit_run,
            "runs_per_hour":runs_per_hour,"profit_hour_usd":profit_run*runs_per_hour}

def single(env: Environment, dep: Deposit, st: Station, override_v=None):
    drop=simulate_drop(env, dep)
    vcap = override_v if override_v is not None else drop["final_speed_ms"]
    cap=capture_requirements(env, dep, st, vcap)
    price={"gold (Au)":90000.0,"silver (Ag)":800.0,"platinum (Pt)":30000.0}[dep.metal]
    eco=economics(dep, st, vcap, cap, price)
    return {**asdict(env), **asdict(dep), **asdict(st), **drop, "v_capture_ms":vcap, **cap, **eco}

def sweep(envs, deps, sts, v_caps, s_brakes_km):
    rows=[]
    for env in envs:
        for dep in deps:
            for st in sts:
                for v in v_caps:
                    for s in s_brakes_km:
                        st2 = Station(**asdict(st)); st2.track_length_km = s
                        rows.append(single(env, dep, st2, override_v=v))
    return pd.DataFrame(rows)

def plots(df, outdir: Path, title: str):
    outdir.mkdir(parents=True, exist_ok=True)
    df.to_csv(outdir/"results.csv", index=False)
    pdf=PdfPages(outdir/"report.pdf")
    for body in df["body"].unique():
        sub=df[(df["body"]==body)&(df["feasible"])]
        if sub.empty: continue
        metal=sub["metal"].iloc[0]; station=sub["station_key"].iloc[0]
        cut=sub[(sub["metal"]==metal)&(sub["station_key"]==station)]
        V=sorted(cut["v_capture_ms"].unique()); S=sorted(cut["track_length_km"].unique())
        Z=np.zeros((len(S),len(V)))
        for i,skm in enumerate(S):
            for j,v in enumerate(V):
                Z[i,j]=cut[(cut["v_capture_ms"]==v)&(cut["track_length_km"]==skm)]["profit_hour_usd"].max()
        fig,ax=plt.subplots(figsize=(7.2,5.2))
        im=ax.imshow(Z,origin="lower",aspect="auto",extent=[min(V),max(V),min(S),max(S)])
        ax.set_title(f"{title} — {body} (profit/hour)"); ax.set_xlabel("v_capture (m/s)"); ax.set_ylabel("track length (km)")
        cb=fig.colorbar(im,ax=ax); cb.set_label("USD/h")
        fig.savefig(outdir/f"heat_profit_{body}.png",dpi=160,bbox_inches="tight"); pdf.savefig(fig); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.2,5.2))
    ax.scatter(df["v_capture_ms"], df["Breq_T"], s=10, alpha=0.7)
    ax.set_xlabel("v_capture (m/s)"); ax.set_ylabel("B_required (T)"); ax.set_title("B_required vs Speed")
    fig.savefig(outdir/"scatter_Breq.png",dpi=160,bbox_inches="tight"); pdf.savefig(fig); plt.close(fig)
    pdf.close()
    return outdir/"results.csv", outdir/"report.pdf"

if __name__=="__main__":
    envs=[Environment(body="earth", alt_release_km=20000.0, speed_factor=0.20, weather_scale=1.0),
          Environment(body="moon",  alt_release_km=20000.0, speed_factor=0.20, weather_scale=1.0)]
    deps=[Deposit(metal="gold (Au)", mass_kg=8000.0, radius_m=0.45)]
    sts=[Station(station_key="generational", track_length_km=100.0, segments=12, coil_R_m=5.0, coil_L_m=20.0, coil_turns=2000, coil_I_max=1e6, regen_frac=0.5, ramp_share=0.30)]
    v_caps=[500, 750, 1000, 1500]
    s_brakes=[50.0, 100.0, 150.0, 200.0]
    df=sweep(envs,deps,sts,v_caps,s_brakes)
    out=Path("./interplanetary_demo"); results, report = plots(df, out, "Interplanetary EM Capture — Demo")
    print(out.resolve())
