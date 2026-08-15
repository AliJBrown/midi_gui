#!/usr/bin/env python3
"""Touch + keyboard MIDI player GUI for a small Pi screen.

Controls:
  Touch:    tap a file to select it, tap Play / Stop / Refresh / Exit
  Keyboard: Up/Down move selection, Enter or Space plays, S stops,
            Escape toggles fullscreen, Q (or the Exit button) quits
"""

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

        screen_h = self.root.winfo_screenheight()
        base_size = max(12, min(28, screen_h // 14))
        self.list_font = tkfont.Font(family="Helvetica", size=base_size)
        self.button_font = tkfont.Font(family="Helvetica", size=base_size, weight="bold")
        self.status_font = tkfont.Font(family="Helvetica", size=base_size, weight="bold")

        ensure_panic_file(PANIC_FILE)
        self.player = MidiPlayer(MIDI_PORT, PANIC_FILE, on_state_change=self._on_state_change)

        self.files = []
        self._build_ui()
        self._refresh_files()

        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self._toggle_fullscreen())
        self.root.bind("<Up>", self._move_up)
        self.root.bind("<Down>", self._move_down)
        self.root.bind("<Return>", lambda e: self._play_selected())
        self.root.bind("<space>", lambda e: self._play_selected())
        self.root.bind("s", lambda e: self._stop())
        self.root.bind("S", lambda e: self._stop())
        self.root.bind("q", lambda e: self._quit())
        self.root.bind("Q", lambda e: self._quit())
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    def _build_ui(self):
        self.status_var = tk.StringVar(value="Stopped")
        status = tk.Label(
            self.root, textvariable=self.status_var, font=self.status_font,
            fg="white", bg="#202020", anchor="w", padx=10, pady=8,
        )
        status.pack(side="top", fill="x")

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

        button_bar = tk.Frame(self.root, bg="black")
        button_bar.pack(side="bottom", fill="x")

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
            for f in files:
                self.listbox.insert(tk.END, "  " + f.stem)
            self.listbox.selection_set(0)
            self.listbox.activate(0)

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

    def _toggle_fullscreen(self):
        is_full = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not is_full)

    def _quit(self):
        self.player.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    MidiGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
