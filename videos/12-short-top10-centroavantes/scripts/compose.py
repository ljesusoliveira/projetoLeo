"""Monta o vídeo 9:16 (sem áudio) do Short do Top 10 centroavantes seguindo o
edl.json. Para cada quadro: recorte do lance que acompanha a jogada (cx),
dentro da área com imagem (as faixas pretas laterais das imagens antigas são
detectadas e ficam de fora), fundo desfocado do próprio lance, correção de cor
e contraste (mais forte nas imagens antigas), grão de filme, punch-in de 8% no
gol, cortes secos no tempo da batida, flash nas viradas (TOP 3 e entrada de
cada jogador do Top 3), escurecimento para o suspense e a camada gráfica do
overlay.py. Nenhum quadro do nº1 é lido: os trechos vêm só do edl.json.
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
AR = W / BH


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
    """Interpolação suave (smoothstep) entre os pontos-chave do enquadramento."""
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
    """Área com imagem (sem faixas pretas) e níveis de cor do trecho, a partir de 3 quadros."""
    fr = [f for i, f in enumerate(read_frames(q['src'], q['n'])) if i in (2, q['n'] // 2, q['n'] - 3)]
    lum = np.mean([f.max(2) for f in fr], 0)
    cols = np.where(lum.mean(0) > 14)[0]
    rows = np.where(lum.mean(1) > 14)[0]
    x0, x1 = int(cols[0]) + 4, int(cols[-1]) - 4
    y0, y1 = int(rows[0]) + 4, int(rows[-1]) - 4
    y0, y1 = max(y0, q['y0']), min(y1, q['y1'])
    g = np.concatenate([cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).ravel()[::7] for f in fr])
    lo, hi = np.percentile(g, 1.0), np.percentile(g, 99.5)
    ch = np.mean([f[y0:y1, x0:x1].reshape(-1, 3)[::11].mean(0) for f in fr], 0)      # média B, G, R
    return dict(x0=x0, x1=x1, y0=y0, y1=y1, lo=float(lo), hi=float(hi), ch=ch.astype(np.float32))


def crop_rect(a, cx, zoom, zoom_y=0.5):
    ch = (a['y1'] - a['y0'])
    h = ch / zoom
    w = h * AR
    cw = a['x1'] - a['x0']
    if w > cw:                                          # imagem estreita (4:3): aproxima até caber
        w = cw
        h = w / AR
    x0 = min(max(cx * SW - w / 2, a['x0']), a['x1'] - w)
    yc = a['y0'] + zoom_y * ch
    ya = min(max(yc - h / 2, a['y0']), a['y1'] - h)
    return x0, ya, w, h


def band_of(src, rect):
    x0, y0, w, h = rect
    s = W / w
    M = np.float32([[s, 0, -s * x0], [0, s, -s * y0]])
    return cv2.warpAffine(src, M, (W, BH), flags=cv2.INTER_LINEAR if s < 1 else cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


LOOK = {                       # contraste, saturação, grão
    None: (0.10, 1.08, 3.5),
    'retro': (0.16, 1.18, 5.5),
    'bw': (0.30, 0.0, 7.5),
}


def grade(img, a, look, wb=0.0, sat=None):
    """Níveis automáticos (estica o preto e o branco do trecho), curva em S, saturação e
    nitidez. 'bw' (Vavá, Ademir): tira o tom roxo/sépia desbotado e deixa um preto e
    branco limpo, levemente quente."""
    con, sat0, _ = LOOK[look]
    sat = sat0 if sat is None else sat
    f = img.astype(np.float32)
    if wb:                                              # balanço de branco (mundo cinza), parcial
        f = f * (1 + wb * (a['ch'].mean() / a['ch'] - 1))
    span = max(40.0, a['hi'] - a['lo'])
    gain = min(1.7, 225.0 / span)
    f = (f - a['lo']) * gain + 12
    f = np.clip(f / 255.0, 0, 1)
    f = f + con * (f - 0.5) * (1 - np.abs(2 * f - 1))                  # curva em S
    g = (f @ np.array([0.114, 0.587, 0.299], np.float32))[..., None]
    if look == 'bw':
        f = g * np.array([0.93, 0.98, 1.04], np.float32)               # BGR: preto e branco quente
    else:
        f = g + (f - g) * sat
    out = np.clip(f * 255, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(out, (0, 0), 1.3)
    return cv2.addWeighted(out, 1.5, blur, -0.5, 0)


_RNG = np.random.default_rng(10)
_GRAIN = [_RNG.normal(0, 1, (BH // 2, W // 2)).astype(np.float32) for _ in range(8)]
_yy, _xx = np.mgrid[0:BH, 0:W].astype(np.float32)
_VIG = (1 - 0.30 * np.clip(np.sqrt(((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - BH / 2) / (BH / 2)) ** 2) - 0.6, 0, 1)
        ** 1.5)[..., None]


def film(band, n, amount):
    g = cv2.resize(_GRAIN[n % len(_GRAIN)], (W, BH), interpolation=cv2.INTER_LINEAR)[..., None]
    return np.clip(band.astype(np.float32) * _VIG + g * amount, 0, 255).astype(np.uint8)


def background(src, a, rect):
    x0, y0, w, h = rect
    cxp = x0 + w / 2
    bw = (a['y1'] - a['y0']) * W / H
    bx = int(min(max(cxp - bw / 2, a['x0']), max(a['x0'], a['x1'] - bw)))
    strip = src[a['y0']:a['y1'], bx:bx + int(bw)]
    small = cv2.resize(strip, (108, 192), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 3.5)
    bg = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    return np.clip(bg * 0.45, 0, 255).astype(np.uint8)


def rays_bg():
    """Fundo escuro com raios dourados (mesmo clima da abertura do vídeo longo)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, BY + BH * 0.45
    ang = np.arctan2(yy - cy, xx - cx)
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    rays = (0.5 + 0.5 * np.cos(ang * 18)) ** 6 * np.exp(-r / 900)
    glow = np.exp(-(r / 520) ** 2)
    base = 10 + 34 * glow[..., None] * np.array([0.35, 0.65, 1.0], np.float32)
    base += 40 * rays[..., None] * np.array([0.2, 0.62, 0.95], np.float32)
    return np.clip(base, 0, 255).astype(np.uint8)


RAYS = rays_bg()


def over(canvas, n):
    ov = np.asarray(overlay.render(n), dtype=np.float32)
    al = ov[..., 3:4] / 255.0
    return (canvas.astype(np.float32) * (1 - al) + ov[..., [2, 1, 0]] * al).astype(np.uint8)


def flash(canvas, a):
    return (canvas.astype(np.float32) * (1 - a) + 255 * a).astype(np.uint8) if a > 0.01 else canvas


def frames():
    """Gera (n, quadro BGR 1080x1920) em ordem."""
    n, last = 0, None
    for q in PIECES:
        if q['kind'] == 'src':
            a = analyze(q)
            z0, z1 = q.get('zoom', [1.0, 1.0])
            punches = [round((t - q['src']) * FPS) for t in q.get('punch', [])]
            grain = LOOK[q.get('look')][2]
            for k, fr in enumerate(read_frames(q['src'], q['n'])):
                t = q['src'] + k / FPS
                z = z0 + (z1 - z0) * smooth(k / max(1, q['n'] - 1))
                for pk in punches:                      # punch-in no gol: entra 8% e fica
                    if k >= pk:
                        z *= 1 + 0.08 * overlay.ease_out_cubic(min(1.0, (k - pk) / 3))
                rect = crop_rect(a, interp(q['cx'], t), z, q.get('zoom_y', 0.5))
                band = film(grade(band_of(fr, rect), a, q.get('look'), q.get('wb', 0.0), q.get('sat')), n, grain)
                canvas = background(fr, a, rect)
                canvas[BY:BY + BH] = band
                fa = 0.0
                if q.get('pos', 99) <= 3 and q['first'] and k < 6:   # entrada de cada um do Top 3
                    fa = 0.7 * (1 - k / 6)
                out = flash(over(canvas, n), fa)
                last = canvas
                yield n, out
                n += 1
            assert k == q['n'] - 1, (q['id'], k)
        elif q['kind'] == 'stinger':
            for k in range(q['n']):
                canvas = RAYS.copy()
                out = flash(over(canvas, n), 0.85 * max(0.0, 1 - k / 5))
                yield n, out
                n += 1
        else:                                           # suspense: escurece e fica no escuro
            dark = (last.astype(np.float32) * 0.35).astype(np.uint8) if last is not None else RAYS
            for k in range(q['n']):
                x = smooth(k / 12)
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
