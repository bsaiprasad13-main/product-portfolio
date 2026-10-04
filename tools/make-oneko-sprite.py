"""Draws a custom oneko-style sprite sheet: an outline-only pixel kitten with big
eyes, fluffy cheek tufts, tufted ears and a fluffy tail.

Each 32x32 frame is built from simple shapes painted back to front; every part
gets a 1px black outline and a white fill, so overlapping parts keep their own
outlines. The sheet uses oneko.gif's 8x4 layout, so oneko.js works unchanged.

Run: python tools/make-oneko-sprite.py [out.png] [--preview preview.png]
Needs Pillow.
"""
import math
import sys
from PIL import Image

S = 32
EMPTY, INK, FILL = 0, 1, 2
COLORS = {INK: (0, 0, 0, 255), FILL: (255, 255, 255, 255)}


# ---- Shape masks --------------------------------------------------------

def ellipse(cx, cy, rx, ry):
    return {(x, y) for x in range(S) for y in range(S)
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1}


def stroke(points, r=1.0):
    out = set()
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        steps = max(1, int(math.hypot(x2 - x1, y2 - y1) * 4))
        for i in range(steps + 1):
            t = i / steps
            px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            out |= {(x, y) for x in range(int(px - r) - 1, int(px + r) + 2)
                    for y in range(int(py - r) - 1, int(py + r) + 2)
                    if 0 <= x < S and 0 <= y < S and (x + 0.5 - px) ** 2 + (y + 0.5 - py) ** 2 <= r * r}
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


def shift(mask, dx, dy):
    return {(x + dx, y + dy) for x, y in mask if 0 <= x + dx < S and 0 <= y + dy < S}


class Frame:
    def __init__(self):
        self.px = [[EMPTY] * S for _ in range(S)]

    def part(self, mask):
        """Black 1px outline ring, then white fill."""
        for x, y in mask:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < S and 0 <= ny < S and (nx, ny) not in mask:
                    self.px[ny][nx] = INK
        for x, y in mask:
            self.px[y][x] = FILL
        return self

    def ink(self, *pts):
        for x, y in pts:
            x, y = round(x), round(y)
            if 0 <= x < S and 0 <= y < S:
                self.px[y][x] = INK
        return self

    def white(self, *pts):
        for x, y in pts:
            x, y = round(x), round(y)
            if 0 <= x < S and 0 <= y < S:
                self.px[y][x] = FILL
        return self

    def image(self):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        for y in range(S):
            for x in range(S):
                if self.px[y][x]:
                    img.putpixel((x, y), COLORS[self.px[y][x]])
        return img


# ---- Kitten parts ---------------------------------------------------------

def fluffy_head(cx, cy, rx=7.5, ry=6.5):
    """Big round head with fur tufts poking out at the cheeks and chin."""
    m = ellipse(cx, cy, rx, ry)
    for sx in (-1, 1):
        m |= triangle((cx + sx * (rx - 1.5), cy + 1), (cx + sx * (rx + 1.4), cy + 4.2), (cx + sx * (rx - 3.5), cy + 4.5))
    m |= triangle((cx - 2, cy + ry - 1), (cx, cy + ry + 1.8), (cx + 2, cy + ry - 1))
    return m


def tufted_ears(f, cx, top, base, spread=4.5):
    for sx in (-1, 1):
        ex = cx + sx * spread
        f.part(triangle((ex - 3.2, base), (ex + sx * 0.8, top), (ex + 3.2, base)))
        f.ink((round(ex + sx * 0.5), top + 3))                           # fur tuft inside the ear


def front_face(f, cx, cy, eyes="open"):
    lx, rx = cx - 4, cx + 2
    if eyes == "open":
        for ex in (lx, rx):                              # big 2x3 eyes with a highlight
            f.ink((ex, cy), (ex + 1, cy), (ex, cy + 1), (ex + 1, cy + 1), (ex, cy + 2), (ex + 1, cy + 2))
            f.white((ex, cy))
    elif eyes == "wide":
        for ex in (lx, rx):
            f.ink((ex - 1, cy), (ex, cy), (ex + 1, cy), (ex - 1, cy + 1), (ex + 1, cy + 1),
                  (ex - 1, cy + 2), (ex, cy + 2), (ex + 1, cy + 2))
    else:                                                # closed: little arcs
        for ex in (lx, rx):
            f.ink((ex - 1, cy + 1), (ex, cy + 2), (ex + 1, cy + 2), (ex + 2, cy + 1))
    f.ink((cx - 1, cy + 3))                              # nose
    f.ink((cx - 2, cy + 4), (cx, cy + 4))                # "w" mouth


def fluffy_tail(points, r=1.9):
    m = stroke(points, r)
    (x2, y2), (x1, y1) = points[-1], points[-2]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    tip = (x2 + ux * 2.5, y2 + uy * 2.5)
    m |= triangle((x2 - uy * 2.4, y2 + ux * 2.4), tip, (x2 + uy * 2.4, y2 - ux * 2.4))
    return m


# ---- Poses ------------------------------------------------------------------

def sit(eyes="open", burst=False):
    f = Frame()
    f.part(fluffy_tail([(21, 28), (26, 26), (27, 21), (26, 17)]))
    f.part(ellipse(16, 23, 6, 6) - {(x, y) for x in range(S) for y in range(29, S)})
    f.part(ellipse(13, 28.5, 2.2, 1.5))
    f.part(ellipse(19, 28.5, 2.2, 1.5))
    tufted_ears(f, 16, 0.5, 9)
    f.part(fluffy_head(16, 12))
    front_face(f, 16, 11, eyes)
    if burst:
        for (x1, y1, x2, y2) in ((3, 3, 5, 5), (2, 9, 5, 9), (27, 3, 25, 5), (28, 9, 25, 9)):
            f.ink(*[(round(x1 + (x2 - x1) * t / 2), round(y1 + (y2 - y1) * t / 2)) for t in range(3)])
    return f


def sleep(breath):
    f = Frame()
    f.part(fluffy_tail([(6, 26), (10, 28), (18, 28)], r=1.5))
    f.part(ellipse(15, 23 - breath * 0.5, 9.5, 5.5 + breath * 0.5))
    tufted_ears(f, 22, 12 - breath, 17, spread=3.5)
    f.part(fluffy_head(22, 20 - breath * 0.5, rx=6, ry=4.8))
    f.ink((18, 21), (19, 22), (20, 21), (23, 21), (24, 22), (25, 21))   # closed eyes
    z = [(26, 5), (27, 5), (28, 5), (29, 5), (28, 6), (27, 7), (26, 8), (27, 8), (28, 8), (29, 8)]
    f.ink(*[(x - 3 + breath * 2, y - breath * 2) for x, y in z])
    return f


def profile_head(f, dy=0, face="side"):
    """Head in profile facing right. face: side (one eye), back (looking away), front (turned to viewer)."""
    f.part(triangle((18.5, 11 + dy), (20, 3.5 + dy), (23.5, 9 + dy)))
    f.part(triangle((24, 9 + dy), (27.5, 3.5 + dy), (28, 11 + dy)))
    head = ellipse(23.5, 13.5 + dy, 6, 5.5)
    head |= triangle((18, 15 + dy), (16.5, 17.5 + dy), (20, 18 + dy))     # cheek tuft at the back
    head |= triangle((21, 18 + dy), (22, 20.5 + dy), (24, 18 + dy))       # chin tuft
    f.part(head)
    if face == "side":
        f.ink((25, 12 + dy), (26, 12 + dy), (25, 13 + dy), (26, 13 + dy), (25, 14 + dy), (26, 14 + dy))
        f.white((25, 12 + dy))
        f.ink((29, 15 + dy))                                               # nose
    elif face == "front":
        for ex in (21, 25):
            f.ink((ex, 12 + dy), (ex + 1, 12 + dy), (ex, 13 + dy), (ex + 1, 13 + dy), (ex, 14 + dy), (ex + 1, 14 + dy))
            f.white((ex, 12 + dy))
        f.ink((24, 16 + dy))
    # "back": no face, just the back of the head


def side_run(stretch, dy=0, face="side"):
    """Running, facing right."""
    f = Frame()
    if stretch:
        legs = [((17, 21), (22, 27)), ((8, 21), (3, 27)), ((20, 21), (25, 27)), ((11, 21), (6, 27))]
        body, tail = ellipse(14, 20, 8, 3.8), [(7, 19), (4, 15), (3, 10)]
    else:
        legs = [((11, 22), (12, 28)), ((14, 22), (14, 28)), ((17, 22), (17, 28)), ((19, 22), (19, 28))]
        body, tail = ellipse(15, 20, 6.5, 4.4), [(9, 19), (6, 14), (6, 9)]
    for a, b in legs:
        f.part(stroke([a, b], 0.9))
    f.part(fluffy_tail(tail))
    f.part(body)
    profile_head(f, dy, face)
    return f


def front_run(stretch):
    """Running toward the viewer (south)."""
    f = Frame()
    f.part(stroke([(12, 24), (12, 30 if stretch else 28)], 1.0))
    f.part(stroke([(20, 24), (20, 28 if stretch else 30)], 1.0))
    f.part(ellipse(16, 22, 6, 5))
    tufted_ears(f, 16, 0.5, 9)
    f.part(fluffy_head(16, 12))
    front_face(f, 16, 11)
    return f


def back_run(stretch):
    """Running away from the viewer (north): back of the head, tail toward us."""
    f = Frame()
    f.part(stroke([(12, 24), (12, 30 if stretch else 28)], 1.0))
    f.part(stroke([(20, 24), (20, 28 if stretch else 30)], 1.0))
    f.part(ellipse(16, 21, 6, 5.5))
    tufted_ears(f, 16, 0.5, 9)
    f.part(fluffy_head(16, 12))
    f.part(fluffy_tail([(17, 25), (21, 28), (25, 26)], r=1.6))
    return f


def tired():
    """Sitting and yawning."""
    f = sit(eyes="closed")
    f.white((14, 15), (16, 15))
    f.ink((14, 15), (15, 15), (16, 15), (14, 16), (16, 16), (14, 17), (15, 17), (16, 17))   # open mouth
    f.white((15, 16))
    return f


def scratch_self(k):
    """Sitting, scratching behind the ear with a hind leg (3 frames)."""
    f = Frame()
    f.part(fluffy_tail([(9, 28), (5, 26), (4, 21), (5, 17)]))
    f.part(ellipse(15, 23, 6, 6) - {(x, y) for x in range(S) for y in range(29, S)})
    f.part(ellipse(12, 28.5, 2.2, 1.5))
    foot = [(23, 13), (24, 16), (23, 11)][k]
    f.part(stroke([(19, 25), (23, 21), foot], 1.1))
    tufted_ears(f, 15, 0.5 + (k == 2), 9)
    f.part(fluffy_head(15, 12))
    front_face(f, 15, 11, eyes="closed")
    return f


def scratch_wall_e(k):
    """Standing up on hind legs, scratching a wall to the right (2 frames)."""
    f = Frame()
    f.part(fluffy_tail([(14, 27), (9, 27), (7, 22), (8, 18)]))
    f.part(stroke([(16, 25), (15, 30)], 1.0))
    f.part(stroke([(20, 25), (20, 30)], 1.0))
    hi, lo = ((29, 9), (29, 17)) if k == 0 else ((29, 12), (29, 20))
    f.part(stroke([(21, 17), hi], 0.9))
    f.part(ellipse(18, 20, 4.8, 7))
    f.part(stroke([(21, 20), lo], 0.9))
    f.part(triangle((14, 7.5), (15.5, 1), (18.5, 6)))
    f.part(triangle((19, 6), (22.5, 1), (23, 7.5)))
    head = ellipse(18.5, 10, 5.5, 5)
    head |= triangle((13.5, 11.5), (12, 14), (15.5, 14))
    f.part(head)
    f.ink((20, 8), (21, 8), (20, 9), (21, 9), (20, 10), (21, 10))
    f.white((20, 8))
    f.ink((23, 11))
    return f

def scratch_wall_n(k):
    """Standing up, seen from behind, scratching the top edge (2 frames)."""
    f = Frame()
    left, right = ((4, 4), (28, 8)) if k == 0 else ((4, 8), (28, 4))
    f.part(stroke([(12, 20), left], 1.0))
    f.part(stroke([(20, 20), right], 1.0))
    f.part(stroke([(13, 27), (13, 31)], 1.0))
    f.part(stroke([(19, 27), (19, 31)], 1.0))
    f.part(ellipse(16, 23, 5.5, 6))
    tufted_ears(f, 16, 6, 13)
    f.part(fluffy_head(16, 16, rx=6.5, ry=5.5))
    f.part(fluffy_tail([(17, 28), (21, 30), (25, 28)], r=1.4))
    return f

def scratch_wall_s(k):
    """Facing the viewer, scratching the bottom edge (2 frames)."""
    f = Frame()
    left, right = ((11, 31), (21, 28)) if k == 0 else ((11, 28), (21, 31))
    f.part(ellipse(16, 21, 6, 5))
    f.part(stroke([(12, 22), left], 1.0))
    f.part(stroke([(20, 22), right], 1.0))
    tufted_ears(f, 16, 0.5, 9)
    f.part(fluffy_head(16, 12))
    front_face(f, 16, 11)
    return f


def mirror(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


def build_sheet():
    """oneko.gif layout: 8 columns x 4 rows of 32px cells; (col, row) per frame."""
    E = [side_run(True).image(), side_run(False).image()]
    NE = [side_run(True, -2, "back").image(), side_run(False, -2, "back").image()]
    SE = [side_run(True, 1, "front").image(), side_run(False, 1, "front").image()]
    wall_e = [scratch_wall_e(0).image(), scratch_wall_e(1).image()]
    cells = {
        (3, 3): sit().image(),
        (7, 3): sit("wide", burst=True).image(),
        (3, 2): tired().image(),
        (2, 0): sleep(0).image(), (2, 1): sleep(1).image(),
        (5, 0): scratch_self(0).image(), (6, 0): scratch_self(1).image(), (7, 0): scratch_self(2).image(),
        (0, 0): scratch_wall_n(0).image(), (0, 1): scratch_wall_n(1).image(),
        (7, 1): scratch_wall_s(0).image(), (6, 2): scratch_wall_s(1).image(),
        (2, 2): wall_e[0], (2, 3): wall_e[1],
        (4, 0): mirror(wall_e[0]), (4, 1): mirror(wall_e[1]),
        (1, 2): back_run(True).image(), (1, 3): back_run(False).image(),
        (0, 2): NE[0], (0, 3): NE[1],
        (3, 0): E[0], (3, 1): E[1],
        (5, 1): SE[0], (5, 2): SE[1],
        (6, 3): front_run(True).image(), (7, 2): front_run(False).image(),
        (5, 3): mirror(SE[0]), (6, 1): mirror(SE[1]),
        (4, 2): mirror(E[0]), (4, 3): mirror(E[1]),
        (1, 0): mirror(NE[0]), (1, 1): mirror(NE[1]),
    }
    assert len(cells) == 32
    sheet = Image.new("RGBA", (S * 8, S * 4), (0, 0, 0, 0))
    for (col, row), img in cells.items():
        sheet.paste(img, (col * S, row * S))
    return sheet


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "kitten-oneko.png"
    build_sheet().save(out, optimize=True)
    print("saved", out)
