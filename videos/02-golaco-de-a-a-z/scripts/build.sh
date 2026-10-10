#!/usr/bin/env bash
# Refaz o vídeo sem as legendas dos jogadores a partir do original.mp4
# (baixado do release video-gols). Precisa de ffmpeg, numpy e opencv-python-headless.
set -euo pipefail
cd "$(dirname "$0")"
# 1) acha a legenda de cada gol quadro a quadro (4 processos em paralelo)
for g in ABCDEFG HIJKLM NOPQRST UVWXYZ; do python3 track.py $g > track_$g.log 2>&1 & done; wait
# 2) separa as fases da legenda: entrada, parada e saída
for g in ABCDEFG HIJKLM NOPQRST UVWXYZ; do python3 prep.py $g > prep_$g.log 2>&1 & done; wait
# 3) apaga as legendas e recodifica (áudio original copiado)
python3 render.py sem_legendas.mp4 19
