#!/usr/bin/env python3
"""fig_sleepwave: deep-sleep probe cadence — 4ms active every 3.28s.
Single-column IEEE version: 3.4in wide, 8pt+ fonts, 300dpi."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "figs", "fig_sleepwave.png"))
os.makedirs(os.path.dirname(OUT), exist_ok=True)

plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9.5, "xtick.labelsize": 9, "ytick.labelsize": 9})

period_s = 3.28
burst_ms = 4.0
sleep_ua_board = 21
active_ma = 35

t = np.linspace(0, 2*period_s, 2000)
current = np.full_like(t, sleep_ua_board * 1e-3)  # mA
for n in range(2):
    start = n*period_s + 0.28
    end = start + burst_ms/1000
    m = (t >= start) & (t < end)
    current[m] = active_ma

fig, ax = plt.subplots(figsize=(3.4, 2.10))
ax.plot(t, current, color="#1b9e77", lw=1.8, drawstyle="steps-post")
ax.fill_between(t, current, step="post", color="#1b9e77", alpha=0.18)

for n in range(2):
    x0 = n*period_s + 0.28
    ax.annotate(f"{burst_ms:.0f} ms", xy=(x0+0.002, active_ma), xytext=(x0+0.38, active_ma-7),
                fontsize=8.5, ha="center", va="center",
                arrowprops=dict(arrowstyle="->", lw=0.9, color="black"),
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="gray", alpha=0.95))
    if n == 0:
        ax.annotate("", xy=(period_s + 0.28, -1.8), xytext=(0.28, -1.8),
                    arrowprops=dict(arrowstyle="<->", lw=1.0, color="black"))
        ax.text(period_s/2 + 0.28, -4.2, f"period {period_s:.2f} s  (3.00 s + 0.28 s boot/USB)", ha="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.9))

ax.set_ylim(-6, 42)
ax.set_xlim(0, 2*period_s)
ax.set_xlabel("time (s)", fontsize=9.5)
ax.set_ylabel("current (mA)", fontsize=9.5)
ax.set_yticks([0, 0.021, 10, 20, 35])
ax.set_yticklabels(["0", "21 µA", "10", "20", "35"], fontsize=8.5)
ax.grid(alpha=0.25, which="both")
ax.set_title("Deep-sleep: 4.0 ms burst every 3.28 s", fontsize=10, pad=8)
fig.tight_layout(pad=0.6)
fig.savefig(OUT, dpi=300)
print("wrote", OUT)
