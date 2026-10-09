#!/usr/bin/env python3
"""Build a 240x135 Nyan Cat scene (sky, rainbow, stars) for the dock screen.

The cat sprite is downloaded from nyan.cat at run time (artwork (c) Christopher
Torres) and is not stored in this repo. Output loops seamlessly in 12 frames.

    .venv/bin/python nyan.py nyan.gif && .venv/bin/python upload_gif.py nyan.gif
"""
import argparse
import io
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageSequence

SPRITE_URL = "https://www.nyan.cat/cats/original.gif"
W, H = 240, 135
PX = 4  # screen pixels per art pixel
SKY = (0, 51, 102)
RAINBOW = [(255, 0, 0), (255, 153, 0), (255, 255, 0),
           (51, 255, 0), (0, 153, 255), (102, 51, 255)]
STAR = (255, 255, 255)


def load_sprite():
    req = urllib.request.Request(SPRITE_URL, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=30).read()
    im = Image.open(io.BytesIO(data))
    frames = []
    for f in ImageSequence.Iterator(im):
        f = f.convert("RGBA")
        # source is drawn at 8 px per art pixel: sample back to 1:1, then scale up
        small = f.resize((f.width // 8, f.height // 8), Image.NEAREST)
        frames.append(small.resize((small.width * PX, small.height * PX), Image.NEAREST))
    return frames, im.info.get("duration", 70)


def draw_star(d, x, y, stage):
    p = PX
    if stage == 0:
        d.rectangle([x, y, x + p - 1, y + p - 1], fill=STAR)
        return
    r = stage  # arm length in art pixels
    for i in range(1, r + 1):
        if stage == 3 and i == 1:
            continue  # hollow centre on the largest stage
        for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
            d.rectangle([x + dx * p, y + dy * p, x + dx * p + p - 1, y + dy * p + p - 1],
                        fill=STAR)
    if stage < 3:
        d.rectangle([x, y, x + p - 1, y + p - 1], fill=STAR)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", nargs="?", default="nyan.gif")
    args = ap.parse_args()

    cats, duration = load_sprite()
    n = len(cats)
    cw, ch = cats[0].size
    cx, cy = W - cw - 8, (H - ch) // 2
    band = 3 * PX  # stripe height
    rb_top = cy + (ch - band * len(RAINBOW)) // 2
    seg = 8 * PX  # rainbow wave segment width

    # (x, y, stage offset); stars scroll left by W over one loop
    stars = [(20, 12, 0), (150, 20, 2), (90, 110, 1), (210, 100, 3), (60, 60, 4), (180, 4, 5)]
    speed = W // n

    frames = []
    for i in range(n):
        im = Image.new("RGB", (W, H), SKY)
        d = ImageDraw.Draw(im)
        for sx, sy, so in stars:
            x = (sx - i * speed) % W
            stage = (i + so) % 6
            draw_star(d, x, sy, stage if stage < 4 else 6 - stage)
        wave = (i // 2) % 2
        for s, x0 in enumerate(range(cx + 6 * PX, 0, -seg)):
            dy = PX if (s + wave) % 2 else 0
            for k, col in enumerate(RAINBOW):
                y0 = rb_top + dy + k * band
                d.rectangle([max(0, x0 - seg), y0, x0 - 1, y0 + band - 1], fill=col)
        im.paste(cats[i], (cx, cy), cats[i])
        frames.append(im)

    frames[0].save(args.out, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0)
    print(f"wrote {args.out}: {n} frames, {W}x{H}, {duration} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
