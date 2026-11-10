// Camada animada do Short do Conca, feita no Remotion e renderizada como PNG com
// transparência (um por quadro do Short). O compose.py junta essa camada por cima do
// vídeo e por baixo da legenda. Elementos:
//   ranking  "OS MAIS BEM PAGOS DO PLANETA • 2011": CONCA entra em 3º e, quando a narração
//            fala, MESSI e CRISTIANO RONALDO aparecem acima dele (sem numerar os dois,
//            porque a narração não diz a ordem entre eles)
//   china    BRASIL é riscado e CHINA bate na tela
//   medidas  "MENOS DE 1,70 M" e "CERCA DE 58 KG"
//   end      encerramento: VÍDEO COMPLETO NO CANAL, título, INSCREVA-SE e o link
// Os quadros de cada elemento e os instantes internos ('marks') vêm de props.json.
import React from 'react';
import {
  AbsoluteFill, Composition, continueRender, delayRender, interpolate, registerRoot,
  spring, staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';

const GOLD = '#F2C230';
const RED = '#D6182C';
const GREEN = '#0E8A43';

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

const Row = ({k, at, children, gold}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: k - at, fps, config: {damping: 13, stiffness: 190}});
  if (k < at) return null;
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 22, padding: '14px 30px',
      background: gold ? 'rgba(242,194,48,.18)' : 'rgba(255,255,255,.06)',
      border: gold ? `4px solid ${GOLD}` : '2px solid rgba(255,255,255,.25)', borderRadius: 16,
      transform: `translateX(${interpolate(s, [0, 1], [380, 0])}px) scale(${gold ? interpolate(s, [0, 1], [1.25, 1]) : 1})`,
      opacity: Math.min(1, s * 1.6)}}>
      {children}
    </div>
  );
};

const Ranking = ({k, n, marks, bandY, bandH}) => {
  const {fps} = useVideoConfig();
  const inS = spring({frame: k, fps, config: {damping: 16, stiffness: 170}});
  const out = interpolate(k, [n - 5, n], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const pulse = 1 + 0.035 * Math.sin(k / fps * 2 * Math.PI * 1.5);
  return (
    <div style={{position: 'absolute', left: 60, right: 60, top: bandY + bandH * 0.13,
      opacity: Math.min(inS, out), transform: `translateY(${interpolate(inS, [0, 1], [60, 0])}px)`,
      background: 'rgba(8,8,10,.86)', border: `3px solid ${GOLD}`, borderRadius: 26, padding: '30px 34px 34px',
      boxShadow: '0 24px 60px rgba(0,0,0,.7)', display: 'flex', flexDirection: 'column', gap: 18}}>
      <div style={{textAlign: 'center'}}>
        <div style={{fontFamily: 'Montserrat', fontWeight: 800, fontSize: 34, letterSpacing: 6, color: GOLD}}>2011</div>
        <div style={{fontFamily: 'Anton', fontSize: 66, lineHeight: 1.1, color: '#fff'}}>OS MAIS BEM PAGOS</div>
        <div style={{fontFamily: 'Anton', fontSize: 66, lineHeight: 1.1, color: '#fff'}}>DO PLANETA</div>
      </div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 14, marginTop: 6, minHeight: 330,
        justifyContent: 'flex-end'}}>
        <Row k={k} at={marks.messi}>
          <div style={{fontFamily: 'Anton', fontSize: 70, color: '#fff'}}>MESSI</div>
        </Row>
        <Row k={k} at={marks.cr}>
          <div style={{fontFamily: 'Anton', fontSize: 70, color: '#fff'}}>CRISTIANO RONALDO</div>
        </Row>
        <Row k={k} at={0} gold>
          <div style={{fontFamily: 'Anton', fontSize: 88, color: GOLD, transform: `scale(${pulse})`,
            minWidth: 110}}>3º</div>
          <div style={{fontFamily: 'Anton', fontSize: 88, color: '#fff'}}>CONCA</div>
        </Row>
      </div>
    </div>
  );
};

const China = ({k, marks, bandY, bandH}) => {
  const {fps} = useVideoConfig();
  const b = spring({frame: k - marks.brasil, fps, config: {damping: 14, stiffness: 200}});
  const risco = interpolate(k, [marks.china - 4, marks.china + 2], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const c = spring({frame: k - marks.china, fps, config: {damping: 9, stiffness: 230, mass: 0.7}});
  const shake = k >= marks.china && k < marks.china + 8 ? Math.sin(k * 3.3) * (marks.china + 8 - k) * 1.3 : 0;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: bandY + bandH * 0.34, display: 'flex',
      flexDirection: 'column', alignItems: 'center', gap: 6, transform: `translateX(${shake}px)`}}>
      {k >= marks.brasil && (
        <div style={{position: 'relative', opacity: Math.min(1, b * 1.6) * interpolate(risco, [0, 1], [1, 0.75]),
          transform: `scale(${interpolate(b, [0, 1], [1.4, 1])})`}}>
          <div style={{fontFamily: 'Anton', fontSize: 120, color: '#fff', background: GREEN, padding: '0 34px',
            borderRadius: 14, border: '5px solid #FFDF00', boxShadow: '0 14px 30px rgba(0,0,0,.6)'}}>BRASIL</div>
          <div style={{position: 'absolute', left: -14, top: '50%', height: 16, width: `${risco * 110}%`,
            background: RED, transform: 'rotate(-8deg)', borderRadius: 8, boxShadow: '0 4px 10px rgba(0,0,0,.5)'}} />
        </div>
      )}
      {k >= marks.china && (
        <div style={{transform: `scale(${interpolate(c, [0, 1], [1.9, 1])}) rotate(${interpolate(c, [0, 1], [-14, -4])}deg)`,
          opacity: Math.min(1, c * 2), marginTop: 8}}>
          <div style={{fontFamily: 'Anton', fontSize: 170, color: '#FFDE00', background: RED, padding: '0 46px',
            borderRadius: 18, border: '7px solid #FFDE00', boxShadow: '0 18px 40px rgba(0,0,0,.65)'}}>CHINA</div>
        </div>
      )}
    </div>
  );
};

const Stat = ({k, at, big, small}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: k - at, fps, config: {damping: 11, stiffness: 200}});
  if (k < at) return null;
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(8,8,10,.85)',
      border: `4px solid ${GOLD}`, borderRadius: 20, padding: '10px 30px 14px', minWidth: 380,
      transform: `scale(${interpolate(s, [0, 1], [1.6, 1])})`, opacity: Math.min(1, s * 2),
      boxShadow: '0 16px 36px rgba(0,0,0,.65)'}}>
      <div style={{fontFamily: 'Montserrat', fontWeight: 800, fontSize: 30, letterSpacing: 4, color: '#fff'}}>{small}</div>
      <div style={{fontFamily: 'Anton', fontSize: 104, lineHeight: 1.1, color: GOLD}}>{big}</div>
    </div>
  );
};

const Medidas = ({k, n, marks, bandY, bandH}) => {
  const out = interpolate(k, [n - 5, n], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: bandY + bandH * 0.50, display: 'flex',
      justifyContent: 'center', gap: 34, opacity: out}}>
      <Stat k={k} at={marks.altura} small="MENOS DE" big="1,70 M" />
      <Stat k={k} at={marks.peso} small="CERCA DE" big="58 KG" />
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
      {inRange(f, p.ranking) && <Ranking k={f - p.ranking[0]} n={len(p.ranking)} marks={p.marks.ranking}
        bandY={p.bandY} bandH={p.bandH} />}
      {inRange(f, p.china) && <China k={f - p.china[0]} marks={p.marks.china} bandY={p.bandY} bandH={p.bandH} />}
      {inRange(f, p.medidas) && <Medidas k={f - p.medidas[0]} n={len(p.medidas)} marks={p.marks.medidas}
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
