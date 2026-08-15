import os
import tempfile
from pathlib import Path

# Directory scanned for .mid / .midi files. Override with MIDI_GUI_DIR.
MIDI_DIR = Path(os.environ.get("MIDI_GUI_DIR", str(Path.home() / "midi"))).expanduser()

# ALSA sequencer port passed to aplaymidi, e.g. "24:0". Override with MIDI_GUI_PORT
# if `aconnect -l` shows your device on a different client:port after a reboot.
MIDI_PORT = os.environ.get("MIDI_GUI_PORT", "24:0")

# Where the generated MIDI-panic file is cached. Regenerated on every launch.
PANIC_FILE = Path(os.environ.get(
    "MIDI_GUI_PANIC_FILE", str(Path(tempfile.gettempdir()) / "midi_gui_panic.mid")
))
