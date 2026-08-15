# midi_gui

Touch + keyboard GUI for playing MIDI files on a small Raspberry Pi
screen, wrapping `aplaymidi --port=24:0 <file>`.

It solves two problems with running `aplaymidi` by hand on a 3" screen:

- **Discoverability** — lists every `.mid`/`.midi` file in a folder as
  big, tappable rows instead of requiring you to know filenames.
- **Clean stop** — killing `aplaymidi` mid-file leaves the MIDI device
  holding a note forever. Stop (and Play, when switching tracks) now
  also plays a tiny generated "panic" MIDI file — All Sound Off / All
  Notes Off / Reset Controllers on all 16 channels — through the same
  port, so the device always goes silent immediately. See
  [panic.py](panic.py).

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
| Select a file        | Tap the row              | Up / Down          |
| Play                | Tap **Play** / double-tap row | Enter or Space |
| Stop (clean, no stuck notes) | Tap **Stop**    | S                 |
| Rescan folder        | Tap **Refresh**          | —                 |
| Toggle fullscreen    | —                        | Escape            |
| Quit (stops playback first) | Tap **Exit**      | Q                 |

### Config (environment variables)

| Variable            | Default        | Purpose                          |
|----------------------|----------------|-----------------------------------|
| `MIDI_GUI_DIR`        | `~/midi`        | Folder scanned for MIDI files      |
| `MIDI_GUI_PORT`       | `24:0`          | ALSA sequencer port for aplaymidi  |
| `MIDI_GUI_PANIC_FILE` | temp dir        | Where the generated panic file is cached |

## Autostart on boot

Launches fullscreen at desktop login; closing it (Exit button or window
close) just exits normally — it won't relaunch until the next login, so
you can get to the rest of the desktop when you need to.

```
./install/install.sh
```

Reboot (or log out/in) to see it launch. To remove it:

```
rm ~/.config/autostart/midi-gui.desktop
```
