"""Shared device access for the Redragon M998-ULT ("BY TECH Gaming 8K", VID 0x372E)."""
import sys

try:
    # Linux: the default `hid` module uses the libusb backend, which doesn't
    # report usage pages and fights the kernel driver; prefer hidraw.
    import hidraw as hid
except ImportError:
    import hid

VID = 0x372E
PIDS = (0x105F, 0x1060)  # 0x105F = 2.4G dongle/dock, 0x1060 = wired USB
INTERFACE = 2  # vendor interface carrying usage pages 0xFF00 and 0xFF06
TFT_USAGE_PAGE = 0xFF06  # output report 0x09: clock, screen, animation
INFO_USAGE_PAGE = 0xFF00  # feature report 0x03: device info, battery
REPORT_LEN = 64


def find_device(usage_page):
    devs = [d for d in hid.enumerate(VID) if d["product_id"] in PIDS]
    for d in devs:
        if d["usage_page"] == usage_page:
            return d
    # Some backends don't expose usage pages; fall back to the interface number.
    for d in devs:
        if d["interface_number"] == INTERFACE:
            return d
    return None


def open_device(usage_page):
    info = find_device(usage_page)
    if not info:
        print(f"device not found (VID 372E, usage page {usage_page:04X} / "
              f"interface {INTERFACE})", file=sys.stderr)
        for d in hid.enumerate(VID):
            print(f"  seen: pid={d['product_id']:04x} if={d['interface_number']} "
                  f"usage_page={d['usage_page']:04x} path={d['path']}",
                  file=sys.stderr)
        return None
    dev = hid.device()
    dev.open_path(info["path"])
    return dev


def tft_packet(cmd: int, payload: bytes = b"", data_at: int = 5) -> bytes:
    """Build a 64-byte output report 0x09 for the dock (DriverComm::SendTFTFeatureReport).

    [0]=09 [1]=50 [2]=checksum [3]=3A [4]=cmd, payload from byte `data_at`;
    checksum = sum(bytes[3:64]) & 0xFF.
    """
    buf = bytearray(REPORT_LEN)
    buf[0:5] = bytes([0x09, 0x50, 0x00, 0x3A, cmd])
    buf[data_at:data_at + len(payload)] = payload
    buf[2] = sum(buf[3:]) & 0xFF
    return bytes(buf)
