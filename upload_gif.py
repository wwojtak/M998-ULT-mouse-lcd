#!/usr/bin/env python3
"""Upload a GIF animation to the LCD of the Redragon M998-ULT charging dock.

Protocol recovered from the official Windows tool (Redragon M998 ULT 1.0.0.5,
DeviceMainDlg::SetLCDRGB565Data and BYDUI::LCDViewList::GetImageRGB565Data).
All packets are output report 0x09 framed as `09 50 <sum> 3A <cmd> ...`:

  A0  start   [6]=frame count [8]=frame delay
  A3  data    [5]=frame index [6..7]=chunk index (big endian) [8..63]=56 bytes
  A1  finish  [6]=frame count [8]=frame delay

Frames are 240x135, RGB565 big endian, rows top-down, max 150 frames.
"""
import argparse
import sys
import time

from PIL import Image, ImageSequence

from m998 import TFT_USAGE_PAGE, open_device, tft_packet

WIDTH, HEIGHT = 240, 135
MAX_FRAMES = 150
CHUNK = 56


def load_frames(path, fit):
    im = Image.open(path)
    frames, durations = [], []
    for f in ImageSequence.Iterator(im):
        frames.append(f.convert("RGBA"))
        durations.append(f.info.get("duration", 100) or 100)

    if len(frames) > MAX_FRAMES:
        step = -(-len(frames) // MAX_FRAMES)
        frames = frames[::step]
        durations = [d * step for d in durations[::step]]
        print(f"too many frames, keeping every {step}th ({len(frames)} frames)")

    # pad / fill transparency with the top-left colour, or black if that's transparent
    r, g, b, a = frames[0].getpixel((0, 0))
    bg = (r, g, b) if a else (0, 0, 0)
    out = []
    for f in frames:
        if f.size == (WIDTH, HEIGHT):
            r = f
        elif fit == "stretch":
            r = f.resize((WIDTH, HEIGHT), Image.LANCZOS)
        else:
            scale = (max if fit == "cover" else min)(WIDTH / f.width, HEIGHT / f.height)
            r = f.resize((max(1, round(f.width * scale)), max(1, round(f.height * scale))),
                         Image.LANCZOS)
        canvas = Image.new("RGB", (WIDTH, HEIGHT), bg)
        canvas.paste(r, ((WIDTH - r.width) // 2, (HEIGHT - r.height) // 2), r)
        out.append(canvas)
    return out, round(sum(durations) / len(durations))


def to_rgb565(img):
    buf = bytearray(WIDTH * HEIGHT * 2)
    for i, (r, g, b) in enumerate(img.getdata()):
        v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        buf[2 * i] = v >> 8
        buf[2 * i + 1] = v & 0xFF
    return bytes(buf)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("gif", help="GIF (or any image) to upload")
    ap.add_argument("--fit", choices=("contain", "cover", "stretch"), default="contain",
                    help="how to scale to 240x135 (default: contain, padded with "
                         "the image's top-left colour)")
    ap.add_argument("--delay", type=int,
                    help="frame delay sent to the dock, 1-255 (default: average "
                         "GIF frame duration in ms)")
    ap.add_argument("--packet-sleep", type=float, default=1.0,
                    help="ms to sleep after each packet (default: 1, as the Windows tool)")
    ap.add_argument("--preview", metavar="PNG",
                    help="save the converted frames as a sprite sheet and exit")
    args = ap.parse_args()

    frames, avg_ms = load_frames(args.gif, args.fit)
    delay = max(1, min(255, args.delay or avg_ms))
    print(f"{len(frames)} frames, delay {delay}")

    if args.preview:
        sheet = Image.new("RGB", (WIDTH, HEIGHT * len(frames)))
        for i, f in enumerate(frames):
            sheet.paste(f, (0, i * HEIGHT))
        sheet.save(args.preview)
        print(f"preview written to {args.preview}")
        return 0

    dev = open_device(TFT_USAGE_PAGE)
    if not dev:
        return 1

    sleep = args.packet_sleep / 1000
    n = len(frames)

    def send(pkt):
        if dev.write(pkt) < 0:
            raise OSError("write failed")
        time.sleep(sleep)

    try:
        send(tft_packet(0xA0, bytes([0x00, n, 0x00, delay])))
        for fi, f in enumerate(frames):
            data = to_rgb565(f)
            for ci in range(-(-len(data) // CHUNK)):
                payload = bytes([fi, ci >> 8, ci & 0xFF]) + data[ci * CHUNK:(ci + 1) * CHUNK]
                send(tft_packet(0xA3, payload))
            print(f"\rframe {fi + 1}/{n}", end="", flush=True)
        print()
        send(tft_packet(0xA1, bytes([0x00, n, 0x00, delay])))
    except BaseException:
        # tell the dock the transfer was aborted (cmd A2), like the Windows tool
        dev.write(tft_packet(0xA2))
        raise
    finally:
        dev.close()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
