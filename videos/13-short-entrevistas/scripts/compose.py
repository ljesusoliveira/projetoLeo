"""Monta o vídeo 9:16 (sem áudio) do Short das entrevistas mais engraçadas
seguindo o edl.json. Para cada quadro: recorte que acompanha quem está falando
(cx), dentro da área com imagem (faixas pretas e o selo do canal no canto ficam
de fora), fundo desfocado da própria imagem, cor levemente mais viva, zoom
curto (punch) na hora da piada, transição em chicote entre as entrevistas e nos
lampejos do final, e a camada gráfica do overlay.py.
  python3 compose.py video.mp4            -> vídeo completo (sem áudio)
  python3 compose.py preview q1 q2 ...    -> frames/prev_<q>.png
"""
import itertools
import subprocess
import sys

import cv2
import numpy as np

import overlay
from timeline import FPS, N, PIECES

SW, SH = 1920, 1080
W, H = overlay.W, overlay.H
BY, BH = overlay.BAND_Y, overlay.BAND_H
AR = W / BH
BADGE_X, BADGE_Y = 1740, 180      # selo do canal no canto de cima à direita do vídeo longo


def read_frames(t0, n):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{t0:.4f}', '-i', 'original.mp4',
                          '-frames:v', str(n), '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    sz = SW * SH * 3
    for _ in range(n):
        buf = p.stdout.read(sz)
        if len(buf) < sz:
            break
        yield np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
    p.stdout.close()
    p.wait()


def interp(keys, t):
    if not isinstance(keys, list):
        return keys
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            x = (t - t0) / max(1e-6, t1 - t0)
            return v0 + (v1 - v0) * x * x * (3 - 2 * x)
    return keys[-1][1]


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def analyze(q):
    """Área com imagem (sem faixas pretas), a partir de 3 quadros do trecho."""
    idx = {1, q['n'] // 2, max(1, q['n'] - 2)}
    fr = [f for i, f in enumerate(read_frames(q['src'], q['n'])) if i in idx]
    lum = np.mean([f.max(2) for f in fr], 0)
    cols = np.where(lum.mean(0) > 16)[0]
    rows = np.where(lum.mean(1) > 16)[0]
    return dict(x0=int(cols[0]) + 4, x1=int(cols[-1]) - 4, y0=int(rows[0]) + 4,
                y1=min(int(rows[-1]) - 4, q.get('y1', SH)))     # y1: corta legendas do próprio vídeo


def crop_rect(a, cx, zoom):
    ch = a['y1'] - a['y0']
    h = ch / zoom
    w = h * AR
    xmax = min(a['x1'], BADGE_X) if a['y0'] < BADGE_Y else a['x1']
    if w > xmax - a['x0']:
        w = xmax - a['x0']
        h = w / AR
    x0 = min(max(cx * SW - w / 2, a['x0']), xmax - w)
    yc = a['y0'] + 0.45 * ch                            # mira um pouco acima do centro (rostos)
    ya = min(max(yc - h / 2, a['y0']), a['y1'] - h)
    return x0, ya, w, h


def band_of(src, rect):
    x0, y0, w, h = rect
    s = W / w
    M = np.float32([[s, 0, -s * x0], [0, s, -s * y0]])
    return cv2.warpAffine(src, M, (W, BH), flags=cv2.INTER_LINEAR if s < 1 else cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def grade(img):
    """Cor levemente mais viva e nitidez suave (as entrevistas já vêm com cor boa)."""
    f = img.astype(np.float32) / 255.0
    f = f + 0.08 * (f - 0.5) * (1 - np.abs(2 * f - 1))
    g = (f @ np.array([0.114, 0.587, 0.299], np.float32))[..., None]
    f = g + (f - g) * 1.08
    out = np.clip(f * 255, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(out, (0, 0), 1.2)
    return cv2.addWeighted(out, 1.4, blur, -0.4, 0)


def background(src, a, rect):
    x0, y0, w, h = rect
    bw = (a['y1'] - a['y0']) * W / H
    bx = int(min(max(x0 + w / 2 - bw / 2, a['x0']), max(a['x0'], a['x1'] - bw)))
    strip = src[a['y0']:a['y1'], bx:bx + int(bw)]
    small = cv2.GaussianBlur(cv2.resize(strip, (108, 192), interpolation=cv2.INTER_AREA), (0, 0), 3.5)
    bg = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    return np.clip(bg * 0.42, 0, 255).astype(np.uint8)


WHIP_IN = [(55, 260), (37, 140), (21, 60), (9, 16)]


def whip(band, strength, shift):
    L = int(strength) | 1
    if L > 1:
        band = cv2.filter2D(band, -1, np.full((1, L), 1.0 / L, np.float32), borderType=cv2.BORDER_REFLECT)
    return np.roll(band, int(shift), axis=1) if shift else band


def rays_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, BY + BH * 0.45
    ang = np.arctan2(yy - cy, xx - cx)
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    rays = (0.5 + 0.5 * np.cos(ang * 18)) ** 6 * np.exp(-r / 900)
    glow = np.exp(-(r / 520) ** 2)
    base = 10 + 30 * glow[..., None] * np.array([0.3, 0.75, 1.0], np.float32)
    base += 36 * rays[..., None] * np.array([0.15, 0.7, 1.0], np.float32)
    return np.clip(base, 0, 255).astype(np.uint8)


RAYS = rays_bg()


def over(canvas, n):
    ov = np.asarray(overlay.render(n), dtype=np.float32)
    al = ov[..., 3:4] / 255.0
    return (canvas.astype(np.float32) * (1 - al) + ov[..., [2, 1, 0]] * al).astype(np.uint8)


def flash(canvas, a):
    return (canvas.astype(np.float32) * (1 - a) + 255 * a).astype(np.uint8) if a > 0.01 else canvas


def frames():
    n, last = 0, None
    for i, q in enumerate(PIECES):
        if q['kind'] in ('clip', 'flash'):
            a = analyze(q)
            punches = [round((t - q['src']) * FPS) for t in q.get('punch', [])]
            k = -1
            held = None
            off = round((q.get('video_from', q['src']) - q['src']) * FPS)    # quadros de transição do vídeo longo
            gen = read_frames(q['src'] + off / FPS, q['n'] - off)
            first = next(gen)
            for k, fr in enumerate(itertools.chain([first] * (off + 1), gen)):
                t = q['src'] + k / FPS
                if t > q.get('freeze_after', 1e9):                         # imagem parada: o vídeo longo já trocou
                    fr = held
                held = fr
                if q['kind'] == 'clip':
                    z = 1.0 + 0.04 * smooth(k / max(1, q['n'] - 1))          # aproximação lenta e constante
                else:
                    z = 1.06 + 0.06 * smooth(k / max(1, q['n'] - 1))
                for pk in punches:                                         # punch na piada: entra 7% e volta
                    if 0 <= k - pk < 24:
                        j = k - pk
                        z *= 1 + 0.07 * (min(1.0, j / 3) if j < 3 else max(0.0, 1 - (j - 3) / 21) ** 2)
                rect = crop_rect(a, interp(q['cx'], t), z)
                band = grade(band_of(fr, rect))
                if i > 0 and k < len(WHIP_IN):                             # chicote na entrada
                    band = whip(band, *WHIP_IN[k])
                canvas = background(fr, a, rect)
                canvas[BY:BY + BH] = band
                fa = 0.0
                if q['kind'] == 'flash' and k < 3:
                    fa = 0.5 * (1 - k / 3)
                last = canvas
                yield n, flash(over(canvas, n), fa)
                n += 1
            assert k == q['n'] - 1, (q['id'], k)
        else:                                                              # encerramento
            dark = (last.astype(np.float32) * 0.4).astype(np.uint8)
            for k in range(q['n']):
                x = smooth(k / 10)
                canvas = (dark.astype(np.float32) * (1 - x) + RAYS.astype(np.float32) * x).astype(np.uint8)
                yield n, over(canvas, n)
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
                                '-color_trc', 'bt709', '-color_range', 'tv', sys.argv[1]], stdin=subprocess.PIPE)
        for n, img in frames():
            enc.stdin.write(img.tobytes())
            if n % 150 == 0:
                print(f'quadro {n}/{N}', flush=True)
        enc.stdin.close()
        enc.wait()
