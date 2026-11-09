// Camada animada do Short do Viola, feita no Remotion e renderizada como PNG com
// transparência (um por quadro do Short). O compose.py junta essa camada por cima do
// vídeo e por baixo da legenda. Elementos:
//   vilao        carimbo "VILÃO" que cai girando sobre a imagem
//   reviravolta  "REVIRAVOLTA" entrando com desfoque de movimento
//   versus       rótulos da tela dividida (1993 PROVOCOU x 1996 VESTIU A CAMISA) e o "VS"
//   end          encerramento: VÍDEO COMPLETO NO CANAL, título, INSCREVA-SE e o link
// Os quadros de cada elemento vêm de props.json (gerado a partir do edl.json).
import React from 'react';
import {
  AbsoluteFill, Composition, continueRender, delayRender, interpolate, registerRoot,
  spring, staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';

const GOLD = '#F2C230';
const RED = '#D6182C';
const GREEN = '#0B7A3B';

const fontHandle = delayRender('fontes');
const fontes = new FontFace('Anton', `url(${staticFile('Anton-Regular.ttf')})`);
const fontes2 = new FontFace('Montserrat', `url(${staticFile('Montserrat.ttf')})`, {weight: '100 900'});
Promise.all([fontes.load(), fontes2.load()]).then(([a, b]) => {
  document.fonts.add(a);
  document.fonts.add(b);
  continueRender(fontHandle);
});

const stroke = (px, color = '#000') => ({
  WebkitTextStroke: `${px}px ${color}`, paintOrder: 'stroke fill',
  textShadow: '0 8px 18px rgba(0,0,0,.75)',
});

const inRange = (f, [a, b]) => f >= a && f < b;

const Vilao = ({k, bandY, bandH}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: k, fps, config: {damping: 9, stiffness: 220, mass: 0.7}});
  const scale = interpolate(s, [0, 1], [2.6, 1]);
  const rot = interpolate(s, [0, 1], [-28, -11]);
  const op = interpolate(k, [0, 2], [0, 1], {extrapolateRight: 'clamp'});
  const shake = k < 8 ? Math.sin(k * 3.1) * (8 - k) * 1.2 : 0;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: bandY + bandH * 0.36, display: 'flex',
      justifyContent: 'center', transform: `translateX(${shake}px)`}}>
      <div style={{transform: `scale(${scale}) rotate(${rot}deg)`, opacity: op, border: `12px solid ${RED}`,
        borderRadius: 18, padding: '6px 38px 0', color: RED, fontFamily: 'Anton', fontSize: 190,
        lineHeight: 1.05, letterSpacing: 6, background: 'rgba(255,255,255,.08)',
        boxShadow: '0 0 0 4px rgba(0,0,0,.35), 0 18px 40px rgba(0,0,0,.6)',
        textShadow: '0 0 2px rgba(0,0,0,.6)'}}>
        VILÃO
      </div>
    </div>
  );
};

const Reviravolta = ({k, n, bandY, bandH}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: k, fps, config: {damping: 14, stiffness: 160}});
  const x = interpolate(s, [0, 1], [-700, 0]);
  const blur = interpolate(s, [0, 0.8, 1], [18, 2, 0]);
  const spacing = interpolate(s, [0, 1], [40, 2]);
  const out = interpolate(k, [n - 5, n], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: bandY + bandH * 0.38, textAlign: 'center',
      transform: `translateX(${x}px)`, filter: `blur(${blur}px)`, opacity: out}}>
      <div style={{fontFamily: 'Anton', fontSize: 150, color: GOLD, letterSpacing: spacing, ...stroke(10)}}>
        REVIRAVOLTA
      </div>
    </div>
  );
};

const Tag = ({year, text, bg, k, delay, side}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: k - delay, fps, config: {damping: 12, stiffness: 180}});
  const dx = (side === 'left' ? -1 : 1) * interpolate(s, [0, 1], [320, 0]);
  return (
    <div style={{width: 540, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14,
      transform: `translateX(${dx}px)`, opacity: Math.min(1, s * 1.5)}}>
      <div style={{fontFamily: 'Montserrat', fontWeight: 800, fontSize: 46, letterSpacing: 8, color: '#000',
        background: GOLD, padding: '6px 22px', borderRadius: 8, boxShadow: '0 8px 20px rgba(0,0,0,.55)'}}>
        {year}
      </div>
      <div style={{fontFamily: 'Anton', fontSize: 64, color: '#fff', background: bg, padding: '4px 26px 0',
        borderRadius: 10, border: '4px solid #fff', boxShadow: '0 10px 24px rgba(0,0,0,.6)'}}>
        {text}
      </div>
    </div>
  );
};

const Versus = ({k, bandY, bandH}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: k - 6, fps, config: {damping: 8, stiffness: 200}});
  const pulse = 1 + (k > 20 ? 0.05 * Math.sin((k - 20) / fps * 2 * Math.PI * 1.6) : 0);
  return (
    <>
      <div style={{position: 'absolute', top: bandY + 36, left: 0, width: 1080, display: 'flex'}}>
        <Tag year="1993" text="PROVOCOU" bg={RED} k={k} delay={2} side="left" />
        <Tag year="1996" text="VESTIU A CAMISA" bg={GREEN} k={k} delay={5} side="right" />
      </div>
      <div style={{position: 'absolute', left: 540 - 95, top: bandY + bandH * 0.47 - 95, width: 190, height: 190,
        borderRadius: 95, background: '#0b0b0d', border: `8px solid ${GOLD}`, display: 'flex',
        alignItems: 'center', justifyContent: 'center', transform: `scale(${s * pulse})`,
        boxShadow: '0 0 40px rgba(242,194,48,.55), 0 14px 30px rgba(0,0,0,.7)'}}>
        <div style={{fontFamily: 'Anton', fontSize: 104, color: GOLD, marginTop: 6}}>VS</div>
      </div>
    </>
  );
};

const Pop = ({k, delay, children, style}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: k - delay, fps, config: {damping: 11, stiffness: 190}});
  return (
    <div style={{position: 'absolute', left: 0, right: 0, display: 'flex', justifyContent: 'center',
      transform: `scale(${interpolate(s, [0, 1], [1.5, 1])})`, opacity: Math.min(1, s * 2), ...style}}>
      {children}
    </div>
  );
};

const Fim = ({k, bandY, title}) => {
  const {fps} = useVideoConfig();
  const pulse = 1 + 0.04 * Math.sin(k / fps * 2 * Math.PI * 1.4);
  return (
    <>
      <Pop k={k} delay={0} style={{top: bandY + 70}}>
        <div style={{fontFamily: 'Anton', fontSize: 124, color: '#fff', ...stroke(9)}}>VÍDEO COMPLETO</div>
      </Pop>
      <Pop k={k} delay={3} style={{top: bandY + 248}}>
        <div style={{fontFamily: 'Anton', fontSize: 92, color: '#fff', background: RED, padding: '2px 40px 0',
          boxShadow: '0 12px 28px rgba(0,0,0,.65)'}}>NO CANAL</div>
      </Pop>
      <Pop k={k} delay={7} style={{top: bandY + 430, flexDirection: 'column', alignItems: 'center'}}>
        {title.map((t, i) => (
          <div key={i} style={{fontFamily: 'Anton', fontSize: 66, lineHeight: 1.12, textAlign: 'center',
            color: i === title.length - 1 ? GOLD : '#fff', ...stroke(6)}}>{t}</div>
        ))}
      </Pop>
      <Pop k={k} delay={11} style={{top: bandY + 720}}>
        <div style={{transform: `scale(${pulse})`, fontFamily: 'Anton', fontSize: 70, color: '#fff',
          background: RED, border: '6px solid #fff', borderRadius: 22, padding: '6px 46px 0',
          boxShadow: '0 12px 28px rgba(0,0,0,.65)'}}>INSCREVA-SE</div>
      </Pop>
      <Pop k={k} delay={15} style={{top: 1408}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 16, fontFamily: 'Montserrat', fontWeight: 800,
          fontSize: 34, letterSpacing: 2, color: '#fff', background: 'rgba(10,10,10,.85)',
          border: `4px solid ${GOLD}`, borderRadius: 44, padding: '14px 34px'}}>
          TOQUE NO VÍDEO RELACIONADO
          <div style={{width: 0, height: 0, borderLeft: '16px solid transparent', borderRight: '16px solid transparent',
            borderTop: `22px solid ${GOLD}`}} />
        </div>
      </Pop>
    </>
  );
};

const Camada = (p) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      {inRange(f, p.vilao) && <Vilao k={f - p.vilao[0]} bandY={p.bandY} bandH={p.bandH} />}
      {inRange(f, p.reviravolta) && <Reviravolta k={f - p.reviravolta[0]} n={p.reviravolta[1] - p.reviravolta[0]}
        bandY={p.bandY} bandH={p.bandH} />}
      {inRange(f, p.versus) && <Versus k={f - p.versus[0]} bandY={p.bandY} bandH={p.bandH} />}
      {inRange(f, p.end) && <Fim k={f - p.end[0]} bandY={p.bandY} title={p.endTitle} />}
    </AbsoluteFill>
  );
};

const props = require('../props.json');

const Root = () => (
  <Composition id="Camada" component={Camada} durationInFrames={props.n} fps={props.fps} width={1080}
    height={1920} defaultProps={props} />
);

registerRoot(Root);
