#!/bin/bash
# Reconstrói o Short a partir do vídeo exportado do CapCut.
# Uso: coloque o vídeo original como original.mp4 nesta pasta e rode ./build.sh
# Requisitos: ffmpeg, python3 com pillow e numpy, fonte Noto Color Emoji.
set -euo pipefail
cd "$(dirname "$0")"

FONTS=../fonts
mkdir -p "$FONTS"
GF=https://raw.githubusercontent.com/google/fonts/main/ofl
[ -f "$FONTS/Anton-Regular.ttf" ] || curl -sSLo "$FONTS/Anton-Regular.ttf" "$GF/anton/Anton-Regular.ttf"
[ -f "$FONTS/Montserrat.ttf" ] || curl -sSLo "$FONTS/Montserrat.ttf" "$GF/montserrat/Montserrat%5Bwght%5D.ttf"

# 1) camada gráfica (título, selo, chamadas, barra de progresso) sem perdas
python3 overlay.py stream | ffmpeg -hide_banner -v error -y -f rawvideo -pix_fmt rgba \
  -s 1080x1920 -framerate 30 -i - -c:v qtrle -pix_fmt argb overlay.mov

# 2) grafo de filtros (recorte por lance, fundo desfocado, cor, áudio)
python3 make_filter.py

COMMON=(-filter_complex_script filter.txt -map "[vout]" -map "[aout]" -c:v libx264
  -preset slow -tune film -profile:v high -level:v 4.2 -g 60 -bf 2 -pix_fmt yuv420p
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv -r 30)

# 3a) versão em alta qualidade (~150 MB), ideal para subir no YouTube
ffmpeg -hide_banner -y -i original.mp4 -i overlay.mov "${COMMON[@]}" -crf 17 \
  -maxrate 16M -bufsize 32M -c:a aac -b:a 320k -ar 48000 -movflags +faststart short_final.mp4

# 3b) versão leve (< 100 MB, cabe no GitHub sem LFS), em duas passadas
ffmpeg -hide_banner -y -i original.mp4 -i overlay.mov "${COMMON[@]}" -b:v 4500k \
  -maxrate 9000k -bufsize 9000k -pass 1 -passlogfile x264pass -an -f null -
ffmpeg -hide_banner -y -i original.mp4 -i overlay.mov "${COMMON[@]}" -b:v 4500k \
  -maxrate 9000k -bufsize 9000k -pass 2 -passlogfile x264pass -c:a aac -b:a 192k \
  -ar 48000 -movflags +faststart short_leve.mp4
