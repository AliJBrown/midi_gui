"""Builds a tiny Standard MIDI File that silences a stuck device.

aplaymidi has no "panic" flag, and killing it mid-file leaves any held
notes sounding forever. The fix used here is to play a hand-built MIDI
file, through the same aplaymidi/port pipeline already in use, that
silences every channel.

All Sound Off / All Notes Off / Reset All Controllers (CC 120/123/121)
are sent first since they're cheap and instant, but they're optional
per the MIDI spec and plenty of hardware synth modules don't fully
implement them. Note Off is not optional -- every MIDI device must
support it -- so an explicit Note Off for all 128 notes on all 16
channels follows as a guaranteed fallback. That sweep is a few
thousand bytes, which over a real 31250-baud MIDI cable takes roughly
2 seconds to transmit; see player.py's panic timeout.
"""

import struct
from pathlib import Path

_PANIC_CONTROLLERS = (120, 123, 121, 64)  # all sound off, all notes off, reset, sustain off


def _vlq(n: int) -> bytes:
    buf = [n & 0x7F]
    n >>= 7
    while n:
        buf.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(buf))


def build_panic_midi() -> bytes:
    track = bytearray()
    for channel in range(16):
        cc_status = 0xB0 | channel
        for controller in _PANIC_CONTROLLERS:
            track += _vlq(0) + bytes([cc_status, controller, 0])

        note_off_status = 0x80 | channel
        for note in range(128):
            track += _vlq(0) + bytes([note_off_status, note, 0])

    track += _vlq(0) + bytes([0xFF, 0x2F, 0x00])  # end of track

    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, 96)
    track_chunk = b"MTrk" + struct.pack(">I", len(track)) + bytes(track)
    return header + track_chunk


def ensure_panic_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_panic_midi())
    return path
