# ESP Indoor PV — Firmware-Only MPPT on ESP32-S3

Indoor light is dim (tens of microwatts per cm²) but perovskite and dye-sensitized cells are now efficient enough to power a sensing node from it. The usual approach adds a dedicated energy-harvesting PMIC between cell and MCU. This project asks whether the MCU itself can do the job.

**Result:** on an ESP32-S3, a single perturb-and-observe MPPT step costs **71 µs / 8.2 µJ**. That is cheaper than the quiescent draw of the TI bq25570, e-peas AEM10941, and ADI ADP5091 once the perturb period exceeds **4.9–7.0 s**. For low-cadence sensing (one reading every tens of seconds to minutes) the firmware hub removes the harvester IC, its cost, and its board area.

Paper: [`paper/document.pdf`](paper/document.pdf) — *Ditch the PMIC: Firmware-Only MPPT on ESP32-S3 for Indoor Photovoltaics* (IEEE conference, 6 pages).

## What this repo contains

- **Paper sources** in `paper/` — LaTeX (`document.tex`), bibliography (`references.bib`), and all 7 figures as 300 dpi PNGs. The compiled PDF is single-column figures/tables with clickable citations.
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
python3 src/compose_figs.py
python3 src/compose_figs2.py
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
| MPPT step | 70.98 µs (ADC 60.0 + PID 6.78 + PWM 4.2 µs) |
| Energy per step @ 3.3 V / 35 mA | 8.2 µJ |
| Crossover period vs PMICs | 4.9 s (ADP5091) / 5.9 s (bq25570) / 7.0 s (AEM10941) |
| SCAPS MAPbI₃ @ 0.05 mW/cm² white LED | E_g=1.6 eV → 0.018 mA/cm², 26.1%; 2.1 eV → 0.0075 mA/cm², 14.6% |
| 38% DSC dispatch (24 h, 100 ms @100 mA, 90% budget) | ~821 µW avg harvest → ~1935 serves/day |
| Deep-sleep probe | 4.0 ms wake every 3.28 s; housekeeping ~0.44 µJ at the sleep floor |

## Hardware & dependencies

- ESP32-S3 DevKitM-1 (240 MHz, 16 MB flash, native USB)
- PlatformIO + Arduino framework, Python 3 with `numpy`/`matplotlib`
- SCAPS-1D for the indoor cell sweep (bundled white 400–800 nm spectrum)

## Citation

If you use the models, figures, or firmware harness, please cite the paper in `paper/document.pdf` and the relevant datasheets and SCAPS references listed in `references.bib`.

## License

Code and paper sources are provided as-is for reproduction. See `paper/document.pdf` for the full analysis.
