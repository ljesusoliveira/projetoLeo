"""Monta o vídeo 9:16 (sem áudio) do Short do Catê seguindo o edl.json.
Para cada quadro: recorte da imagem (cx), fundo desfocado da própria imagem,
movimento constante, "punch" (zoom curto) nos cortes, correção de cor (passado
quente; 2011 em preto e branco frio com chuva), grão de filme, vinheta, flash,
tremida e escurecimento nas viradas, e a camada gráfica do overlay.py.
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
    yc = y0 + q.get('zoom_y', 0.5) * (y1 - y0)       # ponto que a aproximação mira
    ya = min(max(yc - h / 2, y0), y1 - h)
    return x0, ya, w, h


def band_of(src, rect):
    x0, y0, w, h = rect
    s = W / w
    M = np.float32([[s, 0, -s * x0], [0, s, -s * y0]])
    return cv2.warpAffine(src, M, (W, BH), flags=cv2.INTER_LINEAR if s < 1 else cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def grade(img, desat=0.0, cold=False):
    """Cor: contraste e saturação para as imagens antigas ficarem mais vivas, com um tom
    levemente quente (nostalgia). 'cold' = preto e branco frio (o presente, 2011)."""
    f = img.astype(np.float32)
    f = (f - 128) * 1.10 + 128                       # contraste
    g = f.mean(2, keepdims=True)
    if cold:
        f = g * np.array([1.07, 1.0, 0.92], np.float32) * 0.9   # BGR: puxa para o azul
    else:
        f = g + (f - g) * (1.18 * (1 - desat))       # saturação
        f = f * np.array([0.96, 1.0, 1.05], np.float32)          # tom quente
        if desat:
            f = f * (1 - 0.15 * desat)
    out = np.clip(f, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(out, (0, 0), 1.3)
    return cv2.addWeighted(out, 1.45, blur, -0.45, 0)  # nitidez suave


_RNG = np.random.default_rng(7)
_GRAIN = [(_RNG.normal(0, 1, (BH // 2, W // 2)).astype(np.float32)) for _ in range(8)]
_VIG = None


def film(band, n, amount=5.5):
    """Grão de filme (muda a cada quadro) e vinheta suave."""
    global _VIG
    if _VIG is None:
        yy, xx = np.mgrid[0:BH, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - BH / 2) / (BH / 2)) ** 2)
        _VIG = (1 - 0.32 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None]
    g = cv2.resize(_GRAIN[n % len(_GRAIN)], (W, BH), interpolation=cv2.INTER_LINEAR)[..., None]
    f = band.astype(np.float32) * _VIG + g * amount
    return np.clip(f, 0, 255).astype(np.uint8)


_DROPS = None


def rain(band, n):
    """Chuva (só imagem): riscos claros e finos caindo em diagonal."""
    global _DROPS
    rng = np.random.default_rng(3)
    if _DROPS is None:
        _DROPS = np.stack([rng.uniform(0, W, 260), rng.uniform(0, BH, 260), rng.uniform(26, 60, 260),
                           rng.uniform(0.35, 1.0, 260)], 1)
    lay = np.zeros((BH, W), np.float32)
    for x, y, ln, a in _DROPS:
        yy = (y + n * 38 * a * 1.6) % (BH + 80) - 40
        xx = (x - n * 6 * a) % W
        cv2.line(lay, (int(xx), int(yy)), (int(xx - ln * 0.18), int(yy + ln)), float(a), 1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 0.8)[..., None]
    f = band.astype(np.float32) * 0.86 + lay * 95
    return np.clip(f, 0, 255).astype(np.uint8)


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
    cold = q.get('look') == 'frio'
    rect = crop_rect(q, cx, zoom)
    band = grade(band_of(src, rect), desat, cold)
    if q.get('gain'):                                  # imagem de origem escura: mais exposição
        band = np.clip(band.astype(np.float32) * q['gain'], 0, 255).astype(np.uint8)
    bg = background(src[q['y0']:q['y1']], cx, 1.0 if cold else desat)   # só a área usada
    if extra.get('blur', 0) > 0.3:
        band = cv2.GaussianBlur(band, (0, 0), extra['blur'])
    if cold:
        band = rain(band, n)
    band = film(band, n)
    if extra.get('endcard'):
        band = (cv2.GaussianBlur(band, (0, 0), 7) * 0.32).astype(np.uint8)
    if extra.get('dim', 1.0) < 1.0:
        band = (band.astype(np.float32) * extra['dim']).astype(np.uint8)
    if extra.get('shake'):
        a = extra['shake']
        dx, dy = int(a * 12 * np.sin(k * 2.9)), int(a * 8 * np.cos(k * 3.7))
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


def cx_at(q, t):
    return interp(q['cx'], t) if isinstance(q['cx'], list) else q['cx']


PUNCH_F = 7


def effects(q, k, n):
    """Efeitos do quadro k do trecho q (n = quadro do Short)."""
    extra = {}
    x = smooth(k / max(1, q['n'] - 1))
    if q.get('desat_from_f') is not None:              # a cor some a partir de um instante
        j = n - q['desat_from_f']
        if j > 0:
            extra['desat'] = 0.85 * smooth(min(1.0, j / 12))
    if q.get('endcard'):
        extra['endcard'] = True
    if q.get('darken'):                                # respiro: a imagem escurece
        extra['desat'] = 0.85
        extra['dim'] = 1 - 0.75 * x
    if q.get('reveal') and k < 18:                     # revelação: entra desfocado e ganha foco
        extra['blur'] = 14 * (1 - smooth(k / 17))
    if q.get('fade_in') and k < 10:                    # volta do escuro
        extra['dim'] = 0.25 + 0.75 * smooth(k / 9)
    hits = []
    if q.get('flash_in'):
        hits.append(q['start'])
    if q.get('hit_f') is not None:
        hits.append(q['hit_f'])
    for h in hits:
        if 0 <= n - h < 9:
            j = n - h
            extra['flash'] = max(extra.get('flash', 0), 0.8 * (1 - j / 6))
            extra['shake'] = max(extra.get('shake', 0), 0.8 * (1 - j / 9))
    if q.get('shake_at_f') is not None and 0 <= n - q['shake_at_f'] < 10:
        extra['shake'] = max(extra.get('shake', 0), 0.7 * (1 - (n - q['shake_at_f']) / 10))
    return extra


def zoom_at(q, k):
    z0, z1 = q.get('zoom', [1.0, 1.0])
    z = z0 + (z1 - z0) * smooth(k / max(1, q['n'] - 1))
    p = q.get('punch')
    if p and k < PUNCH_F:                              # corte com "punch": entra mais perto e assenta
        amp = 0.07 if p is True else p
        z *= 1 + amp * (1 - overlay.ease_out_cubic(k / PUNCH_F))
    return z


def frames():
    """Gera (n, quadro BGR 1080x1920) em ordem."""
    last = {}
    n = 0
    for q in PIECES:
        if q['kind'] == 'src':
            fr = None
            for k, fr in enumerate(read_frames(q['src'], q['n'])):
                yield n, compose(n, fr, q, cx_at(q, q['src'] + k / FPS), zoom_at(q, k), k, effects(q, k, n))
                n += 1
            assert fr is not None and k == q['n'] - 1, (q['id'], k)
            last[q['id']] = fr
        else:
            fr = last[q['of']]
            for k in range(q['n']):
                yield n, compose(n, fr, q, cx_at(q, 0), zoom_at(q, k), k, effects(q, k, n))
                n += 1
            last[q['id']] = fr
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
