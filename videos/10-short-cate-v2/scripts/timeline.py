"""Linha do tempo da versão 2 do Short a partir do edl.json (usada pela montagem, pela
camada gráfica e pelo áudio). A narração manda: os cortes de imagem e os
textos são marcados no tempo da narração do vídeo longo e convertidos aqui
para quadros do Short."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EDL = json.load(open(os.path.join(HERE, 'edl.json')))
FPS = EDL['fps']
TITLE = EDL['title']
END_TITLE_LINES = EDL['end_title']


def build_audio():
    """Trechos de áudio com início/fim em quadros do Short."""
    out, n = [], 0
    for a in EDL['audio']:
        q = dict(a)
        d = a['src'][1] - a['src'][0] if 'src' in a else a['gap']
        q['start'] = n
        q['end'] = n + round(d * FPS)
        n = q['end']
        out.append(q)
    return out, n


AUDIO, N = build_audio()
GAPS = {a['id']: a for a in AUDIO if 'gap' in a}


def F(t):
    """Quadro do Short para um instante da narração (s no vídeo longo) ou 'gap:<id>[-start]'."""
    if isinstance(t, str):
        gid = t.split(':')[1]
        if gid.endswith('-start'):
            return GAPS[gid[:-6]]['start']
        return GAPS[gid]['end']
    for a in AUDIO:
        if 'src' in a and a['src'][0] - 1e-6 <= t <= a['src'][1] + 1e-6:
            return a['start'] + round((t - a['src'][0]) * FPS)
    raise ValueError(f'instante {t} fora da narração usada')


def build_video():
    pieces, byid, n = [], {}, 0
    for p in EDL['video']:
        q = dict(p)
        end = F(p['cut'])
        assert end > n, (p['id'], n, end)
        q['start'], q['end'], q['n'] = n, end, end - n
        if 'src' in p:
            q['kind'] = 'src'
        else:
            q['kind'] = 'freeze'
            base = byid[p['of']]
            for k in ('y0', 'y1', 'cx', 'zoom_y'):
                if k in base:
                    q.setdefault(k, base[k])
            q.setdefault('zoom', [base.get('zoom', [1, 1])[1]] * 2)
        for k in ('to_sepia', 'dim'):
            if k in p:
                q[k + '_f'] = F(p[k])
        for k in ('punch', 'leak'):
            q[k + '_f'] = [F(t) for t in p.get(k, [])]
        n = end
        byid[p['id']] = q
        pieces.append(q)
    assert n == N, (n, N)
    for a, b in zip(pieces, pieces[1:]):               # chicote: sai de um trecho e entra no outro
        if b.get('whip'):
            a['whip_out'] = True
    return pieces, byid


PIECES, BYID = build_video()
CHAPTERS = [F(t) for t in EDL['chapters']]
STAMPS = [dict(s, a=F(s['from']), b=F(s['to'])) for s in EDL['stamps']]
LOWER = [dict(l, a=F(l['from']), b=F(l['to'])) for l in EDL['lower']]
CAPTIONS = [(F(a), F(b), txt) for a, b, txt in EDL['captions']]
END_A = BYID['final']['start']

if __name__ == '__main__':
    for a in AUDIO:
        print(f"audio {a['id']:4s} {a['start'] / FPS:6.2f}-{a['end'] / FPS:6.2f}s")
    for q in PIECES:
        src = f"{q['src']:.2f}-{q['src'] + q['n'] / FPS:.2f}" if q['kind'] == 'src' else 'congelado'
        print(f"{q['id']:10s} {q['start'] / FPS:6.2f}-{q['end'] / FPS:6.2f}s ({q['n'] / FPS:4.2f}s)  {src}")
    print('capítulos:', [round(c / FPS, 2) for c in CHAPTERS])
    print(f'total {N} quadros = {N / FPS:.2f} s')
