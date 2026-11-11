# 🐱 Bongo Cat for Omarchy

A small bongo cat that sits in your Omarchy bar and drums on the table with its
paws whenever you type, and on the beat when music is playing. Stop typing for
a second and it goes back to its default pose (both paws up).

> Forked from [Samon97/omarchy-bongocat](https://github.com/Samon97/omarchy-bongocat)
> by Deoxizn. This fork adds music beat detection (see below) and renames the
> plugin id to `deoxizn.bongocat`.

![Bongo cat drumming in the bar](https://github.com/Samon97/omarchy-bongocat/raw/main/assets/bongocat.gif)

> **Heads up:** this is an adaptation of the
> [Bongo Cat](https://github.com/kitgore/BongoCat) VS Code extension by
> **pixl-garden**. I rebuilt it as an Omarchy bar widget and borrowed its icon
> font (more on that [below](#credits)).

## What it does

- Drums on every keypress, alternating paws (left down / right down).
- Drums on the beat when music is playing, alternating paws the same way.
- Goes back to its idle pose after ~1 second without typing or beats.
- Fits compactly in the bar — the cat's bottom line lines up with the clock's
  text.
- Reads keypresses locally from `/dev/input/event*` (keyboard devices only —
  no mouse, touchpad, or other input) — no cloud, no editor dependency.

## Install

Install it as an Omarchy plugin straight from GitHub:

```bash
omarchy plugin add https://github.com/Deoxizn/omarchy-bongocat.git --enable
```

Then enable / move it in the bar with:

```bash
omarchy plugin enable deoxizn.bongocat
```

### Requirements

- **Omarchy** (and its Quickshell-based shell)
- **PipeWire with pipewire-pulse** for the music detection: `audio_monitor.py`
  reads the default sink's monitor source with `parec`, which ships with
  PipeWire. No extra setup, no extra packages, and no input-group access
  needed for the audio side. If `parec` is missing the cat still drums on
  keypresses and logs a warning.
- **Read access to keyboard input devices.** The monitor opens only keyboard
  devices (`/dev/input/by-path/*-kbd` and `/dev/input/by-id/*-kbd`, filtered by
  device capabilities) — it never reads mice, touchpads, or other inputs. Those
  keyboards belong to the `input` group, so most setups just work. If nothing
  happens on the first launch, run the one-time setup once:

  ```bash
  sudo ./setup/install.sh
  ```

  It adds your user to the `input` group and installs a udev rule that keeps
  keyboard event devices owned by that group, then reloads and re-applies the
  rules immediately. No need to remember `usermod -aG input` by hand. If your
  current session was started before the group was added, a single log out /
  back in picks it up. Note: this is a deliberate, privileged global-input
  read — review the udev rule before trusting it in a shared/sensitive
  session.
- An **external asset**: the bundled `bongocat.ttf` icon font is a modified
  conversion of the font from the MIT-licensed
  [Bongo Cat](https://github.com/kitgore/BongoCat) VS Code extension by
  pixl-garden (Copyright © 2023 ben). See [Credits](#credits) and
  [`LICENSE`](LICENSE).

## Uninstall

Remove the plugin again with:

```bash
# Disable it in the bar, then remove the plugin folder
omarchy plugin disable deoxizn.bongocat
rm -rf ~/.config/omarchy/plugins/deoxizn.bongocat
```

That's it — the plugin doesn't write any config or state outside its own
folder.

## Repo layout

```
deoxizn.bongocat/
├── manifest.json       # Omarchy manifest (must live in the repo root)
├── BarWidget.qml       # Widget entry point (canvas rendering + logic)
├── key_monitor.py      # Reads keypresses from /dev/input
├── audio_monitor.py    # Reads music beats from the PipeWire monitor source
├── bongocat.ttf        # Bundled icon font (converted from pixl-garden)
├── assets/bongocat.gif # Demo GIF for this README
├── setup/
│   ├── 50-bongocat-input.rules  # udev rule: keyboard devices readable by input group
│   └── install.sh               # One-time privileged setup (adds group + installs rule)
├── LICENSE             # MIT (with a note about the original font)
├── CHANGELOG.md
└── README.md
```

**Note for the repo:** `omarchy plugin add` clones your repo and validates it
directly, so `manifest.json` and the entry point `BarWidget.qml` have to sit in
the **repo root**. Entry points are relative paths, and symlinks aren't
allowed. This flat layout follows the convention of the built-in bar widgets.

## How it works

1. `key_monitor.py` opens keyboard input devices only and prints one line to
   stdout per pressed key (`EV_KEY` event with value 1), coalescing bursts to
   a bounded rate.
2. `audio_monitor.py` reads the default PipeWire sink's monitor source with
   `parec` and prints one line per detected beat (see
   [Music detection](#music-detection)).
3. `BarWidget.qml` runs both scripts as `Process`es, reading stdout through a
   `SplitParser` (one `onRead` per line, immediately discarded). Each line
   calls `drum()`, which switches between "left paw down" and "right paw down" —
   the shell-side buffer stays bounded even for a long-lived process.
4. A `Timer` resets it to the idle pose after ~1 second.
5. The icon glyphs are drawn on a `Canvas`. Instead of the invisible bounding
   box, the *visible* painted outline is centered, and the cat's bottom edge is
   anchored to the bottom of the clock's text line.

## Music detection

`audio_monitor.py` taps the default sink's monitor source, the same audio
you hear, with `parec --raw` (mono 16-bit PCM at 22050 Hz) and runs a small
energy-onset detector over it, all in the standard library:

- Each ~46 ms chunk gets an RMS energy value.
- A beat is a chunk louder than the rolling mean of the last ~1.5 s times
  1.6, with an absolute floor so silence and hiss never trigger.
- A 150 ms refractory period keeps one hit from firing twice.

It is tuned for kick-heavy music, which is where the cat looks best. If a
sink disappears mid-song (Bluetooth drop, server restart) the script waits
two seconds and re-discovers the monitor instead of dying, so the cat picks
the beat back up on its own. If `parec` itself is missing it exits and the
widget logs the warning, keys keep working.

Tuning knobs live at the top of `audio_monitor.py`: `THRESHOLD_FACTOR`
(lower drums more easily), `FLOOR` (higher ignores quiet passages),
`REFRACTORY` (lower allows faster drumming).

## Credits

This is an **adaptation**, not a from-scratch idea. It's based on the
**[Bongo Cat](https://github.com/kitgore/BongoCat)** VS Code extension by
**pixl-garden** (MIT, Copyright © 2023 ben).

What I took from pixl-garden:
- The **cat artwork**, as an icon font. The `bongocat.ttf` here is a
  conversion of the font pixl-garden published (`bongocat.woff`).
- The **behavior**: drum on input with alternating paws, then settle back after
  a pause. That logic comes from their `src/extension.ts` and was reworked for
  Omarchy.

What's new here (my own work):
- The whole Omarchy / Quickshell plugin: `BarWidget.qml` is fresh QML code
  (canvas rendering, process handling, the alignment stuff) written from
  scratch, not copied.
- `key_monitor.py`: a new Linux input reader for `/dev/input`. The original
  extension was pure VS Code status-bar logic and couldn't be reused.
- A small **font fix**: removed a duplicate overlapping outline in the
  "left paw up" glyph that made the mouth look hollow.

So the cat isn't "cloned" — I took pixl-garden's freely MIT-licensed icon font
and built a brand new Omarchy widget around it.

## How AI was involved

This project was made together with an **AI coding assistant**
([opencode](https://opencode.ai)), in an iterative back-and-forth:

- The **AI** designed and wrote most of the QML / Python, ran
  `omarchy plugin validate`, and reloaded the shell as we went.
- The **AI** debugged things like the hollow mouth (traced to the duplicate
  font outline) and fixed the vertical alignment to the clock.
- The **human** (me) judged what it looked like — e.g. deciding the cat should
  line up with the bottom of the clock — and steered the design.

So the behavior, look, and feel were decided together; the coding was mostly
done by the AI, then reviewed and approved by me. See `CHANGELOG.md` and
`LICENSE` for source and licensing details.

## License

MIT — see [`LICENSE`](LICENSE). The bundled icon font comes from the Bongo Cat
extension by pixl-garden (MIT, Copyright © 2023 ben); their license and
copyright are noted in `LICENSE`.
