"""Draws the original pixel-art cat sprite sheet used by cat.js.

Each 32x32 frame is built from simple shapes painted back to front. Every
part gets a 1px black outline and a white fill, so overlapping parts (head
over body, legs behind body) keep their own outlines, like hand-drawn
pixel art. Run: python tools/make-cat-sprite.py  ->  cat-sprite.png
"""
import math
import sys
from PIL import Image

S = 32
EMPTY, INK, FILL = 0, 1, 2
COLORS = {INK: (20, 20, 24, 255), FILL: (255, 255, 255, 255)}


def ellipse(cx, cy, rx, ry):
    return {(x, y) for x in range(S) for y in range(S)
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1}


def stroke(points, r=1.0):
    """Thick polyline through points, radius r."""
    out = set()
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        steps = max(1, int(math.hypot(x2 - x1, y2 - y1) * 4))
        for i in range(steps + 1):
            t = i / steps
            px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            out |= {(x, y) for x in range(S) for y in range(S)
                    if (x + 0.5 - px) ** 2 + (y + 0.5 - py) ** 2 <= r * r}
    return out


def triangle(a, b, c):
    def side(p, q, r):
        return (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1])
    out = set()
    for x in range(S):
        for y in range(S):
            p = (x + 0.5, y + 0.5)
            d1, d2, d3 = side(p, a, b), side(p, b, c), side(p, c, a)
            if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
                out.add((x, y))
    return out


class Frame:
    def __init__(self):
        self.px = [[EMPTY] * S for _ in range(S)]

    def part(self, mask):
        """Paint a part: black 1px outline ring, then white fill."""
        for x, y in mask:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < S and 0 <= ny < S and (nx, ny) not in mask:
                    self.px[ny][nx] = INK
        for x, y in mask:
            self.px[y][x] = FILL
        return self

    def ink(self, *pts):
        for x, y in pts:
            if 0 <= x < S and 0 <= y < S:
                self.px[y][x] = INK
        return self

    def image(self):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        for y in range(S):
            for x in range(S):
                if self.px[y][x]:
                    img.putpixel((x, y), COLORS[self.px[y][x]])
        return img


def ears(f, lx, rx, top, base):
    f.part(triangle((lx - 3, base), (lx - 1, top), (lx + 2, base)))
    f.part(triangle((rx - 2, base), (rx + 1, top), (rx + 3, base)))


def front_face(f, cx, cy):
    f.ink((cx - 3, cy), (cx + 2, cy), (cx, cy + 2), (cx - 1, cy + 2))


# --- Poses ---------------------------------------------------------------

def sit(alert=False):
    f = Frame()
    f.part(stroke([(22, 28), (27, 26), (28, 21), (27, 17)], 1.1))   # tail
    f.part(ellipse(16, 22, 6.5, 6.5) - {(x, y) for x in range(S) for y in range(29, S)})
    f.part(ellipse(13, 28, 2.2, 1.6))                                 # paws
    f.part(ellipse(19, 28, 2.2, 1.6))
    ears(f, 12, 19, 4, 10)
    f.part(ellipse(16, 12, 6.5, 5.5))                                 # head
    if alert:
        f.ink((13, 11), (13, 12), (18, 11), (18, 12))                 # wide eyes
        f.ink((16, 14), (15, 14))
        for (x1, y1, x2, y2) in ((4, 4, 6, 6), (3, 9, 6, 9), (5, 14, 7, 13),
                                 (27, 4, 25, 6), (28, 9, 25, 9), (26, 14, 24, 13)):
            f.ink(*[(round(x1 + (x2 - x1) * t / 3), round(y1 + (y2 - y1) * t / 3)) for t in range(4)])
    else:
        front_face(f, 16, 12)
    return f


def sleep(breath):
    f = Frame()
    f.part(ellipse(15, 23 - breath * 0.5, 10, 5.5 + breath * 0.5))   # curled body
    ears(f, 19, 25, 13 - breath, 18)
    f.part(ellipse(22, 20 - breath * 0.5, 5.5, 4.2))                  # head tucked in
    f.ink((20, 20), (21, 20), (24, 20), (25, 20))                      # closed eyes
    f.ink(*[(x, 26) for x in range(8, 19)])                            # tail wrapped round
    z = [(26, 5), (27, 5), (28, 5), (29, 5), (28, 6), (27, 7), (26, 8), (27, 8), (28, 8), (29, 8)]
    f.ink(*[(x - 2 + breath * 2, y - breath * 2) for x, y in z])      # little "z"
    return f


def side(stretch, head_dy=0, face="side"):
    """Running, facing right. stretch=True: legs reaching, False: gathered."""
    f = Frame()
    if stretch:
        legs = [((19, 21), (24, 27)), ((9, 21), (4, 27)), ((21, 21), (26, 27)), ((11, 21), (6, 27))]
        body = ellipse(15, 19, 8.5, 3.8)
        tail = [(7, 18), (4, 15), (3, 11)]
    else:
        legs = [((12, 22), (13, 28)), ((15, 22), (15, 28)), ((18, 22), (18, 28)), ((20, 22), (20, 28))]
        body = ellipse(16, 19, 7, 4.5)
        tail = [(9, 18), (6, 14), (6, 10)]
    for a, b in legs:
        f.part(stroke([a, b], 0.9))
    f.part(stroke(tail, 1.1))
    f.part(body)
    hy = 14 + head_dy
    f.part(triangle((20, hy - 3), (21, hy - 8), (24, hy - 4)))
    f.part(triangle((25, hy - 4), (28, hy - 8), (28.5, hy - 2)))
    f.part(ellipse(24.5, hy, 5.2, 4.6))
    if face == "side":
        f.ink((26, hy - 1), (29, hy + 1))
    elif face == "front":
        f.ink((23, hy - 1), (27, hy - 1), (25, hy + 1))
    return f


def front_run(stretch):
    f = Frame()
    left_long = stretch
    f.part(stroke([(12, 24), (12, 30 if left_long else 28)], 1.0))
    f.part(stroke([(20, 24), (20, 28 if left_long else 30)], 1.0))
    f.part(ellipse(16, 21, 6, 5))
    ears(f, 12, 19, 4, 10)
    f.part(ellipse(16, 12, 6.5, 5.5))
    front_face(f, 16, 12)
    return f


def back_run(stretch):
    f = Frame()
    left_long = stretch
    f.part(stroke([(19, 24), (23, 27), (25, 25)], 1.0))               # tail
    f.part(stroke([(12, 24), (12, 30 if left_long else 28)], 1.0))
    f.part(stroke([(20, 24), (20, 28 if left_long else 30)], 1.0))
    f.part(ellipse(16, 20, 6, 5.5))
    ears(f, 12, 19, 4, 10)
    f.part(ellipse(16, 12, 6.5, 5.5))
    f.ink((16, 15), (16, 16))                                          # back-of-head tuft
    return f


def mirror(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


# Sheet order must match FRAMES in cat.js
E = [side(True).image(), side(False).image()]
NE = [side(True, -2, "back").image(), side(False, -2, "back").image()]
SE = [side(True, 1, "front").image(), side(False, 1, "front").image()]
N = [back_run(True).image(), back_run(False).image()]
Sv = [front_run(True).image(), front_run(False).image()]
frames = [
    sit().image(), sit(alert=True).image(), sleep(0).image(), sleep(1).image(),
    *E, *NE, *N, *map(mirror, NE), *map(mirror, E), *map(mirror, SE), *Sv, *SE,
]

sheet = Image.new("RGBA", (S * len(frames), S), (0, 0, 0, 0))
for i, fr in enumerate(frames):
    sheet.paste(fr, (i * S, 0))
out = sys.argv[1] if len(sys.argv) > 1 else "cat-sprite.png"
sheet.save(out, optimize=True)
print(f"saved {out}: {len(frames)} frames, {sheet.size[0]}x{sheet.size[1]}")
