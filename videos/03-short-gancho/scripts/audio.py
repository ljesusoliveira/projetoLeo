"""Gera o áudio do Short-gancho (audio.wav): narração/torcida de cada lance
na mesma sincronia do vídeo, efeitos sonoros sintetizados (impacto, passagem,
fita rebobinando, subida de tensão) e volume final em -14 LUFS."""
import json
import subprocess

from timeline import BYID, FPS, GROUPS, N, PIECES

SR = 48000
F = []      # cadeias do filtro
mix = []    # rótulos que vão para a mixagem final


def sec(n):
    return n / FPS


# ---------------------------------------------------------------- trilha base
labels = []
srcs = [q for q in PIECES if q['kind'] == 'src']
F.append(f"[0:a]asplit={len(srcs) + 2}" + ''.join(f"[s{i}]" for i in range(len(srcs) + 2)))
si = 0
for i, q in enumerate(PIECES):
    d = q['n'] / FPS
    if q['kind'] == 'src':
        a, b = q['src']
        F.append(f"[s{si}]atrim=start={a}:end={a + d},asetpts=PTS-STARTPTS,aresample={SR},"
                 f"aformat=channel_layouts=stereo,afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[p{i}]")
        si += 1
    elif q['kind'] == 'rewind':
        # som de fita: o final do lance anterior tocado de trás para frente em 2x
        of = BYID[q['of']]
        b = of['src'][1]
        F.append(f"[s{si}]atrim=start={b - 2 * d:.3f}:end={b},asetpts=PTS-STARTPTS,areverse,atempo=2.0,"
                 f"aresample={SR},aformat=channel_layouts=stereo,lowpass=f=3500,volume=0.8,"
                 f"atrim=duration={d:.3f},afade=t=in:d=0.03,afade=t=out:st={d - 0.06:.3f}:d=0.06[p{i}]")
        si += 1
    else:
        F.append(f"anullsrc=r={SR}:cl=stereo,atrim=duration={d:.4f}[p{i}]")
    labels.append(f"[p{i}]")
F.append(''.join(labels) + f"concat=n={len(labels)}:v=0:a=1[base]")
mix.append('[base]')

# fundo abafado da torcida no encerramento
fin = BYID['final']
F.append(f"[s{si}]atrim=start=246.6:end={246.6 + fin['n'] / FPS:.3f},asetpts=PTS-STARTPTS,"
         f"aresample={SR},aformat=channel_layouts=stereo,lowpass=f=1200,volume=0.22,"
         f"afade=t=in:d=0.4,afade=t=out:st={fin['n'] / FPS - 0.8:.3f}:d=0.8,"
         f"adelay={round(sec(fin['start']) * 1000)}:all=1[bed]")
mix.append('[bed]')

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
    sfx(f"anoisesrc=d=0.18:c=white:a=0.6:r={SR},highpass=f=2500,afade=t=out:d=0.18:curve=exp", at, vol * 0.5)


def whoosh(at, vol, d=0.4):
    sfx(f"anoisesrc=d={d}:c=pink:a=0.9:r={SR},bandpass=f=1400:width_type=h:w=2200,"
        f"afade=t=in:d={d * 0.7:.3f}:curve=exp,afade=t=out:st={d * 0.7:.3f}:d={d * 0.3:.3f}", at, vol)


# gancho: passagem + impacto no congelamento da bicicleta
gf = BYID['gancho-freeze']
whoosh(sec(gf['start']) - 0.32, 0.9)
boom(sec(gf['start']), 1.0)
# passagens leves entre os gols
for g in GROUPS[1:]:
    if g['id'] in ('rebobina', 'final'):
        continue
    whoosh(sec(g['start']) - 0.2, 0.45, 0.32)
# subida de tensão no suspense e impacto no encerramento
su = BYID['suspense']
d = su['n'] / FPS
sfx(f"aevalsrc=exprs='0.22*sin(2*PI*(170*t+230*t*t))*pow(t/{d:.3f},2)':s={SR}:d={d:.3f}", sec(su['start']), 1.0)
sfx(f"anoisesrc=d={d:.3f}:c=pink:a=0.5:r={SR},highpass=f=900,afade=t=in:d={d:.3f}:curve=exp",
    sec(su['start']), 0.8)
boom(sec(fin['start']), 1.0, 1.8)

F.append(''.join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,"
         f"asetpts=PTS-STARTPTS,apad,atrim=duration={N / FPS:.4f}[aout]")
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
