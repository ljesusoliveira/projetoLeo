"""Gera o áudio do Short do Mozer (audio.wav): só a narração original do vídeo
longo (o vídeo longo veio sem música), sem acelerar nem regravar,
cortada nos silêncios entre as frases. As pausas do roteiro ficam em
silêncio. Nada de música ou efeito extra: os bancos livres de direitos
(Pixabay, YouTube Audio Library) não estão acessíveis neste ambiente.
Volume final em -14 LUFS (padrão do YouTube)."""
import json
import subprocess

from timeline import AUDIO, FPS, N

SR = 48000
F = []
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
F.append(''.join(labels) + f"concat=n={len(labels)}:v=0:a=1,asetpts=PTS-STARTPTS,apad,"
         f"atrim=duration={N / FPS:.4f}[aout]")
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
