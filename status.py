#!/usr/bin/env python3
"""Show the current state and settings of the Redragon M998-ULT.

Read-only. Layout recovered from DeviceMainDlg::GetMouseData2 in the official
Windows tool (Redragon M998 ULT 1.0.0.5):

  device info: 2 reads, block 0x02, index 0x80+i -> 20 bytes
    [0..1] protocol version   [2..7] device id   [8] work mode  [9] connection
    [10] bit7 charging, bits0-6 battery %
    [11] low nibble current profile, high nibble profile count
    [12] max polling rate index  [13] sensor  [14..15] max DPI (BE)

  config: 6 reads, block 0x0A+i, index 0x40+i -> 60 bytes
    [0] DPI range (2 = up to 30000)
    [1] low 3 bits wireless polling rate index, high nibble wired index
    [2] high nibble DPI stage (1-based), low nibble stage count
    [3] lift-off height   [4] button response time (debounce)
    [5] sensor flags (bits 6-7 e-sports mode)   [8] sleep
    [11..26] 8 DPI stages, little endian u16 v -> DPI = (v + 1) * 50
    [27..50] 8 DPI stage colours, R G B
"""
import argparse
import sys

from battery import read_block, read_chunk
from m998 import INFO_USAGE_PAGE, open_device

RATES = [125, 250, 500, 1000, 2000, 4000, 8000]


def rate(i):
    return f"{RATES[i]} Hz" if 0 <= i < len(RATES) else f"? (index {i})"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", action="store_true", help="also dump raw info/config bytes")
    args = ap.parse_args()

    dev = open_device(INFO_USAGE_PAGE)
    if not dev:
        return 1
    try:
        info = b"".join(read_chunk(dev, c)[6:16] for c in (0, 1))
        cfg = b"".join(read_block(dev, 0x0A + i, 0x40 + i)[6:16] for i in range(6))
    finally:
        dev.close()

    if args.raw:
        print(f"info  : {info.hex(' ')}")
        for i in range(0, len(cfg), 20):
            print(f"cfg {i:2}: {cfg[i:i + 20].hex(' ')}")
        print()

    level, charging = info[10] & 0x7F, bool(info[10] & 0x80)
    profile, profiles = info[11] & 0x0F, info[11] >> 4
    stage, stages = (cfg[2] >> 4) - 1, cfg[2] & 0x0F

    dpis, colours = [], []
    for k in range(8):
        v = cfg[11 + 2 * k] | cfg[12 + 2 * k] << 8
        dpis.append((v + 1) * 50)
        colours.append(cfg[27 + 3 * k:30 + 3 * k])

    print(f"battery        {level}%{' (charging)' if charging else ''}")
    print(f"profile        {profile + 1} of {profiles}")
    print(f"polling rate   {rate(cfg[1] & 0x07)} wireless, {rate(cfg[1] >> 4)} wired "
          f"(max {rate(info[12])})")
    print(f"DPI            {dpis[stage] if 0 <= stage < 8 else '?'} "
          f"(stage {stage + 1} of {stages})")
    for k in range(min(stages, 8)):
        mark = "*" if k == stage else " "
        print(f"  {mark} stage {k + 1}    {dpis[k]:>5}  #{colours[k].hex()}")
    print(f"lift-off       {cfg[3]}")
    print(f"debounce       {cfg[4]}")
    print(f"sleep          {cfg[8]}")
    print(f"sensor flags   {cfg[5]:#04x} (e-sports mode {cfg[5] >> 6})")
    print(f"sensor         {info[13]:#04x}, max DPI {info[14] << 8 | info[15]}")
    print(f"protocol       {info[0] << 8 | info[1]:x}, device id {info[2:8].hex()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
