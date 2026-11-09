"""Tempo de fim de cada palavra num trecho: transcreve prefixos [a, t] a cada 70 ms e anota
quando o número de palavras cresce (a última palavra de um prefixo costuma sair cortada,
então conta só as anteriores). Use o modelo small (rápido); o texto certo vem do large-v3.
uso: tempo_palavras.py <pasta_modelo> <audio16k.wav> <saida.json> a:b [a:b ...]"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # funciona também com python -I
from whisper_comum import carregar_wav, reconhecedor, transcrever

modelo, wav, saida = sys.argv[1:4]
x = carregar_wav(wav)
rec = reconhecedor(modelo)


def palavras(a, b):
    t = re.sub(r'\.\.\.|…', ' ', transcrever(rec, x, a, b))
    return [p for p in re.split(r'\s+', t.strip()) if re.search(r'\w', p)]


res = {}
for rng in sys.argv[4:]:
    a, b = map(float, rng.split(':'))
    final = palavras(a, b)
    fins, n_ok, t = [], 0, a + 0.25
    while t < b + 0.01:
        n = max(0, len(palavras(a, t)) - 1)
        while n_ok < min(n, len(final)):
            fins.append(round(t - 0.07, 2))
            n_ok += 1
        t += 0.07
    while len(fins) < len(final):
        fins.append(b)
    res[rng] = list(zip(final, fins))
    print(rng, ' '.join(f'{w}@{e:.2f}' for w, e in res[rng]), flush=True)
json.dump(res, open(saida, 'w'), ensure_ascii=False, indent=1)
