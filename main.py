"""news-image-20261126 -- "Parade Under Pressure".

One-image editorial poster summing up world news for Thursday 26 November
2026 (Thanksgiving Day): the nor'easter and the postponement of the 100th
Macy's parade, US Q3 GDP 4.3%, the Houthi claim on Ras Tanura, and the
CIA/ODNI cyber breach.

Pure Python 3 stdlib only (os, struct, zlib, math). No network, no external
files at runtime: the 5x7 pixel font, the turkey shape and all geometry are
embedded below. Fully deterministic: two runs produce byte-identical PNGs.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
Canvas: exactly 1024x1024, exactly four colours.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# --- Palette: exactly four colours -------------------------------------------
CRANBERRY = (178, 58, 72)    # #B23A48 turkey body
NAVY = (20, 33, 61)          # #14213D hero sky, masthead text, foot bar
CREAM = (242, 230, 207)      # #F2E6CF paper, strip background
AMBER = (244, 163, 0)        # #F4A300 accents, rules, big number, storm bars

# --- 5x7 pixel font -----------------------------------------------------------
# Each glyph: 7 rows of 5 characters, '#' = ink, '.' = empty.
# Covers A-Z, 0-9, space, and . , % $ ' -- everything the poster text needs.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
}


class Canvas:
    """RGB pixel buffer with filled-shape and text helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        r, g, b = color
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            for x in range(x0, x1):
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b
                i += 3

    def fill_ellipse(self, cx, cy, rx, ry, color):
        for y in range(cy - ry, cy + ry + 1):
            dy = (y - cy) / ry
            if abs(dy) > 1.0:
                continue
            half = int(rx * math.sqrt(1.0 - dy * dy))
            self.fill_rect(cx - half, y, cx + half + 1, y + 1, color)

    def fill_circle(self, cx, cy, r, color):
        self.fill_ellipse(cx, cy, r, r, color)

    def fill_rot_ellipse(self, cx, cy, a, b, angle_deg, color):
        """Filled ellipse rotated by angle_deg, via bounding-box point test."""
        th = math.radians(angle_deg)
        co = math.cos(th)
        si = math.sin(th)
        ext = int(max(a, b)) + 1
        for y in range(cy - ext, cy + ext + 1):
            for x in range(cx - ext, cx + ext + 1):
                dx = x - cx
                dy = y - cy
                u = dx * co + dy * si
                v = -dx * si + dy * co
                if (u / a) * (u / a) + (v / b) * (v / b) <= 1.0:
                    self.set(x, y, color)

    def fill_polygon(self, pts, color):
        """Scanline fill for a simple polygon given as [(x, y), ...]."""
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[j]), y, int(xs[j + 1]) + 1, y + 1, color)

    def draw_line(self, x0, y0, x1, y1, width, color):
        """Thick line by stamping circles along the segment."""
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        r = max(1, width // 2)
        for s in range(steps + 1):
            t = s / steps
            x = int(x0 + (x1 - x0) * t)
            y = int(y0 + (y1 - y0) * t)
            self.fill_circle(x, y, r, color)

    # -- text ---------------------------------------------------------------
    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def draw_text(self, s, x, y, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch)
            if glyph is None:
                raise ValueError("unsupported character: %r" % ch)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(
                            cx + col * scale,
                            y + row * scale,
                            cx + (col + 1) * scale,
                            y + (row + 1) * scale,
                            color,
                        )
            cx += 6 * scale

    def draw_text_centered(self, s, cx, y, scale, color):
        self.draw_text(s, cx - self.text_width(s, scale) // 2, y, scale, color)


def draw_turkey_balloon(cv):
    """Cranberry turkey silhouette shaped like a parade balloon.

    Tail fan first (behind), then body, belly patch, head, beak, eye.
    The balloon sits in the lower two thirds of the hero.
    """
    # Tail fan: five feathers fanning up-left from the body.
    for ang in (-58, -34, -10, 14, 38):
        cv.fill_rot_ellipse(340, 478, 118, 30, ang, CRANBERRY)
    # Body: big horizontal balloon.
    cv.fill_ellipse(480, 478, 215, 122, CRANBERRY)
    # Belly patch: cream oval low on the body (cream is not the sky colour,
    # so it reads as a patch, never as a see-through hole).
    cv.fill_ellipse(480, 528, 115, 42, CREAM)
    # Head: circle riding the top-right of the body.
    cv.fill_circle(655, 388, 60, CRANBERRY)
    # Beak: amber triangle pointing right from the head.
    cv.fill_polygon([(701, 378), (733, 396), (701, 414)], AMBER)
    # Wattle: small amber drop under the beak.
    cv.fill_ellipse(707, 434, 11, 18, AMBER)
    # Eye: cream dot.
    cv.fill_circle(667, 372, 7, CREAM)


def draw_handler(cv):
    """Small cream balloon-handler figure, bottom-right of the hero,
    holding two tether lines up to the balloon."""
    # Tether lines from the handler's hand to the balloon's underside.
    cv.draw_line(905, 548, 700, 588, 4, CREAM)
    cv.draw_line(905, 548, 600, 588, 4, CREAM)
    # Head, torso, legs.
    cv.fill_circle(905, 540, 11, CREAM)
    cv.fill_ellipse(905, 578, 14, 26, CREAM)
    cv.fill_rect(894, 600, 901, 632, CREAM)
    cv.fill_rect(909, 600, 916, 632, CREAM)


def draw_storm_bars(cv):
    """Three thick amber diagonal bars slanting down-left across the hero,
    cutting through the turkey: the nor'easter wind/rain."""
    for x in (350, 620, 890):
        cv.fill_polygon(
            [(x, 70), (x + 16, 70), (x - 280, 640), (x - 296, 640)], AMBER
        )


def build():
    cv = Canvas(W, H, CREAM)

    # --- Masthead (y 0-64) --------------------------------------------------
    cv.fill_rect(0, 0, W, 64, CREAM)
    cv.draw_text("THURSDAY, 26 NOVEMBER 2026", 32, 22, 3, NAVY)
    right = "THANKSGIVING DAY"
    cv.draw_text(right, 992 - cv.text_width(right, 3), 22, 3, NAVY)
    # Amber rule under the masthead (y 64-70).
    cv.fill_rect(0, 64, W, 70, AMBER)

    # --- Hero (y 70-640, navy sky) ------------------------------------------
    cv.fill_rect(0, 70, W, 640, NAVY)
    # Order matters: turkey first, storm bars cut across the turkey, then the
    # handler, and the headline/kicker LAST so no bar ever crosses the text.
    draw_turkey_balloon(cv)
    draw_storm_bars(cv)
    draw_handler(cv)
    cv.draw_text_centered("PARADE IN A", 512, 96, 8, CREAM)
    cv.draw_text_centered("NOR'EASTER", 512, 168, 8, CREAM)
    cv.draw_text_centered(
        "MACY'S 100TH MOVED TO SATURDAY.", 512, 252, 3, CREAM
    )

    # --- Strip (y 640-960, cream) -------------------------------------------
    cv.fill_rect(0, 640, W, 960, CREAM)
    # Vertical amber divider at x=512.
    cv.fill_rect(509, 640, 515, 960, AMBER)

    # Left: MONEY.
    cv.draw_text("MONEY", 48, 668, 2, NAVY)
    cv.draw_text("4.3%", 48, 700, 12, AMBER)
    cv.draw_text("US GDP, Q3", 48, 806, 4, NAVY)
    cv.draw_text("BRENT CRUDE ABOUT $93.", 48, 862, 2, NAVY)

    # Right: WORLD.
    cv.draw_text("WORLD", 560, 668, 2, NAVY)
    cv.draw_text("HOUTHIS CLAIM", 560, 700, 5, NAVY)
    cv.draw_text("RAS TANURA", 560, 745, 5, NAVY)
    cv.draw_text("STRIKE", 560, 790, 5, NAVY)
    cv.draw_text("CIA, ODNI REPORT CYBER BREACH.", 560, 862, 2, NAVY)

    # --- Foot rule (y 960-1024, navy bar) ------------------------------------
    cv.fill_rect(0, 960, W, 1024, NAVY)
    cv.draw_text_centered(
        "81.5M AMERICANS TRAVEL FOR THANKSGIVING", 512, 981, 3, CREAM
    )

    return cv


def write_png(cv, path):
    """Hand-written PNG encoder: signature, IHDR, IDAT (zlib), IEND."""

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: None
        raw += cv.px[y * stride:(y + 1) * stride]

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(
        b"IHDR",
        struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0),
    )
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    write_png(cv, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
