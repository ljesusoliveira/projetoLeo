"""Onde termina cada palavra: acha os vales de energia da voz (pausas >= 40 ms) num trecho e
transcreve o prefixo [a, vale]. Mostra quais palavras já foram ditas em cada vale; é nesses
vales que se pode cortar ou trocar a legenda.
uso: palavras.py <pasta_modelo> <audio16k.wav> <audio16k_passa_banda.wav> a:b [a:b ...]
(o passa-banda: ffmpeg -af "highpass=f=300,highpass=f=300,lowpass=f=3400")"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # funciona também com python -I
from whisper_comum import carregar_wav, reconhecedor, transcrever

modelo, wav, wbp = sys.argv[1:4]
x, y = carregar_wav(wav), carregar_wav(wbp)
e = np.array([np.sqrt(np.mean(y[i:i + 320] ** 2)) for i in range(0, len(y) - 320, 160)])
db = 20 * np.log10(e + 1e-6)
rec = reconhecedor(modelo)
for rng in sys.argv[4:]:
    a, b = map(float, rng.split(':'))
    seg = db[int(a * 100):int(b * 100)]
    ref = np.percentile(seg, 80)
    vales, i = [], 0
    while i < len(seg):
        if seg[i] < ref - 16:
            j = i
            while j < len(seg) and seg[j] < ref - 16:
                j += 1
            if j - i >= 4 and i > 15 and j < len(seg) - 15:
                vales.append(a + (i + int(np.argmin(seg[i:j]))) / 100)
            i = j
        i += 1
    print(f'== {rng}')
    for v in vales:
        print(f'  {v:7.2f}  {transcrever(rec, x, a, v)}', flush=True)
