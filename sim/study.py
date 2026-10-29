"""Synthetic brushing sessions through the firmware logic: detection, latency and false alarms.

ASSUMED INPUTS (placeholders, see README): force profile of brushing, over pressure episodes and short
spikes, force sensor gain, offset, noise and 12 bit quantization, sample rate.
"""
import json, pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import harness

OUT = pathlib.Path(__file__).resolve().parents[1] / "results"
FS = 100                       # sensor rate, Hz
ADC_OFFSET, MN_PER_CNT = 400, 2.0                    # sensor: counts at zero force, mN per count
NOISE_MN = 120.0               # sensor and motor noise, mN rms
F_NORMAL, F_SCRUB = 1500.0, 500.0                    # mean brushing force and scrub oscillation amplitude, mN
F_OVER = 3600.0                # force during an over pressure episode, mN
ON, OFF, IDLE = 3000, 2500, 300                      # warning thresholds, mN
N_SESSIONS, T_SESSION = 40, 120.0                    # sessions and duration, s
SEED = 3

def session(rng):
    t = np.arange(0, T_SESSION, 1 / FS)
    f = F_NORMAL + F_SCRUB * np.sin(2 * np.pi * rng.uniform(2.0, 3.5) * t)
    truth = np.zeros_like(t, dtype=bool); episodes = []
    t0 = 5.0
    while t0 < T_SESSION - 8:
        t0 += rng.uniform(6, 14)
        if t0 > T_SESSION - 5: break
        if rng.random() < 0.6:                        # real over pressure episode, 0.6 to 3 s
            d = rng.uniform(0.6, 3.0); m = (t >= t0) & (t < t0 + d)
            f[m] += F_OVER - F_NORMAL; truth |= m; episodes.append((t0, d))
        else:                                         # short knock or spike, 50 to 150 ms, must not warn
            d = rng.uniform(0.05, 0.15); m = (t >= t0) & (t < t0 + d)
            f[m] += rng.uniform(2500, 4000)
    f += rng.normal(0, NOISE_MN, t.size)
    f[: int(1.5 * FS)] = 0                            # head lifted at the start
    adc = np.clip(np.round(ADC_OFFSET + f / MN_PER_CNT), 0, 4095)
    return t, adc, truth, episodes

def evaluate(states, t, truth, episodes):
    warn = states == 2
    lat, det = [], 0
    for t0, d in episodes:
        idx = np.where(warn & (t >= t0) & (t < t0 + d + 0.5))[0]
        if idx.size: det += 1; lat.append(t[idx[0]] - t0)
    rising = np.where(np.diff(warn.astype(int)) == 1)[0] + 1
    false = sum(1 for i in rising if not truth[max(0, i - 60): i + 1].any())   # no true episode in the last 0.6 s
    return det, lat, false

def main():
    OUT.mkdir(exist_ok=True); harness.build(); rng = np.random.default_rng(SEED)
    designs = {
        "raw threshold": [ADC_OFFSET, int(MN_PER_CNT * 256), 32767, ON, ON, IDLE, 1, 1],
        "filter, hysteresis, debounce": [ADC_OFFSET, int(MN_PER_CNT * 256), int(0.25 * 32768), ON, OFF, IDLE, 25, 20],
    }
    sessions = [session(rng) for _ in range(N_SESSIONS)]
    n_ep = sum(len(s[3]) for s in sessions); minutes = N_SESSIONS * T_SESSION / 60
    res = {}
    for name, cfg in designs.items():
        D, L, F = 0, [], 0
        for t, adc, truth, ep in sessions:
            d, l, f = evaluate(harness.run(cfg, adc), t, truth, ep); D += d; L += l; F += f
        res[name] = dict(episodes=n_ep, detected=D, detection_pct=round(100 * D / n_ep, 1),
                         latency_median_ms=round(1000 * float(np.median(L)), 0) if L else None,
                         latency_p95_ms=round(1000 * float(np.percentile(L, 95)), 0) if L else None,
                         false_alarms=F, false_alarms_per_min=round(F / minutes, 2))
    res["test_minutes"] = minutes
    (OUT / "summary.json").write_text(json.dumps(res, indent=2))
    return res

if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
