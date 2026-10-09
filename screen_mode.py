#!/usr/bin/env python3
"""Set which page the M998-ULT dock screen shows at power-up (GIF or date).

Packet from DeviceMainDlg::Trd_SetTFTMode: `09 50 <sum> 3A B2 <mode>`,
mode 1 = GIF animation, 0 = date/clock. Takes effect the next time the dock
is plugged in; the dock's screen button still cycles pages
(GIF -> date -> DPI -> polling rate -> lift-off distance) at any time.
"""
import argparse
import sys

from m998 import TFT_USAGE_PAGE, open_device, tft_packet

MODES = {"gif": 1, "date": 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=[*MODES, "0", "1"],
                    help="startup page: gif (1) or date (0)")
    args = ap.parse_args()
    mode = MODES.get(args.mode, None)
    if mode is None:
        mode = int(args.mode)

    dev = open_device(TFT_USAGE_PAGE)
    if not dev:
        return 1
    try:
        n = dev.write(tft_packet(0xB2, bytes([mode])))
    finally:
        dev.close()
    if n < 0:
        print("write failed", file=sys.stderr)
        return 1
    name = "gif" if mode else "date"
    print(f"startup page set to {name}; takes effect after replugging the dock")
    return 0


if __name__ == "__main__":
    sys.exit(main())
