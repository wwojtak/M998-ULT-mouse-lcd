#!/usr/bin/env python3
"""Show firmware versions of the Redragon M998-ULT dongle/dock (and mouse when wired).

The Windows tool (DriverComm::GetCuDeviceVersion) shows the USB release number
(bcdDevice) of the connected device in hex: the 2.4G dongle/dock (PID 105F),
or the mouse itself when plugged in by cable (PID 1060).

This is NOT the version Redragon's OTA updater checks: the updater
("Redragon_M998-ULT _software_OTATool_bootV10_1.exe") reads and writes its own
firmware version over a separate GeeHy bootloader protocol. Its bundled
firmware (config.json: pid 105f, version 0052, firmware.bin dated 2026-03-03)
can't be compared with the USB release number shown here.
"""
import sys

from battery import read_chunk
from m998 import INFO_USAGE_PAGE, PIDS, VID, hid, open_device

NAMES = {0x105F: "2.4G dongle/dock", 0x1060: "mouse (wired)"}


def main():
    seen = {}
    for d in hid.enumerate(VID):
        if d["product_id"] in PIDS:
            seen[d["product_id"]] = d["release_number"]
    if not seen:
        print("device not found (VID 372E)", file=sys.stderr)
        return 1

    for pid, ver in sorted(seen.items()):
        print(f"{NAMES[pid]:<18} {ver:x}")

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
