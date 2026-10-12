"""Passo 2: decodifica o vídeo, apaga a legenda dos quadros que têm legenda e
recodifica (áudio original copiado, sem mexer).
  python3 render.py saida.mp4 [início_s fim_s]"""
import subprocess
import sys
import time

import numpy as np

from unsub import FPS, H, RY0, RY1, W, Boxes, clean

out = sys.argv[1]
t0, t1 = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (0.0, None)
bx = Boxes()
cut = ['-ss', f'{t0:.3f}'] + (['-t', f'{t1 - t0:.3f}'] if t1 else [])
dec = subprocess.Popen(['ffmpeg', '-v', 'error'] + cut + ['-i', 'original.mp4', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
                       stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-'] + cut + ['-i', 'original.mp4', '-map', '0:v', '-map', '1:a',
                       '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
                       '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                       '-c:a', 'copy', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
n = round(t0 * FPS)
done = 0
tic = time.time()
while True:
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    e = bx[n]
    if e is not None:
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        fr[RY0:RY1] = clean(fr[RY0:RY1], *e)
        buf = fr.tobytes()
        done += 1
    enc.stdin.write(buf)
    n += 1
    if n % 900 == 0:
        print(f'{n / FPS / 60:.1f} min ({n / (time.time() - tic):.0f} quadros/s)', flush=True)
enc.stdin.close()
enc.wait()
dec.wait()
print(f'quadros {n - round(t0 * FPS)}, com legenda apagada {done}, em {(time.time() - tic) / 60:.1f} min')
