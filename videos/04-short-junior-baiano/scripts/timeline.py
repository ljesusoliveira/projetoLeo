"""Linha do tempo do Short a partir do edl.json (usada pela montagem, pela
camada gráfica e pelo áudio)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EDL = json.load(open(os.path.join(HERE, 'edl.json')))
FPS = EDL['fps']
TITLE = EDL['title']


def build():
    pieces, byid, n = [], {}, 0
    for p in EDL['pieces']:
        q = dict(p)
        if 'src' in p:
            q['kind'] = 'src'
            q['n'] = round((p['src'][1] - p['src'][0]) * FPS)
        else:
            q['kind'] = 'freeze'
            q['n'] = round(p['freeze'] * FPS)
            base = byid[p['of']]  # congelamento herda o enquadramento do trecho de origem
            q['y0'], q['y1'] = base['y0'], base['y1']
            q['cx'] = [[0, base['cx'][-1][1]]]
        q['start'], q['end'] = n, n + q['n']
        n += q['n']
        byid[p['id']] = q
        pieces.append(q)
    # grupos: cada falta (com congelamentos, replays e reações) vira um bloco
    # na barra de progresso; um grupo começa no gancho, em cada trecho com
    # "tag" e no suspense/encerramento
    groups = []
    for q in pieces:
        if not groups or 'tag' in q or q['id'] in ('teaser', 'final'):
            groups.append(dict(id=q['id'], start=q['start'], end=q['end'], tag=q.get('tag')))
            groups[-1]['tag_end'] = None
        else:
            groups[-1]['end'] = q['end']
        if q.get('notag') and groups[-1]['tag_end'] is None:
            groups[-1]['tag_end'] = q['start']  # etiqueta sai quando entram cartão e reação
    k = 0
    for g in groups:
        g['tag_end'] = g['tag_end'] or g['end']
        if g['tag']:
            k += 1
            g['num'] = k
    return pieces, byid, groups, n


PIECES, BYID, GROUPS, N = build()


def out_frame(pid, t):
    """Quadro do Short em que aparece o instante t (s) do vídeo longo, dentro do trecho pid."""
    q = BYID[pid]
    return q['start'] + round((t - q['src'][0]) * FPS)


if __name__ == '__main__':
    for q in PIECES:
        print(f"{q['id']:10s} {q['kind']:7s} {q['start'] / FPS:6.2f}-{q['end'] / FPS:6.2f}s")
    print('grupos:', [(g['id'], g.get('num'), round(g['start'] / FPS, 2)) for g in GROUPS])
    print(f'total {N} quadros = {N / FPS:.2f} s')
