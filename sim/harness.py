"""Build the firmware for the host and run ADC sample streams through it."""
import pathlib, subprocess, numpy as np
ROOT = pathlib.Path(__file__).resolve().parents[1]
BIN = ROOT / "build" / "pf_host"

def build():
    subprocess.run(["cmake", "-S", str(ROOT), "-B", str(ROOT / "build"), "-DCMAKE_BUILD_TYPE=Release"],
                   check=True, capture_output=True)
    subprocess.run(["cmake", "--build", str(ROOT / "build")], check=True, capture_output=True)
    return BIN

def run(cfg, adc):
    inp = " ".join(str(int(v)) for v in cfg) + "\n" + "\n".join(str(int(a)) for a in adc) + "\n"
    out = subprocess.run([str(BIN)], input=inp, capture_output=True, text=True, check=True).stdout
    return np.array([int(s) for s in out.split()])
