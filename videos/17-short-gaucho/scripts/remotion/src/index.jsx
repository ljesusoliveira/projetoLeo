// Camada animada do Short do Gaúcho, feita no Remotion e renderizada como PNG com
// transparência (um por quadro do Short). O compose.py junta essa camada por cima do
// vídeo e por baixo da legenda. Elementos:
//   defesas  enquanto passam as defesas, ZINHO e ALDAIR entram pequenos no alto da tela
//            (luva + DEFENDEU) no instante em que a narração fala cada nome; em "os dois"
//            o quadro cresce para o centro e, em "campeões do mundo", cada nome ganha o
//            selo CAMPEÃO DO MUNDO • 1994 (o que a narração diz)
//   end      encerramento: VÍDEO COMPLETO NO CANAL, título, INSCREVA-SE e o link
// Os quadros de cada elemento e os instantes internos ('marks') vêm de props.json.
import React from 'react';
import {
  AbsoluteFill, Composition, continueRender, delayRender, interpolate, registerRoot,
  spring, staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';

const GOLD = '#F2C230';
const RED = '#D6182C';

const fontHandle = delayRender('fontes');
const f1 = new FontFace('Anton', `url(${staticFile('Anton-Regular.ttf')})`);
const f2 = new FontFace('Montserrat', `url(${staticFile('Montserrat.ttf')})`, {weight: '100 900'});
Promise.all([f1.load(), f2.load()]).then(([a, b]) => {
  document.fonts.add(a);
  document.fonts.add(b);
  continueRender(fontHandle);
});

const stroke = (px, color = '#000') => ({
  WebkitTextStroke: `${px}px ${color}`, paintOrder: 'stroke fill',
  textShadow: '0 8px 18px rgba(0,0,0,.75)',
});



const inRange = (f, [a, b]) => f >= a && f < b;
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const GREEN = '#17A34A';

const Luva = ({size = 64}) => (
  <svg width={size} height={size} viewBox="0 0 64 64">
    <g fill="#fff" stroke="#111" strokeWidth="3" strokeLinejoin="round">
      <rect x="15" y="5" width="8" height="28" rx="4" />
      <rect x="24" y="2" width="8" height="30" rx="4" />
      <rect x="33" y="3" width="8" height="30" rx="4" />
      <rect x="42" y="8" width="8" height="26" rx="4" />
      <path d="M13 28 h37 v14 q0 14 -16 14 h-6 q-10 0 -14 -10 l-8 -14 q-2 -5 3 -6 q4 -1 6 3 z" />
      <rect x="16" y="50" width="30" height="11" rx="3" fill={GOLD} />
    </g>
  </svg>
);

const Linha = ({k, at, nome, campeao, grow}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: k - at, fps, config: {damping: 12, stiffness: 200}});
  const b = spring({frame: k - campeao, fps, config: {damping: 10, stiffness: 220, mass: 0.7}});
  if (k < at) return null;
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
      opacity: Math.min(1, s * 1.8), transform: `translateY(${interpolate(s, [0, 1], [-40, 0])}px) scale(${interpolate(s, [0, 1], [1.3, 1])})`}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 16, background: 'rgba(8,8,10,.88)',
        border: `4px solid ${GOLD}`, borderRadius: 20, padding: '8px 24px 8px 16px', boxShadow: '0 14px 30px rgba(0,0,0,.6)'}}>
        <Luva size={66} />
        <div style={{fontFamily: 'Anton', fontSize: 78, lineHeight: 1.15, color: '#fff'}}>{nome}</div>
        <div style={{fontFamily: 'Montserrat', fontWeight: 900, fontSize: 30, letterSpacing: 3, color: '#fff',
          background: GREEN, borderRadius: 12, padding: '8px 14px'}}>DEFENDEU</div>
      </div>
      {k >= campeao && (
        <div style={{opacity: Math.min(1, b * 2), transform: `scale(${interpolate(b, [0, 1], [1.8, 1])}) rotate(${interpolate(b, [0, 1], [-10, -3])}deg)`,
          fontFamily: 'Anton', fontSize: 44, lineHeight: 1.2, color: '#111', background: GOLD, borderRadius: 12,
          padding: '2px 22px', border: '4px solid #fff', boxShadow: '0 10px 24px rgba(0,0,0,.55)'}}>
          ★ CAMPEÃO DO MUNDO • 1994
        </div>
      )}
    </div>
  );
};

const Defesas = ({k, n, marks, bandY, bandH}) => {
  const {fps} = useVideoConfig();
  const grow = spring({frame: k - marks.dois, fps, config: {damping: 16, stiffness: 120}});
  const g = k >= marks.dois ? grow : 0;
  const out = interpolate(k, [n - 5, n], [1, 0], clamp);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: interpolate(g, [0, 1], [bandY + 26, bandY + bandH * 0.20]),
      display: 'flex', justifyContent: 'center', opacity: out}}>
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: interpolate(g, [0, 1], [14, 34]),
        transform: `scale(${interpolate(g, [0, 1], [0.78, 1.08])})`, transformOrigin: 'top center',
        padding: '26px 30px', borderRadius: 30, background: `rgba(8,8,10,${0.55 * g})`}}>
        <Linha k={k} at={marks.zinho} nome="ZINHO" campeao={marks.campeoes} grow={g} />
        <Linha k={k} at={marks.aldair} nome="ALDAIR" campeao={marks.campeoes + 5} grow={g} />
      </div>
    </div>
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
  const len = (r) => r[1] - r[0];
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      {inRange(f, p.defesas) && <Defesas k={f - p.defesas[0]} n={len(p.defesas)} marks={p.marks.defesas}
        bandY={p.bandY} bandH={p.bandH} />}
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
