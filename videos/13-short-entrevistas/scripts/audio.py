"""Gera o áudio do Short das entrevistas (audio.wav): o som original de cada
entrevista, inteira e na mesma sincronia da imagem (sem música, sem efeito,
sem acelerar), e no final a narração de abertura do vídeo longo. Cada trecho é
nivelado (as entrevistas vêm de fontes com volumes bem diferentes) e o total
fica em -14 LUFS (padrão do YouTube). Nas emendas, só um fade de 15 ms."""
import json
import subprocess

from timeline import CLIPS, EDL, FPS, N, NARR_N, OUTRO_A

SR = 48000
TARGET = -16.0                 # nível de cada trecho antes do ajuste final


def lufs(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return float(r[r.rindex('I:'):].split()[1])


def cut(t0, frames, out):
    d = frames / FPS
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'original.mp4', '-vn', '-af',
                    f'atrim=start={t0}:duration={d:.4f},asetpts=PTS-STARTPTS,aresample={SR},'
                    f'aformat=channel_layouts=stereo,afade=t=in:d=0.015,afade=t=out:st={d - 0.015:.4f}:d=0.015',
                    '-c:a', 'pcm_f32le', out], check=True)


parts = []
for q in CLIPS:
    cut(q['src'], q['n'], f"part_{q['id']}.wav")
    parts.append((f"part_{q['id']}.wav", q['n']))
cut(EDL['outro']['narration'][0], NARR_N, 'part_narracao.wav')
parts.append(('part_narracao.wav', NARR_N))

gains = {p: TARGET - lufs(p) for p, _ in parts}
F, labels = [], []
for i, (p, _) in enumerate(parts):
    F.append(f"[{i}:a]volume={gains[p]:.2f}dB[p{i}]")
    labels.append(f"[p{i}]")
F.append(''.join(labels) + f"concat=n={len(parts)}:v=0:a=1,apad,atrim=duration={N / FPS:.4f}[aout]")
cmd = ['ffmpeg', '-v', 'error', '-y']
for p, _ in parts:
    cmd += ['-i', p]
subprocess.run(cmd + ['-filter_complex', ';'.join(F), '-map', '[aout]', '-c:a', 'pcm_f32le', 'mix.wav'], check=True)
assert sum(n for _, n in parts) == OUTRO_A + NARR_N

LN = 'loudnorm=I=-14:TP=-3:LRA=11'
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', 'mix.wav', '-af', LN + ':print_format=json',
                    '-f', 'null', '-'], capture_output=True, text=True).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
ln2 = (f"{LN}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
       f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'mix.wav', '-af',
                f"{ln2},aresample={SR},asetpts=PTS-STARTPTS,apad,atrim=duration={N / FPS:.4f}",
                '-c:a', 'pcm_s16le', 'audio.wav'], check=True)
print('audio.wav ok', {p: round(g, 1) for p, g in gains.items()})
