#!/usr/bin/env python3
"""
make_icon.py — generates the Panda3D Studio launcher icon (pure Python,
no external dependencies).

Output: android/studio/res/drawable-nodpi/ic_launcher.png  (192x192)
"""
import math
import os
import struct
import zlib


def write_png(path, w, h, px):
    """px: bytearray of RGBA rows, top-to-bottom."""
    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        return out

    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)  # no filter
        raw.extend(px[y * stride:(y + 1) * stride])

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def main():
    W = H = 192
    px = bytearray(W * H * 4)

    def setpx(x, y, r, g, b, a=255):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 4
            # simple alpha-over compositing
            if a == 255:
                px[i:i + 4] = bytes((r, g, b, a))
                return
            oa = px[i + 3]
            if oa == 0:
                px[i:i + 4] = bytes((r, g, b, a))
                return
            ia = a / 255.0
            px[i] = int(r * ia + px[i] * (1 - ia))
            px[i + 1] = int(g * ia + px[i + 1] * (1 - ia))
            px[i + 2] = int(b * ia + px[i + 2] * (1 - ia))
            px[i + 3] = min(255, int(a + oa * (1 - ia)))

    R = 42  # corner radius

    def in_rounded_rect(x, y):
        # Distance from the point to the rectangle inset by R: a rounded
        # rectangle is all points within R of that inset rectangle.
        cx = min(max(x, R), W - 1 - R)
        cy = min(max(y, R), H - 1 - R)
        dx = x - cx
        dy = y - cy
        d = math.sqrt(dx * dx + dy * dy)
        if d <= R:
            return 1.0
        if d <= R + 1:
            return 0.5
        return 0.0

    # --- background: rounded square with a subtle vertical gradient ---
    top = (16, 26, 52)
    bot = (30, 48, 92)
    for y in range(H):
        t = y / (H - 1)
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        for x in range(W):
            m = in_rounded_rect(x, y)
            if m > 0:
                setpx(x, y, r, g, b, int(255 * m))

    # --- wireframe cube (slightly rotated, isometric-ish) ---
    # unit cube corners
    corners = []
    for i in range(8):
        corners.append(((i & 1) * 2 - 1, ((i >> 1) & 1) * 2 - 1, ((i >> 2) & 1) * 2 - 1))

    ax, ay = math.radians(24), math.radians(-18)
    def project(p):
        x, y, z = p
        # rotate around Y
        x1 = x * math.cos(ay) + z * math.sin(ay)
        z1 = -x * math.sin(ay) + z * math.cos(ay)
        # rotate around X
        y2 = y * math.cos(ax) - z1 * math.sin(ax)
        z2 = y * math.sin(ax) + z1 * math.cos(ax)
        s = 46.0
        return (96 + x1 * s, 92 + y2 * s)

    pts = [project(c) for c in corners]
    edges = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7),
             (0, 4), (1, 5), (2, 6), (3, 7)]

    def draw_line(x0, y0, x1, y1, r, g, b, thick=7):
        rad = thick / 2.0
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for s in range(steps + 1):
            t = s / steps
            cx = x0 + (x1 - x0) * t
            cy = y0 + (y1 - y0) * t
            for dy in range(int(-rad) - 1, int(rad) + 2):
                for dx in range(int(-rad) - 1, int(rad) + 2):
                    if dx * dx + dy * dy <= rad * rad:
                        setpx(int(cx + dx), int(cy + dy), r, g, b)

    for a, b in edges:
        draw_line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], 235, 242, 255)

    # --- a small green "run" dot (like a little ball to catch) ---
    for dy in range(-13, 14):
        for dx in range(-13, 14):
            if dx * dx + dy * dy <= 13 * 13:
                setpx(148 + dx, 140 + dy, 88, 214, 141)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'res', 'drawable-nodpi', 'ic_launcher.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    write_png(out, W, H, px)
    print('wrote %s' % out)


if __name__ == '__main__':
    main()
