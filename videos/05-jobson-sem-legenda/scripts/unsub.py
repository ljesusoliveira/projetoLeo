"""Remoção da legenda de um quadro.
A faixa da legenda é preta com ~70% de opacidade: dentro dela a imagem é
  dentro = K * fundo + M   (K ~ 0,30, medido no próprio vídeo)
Então o fundo é recuperado invertendo essa conta. Só as letras (brancas
com contorno preto) e a borda de 1-2 px da faixa precisam ser preenchidas
com a imagem em volta."""
import json

import cv2
import numpy as np

W, H, FPS = 1920, 1080, 30
BY0, BY1 = 901, 977                       # linhas da faixa (inclusive, exclusive)
RY0, RY1 = 880, 1000                      # recorte trabalhado
K = np.array([0.310, 0.304, 0.302], np.float32)       # B, G, R
M = np.array([-2.06, -0.52, -1.38], np.float32)
PAD_L, PAD_R = 13, 14                     # faixa = texto + margem
TY0, TY1 = 914, 960                       # linhas ocupadas pelas letras (com acentos e contorno)
ELL = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r, r))


def box_for(x0, x1):
    return x0 - PAD_L, x1 + PAD_R


def refine_box(g, L, R):
    """Acerta as bordas laterais da faixa pelo degrau de brilho (linhas sem texto)."""
    r = g[BY0 + 2 - RY0:BY0 + 12 - RY0].mean(0)
    dx = np.diff(r)
    a0, a1 = max(L - 5, 1), min(L + 6, W - 2)
    b0, b1 = max(R - 5, 1), min(R + 6, W - 2)
    l = a0 + int(np.argmin(dx[a0:a1])) + 1
    rr = b0 + int(np.argmax(dx[b0:b1]))
    if dx[l - 1] < -6:
        L = l
    if dx[rr] > 6:
        R = rr
    return L, R


def clean(crop, L, R, x0=None, x1=None):
    """crop: linhas RY0..RY1 do quadro (BGR uint8). Devolve o recorte sem a legenda."""
    img = crop.astype(np.float32)
    L, R = refine_box(img.mean(2), L, R)
    y0, y1 = BY0 - RY0, BY1 - RY0
    a, b = max(L, 0), min(R + 1, W)
    rec = (img[y0:y1, a:b] - M) / K
    # o ganho de ~3,3x também amplifica o ruído de compressão; suaviza de leve
    rec = cv2.bilateralFilter(np.clip(rec, 0, 255), 7, 18, 4)
    out = img.copy()
    out[y0:y1, a:b] = rec
    # faixa das letras: troca por uma transição suave entre a linha de cima e a de baixo
    tx0 = a + PAD_L - 10 if x0 is None else x0 - 10
    tx1 = b - PAD_R + 10 if x1 is None else x1 + 10
    t0, t1 = TY0 - 3 - RY0, TY1 + 3 - RY0
    top = out[t0 - 4:t0].mean(0)
    bot = out[t1:t1 + 4].mean(0)
    w = np.linspace(0, 1, t1 - t0)[:, None, None]
    band = top[None] * (1 - w) + bot[None] * w
    band = cv2.GaussianBlur(band, (0, 0), sigmaX=6, sigmaY=1.5)
    # bordas da faixa das letras com transição suave de 5 px
    fz = 5
    ramp = (1 - np.cos(np.linspace(0, np.pi, fz + 2)[1:-1])) / 2   # 0 -> 1 suave
    feather = np.ones((t1 - t0, 1, 1), np.float32)
    feather[:fz, 0, 0] = ramp
    feather[-fz:, 0, 0] = ramp[::-1]
    seg = out[t0:t1, tx0:tx1]
    xf = np.ones((1, tx1 - tx0, 1), np.float32)
    xf[0, :fz, 0] = ramp
    xf[0, -fz:, 0] = ramp[::-1]
    al = feather * xf
    out[t0:t1, tx0:tx1] = seg * (1 - al) + band[:, tx0:tx1] * al
    out = np.clip(out, 0, 255).astype(np.uint8)
    # borda da faixa: alguns px com cor misturada e ruído de compressão aumentado
    mask = np.zeros(crop.shape[:2], np.uint8)
    eo, ei = 3, 7                              # px para fora / para dentro da borda
    mask[y0 - eo:y0 + ei, a - eo:b + eo] = 1
    mask[y1 - ei:y1 + eo, a - eo:b + eo] = 1
    mask[y0 - eo:y1 + eo, a - eo:a + ei] = 1
    mask[y0 - eo:y1 + eo, b - ei:b + eo] = 1
    return cv2.inpaint(out, mask * 255, 4, cv2.INPAINT_TELEA)


class Boxes:
    """Extensão da legenda em cada quadro, a partir da detecção quadro a quadro
    (mediana numa janela de ±5 quadros para tirar oscilações e falhas)."""

    def __init__(self, per_frame='per_frame.npy'):
        p = np.load(per_frame)
        self.n = len(p)
        self.ext = [None] * self.n
        for i in range(self.n):
            lo, hi = max(0, i - 5), min(self.n, i + 6)
            win = [tuple(p[j]) for j in range(lo, hi) if p[j][0] >= 0]
            if p[i][0] < 0:
                # quadro sem detecção: só conta se há legenda igual dos dois lados (falha de 1-3 quadros)
                before = [tuple(p[j]) for j in range(max(0, i - 3), i) if p[j][0] >= 0]
                after = [tuple(p[j]) for j in range(i + 1, min(self.n, i + 4)) if p[j][0] >= 0]
                if not before or not after or abs(before[-1][0] - after[0][0]) > 30:
                    continue
            ref = p[i] if p[i][0] >= 0 else np.array(before[-1])
            sim = [w for w in win if abs(w[0] - ref[0]) <= 30 and abs(w[1] - ref[1]) <= 30]
            x0 = int(np.median([w[0] for w in sim]))
            x1 = int(np.median([w[1] for w in sim]))
            self.ext[i] = box_for(x0, x1) + (x0, x1)

    def __getitem__(self, i):
        return self.ext[i] if 0 <= i < self.n else None
