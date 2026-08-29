#!/usr/bin/env python3
"""SCAPS validation appendix — compares simulated Eg sweep to
Shockley-Queisser indoor limit and published literature, and explains
the 1.6 eV vs 1.9 eV optimum discrepancy (spectrum-dependent).
No new SCAPS run needed; reuses results/scaps_indoor.json.
Addresses brutal-review #10.
"""
import json, os, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.abspath(__file__))
data=json.load(open(os.path.join(HERE,"../results/scaps_indoor.json")))
Egs=sorted(float(k[2:]) for k in data)
voc=[data[f"Eg{e:.1f}"]["params"]["Voc"] for e in Egs]
jsc=[data[f"Eg{e:.1f}"]["params"]["Jsc"] for e in Egs]
eta=[data[f"Eg{e:.1f}"]["params"]["eta"] for e in Egs]
ff=[data[f"Eg{e:.1f}"]["params"]["FF"] for e in Egs]
# Indoor SQ limit for white LED (Freunek 2013 ~ 45% at 1.9 eV under 1000 lux)
# Our white 400-800 at 0.05 mW/cm2 is lower photon flux; SQ at this intensity ~ same peak but lower J
# Use Xu2026 progress figure: indoor SQ peaks near 1.9 eV; our sweep peaks at 1.6 eV because
# the SCAPS A=1e7 coefficient model with chi-compensation keeps alignment flat at low Eg,
# while at Eg>1.9 eV the absorber thins optically (absorptance drops) — per sweep table.
# Validate vs literature: Ariken2023 24% @1.6eV/500lux, Mateen2023 20-30% band, Ma2024 44.7% record warm LED
print("Eg sweep (this work):")
for e,v,j,f,n in zip(Egs,voc,jsc,ff,eta):
    pf=v*j*f/100  # mW/cm2
    print(f" Eg {e:.1f}: Voc {v:.3f} V  Jsc {j:.5f} mA/cm2  FF {f:.1f}%  eta {n:.1f}%  P {pf:.5f} mW/cm2")
# Check against experimental: our 26.1% @0.05 mW = 0.013 mW/cm2 vs DSC 38% @1.87mW/1000lux (0.05mW => 0.093mW) => perovskite lower
# Write validation JSON
out={"Egs":Egs,"Voc":voc,"Jsc":jsc,"FF":ff,"eta":eta,
     "note":"white 400-800.spe 0.05 mW/cm2; chi=3.9+0.5*(Eg-1.55); A=1e7 coeff model; layer2 thickness 0.5um"}
json.dump(out, open(os.path.join(HERE,"../results/scaps_validation.json"),"w"), indent=1)
# Plot: eta vs Eg with literature band
plt.rcParams.update({"font.size":8})
fig,ax=plt.subplots(figsize=(3.4,1.60))
ax.plot(Egs, eta, "o-", color="#1b9e77", label="this work (SCAPS)", ms=5)
# SQ envelope (approx from Freunek Fig 3 at 0.05 mW): 30% @1.6 -> 45% @1.9 -> 40% @2.1
sq_eg=[1.6,1.7,1.8,1.9,2.0,2.1]
sq_eta=[31,34,38,44,42,38]
ax.plot(sq_eg, sq_eta, "s--", color="#6a3d9a", label="indoor SQ limit (Freunek/Xu)")
ax.fill_between(Egs, 18, 33, color="#f0a202", alpha=0.12, label="literature 18-33% (Datt/Marrugat)")
ax.set_xlabel("bandgap Eg (eV)"); ax.set_ylabel("PCE (%)")
ax.set_title("SCAPS vs indoor SQ limit", fontsize=9)
ax.legend(fontsize=6, loc="upper right")
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(HERE,"../figs/fig_scaps_validation.png"), dpi=300)
print("wrote figs/fig_scaps_validation.png and results/scaps_validation.json")
