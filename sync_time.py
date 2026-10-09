#!/usr/bin/env python3
"""Sync the clock on the LCD charging dock of the Redragon M998-ULT
("BY TECH Gaming 8K" dongle, VID 0x372E).

Protocol recovered from the official Windows tool (Redragon M998 ULT 1.0.0.5,
DeviceMainDlg::Trd_SetTimeSyns -> DriverComm::SendTFTFeatureReport):

  HID output report 0x09 on the vendor interface (usage page 0xFF06), 64 bytes:
    [0] 0x09  report id
    [1] 0x50
    [2] checksum = sum(bytes[3:64]) & 0xFF
    [3] 0x3A
    [4] 0xB1  command: time sync
    [5] 0x00
    [6] 0x00
    [7] year - 2000
    [8] month   (1-12)
    [9] day     (1-31)
    [10] hour   (0-23)
    [11] minute
    [12] second
    [13] weekday (0 = Sunday)
    rest zero
"""
import argparse
import datetime
import sys

import hid

VID = 0x372E
PIDS = (0x105F, 0x1060)  # 0x105F = 2.4G dongle/dock, 0x1060 = wired USB
USAGE_PAGE = 0xFF06
REPORT_LEN = 64


def build_packet(t: datetime.datetime) -> bytes:
    buf = bytearray(REPORT_LEN)
    buf[0:5] = bytes([0x09, 0x50, 0x00, 0x3A, 0xB1])
    buf[7] = t.year % 2000
    buf[8] = t.month
    buf[9] = t.day
    buf[10] = t.hour
    buf[11] = t.minute
    buf[12] = t.second
    buf[13] = (t.weekday() + 1) % 7  # Python Mon=0 -> Windows Sun=0
    buf[2] = sum(buf[3:]) & 0xFF
    return bytes(buf)


def find_device():
    for d in hid.enumerate(VID):
        if d["product_id"] in PIDS and d["usage_page"] == USAGE_PAGE:
            return d
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="print packet only")
    args = ap.parse_args()

    now = datetime.datetime.now()
    pkt = build_packet(now)
    print(f"time  : {now:%Y-%m-%d %H:%M:%S %a}")
    print(f"packet: {pkt[:16].hex(' ')} ...")
    if args.dry_run:
        return 0

    info = find_device()
    if not info:
        print("device not found (VID 372E, usage page FF06)", file=sys.stderr)
        return 1

    dev = hid.device()
    dev.open_path(info["path"])
    try:
        n = dev.write(pkt)
    finally:
        dev.close()
    if n < 0:
        print("write failed", file=sys.stderr)
        return 1
    print(f"sent {n} bytes to {info['product_string']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
