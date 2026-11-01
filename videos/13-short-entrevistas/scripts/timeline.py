"""Linha do tempo do Short das entrevistas a partir do edl.json: as entrevistas
inteiras, em ordem, e depois o final (lampejos dos outros jogadores sobre a
narração de abertura do vídeo longo e o encerramento). Usada pela montagem,
pela camada gráfica e pelo áudio."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EDL = json.load(open(os.path.join(HERE, 'edl.json')))
FPS = EDL['fps']
TITLE = EDL['title']
END_TITLE_LINES = EDL['end_title']


def build():
    pieces, n = [], 0
    for c in EDL['clips']:
        q = dict(c, kind='clip', n=c['frames'], start=n, end=n + c['frames'])
        n = q['end']
        pieces.append(q)
    o = EDL['outro']
    t0 = o['narration'][0]
    outro_a = n
    for i, f in enumerate(o['flashes']):
        a = outro_a + round((f['from'] - t0) * FPS)
        b = outro_a + round((f['to'] - t0) * FPS)
        pieces.append(dict(f, id=f'flash{i}', kind='flash', n=b - a, start=a, end=b))
        n = b
    narr_n = round((o['narration'][1] - t0) * FPS)
    end_b = outro_a + narr_n + o['tail']
    pieces.append(dict(id='end', kind='end', n=end_b - n, start=n, end=end_b))
    return pieces, end_b, outro_a, narr_n


PIECES, N, OUTRO_A, NARR_N = build()
BYID = {q['id']: q for q in PIECES}
CLIPS = [q for q in PIECES if q['kind'] == 'clip']
END_A = BYID['end']['start']


def to_frame(q, t):
    """Quadro do Short em que aparece o instante t (s) do vídeo longo, dentro do trecho q."""
    return q['start'] + round((t - q['src']) * FPS)


STICKERS = [dict(s, a=to_frame(q, s['from']), b=min(q['end'], to_frame(q, s['to'])))
            for q in CLIPS for s in q.get('stickers', [])]


def piece_at(n):
    for q in PIECES:
        if q['start'] <= n < q['end']:
            return q
    return PIECES[-1]


if __name__ == '__main__':
    for q in PIECES:
        src = f"{q['src']:.2f}-{q['src'] + q['n'] / FPS:.2f}" if 'src' in q else ''
        print(f"{q['id']:8s} {q['kind']:5s} {q['start'] / FPS:6.2f}-{q['end'] / FPS:6.2f}s ({q['n'] / FPS:5.2f}s)  {src}")
    print(f'total {N} quadros = {N / FPS:.2f} s')
