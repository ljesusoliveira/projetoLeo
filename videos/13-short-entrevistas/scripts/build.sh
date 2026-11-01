#!/usr/bin/env bash
# Refaz o Short das entrevistas mais engraçadas a partir do vídeo longo salvo como
# original.mp4 nesta pasta (release entrevistas-jogadores). Precisa de ffmpeg, numpy, pillow e opencv-python-headless.
set -euo pipefail
cd "$(dirname "$0")"

FONTS=../fonts
mkdir -p "$FONTS"
GF=https://raw.githubusercontent.com/google/fonts/main/ofl
[ -f "$FONTS/BebasNeue-Regular.ttf" ] || curl -sSLo "$FONTS/BebasNeue-Regular.ttf" "$GF/bebasneue/BebasNeue-Regular.ttf"
[ -f "$FONTS/Montserrat.ttf" ] || curl -sSLo "$FONTS/Montserrat.ttf" "$GF/montserrat/Montserrat%5Bwght%5D.ttf"

# 1) imagem 9:16 (recorte em quem fala, transições, figurinhas, lampejos e encerramento)
python3 compose.py video.mp4
# 2) áudio (som original de cada entrevista, inteira, + narração de abertura no final, -14 LUFS)
python3 audio.py

COMMON=(-pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv)
# 3a) versão em alta qualidade, para subir no YouTube
ffmpeg -y -i video.mp4 -i audio.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 17 \
  -profile:v high -level:v 4.2 -g 60 -bf 2 -maxrate 16M -bufsize 32M "${COMMON[@]}" \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart short_final.mp4
# 3b) versão leve (< 30 MB), em duas passadas
ffmpeg -y -i video.mp4 -c:v libx264 -preset slow -b:v 5200k -maxrate 9000k -bufsize 9000k -g 60 \
  -pass 1 -passlogfile x264pass -an -f null -
ffmpeg -y -i video.mp4 -i audio.wav -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 5200k \
  -maxrate 9000k -bufsize 9000k -g 60 -pass 2 -passlogfile x264pass "${COMMON[@]}" \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart short_leve.mp4
