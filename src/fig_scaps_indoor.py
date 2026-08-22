#!/usr/bin/env python3
"""Indoor-illumination device sweep: JV curves + bandgap metrics (white 400-800 nm, 0.05 mW/cm^2).
Single-column version for IEEE 2-col: stacked 2×1, 3.4in wide, 8-9pt fonts, 300dpi."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "figs", "fig_scaps_indoor.png"))
os.makedirs(os.path.dirname(OUT), exist_ok=True)

plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.5})

data = json.load(open(os.path.join(HERE, "..", "results", "scaps_indoor.json")))
Egs = sorted((float(k[2:]) for k in data))

# single-column: stacked vertically so text stays >=8pt at 0.95\linewidth (~3.2in)
fig, axs = plt.subplots(2, 1, figsize=(3.4, 3.10), sharex=False)
fig.subplots_adjust(hspace=0.45)

a = axs[0]
for k in sorted(data):
    d = data[k]
    if not d.get("V"):
        continue
    Eg = float(k[2:])
    a.plot(d["V"], d["J"], lw=1.4, label=f"$E_g$={Eg:.1f} eV")
a.set_xlabel("voltage (V)"); a.set_ylabel("J (mA/cm$^2$)")
a.legend(fontsize=7, ncol=2, loc="lower left", framealpha=0.9, handlelength=1.5, borderpad=0.4)
a.set_title("(a) JV curves, 0.05 mW/cm$^2$ white LED", fontsize=9, pad=6)
a.grid(alpha=0.3)
a.tick_params(labelsize=8)

a = axs[1]
voc = [data[f"Eg{e:.1f}"]["params"]["Voc"] for e in Egs if data[f"Eg{e:.1f}"]["params"]]
jsc = [data[f"Eg{e:.1f}"]["params"]["Jsc"] for e in Egs if data[f"Eg{e:.1f}"]["params"]]
eta = [data[f"Eg{e:.1f}"]["params"]["eta"] for e in Egs if data[f"Eg{e:.1f}"]["params"]]
a2 = a.twinx()
l1 = a.plot(Egs, voc, "o-", color="#1b9e77", label="Voc", lw=1.6, ms=5)
l2 = a2.plot(Egs, jsc, "s--", color="#d95f02", label="Jsc", lw=1.4, ms=5)
a.set_xlabel("bandgap $E_g$ (eV)"); a.set_ylabel("Voc (V)", color="#1b9e77")
a2.set_ylabel("Jsc (mA/cm$^2$)", color="#d95f02")
a.tick_params(axis="y", colors="#1b9e77", labelsize=8); a2.tick_params(axis="y", colors="#d95f02", labelsize=8)
a.tick_params(labelsize=8)
a.set_title("(b) Voc and Jsc vs $E_g$", fontsize=9, pad=6)
a.grid(alpha=0.3)
lines = l1 + l2
labels = [l.get_label() for l in lines]
a2.legend(lines, labels, fontsize=7, loc="center right", framealpha=0.9)

fig.tight_layout(pad=0.6)
fig.savefig(OUT, dpi=300)
print("wrote", OUT)
print("Eg:", Egs)
print("Voc:", [round(v, 3) for v in voc])
print("Jsc:", [round(j, 5) for j in jsc])
print("eta:", [round(e, 2) for e in eta])
