# ESP Indoor PV — Firmware-Only MPPT on ESP32-S3

Indoor light is dim (tens of microwatts per cm²) but perovskite and dye-sensitized cells are now efficient enough to power a sensing node from it. The usual approach adds a dedicated energy-harvesting PMIC between cell and MCU. This project asks whether the MCU itself can do the job.

**Result:** on an ESP32-S3, a single-channel control update costs **70.98 µs / 8.2 µJ** (timing-derived at 3.3 V / 35 mA; two-channel P&O ≈ 131 µs / 15.1 µJ; STM32F103 soft-float comparison: 239 µs / 28.4 µJ). The per-wake energy is bounded at 8.2–470 µJ (57× uncertainty pending rail-current measurement), so the firmware-vs-PMIC crossover is a **sensitivity, not a point result**: ≈ 4.9–6.2 s at the algorithm-only lower bound, ≈ 279–356 s at the harness-inclusive upper bound. Once the ≈ 8.5 µW discrete-stage floor (sense + LDO) is included there is **no quiescent-power crossover** — firmware competes on BOM, configurability and workload duty, not static power, and the discrete power stage remains required. A simulated SCAPS-1D cell (26.1% at 1.6 eV, 0.05 mW/cm²) and simulated P&O tracking (~93% at 5 s, ~70% at ≥ 60 s cadence) bound the harvest; under one office profile a 38% DSC with a 2 F supercapacitor sustains ~1730 net 100 mA bursts/day (~1600 at 93.3% MPPT, Tp = 5 s). Timing is measured; harvest, tracking and the converter are simulated.

Paper: [`paper/document.pdf`](paper/document.pdf) — *Bounding the Control-Energy Overhead of Firmware MPPT on ESP32-S3 vs. STM32F103: A Timing Characterization and Simulated Feasibility Envelope* (IEEE conference, 6 pages).

## What this repo contains

- **Paper sources** in `paper/` — LaTeX (`document.tex`), bibliography (`references.bib`), the compiled PDF, and all 10 paper figures as 300 dpi PNGs (also a 6-page `.docx` export). The compiled PDF is single-column figures/tables with clickable citations.
- **Models + figures** in `src/` and `figs/` — Python scripts that generate the crossover, dispatch, and SCAPS plots from the JSON results in `results/`.
- **Firmware harness** in `firmware/` — ESP32-S3 code that measures the MPPT step on silicon and validates the deep-sleep probe. Captured logs live in `firmware/results/`.

```
paper/            compiled paper + LaTeX sources
src/              energy_model.py, SCAPS + dispatch figure generators
figs/             generated figures (also copied into paper/)
results/          energy_model.json, scaps_indoor.json, sleep_probe.json
firmware/src/     main.cpp — modes B / C / H / D
firmware/host/    capture and analysis helpers
references.bib    bibliography (also in paper/)
```

## Reproduce

**Models and figures (no hardware):**

```bash
python3 src/energy_model.py
python3 src/fig_scaps_indoor.py
python3 src/scaps_validation.py
python3 src/compose_figs.py
python3 src/compose_figs2.py
python3 src/fig_stm32_compare.py
python3 src/fig_sleepwave.py
```

**Paper:**

```bash
cd paper
pdflatex document.tex; bibtex document; pdflatex document.tex; pdflatex document.tex
```

**Firmware (ESP32-S3 DevKitM-1):**

Wiring: short **GPIO2 (LEDC PWM, ~100 kHz) → GPIO1 (ADC1_CH0)**. The controller drives duty `d` and senses the averaged pin voltage.

```bash
cd firmware
pio run --target upload
pio device monitor -b 460800
# then on the serial console send: B (benchmark) | H (LEDC/ADC) | C (closed loop) | D3 (deep-sleep 3s ×5)
python3 host/capture.py
python3 host/capture_sleep.py 3 5
```

## Key numbers

| | Value |
|---|---|
| MPPT step (single-channel) | 70.98 µs (ADC 60.0 + PID 6.78 + PWM 4.2 µs); STM32F103 239 µs (soft-float) |
| Two-channel P&O step | ≈ 131 µs / 15.1 µJ ESP32-S3; ≈ 304 µs / 36.1 µJ STM32F103 |
| Energy per step @ 3.3 V / 35 mA | 8.2 µJ (lower bound); per-wake upper bound ≈ 470 µJ (harness-inclusive, rail unmeasured) |
| Crossover period vs PMICs | sensitivity: 4.9–6.2 s (algo-only lower bound) → 279–356 s (harness-inclusive upper); **no crossover** once the 8.5 µW discrete floor (sense + LDO) is added |
| SCAPS MAPbI₃ @ 0.05 mW/cm² white LED | E_g=1.6 eV → 0.018 mA/cm², 26.1%; 2.1 eV → 0.0075 mA/cm², 14.6% (simulated) |
| P&O tracking efficiency (simulated) | 93.3% at Tp=5 s; ~70% at Tp ≥ 60 s |
| 38% DSC dispatch (24 h, 100 ms @100 mA, 90% budget) | ~821 µW avg harvest → **~1730 net serves/day** (100% η_MPPT); ~1600 at 93.3% (Tp=5 s); 1935 is the gross figure ignoring sleep + MPPT losses |
| Deep-sleep probe | 4.0 ms wake every 3.28 s (3.00 s sleep + 0.28 s boot/USB); boot-segment rail current unmeasured |

## Hardware & dependencies

- ESP32-S3 DevKitM-1 (240 MHz, 16 MB flash, native USB)
- PlatformIO + Arduino framework, Python 3 with `numpy`/`matplotlib`
- SCAPS-1D for the indoor cell sweep (bundled white 400–800 nm spectrum)

## Citation

If you use the models, figures, or firmware harness, please cite the paper in `paper/document.pdf` and the relevant datasheets and SCAPS references listed in `references.bib`.

## License

Code and paper sources are provided as-is for reproduction. See `paper/document.pdf` for the full analysis.
