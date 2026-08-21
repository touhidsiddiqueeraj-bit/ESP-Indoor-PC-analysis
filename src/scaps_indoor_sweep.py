import re
import sys
import json
import numpy as np

sys.path.insert(0, "/home/touhid/scaps-runner/src")
from scaps_runner import SCAPSrunner, parse_jv_curve
from scaps_runner.script_gen import from_param_dict

SPECTRUM = "white 400-800.spe"


def input_proc(params):
    cmd = from_param_dict(params)
    if "spectrum" in params:
        cmd = re.sub(
            r"(load definitionfile \S+\n)",
            r"\1action spectrum_defined fromfile\n"
            rf"action spectrumfile {SPECTRUM}\n",
            cmd,
            count=1,
        )
    return cmd


def output_proc(path):
    raw = open(path).read()
    J, V = None, None
    try:
        J, V = parse_jv_curve(path)
    except Exception as e:
        print(f"  jv parse failed: {e}", file=sys.stderr)
    m = {}
    for key in ("Voc", "Jsc", "FF", "eta", "Vmpp", "Jmpp", "Pmpp"):
        r = re.search(rf"^\s*{key}\s*=\s*([-\d.Ee+]+)", raw, re.M)
        if r:
            m[key] = float(r.group(1))
    return {"J": J.tolist() if J is not None else None,
            "V": V.tolist() if V is not None else None, "params": m}


chi_0, Eg_0 = 3.9, 1.55
Egs = [1.6, 1.7, 1.8, 1.9, 2.0, 2.1]
INTENSITY = 0.05  # mW/cm^2, indoor order (~500 lux)

inputs = {}
for i, Eg in enumerate(Egs):
    chi = chi_0 + 0.5 * (Eg - Eg_0)
    inputs[f"Eg{Eg:.1f}"] = {
        "load": "perovskite-mapi.def",
        "set": {"layer2.Eg": Eg, "layer2.chi": chi},
        "workingpoint": {"temperature": 300, "illumination": INTENSITY},
        "iv": {"start": 0, "stop": min(1.4, 0.9 * Eg), "step": 0.01},
        "spectrum": SPECTRUM,
    }

r = SCAPSrunner(input_proc, output_proc, ncores=4)
r.sync_parameters()
out = r.run_inputs(inputs)

results = {}
for k, v in out.items():
    results[k] = v
    try:
        print(f"{k}: params={v['params']}")
    except Exception:
        pass

with open("/home/touhid/Documents/esp-indoor-pv/results/scaps_indoor.json", "w") as f:
    json.dump(results, f)
print("saved", "/home/touhid/Documents/esp-indoor-pv/results/scaps_indoor.json")