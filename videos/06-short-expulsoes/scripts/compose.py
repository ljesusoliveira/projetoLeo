"""Monta o vídeo 9:16 (sem áudio) do Short das expulsões seguindo o edl.json.
Para cada quadro: recorte do lance que acompanha a jogada (cx), fundo
desfocado do próprio lance, aproximação suave, congelamentos com zoom,
flash, tremida no impacto e a camada gráfica do overlay.py.
  python3 compose.py video.mp4            -> vídeo completo (sem áudio)
  python3 compose.py preview q1 q2 ...    -> frames/prev_<q>.png
"""
import subprocess
import sys

import cv2
import numpy as np

import overlay
from timeline import FPS, N, PIECES

SW, SH = 1920, 1080
W, H = overlay.W, overlay.H
BY, BH = overlay.BAND_Y, overlay.BAND_H
AR = W / BH                       # proporção da faixa do vídeo
BADGE_X, BADGE_Y = 1740, 180      # selo do canal no canto de cima (x >= 1747, y <= 175)


def read_frames(t0, n):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-i', 'original.mp4',
                          '-frames:v', str(n), '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
                         stdout=subprocess.PIPE)
    sz = SW * SH * 3
    for _ in range(n):
        buf = p.stdout.read(sz)
        if len(buf) < sz:
            break
        yield np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
    p.stdout.close()
    p.wait()


def interp(keys, t):
    """Interpolação suave (smoothstep) entre os pontos-chave do enquadramento."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            x = (t - t0) / max(1e-6, t1 - t0)
            return v0 + (v1 - v0) * x * x * (3 - 2 * x)
    return keys[-1][1]


def smooth(x):
    return x * x * (3 - 2 * x)


def crop_rect(q, cx, zoom):
    y0, y1 = q['y0'], q['y1']
    h = (y1 - y0) / zoom
    w = h * AR
    xmax = BADGE_X if y0 < BADGE_Y else SW
    x0 = min(max(cx * SW - w / 2, 0), xmax - w)
    yc = (y0 + y1) / 2
    ya = min(max(yc - h / 2, y0), y1 - h)
    return x0, ya, w, h


def band_of(src, rect):
    x0, y0, w, h = rect
    s = W / w
    M = np.float32([[s, 0, -s * x0], [0, s, -s * y0]])
    return cv2.warpAffine(src, M, (W, BH), flags=cv2.INTER_LINEAR if s < 1 else cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def grade(img, desat=0.0):
    f = img.astype(np.float32)
    f = (f - 128) * 1.06 + 128                       # contraste leve
    g = f.mean(2, keepdims=True)
    sat = 1.14 * (1 - desat) + 0.0 * desat
    f = g + (f - g) * sat                             # saturação
    if desat:
        f = f * (1 - 0.18 * desat)
    out = np.clip(f, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(out, (0, 0), 1.3)
    return cv2.addWeighted(out, 1.45, blur, -0.45, 0)  # nitidez suave


def background(src, cx, desat=0.0):
    w = SH * W / H
    x0 = int(min(max(cx * SW - w / 2, 0), SW - w))
    strip = src[:, x0:x0 + int(w)]
    small = cv2.resize(strip, (108, 192), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 3.5)
    bg = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    g = bg.mean(2, keepdims=True)
    bg = g + (bg - g) * (1.3 * (1 - desat))
    return np.clip(bg * 0.5, 0, 255).astype(np.uint8)


def compose(n, src, q, cx, zoom, k, extra):
    desat = extra.get('desat', 0.0)
    rect = crop_rect(q, cx, zoom)
    band = grade(band_of(src, rect), desat)
    bg = background(src, cx, desat)
    if extra.get('endcard'):
        band = (cv2.GaussianBlur(band, (0, 0), 5) * 0.42).astype(np.uint8)
    if extra.get('shake'):
        a = extra['shake']
        dx, dy = int(a * 14 * np.sin(k * 2.9)), int(a * 10 * np.cos(k * 3.7))
        band = np.roll(np.roll(band, dx, axis=1), dy, axis=0)
    canvas = bg
    canvas[BY:BY + BH] = band
    if extra.get('flash', 0) > 0:
        a = extra['flash']
        canvas = (canvas.astype(np.float32) * (1 - a) + 255 * a).astype(np.uint8)
    ov = np.asarray(overlay.render(n), dtype=np.float32)
    al = ov[..., 3:4] / 255.0
    rgb = ov[..., [2, 1, 0]]
    return (canvas.astype(np.float32) * (1 - al) + rgb * al).astype(np.uint8)


def frames():
    """Gera (n, quadro BGR 1080x1920) em ordem."""
    last = {}
    n = 0
    for q in PIECES:
        if q['kind'] == 'src':
            t0 = q['src'][0]
            z0, z1 = q.get('zoom', [1.0, 1.0])
            fr = None
            for k, fr in enumerate(read_frames(t0, q['n'])):
                cx = interp(q['cx'], t0 + k / FPS)
                z = z0 + (z1 - z0) * smooth(k / max(1, q['n'] - 1))
                yield n, compose(n, fr, q, cx, z, k, {})
                n += 1
            last[q['id']] = (fr, q, interp(q['cx'], q['src'][1]), z1)
        else:
            fr, base, cx, _ = last[q['of']]
            z0, z1 = q.get('zoom', [1.0, 1.0])
            for k in range(q['n']):
                x = smooth(k / max(1, q['n'] - 1))
                extra = {}
                if q.get('flash'):
                    extra['flash'] = max(0.0, 0.85 * (1 - k / 6))
                    extra['shake'] = max(0.0, 1 - k / 9)
                if q.get('desat'):
                    extra['desat'] = 0.75 * x
                if q.get('endcard'):
                    extra['desat'] = 0.75
                    extra['endcard'] = True
                yield n, compose(n, fr, base, cx, z0 + (z1 - z0) * x, k, extra)
                n += 1
            last[q['id']] = (fr, base, cx, z1)
    assert n == N, (n, N)


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        want = {int(x) for x in sys.argv[2:]}
        for n, img in frames():
            if n in want:
                cv2.imwrite(f'frames/prev_{n:05d}.png', img)
                want.discard(n)
                if not want:
                    break
    else:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
                                '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                '-c:v', 'libx264', '-preset', 'slow', '-crf', '14',
                                '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                                '-color_trc', 'bt709', '-color_range', 'tv', sys.argv[1]],
                               stdin=subprocess.PIPE)
        for n, img in frames():
            enc.stdin.write(img.tobytes())
            if n % 150 == 0:
                print(f'quadro {n}/{N}', flush=True)
        enc.stdin.close()
        enc.wait()
