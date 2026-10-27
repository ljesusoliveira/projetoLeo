"""Passo 1: acha a caixa amarela da legenda em todos os quadros.
A caixa é amarelo puro (BGR ~0,253,253), sempre na mesma faixa de altura e
centralizada; a largura muda com a palavra. Gera boxes.npy com (x0, y0, x1, y1)
por quadro, ou -1 quando não há legenda."""
import subprocess
import sys

import cv2
import numpy as np

W, H, FPS = 1920, 1080, 30
SY0, SY1 = 820, 1040                     # faixa de busca


def find_box(band):
    b, g, r = [band[..., i].astype(np.int16) for i in range(3)]
    yel = ((b < 40) & (g > 225) & (r > 225)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(yel)
    best = None
    for i in range(1, n):
        x, y, w, h, a = st[i]
        cx = x + w / 2
        # caixa: retângulo cheio (com as letras pretas dentro), centralizada
        if h < 40 or w < 60 or abs(cx - W / 2) > 60:
            continue
        if a / (w * h) < 0.45:
            continue
        if best is None or a > best[4]:
            best = (x, y, w, h, a)
    if best is None:
        return None
    x, y, w, h, _ = best
    return x, SY0 + y, x + w - 1, SY0 + y + h - 1


def main():
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', 'original.mp4', '-vf', f'crop={W}:{SY1 - SY0}:0:{SY0}',
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    sz = W * (SY1 - SY0) * 3
    out = []
    while True:
        buf = p.stdout.read(sz)
        if len(buf) < sz:
            break
        bx = find_box(np.frombuffer(buf, np.uint8).reshape(SY1 - SY0, W, 3))
        out.append(bx if bx else (-1, -1, -1, -1))
    p.wait()
    out = np.array(out)
    np.save('boxes.npy', out)
    has = out[:, 0] >= 0
    print(f'{len(out)} quadros, {has.sum()} com legenda')
    if has.any():
        print('y0', np.unique(out[has, 1], return_counts=True))
        print('y1', np.unique(out[has, 3], return_counts=True))
        print('largura', out[has, 2].max() - 0, 'min x0', out[has, 0].min(), 'max x1', out[has, 2].max())


if __name__ == '__main__':
    main()
