#!/usr/bin/env python3
"""fig_step: MPPT step timing breakdown.  fig_cadence: serve-vs-sleep budget split.
Regenerated for IEEE column legibility: 3.4in wide, 8-9pt fonts, 300dpi."""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.abspath(os.path.join(HERE, "..", "figs"))
os.makedirs(FIG, exist_ok=True)
D = json.load(open(os.path.join(HERE, "..", "results", "energy_model.json")))

plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 7.5})

# ---- fig_step : one perturb step, timing + energy contribution ----
comp = ["ADC read", "float PID", "PWM write"]
t_us  = [60.0, 6.78, 4.2]
fig, ax = plt.subplots(figsize=(3.4, 1.50))
bars = ax.bar(comp, t_us, color=["#7570b3", "#1b9e77", "#d95f02"], width=0.58, edgecolor="white", linewidth=0.6)
for b, v in zip(bars, t_us):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}", ha="center", fontsize=8.5, fontweight="bold")
ax.set_ylabel("wall time ($\\mu$s)", fontsize=8.5)
ax.set_ylim(0, 72)
ax.grid(axis="y", alpha=0.25)
ax.set_title("one MPPT perturb step: 70.98 $\\mu$s", fontsize=9, pad=8)
for lbl in ax.get_xticklabels():
    lbl.set_fontsize(8)
ax.tick_params(labelsize=8)
fig.tight_layout(pad=0.5)
fig.savefig(os.path.join(FIG, "fig_step.png"), dpi=300)
print("wrote figs/fig_step.png")

# ---- fig_cadence : daily serve vs sleep energy, by cadence ----
C = D["part_c"]
cads = [c["cadence_min"] for c in C]
serve = [c["e_serve_j"] for c in C]
sleep = [c["e_sleep_j"] for c in C]
fig, ax = plt.subplots(figsize=(3.4, 1.50))
x = np.arange(len(cads))
ax.bar(x, sleep, color="#7570b3", label="sleep floor", width=0.68, edgecolor="white", linewidth=0.5)
ax.bar(x, serve, bottom=sleep, color="#1b9e77", label="serving", width=0.68, edgecolor="white", linewidth=0.5)
for i, (s, sl) in enumerate(zip(serve, sleep)):
    pct = 100 * s / (s + sl)
    # label inside the serving segment if tall enough, else above
    if s > 4:
        ax.text(i, sl + s/2, f"{pct:.0f}%", ha="center", va="center", fontsize=8, color="white", fontweight="bold")
    else:
        ax.text(i, s + sl + 0.9, f"{pct:.0f}%", ha="center", fontsize=8, color="black")
ax.set_xticks(x)
ax.set_xticklabels([f"{c}" for c in cads], fontsize=8)
ax.set_xlabel("serve cadence (min)", fontsize=8.5)
ax.set_ylabel("daily energy (J)", fontsize=8.5)
ax.legend(fontsize=7.5, loc="upper right", framealpha=0.9)
ax.grid(axis="y", alpha=0.25)
ax.set_title("serve vs sleep (100 mA burst)", fontsize=8.5, pad=6)
ax.tick_params(labelsize=8)
fig.tight_layout(pad=0.5)
fig.savefig(os.path.join(FIG, "fig_cadence.png"), dpi=300)
print("wrote figs/fig_cadence.png")
