#!/usr/bin/env bash
# Sync the M998-ULT dock clock when the dongle/dock is plugged in, at login and daily
# (the Windows tool syncs only on connect).
# Usage: ./install.sh            install / update
#        ./install.sh uninstall  remove timer, service and udev rule
set -euo pipefail

NAME=mouse-lcd-sync
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UDEV_RULE=/etc/udev/rules.d/70-redragon-m998.rules

if [[ "${1:-}" == "uninstall" ]]; then
    systemctl --user disable --now "$NAME.timer" 2>/dev/null || true
    rm -f "$UNIT_DIR/$NAME.service" "$UNIT_DIR/$NAME.timer"
    systemctl --user daemon-reload
    if [[ -f "$UDEV_RULE" ]]; then
        sudo rm -f "$UDEV_RULE"
        sudo udevadm control --reload
    fi
    echo "uninstalled"
    exit 0
fi

# Python venv with hidapi
if [[ ! -x "$REPO/.venv/bin/python" ]]; then
    python3 -m venv "$REPO/.venv"
fi
"$REPO/.venv/bin/pip" install -q -r "$REPO/requirements.txt"

# udev: let the logged-in user write to the dongle, and start a sync on plug-in.
# Fires once per hidraw node (3); systemd merges the start requests.
RULES='SUBSYSTEM=="hidraw", ATTRS{idVendor}=="372e", TAG+="uaccess", MODE="0660"
ACTION=="add", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="372e", ATTRS{idProduct}=="105f", TAG+="systemd", ENV{SYSTEMD_USER_WANTS}+="'"$NAME"'.service"'
if [[ "$(cat "$UDEV_RULE" 2>/dev/null)" != "$RULES" ]]; then
    echo "$RULES" | sudo tee "$UDEV_RULE" >/dev/null
    sudo udevadm control --reload
    sudo udevadm trigger --subsystem-match=hidraw
fi

mkdir -p "$UNIT_DIR"

cat >"$UNIT_DIR/$NAME.service" <<EOF
[Unit]
Description=Sync Redragon M998-ULT LCD dock clock

[Service]
Type=oneshot
# give a freshly plugged dock a moment to come up
ExecStartPre=/usr/bin/env sleep 2
ExecStart=$REPO/.venv/bin/python $REPO/sync_time.py
EOF

cat >"$UNIT_DIR/$NAME.timer" <<EOF
[Unit]
Description=Sync Redragon M998-ULT LCD dock clock at login and daily

[Timer]
OnStartupSec=10s
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable "$NAME.timer"
systemctl --user restart "$NAME.timer"  # pick up schedule changes
systemctl --user start "$NAME.service" || true

echo
systemctl --user --no-pager list-timers "$NAME.timer"
echo
echo "logs: journalctl --user -u $NAME.service"
