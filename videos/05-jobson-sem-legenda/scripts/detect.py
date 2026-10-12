"""Passo 1: acha as legendas em todos os quadros.
A legenda é sempre centralizada, numa faixa escura semitransparente fixa
nas linhas 901 a 976. O texto é branco com contorno preto: um pixel claro
com pixel escuro colado a ele, dentro da faixa, é texto.
Gera legendas.json com cada legenda (quadro inicial, final e extensão x)."""
import json
import subprocess

import cv2
import numpy as np

W, H, FPS = 1920, 1080, 30
BY0, BY1 = 901, 977                 # faixa da caixa (linhas)
K5 = np.ones((5, 5), np.uint8)


TR0, TR1 = 914 - BY0, 960 - BY0          # linhas das letras dentro do recorte


def text_extent(band):
    g = band.astype(np.float32).mean(2)[TR0:TR1]
    bright = g > 190
    dark = (g < 45).astype(np.uint8)
    # letra = pixel claro com contorno escuro dos DOIS lados (até 7 px); o fundo
    # claro colado na borda da faixa só tem escuro de um lado e fica de fora
    left = cv2.dilate(dark, np.ones((1, 8), np.uint8), anchor=(7, 0))
    right = cv2.dilate(dark, np.ones((1, 8), np.uint8), anchor=(0, 0))
    txt = bright & (left > 0) & (right > 0)
    cols = txt.sum(0)
    xs = np.where(cols > 0)[0]
    if cols.sum() < 120:
        return None
    # agrupa colunas (espaço entre palavras < 60 px) e fica com o grupo que passa
    # pelo centro da tela (outras coisas claras na imagem ficam de fora)
    groups = np.split(xs, np.where(np.diff(xs) > 60)[0] + 1)
    groups = [gp for gp in groups if cols[gp].sum() > 30]
    if not groups:
        return None
    gp = min(groups, key=lambda a: 0 if a[0] <= W / 2 <= a[-1] else min(abs(a[0] - W / 2), abs(a[-1] - W / 2)))
    x0, x1 = gp[0], gp[-1]
    # a legenda é centralizada: rejeita o que não estiver em volta do meio
    if abs((x0 + x1) / 2 - W / 2) > 40:
        return None
    return int(x0), int(x1), int(cols.sum())


def main():
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', 'original.mp4', '-vf', f'crop={W}:{BY1 - BY0}:0:{BY0}',
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    sz = W * (BY1 - BY0) * 3
    per = []
    n = 0
    while True:
        buf = p.stdout.read(sz)
        if len(buf) < sz:
            break
        per.append(text_extent(np.frombuffer(buf, np.uint8).reshape(BY1 - BY0, W, 3)))
        n += 1
    p.wait()
    # junta quadros seguidos com a mesma legenda: a extensão pode oscilar uns
    # pixels (fundo claro colado à caixa), então compara com a mediana do trecho
    subs = []
    for i, e in enumerate(per):
        if e is None:
            continue
        x0, x1, _ = e
        if subs:
            s = subs[-1]
            m0, m1 = np.median(s['xs0']), np.median(s['xs1'])
            if s['f1'] >= i - 3 and abs(m0 - x0) <= 30 and abs(m1 - x1) <= 30:
                s['f1'] = i
                s['xs0'].append(x0)
                s['xs1'].append(x1)
                continue
        subs.append(dict(f0=i, f1=i, xs0=[x0], xs1=[x1]))
    for s in subs:
        s['x0'] = int(np.median(s.pop('xs0')))
        s['x1'] = int(np.median(s.pop('xs1')))
    subs = [s for s in subs if s['f1'] - s['f0'] >= 3]
    json.dump(dict(frames=n, legendas=subs), open('legendas.json', 'w'), indent=1)
    np.save('per_frame.npy', np.array([e[:2] if e else (-1, -1) for e in per]))
    print(f'{n} quadros, {len(subs)} legendas')
    for s in subs:
        print(f"  {s['f0'] / FPS:7.2f}-{(s['f1'] + 1) / FPS:7.2f}s  x {s['x0']}-{s['x1']}")


if __name__ == '__main__':
    main()
