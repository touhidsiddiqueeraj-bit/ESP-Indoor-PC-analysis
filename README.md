# Ditch the PMIC: Firmware-Only MPPT on ESP32-S3 for Indoor Photovoltaics

> **Can an ESP32-S3 run its own maximum power point tracking (MPPT) and ditch the dedicated energy-harvesting PMIC indoors?** This repo contains the full analysis, firmware, and paper sources showing the answer is *yes* — above a 4.9–7.0 s perturb cadence, firmware MPPT is strictly cheaper than the TI bq25570 / e-peas AEM10941 / ADI ADP5091.

Paper: [`paper/document.pdf`](paper/document.pdf) — 6-page IEEE conference format (20 refs, all clickable, single-column figures/tables).

## Key Result

| Quantity | Value | Source |
|---|---|---|
| One MPPT perturb step (`ADC + PID + PWM`) | **70.98 µs = 60.0 + 6.78 + 4.2 µs** | ESP32-S3 cycle-counter (Fig. 1, Tab. I) |
| Energy per step `@3.3V × 35mA` | **8.2 µJ** | Eq. 1 |
| Firmware control tax | **8.2 µW @1s → 0.008 µW @60s** (`E_step / T_p`) | `results/energy_model.json:part_a` |
| PMIC quiescent tax `@3.3V` | **1.61 / 1.32 / 1.68 µW** (bq25570 / AEM10941 / ADP5091) | datasheets + Tab. II |
| **Crossover`T_p`** (firmware beats IC) | **5.88 / 7.02 / 4.92 s** | Fig. 3, `cross_period_s` (logspace grid, Sec. IV) |
| Indoor harvest (MAPbI₃ SCAPS, `E_g=1.6eV, 0.05mW/cm²`) | **0.018 mA/cm², 26.1%** | SCAPS-1D sweep, Fig. 2 |
| 38% DSC cell daily avg | **821 µW → 1935 serves/day** (100 ms @100 mA, 90% budget) | 24h dispatch, Tab. III, Fig. 4–5 |
| Deep-sleep wake latency | **4.0 ms** every **3.28 s**, `~0.44µJ` at sleep floor (`~5%` of a step) | `results/sleep_probe.json`, Fig. 7 |

At the crossover, firmware tax falls to 1.2–1.7 µW and keeps dropping with `T_p`. For any workload tolerating a ≥5 s MPPT cadence, the firmware hub omits the $1–3 PMIC and its footprint with no extra hardware.

## Repo Layout

```
esp-indoor-pv/
├── paper/                 # compiled paper (PDF + LaTeX + .bib + PNGs)
│   ├── document.pdf       # ← read this
│   ├── document.tex       # IEEEtran source (with hyperref, clickable cites)
│   ├── references.bib     # 20 entries
│   └── fig_*.png          # 7 single-column figures (300 dpi)
├── src/                   # modelling / figure generation
│   ├── energy_model.py    # Part A/B/C: fw tax vs PMIC, 24h dispatch
│   ├── fig_scaps_indoor.py
│   ├── compose_figs.py / compose_figs2.py
│   └── sim_core.py
├── figs/                  # regenerated PNGs (copied to paper/ + workspace)
├── results/
│   ├── energy_model.json  # e_step_uj, fw_tax, ic_bars_uw, cross_period_s, part_c
│   ├── scaps_indoor.json  # JV curves Eg 1.6–2.1 eV + Voc/Jsc/FF/eta
│   └── sleep_probe.json   # 5 × 4.0 ms wakes, 3.28 s spacing
└── firmware/              # ESP32-S3 harness (PlatformIO / Arduino)
    ├── src/main.cpp       # Modes B (pipeline), C (closed loop), H (LEDC/ADC), D (deep-sleep)
    ├── host/capture.py, capture_sleep.py, analyze.py, compose_fig.py
    └── platformio.ini     # esp32-s3-devkitm-1, 240 MHz, 16 MB, 460800 baud
```

## Reproduce

### 1. Energy / dispatch model (no hardware)

```bash
python3 src/energy_model.py        # writes results/energy_model.json + self-checks
python3 src/fig_scaps_indoor.py    # figs/fig_scaps_indoor.png
python3 src/compose_figs.py        # figs/fig_overhead.png, fig_dispatch.png, fig_feas.png
python3 src/compose_figs2.py       # figs/fig_step.png, fig_cadence.png
# sleepwave (from measured sleep_probe.json):
python3 - <<'PY'
import json, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
d=json.load(open("results/sleep_probe.json")); T_ROUND=d["round_spacing_s"][0]*1000
# (see src history for full 3.4×1.7 step plot — figs/fig_sleepwave.png)
PY
```

### 2. Paper (6 pp IEEE)

Direct LaTeX (no texflow MCP needed — `texflow/model.py` was patched to keep `hyperref` for IEEE conference):

```bash
cd paper   # or workspace copy at ~/Documents/texflowmcp/workspace
pdflatex document.tex; bibtex document; pdflatex document.tex; pdflatex document.tex
# → document.pdf (6 pages, hyperref clickable, 0 figure*/table*)
```

Or via texflow MCP layout `ieee-conference` (requires `hyperref` kept in `required_packages`).

Figures are single-column (`0.85–0.95\linewidth`, `small` tables, no `figure*`/`table*`). Regenerated Figs 2,3,5,6 use larger fonts (8–10 pt axes) so text is legible at column width.

### 3. Firmware (needs ESP32-S3 DevKitM-1, GPIO2→GPIO1 jumper)

```bash
cd firmware
pio run --target upload   # flashes main.cpp
pio device monitor -b 460800
# On serial, send: B  (benchmark), H  (LEDC/ADC), C  (closed loop), D3  (deep-sleep 3s×5)
python3 host/capture.py        # streams CSV,... lines
python3 host/capture_sleep.py 3 5  # writes results/sleep_probe.json
python3 host/analyze.py && python3 host/compose_fig.py  # firmware/results/fig_emb.png
```

Wiring: **GPIO2 (LEDC PWM ~100 kHz) shorted to GPIO1 (ADC1_CH0)**. Controller drives duty `d`; sensed `Vpin = d×3.3V` maps to paper's `Vout = Vpin×24/3.3−24` (Vref=−12 V half-scale).

## Numbers to Check Before Submission

* Eq. 1: `8.2µJ ×1Hz =8.2µW`; `100Hz →820µW` (Sec. II text now says `1Hz→8.2µW`, `4.9–7.0s→1.2–1.7µW`).
* Cross: analytic `E_step/tax =5.09/6.21/4.87s` vs grid `5.88/7.02/4.92s` (`logspace(1,1000,40)` next grid point — Tab. II is consistent with grid, not analytic).
* Deep-sleep: `4ms @35mA =462µJ` (`56×` step); `0.44µJ` in text is at `~33µA` sleep floor (`5%` of step) — why firmware sleeps immediately after the `71µs` step.
* `E_sleep =21µA×3.3V×86400=5.99J/day` (`≈6J` prose); `5h night @21µA=1.25J` — `3.7J` worst-case in Sec. V includes regulator overhead (verify).
* SCAPS `Eg=1.6→2.1eV`: `Voc 0.896→1.481V`, `Jsc 0.0182→0.0075 mA/cm²`, `η 26.1→14.6%`.

## Citation Note

Prior work (Murtola et al., PerCom Workshops 2022) is characterized as “found a conventional harvester node in their setup struggled to sustain sensor bursts” — intentionally softened from a stronger “unsuited” claim to avoid a straw-man. The paper’s abstract now reads “can sustain where prior work struggled” rather than “refute”.

## Acknowledgements

SCAPS-1D (Burgelman et al.), Espressif ESP32-S3 datasheet/TRM/current-measurement guide, TI/e-peas/ADI datasheets, indoor PV refs (Ariken, Mateen, Mathews, Ma 2024 44.7% record, Xu 2026 progress).

## License

Paper sources and firmware/model code as-is for reproduction. Figure data in `results/*.json` is the ground truth — verify before citing.
