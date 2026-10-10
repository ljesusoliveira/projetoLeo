"""Passo 2: decodifica o vídeo inteiro, apaga as legendas e recodifica (áudio copiado)."""
import numpy as np, subprocess, sys, time
from track import X0,Y0,ZW,ZH
from rmlabel import load_goals, Masker, clean
W,H,FPS=1920,1080,60
out=sys.argv[1]; crf=sys.argv[2] if len(sys.argv)>2 else "19"
mk=Masker(load_goals())
dec=subprocess.Popen(["ffmpeg","-v","error","-i","original.mp4","-f","rawvideo","-pix_fmt","bgr24","-"],stdout=subprocess.PIPE,bufsize=W*H*3*4)
enc=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
    "-i","original.mp4","-map","0:v","-map","1:a","-c:v","libx264","-preset","medium","-crf",crf,
    "-pix_fmt","yuv420p","-color_range","tv","-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709",
    "-c:a","copy","-movflags","+faststart",out],stdin=subprocess.PIPE)
n=0; touched=0; t0=time.time()
while True:
    buf=dec.stdout.read(W*H*3)
    if len(buf)<W*H*3: break
    fr=np.frombuffer(buf,np.uint8).reshape(H,W,3)
    z=fr[Y0:Y0+ZH,X0:X0+ZW]
    M=mk(n,z)
    if M is not None:
        fr=fr.copy(); fr[Y0:Y0+ZH,X0:X0+ZW]=clean(np.ascontiguousarray(z),M); touched+=1
    enc.stdin.write(fr.tobytes()); n+=1
    if n%1800==0: print(f"{n/FPS/60:.1f} de 9.8 min  ({n/(time.time()-t0):.0f} quadros/s)",flush=True)
enc.stdin.close(); enc.wait(); dec.wait()
print("quadros",n,"com legenda apagada",touched,f"em {(time.time()-t0)/60:.1f} min")
