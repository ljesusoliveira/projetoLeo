"""Camada gráfica (RGBA 1080x1920) do Short-gancho: selo do canal, título,
gancho, legendas dos lances, rebobinada, suspense, encerramento e barra de
progresso. Mesmo visual do Short "Momentos Bizarros".
  python3 overlay.py preview <quadro> [...]  -> frames/ov_<quadro>.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from timeline import BYID, FPS, GROUPS, N

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'fonts')
EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

W, H = 1080, 1920
BAND_Y, BAND_H = 500, 860          # faixa do vídeo
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
F_TITLE = anton(84)
TITLE = text_block([
    [('t', 'AS MAIORES PINTURAS', WHITE)],
    [('t', 'DO FUTEBOL BRASILEIRO', YEL), ('e', '🎨', None)],
], F_TITLE)

CTA_FINAL = text_block([
    [('t', 'O FINAL VOCÊ VÊ', WHITE)],
    [('t', 'NO VÍDEO COMPLETO', YEL), ('e', '👇', None)],
], F_TITLE)

END_TOP = text_block([
    [('t', 'VÍDEO COMPLETO', WHITE)],
    [('t', 'LÁ NO CANAL', YEL), ('e', '🔥', None)],
], anton(92))

END_TITLE = text_block([
    [('t', '"AS MAIORES PINTURAS DO', WHITE)],
    [('t', 'FUTEBOL BRASILEIRO:', WHITE)],
    [('t', 'GOLS DE DIFERENTES GERAÇÕES"', YEL)],
], anton(60), stroke=6)

BRAND = pill_label('BASTIDORES DO FUTEBOL', mont(29, 800), icon='⚽', h=60)
HOOK = sticker('QUAL É O MAIS BONITO?', anton(58), icon='🤔', h=100)
SUSP = sticker('SERÁ QUE ENTROU?', anton(74), icon='👀', h=124, angle=-2.5)
REWIND = text_block([[('e', '⏪', None), ('t', ' VOLTANDO NO TEMPO...', WHITE)]], anton(76))
SUB_BTN = sticker('INSCREVA-SE', anton(58), icon='🔔', fg=WHITE, bg=RED, h=104,
                  border=WHITE, bw=5, angle=0)
LINK = pill_label('TOQUE NO VÍDEO RELACIONADO', mont(30, 800), icon='👇', h=66)

NAMES = {g['id']: pill_label(g['name'], mont(31, 800), icon='⚽', h=62)
         for g in GROUPS if g.get('name')}
TAGS = {g['id']: sticker(g['tag'][0], anton(60), icon=g['tag'][1], h=100, angle=-3.0)
        for g in GROUPS if g.get('tag')}

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
MARKS = [g['start'] / N * W for g in GROUPS[1:]]


def build_base():
    ys = np.arange(H, dtype=np.float32)
    a = np.zeros(H, dtype=np.float32)
    # escurece atrás do título e embaixo; sombra colada na faixa do vídeo
    t = np.clip(ys / BAND_Y, 0, 1)
    a = np.where(ys < BAND_Y, 150 - 80 * t, a)
    b0 = BAND_BOT + BAR_H
    t2 = np.clip((ys - b0) / (H - b0), 0, 1)
    a = np.where(ys >= b0, 70 + 110 * t2, a)
    sh = 46
    up = np.clip(1 - (BAND_Y - ys) / sh, 0, 1) ** 2
    a = np.where((ys < BAND_Y) & (ys >= BAND_Y - sh), np.maximum(a, 60 + 120 * up), a)
    dn = np.clip(1 - (ys - b0) / sh, 0, 1) ** 2
    a = np.where((ys >= b0) & (ys < b0 + sh), np.maximum(a, 60 + 120 * dn), a)
    a[BAND_Y:BAND_BOT] = 0
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 3] = np.repeat(a[:, None], W, axis=1).clip(0, 255).astype(np.uint8)
    base = Image.fromarray(arr, 'RGBA')
    d = ImageDraw.Draw(base)
    d.rectangle((0, BAND_BOT, W - 1, BAND_BOT + BAR_H - 1), fill=(255, 255, 255, 70))
    for x in MARKS:
        d.rectangle((int(x) - 2, BAND_BOT, int(x) + 1, BAND_BOT + BAR_H - 1), fill=(0, 0, 0, 200))
    place(base, BRAND, W / 2, BRAND_CY)
    return base


BASE = build_base()
BASE_T = BASE.copy()
place(BASE_T, TITLE, W / 2, TITLE_CY)

P = BYID
SUSP_A = P['suspense']['start']
CTA_A = SUSP_A + round(0.5 * FPS)
END_A = P['final']['start']


def title_state(n):
    if n < IN_F:  # abertura: "punch" de 1.12 -> 1.0, já visível no quadro 0
        return 1.12 - 0.12 * ease_out_cubic(n / IN_F), 1.0
    if CTA_A - OUT_F <= n < CTA_A:
        x = 1 - (CTA_A - n) / OUT_F
        return 1 - 0.18 * ease_out_cubic(x), 1 - x
    if n >= CTA_A:
        return None
    return 1.0, 1.0


def render(n):
    ts = title_state(n)
    static = ts == (1.0, 1.0)
    im = (BASE_T if static else BASE).copy()
    if ts and not static:
        place(im, TITLE, W / 2, TITLE_CY, *ts)
    # chamada do suspense no lugar do título, depois a do encerramento
    show(im, CTA_FINAL, n, CTA_A, END_A, W / 2, TITLE_CY, pulse=0.03, hz=1.5)
    show(im, END_TOP, n, END_A, N + 10, W / 2, TITLE_CY, pulse=0.03, hz=1.5)
    # gancho
    g0 = GROUPS[0]
    show(im, HOOK, n, g0['start'] + 2, g0['end'] - 2, W / 2, BAND_BOT - 120, pulse=0.025, hz=1.8)
    # legendas dos lances (etiqueta + nome), no terço de baixo da faixa
    for g in GROUPS:
        e = min(g['end'], SUSP_A)  # no suspense a tela fica só com a pergunta
        if g['id'] in TAGS:
            show(im, TAGS[g['id']], n, g['start'] + 4, e - 4, W / 2, BAND_BOT - 205)
        if g['id'] in NAMES:
            show(im, NAMES[g['id']], n, g['start'] + 9, e - 4, W / 2, BAND_BOT - 95)
    # rebobinada
    rw = P['rebobina']
    st = anim_state(n, rw['start'], rw['end'] + 4)
    if st:
        jx = 6 * math.sin(n * 2.7)
        place(im, REWIND, W / 2 + jx, BAND_Y + BAND_H / 2, *st)
    # suspense
    show(im, SUSP, n, SUSP_A + 2, END_A, W / 2, BAND_Y + BAND_H / 2 + 40, pulse=0.04, hz=2.2)
    # encerramento
    show(im, END_TITLE, n, END_A + 3, N + 10, W / 2, BAND_Y + 250)
    show(im, SUB_BTN, n, END_A + 10, N + 10, W / 2, BAND_Y + 520, pulse=0.045)
    show(im, LINK, n, END_A + 16, N + 10, W / 2, BAND_Y + 700, pulse=0.02)
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
