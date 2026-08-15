"""Subprocess wrapper around aplaymidi with a clean, non-stuck stop."""

import subprocess
import threading
from pathlib import Path


class MidiPlayer:
    def __init__(self, port, panic_file, on_state_change=None):
        self.port = port
        self.panic_file = Path(panic_file)
        self.on_state_change = on_state_change  # callback(playing: bool, path | None)
        self._lock = threading.Lock()
        self._process = None
        self._current_file = None

    def is_playing(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def play(self, filepath):
        self.stop()
        proc = subprocess.Popen(
            ["aplaymidi", f"--port={self.port}", str(filepath)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with self._lock:
            self._process = proc
            self._current_file = Path(filepath)
        threading.Thread(target=self._watch, args=(proc,), daemon=True).start()
        self._notify(True, filepath)

    def stop(self):
        with self._lock:
            proc = self._process
            self._process = None
            self._current_file = None

        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        self._send_panic()
        self._notify(False, None)

    def _watch(self, proc):
        proc.wait()
        with self._lock:
            if self._process is proc:
                self._process = None
                self._current_file = None
                finished_naturally = True
            else:
                finished_naturally = False
        if finished_naturally:
            self._notify(False, None)

    def _send_panic(self):
        try:
            subprocess.run(
                ["aplaymidi", f"--port={self.port}", str(self.panic_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
        except Exception:
            pass

    def _notify(self, playing, filepath):
        if self.on_state_change is not None:
            self.on_state_change(playing, filepath)
