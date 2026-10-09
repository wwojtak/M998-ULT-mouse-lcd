#!/usr/bin/env python3
"""Show firmware versions of the Redragon M998-ULT dongle/dock (and mouse when wired).

The Windows tool (DriverComm::GetCuDeviceVersion) shows the USB release number
(bcdDevice) of the connected device in hex: the 2.4G dongle/dock (PID 105F),
or the mouse itself when plugged in by cable (PID 1060).

Latest known firmware comes from Redragon's OTA updater
("Redragon_M998-ULT _software_OTATool_bootV10_1.exe", config.json:
pid 105f, version 0052, firmware.bin dated 2026-03-03).
"""
import sys

from battery import read_chunk
from m998 import INFO_USAGE_PAGE, PIDS, VID, hid, open_device

NAMES = {0x105F: "2.4G dongle/dock", 0x1060: "mouse (wired)"}
LATEST = {0x105F: 0x0052}


def main():
    seen = {}
    for d in hid.enumerate(VID):
        if d["product_id"] in PIDS:
            seen[d["product_id"]] = d["release_number"]
    if not seen:
        print("device not found (VID 372E)", file=sys.stderr)
        return 1

    for pid, ver in sorted(seen.items()):
        line = f"{NAMES[pid]:<18} {ver:x}"
        latest = LATEST.get(pid)
        if latest is not None:
            if ver >= latest:
                line += "  (up to date)"
            else:
                line += f"  (update available: {latest:x})"
        print(line)

    dev = open_device(INFO_USAGE_PAGE)
    if dev:
        try:
            info = read_chunk(dev, 0)[6:16]
            print(f"{'protocol version':<18} {info[0] << 8 | info[1]:x}")
        except OSError as e:
            print(f"protocol version: unavailable ({e})", file=sys.stderr)
        finally:
            dev.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
