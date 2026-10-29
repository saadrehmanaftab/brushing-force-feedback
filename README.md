# Brushing force feedback for a smart consumer device (personal project, assumed data)

Personal project. Embedded style C++ logic that watches a force sensor in the head of a handheld
consumer device (for example a power toothbrush) and raises an over pressure warning, plus a Python
test bench that drives the compiled logic with synthetic brushing sessions and scores it.

## Firmware logic (`firmware/`)
- Fixed point integer math, no heap, no exceptions, one `update()` call per sample at 100 Hz.
- ADC counts to force in mN (offset and Q8 gain), first order IIR low pass (Q15), and a three state
  machine: Idle (head off the teeth), Normal, Overpressure.
- Hysteresis (on 3.0 N, off 2.5 N) and debounce counters (25 samples to raise, 20 to clear).
- Built for the host with CMake and `-Wall -Wextra -Werror -fno-exceptions`.

## Test bench (`sim/`, `tests/`)
- `sim/study.py` generates 40 sessions of 2 minutes: brushing at 1.5 N with a 2 to 3.5 Hz scrub
  oscillation, real over pressure episodes (3.6 N, 0.6 to 3 s) and short knocks (50 to 150 ms) that
  must not warn, sensor noise and 12 bit quantization. It compares a raw threshold against the
  filtered, hysteresis and debounce design.
- `tests/test_firmware.py` checks idle detection, debounce timing, spike rejection and that the
  warning does not chatter inside the hysteresis band.

## Assumed inputs (placeholders, not measured device data)
Sample rate 100 Hz · sensor offset 400 counts, 2 mN per count, noise 120 mN rms · brushing force
1.5 N, scrub amplitude 0.5 N · over pressure 3.6 N · warning thresholds 3.0 N on, 2.5 N off.

## Result (`python sim/study.py`, written to `results/summary.json`)
| Design | episodes detected | median latency | p95 latency | false alarms in 80 min |
|---|---|---|---|---|
| raw threshold | 268 of 268 | 5 ms | 10 ms | 149 (1.86 per min) |
| filter, hysteresis, debounce | 268 of 268 | 281 ms | 331 ms | 0 |

The filtered design trades about a quarter of a second of latency for zero false alarms.

## Limits
Synthetic data only, single axis force, no motor current or IMU input, no temperature drift of the
sensor, and no target hardware: the logic is compiled and tested on the host.

## Run
```
pip install numpy pytest
python sim/study.py
pytest -q
```
