#!/usr/bin/env python3
"""Indoor-illumination device sweep: JV families only (white 400-800 nm, 0.05 mW/cm^2).
Regenerated to remove overlap with Fig 6 (PCE vs SQ envelope): single panel JV only.
Single-column IEEE: 3.4in wide, 8-9pt fonts, 300dpi. ponytail: JV panel alone, Voc/Jsc in text, saves 1.25in vertical."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "figs", "fig_scaps_indoor.png"))
OUT_PAPER = os.path.abspath(os.path.join(HERE, "..", "paper", "fig_scaps_indoor.png"))
os.makedirs(os.path.dirname(OUT), exist_ok=True)

plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7})

data = json.load(open(os.path.join(HERE, "..", "results", "scaps_indoor.json")))
Egs = sorted((float(k[2:]) for k in data))

# single panel: JV families only — saves vertical space, distinct from Fig 6 (PCE vs envelope)
fig, ax = plt.subplots(figsize=(3.4, 1.75))
for k in sorted(data):
    d = data[k]
    if not d.get("V"):
        continue
    Eg = float(k[2:])
    ax.plot(d["V"], d["J"], lw=1.4, label=f"$E_g$={Eg:.1f} eV")
ax.set_xlabel("voltage (V)")
ax.set_ylabel("J (mA/cm$^2$)")
ax.legend(fontsize=6.8, ncol=3, loc="upper right", framealpha=0.9, handlelength=1.4, borderpad=0.3, labelspacing=0.3)
ax.set_title("JV families, 0.05 mW/cm$^2$ white LED (sim.)", fontsize=9, pad=6)
ax.grid(alpha=0.25)
ax.tick_params(labelsize=8)
ax.set_xlim(0, 1.6)
# annotate peak
ax.text(0.02, 0.018, "peak 26.1% @1.6eV", fontsize=6.5, color="#1b9e77", va="top", ha="left",
        bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#1b9e77", alpha=0.85))

fig.tight_layout(pad=0.5)
fig.savefig(OUT, dpi=300)
# copy to paper
import shutil
shutil.copy(OUT, OUT_PAPER)
print("wrote", OUT)
print("wrote", OUT_PAPER)
print("Eg:", Egs)
voc = [data[f"Eg{e:.1f}"]["params"]["Voc"] for e in Egs if data[f"Eg{e:.1f}"]["params"]]
jsc = [data[f"Eg{e:.1f}"]["params"]["Jsc"] for e in Egs if data[f"Eg{e:.1f}"]["params"]]
eta = [data[f"Eg{e:.1f}"]["params"]["eta"] for e in Egs if data[f"Eg{e:.1f}"]["params"]]
print("Voc:", [round(v, 3) for v in voc])
print("Jsc:", [round(j, 5) for j in jsc])
print("eta:", [round(e, 2) for e in eta])
