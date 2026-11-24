#!/usr/bin/env python3
"""The World in One Day - 23 November 2026.

A pure-standard-library newspaper front page generator.
Draws one 1024x1024 PNG summing up the world news of Monday
23 November 2026 and writes it to the make.fun output directory.
No network, no third-party packages, fully deterministic.
"""
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (244, 238, 221)
INK = (20, 20, 20)
RED = (176, 30, 36)
NAVY = (23, 54, 93)
TEAL = (14, 116, 110)
ORANGE = (232, 119, 34)
GOLD = (201, 152, 28)
GREY = (96, 96, 96)
WHITE = (255, 255, 255)
SKY = (168, 205, 226)
SEA = (38, 92, 140)
SAND = (226, 205, 160)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 pixels, '#' = ink.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#####", "...#.", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", ".#.##", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


class Canvas:
    def __init__(self):
        self.px = bytearray(W * H * 3)
        self.fill(0, 0, W, H, PAPER)

    def set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i:i + 3] = bytes(c)

    def fill(self, x, y, w, h, c):
        for yy in range(max(0, y), min(H, y + h)):
            base = (yy * W + max(0, x)) * 3
            row = bytes(c) * max(0, min(W, x + w) - max(0, x))
            self.px[base:base + len(row)] = row

    def rect(self, x, y, w, h, c, t=3):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=3):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = t // 2
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            self.fill(x - r, y - r, t, t, c)

    def circle(self, cx, cy, rad, c, fill=True, t=3):
        for yy in range(cy - rad, cy + rad + 1):
            for xx in range(cx - rad, cx + rad + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill and d2 <= rad * rad:
                    self.set(xx, yy, c)
                elif not fill and rad * rad - t * 2 * rad <= d2 <= rad * rad:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            for xx in range(min(xs), max(xs) + 1):
                inside = False
                j = len(pts) - 1
                for i in range(len(pts)):
                    xi, yi = pts[i]
                    xj, yj = pts[j]
                    if ((yi > yy) != (yj > yy)) and (
                            xx < (xj - xi) * (yy - yi) / (yj - yi) + xi):
                        inside = not inside
                    j = i
                if inside:
                    self.set(xx, yy, c)

    def text(self, x, y, s, scale, c, bold=False):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "#":
                        self.fill(cx + gx * scale, y + gy * scale,
                                  scale, scale, c)
                        if bold:
                            self.fill(cx + gx * scale + scale // 2,
                                      y + gy * scale, scale // 2 + 1, scale, c)
            cx += 6 * scale
        return cx

    def text_c(self, cx, y, s, scale, c, bold=False):
        return self.text(cx - text_w(s, scale) // 2, y, s, scale, c, bold)

    def wrap(self, x, y, s, scale, c, max_chars, leading=None):
        leading = leading or 9 * scale
        words = s.upper().split()
        lines = []
        cur = ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if len(trial) <= max_chars:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        for i, ln in enumerate(lines):
            self.text(x, y + i * leading, ln, scale, c)
        return y + len(lines) * leading


def save_png(cv, path):
    raw = bytearray()
    stride = W * 3
    for yy in range(H):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


# ---------------------------------------------------------------- pictures
def draw_chip(cv, x, y, s):
    """AI chip with pins and a rising market arrow."""
    cv.fill(x, y, s, s, NAVY)
    cv.rect(x, y, s, s, INK, 5)
    inner = s // 4
    cv.fill(x + inner, y + inner, s - 2 * inner, s - 2 * inner, TEAL)
    cv.text_c(x + s // 2, y + s // 2 - 14, "AI", 4, WHITE, bold=True)
    pin = s // 10
    for i in range(4):
        off = s // 8 + i * (s // 4)
        cv.fill(x + off, y - pin, pin // 2, pin, INK)
        cv.fill(x + off, y + s, pin // 2, pin, INK)
        cv.fill(x - pin, y + off, pin, pin // 2, INK)
        cv.fill(x + s, y + off, pin, pin // 2, INK)


def draw_globe_crack(cv, cx, cy, rad):
    cv.circle(cx, cy, rad, SKY)
    cv.circle(cx, cy, rad, NAVY, fill=False, t=5)
    # simple continents, kept inside the circle
    cv.poly([(cx - 38, cy - 34), (cx - 10, cy - 44), (cx - 3, cy - 16),
             (cx - 22, cy - 3), (cx - 39, cy - 16)], TEAL)
    cv.poly([(cx + 11, cy + 3), (cx + 39, cy - 5), (cx + 44, cy + 19),
             (cx + 19, cy + 30), (cx + 8, cy + 18)], TEAL)
    # crack of failure: jagged red line
    pts = [(cx - 44, cy - 13), (cx - 22, cy + 1), (cx - 30, cy + 16),
           (cx - 3, cy + 28), (cx + 1, cy + 44)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED, 7)


def draw_ship(cv, x, y, w):
    """Warship on waves, a small sea drone approaching."""
    cv.fill(x, y, w, 84, SEA)
    cv.poly([(x + 30, y + 42), (x + w - 40, y + 42), (x + w - 75, y + 64),
             (x + 60, y + 64)], (52, 58, 66))
    cv.fill(x + 70, y + 27, 150, 15, (52, 58, 66))
    cv.fill(x + 105, y + 12, 60, 15, (52, 58, 66))
    cv.line(x + 190, y + 27, x + 245, y + 6, INK, 5)
    # drone boat
    cv.poly([(x + w - 95, y + 66), (x + w - 35, y + 66), (x + w - 48, y + 76),
             (x + w - 82, y + 76)], ORANGE)
    for i in range(5):
        wx = x + 18 + i * (w // 5)
        cv.line(wx, y + 74, wx + 22, y + 74, WHITE, 4)


def draw_factory(cv, x, y, w):
    cv.fill(x, y, w, 72, SAND)
    cv.fill(x + 18, y + 28, 150, 40, (105, 95, 85))
    cv.poly([(x + 18, y + 28), (x + 60, y + 10), (x + 102, y + 28)], (80, 70, 62))
    cv.poly([(x + 92, y + 28), (x + 134, y + 10), (x + 168, y + 28)], (80, 70, 62))
    cv.fill(x + 178, y + 6, 16, 62, (80, 70, 62))
    # flames above roofline
    for fx, fh in ((36, 20), (66, 28), (104, 22), (180, 18)):
        cv.poly([(x + fx, y + 30), (x + fx + 10, y + 30 - fh),
                 (x + fx + 20, y + 30)], ORANGE)
        cv.poly([(x + fx + 5, y + 30), (x + fx + 10, y + 30 - fh // 2),
                 (x + fx + 15, y + 30)], GOLD)


def draw_ball(cv, cx, cy, rad):
    cv.circle(cx, cy, rad, WHITE)
    cv.circle(cx, cy, rad, INK, fill=False, t=5)
    cv.poly([(cx - 18, cy - 22), (cx + 18, cy - 22), (cx + 30, cy + 4),
             (cx, cy + 26), (cx - 30, cy + 4)], INK)
    cv.line(cx, cy - rad, cx - 18, cy - 22, INK, 4)
    cv.line(cx + rad - 6, cy - 20, cx + 18, cy - 22, INK, 4)
    cv.line(cx - rad + 6, cy + 22, cx - 30, cy + 4, INK, 4)
    cv.line(cx + rad - 6, cy + 22, cx + 30, cy + 4, INK, 4)
    cv.line(cx, cy + rad, cx, cy + 26, INK, 4)


# ---------------------------------------------------------------- page
def build():
    cv = Canvas()
    cv.rect(14, 14, W - 28, H - 28, INK, 4)
    cv.rect(26, 26, W - 52, H - 52, INK, 2)

    # masthead
    cv.text_c(W // 2, 40, "THE WORLD IN ONE DAY", 3, GREY)
    cv.text_c(W // 2, 74, "THE DAILY WORLD", 9, INK, bold=True)
    cv.fill(48, 148, W - 96, 6, RED)
    cv.fill(48, 162, W - 96, 62, INK)
    cv.text_c(W // 2, 176, "MONDAY 23 NOVEMBER 2026", 5, WHITE, bold=True)
    cv.text_c(W // 2, 234, "THE DAY'S BIGGEST STORIES - IN ONE PICTURE", 3, INK)

    half = (W - 96 - 24) // 2  # 452 per column

    # ---- lead story: Nvidia (full width)
    ly = 262
    cv.fill(48, ly, W - 96, 5, INK)
    cv.text(48, ly + 14, "TECH + MARKETS - UNITED STATES", 3, RED, bold=True)
    cv.text(48, ly + 44, "HUANG RETURNS", 6, INK, bold=True)
    cv.text(48, ly + 90, "NVIDIA LEAPS 31%", 6, RED, bold=True)
    cv.wrap(48, ly + 142,
            "Nvidia reinstated Jensen Huang as CEO after Trump "
            "intervened. Nasdaq up 7 percent.", 3, INK, 33)
    draw_chip(cv, 742, ly + 34, 150)
    cv.text_c(817, ly + 198, "CHIP INDEX +14%", 3, NAVY, bold=True)

    # ---- middle row: COP31 + Ukraine
    my = 506
    cv.fill(48, my - 12, W - 96, 4, INK)
    cv.line(512, my, 512, my + 226, INK, 3)
    # COP31
    cv.text(48, my + 2, "CLIMATE - ANTALYA, TURKIYE", 3, TEAL, bold=True)
    cv.text(48, my + 30, "COP31 ENDS", 5, INK, bold=True)
    cv.text(48, my + 68, "WITH NO DEAL", 5, INK, bold=True)
    draw_globe_crack(cv, 118, my + 156, 50)
    cv.wrap(196, my + 110,
            "Talks collapsed over fossil fuels. EU rejected the pact.",
            3, INK, 16)
    # Ukraine
    ux = 48 + half + 24
    cv.text(ux, my + 2, "WAR - BENGHAZI, LIBYA", 3, RED, bold=True)
    cv.text(ux, my + 30, "SEA DRONES SINK", 5, INK, bold=True)
    cv.text(ux, my + 68, "RUSSIAN WARSHIP", 5, INK, bold=True)
    draw_ship(cv, ux, my + 108, half)
    cv.wrap(ux, my + 194,
            "Zelensky: 7 sea drones sank corvette Merkury.",
            3, INK, 25)

    # ---- bottom row: Indonesia + FIFA
    by = 762
    cv.fill(48, by - 12, W - 96, 4, INK)
    cv.line(512, by, 512, by + 150, INK, 3)
    # Indonesia factory fire
    cv.text(48, by + 2, "DISASTER - INDONESIA", 3, ORANGE, bold=True)
    cv.text(48, by + 30, "FACTORY FIRE:", 5, INK, bold=True)
    cv.text(48, by + 68, "24 DEAD", 5, RED, bold=True)
    draw_factory(cv, 48, by + 106, 210)
    cv.wrap(278, by + 106,
            "Deaths set on Monday. 30 missing.",
            3, INK, 12)
    # FIFA Women's World Cup
    cv.text(ux, by + 2, "FOOTBALL - FIFA CONGRESS", 3, TEAL, bold=True)
    cv.text(ux, by + 30, "UK TO HOST", 5, INK, bold=True)
    cv.text(ux, by + 68, "WOMEN'S WC 2035", 5, INK, bold=True)
    draw_ball(cv, ux + 50, by + 140, 30)
    cv.wrap(ux + 100, by + 106,
            "Four UK nations host. USA group gets 2031.",
            3, INK, 19)

    # ---- footer ticker: sixth story
    cv.fill(48, 954, W - 96, 42, INK)
    cv.text_c(W // 2, 965, "ALSO: CROWDSTRIKE BUYS ZSCALER - $43.9BN DEAL",
              3, WHITE, bold=True)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    save_png(cv, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
