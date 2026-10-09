#!/usr/bin/env python3
"""Switch the M998-ULT dock screen between its two modes (animation / system).

Packet from DeviceMainDlg::Trd_SetTFTMode: `09 50 <sum> 3A B2 <mode>`. The
Windows UI toggles mode between 0 and 1; which value is which isn't visible
in the code, so try both.
"""
import argparse
import sys

from m998 import TFT_USAGE_PAGE, open_device, tft_packet


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", type=int, choices=(0, 1))
    args = ap.parse_args()

    dev = open_device(TFT_USAGE_PAGE)
    if not dev:
        return 1
    try:
        n = dev.write(tft_packet(0xB2, bytes([args.mode])))
    finally:
        dev.close()
    if n < 0:
        print("write failed", file=sys.stderr)
        return 1
    print(f"screen mode {args.mode} sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
