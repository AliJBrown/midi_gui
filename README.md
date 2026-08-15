# midi_gui

Touch + keyboard GUI for playing MIDI files on a small Raspberry Pi
screen, wrapping `aplaymidi --port=24:0 <file>`.

It solves two problems with running `aplaymidi` by hand on a 3" screen:

- **Discoverability** — lists every `.mid`/`.midi` file in a folder as
  big, tappable rows instead of requiring you to know filenames.
- **Clean stop** — killing `aplaymidi` mid-file leaves the MIDI device
  holding a note forever. Stop (and Play, when switching tracks) now
  also plays a generated "panic" MIDI file through the same port: All
  Sound Off / All Notes Off / Reset Controllers on all 16 channels
  first (instant), followed by an explicit Note Off for all 128 notes
  on all 16 channels as a guaranteed fallback, since Note Off — unlike
  those controller messages — is mandatory in the MIDI spec and every
  device honors it. That full sweep takes ~2-3 seconds to transmit
  over a real MIDI cable, so Stop isn't instant, but it reliably
  silences the device even on hardware that ignores the optional
  controller messages. See [panic.py](panic.py).

## Requirements (on the Pi)

```
sudo apt install -y python3-tk alsa-utils
```

No pip packages are needed — everything else is Python standard library.

## Usage

1. Put your `.mid` / `.midi` files in `~/midi` (or set `MIDI_GUI_DIR`).
2. Confirm your device's ALSA sequencer port with `aconnect -l` — if it's
   not `24:0`, set `MIDI_GUI_PORT` accordingly (this can shift across
   reboots depending on device enumeration order).
3. Run it:

   ```
   python3 app.py
   ```

### Controls

| Action              | Touch                  | Keyboard         |
|---------------------|-------------------------|-------------------|
| Move the highlighted file | Tap a row (selects it directly) | Up / Down |
| Play the highlighted file | Tap **Play** / double-tap row | Enter or Space |
| Stop (clean, no stuck notes, ~2-3s) | Tap **Stop** | S |
| Rescan folder        | Tap **Refresh**          | —                 |
| Toggle fullscreen    | —                        | Escape            |
| Quit (stops playback first) | Tap **Exit**      | Q                 |

There's no separate step to "focus" the Play/Stop buttons from the
keyboard — Enter/Space/S act directly on whatever row is currently
highlighted in the list, bypassing the buttons entirely. Up/Down only
work while the app window has keyboard focus, which it now claims for
itself on launch.

### Config (environment variables)

| Variable            | Default        | Purpose                          |
|----------------------|----------------|-----------------------------------|
| `MIDI_GUI_DIR`        | `~/midi`        | Folder scanned for MIDI files      |
| `MIDI_GUI_PORT`       | `24:0`          | ALSA sequencer port for aplaymidi  |
| `MIDI_GUI_PANIC_FILE` | temp dir        | Where the generated panic file is cached |

## Autostart on boot

Launches fullscreen at desktop login (with a 3s delay before starting,
and a few fullscreen retries after that, so it doesn't lose the race
against the window manager still starting up); closing it (Exit button
or window close) just exits normally — it won't relaunch until the
next login, so you can get to the rest of the desktop when you need to.

```
./install/install.sh
```

Reboot (or log out/in) to see it launch. To remove it:

```
rm ~/.config/autostart/midi-gui.desktop
```
