#!/usr/bin/env bash
# Install a systemd user timer that syncs the M998-ULT dock clock every 5 minutes.
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

# udev rule so the logged-in user can write to the dongle's hidraw node
if [[ ! -f "$UDEV_RULE" ]]; then
    echo 'SUBSYSTEM=="hidraw", ATTRS{idVendor}=="372e", TAG+="uaccess", MODE="0660"' \
        | sudo tee "$UDEV_RULE" >/dev/null
    sudo udevadm control --reload
    sudo udevadm trigger --subsystem-match=hidraw
fi

mkdir -p "$UNIT_DIR"

cat >"$UNIT_DIR/$NAME.service" <<EOF
[Unit]
Description=Sync Redragon M998-ULT LCD dock clock

[Service]
Type=oneshot
ExecStart=$REPO/.venv/bin/python $REPO/sync_time.py
EOF

cat >"$UNIT_DIR/$NAME.timer" <<EOF
[Unit]
Description=Sync Redragon M998-ULT LCD dock clock every 5 minutes

[Timer]
OnStartupSec=10s
OnUnitActiveSec=5min
AccuracySec=10s

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now "$NAME.timer"
systemctl --user start "$NAME.service" || true

echo
systemctl --user --no-pager list-timers "$NAME.timer"
echo
echo "logs: journalctl --user -u $NAME.service"
