#!/usr/bin/env python3
"""Beat monitor for the Bongo Cat bar widget.

Reads whatever is currently playing through the default PipeWire sink's
monitor source (`parec`, which ships with pipewire-pulse, so no new
packages), runs a small energy-onset beat detector over the raw PCM, and
prints one blank line per detected beat. The widget treats each line as a
drum hit, exactly like a keypress from key_monitor.py.

Detector: RMS energy per ~46 ms chunk against a rolling mean of the last
~1.5 s. A beat is an energy spike above the rolling mean times a factor,
with an absolute floor so silence and background hiss never trigger, and a
short refractory period so one hit can't fire twice. Tuned for kick-heavy
music; a quiet acoustic track still drums, just less often.
"""
import math
import shutil
import struct
import subprocess
import sys
import time

RATE = 22050
CHUNK_SAMPLES = 1024  # ~46 ms per chunk at 22050 Hz
CHUNK_BYTES = CHUNK_SAMPLES * 2  # s16le mono
REFRACTORY = 0.15  # min seconds between beats
THRESHOLD_FACTOR = 1.6  # beat when RMS > rolling mean * this
FLOOR = 0.02  # absolute RMS floor; silence stays silent
WINDOW = 32  # chunks of history (~1.5 s)
RETRY_DELAY = 2.0  # seconds between parec respawn attempts


def default_monitor():
    """Name of the default sink's monitor source, or None."""
    sink = ""
    try:
        sink = subprocess.check_output(
            ["pactl", "get-default-sink"], text=True, timeout=5
        ).strip()
    except Exception:
        pass
    if sink:
        return sink + ".monitor"
    try:
        out = subprocess.check_output(
            ["pactl", "list", "short", "sinks"], text=True, timeout=5
        )
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                return parts[1] + ".monitor"
    except Exception:
        pass
    return None


def rms(chunk):
    samples = struct.unpack("<%dh" % (len(chunk) // 2), chunk)
    total = 0.0
    for s in samples:
        total += s * s
    return math.sqrt(total / len(samples)) / 32768.0


def watch(monitor):
    """Stream parec and emit one line per beat. Returns when the stream ends."""
    proc = subprocess.Popen(
        ["parec", "--device", monitor, "--raw", "--format=s16le",
         "--rate=%d" % RATE, "--channels=1"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    history = []
    last_beat = 0.0
    try:
        while True:
            chunk = proc.stdout.read(CHUNK_BYTES)
            if not chunk or len(chunk) < CHUNK_BYTES:
                return
            energy = rms(chunk)
            history.append(energy)
            if len(history) > WINDOW:
                history.pop(0)
            mean = sum(history) / len(history)
            now = time.monotonic()
            if (energy > max(mean * THRESHOLD_FACTOR, FLOOR)
                    and now - last_beat >= REFRACTORY):
                last_beat = now
                sys.stdout.write("\n")
                sys.stdout.flush()
    finally:
        proc.kill()


def main():
    # parec missing means PipeWire's PulseAudio layer isn't there; nothing
    # will fix that at runtime, so fail loud and let the widget log it.
    if shutil.which("parec") is None:
        print("audio_monitor: parec not found (install pipewire-pulse)",
              file=sys.stderr)
        return 1
    # A dead stream (sink unplugged, server restarted) is transient: wait and
    # try again with a freshly discovered monitor instead of dying.
    while True:
        monitor = default_monitor()
        if monitor is None:
            print("audio_monitor: no default sink found (is PipeWire running?)",
                  file=sys.stderr)
            time.sleep(RETRY_DELAY)
            continue
        watch(monitor)
        time.sleep(RETRY_DELAY)


if __name__ == "__main__":
    sys.exit(main())
