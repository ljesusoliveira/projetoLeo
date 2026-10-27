"""Remoção da caixa amarela da legenda.
A caixa é opaca: o que está atrás dela não existe no próprio quadro. Então:
 1. A imagem real é copiada de quadros vizinhos (até 2 s antes ou depois) em
    que aquele ponto não estava coberto: no intervalo entre palavras a legenda
    some, e palavras curtas cobrem menos. O quadro vizinho é alinhado antes
    (compensa o zoom lento das fotos e pequenos movimentos) e só é usado se a
    região em volta da caixa bater com o quadro atual.
 2. Fotos que deslizam ou dão zoom rápido: o quadro sem legenda é alinhado inteiro,
    por pontos em comum (ORB).
 3. Se a caixa inteira não bate (jogadores andando), tenta faixas estreitas,
    cada uma com o seu próprio anel.
 4. O que sobrar é refeito a partir da imagem em volta (inpaint suavizado
    com grão)."""
import cv2
import numpy as np

W, H, FPS = 1920, 1080, 30
PAD = 6                          # margem em volta da caixa (halo amarelado da compressão vai até ~5 px)
BY0, BY1 = 800, 1030             # faixa trabalhada (a caixa fica em ~880..988)
RING = 14                        # anel em volta da caixa usado para comparar quadros
REACH = 60                       # quadros vizinhos consultados (2 s para cada lado)
ROI_X = 160                      # contexto lateral usado para alinhar quadros
ROI_Y1 = 1010                    # abaixo disso começa a moldura da TV (fixa): fica fora do alinhamento
MAX_ALIGN = 6                    # tentativas de alinhamento por quadro
STRIP = 40                       # largura das faixas da 2ª passada
SX0, SX1, SY0, SY1 = 90, 1830, 60, 1005   # tela dentro da moldura de TV (a moldura não se mexe)
FEAT_TRIES = 2                   # quadros sem legenda alinhados por pontos (fotos que deslizam)


def rect(box, pad):
    x0, y0, x1, y1 = box
    return max(y0 - pad, BY0) - BY0, min(y1 + pad + 1, BY1) - BY0, max(x0 - pad, 0), min(x1 + pad + 1, W)


def cover(box, pad):
    m = np.zeros((BY1 - BY0, W), bool)
    if box is not None:
        a, b, c, d = rect(box, pad)
        m[a:b, c:d] = True
    return m


def match(a, b, ring, tol=1.0):
    if ring.sum() < 500:
        return False
    d = np.abs(a[ring].astype(np.int16) - b[ring].astype(np.int16)).mean(1)
    return d.mean() < 3.0 * tol and np.percentile(d, 95) < 11 * tol


def align(band, other, valid, roi):
    """Alinha `other` a `band` dentro do recorte roi (y0, y1, x0, x1) com ECC afim,
    usando só os pontos válidos. Devolve o recorte de `other` alinhado, ou None."""
    y0, y1, x0, x1 = roi
    g1 = cv2.cvtColor(band[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(other[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    s1 = cv2.resize(g1, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA).astype(np.float32)
    s2 = cv2.resize(g2, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA).astype(np.float32)
    vm = cv2.resize(valid[y0:y1, x0:x1].astype(np.uint8) * 255, (s1.shape[1], s1.shape[0]),
                    interpolation=cv2.INTER_NEAREST)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        cv2.findTransformECC(s1, s2, warp, cv2.MOTION_AFFINE,
                             (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 1e-5), vm, 3)
    except cv2.error:
        return None
    warp[:, 2] *= 2.0                                   # translação de volta à resolução cheia
    return cv2.warpAffine(other[y0:y1, x0:x1], warp, (x1 - x0, y1 - y0),
                          flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)


_orb = None
DEBUG = False


def align_full(fn, fm, box):
    """Alinha o quadro inteiro fm ao fn por pontos (ORB) com uma transformação de semelhança
    (deslocamento, zoom e giro). Serve para fotos que deslizam ou dão zoom rápido, onde o
    alinhamento só em volta da caixa não alcança. Devolve (faixa alinhada, máscara válida) ou None."""
    global _orb
    if _orb is None:
        _orb = cv2.ORB_create(4000)
    g1 = cv2.cvtColor(cv2.resize(fn, (W // 2, H // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(cv2.resize(fm, (W // 2, H // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    mk = np.zeros((H // 2, W // 2), np.uint8)
    mk[SY0 // 2:SY1 // 2, SX0 // 2:SX1 // 2] = 255
    for cy in (SY0 // 2, SY1 // 2 - 60):                 # cantos arredondados da moldura
        for cx in (SX0 // 2, SX1 // 2 - 60):
            mk[cy:cy + 60, cx:cx + 60] = 0
    mk[(box[1] - PAD) // 2 - 4:(box[3] + PAD) // 2 + 4, (box[0] - PAD) // 2 - 4:(box[2] + PAD) // 2 + 4] = 0
    k1, d1 = _orb.detectAndCompute(g1, mk)
    k2, d2 = _orb.detectAndCompute(g2, mk)
    if d1 is None or d2 is None or len(k1) < 30 or len(k2) < 30:
        return None
    ms = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(d1, d2)
    if len(ms) < 30:
        return None
    p1 = np.float32([k1[x.queryIdx].pt for x in ms])
    p2 = np.float32([k2[x.trainIdx].pt for x in ms])
    A, inl = cv2.estimateAffinePartial2D(p2, p1, method=cv2.RANSAC, ransacReprojThreshold=1.5,
                                         maxIters=3000, confidence=0.995)
    if A is None or inl.sum() < 25:
        return None
    # texto fixo por cima de imagem que se mexe (legendas das próprias filmagens): o alinhamento
    # seguiria o fundo e o texto sairia dobrado. Nesse caso não usa.
    err = np.abs(p2 @ A[:, :2].T + A[:, 2] - p1).max(1)
    still = int(((np.abs(p1 - p2).max(1) < 1.0) & (err > 2.5)).sum())   # parados que não seguem o movimento
    if DEBUG:
        print('orb', int(inl.sum()), still, np.round(A, 3).tolist(), flush=True)
    if still > max(10, 0.2 * int(inl.sum())):
        return None
    A[:, 2] *= 2.0                                       # de volta à resolução cheia
    A[1, 2] -= BY0                                       # saída só com as linhas da faixa
    warped = cv2.warpAffine(fm, A, (W, BY1 - BY0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    scr = np.zeros((H, W), np.uint8)
    scr[SY0:SY1, SX0:SX1] = 1                            # só vale o que veio de dentro da tela
    valid = cv2.warpAffine(scr, A, (W, BY1 - BY0), flags=cv2.INTER_NEAREST, borderValue=0).astype(bool)
    return warped, valid


def clean_band(n, bands, boxes, full=None):
    """bands: dict quadro -> faixa BGR (BY0..BY1); boxes: array de caixas;
    full: função quadro -> imagem inteira (opcional, para o alinhamento por pontos).
    Devolve a faixa do quadro n sem a caixa (ou None se não há legenda)."""
    b = boxes[n]
    if b[0] < 0:
        return None
    box = tuple(int(v) for v in b)
    band = bands[n]
    hole = cover(box, PAD)
    a, bb, c, d = rect(box, PAD + RING)
    ring_all = np.zeros_like(hole)
    ring_all[a:bb, c:d] = True
    ring_all &= ~hole
    roi = (0, ROI_Y1 - BY0, max(box[0] - ROI_X, 0), min(box[2] + ROI_X, W))
    out = band.copy()
    left = hole.copy()
    # candidatos: primeiro os quadros sem legenda (descobrem tudo), depois os mais próximos
    cands = [m for k in range(1, REACH + 1) for m in (n - k, n + k) if m in bands]
    cands.sort(key=lambda m: (boxes[m][0] >= 0, abs(m - n)))
    tries = 0
    sources = []                     # quadros alinhados que não serviram inteiros (2ª passada)
    for m in cands:
        if not left.any():
            break
        bm = boxes[m]
        cm = cover(tuple(int(v) for v in bm), PAD + 4) if bm[0] >= 0 else np.zeros_like(hole)
        take = left & ~cm
        if not take.any():
            continue
        ring = ring_all & ~cm
        if match(band, bands[m], ring):
            out[take] = bands[m][take]
            left &= ~take
            continue
        if tries >= MAX_ALIGN:
            continue
        tries += 1
        valid = ~(hole | cm)
        al = align(band, bands[m], valid, roi)
        if al is None:
            continue
        y0, y1, x0, x1 = roi
        warped = band.copy()
        warped[y0:y1, x0:x1] = al
        # depois de alinhar, partes perto da borda do recorte podem ter vindo de fora: só usa o miolo
        inner = np.zeros_like(hole)
        inner[y0 + 8:y1 - 8, x0 + 8:x1 - 8] = True
        take &= inner
        if take.any() and match(band, warped, ring & inner):
            out[take] = warped[take]
            left &= ~take
        else:
            sources.append((warped, cm | ~inner))
    if left.sum() > 1000 and full is not None:
        # foto que desliza ou dá zoom rápido: alinha o quadro inteiro por pontos
        fn = full(n)
        for m in [m for m in cands if boxes[m][0] < 0][:FEAT_TRIES]:
            r = align_full(fn, full(m), box)
            if r is None:
                continue
            warped, valid = r
            take = left & valid
            # a reamostragem (zoom) amacia um pouco a imagem; o alinhamento por pontos já é confiável
            if take.any() and match(band, warped, ring_all & valid, tol=1.5):
                out[take] = warped[take]
                left &= ~take
            else:
                sources.append((warped, ~valid))
            if not left.any():
                break
    if left.any():
        # 2ª passada, em faixas estreitas: com jogadores andando, a caixa inteira quase nunca
        # bate com outro quadro, mas a grama de um lado ou os pés parados de outro batem.
        for m in cands:
            if not left.any():
                break
            bm = boxes[m]
            cm = cover(tuple(int(v) for v in bm), PAD + 4) if bm[0] >= 0 else np.zeros_like(hole)
            sources.append((bands[m], cm))
        for src, cm in sources:
            if not left.any():
                break
            strips_from(out, band, src, left, ring_all & ~cm, cm, box)
    if left.any():
        out = smooth_fill(out, left, ring_all)
    return out


def strips_from(out, band, src, left, ring, cm, box):
    """Copia de `src` as faixas verticais de STRIP px cujo anel (acima e abaixo da caixa) bate."""
    x0, x1 = max(box[0] - PAD, 0), min(box[2] + PAD + 1, W)
    d = np.abs(band[:, x0:x1].astype(np.int16) - src[:, x0:x1].astype(np.int16)).mean(2)
    r = ring[:, x0:x1]
    cuts = np.arange(0, x1 - x0, STRIP)
    cnt = np.add.reduceat(r.sum(0), cuts)
    tot = np.add.reduceat((d * r).sum(0), cuts)
    big = np.add.reduceat(((d > 11) & r).sum(0), cuts)
    for i, c in enumerate(cuts):
        if cnt[i] < 300 or tot[i] / cnt[i] >= 3.0 or big[i] > 0.05 * cnt[i]:
            continue
        sl = slice(x0 + c, x0 + min(c + STRIP, x1 - x0))
        take = left[:, sl] & ~cm[:, sl]
        if take.any():
            out[:, sl][take] = src[:, sl][take]
            left[:, sl] &= ~take


def smooth_fill(band, left, ring):
    """Refaz a área a partir da imagem em volta: inpaint Telea, suavizado para não
    deixar desenhos de losango, com um grão leve igual ao da imagem ao redor."""
    m8 = left.astype(np.uint8) * 255
    out = cv2.inpaint(band, m8, 9, cv2.INPAINT_TELEA).astype(np.float32)
    soft = cv2.GaussianBlur(out, (0, 0), 3.5)
    al = cv2.GaussianBlur(left.astype(np.float32), (0, 0), 2.0)[..., None] * left[..., None]
    out = out * (1 - al) + soft * al
    # grão: mesmo nível de ruído fino do anel em volta
    hp = band.astype(np.float32) - cv2.GaussianBlur(band.astype(np.float32), (0, 0), 1.5)
    sd = float(hp[ring].std()) if ring.any() else 0.0
    rng = np.random.default_rng(int(band[ring][:64].sum()) if ring.any() else 0)
    grain = rng.normal(0, min(sd, 6.0), left.shape).astype(np.float32)[..., None]
    out[left] += grain[left]
    return np.clip(out, 0, 255).astype(np.uint8)
