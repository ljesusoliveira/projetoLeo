"""Gera o áudio do Short do Mário Sérgio (audio.wav): a narração original do
vídeo longo (com a trilha que já vem por baixo dela), cortada nas pausas entre
as frases, sem trocar a música. Só entram efeitos curtos: passagem entre os
capítulos, impacto nos congelamentos e no "revólver", e um grave na virada
"33 anos depois". Volume final em -14 LUFS (padrão do YouTube)."""
import json
import subprocess

from timeline import AUDIO, BYID, CHAPTERS, END_A, FPS, N, PIECES

SR = 48000
F = []      # cadeias do filtro
mix = []    # rótulos que vão para a mixagem final


def sec(n):
    return n / FPS


# ---------------------------------------------------------------- narração
labels = []
srcs = [a for a in AUDIO if 'src' in a]
F.append(f"[0:a]asplit={len(srcs)}" + ''.join(f"[s{i}]" for i in range(len(srcs))))
si = 0
for i, a in enumerate(AUDIO):
    d = (a['end'] - a['start']) / FPS
    if 'src' in a:
        t0 = a['src'][0]
        F.append(f"[s{si}]atrim=start={t0}:end={t0 + d:.4f},asetpts=PTS-STARTPTS,aresample={SR},"
                 f"aformat=channel_layouts=stereo,"
                 f"afade=t=in:d=0.03,afade=t=out:st={d - 0.04:.3f}:d=0.04[p{i}]")
        si += 1
    else:
        F.append(f"anullsrc=r={SR}:cl=stereo,atrim=duration={d:.4f}[p{i}]")
    labels.append(f"[p{i}]")
F.append(''.join(labels) + f"concat=n={len(labels)}:v=0:a=1[base]")
mix.append('[base]')

# ---------------------------------------------------------------- efeitos
k = 0


def sfx(chain, at, vol):
    global k
    lab = f"fx{k}"
    k += 1
    F.append(f"{chain},aformat=sample_rates={SR}:channel_layouts=stereo,volume={vol},"
             f"adelay={max(0, round(at * 1000))}:all=1[{lab}]")
    mix.append(f'[{lab}]')


def boom(at, vol, d=1.4):
    sfx(f"aevalsrc=exprs='0.9*sin(2*PI*(40+120*exp(-9*t))*t)*exp(-2.8*t)':s={SR}:d={d}", at, vol)
    sfx(f"anoisesrc=d=0.18:c=white:a=0.6:r={SR},highpass=f=2500,afade=t=out:d=0.18:curve=exp", at, vol * 0.4)


def whoosh(at, vol, d=0.4):
    sfx(f"anoisesrc=d={d}:c=pink:a=0.9:r={SR},bandpass=f=1400:width_type=h:w=2200,"
        f"afade=t=in:d={d * 0.7:.3f}:curve=exp,afade=t=out:st={d * 0.7:.3f}:d={d * 0.3:.3f}", at, vol)


# passagem curta na entrada de cada capítulo
for c in CHAPTERS[1:]:
    whoosh(sec(c) - 0.25, 0.35, 0.32)
# impacto: "revólver" e os congelamentos com flash
boom(sec(BYID['revolver']['hit_f']), 0.55)
for q in PIECES:
    if q['kind'] == 'freeze' and q.get('flash'):
        boom(sec(q['start']), 0.7)
# virada "33 anos depois": grave longo e respiro antes da tragédia
g2 = next(a for a in AUDIO if a['id'] == 'g2')
boom(sec(g2['start']), 0.85, 2.2)
sfx(f"aevalsrc=exprs='0.25*sin(2*PI*55*t)*exp(-1.6*t)':s={SR}:d=1.6", sec(g2['start']), 0.8)
# encerramento
boom(sec(END_A), 0.5, 1.6)

F.append(''.join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,"
         f"asetpts=PTS-STARTPTS,apad,atrim=duration={N / FPS:.4f},"
         f"afade=t=out:st={N / FPS - 0.12:.3f}:d=0.12[aout]")
open('audio_filter.txt', 'w').write(';\n'.join(F))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'original.mp4', '-filter_complex_script', 'audio_filter.txt',
                '-map', '[aout]', '-c:a', 'pcm_f32le', 'mix.wav'], check=True)

# volume no padrão do YouTube: loudnorm em duas passadas (mede e depois aplica de forma linear)
LN = 'loudnorm=I=-14:TP=-1.5:LRA=11'
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', 'mix.wav', '-af', LN + ':print_format=json',
                    '-f', 'null', '-'], capture_output=True, text=True).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
ln2 = (f"{LN}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
       f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'mix.wav', '-af',
                f"{ln2},aresample={SR},asetpts=PTS-STARTPTS,apad,atrim=duration={N / FPS:.4f}",
                '-c:a', 'pcm_s16le', 'audio.wav'], check=True)
print('audio.wav ok')
