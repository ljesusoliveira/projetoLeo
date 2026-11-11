// Camada animada do Short do Carlos Alberto Torres, feita no Remotion e renderizada como
// PNG com transparência (um por quadro do Short). O compose.py junta essa camada por cima
// do vídeo e por baixo da legenda. Elementos:
//   umacopa  carimbo "SÓ 1 COPA" (com "MÉXICO 1970") quando a narração diz "apenas uma Copa"
//   lista    Copa de 1966: o contador vai a 44 na "lista inicial de 44 jogadores", o carimbo
//            FORA bate em CARLOS ALBERTO e o número cai para 22 nos "22 convocados"
//            (nenhum outro nome aparece, para não inventar a lista)
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

const UmaCopa = ({k, n, marks, bandY, bandH}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: k - marks.stamp, fps, config: {damping: 9, stiffness: 230, mass: 0.7}});
  const sub = spring({frame: k - marks.stamp - 5, fps, config: {damping: 13, stiffness: 200}});
  const shake = k >= marks.stamp && k < marks.stamp + 8 ? Math.sin(k * 3.3) * (marks.stamp + 8 - k) * 1.4 : 0;
  const out = interpolate(k, [n - 4, n], [1, 0], clamp);
  if (k < marks.stamp) return null;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: bandY + bandH * 0.40, display: 'flex',
      flexDirection: 'column', alignItems: 'center', gap: 22, opacity: out, transform: `translateX(${shake}px)`}}>
      <div style={{transform: `scale(${interpolate(s, [0, 1], [2.0, 1])}) rotate(${interpolate(s, [0, 1], [-15, -5])}deg)`,
        opacity: Math.min(1, s * 2)}}>
        <div style={{fontFamily: 'Anton', fontSize: 168, lineHeight: 1.12, color: '#fff', background: RED,
          padding: '0 48px', borderRadius: 18, border: `8px solid ${GOLD}`,
          boxShadow: '0 18px 44px rgba(0,0,0,.7)'}}>SÓ 1 COPA</div>
      </div>
      <div style={{opacity: Math.min(1, sub * 2), transform: `translateY(${interpolate(sub, [0, 1], [30, 0])}px)`,
        fontFamily: 'Montserrat', fontWeight: 800, fontSize: 40, letterSpacing: 6, color: GOLD,
        background: 'rgba(8,8,10,.88)', border: `3px solid ${GOLD}`, borderRadius: 40, padding: '10px 34px'}}>
        MÉXICO 1970
      </div>
    </div>
  );
};

const Lista = ({k, n, marks, bandY, bandH}) => {
  const {fps} = useVideoConfig();
  const inS = spring({frame: k, fps, config: {damping: 16, stiffness: 170}});
  const out = interpolate(k, [n - 5, n], [1, 0], clamp);
  // contador 0 -> 44 entre 'lista' e '44'
  const c = interpolate(k, [marks.lista, marks.n44], [0, 1], clamp);
  const num44 = Math.round(44 * (1 - Math.pow(1 - c, 2.2)));
  const hit44 = spring({frame: k - marks.n44, fps, config: {damping: 8, stiffness: 260, mass: 0.6}});
  const flip = spring({frame: k - marks.n22, fps, config: {damping: 12, stiffness: 210}});
  const fora = spring({frame: k - marks.fora, fps, config: {damping: 9, stiffness: 240, mass: 0.7}});
  const shake = k >= marks.fora && k < marks.fora + 8 ? Math.sin(k * 3.1) * (marks.fora + 8 - k) * 1.5 : 0;
  const after22 = k >= marks.n22;
  const bump = k >= marks.n44 && !after22 ? interpolate(hit44, [0, 1], [1.35, 1]) : 1;
  return (
    <div style={{position: 'absolute', left: 70, right: 70, top: bandY + bandH * 0.10,
      opacity: Math.min(inS, out), transform: `translateY(${interpolate(inS, [0, 1], [70, 0])}px) translateX(${shake}px)`,
      background: 'rgba(8,8,10,.86)', border: `3px solid ${GOLD}`, borderRadius: 28, padding: '30px 34px 38px',
      boxShadow: '0 24px 60px rgba(0,0,0,.7)', display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div style={{fontFamily: 'Montserrat', fontWeight: 800, fontSize: 36, letterSpacing: 7, color: GOLD}}>
        COPA DE 1966
      </div>
      <div style={{position: 'relative', height: 92, width: '100%'}}>
        <div style={{position: 'absolute', left: 0, right: 0, textAlign: 'center', fontFamily: 'Anton', fontSize: 74,
          color: '#fff', opacity: 1 - flip, transform: `translateY(${-40 * flip}px)`}}>LISTA INICIAL</div>
        {after22 && <div style={{position: 'absolute', left: 0, right: 0, textAlign: 'center', fontFamily: 'Anton',
          fontSize: 74, color: '#fff', opacity: flip, transform: `translateY(${40 * (1 - flip)}px)`}}>CONVOCADOS</div>}
      </div>
      <div style={{position: 'relative', height: 250, width: '100%', marginTop: 4}}>
        <div style={{position: 'absolute', left: 0, right: 0, textAlign: 'center', fontFamily: 'Anton', fontSize: 236,
          lineHeight: '250px', color: GOLD, opacity: 1 - flip,
          transform: `translateY(${-90 * flip}px) scale(${bump})`}}>{k >= marks.n44 ? 44 : num44}</div>
        {after22 && <div style={{position: 'absolute', left: 0, right: 0, textAlign: 'center', fontFamily: 'Anton',
          fontSize: 236, lineHeight: '250px', color: '#fff', opacity: Math.min(1, flip * 1.5),
          transform: `translateY(${90 * (1 - flip)}px) scale(${interpolate(flip, [0, 1], [1.3, 1])})`}}>22</div>}
      </div>
      <div style={{fontFamily: 'Montserrat', fontWeight: 800, fontSize: 36, letterSpacing: 6, color: '#fff',
        marginTop: -4}}>JOGADORES</div>
      <div style={{position: 'relative', marginTop: 34, padding: '12px 40px', borderRadius: 16,
        background: k >= marks.fora ? 'rgba(214,24,44,.16)' : 'rgba(255,255,255,.07)',
        border: `3px solid ${k >= marks.fora ? RED : 'rgba(255,255,255,.35)'}`}}>
        <div style={{fontFamily: 'Anton', fontSize: 84, color: '#fff',
          opacity: k >= marks.fora ? interpolate(fora, [0, 1], [1, 0.72]) : 1}}>CARLOS ALBERTO</div>
        {k >= marks.fora && (
          <div style={{position: 'absolute', left: 0, right: 0, top: 0, bottom: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'flex-end'}}>
            <div style={{transform: `translate(96px, -58px) scale(${interpolate(fora, [0, 1], [2.1, 1])}) rotate(${interpolate(fora, [0, 1], [-18, -9])}deg)`,
              opacity: Math.min(1, fora * 2), fontFamily: 'Anton', fontSize: 96, lineHeight: 1.1, color: RED,
              border: `9px solid ${RED}`, borderRadius: 16, padding: '0 36px', background: 'rgba(255,255,255,.92)',
              boxShadow: '0 14px 34px rgba(0,0,0,.6)'}}>FORA</div>
          </div>
        )}
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
      {inRange(f, p.umacopa) && <UmaCopa k={f - p.umacopa[0]} n={len(p.umacopa)} marks={p.marks.umacopa}
        bandY={p.bandY} bandH={p.bandH} />}
      {inRange(f, p.lista) && <Lista k={f - p.lista[0]} n={len(p.lista)} marks={p.marks.lista}
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
