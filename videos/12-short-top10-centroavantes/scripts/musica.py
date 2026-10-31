"""Batida original do Short (sintetizada aqui, nota por nota: sem nenhuma
amostra nem música de terceiros, então não tem direito autoral).

Estilo trailer de esporte em lá menor, 120 BPM (1 tempo = 0,5 s = 15 quadros
a 30 fps, então todo corte cai exatamente num tempo), montada em seções
medidas em tempos, uma por trecho do Short:
  hook     impacto no primeiro quadro, pad baixo (embaixo da narração) e subida
  count    bateria (bumbo, caixa, chimbal), baixo e arpejo; uma seção por
           posição, sempre começando num tempo forte; level 2 = mais cheia
  stinger  "TOP 3": para tudo, impacto e subida invertida até a volta
  top      a base cheia (palmas, chimbal em semicolcheias, acordes de metais)
  suspense tudo para: grave longo, drone e batida de coração
  end      batida final e cauda
Opções: 'fill' (virada de caixa + subida no último tempo), 'hit' (impacto e
prato no primeiro tempo, quando entra a tela de posição), 'accents' (tempos
com prato, nos cortes internos).

  python3 musica.py demo saida.wav      -> prévia de ~30 s
  python3 musica.py edl saida.wav       -> trilha do Short (seções do edl.json)
"""
import json
import os
import sys
import wave

import numpy as np

SR = 48000
BPM = 120
BEAT = 60 / BPM
RNG = np.random.default_rng(1983)

# lá menor épico: Am - F - C - G (um acorde por compasso)
CHORDS = [(220.00, 261.63, 329.63), (174.61, 220.00, 261.63), (261.63, 329.63, 392.00), (196.00, 246.94, 293.66)]
ROOTS = [55.00, 43.65, 65.41, 49.00]


def t_(d):
    return np.arange(int(d * SR)) / SR


def lowpass(x, k):
    """Passa-baixa simples (média móvel de k amostras)."""
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode='same')


def highpass(x, k):
    return x - lowpass(x, k)


def kick(vol=1.0):
    t = t_(0.5)
    f = 45 + 115 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.5)
    click = highpass(RNG.normal(0, 1, len(t)), 6) * np.exp(-t * 400) * 0.3
    knock = np.sin(2 * np.pi * 160 * t) * np.exp(-t * 35) * 0.45   # soco que aparece no celular
    return np.tanh(1.6 * (body + click + knock)) * vol


def snare(vol=1.0):
    t = t_(0.28)
    noise = lowpass(highpass(RNG.normal(0, 1, len(t)), 8), 3) * np.exp(-t * 15) * 1.4
    tone = (np.sin(2 * np.pi * 185 * t) + 0.7 * np.sin(2 * np.pi * 330 * t)) * np.exp(-t * 26) * 0.6
    return (noise + tone) * vol


def clap(vol=1.0):
    t = t_(0.3)
    env = np.zeros_like(t)
    for d in (0.0, 0.011, 0.022):
        env += (t >= d) * np.exp(-np.clip(t - d, 0, None) * 140)
    env += (t >= 0.03) * np.exp(-np.clip(t - 0.03, 0, None) * 18) * 0.6
    return highpass(lowpass(RNG.normal(0, 1, len(t)), 3), 10) * env * 0.5 * vol


def hat(vol=1.0, open_=False):
    t = t_(0.35 if open_ else 0.07)
    n = lowpass(highpass(RNG.normal(0, 1, len(t)), 3), 2)   # brilho sem chiar
    return n * np.exp(-t * (9 if open_ else 85)) * 0.16 * vol


def bass(freq, dur, vol=1.0):
    t = t_(dur)
    env = np.minimum(1, t / 0.006) * np.exp(-t * 2.2)
    # fundamental + harmônicos: o grave de verdade e uma "sombra" média que o celular reproduz
    x = (np.sin(2 * np.pi * freq * t) + 0.6 * np.sin(2 * np.pi * 2 * freq * t)
         + 0.45 * np.sin(2 * np.pi * 4 * freq * t) + 0.3 * saw(4 * freq, t) * np.exp(-t * 6))
    return np.tanh(2.2 * x) * env * 0.5 * vol


def saw(freq, t):
    return 2 * ((freq * t) % 1.0) - 1


def stab(chord, dur=0.45, vol=1.0):
    """Acorde de metais: serras levemente desafinadas, filtradas."""
    t = t_(dur)
    x = sum(saw(f * d, t) for f in chord for d in (0.997, 1.0, 1.004))
    x = lowpass(x / 9, 9)
    env = np.minimum(1, t / 0.01) * np.exp(-t * 4.5)
    return x * env * 0.5 * vol


def pluck(freq, vol=1.0):
    """Nota curta e brilhante (arpejo)."""
    t = t_(0.3)
    x = saw(freq, t) * np.exp(-t * 18) + lowpass(saw(freq, t), 6) * np.exp(-t * 7)
    return x * np.minimum(1, t / 0.003) * 0.35 * vol


def pad(chord, dur, vol=1.0):
    t = t_(dur)
    x = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t) for f in chord) / len(chord)
    env = np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.4)
    return x * env * 0.22 * vol


def riser(dur, vol=1.0):
    t = t_(dur)
    n = RNG.normal(0, 1, len(t))
    x = np.zeros_like(n)
    a = 0.0
    k = np.linspace(0.02, 0.6, len(t))                 # o filtro abre ao longo da subida
    for i in range(len(n)):
        a += k[i] * (n[i] - a)
        x[i] = a
    tone = np.sin(2 * np.pi * np.cumsum(np.linspace(180, 900, len(t))) / SR) * 0.25
    return (highpass(x, 3) * 0.5 + tone) * (t / dur) ** 2.2 * vol


def impact(dur=1.8, vol=1.0):
    t = t_(dur)
    f = 32 + 70 * np.exp(-t * 12)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
    hit = lowpass(RNG.normal(0, 1, len(t)), 6) * np.exp(-t * 9) * 0.6
    return np.tanh(1.4 * (boom + hit)) * vol


def crash(vol=1.0, dur=1.6):
    t = t_(dur)
    x = lowpass(highpass(RNG.normal(0, 1, len(t)), 3), 2) * np.exp(-t * 2.6)
    ring = sum(np.sin(2 * np.pi * f * t) for f in (3150, 4270, 5480)) * 0.04 * np.exp(-t * 3.5)
    return (x * 0.3 + ring) * vol


def reverse_cymbal(dur=1.2, vol=1.0):
    t = t_(dur)
    x = highpass(RNG.normal(0, 1, len(t)), 2) * np.exp(-t * 3.2) * 0.35
    return x[::-1] * vol


def heartbeat(vol=1.0):
    out = np.zeros(int(0.7 * SR))
    for d, v in ((0.0, 1.0), (0.22, 0.7)):
        t = t_(0.3)
        x = (np.sin(2 * np.pi * np.cumsum(55 + 40 * np.exp(-t * 25)) / SR)
             + 0.5 * np.sin(2 * np.pi * 150 * t)) * np.exp(-t * 14) * v
        i = int(d * SR)
        out[i:i + len(x)] += x
    return out * vol


def drone(dur, vol=1.0):
    t = t_(dur)
    x = np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 82.4 * t) + 0.25 * np.sin(2 * np.pi * 110.3 * t)
    x += 0.35 * lowpass(saw(220.0, t), 12)                            # corpo médio (aparece no celular)
    x += 0.12 * np.sin(2 * np.pi * 880 * t + 3 * np.sin(2 * np.pi * 5 * t))   # nota aguda de tensão
    trem = 0.75 + 0.25 * np.sin(2 * np.pi * 0.5 * t)
    env = np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 0.3)
    return x * trem * env * 0.25 * vol


class Mix:
    def __init__(self, dur):
        self.n = int(dur * SR) + SR * 3
        self.bus = {k: np.zeros(self.n) for k in ('drums', 'bass', 'music', 'fx')}
        self.kicks = []

    def add(self, bus, x, at):
        i = int(round(at * SR))
        if i >= self.n:
            return
        j = min(self.n, i + len(x))
        self.bus[bus][i:j] += x[:j - i]

    def render(self, total):
        # o baixo e os acordes "abaixam" um pouco a cada bumbo (bombeia junto com a batida)
        duck = np.ones(self.n)
        tt = t_(0.25)
        curve = 1 - 0.55 * np.exp(-tt * 14)
        for at in self.kicks:
            i = int(at * SR)
            j = min(self.n, i + len(curve))
            duck[i:j] = np.minimum(duck[i:j], curve[:j - i])
        x = (self.bus['drums'] * 0.9 + self.bus['bass'] * duck * 0.8 + self.bus['music'] * duck * 0.75
             + self.bus['fx'] * 0.9)
        x = np.tanh(x * 0.9)
        n = int(total * SR)
        x = x[:n]
        fade = int(0.05 * SR)
        x[-fade:] *= np.linspace(1, 0, fade)
        return x


def section(m, s, t0):
    """Escreve uma seção a partir de t0 (s). Devolve o fim da seção."""
    kind, beats = s['type'], s['beats']
    dur = beats * BEAT
    t1 = t0 + dur
    bar0 = s.get('bar', 0)
    if kind == 'hook':
        m.add('fx', impact(2.2, s.get('impact', 0.9)), t0)
        m.add('music', pad(CHORDS[0], dur + 0.3, s.get('pad', 1.0)), t0)
        m.add('fx', riser(min(dur, 3.0), 0.8), t1 - min(dur, 3.0))
        m.add('fx', reverse_cymbal(min(1.2, dur), 0.8), t1 - min(1.2, dur))
    elif kind == 'stinger':
        m.add('fx', impact(2.4, 1.0), t0)
        m.add('drums', crash(0.9), t0)
        m.add('music', pad(CHORDS[2], dur + 0.2, 0.8), t0)
        m.add('fx', reverse_cymbal(dur, 0.9), t0)
    elif kind in ('count', 'top'):
        full = kind == 'top'
        lvl2 = full or s.get('level', 1) >= 2
        for e in range(beats * 2):                     # colcheias
            at = t0 + e * BEAT / 2
            beat_in_bar = (e // 2) % 4
            bar = bar0 + e // 8
            chord = CHORDS[bar % 4]
            if e % 2 == 0:
                if beat_in_bar in (0, 2):
                    m.add('drums', kick(1.0), at)
                    m.kicks.append(at)
                if beat_in_bar in (1, 3):
                    m.add('drums', snare(0.9), at)
                    if lvl2:
                        m.add('drums', clap(0.8 if not full else 0.9), at)
            elif full and e % 8 == 5:                  # bumbo extra no contratempo
                m.add('drums', kick(0.8), at)
                m.kicks.append(at)
            m.add('drums', hat(0.9 if e % 2 else 0.6), at)
            if lvl2:
                m.add('drums', hat(0.45), at + BEAT / 4)
                if e % 4 == 3:
                    m.add('drums', hat(0.5, open_=True), at)
            if e % 8 in (0, 3, 4, 6) or (full and e % 8 == 7):
                m.add('bass', bass(ROOTS[bar % 4], BEAT * 0.48), at)
            arp = [chord[0] * 2, chord[2] * 2, chord[1] * 2, chord[2] * 2]
            m.add('music', pluck(arp[e % 4], 0.8 if full else 0.6), at)
            if e % 8 == 0:
                m.add('music', pad(chord, 8 * BEAT / 2 + 0.2, 0.7 if full else 0.55), at)
                if full:
                    m.add('music', stab(chord, 0.5, 0.9), at)
            if full and e % 8 == 3:
                m.add('music', stab(chord, 0.3, 0.6), at)
        if s.get('hit'):                               # entra a tela de posição
            m.add('fx', impact(1.4, 0.55 if not full else 0.75), t0)
            m.add('drums', crash(0.7), t0)
        for b in s.get('accents', []):                 # cortes internos
            m.add('drums', crash(0.45, 1.0), t0 + b * BEAT)
        if s.get('fill'):                              # virada no último tempo
            for k in range(4):
                m.add('drums', snare(0.35 + 0.18 * k), t1 - BEAT + k * BEAT / 4)
            m.add('fx', riser(min(2.0, dur), 0.55), t1 - min(2.0, dur))
    elif kind == 'suspense':
        m.add('fx', impact(2.6, 1.0), t0)
        m.add('drums', crash(0.6, 2.4), t0)
        m.add('music', drone(dur, 1.0), t0)
        k = 0.45
        while k < dur - 0.6:
            m.add('fx', heartbeat(0.8), t0 + k)
            k += 0.9
        for at in s.get('hits', []):                   # impactos extras (o "?" na tela)
            m.add('fx', impact(1.6, 0.8), t0 + at)
    elif kind == 'end':
        m.add('fx', impact(2.0, 0.9), t0)
        m.add('music', pad(CHORDS[0], dur, 0.6), t0)
    return t1


def build(sections, out, total=None):
    total = total or sum(s['beats'] for s in sections) * BEAT
    m = Mix(total)
    t = 0.0
    for s in sections:
        t = section(m, s, t)
    x = m.render(total)
    pcm = np.clip(x / max(1e-6, np.abs(x).max()) * 0.89, -1, 1)
    st = np.stack([pcm, pcm], 1)
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    return total


DEMO = [
    {'type': 'hook', 'beats': 6},
    {'type': 'count', 'beats': 8, 'bar': 0},
    {'type': 'count', 'beats': 8, 'bar': 2},
    {'type': 'count', 'beats': 7, 'bar': 0},
    {'type': 'count', 'beats': 7, 'bar': 2, 'fill': True},
    {'type': 'top', 'beats': 16, 'bar': 0},
    {'type': 'suspense', 'beats': 8, 'hits': [1.8]},
    {'type': 'end', 'beats': 4},
]

if __name__ == '__main__':
    if sys.argv[1] == 'demo':
        print(f'{build(DEMO, sys.argv[2]):.2f} s')
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        edl = json.load(open(os.path.join(here, 'edl.json')))
        print(f"{build(edl['music'], sys.argv[2]):.2f} s")
