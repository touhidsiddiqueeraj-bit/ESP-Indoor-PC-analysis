#!/usr/bin/env python3
"""Capture a Mode D deep-sleep probe run from the ESP32-S3.

Usage: python3 capture_sleep.py [sleep_seconds] [rounds]
Prints CSV,WU rows and appends metrics to results/sleep_probe.json.
Requires: pyserial
"""
import json
import sys
import time

import serial

PORT = "/dev/ttyACM0"
BAUD = 460800

def main():
    sleep_s = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(0.8)
    ser.reset_input_buffer()
    ser.write(f"D{sleep_s}".encode())

    t0 = time.time()
    boots = []
    done = False
    while time.time() - t0 < (sleep_s + 6) * rounds + 10:
        try:
            line = ser.readline().decode(errors="replace").strip()
        except Exception:
            line = ""
        if not line:
            continue
        if line.startswith("CSV,WU"):
            p = line.split(",")
            boots.append((time.time() - t0, float(p[3]), p[2]))
        if line.startswith("CSV,DDONE"):
            done = True
            break

    wlat = [b[1] for b in boots]
    spac = [round(boots[i][0] - boots[i - 1][0], 2) for i in range(1, len(boots))]
    print(f"rounds: {len(boots)} ddone: {done}")
    print(f"wake_latency_ms: {[round(x, 2) for x in wlat]}")
    print(f"round_spacing_s: {spac}")

    result = {
        "device": "esp32-s3-n16r8",
        "wake_cause": 4,  # ESP_SLEEP_WAKEUP_TIMER
        "wake_latency_ms": wlat,
        "round_spacing_s": spac,
        "rounds": len(boots),
        "ddone": done,
    }
    with open("/home/touhid/Documents/esp-indoor-pv/results/sleep_probe.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()