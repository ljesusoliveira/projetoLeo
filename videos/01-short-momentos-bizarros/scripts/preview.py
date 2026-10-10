"""Monta quadros de prévia (fundo desfocado + vídeo + camada gráfica)."""
import json
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import overlay  # noqa: E402

D = json.load(open(os.path.join(HERE, 'segments.json')))


def seg_chain(s, grade=True):
    ch, cy, py = s['ch'], s['cy'], s['py']
    fg = 'eq=contrast=1.06:saturation=1.14,unsharp=5:5:0.55:5:5:0' if grade else 'null'
    return (f"crop=1080:{ch}:0:{cy},split[a][b];"
            f"[b]scale=-2:480,crop=270:480,gblur=sigma=12,scale=1080:1920:flags=bicubic,"
            f"eq=brightness=-0.05:saturation=1.3[bg];"
            f"[a]{fg}[fg];[bg][fg]overlay=0:{py}")


def base_frame(n, grade=True):
    s = D['segs'][overlay.seg_of(n)]
    out = os.path.join(HERE, f'base_{n:05d}.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{n / 30:.4f}', '-i',
                    os.path.join(HERE, 'original.mp4'), '-frames:v', '1',
                    '-filter_complex', seg_chain(s, grade), out], check=True)
    return Image.open(out).convert('RGBA')


if __name__ == '__main__':
    frames = [int(x) for x in sys.argv[1:]]
    tiles = []
    for n in frames:
        im = base_frame(n)
        im.alpha_composite(overlay.render(n))
        im.convert('RGB').save(os.path.join(HERE, f'prev_{n:05d}.jpg'), quality=92)
        tiles.append(im.convert('RGB'))
    # folha com as prévias lado a lado (meia resolução)
    tw, th = 540, 960
    sheet = Image.new('RGB', (tw * len(tiles) + 10 * (len(tiles) - 1), th), 'white')
    for k, t in enumerate(tiles):
        sheet.paste(t.resize((tw, th), Image.LANCZOS), (k * (tw + 10), 0))
    sheet.save(os.path.join(HERE, 'prev_sheet.jpg'), quality=90)
