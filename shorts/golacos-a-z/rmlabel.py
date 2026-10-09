"""Máscara e remoção das legendas, usada na prévia e na renderização."""
import cv2, numpy as np, glob, json, math
from track import X0,Y0,ZW,ZH
FPS=60; START=0.016

def place(m,x,y):
    M=np.zeros((ZH,ZW),np.uint8); h,w=m.shape
    x,y=int(round(x)),int(round(y))
    xs,ys=max(x,0),max(y,0); xe,ye=min(x+w,ZW),min(y+h,ZH)
    if xe>xs and ye>ys: M[ys:ye,xs:xe]=m[ys-y:ye-y,xs-x:xe-x]
    return M

def hdilate(m,left,right):
    """Estende a máscara na horizontal (as letras se espalham na entrada e na saída)."""
    pad=left+right+2
    big=np.zeros((m.shape[0],m.shape[1]+2*pad),np.uint8); big[:,pad:pad+m.shape[1]]=m
    big=cv2.dilate(big,np.ones((1,left+right+1),np.uint8),anchor=(right,0))
    return big,pad

K=lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(r,r))

class Goal:
    def __init__(self,g,ph):
        self.res=g['res']; self.box=ph['box']; self.n=ph['n']; pres=ph['pres']
        self.first_ok=ph['first_ok']; self.settle=ph['settle']; self.end_i=ph['end_i']
        # a saída começa quando o texto deixa de estar inteiro
        e=self.end_i
        while e>self.settle and pres[e]<0.9: e-=1
        self.exit_start=max(e-3,self.settle)
        # a animação de saída dura ~0,3 s; não estende por causa de fundo claro depois dela
        self.end_i=min(self.end_i,self.exit_start+27)
        bx0,by0,_,_=self.box; self.bx0,self.by0=bx0,by0
        fx,fy=ph['final']; m=ph['mask']
        self.steady=place(m,fx,fy)
        ex,pad=hdilate(m,45,10); self.exit=place(ex,fx-pad,fy)
        if ph['extra'] is not None:
            self.exit|=cv2.dilate(ph['extra'],np.ones((1,56),np.uint8),anchor=(10,0))
        self.entry_m,self.entry_pad=hdilate(m,35,35)
        rows=np.where(self.steady.any(1))[0]; self.rows=(max(rows.min()-8,0),min(rows.max()+8,ZH))
        self.left=max(np.where(self.steady.any(0))[0].min()-60,0)
        pos=[]; last=None
        for i in range(self.n):
            dx,dy,s=self.res[i]
            if s>=0.4: last=(dx,dy)
            pos.append(last)
        first=next(p for p in pos if p is not None)
        self.pos=[p if p is not None else first for p in pos]
        self.w0=max(self.first_ok-12,0)
    def phase(self,i):
        if i<self.w0 or i>self.end_i+3: return None
        if i<self.settle: return 'entra'
        if i<self.exit_start: return 'parada'
        return 'sai'
    def mask(self,i,z):
        ph=self.phase(i)
        if ph is None: return None
        if ph=='parada': return self.steady
        if ph=='sai': return self.exit
        dx,dy=self.pos[i]
        M=place(self.entry_m,self.bx0+dx-self.entry_pad,self.by0+dy)
        # entrada: as duas linhas entram em tempos diferentes; detecta o texto claro na faixa da legenda
        r0,r1=self.rows; c0=self.left
        r=z[r0:r1,c0:].astype(np.int16)
        lum=r.mean(2); bg=cv2.medianBlur(lum.astype(np.uint8),31).astype(np.int16)
        sat=r.max(2)-r.min(2)
        t=(((lum-bg>14)&(sat<80))|((r[...,2]-r[...,0]>60)&(r[...,1]-r[...,0]>45)&(lum-bg>6))).astype(np.uint8)
        t=cv2.morphologyEx(t,cv2.MORPH_OPEN,K(3))
        M[r0:r1,c0:]|=cv2.dilate(t,K(17))*255
        return M

def load_goals():
    tr={}; ph={}
    for f in glob.glob("track_*.npy"): tr.update({k:v for k,v in np.load(f,allow_pickle=True).item().items() if len(k)==1})
    for f in glob.glob("phases_*.npy"): ph.update(np.load(f,allow_pickle=True).item())
    seg=json.load(open('segments.json'))['gols']
    spans=[]
    for s in seg:
        L=s['letra']; f0=math.ceil((s['inicio']-START)*FPS-1e-6)
        G=Goal(tr[L],ph[L]); G.L=L
        spans.append((f0,f0+G.n,G))
    return spans

class Masker:
    """Máscara de qualquer quadro global n (ou None)."""
    def __init__(self,spans): self.spans=spans
    def goal(self,n):
        for f0,f1,G in self.spans:
            if f0<=n<f1: return f0,G
        return None,None
    def __call__(self,n,z):
        """z = zona da legenda (BGR) do quadro n."""
        f0,G=self.goal(n)
        if G is None: return None
        return G.mask(n-f0,z)

def clean(z,M):
    return cv2.inpaint(z,M,7,cv2.INPAINT_TELEA)
