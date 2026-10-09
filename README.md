# mouse-lcd

Sync the clock on the LCD charging dock of the **Redragon M998-ULT** wireless mouse
(USB dongle shows up as `BY TECH Gaming 8K`, VID `372E`, PID `105F`) from macOS or Linux.
The official software is Windows-only.

## Usage

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python sync_time.py            # sync dock clock to local time
.venv/bin/python sync_time.py --dry-run  # print packet only
```

### Battery level

```bash
.venv/bin/python battery.py        # e.g. "85%" or "85% (charging)"
.venv/bin/python battery.py --raw  # also dump raw device replies
```

Sends feature report `0x03` (usage page `0xFF00`) `03 <sum> 50 00 02 4F 8x 00…`
for chunks `x` = 0, 1 (checksum = sum of bytes 2..63) and reads report `0x03`
back. In the chunk-1 reply, byte 6 holds the battery: bit 7 = charging,
bits 0–6 = percent.

### Firmware versions

```bash
.venv/bin/python firmware.py   # e.g. "2.4G dongle/dock   112"
```

Shows the USB release number (bcdDevice) like the Windows tool does: the
dongle/dock over 2.4G, or the mouse when plugged in by cable. Redragon's OTA
updater (firmware dated 2026-03-03, "version 0052") uses a different version
number read over its own bootloader protocol, so the two can't be compared.
Updating is Windows-only; this tool never writes firmware.

### Custom animation on the dock screen

```bash
.venv/bin/python nyan.py nyan.gif          # (re)build nyan.gif, already included
.venv/bin/python upload_gif.py nyan.gif    # upload it (~1 min for 12 frames)
.venv/bin/python upload_gif.py any.gif --fit cover --preview out.png  # check scaling
.venv/bin/python screen_mode.py 0          # or 1: toggle animation / system screen
```

`upload_gif.py` takes any GIF, scales it to the 240×135 screen
(`--fit contain|cover|stretch`), and uploads up to 150 frames. `nyan.py`
downloads the cat sprite from nyan.cat at run time (artwork © Christopher
Torres; not included here).

Upload protocol (output report `0x09`, framed `09 50 <sum> 3A <cmd> …`):
`A0` start (`[6]`=frames, `[8]`=delay), then per frame `A3` data packets
(`[5]`=frame, `[6..7]`=chunk BE, `[8..63]`=56 bytes of RGB565 BE, rows top-down,
1158 chunks per frame), then `A1` finish (`[6]`=frames, `[8]`=delay). `A2` aborts.
Screen mode: `B2`, `[5]`=0/1.

### Linux permissions

To run without `sudo`, add a udev rule and replug the dongle:

```bash
echo 'SUBSYSTEM=="hidraw", ATTRS{idVendor}=="372e", TAG+="uaccess", MODE="0660"' \
  | sudo tee /etc/udev/rules.d/70-redragon-m998.rules
sudo udevadm control --reload && sudo udevadm trigger
```

## Sync every 5 minutes (systemd, e.g. Arch / CachyOS)

```bash
./install.sh            # venv + udev rule + user timer
./install.sh uninstall  # remove it all
```

Installs a systemd **user** timer (`mouse-lcd-sync.timer`) that runs 10 s after
login and then every 5 minutes. Logs: `journalctl --user -u mouse-lcd-sync.service`.

## Protocol

Recovered from the official Windows tool (`Redragon M998 ULT-1.0.0.5`,
`DeviceMainDlg::Trd_SetTimeSyns` → `DriverComm::SendTFTFeatureReport`).

HID output report `0x09` on the vendor interface (usage page `0xFF06`), 64 bytes:

```
09 50 <sum> 3A B1 00 00 YY MM DD hh mm ss DOW 00 ...
```

| Byte | Value |
|------|-------|
| 0 | `0x09` report ID |
| 1 | `0x50` |
| 2 | checksum: sum of bytes 3..63, mod 256 |
| 3 | `0x3A` |
| 4 | `0xB1` time sync command |
| 7 | year − 2000 |
| 8–12 | month, day, hour, minute, second |
| 13 | weekday, 0 = Sunday |

The device sends no response.
