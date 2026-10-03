"""Gera a camada gráfica (RGBA) do Short: título, selo do canal, chamadas,
sombras/gradientes e barra de progresso. Uso:
  python3 overlay.py preview <frame> [<frame> ...]   -> ov_<frame>.png
  python3 overlay.py stream                          -> RGBA cru no stdout
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'fonts')
EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

W, H = 1080, 1920
D = json.load(open(os.path.join(HERE, 'segments.json')))
FPS = D['fps']
N = D['nframes']
SEGS = D['segs']

YEL = (255, 214, 10, 255)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
RED = (229, 9, 20, 255)

BAR_H = 10  # barra de progresso colada embaixo do vídeo


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
    cap = font.getbbox('H', anchor='ls')
    cap_h = -cap[1]
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
        sh = silhouette(main)
        sh = sh.filter(ImageFilter.GaussianBlur(9))
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


def pill_label(text, font, icon=None, h=56, padx=26, track=2.0, fg=WHITE,
               bg=(10, 10, 10, 200), border=YEL, bw=3):
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
F_TITLE = anton(88)
TITLE = text_block([
    [('t', 'MOMENTOS MAIS BIZARROS', WHITE)],
    [('t', 'DO FUTEBOL BRASILEIRO', YEL), ('e', '🇧🇷', None)],
], F_TITLE)

CTA_FULL = text_block([
    [('t', 'VÍDEO COMPLETO DE 11 MIN', WHITE)],
    [('t', 'LÁ NO CANAL', YEL), ('e', '🔥', None)],
], F_TITLE)

CTA_SUB = text_block([
    [('t', 'SE INSCREVE NO CANAL', WHITE)],
    [('t', 'PRA NÃO PERDER NADA', YEL), ('e', '🔔', None)],
], F_TITLE)

CTA_END = text_block([
    [('t', 'QUER VER MAIS LOUCURA?', WHITE)],
    [('t', 'VÍDEO COMPLETO NO CANAL', YEL), ('e', '👇', None)],
], anton(84))

BRAND = pill_label('BASTIDORES DO FUTEBOL', mont(29, 800), icon='⚽', h=60)

HOOK = sticker('ASSISTA ATÉ O FINAL', anton(54), icon='👀')

SUB_BTN = sticker('INSCREVA-SE', anton(58), icon='🔔', fg=WHITE, bg=RED, h=104,
                  border=WHITE, bw=5, angle=0)

# ------------------------------------------------------------------ layout
TITLE_CY = 316       # centro vertical do bloco de título/CTA
BRAND_CY = 176       # centro vertical do selo do canal


def sec(s):
    return int(round(s * FPS))


# janelas em que o título dá lugar a uma chamada (CTA)
CTA_WINDOWS = [
    (sec(53.4), sec(57.6), CTA_FULL),
    (sec(108.5), sec(112.7), CTA_SUB),
    (sec(163.6), N + 10, CTA_END),
]
HOOK_WIN = (sec(0.15), sec(3.6))
SUB_WIN = (sec(164.2), N + 10)


def seg_of(n):
    for i, s in enumerate(SEGS):
        if s['start'] <= n <= s['end']:
            return i
    return len(SEGS) - 1


def ease_out_back(x):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


IN_F = sec(0.30)
OUT_F = sec(0.17)


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
    # recorta o que sair da tela
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(sp.width, W - x), min(sp.height, H - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    canvas.alpha_composite(sp, (x + sx0, y + sy0), (sx0, sy0, sx1, sy1))


# ------------------------------------------------------------------ base por segmento
CUTS_X = [s['start'] / N * W for s in SEGS[1:]]


def build_base(i):
    s = SEGS[i]
    top, bot = s['py'], s['py'] + s['ch']
    a = np.zeros(H, dtype=np.float32)  # alpha por linha
    ys = np.arange(H, dtype=np.float32)
    # gradiente escuro em cima (atrás do título) e embaixo
    t = np.clip(ys / max(1, top), 0, 1)
    a = np.where(ys < top, 150 - 85 * t, a)
    b0 = bot + BAR_H
    t2 = np.clip((ys - b0) / max(1, H - b0), 0, 1)
    a = np.where(ys >= b0, 65 + 110 * t2, a)
    # sombra suave colada nas bordas do vídeo (efeito "card")
    sh = 46
    up = np.clip(1 - (top - ys) / sh, 0, 1) ** 2
    a = np.where((ys < top) & (ys >= top - sh), np.maximum(a, 60 + 120 * up), a)
    dn = np.clip(1 - (ys - b0) / sh, 0, 1) ** 2
    a = np.where((ys >= b0) & (ys < b0 + sh), np.maximum(a, 60 + 120 * dn), a)
    a[top:bot] = 0
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 3] = np.repeat(a[:, None], W, axis=1).clip(0, 255).astype(np.uint8)
    base = Image.fromarray(arr, 'RGBA')
    # trilho da barra de progresso com divisões por lance
    d = ImageDraw.Draw(base)
    d.rectangle((0, bot, W - 1, bot + BAR_H - 1), fill=(255, 255, 255, 70))
    for x in CUTS_X:
        d.rectangle((int(x) - 2, bot, int(x) + 1, bot + BAR_H - 1), fill=(0, 0, 0, 200))
    place(base, BRAND, W / 2, BRAND_CY)
    return base


_bases = {}


def base_for(i, with_title):
    key = (i, with_title)
    if key not in _bases:
        b = build_base(i).copy()
        if with_title:
            place(b, TITLE, W / 2, TITLE_CY)
        _bases[key] = b
    return _bases[key]


def title_state(n):
    """Título some (sai) antes de cada CTA e volta (pop) depois."""
    if n < IN_F:  # abertura: "punch" de 1.12 -> 1.0, já visível no frame 0
        x = n / IN_F
        return 1.12 - 0.12 * ease_out_cubic(x), 1.0
    for a, b, _ in CTA_WINDOWS:
        if a - OUT_F <= n < a:
            x = 1 - (a - n) / OUT_F
            return 1 - 0.18 * ease_out_cubic(x), 1 - x
        if a <= n < b:
            return None
        if b <= n < b + IN_F:
            st = anim_state(n, b, b + 10 ** 6)
            return st
    return 1.0, 1.0


def render(n):
    i = seg_of(n)
    s = SEGS[i]
    bot = s['py'] + s['ch']
    ts = title_state(n)
    static_title = ts == (1.0, 1.0)
    im = base_for(i, static_title).copy()
    if ts and not static_title:
        place(im, TITLE, W / 2, TITLE_CY, *ts)
    for a, b, spr in CTA_WINDOWS:
        st = anim_state(n, a, b)
        if st:
            sc, al = st
            if st == (1.0, 1.0):
                sc = 1 + 0.03 * math.sin(2 * math.pi * 1.5 * (n - a) / FPS)
            place(im, spr, W / 2, TITLE_CY, sc, al)
    # barra de progresso (preenchimento)
    d = ImageDraw.Draw(im)
    xf = (n + 1) / N * W
    d.rectangle((0, bot, int(xf), bot + BAR_H - 1), fill=YEL)
    for x in CUTS_X:
        if x < xf:
            d.rectangle((int(x) - 2, bot, int(x) + 1, bot + BAR_H - 1), fill=(0, 0, 0, 200))
    # gancho inicial
    st = anim_state(n, *HOOK_WIN)
    if st:
        sc, al = st
        if st == (1.0, 1.0):
            sc = 1 + 0.025 * math.sin(2 * math.pi * 1.8 * (n - HOOK_WIN[0]) / FPS)
        place(im, HOOK, W / 2, bot - 6, sc, al)
    # botão de inscrição no final
    st = anim_state(n, *SUB_WIN)
    if st:
        sc, al = st
        if st == (1.0, 1.0):
            sc = 1 + 0.045 * math.sin(2 * math.pi * 1.6 * (n - SUB_WIN[0]) / FPS)
        place(im, SUB_BTN, W / 2, bot - 70, sc, al)
    return im


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'preview':
        for f in sys.argv[2:]:
            render(int(f)).save(os.path.join(HERE, f'ov_{int(f):05d}.png'))
    elif mode == 'stream':
        out = sys.stdout.buffer
        for n in range(N):
            out.write(render(n).tobytes())
            if n % 300 == 0:
                print(f'frame {n}/{N}', file=sys.stderr, flush=True)
