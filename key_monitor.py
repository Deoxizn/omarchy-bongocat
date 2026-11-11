#!/usr/bin/env python3
"""Key monitor for the Bongo Cat bar widget, Noctalia-style.

Runs `evtest` on every keyboard device and prints one blank line per
keypress. evtest prints one human-readable line per input event, so unlike
a raw evdev reader this is trivially debuggable: run
`evtest /dev/input/event7`, type, and watch the lines.

Same deal as before: keyboard devices only, found via the udev -kbd
symlinks. Requires `evtest` and read access to the keyboard devices
(user in the `input` group, or a fresh login after setup/install.sh).
"""
import glob
import os
import select
import shutil
import subprocess
import sys


def evtest_cmd(device):
    # evtest block-buffers when its stdout is a pipe, which would deliver
    # keypresses in bursts. stdbuf forces line buffering so every event
    # arrives as it happens.
    if shutil.which("stdbuf") is not None:
        return ["stdbuf", "-oL", "evtest", device]
    return ["evtest", device]


def is_key_hit(line):
    # evtest prints one line per event, e.g.:
    #   Event: time 1700.0, type 1 (EV_KEY), code 57 (KEY_SPACE), value 1
    # value 1 = press, value 2 = repeat (held key). value 0 = release.
    if "EV_KEY" not in line or "BTN_TOOL_" in line:
        return False
    return "value 1" in line or "value 2" in line


def main():
    if shutil.which("evtest") is None:
        print("key_monitor: evtest not found (sudo pacman -S evtest)",
              file=sys.stderr)
        return 1

    devices = []
    for pattern in ("/dev/input/by-path/*-kbd", "/dev/input/by-id/*-kbd"):
        for path in glob.glob(pattern):
            real = os.path.realpath(path)
            if real not in devices:
                devices.append(real)
    if not devices:
        print("key_monitor: no keyboard devices found", file=sys.stderr)
        return 1

    procs = []
    for dev in devices:
        try:
            p = subprocess.Popen(evtest_cmd(dev), stdout=subprocess.PIPE,
                                 text=True)
        except OSError as e:
            print(f"key_monitor: cannot start evtest on {dev}: {e}",
                  file=sys.stderr)
            continue
        procs.append((dev, p))
    if not procs:
        print("key_monitor: could not start evtest on any keyboard",
              file=sys.stderr)
        return 1

    print("key_monitor: reading " + ", ".join(d for d, _ in procs),
          file=sys.stderr)

    streams = {p.stdout: p for _, p in procs}
    while streams:
        try:
            readable, _, _ = select.select(list(streams), [], [], 0.5)
        except (OSError, ValueError):
            return 0
        for stream in readable:
            line = stream.readline()
            if not line:
                streams.pop(stream, None)
                continue
            if is_key_hit(line):
                sys.stdout.write("\n")
                sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
