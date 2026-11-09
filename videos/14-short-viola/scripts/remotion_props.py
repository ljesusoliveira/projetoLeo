"""Gera remotion/props.json (quadros de cada elemento animado) a partir do edl.json."""
import json
import os

import overlay
from timeline import END_TITLE_LINES, FPS, N, REMOTION

HERE = os.path.dirname(os.path.abspath(__file__))
props = dict(n=N, fps=FPS, bandY=overlay.BAND_Y, bandH=overlay.BAND_H, endTitle=END_TITLE_LINES,
             **{k: list(v) for k, v in REMOTION.items()})
json.dump(props, open(os.path.join(HERE, 'remotion', 'props.json'), 'w'), ensure_ascii=False, indent=1)
print(props)
