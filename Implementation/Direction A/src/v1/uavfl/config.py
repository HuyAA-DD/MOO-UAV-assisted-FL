"""Configuration: SI units; all algorithm comparisons share these settings."""
from copy import deepcopy
from pathlib import Path
import json
import numpy as np

DEFAULT = {
    "data": {"train": 6000, "search": 600, "audit": 600, "test": 1000,
             "partition": "dirichlet", "alpha": 0.5},
    "fl": {"local_steps": 5, "batch_size": 32, "lr": 0.01,
           "search_replicates": 3, "audit_replicates": 10, "threads": 1},
    "search": {"population": 28, "seconds": 30.0, "max_proposals": 10000,
               "neighbors": 8, "neighbor_probability": 0.9, "max_replacements": 2,
               "guided_probability": 0.0, "guided_trials": 16,
               "history_max_age": 30.0, "history_max_drift": 0.1,
               "scales": [2.302585092994046, 1000.0, 5.0],
               "hv_reference": [1.5, 1.0, 1.0], "preference": [1/3, 1/3, 1/3],
               "trace_seconds": 1.0},
    "network": {
        "uav_positions": [[0,0,100],[200,0,100]],
        "client_positions": [[-80,-40,0],[0,40,0],[70,-20,0],
                             [130,50,0],[220,-40,0],[300,30,0]],
        "radius": 350.0, "nmax": 4, "bandwidth": 2e6, "bmin": 5e4,
        "tx_power": 0.1, "noise_psd": 4e-20, "beta0": 1e-4,
        "mac_efficiency": 0.8, "coding_gap": 1.0,
        "fmin": 0.5e9, "fmax": 2e9, "kappa": 1e-28,
        "train_cycles": 1e8, "report_cycles": 1e6,
        "coordinator_down_rate": 20e6, "client_down_rate": 5e6,
        "backhaul_rate": 20e6, "agg_setup": 0.002, "agg_per_client": 0.001,
        "global_agg_setup": 0.002, "global_agg_per_uav": 0.001,
        "client_base": 0.05, "client_rx": 0.05, "uav_base": 5.0,
        "hover_power": 80.0, "uav_rx": 0.2, "uav_tx": 1.0, "uav_agg": 2.0,
        "coordinator_base": 20.0, "coordinator_tx": 2.0,
        "coordinator_rx": 0.5, "coordinator_agg": 5.0,
        "client_battery": 1000.0, "client_reserve": 100.0,
        "uav_battery": 20000.0, "uav_reserve": 2000.0,
        "deadline": 5.0, "sketch_dimension": 64, "metadata_bits": 256
    }
}

def merge(base, update):
    out = deepcopy(base)
    for key, value in update.items():
        if key not in out:
            raise ValueError(f"Unknown config key: {key}")
        if isinstance(out[key], dict):
            out[key] = merge(out[key], value)
        else:
            out[key] = value
    return out

def load_config(path=None):
    cfg = deepcopy(DEFAULT)
    if path:
        cfg = merge(cfg, json.loads(Path(path).read_text(encoding="utf-8")))
    validate(cfg)
    return cfg

def validate(c):
    n, f, s, d = (c[k] for k in ("network","fl","search","data"))
    if not 0 < n["fmin"] <= n["fmax"] or not 0 < n["bmin"] <= n["bandwidth"]:
        raise ValueError("Invalid frequency or bandwidth limits")
    if n["deadline"] <= 0 or n["nmax"] < 1:
        raise ValueError("Invalid constraints")
    for key in ("tx_power","noise_psd","beta0","train_cycles","report_cycles",
                "coordinator_down_rate","client_down_rate","backhaul_rate"):
        if not np.isfinite(n[key]) or n[key] <= 0:
            raise ValueError(f"Invalid positive parameter: {key}")
    if not 0 < n["mac_efficiency"] <= 1 or n["coding_gap"] < 1:
        raise ValueError("Invalid radio efficiency/gap")
    for key in ("client_battery","uav_battery"):
        if n[key] < n[key.replace("battery","reserve")]:
            raise ValueError("Battery below reserve")
    if f["local_steps"] < 1 or f["batch_size"] < 1 or f["lr"] <= 0:
        raise ValueError("Invalid local SGD")
    if min(f["search_replicates"],f["audit_replicates"],f["threads"]) < 1:
        raise ValueError("Invalid replicate/thread count")
    if s["population"] < 4 or s["seconds"] <= 0 or s["max_proposals"] < s["population"]:
        raise ValueError("Invalid search budget")
    if not 0 <= s["guided_probability"] < 1:
        raise ValueError("Keep positive generic exploration probability")
    if not 0 <= s["neighbor_probability"] <= 1 or s["max_replacements"] < 1:
        raise ValueError("Invalid MOEA/D options")
    if len(s["scales"]) != 3 or min(s["scales"]) <= 0:
        raise ValueError("Three positive objective scales required")
    if len(s["hv_reference"]) != 3 or min(s["hv_reference"]) <= 0:
        raise ValueError("Invalid HV reference")
    if len(s["preference"]) != 3 or min(s["preference"]) <= 0:
        raise ValueError("Positive selection preference required")
    if d["partition"] not in ("iid","dirichlet") or d["alpha"] <= 0:
        raise ValueError("Invalid data partition")
    if any(d[k] < 10 or d[k] % 10 for k in ("train","search","audit","test")):
        raise ValueError("Split sizes must be positive multiples of ten")
    if d["train"]+d["search"]+d["audit"] > 60000 or d["test"] > 10000:
        raise ValueError("Split sizes exceed Fashion-MNIST")
