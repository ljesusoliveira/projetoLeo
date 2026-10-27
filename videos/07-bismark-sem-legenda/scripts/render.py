"""Passo 2: apaga a legenda de um trecho do vídeo (só imagem, sem áudio).
  python3 render.py saida.mp4 quadro_inicial quadro_final
Lê 2 s a mais antes e depois do trecho, para poder copiar a imagem real de
quadros vizinhos em cenas paradas."""
import subprocess
import sys
import time
from collections import deque

import numpy as np

from unsub import BY0, BY1, FPS, H, REACH, W, clean_band

boxes = np.load('boxes.npy')
out, f0, f1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
r0, r1 = max(0, f0 - REACH), min(len(boxes), f1 + REACH)
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{r0 / FPS:.4f}', '-i', 'original.mp4',
                        '-frames:v', str(r1 - r0), '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
                       stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                        '-pix_fmt', 'yuv420p', '-color_range', 'tv', '-colorspace', 'bt709',
                        '-color_primaries', 'bt709', '-color_trc', 'bt709', out], stdin=subprocess.PIPE)
frames = {}          # quadro -> bytes do quadro inteiro (janela deslizante)
bands = {}           # quadro -> faixa da legenda (para os vizinhos)
order = deque()
nxt = r0             # próximo quadro a ler
cur = f0             # próximo quadro a escrever
tic = time.time()


def read_one():
    global nxt
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        return False
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    frames[nxt] = buf
    bands[nxt] = np.ascontiguousarray(fr[BY0:BY1])
    order.append(nxt)
    nxt += 1
    return True


alive = True
while cur < f1:
    while alive and nxt <= min(cur + REACH, r1 - 1):
        alive = read_one()
    if cur not in frames:
        break
    band = clean_band(cur, bands, boxes, lambda m: np.frombuffer(frames[m], np.uint8).reshape(H, W, 3))
    buf = frames[cur]
    if band is not None:
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        fr[BY0:BY1] = band
        buf = fr.tobytes()
    enc.stdin.write(buf)
    cur += 1
    while order and order[0] < cur - REACH:
        old = order.popleft()
        frames.pop(old, None)
        bands.pop(old, None)
    if (cur - f0) % 300 == 0:
        print(f'{cur / FPS / 60:.2f} min ({(cur - f0) / (time.time() - tic):.1f} quadros/s)', flush=True)
enc.stdin.close()
enc.wait()
dec.kill()
print(f'trecho {f0}-{f1} pronto em {(time.time() - tic) / 60:.1f} min', flush=True)
