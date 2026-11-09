"""Partes comuns das ferramentas de transcrição (Whisper via sherpa-onnx, sem GPU).
O modelo fica numa pasta como .../sherpa-onnx-whisper-large-v3 (ver instalar.sh)."""
import glob
import os
import wave

import numpy as np


def carregar_wav(path):
    """WAV 16 kHz mono -> float32."""
    w = wave.open(path)
    assert w.getframerate() == 16000 and w.getnchannels() == 1, 'use WAV 16 kHz mono'
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def reconhecedor(pasta_modelo, threads=4):
    import sherpa_onnx
    def achar(sufixo):
        a = sorted(glob.glob(os.path.join(pasta_modelo, f'*-{sufixo}')))
        return a[0]
    enc = achar('encoder.int8.onnx')
    dec = achar('decoder.int8.onnx')
    tok = achar('tokens.txt')
    return sherpa_onnx.OfflineRecognizer.from_whisper(encoder=enc, decoder=dec, tokens=tok, language='pt',
                                                     task='transcribe', num_threads=threads, tail_paddings=800)


def transcrever(rec, x, a, b):
    s = rec.create_stream()
    s.accept_waveform(16000, x[int(a * 16000):int(b * 16000)])
    rec.decode_stream(s)
    return s.result.text.strip()
