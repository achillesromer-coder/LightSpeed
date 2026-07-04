"""
Luke — Master Sweeps
- Interplanetary A→B captures using ground/tether station (Earth/Moon/Mars)
- Luke II → Luke II toroidal hand-off (SLOW→GLIDE→SEND)
Outputs CSVs + a consolidated PDF report.

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
Luke — Master Sweeps
- Interplanetary A→B captures using ground/tether station (Earth/Moon/Mars)
- Luke II → Luke II toroidal hand-off (SLOW→GLIDE→SEND)
Outputs CSVs + a consolidated PDF report.
"""
import math, numpy as np, pandas as pd
from dataclasses import dataclass, asdict
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# ---- Constants and simple physical models (surrogate; fast) ----
MU0 = 4e-7*math.pi
RHO_CU = 1.68e-8
K_SG = 1.83e-4*1e4
CD_SPHERE = 0.47
ETA_EM = 0.65
SITE = {"P_max_W": 3.0e9, "dBdt_max_Ts": 50.0}
KWH_COST = 0.08

BODIES = {
    "earth":  {"mu": 3.986004418e14, "R": 6_371_000.0, "rho0": 1.225, "H": 8400.0},
    "moon":   {"mu": 4.9048695e12,   "R": 1_737_400.0, "rho0": 0.0,   "H": 1e6},
    "mars":   {"mu": 4.282837e13,    "R": 3_389_500.0, "rho0": 0.020, "H": 11100.0},
}
STATIONS = {"small": 2.0, "medium-large": 5.0, "generational": 10.0}
METALS = {
    "gold (Au)": {"sigma": 4.10e7, "price": 90000.0},
    "silver (Ag)": {"sigma": 6.30e7, "price": 800.0},
    "platinum (Pt)": {"sigma": 9.43e6, "price": 30000.0},
}

# ---- Helpers ----
def rho_atm(body, h, weather_scale=1.0):
    b=BODIES[body]; rho0,H=b["rho0"],b["H"]
    if rho0<=0: return 0.0
    if h<0: h=0.0
    return weather_scale*rho0*math.exp(-h/H)

def v_circ(body, alt_m):
    b=BODIES[body]
    return math.sqrt(b["mu"]/(b["R"]+alt_m))

def coupling_gain(sigma, radius, geom_factor=1.0):
    # Eddy-current surrogate scaling
    return 2e-5*(sigma/1e7)*(radius**3)*geom_factor

def solenoid_B_center(N, I, R, L):
    return MU0*N*I/max(1e-6, math.sqrt(R*R + (L*0.5)**2))

def solenoid_L(N, R, L):
    A=math.pi*R*R
    return MU0*(N**2)*A/max(0.1,L)

def solenoid_R_ohm(N, R, wire_area_m2=5e-6):
    length=2*math.pi*R*N
    return RHO_CU*length/max(1e-8,wire_area_m2)

# ---- Data classes ----
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
    ramp_share: float = 0.30

@dataclass
class Toroid:
    major_R_m: float = 12.0
    minor_a_m: float = 2.0
    sectors: int = 16
    turns: int = 2500
    I_max: float = 1.0e6
    B_cap_T: float = 5.0
    ramp_share: float = 0.30
    regen_frac: float = 0.5
    eta_recover: float = 0.85

# ---- Atmospheric drop to surface approach speed ----
def simulate_drop(env: Environment, dep: Deposit, dt_base=0.2):
    alt0=env.alt_release_km*1e3
    v0=v_circ(env.body, alt0)*env.speed_factor
    z=alt0; vz=-v0; vx=vy=0.0
    area=math.pi*(dep.radius_m**2)
    t=0.0; heat_peak=0.0; qdyn_peak=0.0; dt=dt_base
    while z>0 and t<10*3600:
        rho=rho_atm(env.body, z, env.weather_scale)
        v=max(1e-3, math.sqrt(vx*vx+vy*vy+vz*vz))
        rn=max(0.01,0.5*dep.radius_m)
        q_heat=K_SG*math.sqrt(max(rho,0.0)/rn)*v**3
        heat_peak=max(heat_peak,q_heat); qdyn_peak=max(qdyn_peak,0.5*rho*v*v)
        Fd=0.5*rho*CD_SPHERE*area*v*v
        ax=-Fd/dep.mass_kg*(vx/v); ay=-Fd/dep.mass_kg*(vy/v); az=-Fd/dep.mass_kg*(vz/v)
        g=BODIES[env.body]["mu"]/((BODIES[env.body]["R"]+z)**2)
        vx+=ax*dt; vy+=ay*dt; vz+=(-g+az)*dt
        z+=vz*dt; t+=dt
        dt=2.0 if rho<1e-6 else (0.2 if rho<1e-3 else 0.02)
    vfin=math.sqrt(vx*vx+vy*vy+vz*vz)
    return {"time_s":t,"final_speed_ms":abs(vfin),"heat_peak_W_m2":heat_peak,"qdyn_peak_Pa":qdyn_peak}

# ---- Ground/tether capture requirements (A→B legs) ----
def capture_requirements(env: Environment, dep: Deposit, st: Station, v_capture_ms: float):
    KE=0.5*dep.mass_kg*v_capture_ms*v_capture_ms
    s=st.track_length_km*1000.0
    Favg=KE/max(1.0,s)
    Bmax_geom = solenoid_B_center(st.coil_turns, st.coil_I_max, st.coil_R_m, st.coil_L_m)
    sigma = METALS[dep.metal]["sigma"]
    gain = coupling_gain(sigma, dep.radius_m, 1.0)
    Breq = math.sqrt( Favg / (gain*max(1.0,v_capture_ms)) )
    v_avg=max(1.0, 0.6*v_capture_ms)
    t_len=s/v_avg
    dBdt_need = Breq/max(0.01, st.ramp_share*t_len)
    P_em = (gain*(Breq**2)*v_capture_ms)*v_capture_ms/ETA_EM
    Lcoil = solenoid_L(st.coil_turns, st.coil_R_m, st.coil_L_m)
    Rcoil = solenoid_R_ohm(st.coil_turns, st.coil_R_m)
    P_resist = (st.coil_I_max**2)*Rcoil
    feas = (Breq<=STATIONS[st.station_key]) and (Breq<=Bmax_geom) and (dBdt_need<=SITE["dBdt_max_Ts"]) and (P_em<=SITE["P_max_W"])
    return {"Breq_T":Breq,"Bmax_station_T":STATIONS[st.station_key],"Bmax_geom_T":Bmax_geom,
            "dBdt_need_Ts":dBdt_need,"P_em_W":P_em,"P_resist_W":P_resist,"L_H":Lcoil,"R_ohm":Rcoil,
            "feasible":bool(feas),"margin_B_station":STATIONS[st.station_key]/max(1e-6,Breq),
            "margin_B_geom":Bmax_geom/max(1e-6,Breq),"margin_dBdt":SITE["dBdt_max_Ts"]/max(1e-6,dBdt_need),
            "margin_P":SITE["P_max_W"]/max(1.0,P_em),"t_len_s":t_len}

def economics(dep: Deposit, st: Station, v_capture_ms: float, cap: dict):
    E_in=(0.5*dep.mass_kg*v_capture_ms*v_capture_ms)/ETA_EM
    E_rec=st.regen_frac*st.eta_recover*(0.5*dep.mass_kg*v_capture_ms*v_capture_ms)
    E_net=max(0.0,E_in-E_rec)
    kWh=E_net/3.6e6; energy_cost=kWh*KWH_COST
    revenue=dep.mass_kg*METALS[dep.metal]["price"]
    profit_run=max(0.0,revenue-energy_cost)
    run_time=1.3*max(cap["t_len_s"], E_net/max(1.0,SITE["P_max_W"])) + 10.0
    runs_per_hour=3600.0/max(1.0,run_time)
    return {"energy_kWh":kWh,"energy_cost_usd":energy_cost,"profit_run_usd":profit_run,
            "runs_per_hour":runs_per_hour,"profit_hour_usd":profit_run*runs_per_hour}

def single_AB(env: Environment, dep: Deposit, st: Station, override_v=None, leg_name=""):
    drop=simulate_drop(env, dep)
    vcap=override_v if override_v is not None else drop["final_speed_ms"]
    cap=capture_requirements(env, dep, st, vcap)
    eco=economics(dep, st, vcap, cap)
    return {"leg":leg_name or env.body+"_surface", **asdict(env), **asdict(dep), **asdict(st),
            **drop, "v_capture_ms":vcap, **cap, **eco}

# ---- Luke II toroidal hand-off ----
@dataclass
class ToroidEnv:
    # for compatibility naming
    body: str = "earth"
    alt_release_km: float = 20000.0
    speed_factor: float = 0.20
    weather_scale: float = 1.0

def toroid_pass_requirements(dep: Deposit, tor: "Toroid", v_in_ms: float, v_out_ms: float):
    s = 2.0*tor.minor_a_m
    KE_diff = 0.5*dep.mass_kg*(v_in_ms*v_in_ms - v_out_ms*v_out_ms)
    Favg = KE_diff/max(1e-3, s)
    sigma = METALS[dep.metal]["sigma"]
    gain = coupling_gain(sigma, dep.radius_m, 1.0)
    Breq = math.sqrt(abs(Favg)/max(1e-6, gain*max(v_in_ms,1.0)))
    t = s/max(1.0, 0.5*(v_in_ms+v_out_ms))
    dBdt_need = Breq/max(0.01, tor.ramp_share*t)
    Bgeom = MU0*tor.turns*tor.I_max/max(1e-3, tor.minor_a_m)
    feasible=(Breq<=min(Bgeom, tor.B_cap_T)) and (dBdt_need<=SITE["dBdt_max_Ts"])
    return {"Breq_T":Breq,"Bgeom_T":Bgeom,"Bcap_T":tor.B_cap_T,"dBdt_need_Ts":dBdt_need,
            "path_m":s,"t_cross_s":t,"Favg_N":Favg,"feasible":bool(feasible)}

def toroid_energy(dep: Deposit, tor: "Toroid", v_in_ms: float, v_out_ms: float):
    E_in=(0.5*dep.mass_kg*v_in_ms*v_in_ms - 0.5*dep.mass_kg*v_out_ms*v_out_ms)/ETA_EM
    E_rec=tor.regen_frac*tor.eta_recover*max(0.0, 0.5*dep.mass_kg*(v_in_ms*v_in_ms - v_out_ms*v_out_ms))
    Enet=max(0.0, E_in - E_rec)
    return {"E_in_J":E_in,"E_rec_J":E_rec,"E_net_J":Enet}

def single_L2L2(env: ToroidEnv, dep: Deposit, tor: Toroid, v_in_ms: float, v_out_ms: float):
    req=toroid_pass_requirements(dep, tor, v_in_ms, v_out_ms)
    energy=toroid_energy(dep, tor, v_in_ms, v_out_ms)
    clearance_ok=(dep.radius_m*1.05) <= (0.8*tor.minor_a_m)
    return {"leg":"luke2_to_luke2", **asdict(env), **asdict(dep), **asdict(tor),
            "v_in_ms":v_in_ms, "v_out_ms":v_out_ms, **req, **energy, "clearance_ok":bool(clearance_ok)}

# ---- Sweep runners ----
def run_interplanetary_AB():
    envs=[]
    # Earth ground capture with weather range
    for ws in [0.8, 1.0, 1.2]:
        envs.append(Environment(body="earth", alt_release_km=20000.0, speed_factor=0.20, weather_scale=ws))
    # Moon/Mars (no weather on Moon)
    envs.append(Environment(body="moon", alt_release_km=20000.0, speed_factor=0.20, weather_scale=1.0))
    for ws in [0.8, 1.0, 1.4]:
        envs.append(Environment(body="mars", alt_release_km=20000.0, speed_factor=0.20, weather_scale=ws))

    deps=[Deposit(metal="gold (Au)", mass_kg=8000.0, radius_m=0.45)]
    sts=[Station(station_key="generational", track_length_km=50.0, segments=12, coil_R_m=5.0, coil_L_m=20.0, coil_turns=2000, coil_I_max=1e6, regen_frac=0.5, ramp_share=0.30)]
    v_caps=[500, 750, 1000, 1500, 2000]
    s_brakes=[50.0, 100.0, 150.0, 200.0]
    rows=[]
    for env in envs:
        for dep in deps:
            for st in sts:
                for v in v_caps:
                    for s in s_brakes:
                        st2=Station(**asdict(st)); st2.track_length_km=s
                        rows.append(single_AB(env, dep, st2, override_v=v, leg_name=env.body+"_surface"))
    return pd.DataFrame(rows)

def run_luke2_to_luke2():
    env=ToroidEnv(body="earth", alt_release_km=20000.0, speed_factor=0.20, weather_scale=1.0)
    deps=[Deposit(metal="gold (Au)", mass_kg=8000.0, radius_m=0.45)]
    tors=[Toroid(major_R_m=12.0, minor_a_m=2.0, sectors=16, turns=2500, I_max=1e6, B_cap_T=5.0, ramp_share=0.30)]
    v_in=[300, 500, 750, 1000, 1500]
    v_out=[0, 150, 300, 600, 900]
    rows=[]
    for dep in deps:
        for tor in tors:
            for vin in v_in:
                for vout in v_out:
                    rows.append(single_L2L2(env, dep, tor, vin, vout))
    return pd.DataFrame(rows)

# ---- Reporting ----
def report_all(df_ab: pd.DataFrame, df_l2l2: pd.DataFrame, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    csv_ab = outdir/"interplanetary_AB_master.csv"; df_ab.to_csv(csv_ab, index=False)
    csv_l2 = outdir/"luke2_to_luke2_gold_master.csv"; df_l2l2.to_csv(csv_l2, index=False)

    pdf = PdfPages(outdir/"master_report.pdf")

    # AB: profit/hour heatmaps by body
    for body in df_ab["body"].unique():
        sub=df_ab[(df_ab["body"]==body)&(df_ab["feasible"])]
        if sub.empty: continue
        V=sorted(sub["v_capture_ms"].unique()); S=sorted(sub["track_length_km"].unique())
        Z=np.zeros((len(S),len(V)))
        for i,skm in enumerate(S):
            for j,v in enumerate(V):
                Z[i,j]=sub[(sub["v_capture_ms"]==v)&(sub["track_length_km"]==skm)]["profit_hour_usd"].max()
        fig,ax=plt.subplots(figsize=(7.2,5.2))
        im=ax.imshow(Z,origin="lower",aspect="auto",extent=[min(V),max(V),min(S),max(S)])
        ax.set_title(f"AB profit/hour — {body}"); ax.set_xlabel("v_capture (m/s)"); ax.set_ylabel("track length (km)")
        fig.colorbar(im,ax=ax).set_label("USD/h")
        fig.savefig(outdir/f"ab_heat_{body}.png",dpi=160,bbox_inches="tight"); pdf.savefig(fig); plt.close(fig)

    # AB: feasibility envelope Breq vs speed
    fig,ax=plt.subplots(figsize=(7.2,5.2))
    ax.scatter(df_ab["v_capture_ms"], df_ab["Breq_T"], s=10, alpha=0.7)
    ax.set_xlabel("v_capture (m/s)"); ax.set_ylabel("B_required (T)"); ax.set_title("AB: B_required vs Speed")
    fig.savefig(outdir/"ab_scatter_Breq.png",dpi=160,bbox_inches="tight"); pdf.savefig(fig); plt.close(fig)

    # L2L2: Breq vs (v_in, v_out) heatmap
    sub=df_l2l2[df_l2l2["feasible"]]
    if not sub.empty:
        VIN=sorted(sub["v_in_ms"].unique()); VOUT=sorted(sub["v_out_ms"].unique())
        Z=np.zeros((len(VOUT),len(VIN)))
        for i,vo in enumerate(VOUT):
            for j,vi in enumerate(VIN):
                Z[i,j]=sub[(sub["v_in_ms"]==vi)&(sub["v_out_ms"]==vo)]["Breq_T"].min()
        fig,ax=plt.subplots(figsize=(7.2,5.2))
        im=ax.imshow(Z,origin="lower",aspect="auto",extent=[min(VIN),max(VIN),min(VOUT),max(VOUT)])
        ax.set_title("Luke II→Luke II: B_required"); ax.set_xlabel("v_in (m/s)"); ax.set_ylabel("v_out (m/s)")
        fig.colorbar(im,ax=ax).set_label("T")
        fig.savefig(outdir/"l2l2_heat_Breq.png",dpi=160,bbox_inches="tight"); pdf.savefig(fig); plt.close(fig)

    # L2L2: feasibility cloud
    fig,ax=plt.subplots(figsize=(7.2,5.2))
    ax.scatter(df_l2l2["Bgeom_T"], df_l2l2["Breq_T"], s=10, alpha=0.8)
    ax.set_xlabel("Geom B max (T)"); ax.set_ylabel("B_required (T)"); ax.set_title("L2L2: Feasibility cloud")
    fig.savefig(outdir/"l2l2_scatter_feas.png",dpi=160,bbox_inches="tight"); pdf.savefig(fig); plt.close(fig)

    pdf.close()
    return csv_ab, csv_l2, outdir/"master_report.pdf"

if __name__=="__main__":
    df_ab = run_interplanetary_AB()
    df_l2l2 = run_luke2_to_luke2()
    out = Path("./master_sweeps")
    csv_ab, csv_l2, pdf = report_all(df_ab, df_l2l2, out)
    print(out.resolve())
