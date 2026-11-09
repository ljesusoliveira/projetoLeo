"""Energia da voz em dB a cada 20 ms (para ver pausas e o fim exato de uma palavra).
uso: energia.py <audio16k_passa_banda.wav> a:b [a:b ...]"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # funciona também com python -I
from whisper_comum import carregar_wav

x = carregar_wav(sys.argv[1])
for r in sys.argv[2:]:
    a, b = map(float, r.split(':'))
    print(f'[{r}]', ' '.join(f'{t:.2f}:{20 * np.log10(np.sqrt(np.mean(x[int(t * 16000):int((t + 0.02) * 16000)] ** 2)) + 1e-6):.0f}'
                             for t in np.arange(a, b, 0.02)))
