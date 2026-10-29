#!/usr/bin/env python3
"""fig_sleepwave: deep-sleep probe cadence — 4 ms active every 3.28 s.
Single-column IEEE version: 3.4in wide, 8pt+ fonts, 300dpi.

Fixed (2026):
 - legend added BELOW the axes (was absent; bottom-left annotations crowded the axis)
 - y-tick collision removed ("0" and "21 µA" sat on top of each other);
   the 21 µA floor now lives in the legend where it is readable
 - 0.28 s ROM-boot/USB segments shaded gray "(current unmeasured)" instead of
   being drawn at the sleep floor (sleep_probe.json contains timings only;
   the paper states boot current requires external rail measurement)
 - burst geometry built from exact corner points (was a 3.28 ms-grid artifact)
   so the drawn burst is exactly the measured 4.0 ms wide
 - current levels explicitly labelled nominal/typ. — only T is measured.
Timings (4.0 ms, 3.28 s, 3.00 s sleep) verified against results/sleep_probe.json.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "figs", "fig_sleepwave.png"))
os.makedirs(os.path.dirname(OUT), exist_ok=True)

plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8})

period_s = 3.28      # measured round spacing (sleep_probe.json)
burst_ms = 4.0       # measured firmware-visible wake latency (sleep_probe.json)
boot_s = 0.28        # 3.28 - 3.00 s programmed: ROM boot + USB re-enumeration (host-side)
sleep_ua_board = 21  # nominal board sleep floor (assumed, used by dispatch)
active_ma = 35       # datasheet-typical active current (not measured on the rail)

floor_ma = sleep_ua_board * 1e-3

# Exact piecewise-constant waveform (steps-post): the burst is drawn exactly
# burst_ms wide instead of depending on a sampling grid.
t_pts, i_pts = [], []
for n in range(2):
    t0 = n * period_s
    t_pts += [t0, t0 + boot_s, t0 + boot_s + burst_ms/1000]
    i_pts += [floor_ma, active_ma, floor_ma]
t_pts.append(2 * period_s)
i_pts.append(floor_ma)
t_pts = np.array(t_pts); i_pts = np.array(i_pts)

fig, ax = plt.subplots(figsize=(3.4, 1.9))

# gray boot/USB bands: current UNMEASURED (do not imply sleep-floor current)
for n in range(2):
    ax.axvspan(n*period_s, n*period_s + boot_s, color="#9e9e9e", alpha=0.35, zorder=0)

ax.plot(t_pts, i_pts, color="#1b9e77", lw=1.8, drawstyle="steps-post", zorder=3)
ax.fill_between(t_pts, i_pts, step="post", color="#1b9e77", alpha=0.18, zorder=1)

for n in range(2):
    x0 = n*period_s + boot_s
    ax.annotate(f"{burst_ms:.0f} ms", xy=(x0 + burst_ms/2000, active_ma), xytext=(x0 + 0.38, active_ma - 7),
                fontsize=8.5, ha="center", va="center",
                arrowprops=dict(arrowstyle="->", lw=0.9, color="black"),
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="gray", alpha=0.95))
    if n == 0:
        ax.annotate("", xy=(period_s + boot_s, -1.8), xytext=(boot_s, -1.8),
                    arrowprops=dict(arrowstyle="<->", lw=1.0, color="black"))
        ax.text(period_s/2 + boot_s, -3.9, f"period {period_s:.2f} s  (3.00 s deep sleep + 0.28 s boot/USB)",
                ha="center", fontsize=7.5,
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.9))

ax.set_ylim(-5.2, 42)
ax.set_xlim(0, 2*period_s)
ax.set_xlabel("time (s)", fontsize=9.5)
ax.set_ylabel("current (mA)", fontsize=9.5)
ax.set_yticks([0, 10, 20, 35])          # no 0.021 tick: it collided with "0"
ax.set_yticklabels(["0", "10", "20", "35"], fontsize=8.5)
ax.grid(alpha=0.25, which="major")
ax.set_title("Deep-sleep: 4.0 ms burst every 3.28 s", fontsize=10, pad=8)

legend_handles = [
    Line2D([0], [0], color="#1b9e77", lw=1.8,
          label=f"sleep floor {sleep_ua_board} µA (nominal board)"),
    Line2D([0], [0], color="#1b9e77", lw=3.2,
          label=f"active burst {burst_ms:.0f} ms @ {active_ma} mA (datasheet typ.)"),
    Patch(facecolor="#9e9e9e", alpha=0.30,
          label=f"{boot_s:.2f} s ROM boot + USB re-enum. (current unmeasured)"),
]
ax.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.40),
          ncol=1, fontsize=6.8, frameon=False, columnspacing=1.0, handlelength=1.6,
          labelspacing=0.28)
# explicit margins: reserve bottom room so the legend clears the x-axis label
fig.subplots_adjust(left=0.145, right=0.975, top=0.86, bottom=0.42)
fig.savefig(OUT, dpi=300, bbox_inches="tight", pad_inches=0.02)
print("wrote", OUT)
