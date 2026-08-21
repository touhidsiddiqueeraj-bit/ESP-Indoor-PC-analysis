#!/usr/bin/env python3
"""Indoor-illumination device sweep: JV curves + bandgap metrics (white 400-800 nm, 0.05 mW/cm^2)."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "figs", "fig_scaps_indoor.png"))
os.makedirs(os.path.dirname(OUT), exist_ok=True)

data = json.load(open(os.path.join(HERE, "..", "results", "scaps_indoor.json")))
Egs = sorted((float(k[2:]) for k in data))

fig, axs = plt.subplots(1, 2, figsize=(6.8, 3.0))
a = axs[0]
for k in sorted(data):
    d = data[k]
    if not d.get("V"):
        continue
    Eg = float(k[2:])
    a.plot(d["V"], d["J"], lw=1.2, label=f"$E_g$={Eg:.1f} eV")
a.set_xlabel("voltage (V)"); a.set_ylabel("J (mA/cm²)")
a.legend(fontsize=6.5, ncol=2, loc="lower left")
a.set_title("(a) JV curves, 0.05 mW/cm² white LED", fontsize=9)
a.grid(alpha=0.3)

a = axs[1]
voc = [data[f"Eg{e:.1f}"]["params"]["Voc"] for e in Egs if data[f"Eg{e:.1f}"]["params"]]
jsc = [data[f"Eg{e:.1f}"]["params"]["Jsc"] for e in Egs if data[f"Eg{e:.1f}"]["params"]]
eta = [data[f"Eg{e:.1f}"]["params"]["eta"] for e in Egs if data[f"Eg{e:.1f}"]["params"]]
a2 = a.twinx()
a.plot(Egs, voc, "o-", color="#1b9e77", label="Voc")
a2.plot(Egs, jsc, "s--", color="#d95f02", label="Jsc")
a.set_xlabel("bandgap Eg (eV)"); a.set_ylabel("Voc (V)", color="#1b9e77")
a2.set_ylabel("Jsc (mA/cm²)", color="#d95f02")
a.tick_params(axis="y", colors="#1b9e77"); a2.tick_params(axis="y", colors="#d95f02")
a.set_title("(b) Voc and Jsc vs Eg", fontsize=9)
a.grid(alpha=0.3)

fig.tight_layout()
fig.savefig(OUT, dpi=200)
print("wrote", OUT)
print("Eg:", Egs)
print("Voc:", [round(v, 3) for v in voc])
print("Jsc:", [round(j, 5) for j in jsc])
print("eta:", [round(e, 2) for e in eta])