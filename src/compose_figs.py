#!/usr/bin/env python3
"""Figures for the ESP32-S3 indoor-PV power hub paper.
fig_overhead:  firmware MPPT control tax (uW) vs perturb period, vs IC quiescent.
fig_dispatch:  24 h dispatch -- lux, harvest, storage SOC, serve events.
fig_feas:      peak sustainable active duty vs active-burst current, by PV type.
Single-column IEEE: 3.4in wide, 8pt+ fonts, 300dpi."""
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

V = 3.3
I_SLEEP_BOARD = 21e-6
N_HOURS = 24

# ---- fig_overhead ----  single-column, whitespace-trimmed
A = D["part_a"]
fig, ax = plt.subplots(figsize=(3.4, 1.85))
per = np.array(A["fw_tax"]["period_s"])
fw = np.array(A["fw_tax"]["uw"])
ax.semilogx(per, fw, lw=1.6, color="#1b9e77", label="firmware MPPT tax")
for name, tax in A["ic_bars_uw"].items():
    ax.axhline(tax, ls="--", lw=1.1, color="#d95f02", alpha=0.85)
    ax.text(1.08, tax * 1.28, f"{name} $I_q$", fontsize=6.5, color="#d95f02", va="center", ha="left",
            bbox=dict(boxstyle="round,pad=0.08", fc="white", ec="none", alpha=0.85))
for name, p in A["cross_period_s"].items():
    if p:
        ax.plot(p, A["ic_bars_uw"][name], "o", ms=3.5, color="#d95f02", mec="white", mew=0.6, zorder=5)
ax.annotate("one 8.2 $\\mu$J\nperturb / period",
            xy=(16, 8.2e-6 * 1e6 / 16), xytext=(28, 3.0),
            fontsize=6.5, arrowprops=dict(arrowstyle="->", lw=0.7, color="black"),
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="gray", alpha=0.85))
ax.set_xlabel("MPPT perturb period (s)", fontsize=8)
ax.set_ylabel("average control tax ($\\mu$W)", fontsize=8)
ax.grid(True, which="both", alpha=0.25)
ax.set_ylim(0.008, 12)
ax.set_xlim(1, 1000)
ax.legend(fontsize=6.5, loc="upper right", framealpha=0.92, handlelength=1.2, borderpad=0.3, labelspacing=0.3)
ax.tick_params(labelsize=7.5, pad=2)
fig.tight_layout(pad=0.35)
fig.subplots_adjust(top=0.92, bottom=0.18, left=0.18, right=0.97)
fig.savefig(os.path.join(FIG, "fig_overhead.png"), dpi=300, bbox_inches="tight", pad_inches=0.02)
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
harvest = p_pv_ref * (lux / 1000.0) * eta_conv
dt = t[1] - t[0]
soc = np.zeros_like(t)
E = 0.0
serve_e = V * 100e-3 * 0.100
serve_idx = np.round(np.arange(0, t[-1], 0.5) * 60).astype(int)
sleep_pow = V * I_SLEEP_BOARD
for k in range(len(t)):
    active = 0.0
    if k in serve_idx and 7.0 <= t[k] <= 22.0:
        active = 1.0
    consume = (1 - active) * sleep_pow + active * (V * 0.100)
    E += (harvest[k] - consume) * dt / 3600.0 * 3600.0
    E = max(E, 0.0)
    soc[k] = E

fig, axs = plt.subplots(3, 1, figsize=(3.4, 2.45), sharex=True, height_ratios=[1, 1, 1.4])
axs[0].fill_between(t, lux / 1000.0, alpha=0.5, color="#f0a202", step="mid")
axs[0].set_ylabel("illum.\n(klux)", fontsize=8)
axs[0].set_yticks([0.05, 0.3, 1.0])
axs[0].tick_params(labelsize=8)
axs[1].plot(t, harvest * 1e3, color="#1b9e77", lw=1.3)
axs[1].set_ylabel("harvest\n(mW)", fontsize=8)
axs[1].tick_params(labelsize=8)
axs[2].plot(t, soc, color="#7570b3", lw=1.3)
axs[2].set_ylabel("stored\n(J)", fontsize=8)
axs[2].set_xlabel("time (h)", fontsize=8)
axs[2].set_xlim(0, 24)
axs[2].set_xticks([0, 6, 12, 18, 24])
axs[2].tick_params(labelsize=8)
for a in axs:
    a.grid(alpha=0.25)
    a.tick_params(labelsize=8)
fig.tight_layout(pad=0.4, h_pad=0.35)
fig.savefig(os.path.join(FIG, "fig_dispatch.png"), dpi=300)
print("wrote figs/fig_dispatch.png")

# ---- fig_feas : sustainable duty vs active current, per PV ----
fig, ax = plt.subplots(figsize=(3.4, 1.85))
i_act = np.array([100, 250, 500])
colors = {"DSC (38%)": "#1b9e77", "a-Si thin-film": "#d95f02", "SCAPS Eg=1.6 cell": "#7570b3"}
xpos = np.arange(len(i_act))
w = 0.26
for j, (pv, col) in enumerate(colors.items()):
    sub = [r for r in D["part_b"] if r["pv"] == pv and r["sleep"] == "board"]
    duty = [r["max_duty_pct"] for r in sub]
    wakes = [r["wakes_per_hour_100ms"] for r in sub]
    ax.bar(xpos + (j - 1) * w, duty, w, color=col, label=pv, edgecolor="white", linewidth=0.6)
    for xi, wk in zip(xpos + (j - 1) * w, wakes):
        ax.text(xi, 0.32, f"{wk:.0f}/h", ha="center", fontsize=6.5, rotation=90,
                color="white", fontweight="bold", va="bottom")
ax.set_xticks(xpos)
ax.set_xticklabels([f"{v} mA" for v in i_act], fontsize=8)
ax.set_xlabel("active-burst current", fontsize=8)
ax.set_ylabel("sustainable duty (%)", fontsize=8)
ax.set_yscale("log")
ax.set_ylim(0.02, 2)
ax.legend(fontsize=7, loc="upper right", framealpha=0.9)
ax.grid(alpha=0.25, which="both")
ax.tick_params(labelsize=8)
fig.tight_layout(pad=0.4)
fig.savefig(os.path.join(FIG, "fig_feas.png"), dpi=300)
print("wrote figs/fig_feas.png")
