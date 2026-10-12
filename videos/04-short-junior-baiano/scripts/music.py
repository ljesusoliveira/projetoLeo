"""Trilha original no estilo phonk para o Short (music.wav), gerada do zero
(síntese em numpy: bumbo, 808, palmas, chimbal e cowbell). Por ser criada
aqui, não usa material de terceiros, portanto não tem direitos autorais de
ninguém.

A trilha segue a linha do tempo do Short: introdução abafada no gancho,
"drop" exatamente no "SERÁ?", pausa nos congelamentos, filtro fechando no
suspense, impacto no encerramento e final em fade.
"""
import wave

import numpy as np

from timeline import BYID, FPS, N, PIECES

SR = 48000
BPM = 130
BEAT = 60 / BPM
STEP = BEAT / 4                     # semicolcheia
BAR = 16 * STEP
DUR = N / FPS
T_DROP = BYID['f1a']['start'] / FPS
T_TEASE = BYID['teaser']['start'] / FPS
T_FINAL = BYID['final']['start'] / FPS
rng = np.random.default_rng(7)


def t_of(n):
    return np.arange(n) / SR


def fft_filter(x, lo=None, hi=None, order=4):
    """Filtro de fase zero no domínio da frequência (passa-alta lo, passa-baixa hi)."""
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    H = np.ones_like(f)
    if hi:
        H /= np.sqrt(1 + (f / hi) ** (2 * order))
    if lo:
        H /= np.sqrt(1 + (lo / np.maximum(f, 1e-3)) ** (2 * order))
    if x.ndim == 2:
        H = H[:, None]
    return np.fft.irfft(X * H, n=len(x), axis=0)


def sweep_lowpass(x, cutoff_at, block=4096):
    """Passa-baixa variando no tempo (blocos com sobreposição de 50% e janela Hann)."""
    hop = block // 2
    win = np.hanning(block + 1)[:-1][:, None]
    pad = np.zeros((block, x.shape[1]))
    xp = np.vstack([pad, x, pad])
    out = np.zeros_like(xp)
    f = np.fft.rfftfreq(block, 1 / SR)[:, None]
    for i in range(0, len(xp) - block, hop):
        c = cutoff_at((i - block + hop) / SR)
        X = np.fft.rfft(xp[i:i + block] * win, axis=0)
        H = 1 / np.sqrt(1 + (f / c) ** 8)
        out[i:i + block] += np.fft.irfft(X * H, n=block, axis=0)
    return out[block:block + len(x)]


# ---------------------------------------------------------------- instrumentos
def kick():
    t = t_of(int(0.5 * SR))
    f = 46 + 120 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 6.5)
    click = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.35
    return np.tanh(1.8 * (body + click)) * 0.9


def clap():
    n = int(0.35 * SR)
    t = t_of(n)
    env = np.zeros(n)
    for d in (0.0, 0.011, 0.022):
        k = t >= d
        env[k] += np.exp(-(t[k] - d) * 190)
    env += 0.55 * np.exp(-t * 16)
    x = rng.standard_normal(n) * env
    return fft_filter(x, lo=900, hi=4200, order=2) * 0.9


def hat(open_=False):
    n = int((0.28 if open_ else 0.06) * SR)
    t = t_of(n)
    x = rng.standard_normal(n) * np.exp(-t * (11 if open_ else 70))
    return fft_filter(x, lo=7000, order=3) * (0.35 if open_ else 0.3)


def cowbell(freq, length=0.32):
    """Cowbell 808 afinado: duas ondas quadradas (razão 1,48) filtradas."""
    n = int(length * SR)
    t = t_of(n)
    sq = np.sign(np.sin(2 * np.pi * freq * t)) + 0.8 * np.sign(np.sin(2 * np.pi * freq * 1.48 * t))
    env = 0.75 * np.exp(-t * 28) + 0.25 * np.exp(-t * 6)
    x = fft_filter(sq * env, lo=freq * 0.9, hi=freq * 4.5, order=2)
    return np.tanh(1.4 * x) * 0.32


def bass808(freq, length, glide_from=None):
    n = int(length * SR)
    t = t_of(n)
    f = np.full(n, freq)
    if glide_from:
        g = np.exp(-t * 18)
        f = freq + (glide_from - freq) * g
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(1, t / 0.004) * np.exp(-t * 1.1)
    env[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    return np.tanh(2.2 * np.sin(ph) * env) * 0.55


def crash():
    n = int(2.2 * SR)
    t = t_of(n)
    x = rng.standard_normal(n) * np.exp(-t * 2.2)
    return fft_filter(x, lo=3500, order=2) * 0.28


# ---------------------------------------------------------------- arranjo
NOTE = {'A4': 440.0, 'C5': 523.25, 'D5': 587.33, 'E5': 659.26, 'F5': 698.46, 'G5': 783.99,
        'A5': 880.0, 'C6': 1046.5, 'D6': 1174.66, 'Bb4': 466.16}
ROOT = [73.42, 58.27, 65.41, 55.0]            # Ré, Si bemol, Dó, Lá (2 compassos cada)
RIFF = [  # (passo dentro de 2 compassos, nota)
    (0, 'D5'), (3, 'D5'), (6, 'F5'), (8, 'A5'), (10, 'G5'), (12, 'F5'), (14, 'D5'),
    (16, 'C5'), (19, 'C5'), (22, 'D5'), (24, 'F5'), (26, 'E5'), (28, 'C5'), (30, 'A4'),
]
KICK = [0, 6, 10]
CLAP = [4, 12]

L = int(DUR * SR) + SR
stems = {k: np.zeros(L) for k in ('kick', 'clap', 'hat', 'bell', 'bass', 'fx')}


def put(stem, x, at, gain=1.0):
    i = int(round(at * SR))
    if i >= L or i + len(x) <= 0:
        return
    a, b = max(0, -i), min(len(x), L - i)
    stems[stem][i + a:i + b] += x[a:b] * gain


K, C = kick(), clap()
H, HO = hat(), hat(True)
bells = {k: cowbell(v) for k, v in NOTE.items()}
first = int(np.floor((0 - T_DROP) / BAR)) - 1
last = int(np.ceil((DUR - T_DROP) / BAR)) + 1
prev_root = None
for b in range(first, last):
    t0 = T_DROP + b * BAR
    intro = t0 < T_DROP - 1e-6
    tease = t0 >= T_TEASE - BAR + 1e-6 and t0 < T_FINAL - 1e-6
    outro = t0 >= T_FINAL - 1e-6
    root = ROOT[(b // 2) % 4]
    section = (b // 8) % 3          # variação a cada 8 compassos
    # cowbell (toca em tudo; dobra a oitava no meio)
    for s, nm in RIFF:
        if (s >= 16) != (b % 2 == 1):
            continue
        at = t0 + (s % 16) * STEP
        put('bell', bells[nm], at, 0.8 if not outro else 0.6)
        if section == 1 and not intro:
            put('bell', cowbell(NOTE[nm] * 2), at, 0.25)
    if intro:
        continue
    # bateria
    if not tease:
        kicks = KICK + ([14] if b % 4 == 3 else []) + ([3] if section == 2 else [])
        for s in kicks:
            put('kick', K, t0 + s * STEP)
        for s in CLAP:
            put('clap', C, t0 + s * STEP)
        hs = range(0, 16, 1 if section >= 1 else 2)
        for s in hs:
            v = 1.0 if s % 4 == 2 else 0.6
            put('hat', H, t0 + s * STEP, v)
        if b % 4 == 3:  # virada de chimbal no fim de cada 4 compassos
            for j in range(6):
                put('hat', H, t0 + (12 + j * 0.667) * STEP, 0.8)
        put('hat', HO, t0 + 14 * STEP, 0.6)
    # 808
    for s in (KICK if not tease else [0]):
        ln = (16 - s) * STEP if tease else (min([k for k in KICK + [16] if k > s]) - s) * STEP
        glide = prev_root * 1.5 if (s == 0 and prev_root and prev_root != root) else None
        put('bass', bass808(root, ln, glide), t0 + s * STEP)
    prev_root = root

# impacto do encerramento
put('kick', K, T_FINAL, 1.2)
put('bass', bass808(ROOT[0], 2.6), T_FINAL, 1.1)
put('fx', crash(), T_FINAL)
# subida (ruído crescendo) na entrada do drop
n = int(1.6 * SR)
sw = rng.standard_normal(n) * np.linspace(0, 1, n) ** 2
put('fx', fft_filter(sw, lo=1500, hi=9000, order=2) * 0.35, T_DROP - 1.6)

# ---------------------------------------------------------------- mixagem
mix = (stems['kick'] * 0.95 + stems['clap'] * 0.55 + stems['hat'] * 0.5 + stems['bell'] * 0.75
       + stems['fx'])
# o 808 "respira" com o bumbo (sidechain)
env = np.convolve(np.abs(stems['kick']), np.ones(int(0.01 * SR)) / int(0.01 * SR), mode='same')
duck = 1 - 0.55 * np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
mix += stems['bass'] * duck
stereo = np.stack([mix, mix], axis=1)
# cowbell um pouco aberto no estéreo
d = int(0.012 * SR)
stereo[d:, 1] += stems['bell'][:-d] * 0.18
stereo[:, 0] += stems['bell'] * 0.18


def cutoff(t):
    if t < T_DROP:                       # introdução abafada abrindo até o drop
        x = max(0.0, t / T_DROP)
        return 500 + 2500 * x ** 2
    if T_TEASE <= t < T_FINAL:          # suspense: filtro fechando
        x = (t - T_TEASE) / (T_FINAL - T_TEASE)
        return 16000 * (1 - x) ** 3 + 300
    return 16000


stereo = sweep_lowpass(stereo, cutoff)
# pausa nos congelamentos (o impacto fica sozinho)
gain = np.ones(L)
for q in PIECES:
    if q['kind'] == 'freeze' and q['id'] not in ('teaser', 'final'):
        a, b = int(q['start'] / FPS * SR), int(q['end'] / FPS * SR)
        r = int(0.02 * SR)
        gain[a:b] = 0
        gain[a - r:a] = np.linspace(1, 0, r)
        gain[b:b + r] = np.linspace(0, 1, r)
stereo *= gain[:, None]
stereo = stereo[:int(DUR * SR)]
fo = int(1.6 * SR)
stereo[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
stereo = np.tanh(stereo * 0.9) / np.tanh(0.9)
stereo *= 0.89 / np.abs(stereo).max()
with wave.open('music.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype('<i2').tobytes())
print(f'music.wav ok ({len(stereo) / SR:.2f} s, {BPM} BPM, drop em {T_DROP:.2f} s)')
