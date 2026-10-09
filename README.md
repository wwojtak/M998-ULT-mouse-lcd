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

### Linux permissions

To run without `sudo`, add a udev rule and replug the dongle:

```bash
echo 'SUBSYSTEM=="hidraw", ATTRS{idVendor}=="372e", TAG+="uaccess", MODE="0660"' \
  | sudo tee /etc/udev/rules.d/70-redragon-m998.rules
sudo udevadm control --reload && sudo udevadm trigger
```

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
