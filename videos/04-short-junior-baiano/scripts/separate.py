"""Separa a voz (narração e entrevista) da música do vídeo longo, só nos
trechos usados no Short, com um modelo MDX-Net (UVR "Kim_Vocal_2", ONNX).
Gera voz.wav (44,1 kHz, estéreo) do tamanho do vídeo longo, com silêncio
fora dos trechos usados.
  python3 separate.py <caminho do Kim_Vocal_2.onnx>
O modelo é baixado de:
  https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/Kim_Vocal_2.onnx
"""
import subprocess
import sys
import wave

import numpy as np
import onnxruntime as ort

from timeline import PIECES

SR = 44100
N_FFT, HOP, DIM_F, DIM_T = 7680, 1024, 3072, 256
COMPENSATE = 1.009
CHUNK = HOP * (DIM_T - 1)
TRIM = N_FFT // 2
GEN = CHUNK - 2 * TRIM
WIN = np.hanning(N_FFT + 1)[:-1].astype(np.float32)
NB = N_FFT // 2 + 1


def stft(x):
    """x: (2, CHUNK) -> (1, 4, DIM_F, DIM_T) no formato do modelo (Lre, Lim, Rre, Rim)."""
    xp = np.pad(x, ((0, 0), (N_FFT // 2, N_FFT // 2)), mode='reflect')
    idx = np.arange(DIM_T)[:, None] * HOP + np.arange(N_FFT)[None, :]
    out = []
    for c in range(2):
        S = np.fft.rfft(xp[c][idx] * WIN, axis=1).T[:DIM_F]       # (DIM_F, DIM_T)
        out += [S.real, S.imag]
    return np.stack(out)[None].astype(np.float32)


def istft(spec):
    """(1, 4, DIM_F, DIM_T) -> (2, CHUNK)."""
    res = []
    for c in range(2):
        S = np.zeros((NB, DIM_T), np.complex64)
        S[:DIM_F] = spec[0, 2 * c] + 1j * spec[0, 2 * c + 1]
        frames = np.fft.irfft(S.T, n=N_FFT, axis=1) * WIN
        L = N_FFT + HOP * (DIM_T - 1)
        y = np.zeros(L, np.float32)
        wsum = np.zeros(L, np.float32)
        for t in range(DIM_T):
            y[t * HOP:t * HOP + N_FFT] += frames[t]
            wsum[t * HOP:t * HOP + N_FFT] += WIN ** 2
        y = y / np.maximum(wsum, 1e-8)
        res.append(y[N_FFT // 2:N_FFT // 2 + CHUNK])
    return np.stack(res)


def separate(sess, mix):
    """mix: (2, n) -> voz (2, n)."""
    n = mix.shape[1]
    pad = GEN + TRIM - (n % GEN)
    m = np.concatenate([np.zeros((2, TRIM), np.float32), mix, np.zeros((2, pad), np.float32)], 1)
    outs = []
    for i in range(0, m.shape[1] - 2 * TRIM - pad + GEN, GEN):
        w = m[:, i:i + CHUNK]
        if w.shape[1] < CHUNK:
            w = np.pad(w, ((0, 0), (0, CHUNK - w.shape[1])))
        pred = sess.run(None, {sess.get_inputs()[0].name: stft(w)})[0]
        outs.append(istft(pred)[:, TRIM:-TRIM])
    v = np.concatenate(outs, 1)[:, :n]
    return v * COMPENSATE


def main(model):
    sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'original.mp4', '-vn', '-ac', '2', '-ar', str(SR),
                          '-f', 'f32le', '-'], capture_output=True).stdout
    audio = np.frombuffer(raw, np.float32).reshape(-1, 2).T.copy()
    voice = np.zeros_like(audio)
    # trechos usados (com 1,5 s de margem), unidos quando se sobrepõem
    wins = sorted((max(0, q['src'][0] - 1.5), q['src'][1] + 1.5) for q in PIECES if q['kind'] == 'src')
    merged = []
    for a, b in wins:
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    for a, b in merged:
        i, j = int(a * SR), min(int(b * SR), audio.shape[1])
        voice[:, i:j] = separate(sess, audio[:, i:j])
        print(f'  voz separada {a:6.1f}-{b:6.1f} s', flush=True)
    pcm = (np.clip(voice.T, -1, 1) * 32767).astype('<i2')
    with wave.open('voz.wav', 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print('voz.wav ok')


if __name__ == '__main__':
    main(sys.argv[1])
