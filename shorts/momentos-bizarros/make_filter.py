"""Gera filter.txt: para cada lance, recorta o vídeo (sem as faixas pretas),
monta o fundo desfocado, aplica cor/nitidez e junta tudo com a camada gráfica."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
segs = json.load(open(os.path.join(HERE, 'segments.json')))['segs']
af = open(os.path.join(HERE, 'af.txt')).read().strip()

parts = [f"[0:v]split={len(segs)}" + ''.join(f"[s{i}]" for i in range(len(segs)))]
for i, s in enumerate(segs):
    parts.append(
        f"[s{i}]trim=start_frame={s['start']}:end_frame={s['end'] + 1},setpts=PTS-STARTPTS,"
        f"crop=1080:{s['ch']}:0:{s['cy']},split[a{i}][b{i}]")
    parts.append(
        f"[b{i}]scale=-2:480,crop=270:480,gblur=sigma=12,scale=1080:1920:flags=bicubic,"
        f"eq=brightness=-0.05:saturation=1.3[bg{i}]")
    parts.append(f"[a{i}]eq=contrast=1.06:saturation=1.14,unsharp=5:5:0.55:5:5:0[fg{i}]")
    parts.append(f"[bg{i}][fg{i}]overlay=0:{s['py']},setsar=1[v{i}]")
parts.append(''.join(f"[v{i}]" for i in range(len(segs)))
             + f"concat=n={len(segs)}:v=1:a=0,format=yuv444p[base]")
parts.append("[1:v]scale=out_color_matrix=bt709:out_range=tv,format=yuva444p[ov]")
parts.append("[base][ov]overlay=0:0:format=yuv444:eof_action=pass,format=yuv420p[vout]")
parts.append(f"[0:a]{af}[aout]")
open(os.path.join(HERE, 'filter.txt'), 'w').write(';\n'.join(parts))
