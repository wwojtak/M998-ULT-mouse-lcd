#!/usr/bin/env python3
"""Read the battery level of the Redragon M998-ULT mouse.

Protocol recovered from the official Windows tool (Redragon M998 ULT 1.0.0.5,
DriverComm::GetDeviceInfo -> DriverComm::GetFeatureReport, and
DeviceMainDlg::GetMouseData2 which decodes the result):

  Send feature report 0x03 (usage page 0xFF00), 64 bytes:
    [0] 0x03  report id
    [1] checksum = sum(bytes[2:64]) & 0xFF
    [2] 0x50
    [3] 0x00
    [4] 0x02
    [5] 0x4F  command: device info
    [6] 0x80 | chunk  (chunk 0 or 1)
  then read feature report 0x03 back. reply[2] is a status (0 = ok) and
  reply[6:16] holds 10 bytes of device info; the two chunks are concatenated.

  Device info byte 10 (= chunk 1, reply[6]):
    bit 7     charging
    bits 0-6  battery percent
"""
import argparse
import sys
import time

from m998 import INFO_USAGE_PAGE, REPORT_LEN, open_device

REPORT_ID = 0x03


def build_request(block: int, index: int) -> bytes:
    """Feature report 0x03 read request: `03 <sum> 50 00 <block> 4F <index>`."""
    buf = bytearray(REPORT_LEN)
    buf[0] = REPORT_ID
    buf[2:7] = bytes([0x50, 0x00, block, 0x4F, index])
    buf[1] = sum(buf[2:]) & 0xFF
    return bytes(buf)


def read_chunk(dev, chunk: int) -> bytes:
    """Device-info chunk 0 or 1."""
    return read_block(dev, 0x02, 0x80 | chunk)


def read_block(dev, block: int, index: int) -> bytes:
    """Send a read request and return the 64-byte reply; data is reply[6:16]."""
    if dev.send_feature_report(build_request(block, index)) < 0:
        raise OSError("send_feature_report failed")
    time.sleep(0.03)
    reply = bytes(dev.get_feature_report(REPORT_ID, REPORT_LEN))
    if len(reply) < 16:
        raise OSError(f"short reply: {reply.hex(' ')}")
    if reply[2] != 0:
        raise OSError(f"device returned status {reply[2]:#04x}: {reply[:16].hex(' ')}")
    return reply


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", action="store_true", help="also dump raw replies")
    args = ap.parse_args()

    dev = open_device(INFO_USAGE_PAGE)
    if not dev:
        return 1
    try:
        replies = [read_chunk(dev, c) for c in (0, 1)]
    finally:
        dev.close()

    if args.raw:
        for c, r in enumerate(replies):
            print(f"chunk {c}: {r[:16].hex(' ')}")

    data = replies[0][6:16] + replies[1][6:16]
    level = data[10] & 0x7F
    charging = bool(data[10] & 0x80)
    print(f"{level}%{' (charging)' if charging else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
