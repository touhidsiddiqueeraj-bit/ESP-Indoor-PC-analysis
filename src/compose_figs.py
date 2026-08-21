#!/usr/bin/env python3
"""Figures for the ESP32-S3 indoor-PV power hub paper.

fig_overhead:  firmware MPPT control tax (uW) vs perturb period, vs IC quiescent.
fig_dispatch:  24 h dispatch -- lux, harvest, storage SOC, serve events.
fig_feas:      peak sustainable active duty vs active-burst current, by PV type.
"""
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

V = 3.3
I_SLEEP_BOARD = 21e-6
N_HOURS = 24

# ---- fig_overhead ----
A = D["part_a"]
fig, ax = plt.subplots(figsize=(4.2, 2.6))
per = np.array(A["fw_tax"]["period_s"])
fw = np.array(A["fw_tax"]["uw"])
ax.semilogx(per, fw, lw=1.6, color="#1b9e77", label="firmware MPPT tax")
for name, tax in A["ic_bars_uw"].items():
    ax.axhline(tax, ls="--", lw=1.0, color="#d95f02", alpha=0.8)
    ax.text(1.25, tax * 1.28, f"{name} Iq", fontsize=6.5, color="#d95f02")
# crossover markers
for name, p in A["cross_period_s"].items():
    if p:
        ax.plot(p, A["ic_bars_uw"][name], "o", ms=4, color="#d95f02")
ax.annotate("one 8.2 $\\mu$J\nperturb / period",
            xy=(16, 8.2e-6 * 1e6 / 16), xytext=(60, 2.5),
            fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.7))
ax.set_xlabel("MPPT perturb period (s)")
ax.set_ylabel("average control tax ($\\mu$W)")
ax.grid(True, which="both", alpha=0.25)
ax.set_ylim(1e-3, 30)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_overhead.png"), dpi=300)
print("wrote figs/fig_overhead.png")

# ---- fig_dispatch : 24 h timeline ----
def lux_profile(t_h):
    if 8.0 <= t_h < 19.0:
        return 1000.0
    if 6.0 <= t_h < 8.0 or 19.0 <= t_h < 20.0:
        return 300.0
    return 50.0

p_pv_ref = 1.87e-3
eta_conv = 0.85
t = np.linspace(0, 24, 24 * 60)
lux = np.array([lux_profile(x) for x in t])
harvest = p_pv_ref * (lux / 1000.0) * eta_conv                     # W
# battery/	supercap simulation: serve every 30 min at 07-22, sleep floor otherwise
dt = t[1] - t[0]
soc = np.zeros_like(t)
E = 0.0
serve_e = V * 100e-3 * 0.100  # 33 mJ
serve_idx = np.round(np.arange(0, t[-1], 0.5) * 60).astype(int)
sleep_pow = V * I_SLEEP_BOARD
serve_w = np.zeros_like(t)
for k in range(len(t)):
    active = serve_power = 0.0
    if k in serve_idx and 7.0 <= t[k] <= 22.0:
        active, serve_power = 1.0, serve_e / (0.100)  # instantaneous during serve
    consume = (1 - active) * sleep_pow + active * (V * 0.100)
    E += (harvest[k] - consume) * dt / 3600.0 * 3600.0   # J (dt in h)
    E = max(E, 0.0)
    soc[k] = E

fig, axs = plt.subplots(3, 1, figsize=(4.2, 3.6), sharex=True, height_ratios=[1, 1, 1.4])
axs[0].fill_between(t, lux / 1000.0, alpha=0.5, color="#f0a202")
axs[0].set_ylabel("illum. (klux)")
axs[0].set_yticks([0.05, 0.3, 1.0])
axs[1].plot(t, harvest * 1e3, color="#1b9e77", lw=1.0)
axs[1].set_ylabel("harvest (mW)")
axs[2].plot(t, soc / 1e3, color="#7570b3", lw=1.0)
axs[2].set_ylabel("stored (mJ)")
axs[2].set_xlabel("time (h)")
axs[2].set_xlim(0, 24)
for a in axs:
    a.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_dispatch.png"), dpi=300)
print("wrote figs/fig_dispatch.png")

# ---- fig_feas : sustainable duty vs active current, per PV ----
fig, ax = plt.subplots(figsize=(4.2, 2.6))
i_act = np.array([100, 250, 500])
colors = {"DSC (38%)": "#1b9e77", "a-Si thin-film": "#d95f02", "SCAPS Eg=1.6 cell": "#7570b3"}
xpos = np.arange(len(i_act))
w = 0.26
for j, (pv, col) in enumerate(colors.items()):
    sub = [r for r in D["part_b"] if r["pv"] == pv and r["sleep"] == "board"]
    duty = [r["max_duty_pct"] for r in sub]
    wakes = [r["wakes_per_hour_100ms"] for r in sub]
    ax.bar(xpos + (j - 1) * w, duty, w, color=col, label=pv)
    for xi, wk in zip(xpos + (j - 1) * w, wakes):
        ax.text(xi, 0.5, f"{wk:.0f}/h", ha="center", fontsize=6.5, rotation=90,
                color="white")
ax.set_xticks(xpos)
ax.set_xticklabels([f"{v} mA" for v in i_act])
ax.set_xlabel("active-burst current")
ax.set_ylabel("sustainable duty (%)")
ax.set_yscale("log")
ax.legend(fontsize=6.5, loc="upper right")
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_feas.png"), dpi=300)
print("wrote figs/fig_feas.png")