"""Transcreve trechos exatos (s). uso: trecho.py <pasta_modelo> <audio16k.wav> a:b [a:b ...]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # funciona também com python -I
from whisper_comum import carregar_wav, reconhecedor, transcrever

modelo, wav = sys.argv[1:3]
x = carregar_wav(wav)
rec = reconhecedor(modelo)
for r in sys.argv[3:]:
    a, b = map(float, r.split(':'))
    print(f'{a:7.2f}-{b:7.2f}  {transcrever(rec, x, a, b)}', flush=True)
