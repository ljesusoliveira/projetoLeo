"""Passo 1b: para cada gol calcula as fases da legenda.
- entrada: posição e escala quadro a quadro (o texto entra maior e deslizando)
- parada:  posição final fixa
- saída:   quando as letras somem (medido pela presença dos pixels do texto)"""
import cv2, numpy as np, subprocess, json, glob, math, sys
from track import X0,Y0,ZW,ZH,REF,EXACT,build_template,textpix,feat,zone_at
START=0.016; FPS=60
seg={s['letra']:s for s in json.load(open('segments.json'))['gols']}
tr={}
for f in glob.glob("track_*.npy"):
    tr.update({k:v for k,v in np.load(f,allow_pickle=True).item().items() if len(k)==1})
SCALES=np.arange(0.90,1.46,0.025)
def place(m,x,y):
    M=np.zeros((ZH,ZW),np.uint8); h,w=m.shape
    x,y=int(round(x)),int(round(y))
    xs,ys=max(x,0),max(y,0); xe,ye=min(x+w,ZW),min(y+h,ZH)
    if xe>xs and ye>ys: M[ys:ye,xs:xe]=m[ys-y:ye-y,xs-x:xe-x]
    return M
out={}
for L in sys.argv[1]:
    s=seg[L]; g=tr[L]; res=g['res']
    tm=build_template(REF[L],s['inicio'],s['fim'],EXACT.get(L))
    assert tuple(tm['box'])==tuple(g['box']), (L,tm['box'],g['box'])
    bx0,by0,bx1,by1=tm['box']
    good=res[:,2]>=0.9
    fdx,fdy=int(np.median(res[good,0])),int(np.median(res[good,1]))
    fx,fy=bx0+fdx,by0+fdy
    ok=np.where(res[:,2]>=0.5)[0]; first_ok=ok.min()
    near=np.abs(res[:,0]-fdx)<=1
    settle=next(i for i in range(first_ok,len(res)-10) if near[i:i+10].all())
    txt_pl=place(tm['txt'],fx,fy)>0
    e0,e1=max(first_ok-12,0),settle+6
    f0=math.ceil((s['inicio']-START)*FPS-1e-6)
    p=subprocess.Popen(["ffmpeg","-v","error","-ss",f"{s['inicio']:.3f}","-i","original.mp4","-frames:v",str(len(res)),
        "-vf",f"crop={ZW}:{ZH}:{X0}:{Y0}","-f","rawvideo","-pix_fmt","bgr24","-"],stdout=subprocess.PIPE)
    pres=[]; entry={}; i=0
    T=tm['T']
    while True:
        buf=p.stdout.read(ZW*ZH*3)
        if len(buf)<ZW*ZH*3: break
        z=np.frombuffer(buf,np.uint8).reshape(ZH,ZW,3)
        pres.append(textpix(z)[txt_pl].mean())
        i+=1
    p.wait()
    pres=np.array(pres)
    # fim da legenda: 1º quadro depois de assentar em que o texto some por 20 quadros seguidos
    low=pres<0.12
    end_i=next(i for i in range(settle,len(pres)) if low[i:i+20].all() or i==len(pres)-1)-1
    extra=None
    if L=='A':   # no gol A a 2ª linha (placar) só aparece na saída
        acc=np.zeros((ZH,ZW),np.uint8)
        for t in (19.85,19.95,20.05,20.15):
            z=zone_at(t); tp=textpix(z).astype(np.uint8); tp[:fy+(by1-by0)-14]=0
            acc|=tp
        acc=cv2.morphologyEx(acc,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
        extra=cv2.dilate(acc,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)))*255
    out[L]=dict(f0=f0,n=len(res),final=(fx,fy),mask=tm['mask'],box=tm['box'],first_ok=first_ok,settle=settle,
                end_i=end_i,entry=entry,pres=pres,extra=extra)
    print(f"{L}: entra {first_ok} assenta {settle} ({(settle-first_ok)/60:.2f}s) some {end_i}/{len(res)} = {s['inicio']+end_i/60:.2f}s",flush=True)
np.save(f"phases_{sys.argv[1]}.npy",out,allow_pickle=True)
