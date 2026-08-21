#!/usr/bin/env python3
"""ESP32-S3 indoor-PV power-hub feasibility model.

Three contributions, all in one script:
  A. Marginal energy tax of firmware MPPT vs dedicated harvester ICs
     (bq25570 / AEM10941 / ADP5091) -- the overhead head-to-head.
  B. Energy-neutrality budget for a duty-cycled power hub over 24 h.
  C. Dispatch: energy-aware scheduling of hub + served devices.

All currents/powers are at the system rail reference (values marked
LIT=literature/datasheet, MEAS=measured in powerpaper/esp32_feas).
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "results"))
os.makedirs(OUT, exist_ok=True)

V = 3.3  # system rail, V

# --- measured ESP32-S3 loop costs (powerpaper/esp32_feas, mode L) ---
T_ADC_RAW_US = 60.0      # MEAS  single 12-bit raw ADC read
T_PID_FLOAT_US = 6.78    # MEAS  float32 velocity-form PID update
T_PWM_US = 4.2           # MEAS  LEDC duty write
T_STEP_US = T_ADC_RAW_US + T_PID_FLOAT_US + T_PWM_US   # ~71 us marginal MPPT step

I_ACTIVE = 35e-3         # ESP32-S3 active (no radio), A  (240 MHz dual core)
I_SLEEP_BOARD = 21e-6    # deep-sleep board floor, A  LIT (17 uA XIAO ... 26 uA PowerFeather midpoint)
I_SLEEP_CHIP = 7e-6      # ESP32-S3 chip deep-sleep typical, A  LIT (datasheet w/ RTC)

# --- dedicated MPPT PMIC quiescent currents (datasheet, LIT) ---
PMIC = {
    "bq25570 (TI)":      0.488e-6,   # full operating quiescent, VSTOR=2.1 V
    "AEM10941 (e-peas)": 0.400e-6,   # LDOs disabled, VBATT 3 V
    "ADP5091 (ADI)":     0.510e-6,   # operating quiescent, SYS pin
}

# --- indoor PV power at 1000 lux (LIT) ---
P_PV_1000LX = {
    "DSC (38%)":      1.87e-3,   # 1000 lux, ~38% indoor efficiency
    "a-Si thin-film": 1.20e-3,   # PowerFilm-class, 0.2-1.9 mW band
    "SCAPS Eg=1.6 cell": 0.55e-3,  # this work, 26% at 0.05 mW/cm^2 white LED
}


def fw_mppt_step_energy():
    """Energy of one firmware MPPT step (single ADC read + PID + PWM)."""
    return V * I_ACTIVE * T_STEP_US * 1e-6


def fw_mppt_tax_watts(period_s):
    """Average control tax of one firmware MPPT perturb per `period_s`."""
    return fw_mppt_step_energy() / period_s


def pmic_tax_watts(iq):
    """Quiescent tax of a dedicated PMIC at the 3.3 V rail."""
    return V * iq


def ic_mppt_period_s():
    """Datasheet MPPT update cadence of the always-on ICs."""
    return {"bq25570": 16.0, "AEM10941": 1.0, "ADP5091": 1.0}


# ---------------- part A: head-to-head ----------------

def part_a():
    periods = np.logspace(np.log10(1.0), np.log10(1000.0), 40)
    fw_tax = [fw_mppt_tax_watts(p) for p in periods]
    ic_bars = {k: pmic_tax_watts(v) for k, v in PMIC.items()}
    # cadence at which firmware MPPT matches the most aggressive IC tax
    cross = {name: {"period": 1.0, "undefined": True} for name in PMIC}
    for name, tax in ic_bars.items():
        for p, t in zip(periods, fw_tax):
            if t <= tax:
                cross[name] = {"period": float(p), "undefined": False}
                break
    r = {
        "e_step_uj": fw_mppt_step_energy() * 1e6,
        "t_step_us": T_STEP_US,
        "fw_tax": {"period_s": periods.tolist(), "uw": [t * 1e6 for t in fw_tax]},
        "ic_bars_uw": {k: v * 1e6 for k, v in ic_bars.items()},
        "cross_period_s": {k: (None if v["undefined"] else v["period"]) for k, v in cross.items()},
    }
    return r


# ---------------- part B: 24 h energy-neutrality budget ----------------

def lux_profile(t_h):
    """Indoor office illuminance over a day (h). Abrupt light on/off at 8/19."""
    if 8.0 <= t_h < 19.0:
        return 1000.0
    if 6.0 <= t_h < 8.0 or 19.0 <= t_h < 20.0:
        return 300.0
    return 50.0


def daily_harvest(p_pv_ref, eta_conv=0.85):
    """Average harvested power over 24 h given P at 1000 lux."""
    H = 96
    dt = 24.0 / H
    vals = []
    for i in range(H):
        t = i * dt
        lux = lux_profile(t)
        vals.append(p_pv_ref * (lux / 1000.0) * eta_conv)
    return float(np.mean(vals)), vals


def hub_consume(I_sleep, duty, I_active_burst, eta_storage=0.95):
    """Average hub current duty-cycled between sleep and active bursts."""
    # energy-based: charge/discharge storage at eta_storage
    return (I_sleep * (1 - duty) + I_active_burst * duty) / eta_storage


def part_b():
    rows = []
    for name, p_pv in P_PV_1000LX.items():
        pavg, _ = daily_harvest(p_pv)
        # max sustainable duty for the board floor (allows duty that consumes exactly pavg)
        for sleep_name, i_sleep in (("board", I_SLEEP_BOARD), ("chip", I_SLEEP_CHIP)):
            # I_active during burst includes radio/serving load
            for i_act in (100e-3, 250e-3, 500e-3):
                duty = (pavg / V) / (i_act - i_sleep)
                duty = min(duty, 1.0)
                rows.append({
                    "pv": name, "sleep": sleep_name, "i_sleep_ua": i_sleep * 1e6,
                    "i_active_ma": i_act * 1e3, "p_avg_uw": pavg * 1e6,
                    "max_duty_pct": duty * 100.0,
                    "wakes_per_hour_100ms": duty * 36000.0,
                })
    return rows


# ---------------- part C: dispatch scheduling ----------------

# Served ring: a BLE/sensor device the hub periodically services.
T_SERVE_MS = 100.0       # hub active window per served event
E_SERVE = V * 100e-3 * T_SERVE_MS * 1e-3   # J per serve event
N_HOURS = 24
BUDGET_MAX_UJ = 18.0e6    # supercap 2 F, 3.0-4.2 V nominal but we use rail 3.3; J = 0.5*C*(dV^2)


def part_c(rows):
    # feasibility vs consultation cadence
    cadences = [1, 5, 15, 30, 60]   # minutes between serves
    res = []
    for cad in cadences:
        serves_per_day = N_HOURS * 60 / cad
        e_day = V * (I_SLEEP_BOARD * (N_HOURS * 3600 - serves_per_day * T_SERVE_MS * 1e-3)
                     + serves_per_day * T_SERVE_MS * 1e-3 * 100e-3 / (I_SLEEP_BOARD * 0 + 1))  # placeholder
        # compute flat: energy = sleep_all_day + serves
        e_sleep = V * I_SLEEP_BOARD * N_HOURS * 3600
        e_serve = serves_per_day * E_SERVE
        e_day = e_sleep + e_serve
        res.append({
            "cadence_min": cad, "serves_per_day": serves_per_day,
            "e_sleep_j": e_sleep, "e_serve_j": e_serve, "e_total_j": e_day,
            "e_total_wh": e_day / 3600.0,
            "e_sleep_us_pct": e_sleep / (e_sleep + e_serve) * 100.0,
            "serves_possible_per_day": servings_daily(),
        })
    return res


def servings_daily():
    """How many 100 ms serve events the DSC harvest alone sustains."""
    pavg, _ = daily_harvest(P_PV_1000LX["DSC (38%)"])
    avail_per_day = pavg * N_HOURS * 3600 * 0.9    # 90% of stored harvest budgeted
    return avail_per_day / E_SERVE


def self_check():
    a = part_a()
    assert abs(a["e_step_uj"] - 3.3 * 35e-3 * 71e-6 * 1e6) < 0.05, a["e_step_uj"]
    assert a["fw_tax"]["uw"][0] > a["ic_bars_uw"]["bq25570 (TI)"]  # 1 s cadence: fw > ic
    assert 3.0 < a["cross_period_s"]["bq25570 (TI)"] < 8.0       # ~5 s crossover
    print("part A self-check OK (step=%.2f uJ, bq25570 crossover ~%.0f s)"
          % (a["e_step_uj"], a["cross_period_s"]["bq25570 (TI)"] or -1))
    for r in part_b():
        assert 0.0 <= r["max_duty_pct"] <= 100.0
        assert r["max_duty_pct"] < 100.0 or r["p_avg_uw"] > 2000.0
    print("part B self-check OK (%d budget rows)" % len(part_b()))
    c = part_c(None)
    # 60-min cadence (c[-1]): sleep dominates; 1-min cadence (c[0]): serving dominates
    assert c[-1]["e_sleep_j"] > c[-1]["e_serve_j"]   # slow cadence = sleep-bound
    assert c[0]["e_sleep_j"] < c[0]["e_serve_j"]     # fast cadence = serve-dominated
    assert servings_daily() > 100
    print("part C self-check OK (dsc day floor %.1f uW avg, serves/day~%.0f)"
          % (daily_harvest(P_PV_1000LX["DSC (38%)"])[0] * 1e6, servings_daily()))


if __name__ == "__main__":
    self_check()
    # dump parts
    data = {"part_a": part_a(), "part_b": part_b(), "part_c": part_c(None),
            "servings_daily": servings_daily()}
    with open(os.path.join(OUT, "energy_model.json"), "w") as f:
        json.dump(data, f, indent=1)
    print("wrote", os.path.join(OUT, "energy_model.json"))