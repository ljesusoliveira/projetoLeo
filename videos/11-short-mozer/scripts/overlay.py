"""Camada gráfica (RGBA 1080x1920) do Short do Mozer: título que conversa com o
título do Short, carimbos de data datilografados, textos grandes (números e
palavras de impacto), placas brancas com barra vermelha, legenda da narração
por cima da imagem, encerramento e barra de progresso. Respeita as áreas seguras: nada acima de
y=288 nem abaixo de y=1536.
  python3 overlay.py preview <quadro> [...]  -> frames/ov_<quadro>.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from timeline import BIG, CAPTIONS, CHAPTERS, EDL, END_A, END_TITLE_LINES, FPS, LOWER, N, STAMPS, TITLE


HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'fonts')
EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

W, H = 1080, 1920
BAND_Y, BAND_H = 440, 1060         # faixa do vídeo (quase quadrada)
BAND_BOT = BAND_Y + BAND_H
BAR_H = 10
BRAND_CY = 128
TITLE_CY = 322

YEL = (255, 214, 10, 255)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
RED = (229, 9, 20, 255)


def anton(size):
    return ImageFont.truetype(os.path.join(FONTS, 'Anton-Regular.ttf'), size,
                              layout_engine=ImageFont.Layout.RAQM)


def mont(size, wght=800):
    f = ImageFont.truetype(os.path.join(FONTS, 'Montserrat.ttf'), size,
                           layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_axes([wght])
    return f


_EMOJI = ImageFont.truetype(EMOJI_FONT, 109, layout_engine=ImageFont.Layout.RAQM)
_emoji_cache = {}


def emoji(ch, height):
    key = (ch, height)
    if key not in _emoji_cache:
        im = Image.new('RGBA', (180, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((4, 4), ch, font=_EMOJI, embedded_color=True)
        im = im.crop(im.getbbox())
        r = height / im.height
        _emoji_cache[key] = im.resize((max(1, round(im.width * r)), height), Image.LANCZOS)
    return _emoji_cache[key]


def silhouette(im, color=(0, 0, 0)):
    s = Image.new('RGBA', im.size, color + (0,))
    s.putalpha(im.getchannel('A'))
    return s


def text_block(lines, font, stroke=7, line_h=None, shadow=True, pad=36, emoji_scale=1.12):
    """lines: lista de linhas; cada linha é lista de (tipo, valor, cor),
    tipo 't' = texto, 'e' = emoji. Retorna sprite RGBA recortado."""
    size = font.size
    line_h = line_h or int(size * 1.06)
    cap_h = -font.getbbox('H', anchor='ls')[1]
    top_room = int(size * 1.2)  # espaço para acentos (Í, É)
    gap = int(size * 0.2)

    def run_w(kind, val):
        if kind == 't':
            return font.getlength(val)
        return emoji(val, int(cap_h * emoji_scale)).width + gap

    widths = [sum(run_w(k, v) for k, v, _ in ln) for ln in lines]
    bw = int(max(widths) + 2 * pad + 2 * stroke)
    bh = int(top_room + line_h * (len(lines) - 1) + size * 0.25 + 2 * pad)
    main = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    dm = ImageDraw.Draw(main)
    for i, ln in enumerate(lines):
        x = (bw - widths[i]) / 2
        base = pad + top_room + i * line_h
        for kind, val, col in ln:
            if kind == 't':
                dm.text((x, base), val, font=font, fill=col, anchor='ls',
                        stroke_width=stroke, stroke_fill=BLACK)
                x += font.getlength(val)
            else:
                e = emoji(val, int(cap_h * emoji_scale))
                ey = int(base - cap_h - (e.height - cap_h) / 2)
                main.alpha_composite(e, (int(x + gap), ey))
                x += e.width + gap
    if shadow:
        sh = silhouette(main).filter(ImageFilter.GaussianBlur(9))
        a = np.asarray(sh.getchannel('A'), dtype=np.float32) * 0.85
        sh.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
        out = Image.new('RGBA', main.size, (0, 0, 0, 0))
        out.alpha_composite(sh, (0, 7))
        out.alpha_composite(main)
    else:
        out = main
    bb = out.getbbox()
    return out.crop((bb[0], 0, bb[2], out.height))


def rounded(size, radius, fill, border=None, bw=0, ss=4):
    """Retângulo arredondado com antialiasing (supersampling)."""
    w, h = size
    im = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if border:
        d.rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radius * ss, fill=border)
        d.rounded_rectangle((bw * ss, bw * ss, w * ss - 1 - bw * ss, h * ss - 1 - bw * ss),
                            (radius - bw) * ss, fill=fill)
    else:
        d.rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), radius * ss, fill=fill)
    return im.resize((w, h), Image.LANCZOS)


def tracked(draw, xy, text, font, fill, track):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill, anchor='ls')
        x += font.getlength(ch) + track
    return x


def tracked_w(text, font, track):
    return sum(font.getlength(c) + track for c in text) - track


def add_shadow(im, blur=10, dy=6, alpha=0.7, pad=24):
    out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    sh.alpha_composite(silhouette(im), (pad, pad + dy))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(sh.getchannel('A'), dtype=np.float32) * alpha
    sh.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
    out.alpha_composite(sh)
    out.alpha_composite(im, (pad, pad))
    return out


def pill_label(text, font, icon=None, h=56, padx=26, track=2.0, fg=WHITE,
               bg=(10, 10, 10, 210), border=YEL, bw=3):
    cap_h = -font.getbbox('H', anchor='ls')[1]
    ic = emoji(icon, int(cap_h * 1.75)) if icon else None
    tw = tracked_w(text, font, track)
    iw = (ic.width + 14) if ic else 0
    w = int(tw + iw + 2 * padx)
    im = rounded((w, h), h // 2, bg, border, bw)
    d = ImageDraw.Draw(im)
    x = padx
    base = h / 2 + cap_h / 2
    if ic:
        im.alpha_composite(ic, (int(x), int(h / 2 - ic.height / 2)))
        x += iw
    tracked(d, (x, base), text, font, fg, track)
    return add_shadow(im, blur=8, dy=5, alpha=0.6)


def sticker(text, font, icon=None, fg=BLACK, bg=YEL, h=96, padx=34, angle=-3.0,
            border=BLACK, bw=5):
    cap_h = -font.getbbox('H', anchor='ls')[1]
    ic = emoji(icon, int(cap_h * 1.25)) if icon else None
    tw = font.getlength(text)
    iw = (ic.width + 16) if ic else 0
    w = int(tw + iw + 2 * padx)
    im = rounded((w, h), 22, bg, border, bw)
    d = ImageDraw.Draw(im)
    base = h / 2 + cap_h / 2
    d.text((padx, base), text, font=font, fill=fg, anchor='ls')
    if ic:
        im.alpha_composite(ic, (int(padx + tw + 16), int(h / 2 - ic.height / 2)))
    im = add_shadow(im, blur=12, dy=8, alpha=0.75)
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    return im



# ------------------------------------------------------------------ sprites
SAFE_TOP, SAFE_BOT = 288, 1536
SP_RED = (214, 20, 32, 255)

TITLE_L1 = text_block([[("t", TITLE[0], WHITE)]], anton(50), stroke=6)
TITLE_L2 = text_block([[("t", TITLE[1], YEL)]], anton(78), stroke=7)
TITLE_L1_CY, TITLE_L2_CY = 325, 393

END_TOP = text_block([[('t', 'VÍDEO COMPLETO', WHITE)]], anton(112), stroke=8)
END_TITLE = text_block([
    [('t', END_TITLE_LINES[0], WHITE)],
    [('t', END_TITLE_LINES[1], WHITE)],
    [('t', END_TITLE_LINES[2], YEL)],
], anton(60), stroke=6)


def red_box(text, font, padx=34, h=104):
    cap_h = -font.getbbox('H', anchor='ls')[1]
    w = int(font.getlength(text) + 2 * padx)
    im = Image.new('RGBA', (w, h), SP_RED)
    ImageDraw.Draw(im).text((padx, h / 2 + cap_h / 2), text, font=font, fill=WHITE, anchor='ls')
    return add_shadow(im, blur=12, dy=8, alpha=0.7)


END_BOX = red_box('NO CANAL', anton(86))
SUB_BTN = sticker('INSCREVA-SE', anton(64), fg=WHITE, bg=RED, h=112, border=WHITE, bw=5, angle=0)
LINK = pill_label('TOQUE NO VÍDEO RELACIONADO', mont(32, 800), h=70)

# carimbo de data datilografado (canto de cima da imagem)
F_STAMP = mont(44, 800)
STAMP_TRACK = 6.0


def stamp_sprite(text):
    cap_h = -F_STAMP.getbbox('H', anchor='ls')[1]
    tw = tracked_w(text, F_STAMP, STAMP_TRACK)
    h, padx = 76, 24
    w = int(tw + 2 * padx + 30)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=(0, 0, 0, 150), outline=(255, 255, 255, 230), width=3)
    d.ellipse((padx - 4, h / 2 - 8, padx + 12, h / 2 + 8), fill=SP_RED)
    tracked(d, (padx + 30, h / 2 + cap_h / 2), text, F_STAMP, WHITE, STAMP_TRACK)
    return im


def stamp_partial(text, k):
    """Datilografado: uma letra a cada 2 quadros."""
    vis = min(len(text), k // 2 + 1)
    return stamp_sprite(text[:vis] + ' ' * (len(text) - vis))


STAMP_X, STAMP_CY = 40, BAND_Y + 64


# textos grandes (números e palavras de impacto), no meio da imagem
COLORS = {'yellow': YEL, 'white': WHITE, 'red': (235, 30, 35, 255)}
BIGS = []
for bt in BIG:
    f_ = anton(bt.get('size', 150))
    spr_ = text_block([[('t', ln, COLORS[bt['color']])] for ln in bt['text']], f_, stroke=9,
                      line_h=int(f_.size * 0.98))
    BIGS.append((spr_, bt['a'], bt['b'], BAND_Y + int(BAND_H * bt.get('y', 0.5))))


# placa branca com barra vermelha
def plate(text):
    f = mont(40, 800)
    track = 2.5
    cap_h = -f.getbbox('H', anchor='ls')[1]
    tw = tracked_w(text, f, track)
    h, bar, padx = 74, 16, 24
    w = int(bar + padx * 2 + tw)
    im = Image.new('RGBA', (w, h), (255, 255, 255, 240))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, bar - 1, h - 1), fill=SP_RED)
    tracked(d, (bar + padx, h / 2 + cap_h / 2), text, f, (12, 12, 12, 255), track)
    return add_shadow(im, blur=10, dy=6, alpha=0.6)


PLATES = [(plate(l['text']), l['a'], l['b']) for l in LOWER]
PLATE_X, PLATE_CY = 40, BAND_Y + BAND_H - 238

# legenda da narração por cima da imagem, no terço de baixo
F_CAP = mont(68, 800)
HL = set(EDL['highlight'])
CAP_MAX_W = 960


def cap_sprite(txt):
    words = txt.split()

    def w_of(ws):
        return F_CAP.getlength(' '.join(ws))

    lines = [words]
    if w_of(words) > CAP_MAX_W:
        k = min(range(1, len(words)), key=lambda k: max(w_of(words[:k]), w_of(words[k:])))
        lines = [words[:k], words[k:]]
    out = []
    for ln in lines:
        runs = []
        for i, wd in enumerate(ln):
            col = YEL if wd.strip(',.!?"…').upper() in HL else WHITE
            runs.append(('t', wd + (' ' if i < len(ln) - 1 else ''), col))
        out.append(runs)
    return text_block(out, F_CAP, stroke=7, line_h=int(F_CAP.size * 1.18), pad=26)


CAPS = [(a, b, cap_sprite(t)) for a, b, t in CAPTIONS]
CAP_CY = 1392


# ------------------------------------------------------------------ animação


def ease_out_back(x):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


IN_F = round(0.30 * FPS)
OUT_F = round(0.17 * FPS)


def anim_state(n, a, b):
    """Escala/alpha de um elemento visível em [a, b) com pop-in e saída."""
    if n < a or n >= b:
        return None
    k = n - a
    if k < IN_F:
        x = k / IN_F
        return 0.55 + 0.45 * ease_out_back(x), min(1.0, k / (IN_F * 0.45))
    r = b - n
    if r <= OUT_F:
        x = 1 - r / OUT_F
        return 1 - 0.18 * ease_out_cubic(x), 1 - x
    return 1.0, 1.0


def place(canvas, sprite, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    sp = sprite
    if abs(scale - 1) > 0.004:
        sp = sprite.resize((max(1, round(sprite.width * scale)),
                            max(1, round(sprite.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        a = np.asarray(sp.getchannel('A'), dtype=np.float32) * alpha
        sp = sp.copy()
        sp.putalpha(Image.fromarray(a.astype(np.uint8)))
    x = int(round(cx - sp.width / 2))
    y = int(round(cy - sp.height / 2))
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(sp.width, W - x), min(sp.height, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    canvas.alpha_composite(sp, (x + sx0, y + sy0), (sx0, sy0, sx1, sy1))


def show(canvas, sprite, n, a, b, cx, cy, pulse=0.0, hz=1.6):
    st = anim_state(n, a, b)
    if not st:
        return
    sc, al = st
    if st == (1.0, 1.0) and pulse:
        sc = 1 + pulse * math.sin(2 * math.pi * hz * (n - a) / FPS)
    place(canvas, sprite, cx, cy, sc, al)



# ------------------------------------------------------------------ base fixa
MARKS = [c / N * W for c in CHAPTERS[1:]]


def build_base():
    ys = np.arange(H, dtype=np.float32)
    a = np.zeros(H, dtype=np.float32)
    # escurece atrás do título e embaixo da faixa
    t = np.clip(ys / BAND_Y, 0, 1)
    a = np.where(ys < BAND_Y, 130 - 40 * t, a)
    b0 = BAND_BOT + BAR_H
    t2 = np.clip((ys - b0) / (H - b0), 0, 1)
    a = np.where(ys >= b0, 110 + 100 * t2, a)
    sh = 40
    up = np.clip(1 - (BAND_Y - ys) / sh, 0, 1) ** 2
    a = np.where((ys < BAND_Y) & (ys >= BAND_Y - sh), np.maximum(a, 60 + 120 * up), a)
    # dentro da faixa: degradê escuro embaixo, para a legenda ler bem por cima da imagem
    g0 = BAND_BOT - 300
    t3 = np.clip((ys - g0) / (BAND_BOT - g0), 0, 1)
    a = np.where((ys >= g0) & (ys < BAND_BOT), 170 * t3 ** 1.3, a)
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 3] = np.repeat(a[:, None], W, axis=1).clip(0, 255).astype(np.uint8)
    base = Image.fromarray(arr, 'RGBA')
    d = ImageDraw.Draw(base)
    d.rectangle((0, BAND_BOT, W - 1, BAND_BOT + BAR_H - 1), fill=(255, 255, 255, 70))
    for x in MARKS:
        d.rectangle((int(x) - 2, BAND_BOT, int(x) + 1, BAND_BOT + BAR_H - 1), fill=(0, 0, 0, 200))
    return base


BASE = build_base()
BASE_T = BASE.copy()
place(BASE_T, TITLE_L1, W / 2, TITLE_L1_CY)
place(BASE_T, TITLE_L2, W / 2, TITLE_L2_CY)


def title_state(n):
    if n < IN_F:  # abertura: "punch" de 1.12 -> 1.0, já visível no quadro 0
        return 1.12 - 0.12 * ease_out_cubic(n / IN_F), 1.0
    if END_A - OUT_F <= n < END_A:
        x = 1 - (END_A - n) / OUT_F
        return 1 - 0.18 * ease_out_cubic(x), 1 - x
    if n >= END_A:
        return None
    return 1.0, 1.0


def show_left(canvas, sprite, n, a, b, x0, cy):
    """Entra deslizando da esquerda e sai com fade."""
    if n < a or n >= b:
        return
    k, r = n - a, b - n
    x, al = x0, 1.0
    if k < 8:
        e = ease_out_cubic(k / 8)
        x = x0 - (1 - e) * (sprite.width * 0.6)
        al = e
    elif r <= OUT_F:
        al = r / OUT_F
    place(canvas, sprite, x + sprite.width / 2, cy, 1.0, al)


def render(n):
    ts = title_state(n)
    static = ts == (1.0, 1.0)
    im = (BASE_T if static else BASE).copy()
    if ts and not static:
        place(im, TITLE_L1, W / 2, TITLE_L1_CY, *ts)
        place(im, TITLE_L2, W / 2, TITLE_L2_CY, *ts)
    # carimbos de data (datilografados) e placas
    for s in STAMPS:
        if s['a'] <= n < s['b']:
            r = s['b'] - n
            spr_ = stamp_partial(s['text'], n - s['a'])
            place(im, spr_, STAMP_X + spr_.width / 2, STAMP_CY, 1.0, min(1.0, r / OUT_F))
    for spr_, a, b in PLATES:
        show_left(im, spr_, n, a, b, PLATE_X, PLATE_CY)
    for spr_, a, b, cy in BIGS:
        show(im, spr_, n, a, b, W / 2, cy)
    # encerramento
    show(im, END_TOP, n, END_A, N + 10, W / 2, BAND_Y + 150)
    show(im, END_BOX, n, END_A + 4, N + 10, W / 2, BAND_Y + 285)
    show(im, END_TITLE, n, END_A + 8, N + 10, W / 2, BAND_Y + 500)
    show(im, SUB_BTN, n, END_A + 12, N + 10, W / 2, BAND_Y + 710, pulse=0.035)
    show(im, LINK, n, END_A + 18, N + 10, W / 2, BAND_Y + 860)
    # legenda da narração (entra com um "pop" curto)
    for a, b, spr_ in CAPS:
        if a <= n < b:
            k = n - a
            if a == 0:                                 # gancho: já inteira no primeiro quadro
                place(im, spr_, W / 2, CAP_CY)
            else:
                place(im, spr_, W / 2, CAP_CY, 0.86 + 0.14 * ease_out_back(min(1.0, k / 4)), min(1.0, (k + 1) / 3))
    # barra de progresso
    d = ImageDraw.Draw(im)
    xf = (n + 1) / N * W
    d.rectangle((0, BAND_BOT, int(xf), BAND_BOT + BAR_H - 1), fill=YEL)
    for x in MARKS:
        if x < xf:
            d.rectangle((int(x) - 2, BAND_BOT, int(x) + 1, BAND_BOT + BAR_H - 1), fill=(0, 0, 0, 200))
    return im


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        for f in sys.argv[2:]:
            render(int(f)).save(os.path.join(HERE, 'frames', f'ov_{int(f):05d}.png'))
