"""Camada gráfica (RGBA 1080x1920) do Short do Top 10 centroavantes: pergunta
do gancho, legenda da narração de abertura, cabeçalho "TOP 10", escada de
posições (10 ao 2 e um "?" no lugar do nº1), tela de posição de cada jogador
(número dourado #F2C230, nome em branco e faixa vermelha, como no vídeo longo,
só que do tamanho do vertical), "TOP 3" e o suspense final.
Áreas seguras: nada acima de y=288 nem abaixo de y=1536.
  python3 overlay.py preview <quadro> [...]  -> frames/ov_<quadro>.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from timeline import (BEAT_F, CAPTIONS, EDL, END_TITLE_LINES, FIM_A, FPS, HOOK_END, N, PIECES, PLAYERS,
                      TOP3_A, piece_at, pos_start)

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', 'fonts')

W, H = 1080, 1920
BAND_Y, BAND_H = 512, 760              # faixa do vídeo
BAND_BOT = BAND_Y + BAND_H

GOLD = (242, 194, 48, 255)             # #F2C230
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
RED = (214, 24, 44, 255)


def bebas(size):
    return ImageFont.truetype(os.path.join(FONTS, 'BebasNeue-Regular.ttf'), size, layout_engine=ImageFont.Layout.RAQM)


def mont(size, wght=800):
    f = ImageFont.truetype(os.path.join(FONTS, 'Montserrat.ttf'), size, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_axes([wght])
    return f


def silhouette(im, color=(0, 0, 0)):
    s = Image.new('RGBA', im.size, color + (0,))
    s.putalpha(im.getchannel('A'))
    return s


def add_shadow(im, blur=10, dy=6, alpha=0.7, pad=24, color=(0, 0, 0)):
    out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    sh.alpha_composite(silhouette(im, color), (pad, pad + dy))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(sh.getchannel('A'), dtype=np.float32) * alpha
    sh.putalpha(Image.fromarray(a.clip(0, 255).astype(np.uint8)))
    out.alpha_composite(sh)
    out.alpha_composite(im, (pad, pad))
    return out


def text_block(lines, font, stroke=7, line_h=None, pad=30, shadow=True):
    """lines: lista de linhas; cada linha é lista de (texto, cor). Sprite RGBA centralizado."""
    size = font.size
    line_h = line_h or int(size * 1.0)
    widths = [sum(font.getlength(t) for t, _ in ln) for ln in lines]
    top_room = int(size * 1.05)
    bw = int(max(widths) + 2 * pad + 2 * stroke)
    bh = int(top_room + line_h * (len(lines) - 1) + size * 0.2 + 2 * pad)
    im = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        x = (bw - widths[i]) / 2
        base = pad + top_room + i * line_h
        for t, col in ln:
            d.text((x, base), t, font=font, fill=col, anchor='ls', stroke_width=stroke, stroke_fill=BLACK)
            x += font.getlength(t)
    if shadow:
        im = add_shadow(im, blur=9, dy=7, alpha=0.8, pad=0)
    bb = im.getbbox()
    return im.crop((bb[0], bb[1], bb[2], bb[3]))


def fit(text, maker, size, max_w, min_size):
    while size > min_size and maker(size).getlength(text) > max_w:
        size -= 2
    return maker(size)


def place(canvas, sprite, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    sp = sprite
    if abs(scale - 1) > 0.004:
        sp = sprite.resize((max(1, round(sprite.width * scale)), max(1, round(sprite.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        a = np.asarray(sp.getchannel('A'), dtype=np.float32) * alpha
        sp = sp.copy()
        sp.putalpha(Image.fromarray(a.astype(np.uint8)))
    x, y = int(round(cx - sp.width / 2)), int(round(cy - sp.height / 2))
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(sp.width, W - x), min(sp.height, H - y)
    if sx1 > sx0 and sy1 > sy0:
        canvas.alpha_composite(sp, (x + sx0, y + sy0), (sx0, sy0, sx1, sy1))


def ease_out_back(x):
    c1 = 1.70158
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def pop(k, dur=6, start=1.6):
    """Escala de um elemento que "bate" na tela: start -> 1 em dur quadros."""
    if k >= dur:
        return 1.0
    return start + (1 - start) * ease_out_cubic(k / dur)


# ------------------------------------------------------------------ peças fixas
HEADER_TOP = text_block([[('TOP 10', GOLD)]], bebas(100), stroke=7)
HEADER_SUB = text_block([[('MAIORES CENTROAVANTES DO BRASIL', WHITE)]], bebas(58), stroke=5)
HEADER_TOP_CY, HEADER_SUB_CY = 340, 422

F_Q = bebas(150)
QUESTION = text_block([
    [('QUEM É O MAIOR', WHITE)],
    [('CENTROAVANTE', GOLD)],
    [('DO BRASIL', WHITE), ('?', GOLD)],
], F_Q, stroke=9, line_h=int(F_Q.size * 0.92))
QUESTION_CY = 520

F_CAP = mont(62, 800)
HL = set(EDL['highlight'])


def cap_sprite(txt):
    words = txt.split()
    runs = [(w + (' ' if i < len(words) - 1 else ''), GOLD if w in HL else WHITE) for i, w in enumerate(words)]
    return text_block([runs], F_CAP, stroke=7, pad=24)


CAPS = [(a, b, cap_sprite(t)) for a, b, t in CAPTIONS]
CAP_CY = 1420

# escada de posições
LADDER = [str(p) for p in range(10, 1, -1)] + ['?']
LAD_W, LAD_H, LAD_GAP = 92, 48, 8
LAD_X0 = (W - (len(LADDER) * LAD_W + (len(LADDER) - 1) * LAD_GAP)) // 2
LAD_CY = 484
F_LAD = bebas(40)


def ladder_box(label, state):
    im = Image.new('RGBA', (LAD_W, LAD_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if label == '?':
        fill, txt = RED, WHITE
    elif state == 'now':
        fill, txt = GOLD, BLACK
    elif state == 'done':
        fill, txt = (30, 30, 32, 225), (242, 194, 48, 200)
    else:
        fill, txt = (0, 0, 0, 150), (255, 255, 255, 150)
    d.rounded_rectangle((0, 0, LAD_W - 1, LAD_H - 1), 8, fill=fill,
                        outline=(255, 255, 255, 70) if state == 'next' and label != '?' else None, width=2)
    d.text((LAD_W / 2, LAD_H / 2 + 1), label, font=F_LAD, fill=txt, anchor='mm')
    return im


LAD_SPR = {(lab, st): ladder_box(lab, st) for lab in LADDER for st in ('done', 'now', 'next')}


# tela de posição: número dourado, barra dourada, nome em branco e faixa vermelha
CARD_X = 52
NUM_BASE = 1512
F_HASH = bebas(96)


def card_sprites(pos):
    name, sub = PLAYERS[pos]
    f_num = bebas(270)
    num = Image.new('RGBA', (int(f_num.getlength(str(pos)) + F_HASH.getlength('#') + 60), 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(num)
    d.text((10, 105), '#', font=F_HASH, fill=WHITE, anchor='ls', stroke_width=4, stroke_fill=BLACK)
    d.text((10 + F_HASH.getlength('#') + 4, 280), str(pos), font=f_num, fill=GOLD, anchor='ls',
           stroke_width=8, stroke_fill=BLACK)
    num = add_shadow(num.crop(num.getbbox()), blur=10, dy=8, alpha=0.8, pad=20)
    x_name = CARD_X + num.width - 10
    avail = W - x_name - 40
    f_name = fit(name, bebas, 118, avail - 16, 70)
    nm = Image.new('RGBA', (int(f_name.getlength(name) + 40), int(f_name.size * 1.1)), (0, 0, 0, 0))
    ImageDraw.Draw(nm).text((14, int(f_name.size * 0.95)), name, font=f_name, fill=WHITE, anchor='ls',
                            stroke_width=6, stroke_fill=BLACK)
    nm = add_shadow(nm.crop(nm.getbbox()), blur=8, dy=6, alpha=0.8, pad=16)
    f_sub = fit(sub, bebas, 46, avail - 40, 30)
    sw = int(f_sub.getlength(sub) + 36)
    band = Image.new('RGBA', (sw, 64), RED)
    ImageDraw.Draw(band).text((18, 50), sub, font=f_sub, fill=WHITE, anchor='ls')
    band = add_shadow(band, blur=8, dy=5, alpha=0.6, pad=12)
    return dict(num=num, name=nm, band=band, x_name=x_name)


CARDS = {p: card_sprites(p) for p in PLAYERS}
GLOW = {}


def num_glow(pos):
    if pos not in GLOW:
        s = CARDS[pos]['num']
        g = Image.new('RGBA', (s.width + 160, s.height + 160), (0, 0, 0, 0))   # folga: o brilho não é cortado
        g.alpha_composite(silhouette(s, (242, 194, 48)), (80, 80))
        g = g.filter(ImageFilter.GaussianBlur(22))
        GLOW[pos] = g
    return GLOW[pos]


def draw_card(im, pos, k):
    """k = quadros desde que a posição entrou."""
    c = CARDS[pos]
    num, nm, band = c['num'], c['name'], c['band']
    ncx = CARD_X + num.width / 2
    ncy = NUM_BASE - num.height / 2 + 20
    if pos <= 3:                                        # top 3: brilho dourado pulsando atrás do número
        a = 0.55 + 0.25 * math.sin(2 * math.pi * k / BEAT_F)
        place(im, num_glow(pos), ncx, ncy, 1.0, a * min(1.0, k / 6))
    sc = pop(k, 6, 1.7)                                 # "bate" crescendo para cima: a base fica parada
    place(im, num, ncx, ncy - (sc - 1) * num.height / 2, sc, min(1.0, (k + 1) / 3))
    # barra dourada vertical entre número e nome
    if k >= 3:
        hbar = int(200 * ease_out_cubic(min(1.0, (k - 3) / 6)))
        d = ImageDraw.Draw(im)
        xb = c['x_name'] - 6
        d.rectangle((xb, 1512 - hbar, xb + 9, 1512), fill=GOLD)
    if k >= 4:
        e = ease_out_cubic(min(1.0, (k - 4) / 7))
        place(im, nm, c['x_name'] + nm.width / 2 + 120 * (1 - e), 1338, 1.0, e)
    if k >= 8:                                          # faixa vermelha entra da esquerda
        e = ease_out_cubic(min(1.0, (k - 8) / 8))
        wv = max(1, int(band.width * e))
        b = band.crop((0, 0, wv, band.height))
        im.alpha_composite(b, (int(c['x_name']), int(1452 - band.height / 2)))


# TOP 3 e suspense
TOP3 = text_block([[('TOP 3', GOLD)]], bebas(330), stroke=10)
TOP3_SUB = text_block([[('OS 3 MAIORES', WHITE)]], bebas(90), stroke=6)
Q_BIG = text_block([[('?', GOLD)]], bebas(620), stroke=12)
Q_GLOW = Image.new('RGBA', (Q_BIG.width + 300, Q_BIG.height + 300), (0, 0, 0, 0))
Q_GLOW.alpha_composite(silhouette(Q_BIG, (242, 194, 48)), (150, 150))
Q_GLOW = Q_GLOW.filter(ImageFilter.GaussianBlur(40))
E_N1 = text_block([[('E O Nº1…', WHITE)]], bebas(140), stroke=8)
VOCE = text_block([[('VOCÊ JÁ SABE', WHITE)], [('QUEM É', GOLD), ('?', GOLD)]], bebas(116), stroke=8,
                  line_h=110)
END_TOP = text_block([[('VÍDEO COMPLETO', WHITE)]], bebas(150), stroke=8)


def red_box(text, font, padx=36, h=110):
    w = int(font.getlength(text) + 2 * padx)
    im = Image.new('RGBA', (w, h), RED)
    ImageDraw.Draw(im).text((w / 2, h / 2 + 4), text, font=font, fill=WHITE, anchor='mm')
    return add_shadow(im, blur=12, dy=8, alpha=0.7)


END_BOX = red_box('NO CANAL', bebas(100))
END_TITLE = text_block([[(END_TITLE_LINES[0], WHITE)], [(END_TITLE_LINES[1], GOLD)]], bebas(80), stroke=6,
                       line_h=78)


def pill(text, font, h=78, padx=34):
    tri = 26                                            # setinha para baixo, desenhada (a fonte não tem o símbolo)
    w = int(font.getlength(text) + 2 * padx + tri + 16)
    im = Image.new('RGBA', (w * 4, h * 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * 4 - 1, h * 4 - 1), h * 2, fill=(10, 10, 10, 220),
                                         outline=GOLD, width=12)
    im = im.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.text((padx, h / 2 + 2), text, font=font, fill=WHITE, anchor='lm')
    x = padx + font.getlength(text) + 16
    d.polygon([(x, h / 2 - 9), (x + tri, h / 2 - 9), (x + tri / 2, h / 2 + 11)], fill=GOLD)
    return add_shadow(im, blur=8, dy=5, alpha=0.6)


SUB_BTN = red_box('INSCREVA-SE', bebas(80), h=104)
LINK = pill('TOQUE NO VÍDEO RELACIONADO', bebas(46))


# ------------------------------------------------------------------ base fixa
def build_base():
    ys = np.arange(H, dtype=np.float32)
    a = np.zeros(H, dtype=np.float32)
    t = np.clip(ys / BAND_Y, 0, 1)
    a = np.where(ys < BAND_Y, 140 - 50 * t, a)
    b0 = BAND_BOT
    t2 = np.clip((ys - b0) / (H - b0), 0, 1)
    a = np.where(ys >= b0, 120 + 90 * t2, a)
    sh = 40
    up = np.clip(1 - (BAND_Y - ys) / sh, 0, 1) ** 2
    a = np.where((ys < BAND_Y) & (ys >= BAND_Y - sh), np.maximum(a, 60 + 120 * up), a)
    dn = np.clip(1 - (ys - b0) / sh, 0, 1) ** 2
    a = np.where((ys >= b0) & (ys < b0 + sh), np.maximum(a, 60 + 120 * dn), a)
    a[BAND_Y:BAND_BOT] = 0
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 3] = np.repeat(a[:, None], W, axis=1).clip(0, 255).astype(np.uint8)
    d = ImageDraw.Draw(base := Image.fromarray(arr, 'RGBA'))
    d.rectangle((0, BAND_BOT - 4, W - 1, BAND_BOT - 1), fill=GOLD)          # filete dourado sob o vídeo
    return base


BASE = build_base()
BASE_HDR = BASE.copy()
place(BASE_HDR, HEADER_TOP, W / 2, HEADER_TOP_CY)
place(BASE_HDR, HEADER_SUB, W / 2, HEADER_SUB_CY)


def current_pos(n):
    q = piece_at(n)
    if n >= FIM_A:
        return 1
    if q['kind'] == 'stinger':
        return 3
    return q.get('pos')


def draw_ladder(im, n):
    cp = current_pos(n)
    k_hdr = n - HOOK_END
    for i, lab in enumerate(LADDER):
        p = 1 if lab == '?' else int(lab)
        st = 'now' if p == cp and lab != '?' else ('done' if p > cp else 'next')
        spr = LAD_SPR[(lab, st)]
        cx = LAD_X0 + i * (LAD_W + LAD_GAP) + LAD_W / 2
        sc, al = 1.0, 1.0
        if k_hdr < 10:                                  # a escada entra caixa por caixa
            kk = k_hdr - i
            if kk < 0:
                continue
            sc, al = pop(kk, 5, 0.4), min(1.0, (kk + 1) / 3)
        if st == 'now':
            sc *= pop(n - (pos_start(p) if p != 3 or n >= pos_start(3) else TOP3_A), 6, 1.35) * 1.08
        if lab == '?' and n >= FIM_A:
            sc *= 1.15 + 0.12 * math.sin(2 * math.pi * (n - FIM_A) / (0.9 * FPS))
        place(im, spr, cx, LAD_CY, sc, al)


def render(n):
    im = (BASE if n < HOOK_END else BASE_HDR).copy()
    if n >= HOOK_END and n - HOOK_END < 8:              # o cabeçalho "bate" na entrada da contagem
        im = BASE.copy()
        k = n - HOOK_END
        place(im, HEADER_TOP, W / 2, HEADER_TOP_CY + 6 * (1 - min(1.0, k / 6)), pop(k, 6, 1.12), min(1.0, (k + 1) / 3))
        place(im, HEADER_SUB, W / 2, HEADER_SUB_CY, 1.0, min(1.0, k / 6))
    # gancho
    if n < HOOK_END:
        out = HOOK_END - n
        sc = 1 + 0.018 * math.sin(2 * math.pi * n / (2 * BEAT_F))
        al = 1.0 if out > 4 else out / 4
        place(im, QUESTION, W / 2, QUESTION_CY, sc, al)
        for a, b, spr in CAPS:
            if a <= n < min(b, HOOK_END):
                k = n - a
                place(im, spr, W / 2, CAP_CY, 0.88 + 0.12 * ease_out_back(min(1.0, k / 4)), 1.0 if a == 0 else min(1.0, (k + 1) / 3))
    else:
        draw_ladder(im, n)
    q = piece_at(n)
    # tela de posição
    if q['kind'] == 'src' and q.get('pos'):
        draw_card(im, q['pos'], n - pos_start(q['pos']))
    # TOP 3
    if q['kind'] == 'stinger':
        k = n - q['start']
        place(im, TOP3, W / 2, BAND_Y + BAND_H / 2 - 40, pop(k, 7, 2.0), min(1.0, (k + 1) / 3))
        if k >= 6:
            place(im, TOP3_SUB, W / 2, BAND_Y + BAND_H / 2 + 170, 1.0, min(1.0, (k - 5) / 5))
    # suspense
    if n >= FIM_A:
        k = n - FIM_A
        half = 7 * BEAT_F
        if k < half:
            beat = (k / FPS - 0.45) % 0.9
            hb = 0.06 * math.exp(-beat * 9) if k / FPS >= 0.45 else 0.0
            sc = pop(k, 8, 0.3) * (1 + hb)
            place(im, Q_GLOW, W / 2, BAND_Y + BAND_H / 2 + 40, sc, 0.7 * min(1.0, k / 8))
            place(im, Q_BIG, W / 2, BAND_Y + BAND_H / 2 + 40, sc, min(1.0, (k + 1) / 4) * (1 if half - k > 4 else (half - k) / 4))
            if k >= 6:
                place(im, E_N1, W / 2, BAND_Y + 110, pop(k - 6, 6, 1.4), min(1.0, (k - 5) / 4))
            if k >= 30:
                place(im, VOCE, W / 2, 1405, pop(k - 30, 6, 1.4), min(1.0, (k - 29) / 4))
        else:
            kk = k - half
            place(im, END_TOP, W / 2, BAND_Y + 150, pop(kk, 6, 1.5), min(1.0, (kk + 1) / 3))
            if kk >= 4:
                place(im, END_BOX, W / 2, BAND_Y + 290, pop(kk - 4, 6, 1.4), min(1.0, (kk - 3) / 3))
            if kk >= 9:
                place(im, END_TITLE, W / 2, BAND_Y + 480, 1.0, min(1.0, (kk - 8) / 6))
            if kk >= 14:
                pulse = 1 + 0.035 * math.sin(2 * math.pi * (kk - 14) / (2 * BEAT_F))
                place(im, SUB_BTN, W / 2, BAND_Y + 660, pop(kk - 14, 6, 1.3) * pulse, min(1.0, (kk - 13) / 3))
            if kk >= 20:
                place(im, LINK, W / 2, 1420, 1.0, min(1.0, (kk - 19) / 6))
    return im


if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        for f in sys.argv[2:]:
            render(int(f)).save(os.path.join(HERE, 'frames', f'ov_{int(f):05d}.png'))
