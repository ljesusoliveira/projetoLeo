#!/usr/bin/env bash
# Refaz o Short do Júnior Baiano a partir do vídeo longo salvo como original.mp4 nesta pasta
# (release junior-baiano). Precisa de ffmpeg, numpy, pillow, opencv-python-headless e onnxruntime.
set -euo pipefail
cd "$(dirname "$0")"

FONTS=../fonts
mkdir -p "$FONTS"
GF=https://raw.githubusercontent.com/google/fonts/main/ofl
[ -f "$FONTS/Anton-Regular.ttf" ] || curl -sSLo "$FONTS/Anton-Regular.ttf" "$GF/anton/Anton-Regular.ttf"
[ -f "$FONTS/Montserrat.ttf" ] || curl -sSLo "$FONTS/Montserrat.ttf" "$GF/montserrat/Montserrat%5Bwght%5D.ttf"

# 0) trilha original (sem direitos autorais) e voz da entrevista separada da música do vídeo longo
MODEL=${MODEL:-Kim_Vocal_2.onnx}
[ -f "$MODEL" ] || curl -sSLo "$MODEL" https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/Kim_Vocal_2.onnx
python3 music.py
python3 separate.py "$MODEL"

# 1) imagem 9:16 (recorte que acompanha o lance, fundo desfocado, efeitos e textos)
python3 compose.py video.mp4
# 2) áudio (voz do gancho + trilha + efeitos, -14 LUFS)
python3 audio.py

COMMON=(-pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv)
# 3a) versão em alta qualidade, para subir no YouTube
ffmpeg -y -i video.mp4 -i audio.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 17 \
  -profile:v high -level:v 4.2 -g 60 -bf 2 -maxrate 16M -bufsize 32M "${COMMON[@]}" \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart short_final.mp4
# 3b) versão leve (< 30 MB), em duas passadas
ffmpeg -y -i video.mp4 -c:v libx264 -preset slow -b:v 5500k -maxrate 9000k -bufsize 9000k -g 60 \
  -pass 1 -passlogfile x264pass -an -f null -
ffmpeg -y -i video.mp4 -i audio.wav -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 5500k \
  -maxrate 9000k -bufsize 9000k -g 60 -pass 2 -passlogfile x264pass "${COMMON[@]}" \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart short_leve.mp4
