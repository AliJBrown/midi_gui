#!/usr/bin/env python3
"""Touch + keyboard MIDI player GUI for a small Pi screen.

Controls:
  Touch:    tap a file to select it, tap Play / Stop / Refresh / Exit
  Keyboard: Up/Down move the highlighted file, Enter or Space plays
            *whatever is currently highlighted* (no need to click the
            Play button itself), S stops, Q (or the Exit button) quits
"""

import signal
import tkinter as tk
from tkinter import font as tkfont

from config import MIDI_DIR, MIDI_PORT, PANIC_FILE
from panic import ensure_panic_file
from player import MidiPlayer

MIDI_EXTENSIONS = (".mid", ".midi")


class MidiGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Player")
        self.root.configure(bg="black")
        self._closing = False

        # Bypass the window manager entirely instead of relying on its
        # "-fullscreen" support: some lightweight WMs (e.g. openbox on
        # Raspberry Pi OS) reserve space for the panel/taskbar via struts
        # and will resize even a "fullscreen" window once the panel
        # finishes loading, which is what was leaving a strip of desktop
        # visible. overrideredirect makes this window unmanaged, so no
        # panel or desktop can ever push it around; geometry is set to
        # the exact screen size ourselves.
        self._screen_w = self.root.winfo_screenwidth()
        self._screen_h = self.root.winfo_screenheight()
        self.root.overrideredirect(True)
        self.root.geometry(f"{self._screen_w}x{self._screen_h}+0+0")
        self.root.wm_attributes("-topmost", True)

        base_size = max(12, min(28, self._screen_h // 14))
        self.list_font = tkfont.Font(family="Helvetica", size=base_size)
        self.button_font = tkfont.Font(family="Helvetica", size=base_size, weight="bold")
        self.status_font = tkfont.Font(family="Helvetica", size=base_size, weight="bold")

        ensure_panic_file(PANIC_FILE)
        self.player = MidiPlayer(MIDI_PORT, PANIC_FILE, on_state_change=self._on_state_change)

        self.files = []
        self._build_ui()
        self._refresh_files()

        self.root.bind("<Up>", self._move_up)
        self.root.bind("<Down>", self._move_down)
        self.root.bind("<Return>", lambda e: self._play_selected())
        self.root.bind("<space>", lambda e: self._play_selected())
        self.root.bind("s", lambda e: self._stop())
        self.root.bind("S", lambda e: self._stop())
        self.root.bind("q", lambda e: self._quit())
        self.root.bind("Q", lambda e: self._quit())
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        # Key bindings on root only fire while the window actually holds
        # X keyboard focus. A one-time focus_force() isn't enough here:
        # the desktop panel finishing its own startup (which is also what
        # was resizing the window before overrideredirect) can steal
        # focus back afterward, and some window managers are generally
        # reluctant to leave focus on an unmanaged window. Keep
        # reclaiming focus/position/stacking indefinitely rather than
        # gambling on a delay that's "long enough".
        self._keep_on_top()

        # Catch external termination (e.g. `pkill -f app.py`, or systemd
        # stopping the service) and still silence the device instead of
        # leaving a note stuck, same as a normal Exit.
        signal.signal(signal.SIGTERM, self._handle_kill_signal)
        signal.signal(signal.SIGINT, self._handle_kill_signal)

    def _build_ui(self):
        self.status_var = tk.StringVar(value="Stopped")
        status = tk.Label(
            self.root, textvariable=self.status_var, font=self.status_font,
            fg="white", bg="#202020", anchor="w", padx=10, pady=8,
        )
        status.pack(side="top", fill="x")

        # Pack the button bar before the expanding file list: in Tkinter's
        # pack manager, a widget packed with expand=True claims all
        # remaining space at the moment it's packed, so anything packed
        # after it gets squeezed to zero size.
        button_bar = tk.Frame(self.root, bg="black")
        button_bar.pack(side="bottom", fill="x")

        list_frame = tk.Frame(self.root, bg="black")
        list_frame.pack(side="top", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame, font=self.list_font, activestyle="none",
            selectbackground="#3a6ea5", selectforeground="white",
            fg="white", bg="black", bd=0, highlightthickness=0,
            yscrollcommand=scrollbar.set, exportselection=False,
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<Double-Button-1>", lambda e: self._play_selected())

        # Listbox's built-in drag behavior (click, then move) auto-scrolls
        # horizontally once the pointer nears/passes the widget's edge --
        # on a touchscreen even a stationary tap can register as a small
        # drag, which is what causes an unwanted scroll-to-the-right.
        # Tap-to-select doesn't need drag at all, so just disable it.
        self.listbox.bind("<B1-Motion>", lambda e: "break")
        self.listbox.bind("<Button-2>", lambda e: "break")
        self.listbox.bind("<B2-Motion>", lambda e: "break")

        btn_opts = dict(font=self.button_font, height=2, bd=0, highlightthickness=0)
        self.play_btn = tk.Button(button_bar, text="Play", bg="#2f8f4e", fg="white",
                                   command=self._play_selected, **btn_opts)
        self.stop_btn = tk.Button(button_bar, text="Stop", bg="#a13a3a", fg="white",
                                   command=self._stop, **btn_opts)
        self.refresh_btn = tk.Button(button_bar, text="Refresh", bg="#3a3a3a", fg="white",
                                      command=self._refresh_files, **btn_opts)
        self.exit_btn = tk.Button(button_bar, text="Exit", bg="#3a3a3a", fg="white",
                                   command=self._quit, **btn_opts)

        for b in (self.play_btn, self.stop_btn, self.refresh_btn, self.exit_btn):
            b.pack(side="left", fill="both", expand=True)

    def _refresh_files(self):
        MIDI_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(
            (p for p in MIDI_DIR.iterdir() if p.suffix.lower() in MIDI_EXTENSIONS),
            key=lambda p: p.name.lower(),
        )
        self.files = files
        self.listbox.delete(0, tk.END)
        if not files:
            self.listbox.insert(tk.END, f"  (no MIDI files found in {MIDI_DIR})")
            self.listbox.itemconfig(0, fg="#888888")
        else:
            avail_px = self._available_list_px()
            for f in files:
                self.listbox.insert(tk.END, "  " + self._truncate(f.stem, avail_px))
            self.listbox.selection_set(0)
            self.listbox.activate(0)

    def _available_list_px(self):
        # Keep every row narrower than the widget so there's never
        # anything to scroll into horizontally.
        self.root.update_idletasks()
        width = self.listbox.winfo_width()
        if width <= 1:
            width = self.root.winfo_screenwidth() - 40
        return max(width - 20, 60)

    def _truncate(self, text, max_px):
        if self.list_font.measure(text) <= max_px:
            return text
        ellipsis = "…"
        while text and self.list_font.measure(text + ellipsis) > max_px:
            text = text[:-1]
        return text + ellipsis

    def _selected_path(self):
        if not self.files:
            return None
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.files):
            return None
        return self.files[sel[0]]

    def _move_up(self, event):
        self._move_selection(-1)

    def _move_down(self, event):
        self._move_selection(1)

    def _move_selection(self, delta):
        if not self.files:
            return
        cur = self.listbox.curselection()
        idx = cur[0] if cur else 0
        idx = max(0, min(len(self.files) - 1, idx + delta))
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.activate(idx)
        self.listbox.see(idx)

    def _play_selected(self):
        path = self._selected_path()
        if path is not None:
            self.player.play(path)

    def _stop(self):
        self.player.stop()

    def _on_state_change(self, playing, filepath):
        def update():
            if playing and filepath is not None:
                self.status_var.set(f"Playing: {filepath.stem}")
            else:
                self.status_var.set("Stopped")
        self.root.after(0, update)

    def _keep_on_top(self):
        if self._closing:
            return
        self.root.geometry(f"{self._screen_w}x{self._screen_h}+0+0")
        self.root.lift()
        self.root.focus_force()
        self.root.after(1000, self._keep_on_top)

    def _quit(self):
        self._closing = True
        self.player.stop()
        self.root.destroy()

    def _handle_kill_signal(self, signum, frame):
        self._quit()


def main():
    root = tk.Tk()
    MidiGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
