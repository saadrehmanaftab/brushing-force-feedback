import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "sim"))
import harness

CFG = [400, 512, 8192, 3000, 2500, 300, 25, 20]   # offset, 2 mN per count (Q8), alpha 0.25, thresholds, debounce
harness.build()

def adc(f_mN):
    return np.round(400 + np.asarray(f_mN) / 2.0)

def test_idle_until_head_on_teeth():
    s = harness.run(CFG, adc([0] * 50 + [1500] * 50))
    assert (s[:50] == 0).all() and s[-1] == 1

def test_step_raises_warning_after_debounce():
    s = harness.run(CFG, adc([1500] * 100 + [3600] * 100))
    first = int(np.argmax(s == 2))
    assert 100 + 25 <= first <= 100 + 40                 # filter rise plus 25 sample debounce

def test_short_spike_is_ignored():
    s = harness.run(CFG, adc([1500] * 100 + [5000] * 15 + [1500] * 100))
    assert not (s == 2).any()

def test_no_chatter_inside_hysteresis_band():
    f = [3600] * 100 + list(2750 + 200 * np.sin(np.linspace(0, 20 * np.pi, 400)))
    s = harness.run(CFG, adc([1500] * 50 + f))
    warn = (s == 2).astype(int)
    assert np.sum(np.diff(warn) == 1) == 1 and warn[-1] == 1   # raised once, held in the band
