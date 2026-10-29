#!/usr/bin/env python3
"""Side-by-side ESP32-S3 vs STM32F103 timing — for paper Table/Fig.

Fixed (2026): legend moved below the axes so it no longer crowds the bars,
bar labels now use one uniform decimal (matches Table II: 64.3/135.9/25.0/239.0),
values verified against results/stm32_timing.json (no change to data).
Single-column IEEE: 3.4in wide, 8pt+ fonts, 300dpi.
"""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import numpy as np, os
OUT="figs/fig_stm32_compare.png"
HERE=os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.size":8, "axes.titlesize":9})

labels=["ADC","PID\n(float)","PWM","Total\nstep"]
# measured values (results/stm32_timing.json: esp32_ref + measurements)
esp=[60.0, 6.78, 4.2, 70.98]
stm=[64.32, 135.93, 25.02, 238.97]
x=np.arange(len(labels))
w=0.38
fig,ax=plt.subplots(figsize=(3.4,1.78))
ax.bar(x-w/2, esp, w, color="#1b9e77", label="ESP32-S3 240 MHz (FPU)", edgecolor="white")
ax.bar(x+w/2, stm, w, color="#d95f02", label="STM32F103 72 MHz (soft-float)", edgecolor="white")
for i,(e,s) in enumerate(zip(esp,stm)):
    ax.text(i-w/2, e+6, f"{e:.1f}", ha="center", fontsize=7)   # one decimal, both series
    ax.text(i+w/2, s+6, f"{s:.1f}", ha="center", fontsize=7)   # 64.3/135.9/25.0/239.0 as Table II
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5)
ax.set_ylabel("µs", fontsize=8)
ax.set_ylim(0,268)
ax.grid(axis="y", alpha=0.25)
ax.set_title("One perturb primitive: ESP32-S3 vs STM32F103", fontsize=9)
# legend below the axes: readable at print size, never overlaps the bars
ax.legend(fontsize=7, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.31),
          frameon=False, columnspacing=1.2, handlelength=1.4)
# explicit margins: reserve bottom room so the legend clears the x-tick labels
fig.subplots_adjust(left=0.11, right=0.98, top=0.88, bottom=0.30)
fig.savefig(os.path.join(HERE,"..",OUT), dpi=300, bbox_inches="tight", pad_inches=0.02)
print("wrote", OUT)

# second fig: energy per step band (not used in the paper; kept in sync)
fig,ax=plt.subplots(figsize=(3.4,1.78))
esp_e=[8.2, 470]; stm_e=[28.4, 503.6]
ax.bar([0,1], [esp_e[0], stm_e[0]], color=["#1b9e77","#d95f02"], width=0.6, edgecolor="white")
ax.errorbar([0,1], [esp_e[0], stm_e[0]], yerr=[[0,0],[esp_e[1]-esp_e[0], stm_e[1]-stm_e[0]]], fmt="none", ecolor="black", capsize=6, label="up to +4ms wake")
ax.set_xticks([0,1]); ax.set_xticklabels(["ESP32-S3\n8.2→470 µJ","STM32F103\n28→504 µJ"],fontsize=7.5)
ax.set_ylabel("µJ per wake", fontsize=8)
ax.set_yscale("log")
ax.set_ylim(5,600)
ax.grid(alpha=0.25, which="both")
ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.31), frameon=False)
fig.subplots_adjust(left=0.15, right=0.96, top=0.88, bottom=0.30)
fig.savefig(os.path.join(HERE,"../figs/fig_stm32_energy.png"), dpi=300, bbox_inches="tight", pad_inches=0.02)
print("wrote figs/fig_stm32_energy.png")
