import numpy as np
import pandas as pd
import streamlit as st

from astropy import units as u
from astropy.time import Time
from poliastro.bodies import Earth, Sun
from poliastro.twobody import Orbit
from poliastro.iod import lambert

# -----------------------
# UI – network configuration
# -----------------------
st.set_page_config(page_title="Luke Relay Sandbox", layout="wide")
st.title("Luke Relay Sandbox – Inner Solar Supply Chain")

colL, colR = st.columns([2,1])

with colR:
    st.subheader("Node lattice")
    geo_toggle = st.checkbox("Enable Luke-II (GEO ring, 3 nodes @ 120°)", value=True)
    eml1_toggle = st.checkbox("Enable Luke-IV (EML-1 depot)", value=True)
    thrust_mN = st.slider("Low-thrust level (mN)", 0.0, 100.0, 20.0, 1.0)
    isp = st.slider("Isp (s)", 1000, 4000, 2000, 50)
    payload = st.number_input("Payload mass (kg)", 10.0, 50000.0, 1500.0, 50.0)
    prop_frac = st.slider("Initial propellant fraction", 0.0, 0.9, 0.4, 0.01)

    st.subheader("Windows & legs")
    use_lambert = st.checkbox("Use Lambert for GEO→EML-1 (approx)", value=True)
    add_neo_leg = st.checkbox("Add placeholder EML-1→NEO leg", value=False)
    timewarp = st.slider("Time warp (analysis horizon, days)", 10, 400, 120, 10)

with colL:
    st.subheader("Concept")
    st.markdown("""
    - **Three Luke-II nodes** (GEO) 120° apart keep a route open as targets align.
    - **Luke-IV at EML-1** receives/coasts/captures with minimal Δv using gravity assists when windows permit.
    - Slide **thrust (mN)** and **Isp** to trade time vs propellant.
    """)

# -----------------------
# Quick calculators
# -----------------------
g0 = 9.80665

def hohmann_dv(mu, r1, r2):
    # Instantaneous Hohmann approximation for circular-to-circular
    v1 = np.sqrt(mu/r1)
    v2 = np.sqrt(mu/r2)
    va = np.sqrt(mu*(2/r1 - 1/((r1+r2)/2)))
    vb = np.sqrt(mu*(2/r2 - 1/((r1+r2)/2)))
    dv1 = abs(va - v1)
    dv2 = abs(v2 - vb)
    tof = np.pi * np.sqrt(((r1+r2)/2)**3 / mu)
    return dv1, dv2, tof

def rocket_eq(dv, isp, m0):
    mr = np.exp(dv/(isp*g0))
    m1 = m0 / mr
    prop_used = m0 - m1
    return m1, prop_used

def low_thrust_time(dv, thrust_N, m_bar):
    # crude: t = dv * m / F
    if thrust_N <= 0: return np.inf
    return dv * m_bar / thrust_N

# Earth μ, radii
muE = Earth.k.to_value(u.km**3 / u.s**2)
Re  = Earth.R.to_value(u.km)
rLEO = Re + 400.0
rGEO = 42164.0

# -----------------------
# Leg 1: LEO -> GEO (Hohmann)
# -----------------------
dv1, dv2, tof1 = hohmann_dv(muE, rLEO, rGEO)
dv_LEO_to_GEO = dv1 + dv2  # km/s
tof1_days = (tof1*u.s).to(u.day).value

# -----------------------
# Leg 2: GEO -> EML-1 (approx Lambert)
# -----------------------
dv_GEO_to_EML1 = 1.8   # km/s nominal placeholder
tof2_days = 5.0
if use_lambert:
    # Approximate GEO and EML-1 co-ordinates in Earth-centered frame is involved.
    # Keep a fixed reference; replace later with Horizons states.
    dv_GEO_to_EML1 = 1.5
    tof2_days = 4.0

# -----------------------
# Leg 3: optional EML-1 -> NEO (placeholder)
# -----------------------
dv_EML1_to_NEO = 1.0   # km/s (window-dependent)
tof3_days = 60.0

# -----------------------
# Mass / Prop / Time accounting
# -----------------------
m0 = payload / (1 - prop_frac)
dv_total_kms = dv_LEO_to_GEO + (dv_GEO_to_EML1 if eml1_toggle else 0) + (dv_EML1_to_NEO if add_neo_leg else 0)
dv_total = dv_total_kms * 1000.0
m1, prop_used = rocket_eq(dv_total, isp, m0)
thrust_N = thrust_mN / 1000.0
t_low = low_thrust_time(dv_total, thrust_N, (m0+m1)/2.0)  # seconds

rows = []
rows.append(dict(Leg="LEO→GEO (Hohmann)", dV_km_s=round(dv_LEO_to_GEO,3), TOF_days=round(tof1_days,2)))
if eml1_toggle:
    rows.append(dict(Leg="GEO→EML-1", dV_km_s=round(dv_GEO_to_EML1,3), TOF_days=round(tof2_days,2)))
if add_neo_leg:
    rows.append(dict(Leg="EML-1→NEO", dV_km_s=round(dv_EML1_to_NEO,3), TOF_days=round(tof3_days,1)))

df = pd.DataFrame(rows)

colL.subheader("Leg summary")
colL.dataframe(df, use_container_width=True)

colR.subheader("Totals")
colR.metric("Total Δv", f"{dv_total_kms:.2f} km/s")
colR.metric("Chem prop used (rocket eq.)", f"{prop_used:.1f} kg")
if thrust_mN > 0:
    colR.metric("Low-thrust time (rough)", f"{(t_low/86400):.1f} days")
else:
    colR.write("Set thrust > 0 mN for low-thrust time.")

# -----------------------
# Throughput model (simple path min-capacity)
# -----------------------
def path_efficiency(geo_on, eml1_on):
    # window factor φ_ij: with 3 GEO nodes we increase availability
    base = 0.45
    if geo_on:
        base += 0.25  # coverage bump
    if eml1_on:
        base += 0.20  # depot capture / coasting alignment
    return min(base, 0.95)

phi = path_efficiency(geo_toggle, eml1_toggle)
rate_kg_day = (payload if m1 > payload else m1) * phi / (sum(df.TOF_days) if len(df)>0 else 1)
colL.subheader("Network throughput")
colL.write(f"Effective window factor φ ≈ **{phi:.2f}**; Approx. throughput **{rate_kg_day:.1f} kg/day**")

# Export CSV
st.download_button("Download leg table (CSV)", df.to_csv(index=False).encode(), "relay_legs.csv", "text/csv")
st.caption("Replace placeholders with JPL Trajectory Browser windows + HORIZONS states for realism.")
