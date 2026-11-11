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
- **`evtest` and `cava`** for the two watchers: `sudo pacman -S evtest cava`.
  `evtest` reads the keyboard, `cava` supplies the audio spectrum for beat
  detection. If either is missing, that watcher logs a warning and the other
  side keeps working.
- **Read access to keyboard input devices.** The monitor opens only keyboard
  devices (`/dev/input/by-path/*-kbd` and `/dev/input/by-id/*-kbd`, filtered by
  device capabilities) — it never reads mice, touchpads, or other inputs. Those
  keyboards belong to the `input` group, so most setups just work. If nothing
  happens on the first launch, run the one-time setup once:

  ```bash
  sudo ~/.config/omarchy/plugins/deoxizn.bongocat/setup/install.sh
  ```

  Use the full path: the script lives inside the plugin folder, so `./setup/install.sh`
  only works if you are already standing in it.

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
├── key_monitor.py      # Reads keypresses via evtest
├── audio_monitor.py    # Reads music beats from the cava spectrum
├── cava.conf           # cava config: 16 mono bars as ascii on stdout
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

1. `key_monitor.py` runs `evtest` on each keyboard input device and prints
   one line to stdout per pressed key (`EV_KEY` with value 1, or value 2 for
   a held-key repeat). evtest prints one human-readable line per event, so
   debugging is just `evtest /dev/input/event7` and typing.
2. `audio_monitor.py` runs `cava -p cava.conf` and prints one line per
   detected beat (see [Music detection](#music-detection)).
3. `BarWidget.qml` runs both scripts as `Process`es, reading stdout through a
   `SplitParser` (one `onRead` per line, immediately discarded). Each line
   calls `drum()`, which switches between "left paw down" and "right paw down" —
   the shell-side buffer stays bounded even for a long-lived process.
4. A `Timer` resets it to the idle pose after ~1 second.
5. The icon glyphs are drawn on a `Canvas`. Instead of the invisible bounding
   box, the *visible* painted outline is centered, and the cat's bottom edge is
   anchored to the bottom of the clock's text line.

## Music detection

`audio_monitor.py` runs `cava -p cava.conf`, which prints 16 mono spectrum
bars (low to high) as one ascii line per frame, and runs Noctalia's beat
detector over them, ported from the
[Noctalia bongocat plugin](https://github.com/noctalia-dev/official-plugins/tree/main/bongocat):

- bass = average of the first 8 bars, mid = average of bars 9-16.
- intensity = bass * 0.8 + mid * 0.6, smoothed with alpha 0.75.
- A beat is a rising smoothed intensity past the threshold, with a
  100 ms cooldown so one hit can't fire twice.

cava does the FFT, so the bass is cleanly separated from the rest of the
mix. That is the whole difference from the earlier parec approach, which
measured broadband energy and went deaf on loud, compressed music. The
detector is deliberately trigger-happy, the same as Noctalia's: during a
loud passage the cat drums at the cooldown rate, which is the insane-cat
look. Silence stays silent.

If a sink disappears mid-song the script waits and cava keeps running, so
the cat picks the beat back up on its own. If `cava` itself is missing it
exits and the widget logs the warning, keys keep working.

Tuning knobs live at the top of `audio_monitor.py`: `BEAT_THRESHOLD`
(lower drums more easily), `BEAT_DELTA_THRESHOLD` (lower catches smaller
onsets), `COOLDOWN` (lower allows faster drumming). The cava side is in
`cava.conf`: `bars`, `noise_reduction`, and the input `method` (PipeWire
monitor of the default sink; switch to `pulse` if your cava build lacks
PipeWire support).

Troubleshooting: `cava -p ~/.config/omarchy/plugins/deoxizn.bongocat/cava.conf`
in a terminal shows the raw spectrum lines. If those stay flat while music
plays, cava isn't hearing your sink. `evtest /dev/input/event7` and typing
shows whether your keyboard produces events at all.

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
