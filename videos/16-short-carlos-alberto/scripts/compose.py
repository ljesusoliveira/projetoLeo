"""Monta o vídeo 9:16 (sem áudio) do Short do Carlos Alberto Torres seguindo o edl.json.
Para cada quadro: recorte da imagem (cx) sempre dentro da área com imagem (as
faixas pretas das fotos ficam de fora), fundo desfocado da própria imagem,
movimento constante, tom de cinema ou sépia, punch-in nas palavras-chave, as
transições (chicote, flash com tremida, desfoque que ganha foco, escurecimento,
brilho quente), grão de filme, vinheta, a camada
animada do Remotion (frames/remotion/) e a camada gráfica do overlay.py.
  python3 compose.py video.mp4            -> vídeo completo (sem áudio)
  python3 compose.py preview q1 q2 ...    -> frames/prev_<q>.png
"""
import glob
import os
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


def one_frame(t):
    return next(read_frames(t, 1))


def content_box(frames_):
    """Área com imagem (sem faixas pretas), a partir de alguns quadros."""
    lum = np.mean([f.max(2) for f in frames_], 0)
    cols = np.where(lum.mean(0) > 16)[0]
    rows = np.where(lum.mean(1) > 16)[0]
    return dict(x0=int(cols[0]) + 4, x1=int(cols[-1]) - 4, y0=int(rows[0]) + 4, y1=int(rows[-1]) - 4)


def analyze(t0, n):
    idx = {1, n // 2, max(1, n - 2)}
    return content_box([f for i, f in enumerate(read_frames(t0, n)) if i in idx])


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


def crop_rect(q, cx, zoom, box, ar=AR):
    """Recorte com proporção ar, centrado em cx, sempre dentro da área com imagem."""
    y0, y1 = max(q['y0'], box['y0']), min(q['y1'], box['y1'])
    xmin, xmax = max(box['x0'], q.get('x0', 0)), min(box['x1'], q.get('x1', SW))   # x0/x1: limites da foto
    if y0 < BADGE_Y:
        xmax = min(xmax, BADGE_X)
    h = (y1 - y0) / zoom
    w = h * ar
    if w > xmax - xmin:                                # imagem estreita: aproxima até caber
        w = xmax - xmin
        h = w / ar
    x0 = min(max(cx * SW - w / 2, xmin), xmax - w)
    yc = y0 + q.get('zoom_y', 0.5) * (y1 - y0)       # ponto que a aproximação mira
    ya = min(max(yc - h / 2, y0), y1 - h)
    return x0, ya, w, h


def band_of(src, rect, out_w=W):
    x0, y0, w, h = rect
    sc = out_w / w
    M = np.float32([[sc, 0, -sc * x0], [0, sc, -sc * y0]])
    return cv2.warpAffine(src, M, (out_w, BH), flags=cv2.INTER_LINEAR if sc < 1 else cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def grade(img, sepia=0.0, desat=0.0):
    """Tom de cinema: contraste em S, sombras puxando para o azul-esverdeado e luzes
    para o quente. 'sepia' (0 a 1) mistura para o monocromático sépia."""
    f = img.astype(np.float32) / 255.0
    f = f + 0.18 * (f - 0.5) * (1 - np.abs(2 * f - 1))            # curva em S suave
    lum = f @ np.array([0.114, 0.587, 0.299], np.float32)
    lum = lum[..., None]
    sh = np.clip(1 - lum * 2, 0, 1)                                 # peso das sombras
    hi = np.clip(lum * 2 - 1, 0, 1)                                 # peso das luzes
    f = f + sh * np.array([0.045, 0.02, -0.035], np.float32) + hi * np.array([-0.045, 0.0, 0.04], np.float32)
    g = f @ np.array([0.114, 0.587, 0.299], np.float32)
    g = g[..., None]
    f = g + (f - g) * (0.92 * (1 - desat))                          # saturação levemente contida
    if sepia > 0:
        sep = g * np.array([0.72, 0.88, 1.04], np.float32)          # BGR
        f = f * (1 - sepia) + sep * sepia
    out = np.clip(f * 255, 0, 255).astype(np.uint8)
    blur = cv2.GaussianBlur(out, (0, 0), 1.3)
    return cv2.addWeighted(out, 1.45, blur, -0.45, 0)              # nitidez suave


_RNG = np.random.default_rng(11)
_GRAIN = [(_RNG.normal(0, 1, (BH // 2, W // 2)).astype(np.float32)) for _ in range(8)]
_VIG = None


def film(band, n, amount=4.5):
    """Grão de filme (muda a cada quadro) e vinheta suave."""
    global _VIG
    if _VIG is None:
        yy, xx = np.mgrid[0:BH, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - BH / 2) / (BH / 2)) ** 2)
        _VIG = (1 - 0.28 * np.clip(r - 0.6, 0, 1) ** 1.5)[..., None]
    g = cv2.resize(_GRAIN[n % len(_GRAIN)], (W, BH), interpolation=cv2.INTER_LINEAR)[..., None]
    f = band.astype(np.float32) * _VIG + g * amount
    return np.clip(f, 0, 255).astype(np.uint8)


def whip(band, strength, shift):
    """Chicote: borrão horizontal de movimento + deslocamento."""
    L = int(strength) | 1
    if L > 1:
        k = np.full((1, L), 1.0 / L, np.float32)
        band = cv2.filter2D(band, -1, k, borderType=cv2.BORDER_REFLECT)
    if shift:
        band = np.roll(band, int(shift), axis=1)
    return band


def leak(band, x):
    """Brilho quente que atravessa a imagem (x de 0 a 1)."""
    yy, xx = np.mgrid[0:BH:4, 0:W:4].astype(np.float32)
    cx = -0.2 * W + x * 1.4 * W
    m = np.exp(-(((xx - cx) / (W * 0.28)) ** 2 + ((yy - BH * 0.35) / (BH * 0.6)) ** 2))
    m = cv2.resize(m, (W, BH))[..., None] * 0.55 * np.sin(np.pi * x)
    f = band.astype(np.float32) + m * np.array([40, 130, 255], np.float32)
    return np.clip(f, 0, 255).astype(np.uint8)


def background(src, box, rect, desat=0.0):
    x0, y0, w, h = rect
    bw = (box['y1'] - box['y0']) * W / H
    bx = int(min(max(x0 + w / 2 - bw / 2, box['x0']), max(box['x0'], box['x1'] - bw)))
    strip = src[box['y0']:box['y1'], bx:bx + int(bw)]
    small = cv2.GaussianBlur(cv2.resize(strip, (108, 192), interpolation=cv2.INTER_AREA), (0, 0), 3.5)
    bg = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    g = bg.mean(2, keepdims=True)
    bg = g + (bg - g) * (1.3 * (1 - desat))
    return np.clip(bg * 0.5, 0, 255).astype(np.uint8)


# camada animada do Remotion (PNG com transparência, um por quadro do Short)
REMOTION = {}
for p in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frames', 'remotion', 'element-*.png')):
    REMOTION[int(os.path.basename(p)[8:-4])] = p


def over_png(canvas, path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None or im[..., 3].max() == 0:
        return canvas
    al = im[..., 3:4].astype(np.float32) / 255.0
    return (canvas.astype(np.float32) * (1 - al) + im[..., :3].astype(np.float32) * al).astype(np.uint8)


def finish_band(band, n, k, extra):
    sep = extra.get('sepia', 0.0)
    band = grade(band, sep)
    if extra.get('blur', 0) > 0.3:
        band = cv2.GaussianBlur(band, (0, 0), extra['blur'])
    if extra.get('leak') is not None:
        band = leak(band, extra['leak'])
    band = film(band, n)
    if extra.get('whip'):
        band = whip(band, *extra['whip'])
    if extra.get('endcard'):
        band = (cv2.GaussianBlur(band, (0, 0), 9) * 0.28).astype(np.uint8)
    if extra.get('dim', 1.0) < 1.0:
        band = (band.astype(np.float32) * extra['dim']).astype(np.uint8)
    if extra.get('shake'):
        sa = extra['shake']
        dx, dy = int(sa * 12 * np.sin(k * 2.9)), int(sa * 8 * np.cos(k * 3.7))
        band = np.roll(np.roll(band, dx, axis=1), dy, axis=0)
    return band


def layers(canvas, n, extra):
    if extra.get('flash', 0) > 0:
        fa = extra['flash']
        canvas = (canvas.astype(np.float32) * (1 - fa) + 255 * fa).astype(np.uint8)
    if n in REMOTION:
        canvas = over_png(canvas, REMOTION[n])
    ov = np.asarray(overlay.render(n), dtype=np.float32)
    al = ov[..., 3:4] / 255.0
    rgb = ov[..., [2, 1, 0]]
    return (canvas.astype(np.float32) * (1 - al) + rgb * al).astype(np.uint8)


def compose(n, src, q, cx, zoom, k, extra, box):
    rect = crop_rect(q, cx, zoom, box)
    band = finish_band(band_of(src, rect), n, k, extra)
    canvas = background(src, box, rect, max(extra.get('sepia', 0.0), 0.3))
    canvas[BY:BY + BH] = band
    return layers(canvas, n, extra)


HALF = W // 2


def split_parts(q):
    """Os dois lados da tela dividida: (quadro, área, recorte) de cada um."""
    parts = []
    for side in ('left', 'right'):
        c = q[side]
        fr = one_frame(c['src'])
        box = content_box([fr])
        rect = crop_rect(dict(q, zoom_y=c.get('zoom_y', 0.5)), c['cx'], c.get('zoom', 1.0), box, HALF / BH)
        parts.append((fr, box, rect))
    return parts


def compose_split(n, parts, k, extra, slide=0.0):
    halves = [band_of(fr, rect, HALF) for fr, box, rect in parts]
    if slide > 0:                                      # entrada: cada lado desliza do seu canto
        off = int(HALF * slide)
        halves[0] = np.roll(halves[0], -off, axis=1)
        halves[0][:, HALF - off:] = 0
        halves[1] = np.roll(halves[1], off, axis=1)
        halves[1][:, :off] = 0
    band = finish_band(np.concatenate(halves, 1), n, k, extra)
    band[:, HALF - 4:HALF + 4] = (48, 194, 242)        # divisória dourada (BGR)
    fr, box, rect = parts[0]
    canvas = background(fr, box, rect, 0.5)
    canvas[BY:BY + BH] = band
    return layers(canvas, n, extra)


def cx_at(q, t):
    return interp(q['cx'], t) if isinstance(q['cx'], list) else q['cx']


PUNCH_F = 7


WHIP_IN = [(61, 300), (45, 170), (29, 80), (15, 28), (5, 0)]
WHIP_OUT = [(9, -24), (23, -80), (43, -180), (61, -300)]


def effects(q, k, n):
    """Efeitos do quadro k do trecho q (n = quadro do Short)."""
    extra = {}
    look = q.get('look')
    if look == 'sepia':
        extra['sepia'] = 1.0
    if q.get('color_in') and k < 14:                   # a cor volta depois da sépia
        extra['sepia'] = 1 - smooth(k / 13)
    if q.get('to_sepia_f') is not None and n >= q['to_sepia_f']:
        extra['sepia'] = smooth(min(1.0, (n - q['to_sepia_f']) / 40))
    if q.get('dim_f') is not None and n >= q['dim_f']:
        extra['dim'] = 1 - 0.55 * smooth(min(1.0, (n - q['dim_f']) / 20))
    if q.get('endcard'):
        extra['endcard'] = True
        extra['sepia'] = 0.6
    if q.get('whip') and k < len(WHIP_IN):
        extra['whip'] = WHIP_IN[k]
    j = q['n'] - 1 - k
    if q.get('whip_out') and j < len(WHIP_OUT):
        extra['whip'] = WHIP_OUT[len(WHIP_OUT) - 1 - j]
    for t in q.get('leak_f', []):
        if 0 <= n - t < 16:
            extra['leak'] = (n - t) / 15
    for t in q.get('flash_f', []):                     # flash curto com tremida
        if 0 <= n - t < 9:
            jj = n - t
            extra['flash'] = max(extra.get('flash', 0), 0.75 * (1 - jj / 6))
            extra['shake'] = max(extra.get('shake', 0), 0.8 * (1 - jj / 9))
    if q.get('reveal') and k < 18:                     # desfoque que ganha foco
        extra['blur'] = 14 * (1 - smooth(k / 17))
    if q.get('fade_in') and k < 9:                     # volta do escuro
        extra['dim'] = min(extra.get('dim', 1.0), 0.1 + 0.9 * smooth(k / 8))
    if q.get('fade_out') and j < 8:                    # escurece antes do corte
        extra['dim'] = min(extra.get('dim', 1.0), 0.1 + 0.9 * smooth(j / 7))
    return extra


def zoom_at(q, k, n):
    z0, z1 = q.get('zoom', [1.0, 1.0])
    z = z0 + (z1 - z0) * smooth(k / max(1, q['n'] - 1))
    for t in q.get('punch_f', []):                     # punch-in na palavra: entra 8% e fica
        if n >= t:
            z *= 1 + 0.08 * overlay.ease_out_cubic(min(1.0, (n - t) / 3))
    return z


def frames():
    """Gera (n, quadro BGR 1080x1920) em ordem."""
    last = {}
    n = 0
    for q in PIECES:
        if q['kind'] == 'src':
            box = analyze(q['src'], q['n'])
            fr = None
            for k, fr in enumerate(read_frames(q['src'], q['n'])):
                yield n, compose(n, fr, q, cx_at(q, q['src'] + k / FPS), zoom_at(q, k, n), k, effects(q, k, n), box)
                n += 1
            assert fr is not None and k == q['n'] - 1, (q['id'], k)
            last[q['id']] = ('src', fr, box)
        elif q['kind'] == 'split':
            parts = split_parts(q)
            for k in range(q['n']):
                ex = effects(dict(q, whip=False), k, n)
                slide = (1 - overlay.ease_out_cubic(min(1.0, k / 8))) if k < 8 else 0.0
                yield n, compose_split(n, parts, k, ex, slide)
                n += 1
            last[q['id']] = ('split', parts, None)
        else:
            kind, a, b = last[q['of']]
            for k in range(q['n']):
                ex = effects(q, k, n)
                if q.get('dark'):                      # respiro no escuro entre os capítulos
                    ex['dim'] = 0.1
                if kind == 'split':
                    yield n, compose_split(n, a, k, ex)
                else:
                    yield n, compose(n, a, q, cx_at(q, 0), zoom_at(q, k, n), k, ex, b)
                n += 1
            last[q['id']] = (kind, a, b)
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
