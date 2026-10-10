"""Linha do tempo do Short a partir do edl.json (usada pela montagem, pela
camada gráfica e pelo áudio)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EDL = json.load(open(os.path.join(HERE, 'edl.json')))
FPS = EDL['fps']


def build():
    pieces, byid, n = [], {}, 0
    for p in EDL['pieces']:
        q = dict(p)
        if 'src' in p:
            q['kind'] = 'src'
            q['n'] = round((p['src'][1] - p['src'][0]) * FPS)
        elif 'freeze' in p:
            q['kind'] = 'freeze'
            q['n'] = round(p['freeze'] * FPS)
        else:
            q['kind'] = 'rewind'
            q['n'] = round(p['rewind'] * FPS)
        if 'of' in p:  # congelamento/rebobinada herdam o enquadramento do trecho anterior
            base = byid[p['of']]
            q['y0'], q['y1'] = base['y0'], base['y1']
            q['cx'] = [[0, base['cx'][-1][1]]]
        q['start'], q['end'] = n, n + q['n']
        n += q['n']
        byid[p['id']] = q
        pieces.append(q)
    # grupos de um mesmo gol (lance + comemoração), para legenda e barra de progresso
    groups = []
    for q in pieces:
        if 'cont' in q:
            groups[-1]['end'] = q['end']
        elif q['id'] in ('gancho-freeze', 'gancho-b', 'suspense'):
            groups[-1]['end'] = q['end']
        else:
            groups.append(dict(id=q['id'], start=q['start'], end=q['end'],
                               name=q.get('name'), tag=q.get('tag')))
    return pieces, byid, groups, n


PIECES, BYID, GROUPS, N = build()

if __name__ == '__main__':
    for q in PIECES:
        print(f"{q['id']:16s} {q['kind']:7s} {q['start'] / FPS:6.2f}-{q['end'] / FPS:6.2f}s")
    print('grupos:', [(g['id'], round(g['start'] / FPS, 2)) for g in GROUPS])
    print(f'total {N} quadros = {N / FPS:.2f} s')
