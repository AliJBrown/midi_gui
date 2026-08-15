"""Builds a tiny Standard MIDI File that silences a stuck device.

aplaymidi has no "panic" flag, and killing it mid-file leaves any held
notes sounding forever. The fix used here is to play a hand-built MIDI
file, through the same aplaymidi/port pipeline already in use, that
sends All Sound Off / All Notes Off / Reset All Controllers on every
channel with zero delta-time between events so it plays instantly.
"""

import struct
from pathlib import Path

_PANIC_CONTROLLERS = (120, 123, 121)  # all sound off, all notes off, reset controllers


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
        status = 0xB0 | channel
        for controller in _PANIC_CONTROLLERS:
            track += _vlq(0) + bytes([status, controller, 0])
    track += _vlq(0) + bytes([0xFF, 0x2F, 0x00])  # end of track

    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, 96)
    track_chunk = b"MTrk" + struct.pack(">I", len(track)) + bytes(track)
    return header + track_chunk


def ensure_panic_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_panic_midi())
    return path
