"""Linha do tempo do Short a partir do edl.json: cada trecho dura um número
inteiro de tempos da batida (120 BPM = 15 quadros por tempo), então todo corte
cai num tempo. Usada pela montagem, pela camada gráfica e pelo áudio."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EDL = json.load(open(os.path.join(HERE, 'edl.json')))
FPS = EDL['fps']
BEAT_F = round(FPS * 60 / EDL['bpm'])           # quadros por tempo
PLAYERS = {int(k): v for k, v in EDL['players'].items()}
END_TITLE_LINES = EDL['end_title']


def build():
    pieces, n = [], 0
    for p in EDL['pieces']:
        q = dict(p)
        q['n'] = p['beats'] * BEAT_F
        q['start'], q['end'] = n, n + q['n']
        q['kind'] = 'src' if 'src' in p else ('stinger' if 'stinger' in p else 'suspense')
        n += q['n']
        pieces.append(q)
    # primeiro trecho de cada posição: é ali que a tela de posição entra
    seen = set()
    for q in pieces:
        pos = q.get('pos')
        q['first'] = pos is not None and pos not in seen
        if pos is not None:
            seen.add(pos)
    return pieces, n


PIECES, N = build()
BYID = {q['id']: q for q in PIECES}
CAPTIONS = [(round((a - EDL['narration']['src'][0]) * FPS), round((b - EDL['narration']['src'][0]) * FPS), t)
            for a, b, t in EDL['captions']]
HOOK_END = BYID['hook']['end']
TOP3_A = BYID['top3']['start']
FIM_A = BYID['fim']['start']


def piece_at(n):
    for q in PIECES:
        if q['start'] <= n < q['end']:
            return q
    return PIECES[-1]


def pos_start(pos):
    """Quadro em que a posição entra (o primeiro trecho dela)."""
    return min(q['start'] for q in PIECES if q.get('pos') == pos)


def src_frame(q, t):
    """Quadro do Short em que aparece o instante t (s) do vídeo longo, dentro do trecho q."""
    return q['start'] + round((t - q['src']) * FPS)


if __name__ == '__main__':
    for q in PIECES:
        src = f"{q['src']:.2f}-{q['src'] + q['n'] / FPS:.2f}" if q['kind'] == 'src' else q['kind']
        print(f"{q['id']:6s} #{q.get('pos', '-')!s:4s} {q['start'] / FPS:6.2f}-{q['end'] / FPS:6.2f}s "
              f"({q['beats']:2d} tempos)  {src}")
    print(f'total {N} quadros = {N / FPS:.2f} s')
