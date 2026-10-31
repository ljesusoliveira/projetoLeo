"""Gera o áudio do Short do Top 10 centroavantes (audio.wav).
O vídeo longo não tem som nos lances, só a narração de abertura. Então:
  - a batida original do musica.py (feita do zero aqui, sem direito autoral),
    montada seção por seção a partir da linha do tempo, para cada corte e cada
    tela de posição caírem num tempo da batida;
  - a narração de abertura original ("Dez centroavantes, dez lendas, mas só um
    pode ser o maior da história do Brasil."), sem cortar nem acelerar, por cima
    do gancho, com a batida baixa por baixo.
Volume final em -14 LUFS (padrão do YouTube)."""
import json
import subprocess

import musica
from timeline import EDL, FPS, N, PIECES

SR = 48000


def sections():
    out, bar, i = [], 0, 0
    while i < len(PIECES):
        q = PIECES[i]
        if q['id'] == 'hook':
            out.append({'type': 'hook', 'beats': q['beats'], 'impact': 0.6, 'pad': 0.55})
        elif q['kind'] == 'stinger':
            out.append({'type': 'stinger', 'beats': q['beats']})
        elif q['kind'] == 'suspense':
            out.append({'type': 'suspense', 'beats': q['beats'], 'hits': [7 * musica.BEAT]})
        elif q['pos'] >= 4:                            # contagem: uma seção por posição
            out.append({'type': 'count', 'beats': q['beats'], 'bar': bar, 'level': 1 if q['pos'] >= 8 else 2,
                        'hit': True, 'fill': q.get('fill', False)})
            bar += 1
        else:                                          # Top 3: uma seção por jogador, prato nos cortes internos
            grp = [q]
            while i + 1 < len(PIECES) and PIECES[i + 1].get('pos') == q['pos']:
                i += 1
                grp.append(PIECES[i])
            acc, b = [], 0
            for g in grp[:-1]:
                b += g['beats']
                acc.append(b)
            out.append({'type': 'top', 'beats': sum(g['beats'] for g in grp), 'bar': bar, 'hit': True,
                        'accents': acc, 'fill': grp[-1].get('fill', False)})
            bar += 2
        i += 1
    assert sum(s['beats'] for s in out) * musica.BEAT * FPS == N
    return out


def lufs(path, extra=''):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', extra + 'ebur128', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return float(r[r.rindex('I:'):].split()[1])


secs = sections()
json.dump(secs, open('music_sections.json', 'w'), indent=1)
musica.build(secs, 'music.wav', N / FPS)

# narração de abertura (original, só com um fade de 30 ms nas pontas)
a, b = EDL['narration']['src']
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'original.mp4', '-vn', '-af',
                f'atrim={a}:{b},asetpts=PTS-STARTPTS,aresample={SR},aformat=channel_layouts=stereo,'
                f'afade=t=in:d=0.02,afade=t=out:st={b - a - 0.03:.3f}:d=0.03', 'voz.wav'], check=True)

# a voz fica 2 dB acima do volume da batida na contagem
hook_end = PIECES[0]['n'] / FPS
music_count = lufs('music.wav', f'atrim={hook_end}:{hook_end + 20},')
voice = lufs('voz.wav')
vgain = (music_count + 2) - voice
F = (f"[1:a]volume={vgain:.2f}dB,apad[v];"
     f"[0:a][v]amix=inputs=2:normalize=0:duration=first,atrim=duration={N / FPS:.4f}[m]")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'music.wav', '-i', 'voz.wav', '-filter_complex', F,
                '-map', '[m]', '-c:a', 'pcm_f32le', 'mix.wav'], check=True)

# volume no padrão do YouTube: loudnorm em duas passadas (mede e depois aplica de forma linear)
LN = 'loudnorm=I=-14:TP=-3:LRA=11'          # folga para o pico não passar de -1 dB depois do AAC
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', 'mix.wav', '-af', LN + ':print_format=json',
                    '-f', 'null', '-'], capture_output=True, text=True).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
ln2 = (f"{LN}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
       f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'mix.wav', '-af',
                f"{ln2},aresample={SR},asetpts=PTS-STARTPTS,apad,atrim=duration={N / FPS:.4f}",
                '-c:a', 'pcm_s16le', 'audio.wav'], check=True)
print(f'audio.wav ok (voz {vgain:+.1f} dB)')
