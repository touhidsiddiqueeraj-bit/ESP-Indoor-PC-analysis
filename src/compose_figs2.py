#!/usr/bin/env python3
"""fig_step: MPPT step timing breakdown.  fig_cadence: serve-vs-sleep budget split."""
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

# ---- fig_step : one perturb step, timing + energy contribution ----
comp = ["ADC read", "float PID", "PWM write"]       # order in firmware
t_us  = [60.0, 6.78, 4.2]                            # measured cycle counts
fig, ax = plt.subplots(figsize=(2.9, 2.3))
bars = ax.bar(comp, t_us, color=["#7570b3", "#1b9e77", "#d95f02"], width=0.55)
for b, v in zip(bars, t_us):
    ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.1f}", ha="center", fontsize=7)
ax.set_ylabel("wall time ($\\mu$s)")
ax.set_ylim(0, 72)
ax.grid(axis="y", alpha=0.25)
ax.set_title("one MPPT perturb step: 70.98 $\\mu$s", fontsize=7.5)
for lbl in ax.get_xticklabels():
    lbl.set_fontsize(7)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_step.png"), dpi=300)
print("wrote figs/fig_step.png")

# ---- fig_cadence : daily serve vs sleep energy, by cadence ----
C = D["part_c"]
cads = [c["cadence_min"] for c in C]
serve = [c["e_serve_j"] for c in C]
sleep = [c["e_sleep_j"] for c in C]
fig, ax = plt.subplots(figsize=(2.9, 2.3))
x = np.arange(len(cads))
ax.bar(x, sleep, color="#7570b3", label="sleep floor")
ax.bar(x, serve, bottom=sleep, color="#1b9e77", label="serving")
for i, (s, sl) in enumerate(zip(serve, sleep)):
    ax.text(i, s + sl + 1.0, f"{100 * s / (s + sl):.0f}%", ha="center", fontsize=6.5)
ax.set_xticks(x)
ax.set_xticklabels([f"{c}" for c in cads], fontsize=7)
ax.set_xlabel("serve cadence (min)")
ax.set_ylabel("daily energy (J)")
ax.legend(fontsize=6, loc="upper right")
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_cadence.png"), dpi=300)
print("wrote figs/fig_cadence.png")