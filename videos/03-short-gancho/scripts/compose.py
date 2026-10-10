"""Monta o vídeo 9:16 (sem áudio) do Short-gancho seguindo o edl.json.
Para cada quadro: recorte do lance que acompanha a jogada (cx), fundo
desfocado do próprio lance, congelamentos com zoom, flash, efeito de fita
na rebobinada e a camada gráfica do overlay.py.
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
BADGE_X = 1760                    # selo do canal no canto (x >= 1762, y >= 886)


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
    xmax = BADGE_X if y1 > 886 else SW
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


def vhs(img, k):
    """Efeito de fita rebobinando: canais deslocados, linhas e ruído."""
    out = img.copy()
    out[..., 2] = np.roll(img[..., 2], 7, axis=1)
    out[..., 0] = np.roll(img[..., 0], -7, axis=1)
    out[::3] = (out[::3] * 0.72).astype(np.uint8)
    rng = np.random.default_rng(k)
    noise = rng.normal(0, 14, out.shape[:2]).astype(np.float32)[..., None]
    y = int((k * 97) % out.shape[0])
    out[y:y + 26] = np.roll(out[y:y + 26], 40, axis=1)
    return np.clip(out.astype(np.float32) * 1.08 + noise, 0, 255).astype(np.uint8)


def compose(n, src, q, cx, zoom, k, extra):
    desat = extra.get('desat', 0.0)
    rect = crop_rect(q, cx, zoom)
    band = grade(band_of(src, rect), desat)
    bg = background(src, cx, desat)
    if extra.get('endcard'):
        band = (cv2.GaussianBlur(band, (0, 0), 5) * 0.42).astype(np.uint8)
    if extra.get('vhs'):
        band = vhs(band, k)
        bg = vhs(bg, k + 1000)
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
    last, tail = {}, {}
    n = 0
    for q in PIECES:
        if q['kind'] == 'src':
            t0 = q['src'][0]
            keep = []
            for k, fr in enumerate(read_frames(t0, q['n'])):
                cx = interp(q['cx'], t0 + k / FPS)
                yield n, compose(n, fr, q, cx, 1.0, k, {})
                keep.append(fr)
                keep = keep[-60:]
                n += 1
            last[q['id']] = (keep[-1], q, interp(q['cx'], q['src'][1]))
            tail[q['id']] = keep
        elif q['kind'] == 'freeze':
            fr, base, cx = last[q['of']]
            z0, z1 = q.get('zoom', [1.0, 1.0])
            for k in range(q['n']):
                x = smooth(k / max(1, q['n'] - 1))
                extra = {}
                if q.get('flash'):
                    extra['flash'] = max(0.0, 0.85 * (1 - k / 6))
                if q.get('desat'):
                    extra['desat'] = 0.75 * x
                if q.get('endcard'):
                    extra['desat'] = 0.75
                    extra['endcard'] = True
                yield n, compose(n, fr, base, cx, z0 + (z1 - z0) * x, k, extra)
                n += 1
            last[q['id']] = (fr, base, cx)
        else:  # rebobinada: últimos quadros do trecho anterior, de trás para frente, em 2x
            seq = tail[q['of']][::-1][::2]
            base = PIECES[[p['id'] for p in PIECES].index(q['of'])]
            cx = base['cx'][-1][1]
            for k in range(q['n']):
                fr = seq[min(k, len(seq) - 1)]
                yield n, compose(n, fr, base, cx, 1.0 + 0.06 * k / q['n'], k, {'vhs': True})
                n += 1
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
