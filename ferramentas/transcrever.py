"""Transcreve a narração inteira: o VAD (silero) separa as falas nas pausas e o Whisper
transcreve cada uma. Imprime "início-fim  texto" e salva em JSON.
uso: transcrever.py <pasta_modelo> <silero_vad.onnx> <audio16k.wav> <saida.json>"""
import json
import os
import sys

import numpy as np
import sherpa_onnx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # funciona também com python -I
from whisper_comum import carregar_wav, reconhecedor, transcrever

modelo, vad_path, wav, saida = sys.argv[1:5]
x = carregar_wav(wav)
cfg = sherpa_onnx.VadModelConfig()
cfg.silero_vad.model = vad_path
cfg.silero_vad.threshold = 0.5
cfg.silero_vad.min_silence_duration = 0.08
cfg.silero_vad.min_speech_duration = 0.2
cfg.silero_vad.max_speech_duration = 6
cfg.sample_rate = 16000
vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
segs = []
win = cfg.silero_vad.window_size
for i in range(0, len(x), win):
    vad.accept_waveform(x[i:i + win])
    while not vad.empty():
        segs.append((vad.front.start / 16000, (vad.front.start + len(vad.front.samples)) / 16000))
        vad.pop()
vad.flush()
while not vad.empty():
    segs.append((vad.front.start / 16000, (vad.front.start + len(vad.front.samples)) / 16000))
    vad.pop()
rec = reconhecedor(modelo)
res = []
for a, b in segs:
    t = transcrever(rec, x, a, b)
    res.append({'start': round(a, 2), 'end': round(b, 2), 'text': t})
    print(f'{a:7.2f}-{b:7.2f}  {t}', flush=True)
json.dump(res, open(saida, 'w'), ensure_ascii=False, indent=1)
