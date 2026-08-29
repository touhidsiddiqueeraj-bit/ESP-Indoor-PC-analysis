#!/usr/bin/env python3
"""Side-by-side ESP32-S3 vs STM32F103 timing — for paper Table/Fig."""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import numpy as np, os
OUT="figs/fig_stm32_compare.png"
HERE=os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.size":8, "axes.titlesize":9})
labels=["ADC","PID\n(float)","PWM","Total\nstep"]
esp=[60.0, 6.78, 4.2, 70.98]
stm=[64.32,135.93,25.02,238.97]
x=np.arange(len(labels))
w=0.38
fig,ax=plt.subplots(figsize=(3.4,1.55))
ax.bar(x-w/2, esp, w, color="#1b9e77", label="ESP32-S3 240MHz (FPU)", edgecolor="white")
ax.bar(x+w/2, stm, w, color="#d95f02", label="STM32F103 72MHz (soft-float)", edgecolor="white")
for i,(e,s) in enumerate(zip(esp,stm)):
    ax.text(i-w/2, e+6, f"{e:.1f}", ha="center", fontsize=7)
    ax.text(i+w/2, s+6, f"{s:.0f}", ha="center", fontsize=7)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5)
ax.set_ylabel("µs", fontsize=8)
ax.set_ylim(0,280)
ax.legend(fontsize=6.5, loc="upper left")
ax.grid(axis="y", alpha=0.25)
ax.set_title("One perturb primitive: ESP32-S3 vs STM32F103", fontsize=9)
fig.tight_layout(pad=0.4)
fig.savefig(os.path.join(HERE,"..",OUT), dpi=300)
print("wrote", OUT)

# second fig: energy per step band
fig,ax=plt.subplots(figsize=(3.4,1.7))
esp_e=[8.2, 470]; stm_e=[28.4, 503.6]
ax.bar([0,1], [esp_e[0], stm_e[0]], color=["#1b9e77","#d95f02"], width=0.6, edgecolor="white")
ax.errorbar([0,1], [esp_e[0], stm_e[0]], yerr=[[0,0],[esp_e[1]-esp_e[0], stm_e[1]-stm_e[0]]], fmt="none", ecolor="black", capsize=6, label="up to +4ms wake")
ax.set_xticks([0,1]); ax.set_xticklabels(["ESP32-S3\n8.2→470 µJ","STM32F103\n28→504 µJ"],fontsize=7.5)
ax.set_ylabel("µJ per wake", fontsize=8)
ax.set_yscale("log")
ax.set_ylim(5,600)
ax.legend(fontsize=6.5)
ax.grid(alpha=0.25, which="both")
fig.tight_layout(pad=0.4)
fig.savefig(os.path.join(HERE,"../figs/fig_stm32_energy.png"), dpi=300)
print("wrote figs/fig_stm32_energy.png")
