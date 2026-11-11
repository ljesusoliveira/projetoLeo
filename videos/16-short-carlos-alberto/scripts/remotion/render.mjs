// Renderiza a camada animada (Remotion) em ../frames/remotion/element-NNNN.png, com
// transparência, usando o Chromium que já vem instalado em /opt/pw-browsers.
//   node render.mjs            (depois de: python3 ../remotion_props.py)
import {bundle} from '@remotion/bundler';
import {renderFrames, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';

const browserExecutable = process.env.CHROME ||
  '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const outputDir = path.resolve('../frames/remotion');
fs.rmSync(outputDir, {recursive: true, force: true});
fs.mkdirSync(outputDir, {recursive: true});
const serveUrl = await bundle({entryPoint: path.resolve('src/index.jsx'), publicDir: path.resolve('public')});
const composition = await selectComposition({serveUrl, id: 'Camada', browserExecutable});
const t0 = Date.now();
await renderFrames({
  composition, serveUrl, outputDir, imageFormat: 'png', browserExecutable, concurrency: 4,
  onStart: () => {}, onFrameUpdate: () => {},
});
console.log(`camada ok: ${composition.durationInFrames} quadros em ${((Date.now() - t0) / 1000).toFixed(1)} s`);
