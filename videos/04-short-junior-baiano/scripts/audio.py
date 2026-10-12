"""Gera o áudio do Short do Júnior Baiano (audio.wav): som original de cada
lance na mesma sincronia do vídeo, efeitos sintetizados (parada de fita no
"SERÁ?", impacto no contato de cada falta, passagem entre lances, apito no
cartão vermelho, subida de tensão no suspense) e volume final em -14 LUFS."""
import json
import subprocess

from timeline import BYID, FPS, GROUPS, N, PIECES, out_frame

SR = 48000
F = []      # cadeias do filtro
mix = []    # rótulos que vão para a mixagem final


def sec(n):
    return n / FPS


# ---------------------------------------------------------------- som dos lances
labels = []
srcs = [q for q in PIECES if q['kind'] == 'src']
F.append(f"[0:a]asplit={len(srcs) + 1}" + ''.join(f"[s{i}]" for i in range(len(srcs) + 1)))
si = 0
for i, q in enumerate(PIECES):
    d = q['n'] / FPS
    if q['kind'] == 'src':
        a = q['src'][0]
        F.append(f"[s{si}]atrim=start={a}:end={a + d},asetpts=PTS-STARTPTS,aresample={SR},"
                 f"aformat=channel_layouts=stereo,volume=0.7,"
                 f"afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[p{i}]")
        si += 1
    else:
        F.append(f"anullsrc=r={SR}:cl=stereo,atrim=duration={d:.4f}[p{i}]")
    labels.append(f"[p{i}]")
F.append(''.join(labels) + f"concat=n={len(labels)}:v=0:a=1[base]")
mix.append('[base]')

# torcida abafada por baixo do encerramento
fin = BYID['final']
fd = fin['n'] / FPS
F.append(f"[s{si}]atrim=start=242.0:end={242.0 + fd:.3f},asetpts=PTS-STARTPTS,"
         f"aresample={SR},aformat=channel_layouts=stereo,lowpass=f=1200,volume=0.2,"
         f"afade=t=in:d=0.4,afade=t=out:st={fd - 0.8:.3f}:d=0.8,"
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


def thud(at, vol):
    """Pancada seca no contato: grave curto + estalo."""
    sfx(f"aevalsrc=exprs='0.9*sin(2*PI*(55+90*exp(-25*t))*t)*exp(-11*t)':s={SR}:d=0.45", at, vol)
    sfx(f"anoisesrc=d=0.06:c=brown:a=0.9:r={SR},lowpass=f=1800,afade=t=out:d=0.06", at, vol * 0.6)


def whoosh(at, vol, d=0.4):
    sfx(f"anoisesrc=d={d}:c=pink:a=0.9:r={SR},bandpass=f=1400:width_type=h:w=2200,"
        f"afade=t=in:d={d * 0.7:.3f}:curve=exp,afade=t=out:st={d * 0.7:.3f}:d={d * 0.3:.3f}", at, vol)


def tape_stop(at, vol, d=0.38):
    """Parada de fita: tom que despenca de 700 Hz para quase nada."""
    sfx(f"aevalsrc=exprs='0.5*sin(2*PI*(700*t-850*t*t))*(1-t/{d})':s={SR}:d={d}", at, vol)


def whistle(at, vol, d=0.9):
    """Apito de árbitro: tom agudo com trinado."""
    sfx(f"aevalsrc=exprs='0.35*sin(2*PI*3100*t+2.5*sin(2*PI*32*t))*(0.75+0.25*sin(2*PI*32*t))':"
        f"s={SR}:d={d},afade=t=in:d=0.02,afade=t=out:st={d - 0.12:.3f}:d=0.12", at, vol)


# gancho: a frase dele "trava" e entra o "SERÁ?"
f1 = BYID['f1a']
tape_stop(sec(f1['start']) - 0.36, 0.9)
boom(sec(f1['start']), 0.8, 1.0)
# impacto no contato de cada falta
for q in PIECES:
    if 'hit' in q:
        t = sec(out_frame(q['id'], q['hit']))
        nxt = PIECES[PIECES.index(q) + 1]
        if nxt['kind'] == 'freeze':
            boom(t, 1.0)          # congelamento: impacto forte
        else:
            thud(t, 0.95)
# passagens entre as faltas
for g in GROUPS[2:]:
    if g['id'] in ('teaser', 'final'):
        continue
    whoosh(sec(g['start']) - 0.22, 0.5, 0.34)
# apito no cartão vermelho
cd = BYID['card']
whistle(sec(out_frame('card', cd['whistle'])), 0.6)
# subida de tensão no suspense e impacto no encerramento
su = BYID['teaser']
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
