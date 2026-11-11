#!/usr/bin/env python3
"""Beat monitor for the Bongo Cat bar widget, Noctalia-style.

Runs `cava` in raw-output mode and feeds its spectrum frames through
Noctalia's beat detector. cava does the FFT, so the bass is cleanly
separated from the rest of the mix instead of approximated with a
low-pass. Requires `cava` (sudo pacman -S cava); no other setup.

Beat logic, ported from Noctalia's bongocat plugin:
- 16 mono bars, low to high. sub-bass = avg of the first 4, bass = avg of
  the first 8, mid = avg of bars 9-16.
- intensity = bass * 0.8 + mid * 0.6, smoothed with alpha 0.75.
- a beat is a rising smoothed intensity past the threshold, with a
  ~100 ms cooldown so one hit can't fire twice.
"""
import os
import shutil
import subprocess
import sys
import time

BARS = 16
BEAT_THRESHOLD = 0.07
BEAT_DELTA_THRESHOLD = 0.014
COOLDOWN = 0.1  # seconds between beats
SMOOTH_ALPHA = 0.75


def average(values, first, last):
    vals = values[first - 1:last]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def main():
    if shutil.which("cava") is None:
        print("audio_monitor: cava not found (sudo pacman -S cava)",
              file=sys.stderr)
        return 1
    here = os.path.dirname(os.path.abspath(__file__))
    config = os.path.join(here, "cava.conf")
    proc = subprocess.Popen(["cava", "-p", config],
                            stdout=subprocess.PIPE, text=True)
    smoothed = 0.0
    previous = 0.0
    last_beat = 0.0
    while True:
        line = proc.stdout.readline()
        if not line:
            return 1
        try:
            values = [int(v) / 1000.0
                      for v in line.strip().split(";") if v != ""]
        except ValueError:
            continue
        if len(values) < BARS:
            continue
        bass = average(values, 1, 8)
        mid = average(values, 9, 16)
        intensity = bass * 0.8 + mid * 0.6
        previous = smoothed
        smoothed = SMOOTH_ALPHA * intensity + (1 - SMOOTH_ALPHA) * smoothed
        delta = smoothed - previous
        is_beat = ((delta > BEAT_DELTA_THRESHOLD
                    and smoothed > BEAT_THRESHOLD * 0.5)
                   or (smoothed > BEAT_THRESHOLD and delta > 0))
        now = time.monotonic()
        if is_beat and now - last_beat >= COOLDOWN:
            last_beat = now
            sys.stdout.write("\n")
            sys.stdout.flush()


if __name__ == "__main__":
    sys.exit(main())
