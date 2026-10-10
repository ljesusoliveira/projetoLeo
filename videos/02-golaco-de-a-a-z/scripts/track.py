"""Passo 1: acha a posição da legenda de cada gol em todos os quadros (60 fps).
Gera masks.npz com, por quadro: dx, dy, score e o índice do gol."""
import cv2, numpy as np, subprocess, json, sys
X0,Y0,X1,Y1=0,830,1000,1010            # zona de busca (inclui deslizamento)
ZW,ZH=X1-X0,Y1-Y0
FPS=60
seg=json.load(open('segments.json'))['gols']
REF={'A':10.6,'B':40.5,'C':62,'D':82,'E':110,'F':135.6,'G':163,'H':188.8,'I':210,'J':236,'K':260,'L':280,
'M':302,'N':327.7,'O':350,'P':369.7,'Q':391.6,'R':413.4,'S':433.5,'T':450.7,'U':470,'V':487,'W':505.5,
'X':525.4,'Y':544.6,'Z':565.7}

def zone_at(t):
    raw=subprocess.run(["ffmpeg","-v","error","-ss",f"{t:.3f}","-i","original.mp4","-frames:v","1",
        "-vf",f"crop={ZW}:{ZH}:{X0}:{Y0}","-f","rawvideo","-pix_fmt","bgr24","-"],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(ZH,ZW,3).copy()

def textpix(z):
    b,g,r=[z[...,i].astype(int) for i in range(3)]
    return ((r>185)&(g>185)&(b>170)) | ((r>180)&(g>160)&(b<120))

def feat(z):  # canal mínimo: alto no texto branco, baixo na grama
    return z.min(axis=2).astype(np.float32)

def label_box(tp):
    """Caixa da legenda: maior bloco de linhas com bastante texto (ignora linhas do campo)."""
    rows=np.where(tp.sum(1)>40)[0]
    if len(rows)==0: return None
    groups=np.split(rows,np.where(np.diff(rows)>18)[0]+1)
    g=max(groups,key=lambda a:tp[a].sum())
    y0,y1=g.min(),g.max()
    cols=np.where(tp[y0:y1+1].sum(0)>2)[0]
    cg=np.split(cols,np.where(np.diff(cols)>40)[0]+1)
    c=max(cg,key=len)
    return c.min(),y0,c.max(),y1

# gols em que o quadro de referência é fixado à mão (fundo claro engana a escolha automática)
EXACT={'U':466.0}

def build_template(t,lo,hi,exact=None):
    # escolhe o quadro mais limpo perto de t (menos pixels claros no fundo)
    cands=[exact] if exact else [c for c in np.arange(t-4.2,t+4.3,0.7) if lo+1.5<c<hi-1.5]
    best=None
    for c in cands:
        z=zone_at(c); n=int(textpix(z).sum())
        if n>6000 and (best is None or n<best[0]): best=(n,c,z)
    t=best[1]
    zs=[zone_at(t+d) for d in (-0.6,-0.3,0.3,0.6)]; zs.insert(2,best[2])
    ref=zs[2]
    x0,y0,x1,y1=label_box(textpix(ref))
    pad=14
    bx0,by0,bx1,by1=max(x0-pad,0),max(y0-pad,0),min(x1+pad,ZW),min(y1+pad,ZH)
    T=feat(ref)[by0:by1,bx0:bx1]
    # voto entre quadros alinhados para tirar o fundo
    votes=np.zeros((by1-by0,bx1-bx0),np.int32)
    for z in zs:
        r=cv2.matchTemplate(feat(z),T,cv2.TM_CCOEFF_NORMED)
        _,_,_,(mx,my)=cv2.minMaxLoc(r)
        votes+=textpix(z)[my:my+by1-by0,mx:mx+bx1-bx0]
    txt=(votes>=4).astype(np.uint8)
    # contorno escuro colado ao texto
    near=cv2.dilate(txt,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(25,25)))
    dark=(ref[by0:by1,bx0:bx1].max(2)<80)&(near>0)
    m=(txt|dark).astype(np.uint8)*255
    m=cv2.dilate(m,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9)))
    print(f"  modelo em {t:.1f}s caixa {(bx0,by0,bx1,by1)} px {best[0]}",flush=True)
    return dict(T=T,mask=m,txt=txt,box=(bx0,by0,bx1,by1),t=t)

def run(letters):
    out={}
    for s in seg:
        L=s['letra']
        if L not in letters: continue
        tm=build_template(REF[L],s['inicio'],s['fim'],EXACT.get(L))
        bx0,by0,bx1,by1=tm['box']
        f0=int(round(s['inicio']*FPS)); f1=int(round(s['fim']*FPS))
        p=subprocess.Popen(["ffmpeg","-v","error","-ss",f"{s['inicio']:.3f}","-i","original.mp4","-frames:v",str(f1-f0),
            "-vf",f"crop={ZW}:{ZH}:{X0}:{Y0}","-f","rawvideo","-pix_fmt","bgr24","-"],stdout=subprocess.PIPE)
        res=[]
        while True:
            buf=p.stdout.read(ZW*ZH*3)
            if len(buf)<ZW*ZH*3: break
            z=np.frombuffer(buf,np.uint8).reshape(ZH,ZW,3)
            r=cv2.matchTemplate(feat(z),tm['T'],cv2.TM_CCOEFF_NORMED)
            _,mv,_,(mx,my)=cv2.minMaxLoc(r)
            res.append((mx-bx0,my-by0,mv))
        p.wait()
        out[L]=dict(f0=f0,res=np.array(res,np.float32),mask=tm['mask'],box=np.array(tm['box']))
        a=np.array(res)
        print(L,f"quadros {len(a)}  score>0.5: {(a[:,2]>0.5).mean():.2f}",flush=True)
    return out

if __name__=='__main__':
    letters=sys.argv[1] if len(sys.argv)>1 else "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out=run(letters)
    np.save(f"track_{letters}.npy",out,allow_pickle=True)
