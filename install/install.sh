#!/usr/bin/env bash
# Installs an XDG autostart entry so the MIDI GUI launches fullscreen at
# desktop login, without fighting the user if they close it (unlike a
# systemd service with Restart=always, this just runs once per login).
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"

mkdir -p "$HOME/midi"
mkdir -p "$AUTOSTART_DIR"

sed "s#{{APP_DIR}}#$APP_DIR#g" "$APP_DIR/install/midi-gui.desktop.template" \
    > "$AUTOSTART_DIR/midi-gui.desktop"

echo "Installed autostart entry: $AUTOSTART_DIR/midi-gui.desktop"
echo "Log out and back in (or reboot) to launch it automatically."
echo
echo "Make sure these are installed first:"
echo "  sudo apt install -y python3-tk alsa-utils"
