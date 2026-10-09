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

from m998 import TFT_USAGE_PAGE, open_device, tft_packet


def build_packet(t: datetime.datetime) -> bytes:
    return tft_packet(0xB1, bytes([
        0x00, 0x00,
        t.year % 2000, t.month, t.day,
        t.hour, t.minute, t.second,
        (t.weekday() + 1) % 7,  # Python Mon=0 -> Windows Sun=0
    ]))


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

    dev = open_device(TFT_USAGE_PAGE)
    if not dev:
        return 1
    try:
        n = dev.write(pkt)
    finally:
        dev.close()
    if n < 0:
        print("write failed", file=sys.stderr)
        return 1
    print(f"sent {n} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
